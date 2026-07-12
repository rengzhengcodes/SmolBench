"""Annotate Lean 4 SFT rows with a CoT rationale via Bedrock Claude (Converse).

Package D of the 2026-07-12 CoT SFT plan (see
``notebooks/lean/research/2026-07-12_sft_recipe_deep_research.md``): prior
SFT on bare tactic tails gave no significant deduction-eval gain, and the
research finding is that the fix is CoT-augmented training targets. This
script does not change *what* the trainee model is trained to output (still
the bare Lean 4 tactic tail) -- it augments the ASSISTANT TARGET with a
retrospective natural-language rationale that a stronger model (Claude,
called here) writes *after seeing the ground-truth answer*, wrapped around
the byte-identical tail so the tail supervision signal is unchanged.

Why a hand-rolled Bedrock client, not the smolbench ``aws`` provider
---------------------------------------------------------------------
``smolbench.evals.aws`` (and the ``openai_compat.ChatClient`` it wraps) talks
an OpenAI-chat-completions-shaped wire format and explicitly cannot reach
Anthropic models on Bedrock (see ``smolbench/evals/aws.py`` lines 11-12).
Anthropic models on Bedrock are reached through the **Converse** API
instead, which has a different request/response shape entirely -- so this
module builds a minimal, purpose-built client (`BedrockAnnotator`) rather
than bending the eval-side provider to fit.

Reproducibility note (seed policy)
-----------------------------------
Converse has **no** ``seed`` parameter (unlike the eval-side OpenAI-style
providers, which always thread one through -- see
``notebooks/lean/README.md``'s seed-policy note). Nothing is being dropped
here: this script is not an eval generation, it is an offline data-build
step, and the repo's "never drop ``seed``" rule concerns eval generations.
Reproducibility for THIS step instead rests on ``temperature=0.0`` + a fixed
``--model`` id + the exact prompt template, whose sha256 is recorded in the
manifest (`_TEMPLATE_SHA256`) precisely so a manifest pins what was asked,
even though the model's own sampling is not literally seed-controllable.

Pipeline (see `main`)
----------------------
1. Load ``--dataset`` (default: the decontaminated real-arm SFT JSONL from
   ``build_lean_synth_sft.py --arm real``) and select a seeded, deterministic
   subsample of ``--limit`` rows (idiom shared with `build_lean_synth_sft`'s
   priority sampling, but simplified: since every candidate row already
   costs one paid LLM call regardless of whether its rationale survives QC,
   there is no pool-headroom backfill here -- the subsample is exactly
   ``--limit`` rows, chosen once, deterministically).
2. A hard-error preflight re-scan of every candidate row's BARE (pre-CoT)
   decontamination facets against the eval holdout, BEFORE any AWS spend
   (`_preflight_bare_facet_check`).
3. For each row not already in the resume done-set: call the annotator
   (concurrent, `--workers` threads, around the network call only) to get a
   retrospective rationale; QC-gate it; content-decontaminate the rationale
   itself; compose the final CoT-augmented assistant target
   (`compose_target`); append-write it.
4. Write ``<out>.manifest.json`` (config/provenance/decontam stats) and
   ``<out>.qc.json`` (rationale-quality diagnostics) atomically at the end.
5. Regenerate the PAIRED BARE-CONTROL sibling JSONL from the final (possibly
   resumed-into) ``--out`` file: read back every row `--out` now contains,
   and for each row's ``(full_name, k)`` key, write the ORIGINAL (bare,
   pre-annotation) source row from ``--dataset`` -- byte-identical
   ``system``/``user``/``assistant``/``meta`` -- to a sibling path (the
   style token in ``--out``'s name replaced by ``"bare"``, e.g.
   ``cot_stepk1_think_8k.jsonl`` -> ``cot_stepk1_bare_8k.jsonl``), in the
   same row order (`_write_bare_sibling`). WHY: without this, a
   downstream ``bare-vs-cot`` training comparison that samples its bare
   arm independently (e.g. the trainer's own ``--max-examples N`` seeded
   `ds.shuffle().select()`) ends up training on a DIFFERENT ~N rows than
   the CoT arm saw -- confounding the format comparison (CoT vs. bare
   target) with a sampling difference (which theorems each arm was even
   trained on). The sibling makes the two arms' theorem sets IDENTICAL by
   construction, so any measured difference is attributable to the target
   format alone. Runs on every real (non-``--dry-run``, dataset-found)
   invocation, INCLUDING a resumed one -- it re-derives from ``--out``'s
   current-on-disk content every time, so it always reflects the exact
   UNION of every invocation's emitted rows, not just this run's.

Examples
--------
    .venv/bin/python scripts/annotate_lean_cot.py --style think --limit 5 --dry-run
    .venv/bin/python scripts/annotate_lean_cot.py --style think --limit 8000
    .venv/bin/python scripts/annotate_lean_cot.py --style fenced --limit 0
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Sequence

# Anchor imports on the repo root, matching the sibling build scripts, so an
# ad-hoc `python scripts/annotate_lean_cot.py` works without an editable
# install.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.build_lean_sft import _fingerprint  # noqa: E402
from scripts.build_lean_synth_sft import _facets_from_rendered  # noqa: E402
from smolbench.deduction.lean.decontam import HoldoutIndex  # noqa: E402

_DATA_SFT = _REPO_ROOT / "notebooks" / "lean" / "data" / "sft"
_DEFAULT_DATASET = _DATA_SFT / "novel_premises_train_stepk1_decontam.jsonl"

#: Default Bedrock inference-profile id for the annotator. A flag (not a
#: constant) because the exact profile id in the target account/region is
#: resolved live later -- see the coordination constants in the plan.
_DEFAULT_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


# ---------------------------------------------------------------------------
# Fixed annotation prompt (system + suffix template). MUST stay byte-stable
# across runs -- its sha256 is recorded in the manifest as the reproducibility
# anchor (see module docstring's seed-policy note).
# ---------------------------------------------------------------------------

ANNOTATION_SYSTEM = "You are an expert Lean 4 / Mathlib mathematician writing training data."

#: The row's own ``user`` text (the rendered proof state, ending in an
#: instruction meant for the TRAINEE model -- harmless to leave in, since the
#: annotator is simply asked a different question about the same state) has
#: this suffix appended to form the full annotation-turn prompt. Kept as a
#: module-level constant (not built with the tail inlined) so its sha256 is
#: a stable, row-independent "template" fingerprint.
_ANNOTATION_SUFFIX_TEMPLATE = (
    "\n\n---\nGround-truth completion (verified):\n```lean\n{tail}\n```\n\n"
    "Write the internal reasoning (at most 250 words) that would lead from the proof "
    "state to exactly this completion: identify the goal shape, the relevant "
    "hypotheses/premises, and why each tactic applies, in order. Plain prose; inline "
    "backticks for identifiers are fine. Do NOT restate the completion at the end, do "
    "NOT use code fences, do NOT use <think> tags."
)

#: sha256 over (system, suffix template) -- NOT over any composed prompt
#: (which would vary per-row via ``{tail}``). Recorded in the manifest so a
#: reader can confirm two annotation runs used the identical instructions.
_TEMPLATE_SHA256 = hashlib.sha256(
    (ANNOTATION_SYSTEM + "\x00" + _ANNOTATION_SUFFIX_TEMPLATE).encode("utf-8")
).hexdigest()


def _compose_annotation_prompt(user_text: str, tail: str) -> str:
    """Build the full annotation-turn user prompt for one row.

    Parameters
    ----------
    user_text : str
        The row's rendered proof-state user turn (byte-identical to what the
        eval sends the trainee model at this rung).
    tail : str
        The row's ground-truth (bare) tactic tail -- the answer the
        annotator is shown and asked to explain, never to reproduce.

    Returns
    -------
    str
        ``user_text`` followed by `_ANNOTATION_SUFFIX_TEMPLATE` with ``tail``
        substituted.
    """
    return user_text + _ANNOTATION_SUFFIX_TEMPLATE.format(tail=tail)


# ---------------------------------------------------------------------------
# Composed CoT target styles (coordination constants -- MUST match the
# trainer/orchestrator packages exactly; see the plan's shared context).
# ---------------------------------------------------------------------------

_STYLES = ("think", "fenced")


def compose_target(style: str, rationale: str, tail: str) -> str:
    """Compose the final CoT-augmented assistant target.

    Parameters
    ----------
    style : {"think", "fenced"}
        Which base-model-family convention to wrap the rationale in --
        ``"think"`` for Qwen-style ``<think>`` reasoning blocks, ``"fenced"``
        for Llama/Nemotron-style prose-then-code-fence.
    rationale : str
        The (already QC-gated) natural-language rationale. Must not itself
        contain code fences or ``<think>``/``</think>`` tags -- callers are
        expected to have enforced this via `_qc_gate` before calling here,
        since a rationale containing either would break the round-trip
        through `smolbench.deduction.lean.prompt.extract_tactic_block`.
    tail : str
        The ground-truth tactic tail, inserted byte-identical to the source
        row's ``assistant`` field -- this is the only text used as the
        actual SFT supervision target's answer; the rationale is
        supplementary context.

    Returns
    -------
    str
        ``"<think>\\n{rationale}\\n</think>\\n\\n{tail}"`` for ``"think"``, or
        ``"{rationale}\\n\\n```lean\\n{tail}\\n```"`` for ``"fenced"``.
        `extract_tactic_block` on this string recovers `tail` exactly,
        given the rationale precondition above.

    Raises
    ------
    ValueError
        If `style` is not one of `_STYLES`.
    """
    if style == "think":
        return f"<think>\n{rationale}\n</think>\n\n{tail}"
    if style == "fenced":
        return f"{rationale}\n\n```lean\n{tail}\n```"
    raise ValueError(f"style must be one of {_STYLES}; got {style!r}")


# ---------------------------------------------------------------------------
# Seeded deterministic subsample
# ---------------------------------------------------------------------------


def _priority(seed: int, tag: str, full_name: str, k: int) -> int:
    """Deterministic per-row sampling priority (uniform, order-free).

    Same blake2b-priority idiom as `build_lean_synth_sft._priority`, keyed
    on the row's content identity ``(full_name, k)`` instead of a raw file
    index -- so the selected SET is independent of the input file's row
    order (re-sorting or re-exporting the source JSONL cannot change which
    rows get annotated for a given ``(seed, limit)``). ``tag`` namespaces
    unrelated uses of this same function against each other (the row
    subsample vs. the QC-report's 5-gram sample) so they don't collide on
    identical ``(seed, full_name, k)`` triples.
    """
    return int.from_bytes(
        hashlib.blake2b(f"{seed}:{tag}:{full_name}:{k}".encode("utf-8"), digest_size=8).digest(),
        "big",
    )


def _load_rows(dataset: Path) -> list[dict]:
    """Load every JSONL row of `dataset` into memory as plain dicts."""
    rows: list[dict] = []
    with dataset.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _select_subsample(rows: Sequence[dict], *, seed: int, limit: int) -> list[dict]:
    """Deterministic seeded subsample of `limit` rows (``0`` = keep all).

    Parameters
    ----------
    rows : sequence of dict
        Rows loaded from the dataset (each must have ``meta.full_name`` and
        ``meta.k``).
    seed : int
        Sampling seed (see `_priority`).
    limit : int
        Number of rows to select; ``0`` means "keep every row".

    Returns
    -------
    list of dict
        The selected rows, in their ORIGINAL relative order from `rows`
        (only membership is priority-ranked -- ordering is preserved for
        readability and for stable resume/progress reporting). The
        resulting *set* of selected rows is independent of the order `rows`
        was given in, since `_priority` depends only on each row's
        ``(full_name, k)`` identity, not its position.
    """
    if limit <= 0 or limit >= len(rows):
        return list(rows)
    ranked_indices = sorted(
        range(len(rows)),
        key=lambda i: _priority(seed, "cot", rows[i]["meta"]["full_name"], rows[i]["meta"]["k"]),
    )
    selected = set(ranked_indices[:limit])
    return [rows[i] for i in range(len(rows)) if i in selected]


# ---------------------------------------------------------------------------
# Preflight: hard-error re-scan of BARE facets (before any AWS spend)
# ---------------------------------------------------------------------------


def _preflight_bare_facet_check(rows: Sequence[dict], index: HoldoutIndex) -> None:
    """Hard-error re-scan of every candidate row's BARE facets, pre-spend.

    Re-derives each row's content decontamination facets from its BARE
    (pre-annotation) ``user``/``assistant`` text via the exact same
    `_facets_from_rendered` helper `build_lean_synth_sft.py`'s own zero-leak
    gate uses, and re-checks them against `index`. The source dataset (the
    ``real`` arm's decontaminated output) already passed this exact gate
    when it was built; a hit here means something regressed upstream (a
    stale/hand-edited dataset file, a holdout-spec mismatch between build
    time and now, etc.) -- NOT an expected, occasionally-firing condition
    like the per-row rationale-content check below. So this is fatal
    (`SystemExit`), not a per-row drop-and-continue: better to refuse to
    spend any money than to annotate (and possibly ship) a leaking row.

    Parameters
    ----------
    rows : sequence of dict
        The candidate rows about to be annotated (the post-subsample
        working set).
    index : HoldoutIndex
        The built eval-holdout content index.

    Raises
    ------
    SystemExit
        If any row's re-derived facets hit the holdout index. Prints up to
        20 offending theorem names to stderr first.
    """
    leaks: list[tuple[Optional[str], str]] = []
    for row in rows:
        states, tactics, pairs = _facets_from_rendered(row["user"], row["assistant"])
        hits = index.check(
            statement=states[0] if states else None,
            states=states,
            tactics=tactics,
            pairs=pairs,
        )
        if hits:
            leaks.append((row.get("meta", {}).get("full_name"), hits[0].key))
    if leaks:
        for name, key in leaks[:20]:
            print(f"  leak: {name} ({key})", file=sys.stderr)
        raise SystemExit(
            f"FATAL: preflight re-scan found {len(leaks)} leaking source row(s) in the "
            "working set -- refusing to spend on annotation. The source dataset should "
            "already be clean; see build_lean_synth_sft.py's zero-leak gate."
        )


# ---------------------------------------------------------------------------
# Per-row QC gates
# ---------------------------------------------------------------------------

#: Minimum fraction of the tail's non-empty stripped lines that must appear
#: verbatim (substring match) in the rationale for a multi-line tail to be
#: flagged as a restatement. Chosen per the plan spec: ">=50%" is a
#: deliberately generous threshold -- a rationale legitimately paraphrasing
#: individual tactic names (e.g. "then apply `simp`") will cross it only if
#: it echoes HALF the tail's lines, which a genuine explanation rarely does.
_RESTATEMENT_LINE_FRACTION = 0.5


def _is_restatement(rationale: str, tail: str) -> bool:
    """True if `rationale` looks like it just restates `tail` verbatim.

    Parameters
    ----------
    rationale : str
        The candidate rationale text.
    tail : str
        The ground-truth tactic tail the rationale is meant to explain.

    Returns
    -------
    bool
        For a tail with < 2 non-empty lines (a single-tactic completion,
        where "restatement" and "correctly names the one tactic" are hard
        to distinguish by line-overlap), True only when the two texts are
        identical after stripping. Otherwise, True when at least
        `_RESTATEMENT_LINE_FRACTION` of the tail's non-empty stripped lines
        each appear verbatim (as a substring) somewhere in the rationale.
    """
    tail_lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
    if len(tail_lines) < 2:
        return rationale.strip() == tail.strip()
    hits = sum(1 for ln in tail_lines if ln in rationale)
    return (hits / len(tail_lines)) >= _RESTATEMENT_LINE_FRACTION


def _qc_gate(rationale: str, tail: str, *, max_rationale_chars: int) -> Optional[str]:
    """Run the fixed per-row QC gate sequence; return the first failing reason.

    Gates are checked in this fixed order (a row failing more than one only
    counts once, against the FIRST reason it trips): empty rationale;
    forbidden markup (a code fence or a ``<think>``/``</think>`` tag, either
    of which would break `compose_target`'s round-trip guarantee through
    `extract_tactic_block`); rationale too long; rationale is a restatement
    of the tail rather than an explanation of it.

    Parameters
    ----------
    rationale : str
        The annotator's response. Stripped internally (defensively -- a
        caller-side strip is NOT required), so an all-whitespace response
        correctly counts as empty.
    tail : str
        The ground-truth tactic tail.
    max_rationale_chars : int
        Maximum allowed ``len(rationale)`` (measured on the stripped text).

    Returns
    -------
    str or None
        One of ``"empty_rationale"``, ``"forbidden_markup"``, ``"too_long"``,
        ``"restatement"`` -- or None if `rationale` passes every gate.
    """
    rationale = rationale.strip()
    if not rationale:
        return "empty_rationale"
    if "```" in rationale or "<think>" in rationale or "</think>" in rationale:
        return "forbidden_markup"
    if len(rationale) > max_rationale_chars:
        return "too_long"
    if _is_restatement(rationale, tail):
        return "restatement"
    return None


# ---------------------------------------------------------------------------
# Grounding-rate heuristic (QC report only)
# ---------------------------------------------------------------------------

#: Matches from the first ``⊢`` (the goal turnstile) up to the next
#: backtick -- i.e. through the end of the enclosing fenced code block. The
#: "Current goal" block is always the first thing rendered in a row's user
#: turn (see `scripts.build_lean_synth_sft.render_state_user`), so the FIRST
#: match is always the goal, never a later hypothesis or a stray ``⊢`` deep
#: in the full-state block.
_GOAL_LINE_RE = re.compile(r"⊢([^`]*)")
#: Deliberately simple word-token extraction (per the plan spec) -- no
#: attempt to handle Lean's ``'`` (prime) identifiers or dotted namespaces
#: specially; this is a diagnostic heuristic for the QC report, not a
#: decontamination key.
_IDENT_TOKEN_RE = re.compile(r"\w{3,}")


def _goal_identifiers(user_text: str) -> set[str]:
    """Candidate identifier tokens (``\\w{3,}``) from the row's goal line.

    Parameters
    ----------
    user_text : str
        A row's rendered user turn.

    Returns
    -------
    set of str
        Tokens found between the first ``⊢`` and the next backtick; empty
        if no ``⊢`` is present.
    """
    m = _GOAL_LINE_RE.search(user_text)
    if not m:
        return set()
    return set(_IDENT_TOKEN_RE.findall(m.group(1)))


def _distinct_5gram_ratio(rationales: Sequence[str]) -> tuple[int, float]:
    """Word-level distinct-5-gram diversity ratio over a rationale sample.

    The "distinct-n" diagnostic (Li et al. 2016, "A Diversity-Promoting
    Objective Function for Neural Conversation Models"): unique n-grams
    divided by total n-grams, pooled across the sample. A low ratio flags a
    templated/boilerplate annotator output -- a known failure mode of
    cheap, low-temperature CoT annotation at scale.

    Parameters
    ----------
    rationales : sequence of str
        Rationale texts (already whitespace-normalized by the caller having
        stripped them; word-splitting here uses plain ``str.split``).

    Returns
    -------
    (int, float)
        ``(total_5grams, distinct_ratio)``. ``(0, 0.0)`` if fewer than 5
        tokens exist across the whole sample.
    """
    grams: list[tuple[str, ...]] = []
    for text in rationales:
        tokens = text.split()
        grams.extend(tuple(tokens[i : i + 5]) for i in range(len(tokens) - 4))
    if not grams:
        return 0, 0.0
    return len(grams), len(set(grams)) / len(grams)


def _percentile(sorted_values: Sequence[float], p: float) -> float:
    """Linear-interpolation percentile of an already-sorted sequence.

    Matches numpy's default (``"linear"``) interpolation method, without
    requiring numpy as a dependency of this offline-data-build script.

    Parameters
    ----------
    sorted_values : sequence of float
        MUST already be sorted ascending; not verified (caller's
        responsibility -- this is an internal helper called only after an
        explicit ``sorted(...)``).
    p : float
        Percentile in ``[0, 100]``.

    Returns
    -------
    float
        ``0.0`` for an empty input.
    """
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = (p / 100.0) * (len(sorted_values) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac


# ---------------------------------------------------------------------------
# Bedrock Converse client (retry/backoff) -- boto3/botocore imported lazily
# ---------------------------------------------------------------------------


class BedrockAnnotator:
    """Thin wrapper over a Bedrock Converse client with retry/backoff.

    Deliberately takes an already-constructed `client` object (duck-typed:
    anything with a ``.converse(**kwargs) -> dict`` method matching the
    Bedrock Runtime Converse response shape) rather than constructing one
    itself -- construction (which needs ``boto3``) lives in the free
    function `build_client`, called only from `main`, so this class -- and
    the whole module -- stays importable, and unit-testable with a plain
    stub, without ``boto3``/``botocore`` installed. The ``botocore``
    exception types needed to classify a failure as retryable are imported
    lazily inside `annotate`'s exception handler (not merely deferred to
    method-call time, but to FAILURE time) -- a stub whose ``.converse``
    never raises drives this class through and through without
    ``botocore`` importable at all.

    Parameters
    ----------
    client : Any
        A Bedrock Runtime client (real or stub) exposing ``.converse``.
    model : str
        The Bedrock model / inference-profile id to call.
    max_tokens : int
        ``inferenceConfig.maxTokens`` for every call.
    max_retries : int
        Maximum number of RETRIES after the first failed attempt (so up to
        ``max_retries + 1`` total attempts) for a retryable failure.
    base_delay_s : float, optional
        Backoff base, in seconds (default 5.0).
    cap_delay_s : float, optional
        Backoff cap, in seconds (default 60.0).
    sleep_fn : callable, optional
        Injected in place of `time.sleep` so tests can exercise the retry
        loop without real wall-clock delay (default `time.sleep`).
    """

    #: Bedrock Converse error codes worth retrying (transient capacity /
    #: rate-limit conditions). Anything else -- including
    #: ``AccessDeniedException`` and ``ValidationException`` -- is treated
    #: as fatal and raised immediately: a bad IAM policy or a malformed
    #: request will not resolve itself by waiting, and burning through the
    #: full retry budget on every one of 8000 rows before failing would be
    #: both slow and (for a paid API) needlessly expensive to discover.
    _RETRYABLE_CODES = frozenset({"ThrottlingException", "ServiceUnavailableException"})

    def __init__(
        self,
        *,
        client,
        model: str,
        max_tokens: int,
        max_retries: int,
        base_delay_s: float = 5.0,
        cap_delay_s: float = 60.0,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.base_delay_s = base_delay_s
        self.cap_delay_s = cap_delay_s
        self._sleep = sleep_fn

    def annotate(self, user_text: str) -> str:
        """Call Converse once (retrying transient failures) for one prompt.

        Parameters
        ----------
        user_text : str
            The full annotation-turn user prompt (see
            `_compose_annotation_prompt`); `ANNOTATION_SYSTEM` travels as
            the call's ``system=`` argument.

        Returns
        -------
        str
            The raw text of the model's first (and only requested) content
            block -- NOT yet stripped/QC-gated; callers handle that.

        Raises
        ------
        Exception
            Whatever the underlying client raises for a non-retryable
            failure (e.g. a ``botocore.exceptions.ClientError`` with a
            fatal code) or once `max_retries` retries of a retryable
            failure are exhausted. Propagated as-is (not wrapped), so a
            caller can still inspect e.g. ``err.response["Error"]["Code"]``.

        Notes
        -----
        Design: exponential backoff, ``delay = min(cap_delay_s, base_delay_s
        * 2**attempt)`` -- 5s, 10s, 20s, 40s, 60s, 60s, ... for the default
        base/cap. No jitter: this client is called from a bounded
        ``--workers``-wide thread pool (not a fleet of independent
        processes), so synchronized retries across workers is a minor,
        acceptable cost against the simplicity of an exact, testable delay
        schedule.

        The ``botocore.exceptions`` import is deferred all the way into the
        ``except`` branch below (not just to this method, as the class
        docstring says) -- so the SUCCESS path never touches ``botocore`` at
        all, and a caller whose stub client never raises can drive this
        method with zero boto3/botocore installed, not merely at import
        time.
        """
        attempt = 0
        while True:
            try:
                response = self.client.converse(
                    modelId=self.model,
                    system=[{"text": ANNOTATION_SYSTEM}],
                    messages=[{"role": "user", "content": [{"text": user_text}]}],
                    inferenceConfig={"temperature": 0.0, "maxTokens": self.max_tokens},
                )
                return response["output"]["message"]["content"][0]["text"]
            except Exception as exc:  # noqa: BLE001 -- reclassified via isinstance just below
                from botocore.exceptions import ClientError, ConnectTimeoutError, EndpointConnectionError, ReadTimeoutError

                if isinstance(exc, ClientError):
                    retryable = exc.response.get("Error", {}).get("Code", "") in self._RETRYABLE_CODES
                elif isinstance(exc, (ConnectTimeoutError, EndpointConnectionError, ReadTimeoutError)):
                    retryable = True
                else:
                    # Not a Bedrock/connection error this client knows how to
                    # classify (e.g. a bug in a test stub, or some other
                    # unrelated failure) -- never retry blindly.
                    raise
                if not retryable or attempt >= self.max_retries:
                    raise
            delay = min(self.cap_delay_s, self.base_delay_s * (2**attempt))
            self._sleep(delay)
            attempt += 1


def build_client(region: str):
    """Construct the real boto3 ``bedrock-runtime`` client.

    The ONLY place in this module that imports ``boto3`` -- called from
    `main` only, so importing this module (or constructing a
    `BedrockAnnotator` around a test stub) never requires ``boto3`` to be
    installed.

    Parameters
    ----------
    region : str
        AWS region to construct the client in.

    Returns
    -------
    Any
        A ``boto3`` ``bedrock-runtime`` client. Credentials are resolved
        through boto3's normal chain (``AWS_PROFILE``, instance role,
        etc.) -- no bearer-token minting needed, unlike the mantle
        Bedrock-inference-profile path used elsewhere in this repo (see
        ``aws_bedrock_eval_auth_and_endpoints`` memory): the Converse API
        is reached directly, not through that gateway.
    """
    import boto3  # deferred: see module docstring

    return boto3.client("bedrock-runtime", region_name=region)


# ---------------------------------------------------------------------------
# Resume support
# ---------------------------------------------------------------------------


def _read_done_keys(out_path: Path) -> set[tuple[Optional[str], Optional[int]]]:
    """Read `out_path`'s existing rows into a resume done-set.

    Parameters
    ----------
    out_path : Path
        The (possibly not-yet-existing) output JSONL.

    Returns
    -------
    set of (str or None, int or None)
        ``(full_name, k)`` of every row already present. Empty if
        `out_path` does not exist yet.
    """
    if not out_path.exists():
        return set()
    done: set[tuple[Optional[str], Optional[int]]] = set()
    with out_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            meta = rec.get("meta", {})
            done.add((meta.get("full_name"), meta.get("k")))
    return done


# ---------------------------------------------------------------------------
# Paired bare-control sibling (see module docstring's Pipeline step 5)
# ---------------------------------------------------------------------------


def _sibling_bare_path(out_path: Path, style: str) -> Path:
    """Derive the paired bare-control sibling path from an annotated `out_path`.

    Replaces the ``style`` segment of `out_path`'s stem with ``"bare"`` --
    e.g. ``cot_stepk1_think_8k.jsonl`` -> ``cot_stepk1_bare_8k.jsonl`` -- per
    the ``cot_stepk1_<style>_<tag>`` naming convention every ``--out``
    (whether the `_default_out` default or an explicit override) is expected
    to follow, since every other package that consumes these files
    (`lean_train_ec2.py`'s ``OPTIONAL_DATASETS``, ``lean_cot_recipe.sh``)
    hard-codes that exact shape as a coordination constant.

    Design: matches on ``style`` as a whole ``"_"``-delimited stem segment
    (via ``.split("_")`` + `list.index`) rather than a fixed positional index
    -- e.g. always "the 3rd segment" -- so the derivation does not silently
    misfire if a caller's ``--out`` override reorders or renames the other
    segments while still containing the style token itself.

    Parameters
    ----------
    out_path : Path
        The (real) ``--out`` path an annotation run wrote/is writing to.
    style : {"think", "fenced"}
        The style this run was invoked with (``args.style``) -- NOT
        re-derived from `out_path`'s name, so this works even if a caller's
        override path happens not to literally spell out the style (as long
        as it does; see Raises).

    Returns
    -------
    Path
        `out_path` with its style segment replaced by ``"bare"`` -- same
        parent directory and suffix.

    Raises
    ------
    ValueError
        If `style` is not one of `out_path`'s stem's ``"_"``-delimited
        segments -- an ``--out`` override that doesn't follow the
        coordination-constant naming convention this whole pairing scheme
        depends on.
    """
    stem_parts = out_path.stem.split("_")
    if style not in stem_parts:
        raise ValueError(
            f"cannot derive a bare-control sibling path from {out_path.name!r}: {style!r} is not "
            "one of its '_'-delimited stem segments (expected the 'cot_stepk1_<style>_<tag>' "
            "naming convention -- see _default_out)"
        )
    stem_parts[stem_parts.index(style)] = "bare"
    return out_path.with_name("_".join(stem_parts) + out_path.suffix)


def _write_bare_sibling(
    out_path: Path,
    *,
    style: str,
    source_rows_by_key: dict[tuple[Optional[str], Optional[int]], dict],
) -> tuple[Path, int]:
    """Write the paired bare-control sibling JSONL for a (possibly partial) run.

    Paired-attribution-control rationale: see the module docstring's
    Pipeline step 5. Concretely, this reads `out_path` FRESH off disk (never
    from any in-memory ``kept``/``done`` structure the caller might be
    holding), in file order, and for each row's ``(meta.full_name, meta.k)``
    key writes the matching ORIGINAL row from `source_rows_by_key` --
    byte-identical ``system``/``user``/``assistant``/``meta`` to what
    ``--dataset`` itself contains for that key, i.e. the row BEFORE any CoT
    annotation. This makes the function naturally RESUME-SAFE: after a
    resumed run, `out_path` already reflects the union of every prior
    invocation's emitted rows plus this run's, so re-deriving from it here
    (rather than tracking "what did THIS invocation add") means the sibling
    always reflects that same union with no extra bookkeeping.

    Parameters
    ----------
    out_path : Path
        The annotated output JSONL to pair against. Read-only. Treated as
        containing zero rows if it does not exist (e.g. every candidate row
        was already done and this invocation annotated nothing new, on a
        FIRST-ever invocation whose subsample was itself empty) -- not an
        error, just an empty sibling.
    style : {"think", "fenced"}
        Forwarded to `_sibling_bare_path`.
    source_rows_by_key : dict[(str or None, int or None), dict]
        Every row of the FULL (pre-subsample) ``--dataset`` file, keyed by
        its own ``(meta.full_name, meta.k)`` identity -- built once by
        `main` via `_load_rows`, so the sibling can be regenerated purely
        from ``--out`` + the current ``--dataset``, without needing to know
        which of ``--dataset``'s rows were selected into any particular
        invocation's subsample.

    Returns
    -------
    (sibling_path, n_written) : (Path, int)
        Where the sibling was written (`_sibling_bare_path`'s result) and
        how many rows it contains (``0`` for an empty/missing `out_path`).

    Raises
    ------
    KeyError
        If `out_path` contains a ``(full_name, k)`` key absent from
        `source_rows_by_key` -- the annotated output and the CURRENT
        ``--dataset`` have drifted out of sync (e.g. ``--dataset`` was
        swapped for a different file between invocations against the same
        ``--out``). Raised rather than silently skipped: silently dropping
        the row here would de-pair the two arms without any record of it.
    ValueError
        Propagated from `_sibling_bare_path` if `style` does not appear in
        `out_path`'s stem.
    """
    sibling_path = _sibling_bare_path(out_path, style)

    keys: list[tuple[Optional[str], Optional[int]]] = []
    if out_path.exists():
        with out_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                meta = rec.get("meta", {})
                keys.append((meta.get("full_name"), meta.get("k")))

    lines_out: list[str] = []
    for key in keys:
        source = source_rows_by_key.get(key)
        if source is None:
            raise KeyError(
                f"annotated row {key!r} in {out_path} has no matching source row in the "
                "current --dataset -- the dataset may have changed since this row was "
                "annotated (dataset / annotated-output mismatch)"
            )
        lines_out.append(json.dumps(source, ensure_ascii=False))

    sibling_path.write_text(("\n".join(lines_out) + "\n") if lines_out else "", encoding="utf-8")
    return sibling_path, len(lines_out)


# ---------------------------------------------------------------------------
# Per-row processing (QC gate -> rationale decontam -> compose)
# ---------------------------------------------------------------------------


def _process_annotation(
    row: dict,
    rationale: str,
    *,
    style: str,
    index: HoldoutIndex,
    max_rationale_chars: int,
) -> tuple[Optional[str], Optional[dict]]:
    """QC-gate, decontam-check, and (if it survives) compose one row.

    Parameters
    ----------
    row : dict
        The source row (``system``/``user``/``assistant``/``meta``); its
        ``assistant`` is the BARE ground-truth tail.
    rationale : str
        The raw annotator response for this row (not yet stripped).
    style : {"think", "fenced"}
        Target composition style; see `compose_target`.
    index : HoldoutIndex
        The eval-holdout content index, for the rationale-content re-check.
    max_rationale_chars : int
        `_qc_gate`'s length cap.

    Returns
    -------
    (str or None, dict or None)
        Exactly one element is non-None: a drop reason string (see
        `_qc_gate` and the ``"rationale_leak_<key>"`` family below), or a
        "kept" info dict with keys ``record`` (the JSONL-ready output row),
        ``rationale`` (stripped text, for the QC report), ``mentions``
        (holdout-name mention count), and ``grounded`` (bool).
    """
    rationale = rationale.strip()
    tail = row["assistant"]

    reason = _qc_gate(rationale, tail, max_rationale_chars=max_rationale_chars)
    if reason is not None:
        return reason, None

    # Content-level decontam of the NEW surface this script introduces: the
    # rationale prose. `states=[rationale]` runs the K3 exact-state check
    # against the whole rationale blob; `statement=rationale` ADDITIONALLY
    # reaches the K2 exact+near-duplicate (MinHash/LSH) family -- which
    # `states=` alone cannot reach (`check` only applies near-dup matching to
    # its `statement=` argument) -- so a rationale that PARAPHRASES (alpha-
    # renames a hypothesis in) a memorized eval statement, not just one that
    # quotes it byte-for-byte, also trips this gate. Still a best-effort
    # catch of an annotator regurgitating a memorized eval state, not an
    # exhaustive substring scan: good enough as a defense against gross
    # memorization leakage, not a formal guarantee.
    hits = index.check(statement=rationale, states=[rationale])
    if hits:
        return f"rationale_leak_{hits[0].key}", None

    # Informational only (never a drop): a rationale legitimately citing an
    # eval-set mathlib lemma as a premise ("by `Nat.add_comm`...") reveals
    # the lemma's existence -- which pretraining on mathlib already does --
    # but not its proof. See `HoldoutIndex.count_name_mentions`'s docstring.
    mentions = index.count_name_mentions(rationale)

    composed = compose_target(style, rationale, tail)
    meta = dict(row.get("meta", {}))
    meta["cot_style"] = style
    if mentions:
        meta["holdout_name_mentions"] = mentions
    record = {"system": row["system"], "user": row["user"], "assistant": composed, "meta": meta}

    grounded = bool(_goal_identifiers(row["user"]) & set(_IDENT_TOKEN_RE.findall(rationale)))
    kept_info = {"record": record, "rationale": rationale, "mentions": mentions, "grounded": grounded}
    return None, kept_info


# ---------------------------------------------------------------------------
# The annotation loop
# ---------------------------------------------------------------------------


def _run_annotation(
    rows: Sequence[dict],
    *,
    annotator: BedrockAnnotator,
    index: HoldoutIndex,
    style: str,
    max_rationale_chars: int,
    workers: int,
    out_path: Path,
    done: set,
) -> tuple[int, int, int, dict, list[dict], Optional[str]]:
    """Run the concurrent annotate -> QC -> compose -> append-write loop.

    Design: the `concurrent.futures.ThreadPoolExecutor` wraps ONLY the
    network call (`annotator.annotate`) -- the slow, I/O-bound part.
    Everything else (QC gates, the rationale decontam re-check, composing
    the target, and the file write) runs back in the single main thread as
    futures complete via `as_completed`, mirroring
    `smolbench.deduction.lean.runner`'s concurrent-cell loop (same
    write-lock/print-lock idiom). This means `write_lock`/`print_lock`
    below are technically uncontended today (only the main thread ever
    holds them) -- kept anyway both to match that precedent and as a
    safety net against a future refactor that moves work into the worker
    threads.

    A fatal (non-retryable, or retry-exhausted) `annotator.annotate` error
    is NOT retried further or converted into a per-row drop reason: it
    aborts the loop immediately (cancelling any still-pending futures) and
    is returned as `abort_error`, rather than raised, so the caller can
    still write a manifest/QC report describing the partial progress made
    before the abort. Rows this invocation never got to remain absent from
    `out_path` and will be re-attempted (they are not in the resume
    done-set, which is built only from rows that were actually written) on
    the next invocation of the same command.

    Parameters
    ----------
    rows : sequence of dict
        The (already subsampled) candidate rows for this invocation.
    annotator : BedrockAnnotator
        The client wrapper to call per row.
    style : {"think", "fenced"}
    max_rationale_chars : int
    workers : int
        Thread-pool width.
    out_path : Path
        Output JSONL; opened in append mode.
    done : set of (str or None, int or None)
        Resume done-set (see `_read_done_keys`); rows whose ``(full_name,
        k)`` is in this set are skipped without calling the annotator.

    Returns
    -------
    (n_completed, n_emitted, n_skipped, drop_reasons, kept, abort_error)
        ``n_completed`` counts rows whose annotate call returned AND were
        QC-processed this invocation (kept or dropped); ``n_emitted``
        counts the kept subset; ``n_skipped`` counts rows already in
        `done`; `drop_reasons` maps drop reason -> count; `kept` is the
        list of "kept" info dicts from `_process_annotation` (needed by the
        caller to build the QC report); `abort_error` is None on a clean
        run or a description of the fatal failure otherwise.
    """
    write_lock = threading.Lock()
    print_lock = threading.Lock()
    drop_reasons: dict[str, int] = {}
    kept: list[dict] = []
    n_emitted = 0
    n_completed = 0
    abort_error: Optional[str] = None

    to_process = [r for r in rows if (r["meta"].get("full_name"), r["meta"].get("k")) not in done]
    n_skipped = len(rows) - len(to_process)
    if not to_process:
        return 0, 0, n_skipped, drop_reasons, kept, None

    with out_path.open("a", encoding="utf-8") as f:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, len(to_process)))
        try:
            future_to_row = {
                executor.submit(annotator.annotate, _compose_annotation_prompt(r["user"], r["assistant"])): r
                for r in to_process
            }
            for fut in concurrent.futures.as_completed(future_to_row):
                row = future_to_row[fut]
                try:
                    rationale = fut.result()
                except Exception as exc:  # noqa: BLE001 -- any exhausted/fatal annotate() error aborts the run
                    name = row["meta"].get("full_name")
                    k = row["meta"].get("k")
                    abort_error = f"{name} k={k}: {type(exc).__name__}: {exc}"
                    for other in future_to_row:
                        other.cancel()
                    break

                n_completed += 1
                reason, kept_info = _process_annotation(
                    row, rationale, style=style, index=index, max_rationale_chars=max_rationale_chars
                )
                if reason is not None:
                    drop_reasons[reason] = drop_reasons.get(reason, 0) + 1
                else:
                    with write_lock:
                        f.write(json.dumps(kept_info["record"], ensure_ascii=False) + "\n")
                        f.flush()
                    kept.append(kept_info)
                    n_emitted += 1

                if n_completed % 100 == 0:
                    with print_lock:
                        print(
                            f"  [{n_completed}/{len(to_process)}] emitted={n_emitted} "
                            f"dropped={n_completed - n_emitted}",
                            flush=True,
                        )
        finally:
            # wait=False + cancel_futures: don't block shutdown on threads
            # for rows we're abandoning anyway (matches
            # smolbench.deduction.lean.runner's concurrent-cell teardown).
            executor.shutdown(wait=False, cancel_futures=True)

    return n_completed, n_emitted, n_skipped, drop_reasons, kept, abort_error


# ---------------------------------------------------------------------------
# Manifest + QC report
# ---------------------------------------------------------------------------


def _write_json_atomic(path: Path, obj: dict) -> None:
    """Write `obj` as indented JSON to `path`, atomically (tmp + replace)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _count_lines(path: Path) -> int:
    """Count non-blank lines of `path` (0 if it does not exist)."""
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _build_manifest(
    args: argparse.Namespace,
    *,
    index: HoldoutIndex,
    n_subsample: int,
    n_completed: int,
    n_emitted: int,
    n_skipped: int,
    drop_reasons: dict,
    kept: list,
    abort_error: Optional[str],
    bare_sibling_path: Path,
    bare_sibling_rows: int,
) -> dict:
    """Assemble the ``<out>.manifest.json`` document.

    Scope note: ``stats`` describe THIS INVOCATION's newly-attempted rows
    only (a resumed run's manifest does not retroactively recompute stats
    for rows an earlier invocation already wrote) -- ``total_rows_in_out``
    is the one cumulative figure, read directly off the final output file.
    ``bare_sibling`` is likewise a CUMULATIVE figure (see
    `_write_bare_sibling`'s docstring: it always regenerates from `args.out`'s
    full current content), not a per-invocation delta.

    Parameters
    ----------
    bare_sibling_path : Path
        `_write_bare_sibling`'s returned sibling path -- recorded so a
        manifest reader can find the paired bare-control file without
        re-deriving `_sibling_bare_path` by hand.
    bare_sibling_rows : int
        `_write_bare_sibling`'s returned row count.
    """
    mention_rows = sum(1 for k in kept if k["mentions"])
    mention_total = sum(k["mentions"] for k in kept)
    return {
        "config": {
            "dataset": str(args.dataset),
            "style": args.style,
            "limit": args.limit,
            "seed": args.seed,
            "model": args.model,
            "region": args.region,
            "max_annotation_tokens": args.max_annotation_tokens,
            "max_retries": args.max_retries,
            "max_rationale_chars": args.max_rationale_chars,
            "workers": args.workers,
            "prompt_template_sha256": _TEMPLATE_SHA256,
        },
        "stats": {
            "subsample_size": n_subsample,
            "already_done_skipped": n_skipped,
            "processed_this_run": n_completed,
            "emitted_this_run": n_emitted,
            "dropped_this_run_total": sum(drop_reasons.values()),
            "dropped_this_run": dict(sorted(drop_reasons.items())),
            "holdout_name_mention_rows_this_run": mention_rows,
            "holdout_name_mentions_total_this_run": mention_total,
            "total_rows_in_out": _count_lines(args.out),
        },
        "decontamination": {
            "holdout_size": len(index.names),
            "holdout_fingerprint": _fingerprint(index.names),
            "index": index.stats(),
            "preflight_bare_facet_rescan": "passed",
        },
        "aborted": abort_error is not None,
        "abort_error": abort_error,
        "output_jsonl": args.out.name,
        "bare_sibling": {
            "path": bare_sibling_path.name,
            "rows": bare_sibling_rows,
        },
    }


def _build_qc_report(args: argparse.Namespace, *, kept: list[dict], drop_reasons: dict) -> dict:
    """Assemble the ``<out>.qc.json`` document.

    Scope note: like `_build_manifest`, covers this invocation's newly-KEPT
    rows only.
    """
    lengths = sorted(len(k["rationale"]) for k in kept)

    def _ngram_sample_key(k: dict) -> int:
        meta = k["record"]["meta"]
        return _priority(args.seed, "cot5gram", meta.get("full_name"), meta.get("k"))

    ngram_sample_rows = sorted(kept, key=_ngram_sample_key)[:1000]
    n_5grams, distinct_ratio = _distinct_5gram_ratio([k["rationale"] for k in ngram_sample_rows])
    grounded = sum(1 for k in kept if k["grounded"])
    mention_rows = sum(1 for k in kept if k["mentions"])
    mention_total = sum(k["mentions"] for k in kept)

    return {
        "config": {"style": args.style, "seed": args.seed},
        "kept_this_run": len(kept),
        "rationale_length_chars": {
            "min": lengths[0] if lengths else 0,
            "p10": _percentile(lengths, 10),
            "p25": _percentile(lengths, 25),
            "p50": _percentile(lengths, 50),
            "p75": _percentile(lengths, 75),
            "p90": _percentile(lengths, 90),
            "p99": _percentile(lengths, 99),
            "max": lengths[-1] if lengths else 0,
            "mean": (sum(lengths) / len(lengths)) if lengths else 0.0,
        },
        "distinct_5gram_ratio": {
            "sample_size": len(ngram_sample_rows),
            "total_5grams": n_5grams,
            "ratio": distinct_ratio,
        },
        "grounding_rate": {
            "grounded": grounded,
            "total": len(kept),
            "rate": (grounded / len(kept)) if kept else 0.0,
        },
        "holdout_name_mentions": {"rows": mention_rows, "total": mention_total},
        "drop_histogram": dict(sorted(drop_reasons.items())),
    }


# ---------------------------------------------------------------------------
# --dry-run
# ---------------------------------------------------------------------------


def _print_dry_run(sample_rows: Sequence[dict], style: str) -> None:
    """Print composed annotation prompts + one sample composed target.

    Constructs NO AWS client and makes NO network call -- see `main`.

    Parameters
    ----------
    sample_rows : sequence of dict
        Up to 5 rows (per the CLI contract) to preview.
    style : {"think", "fenced"}
        Style to preview `compose_target` with.
    """
    print(f"--dry-run: previewing {len(sample_rows)} row(s); no AWS client constructed, no network call made.\n")
    for i, row in enumerate(sample_rows):
        meta = row.get("meta", {})
        prompt_text = _compose_annotation_prompt(row["user"], row["assistant"])
        print(f"--- row {i} ({meta.get('full_name')}, k={meta.get('k')}) ---")
        print(f"[system]\n{ANNOTATION_SYSTEM}\n")
        print(f"[user]\n{prompt_text}\n")
    if sample_rows:
        placeholder = (
            "This is a PLACEHOLDER rationale for --dry-run -- no LLM call was made. A real "
            "run replaces this paragraph with Claude's generated reasoning about the goal "
            "shape, the relevant hypotheses, and why each tactic below applies."
        )
        sample_target = compose_target(style, placeholder, sample_rows[0]["assistant"])
        print(f"--- SAMPLE composed target (style={style}) ---\n{sample_target}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _default_out(style: str, limit: int) -> Path:
    """Default ``--out`` path, per the coordination-constants naming rule.

    ``limit==8000`` -> ``..._8k.jsonl`` (the smoke-size default);
    ``limit==0`` -> ``..._full.jsonl``; anything else -> the literal count.
    """
    if limit == 8000:
        tag = "8k"
    elif limit == 0:
        tag = "full"
    else:
        tag = str(limit)
    return _DATA_SFT / f"cot_stepk1_{style}_{tag}.jsonl"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", type=Path, default=_DEFAULT_DATASET, help="source SFT JSONL (bare-tail rows)")
    # NOTE: defaults to "think" (not required) so the acceptance smoke
    # `annotate_lean_cot.py --dry-run --limit 5` (no --style given) works --
    # the coordination constants list both think sizes (8k, full) but only
    # fenced_full, i.e. "think" is the primary style for the Qwen sweep arm.
    p.add_argument("--style", default="think", choices=_STYLES, help="CoT wrapper convention")
    p.add_argument("--out", type=Path, default=None, help="output JSONL (default: per --style/--limit)")
    p.add_argument("--limit", type=int, default=8000, help="rows to annotate; 0 = all")
    p.add_argument("--seed", type=int, default=1776, help="subsample + QC-sample seed")
    p.add_argument("--model", default=_DEFAULT_MODEL, help="Bedrock model/inference-profile id")
    p.add_argument("--region", default="us-west-2", help="AWS region for the bedrock-runtime client")
    p.add_argument("--max-annotation-tokens", type=int, default=700, help="Converse inferenceConfig.maxTokens")
    p.add_argument("--max-retries", type=int, default=6, help="retries after the first failed attempt")
    p.add_argument("--max-rationale-chars", type=int, default=2500, help="QC length-cap gate")
    p.add_argument("--workers", type=int, default=8, help="concurrent annotation calls")
    p.add_argument("--dry-run", action="store_true", help="preview prompts/targets; no AWS client, no network")
    p.add_argument(
        "--judge-sample",
        type=int,
        default=0,
        help="RESERVED: LLM-judge faithfulness pass over N rows -- not implemented in round 1",
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.judge_sample:
        print(
            "--judge-sample: not implemented in round 1 (reserved for the LLM-judge "
            "faithfulness pass, to be run live later over a 200-500 row sample)",
            file=sys.stderr,
        )
        return 1

    if args.out is None:
        args.out = _default_out(args.style, args.limit)

    # CI boxes may not have the (large, gitignored) bootstrapped dataset --
    # skip gracefully (exit 0) rather than erroring, so an offline smoke
    # check of this script's plumbing doesn't require the full data bootstrap.
    # NOTE: this deliberately differs from build_lean_synth_sft.py's stricter
    # "missing source -> exit 1" convention -- see the shared task spec's
    # explicit "skip gracefully" instruction for THIS script.
    if not args.dataset.exists():
        print(
            f"note: dataset {args.dataset} not found -- skipping (offline/CI box without the "
            "data bootstrap; see notebooks/lean/README.md)",
            file=sys.stderr,
        )
        return 0

    rows = _load_rows(args.dataset)
    working = _select_subsample(rows, seed=args.seed, limit=args.limit)

    if args.dry_run:
        _print_dry_run(working[:5], args.style)
        return 0

    index = HoldoutIndex.build()
    _preflight_bare_facet_check(working, index)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    done = _read_done_keys(args.out)

    client = build_client(args.region)
    annotator = BedrockAnnotator(
        client=client, model=args.model, max_tokens=args.max_annotation_tokens, max_retries=args.max_retries
    )

    n_completed, n_emitted, n_skipped, drop_reasons, kept, abort_error = _run_annotation(
        working,
        annotator=annotator,
        index=index,
        style=args.style,
        max_rationale_chars=args.max_rationale_chars,
        workers=args.workers,
        out_path=args.out,
        done=done,
    )

    # Paired bare-control sibling (Fix 1 / module docstring Pipeline step
    # 5): keyed off the FULL --dataset (every row, not just this
    # invocation's `working` subsample), since a resumed run's --out can
    # contain rows selected by an EARLIER invocation's subsample too.
    # Regenerated unconditionally here (whether this invocation emitted
    # anything new or was entirely a resume-skip, and even if it aborted
    # partway through) so it always reflects args.out's current on-disk
    # content -- see _write_bare_sibling's docstring.
    source_rows_by_key = {(r["meta"].get("full_name"), r["meta"].get("k")): r for r in rows}
    bare_sibling_path, n_bare_sibling = _write_bare_sibling(
        args.out, style=args.style, source_rows_by_key=source_rows_by_key
    )

    manifest = _build_manifest(
        args,
        index=index,
        n_subsample=len(working),
        n_completed=n_completed,
        n_emitted=n_emitted,
        n_skipped=n_skipped,
        drop_reasons=drop_reasons,
        kept=kept,
        abort_error=abort_error,
        bare_sibling_path=bare_sibling_path,
        bare_sibling_rows=n_bare_sibling,
    )
    manifest_path = args.out.with_name(args.out.stem + ".manifest.json")
    _write_json_atomic(manifest_path, manifest)

    qc_report = _build_qc_report(args, kept=kept, drop_reasons=drop_reasons)
    qc_path = args.out.with_name(args.out.stem + ".qc.json")
    _write_json_atomic(qc_path, qc_report)

    if abort_error:
        print(f"FATAL: annotation aborted: {abort_error}", file=sys.stderr)
        print(f"partial progress: emitted {n_emitted}, dropped {sum(drop_reasons.values())} this run", file=sys.stderr)
        print(
            f"manifest -> {manifest_path}\nqc report -> {qc_path}\n"
            f"bare sibling -> {bare_sibling_path} ({n_bare_sibling} rows)",
            file=sys.stderr,
        )
        return 1

    print(
        f"[{args.style}] subsample {len(working)} ({n_skipped} already done) -> "
        f"processed {n_completed}: {sum(drop_reasons.values())} dropped {drop_reasons}, "
        f"{n_emitted} emitted\n-> {args.out}\nmanifest -> {manifest_path}\nqc report -> {qc_path}\n"
        f"bare sibling -> {bare_sibling_path} ({n_bare_sibling} rows)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
