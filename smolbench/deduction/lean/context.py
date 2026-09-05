"""Render context rungs along the `stepk`, `hint`, and `noise` chains.

- `stepk:0..2` adds *step-k* information with no answer-conditional content;
  cumulative (`stepk:n` includes `stepk:0..n-1`).
- `hint:0..4` adds *answer-conditional* detail about the premises the *true*
  next tactic uses; cumulative, on a `stepk:2` baseline.
- `noise:N` is `hint:(N-1)` whitespace-padded to `hint:N`'s exact token
  count IN THE FULL PROMPT the model receives (`prompt.build_user_prompt`,
  i.e. this rung's context plus the fixed instruction suffix) — the length
  control for the hint chain. Matched on the prompt, not the bare context,
  because equal-token CONTEXTS do not imply equal-token PROMPTS: the
  instruction suffix's own token cost depends on what precedes it (BPE merges
  across that boundary), so a context-only match can be one token short of
  its `hint:N` twin in the only text that matters. See `_render_noise_parts`'s
  docstring for the measured example (28 vs. 27 suffix tokens).

`stepk:*` and `hint:0` build from a `BenchmarkTheorem` alone; `hint:1+` needs
a premise-body lookup against the premise corpus (see `.premises`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .corpus import BenchmarkTheorem

Chain = Literal["stepk", "hint", "noise"]

# `_MAX_LEVEL` bounds `validate`'s (chain, level) range check, per chain:
#
# - "stepk" caps at 2: `_render_stepk_parts` defines only 0 (bare goal),
#   1 (+ full tactic state), 2 (+ proof-so-far + theorem identity).
# - "hint" caps at 9: `_render_hint_parts` defines 0 (premise names), 1
#   (+ signatures), 2 (+ full bodies with proofs), and 3+ as a transitive
#   premise-dependency closure of `level - 2` hops (hint:3 = 1-hop ...
#   hint:9 = 7-hop). Deliberately past the hint:0..4 range
#   `notebooks/deduction/README.md` documents and sweep-tests, so `validate`
#   is a real bound and not a pin on the levels currently in use: deeper
#   hops only truncate earlier, since `_HINT2_3_TOKEN_CAP` (50k tokens)
#   bounds the rendered text however far the closure walks.
# - "noise" caps at 9 to mirror "hint": `_render_noise_parts(level)`
#   renders `_render_hint_parts` at both `level - 1` and `level`.
_MAX_LEVEL: dict[str, int] = {"stepk": 2, "hint": 9, "noise": 9}


# ---------------------------------------------------------------------------
# Goal-state parsing
# ---------------------------------------------------------------------------


def split_state(state_pp: str) -> tuple[str, str]:
    """Return `(hypotheses, goals)` from a Lean tactic-state pretty-print.

    `goals` starts at the first `⊢` line, with any preceding `case ...`
    headers attached. A state with no `⊢` line yields `(state_pp, "")`.
    """
    lines = state_pp.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("⊢"):
            goal_start = i
            while goal_start > 0 and lines[goal_start - 1].lstrip().startswith("case "):
                goal_start -= 1
            return "\n".join(lines[:goal_start]).rstrip(), "\n".join(lines[goal_start:]).rstrip()
    return state_pp.rstrip(), ""


def extract_goal_only(state_pp: str) -> str:
    """`stepk:0` helper: drop hypotheses, keep every goal's `case ...`/`⊢` lines.

    A tactic state can carry MULTIPLE goals at once -- the normal shape right
    after a branching tactic (`cases`, `constructor`, `rcases`, ...) -- each
    rendered as an optional `case ...` header, that goal's own hypothesis
    lines, and a `⊢ ...` goal line. `split_state` only locates the FIRST `⊢`,
    which is exactly right for its own callers (`_render_stepk_parts`'s
    `stepk:1` full-state dump wants everything; `is_trivial_rung`'s
    `stepk:1` check wants only the first goal's hypotheses, to match what
    `stepk:0` withholds), but is the wrong tool here: naively keeping
    everything from the first `⊢` onward would pass every LATER goal's
    hypotheses straight through, unfiltered, into the very rung defined to
    drop them. This function instead walks every line and keeps `case ...`
    headers and `⊢ ...` goal lines across ALL goals, and drops every
    hypothesis line, however many goals the state has.

    Continuation lines
    ------------------
    Lean line-wraps a long `⊢ ...` goal onto following lines, and those
    continuation lines are indented relative to the `⊢` itself (which, like
    every hypothesis and `case ...` header, starts at column 0). That
    indentation is the only signal available here to tell a wrapped goal
    continuation apart from the next goal's hypotheses -- both are plain
    text with no leading marker -- so: once a `⊢` line is kept, any
    immediately following line that is still indented and non-blank is
    treated as part of that same goal and kept too; the first unindented
    line ends it (reclassified normally as a blank separator, a new
    `case ...` header, a new `⊢` line, or a hypothesis line to drop).

    Parameters
    ----------
    state_pp : str
        A Lean tactic-state pretty-print (`TracedTactic.state_before`).

    Returns
    -------
    str
        `state_pp` with every hypothesis line removed, keeping `case ...`
        headers, `⊢ ...` goal lines, their wrapped continuations, and the
        blank lines that separate goals -- rstripped. If `state_pp` has no
        `⊢` line at all (already closed, or unparseable), it is returned
        completely UNCHANGED (not even rstripped), matching this function's
        prior behaviour of falling back to `state_pp` in that case.
    """
    lines = state_pp.splitlines()
    if not any(line.lstrip().startswith("⊢") for line in lines):
        return state_pp

    kept: list[str] = []
    in_goal = False  # True while consuming a just-kept `⊢` line's wrapped continuation.
    for line in lines:
        stripped = line.lstrip()
        if in_goal and stripped and line != stripped:
            # Indented and non-blank: a continuation of the previous `⊢` line.
            kept.append(line)
            continue
        in_goal = False
        if stripped.startswith("case ") or stripped.startswith("⊢"):
            kept.append(line)
            in_goal = stripped.startswith("⊢")
            continue
        if not stripped:
            # Blank separator between goals -- keep at most one, and never
            # leading, so dropped hypotheses don't leave behind a run of
            # blank lines or an empty line at the very start.
            if kept and kept[-1] != "":
                kept.append("")
            continue
        # Anything else is a hypothesis line: drop it.
    return "\n".join(kept).rstrip()


# ---------------------------------------------------------------------------
# Rendered context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RenderedContext:
    """One rendered (chain, level) context rung.

    Returned by `render`; `prompt.build_user_prompt` consumes `text`, and every
    result row records `label` as the cell's ``rung``.
    """

    chain: Chain
    level: int
    #: Prompt-context text: the chain-specific parts, blank-line-joined by
    #: `render`.
    text: str

    @property
    def label(self) -> str:
        """This rung's canonical ``"<chain>:<level>"`` identifier, e.g. ``"hint:2"``.

        The single ``":"`` is a wire contract: `cli.py`'s ``--rung`` and
        `runner.py`'s sweep-config ``rungs`` split on it to recover
        ``(chain, level)``; `runner.slug_rung` swaps it for ``"-"`` in paths.
        """
        return f"{self.chain}:{self.level}"


# ---------------------------------------------------------------------------
# Per-chain rendering (cumulative within each chain)
# ---------------------------------------------------------------------------


def _render_stepk_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """Cumulative `stepk:0..level`, for `level` in {0,1,2}."""
    tt = theorem.traced_tactics[k]
    parts: list[str] = [
        f"## Current goal\n```\n{extract_goal_only(tt.state_before)}\n```"
    ]
    if level >= 1:
        parts.append(f"## Full tactic state\n```\n{tt.state_before}\n```")
    if level >= 2:
        prior = theorem.traced_tactics[:k]
        if prior:
            tactics_block = "\n".join(t.tactic for t in prior)
            label = f"{k} tactic{'s' if k != 1 else ''}"
            parts.append(f"## Proof so far ({label})\n```lean\n{tactics_block}\n```")
        else:
            parts.append(
                "## Proof so far\n_(no tactics applied yet — this is the start of the proof)_"
            )
        parts.append(
            f"## Theorem\n`{theorem.full_name}` in `{theorem.file_path}`"
        )
    return parts


_HINT2_3_TOKEN_CAP = 50_000  # token budget for transitive closure rendering


# ---------------------------------------------------------------------------
# Noise (whitespace) padding — control arm for hint:3 / hint:4
# ---------------------------------------------------------------------------


def _count_tokens(s: str) -> int:
    """Token count of `s`: `tiktoken` ``cl100k_base``, else ``len(s) // 4``.

    A graceful-degrade counter for BUDGET-style measurements, where an
    approximation is an acceptable price for never raising just because
    `tiktoken` is missing: `_render_hint_parts`'s hint:3+ transitive-closure
    cap applies this exact tiktoken-or-``len(s) // 4`` policy inline (its own
    local ``tok()``, not a call to this function, but the same fallback
    contract), and `is_trivial_rung`'s non-``noise`` branches size their
    checks the same tolerant way. Outside this module, `cli.py` and
    `tests/deduction/test_s3_archive.py` call this directly for the same
    reason.

    Design: the ``noise`` chain does NOT use this counter -- see
    `_render_noise_parts` and `is_trivial_rung`'s ``noise`` branch, both of
    which use `smolbench.evals.tokenization.TiktokenTokenizer` instead. A
    rough count is fine for a 50k-token BUDGET (missing the cap by a few
    tokens changes nothing about correctness); it is fatal for an EXACT
    length control, where a wrong count would silently reintroduce the very
    confound the control exists to remove. Two different tolerances for two
    different jobs, not an oversight.
    """
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(s))
    except Exception:  # noqa: BLE001
        return len(s) // 4


def _as_full_prompt(level: int, text: str) -> str:
    """Wrap noise-chain context `text` as the FULL prompt the model receives.

    `_render_noise_parts` and `is_trivial_rung`'s ``noise`` branch must
    measure and pad against IDENTICAL text -- the actual prompt, not the bare
    context -- or the two could disagree about which rungs are trivial and
    which pad lengths are exact (see both callers' Notes). Centralizing the
    ``RenderedContext`` construction and the lazy `prompt` import here is what
    keeps that in lockstep: there is exactly one place that decides "what does
    the model see", and both callers go through it.

    Parameters
    ----------
    level : int
        This rung's ``noise`` level, threaded through only to build an honest
        `RenderedContext` (`prompt.build_user_prompt` reads only `.text`, but
        a real object is cheaper to explain than a dummy with placeholder
        metadata).
    text : str
        Context text to wrap -- a `hint:N` rendering, or that rendering with a
        whitespace pad appended.

    Returns
    -------
    str
        ``prompt.build_user_prompt(RenderedContext(chain="noise", level=level, text=text))``.

    Notes
    -----
    The import is LAZY: `.prompt` does ``from .context import RenderedContext``
    at module scope, so importing it at THIS module's top level would be a
    cycle. `runner.py` imports `context` at top level, so the cycle would bite
    on every run, not just tests.
    """
    from . import prompt as _prompt
    return _prompt.build_user_prompt(RenderedContext(chain="noise", level=level, text=text))


def _render_noise_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """`noise:N` = `hint:(N-1)` whitespace-padded to `hint:N`'s exact PROMPT token count.

    The length control for the hint chain: both rungs cost identical tokens IN
    THE PROMPT THE MODEL RECEIVES, so only `hint:N`'s marginal *content*
    differs. Matched on `prompt.build_user_prompt`'s output, not on the bare
    context text: the model is sent this rung's context text followed by a
    fixed instruction suffix (`prompt.build_user_prompt` -- see `prompt.py`
    for the exact suffix; not reproduced here, so this docstring cannot drift
    from it), and that suffix's OWN token cost is not constant -- it depends
    on what precedes it, since BPE merges across the context/suffix boundary.
    Concretely, under `cl100k_base` with the pad unit `choose_whitespace_unit`
    picks (``" \\t"``, ~1 token/rep), the suffix costs 28 tokens after most
    pad lengths but 27 after a two-unit pad:
    matching on context tokens alone can land exactly on the `hint:N` context
    count while shipping a prompt one token SHORT of it -- reintroducing, in
    the one text that matters, the exact length confound this rung exists to
    remove. Matching on the full prompt closes that gap by construction.

    The pad is appended to the LAST part's text, never as a new list element —
    `render()` joins parts with ``"\\n\\n"``, and a new element would add a
    separator the token search never measured. A baseline already equal to
    the target (a trivial rung, see `is_trivial_rung`) returns unchanged:
    `render()` still calls this under ``skip_trivial: false``, so that case
    must not raise.

    Raises
    ------
    ValueError
        `level < 1` (the `hint:0`/`stepk:2` baseline has no noise counterpart);
        the `hint:(level - 1)` baseline's PROMPT is LONGER in tokens than the
        `hint:level` target's PROMPT, since whitespace can only grow a
        rendering and under-padding would reintroduce the length confound;
        `choose_whitespace_unit` finds no unit costing ~1 token per repetition
        under `TiktokenTokenizer`; the pad search misses the target; or the
        recovered pad does not reconstruct the padded prompt structurally
        (see the reconstruction check below).
    ImportError
        `tiktoken` is not installed (`TiktokenTokenizer`'s constructor raises
        rather than degrading -- see `_count_tokens`'s Design note on why the
        noise chain, unlike the hint:3+ budget, cannot tolerate a fallback).

    Notes
    -----
    The pad search is `smolbench.induction._common.token_matched_noise_prompt`,
    reused so the two benchmarks' padding cannot drift apart; its import is
    LAZY because that module pulls in `numpy`/`ordered_set`/`smolbench.evals`
    and `runner.py` imports this module at top level. `TiktokenTokenizer`
    (`smolbench.evals.tokenization`) is imported the same way and for the same
    reason -- both are one hop further than `smolbench.evals` alone, which the
    lazy `token_matched_noise_prompt` import already pulls in, so importing
    the tokenizer lazily too adds no new cost, only avoids paying it at
    `runner.py`'s top-level `import context`. The pad is pure whitespace —
    prose or a header would be content the paired `hint:N` rung lacks.

    The exactness re-check below is NOT redundant with
    `token_matched_noise_prompt`'s own internal verification: it re-derives
    the pad from the helper's returned PROMPT by slicing out the instruction
    suffix (`build_user_prompt` never appears twice, so the suffix length must
    be measured, not hardcoded -- see `suffix_len` below), and then re-renders
    that recovered pad through `_as_full_prompt` to confirm the slice actually
    recovered it. That second render is cheap insurance: `suffix_len` is
    computed as a total ``len(prompt) - len(text)`` difference, so if
    `build_user_prompt` ever grew a PREFIX (not just its current fixed
    suffix), the slice below would silently mis-locate the pad instead of
    raising -- this reconstruction check is what would catch that.
    """
    if level < 1:
        raise ValueError(f"noise:{level} not defined; only noise:1+ supported")

    # Lazy imports -- see this function's Notes.
    from smolbench.induction._common import choose_whitespace_unit, token_matched_noise_prompt
    from smolbench.evals.tokenization import TiktokenTokenizer

    base_parts = _render_hint_parts(theorem, k, level - 1)
    base_text = "\n\n".join(base_parts)
    base_prompt = _as_full_prompt(level, base_text)

    target_text = "\n\n".join(_render_hint_parts(theorem, k, level))
    target_prompt = _as_full_prompt(level, target_text)

    # One tokenizer instance for every measurement in this call -- cheap to
    # build, but there is no reason to re-load the encoding per count.
    tokenizer = TiktokenTokenizer()
    base_tokens = tokenizer.count(base_prompt)
    target_tokens = tokenizer.count(target_prompt)

    if base_tokens > target_tokens:
        raise ValueError(
            f"noise:{level} baseline (hint:{level - 1}, {base_tokens} PROMPT "
            f"tokens) is LONGER than its hint:{level} target ({target_tokens} "
            f"PROMPT tokens) for {theorem.full_name!r} at k={k} -- a "
            "whitespace pad can only grow a rendering, never shrink one, so "
            "this rung cannot be built as a length control"
        )
    if base_tokens == target_tokens:
        # Already exact: nothing to pad. Common -- every rung where
        # hint:level adds nothing over hint:(level - 1) lands here, and
        # `render()` still calls this on such rungs under
        # `skip_trivial: false`, so it must return cleanly, not raise.
        return base_parts

    padded_prompt = token_matched_noise_prompt(
        # render: pad string -> the FULL prompt with that pad appended to the
        # context, not the bare context -- see this function's docstring for
        # why matching on context tokens alone under-counts the confound.
        lambda pad: _as_full_prompt(level, base_text + pad),
        "",  # context: empty -- the pad IS the whole variable part being searched
        target_tokens,
        tokenizer,
        unit=choose_whitespace_unit(tokenizer),
    )

    # Verify exactness here rather than trusting the helper (see Notes).
    padded_tokens = tokenizer.count(padded_prompt)
    if padded_tokens != target_tokens:
        raise ValueError(
            f"noise:{level} padding for {theorem.full_name!r} at k={k} did not "
            f"hit the exact target: got {padded_tokens} PROMPT tokens, wanted "
            f"{target_tokens}"
        )

    # Recover the pad structurally: `padded_prompt` is
    # `base_text + pad + <fixed instruction suffix>`, and the suffix's length
    # is derived from `base_prompt` itself, never hardcoded from `prompt.py`'s
    # own suffix-building expression -- copying that literal into this module
    # is exactly the drift this fix closes.
    suffix_len = len(base_prompt) - len(base_text)
    pad = padded_prompt[len(base_text): len(padded_prompt) - suffix_len]

    # Verify the reconstruction (see Notes) rather than trusting the slice.
    reconstructed = _as_full_prompt(level, base_text + pad)
    if reconstructed != padded_prompt:
        raise ValueError(
            f"noise:{level} pad recovery for {theorem.full_name!r} at k={k} "
            "did not reconstruct the padded prompt: slicing the instruction "
            "suffix off the helper's returned prompt produced a pad that, "
            "re-rendered, does not reproduce that prompt byte-for-byte"
        )

    return base_parts[:-1] + [base_parts[-1] + pad]


def _render_hint_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """`hint:0..level` on a `stepk:2` baseline; `level` 0..9, sweep-tested 0..4."""
    parts = _render_stepk_parts(theorem, k, 2)

    tt = theorem.traced_tactics[k]
    names = [p["full_name"] for p in tt.premises]

    # hint:0 — bare premise names
    if names:
        block = "\n".join(f"- `{n}`" for n in names)
        parts.append(f"## Premises used in the next tactic\n{block}")
    else:
        parts.append("## Premises used in the next tactic\n_(none recorded)_")

    if level >= 1:
        from .premises import lookup, signature
        sigs: list[str] = []
        for n in names:
            p = lookup(n)
            if p is None:
                sigs.append(f"### `{n}`\n_(not found in premise corpus)_")
            else:
                sigs.append(
                    f"### `{n}` ({p.kind})\n```lean\n{signature(p)}\n```"
                )
        if sigs:
            parts.append("## Premise signatures\n" + "\n\n".join(sigs))

    if level >= 2:
        # 13-09: `body_with_proof` silently falls back to the corpus's stored
        # `Premise.code` (a signature, usually with no proof body) whenever
        # `premises.slice_full_decl` can't find a traced-repo source slice --
        # true on any box without `premises._traced_root()` (CI, an analysis
        # box). The heading must say which one this block actually rendered:
        # `has_full_source` re-answers that per premise (cheap -- backed by
        # the same `lru_cache`d `slice_full_decl` `body_with_proof` already
        # called), and the SECTION heading is decided from whether ANY
        # premise in it got a real slice, with individual entries that fell
        # back marked inline so a mixed block (some real, some fallback) is
        # not misread as uniformly one or the other.
        from .premises import lookup, body_with_proof, has_full_source
        resolved = [(n, lookup(n)) for n in names]
        full_source: dict[str, bool] = {
            n: has_full_source(p) for n, p in resolved if p is not None
        }
        any_full_source = any(full_source.values())
        bodies: list[str] = []
        for n, p in resolved:
            if p is None:
                bodies.append(f"### `{n}`\n_(not found in premise corpus)_")
                continue
            header = f"### `{n}` ({p.kind}) at `{p.file_path}`"
            if any_full_source and not full_source[n]:
                # Mixed block: a sibling premise below (or above) got a real
                # traced-repo slice, so this fallback entry must be called
                # out individually -- the section heading alone would say
                # "full source" for the whole block.
                header += "  _(no traced source for this premise; signature shown)_"
            bodies.append(f"{header}\n```lean\n{body_with_proof(p)}\n```")
        if bodies:
            heading = (
                "## Premise full source (with proof)"
                if any_full_source
                # No premise in this block got a real traced-repo slice: every
                # body below is `body_with_proof`'s corpus-signature fallback,
                # so heading it "full source (with proof)" would tell the
                # model it had been given proofs it was not given.
                else "## Premise signature (corpus record; traced source unavailable)"
            )
            parts.append(f"{heading}\n" + "\n\n".join(bodies))

    if level >= 3:
        from .premises import body_with_proof, lookup, premise_dep_closure
        depth = level - 2  # hint:3 = 1-hop, hint:4 = 2-hop, hint:5 = 3-hop, ...
        seeds: list = []
        for n in names:
            p = lookup(n)
            if p is not None:
                seeds.append(p)
        if seeds:
            transitive_premises = premise_dep_closure(seeds, depth)
            try:
                import tiktoken
                enc = tiktoken.get_encoding("cl100k_base")

                def tok(s: str) -> int:
                    return len(enc.encode(s))
            except Exception:  # noqa: BLE001
                def tok(s: str) -> int:
                    return len(s) // 4

            chunks: list[str] = []
            used = 0
            n_kept = 0
            for p in transitive_premises:
                # Same content shape as hint:2 — full source incl. proof body.
                snippet = (
                    f"### `{p.full_name}` ({p.kind}) at `{p.file_path}`\n"
                    f"```lean\n{body_with_proof(p)}\n```"
                )
                cost = tok(snippet)
                if used + cost > _HINT2_3_TOKEN_CAP:
                    break
                chunks.append(snippet)
                used += cost
                n_kept += 1
            if chunks:
                parts.append(
                    f"## Transitive premise context ({depth}-hop, "
                    f"{n_kept}/{len(transitive_premises)} premises, ≈{used} tokens)\n"
                    + "\n\n".join(chunks)
                )
    return parts


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------


def validate(chain: Chain, level: int) -> None:
    """Check that `(chain, level)` names an in-range rung.

    Raises
    ------
    ValueError
        `chain` is not a `_MAX_LEVEL` key, or `level` is outside
        ``[0, _MAX_LEVEL[chain]]``. Narrower per-chain constraints are not
        applied, so ``noise:0`` passes here and `_render_noise_parts`
        rejects it later.
    """
    if chain not in _MAX_LEVEL:
        raise ValueError(f"unknown chain: {chain!r}")
    hi = _MAX_LEVEL[chain]
    if not 0 <= level <= hi:
        raise ValueError(f"{chain} level must be 0..{hi}; got {level}")


def render(theorem: BenchmarkTheorem, k: int, chain: Chain, level: int) -> RenderedContext:
    """Render context at proof step `k` of `theorem` for the given (chain, level).

    Parameters
    ----------
    k : int
        0-indexed step about to be proved, in ``[0, len(traced_tactics))``: the
        context describes the state immediately before
        ``theorem.traced_tactics[k]``, and the model is expected to produce the
        tail starting at that tactic.
    chain, level : Chain, int
        Rung to render; checked by `validate`.

    Raises
    ------
    ValueError
        `k` out of range; `(chain, level)` rejected by `validate`; or --
        for ``noise`` -- propagated from `_render_noise_parts` (notably
        ``noise:0``, which `validate` allows through).
    ImportError
        For ``noise`` -- propagated from `_render_noise_parts` when
        `tiktoken` is not installed (see that function's Raises).
    """
    if not 0 <= k < len(theorem.traced_tactics):
        raise ValueError(f"k={k} out of range [0, {len(theorem.traced_tactics)})")
    validate(chain, level)

    if chain == "stepk":
        parts = _render_stepk_parts(theorem, k, level)
    elif chain == "hint":
        parts = _render_hint_parts(theorem, k, level)
    elif chain == "noise":
        parts = _render_noise_parts(theorem, k, level)
    else:
        raise ValueError(f"unknown chain {chain!r}")
    return RenderedContext(chain=chain, level=level, text="\n\n".join(parts))


# Canonical default rung universe. Depths up to hint:9 run (see `_MAX_LEVEL`),
# but mathlib's dependency fan-out hits the 50k token cap by depth ~5-6.
IMPLEMENTED_RUNGS: tuple[tuple[Chain, int], ...] = (
    ("stepk", 0), ("stepk", 1), ("stepk", 2),
    ("hint", 0), ("hint", 1), ("hint", 2), ("hint", 3),
    ("noise", 1), ("noise", 2), ("noise", 3),
)


# ---------------------------------------------------------------------------
# Trivial-rung detection (skip cells where a rung adds no new information)
# ---------------------------------------------------------------------------


def is_trivial_rung(theorem: BenchmarkTheorem, k: int, chain: Chain, level: int) -> bool:
    """True iff this rung adds no informational content beyond the previous rung.

    Skipping these cells keeps per-rung pass rates apples-to-apples: every
    counted cell saw a real context expansion. Trivial when:

      - `stepk:1` and the state has no hypotheses (same as stepk:0);
      - `hint:*` and no premises are recorded for the next tactic;
      - `hint:1` and the corpus has no record for any true premise;
      - `hint:2` and no premise's body differs from its signature;
      - `hint:3+` and the closure at that hop depth is empty;
      - `noise:N` and `hint:N` is trivial or adds no PROMPT tokens over
        `hint:(N-1)` (see the ``noise`` branch below for why this must be a
        prompt-level count, matching `_render_noise_parts` exactly).

    `stepk:0` and `stepk:2` are never trivial (stepk:2 adds theorem identity
    even at k=0). Only caller is `runner.sweep`, gated by ``skip_trivial``.

    Returns
    -------
    bool
        True if the rung is trivial. False -- not an exception -- for an
        unrecognized `chain` or an out-of-range `k`, so the cell still runs
        instead of being silently dropped.

    Raises
    ------
    ImportError
        `chain == "noise"`, `level >= 1`, and `tiktoken` is not installed
        (`TiktokenTokenizer`'s constructor). Deliberately not caught into a
        `False`/`True` guess: `_render_noise_parts` cannot build that rung
        either without `tiktoken`, so a tokenizer-optional answer here could
        tell `runner.sweep` a rung is fine to render when rendering it would
        raise -- the exact divergence this function's ``noise`` branch is
        written to avoid (see below).
    """
    if not 0 <= k < len(theorem.traced_tactics):
        return False
    tt = theorem.traced_tactics[k]

    if chain == "stepk":
        if level == 0:
            return False
        if level == 1:
            hyps, _ = split_state(tt.state_before)
            return not hyps.strip()
        if level == 2:
            # stepk:2 adds theorem identity even at k=0.
            return False
        return False

    if chain == "hint":
        # Collapses the whole chain: hint:0 says "(none recorded)", 1+ have
        # nothing to elaborate.
        if not tt.premises:
            return True
        if level == 0:
            return False
        from .premises import body_with_proof, lookup, signature
        premises = [lookup(p["full_name"]) for p in tt.premises]
        if level == 1:
            return all(p is None for p in premises)
        if level == 2:
            for p in premises:
                if p is not None and signature(p) != body_with_proof(p):
                    return False
            return True
        if level >= 3:
            from .premises import premise_dep_closure
            seeds = [p for p in premises if p is not None]
            return not premise_dep_closure(seeds, level - 2)
        return False
    if chain == "noise":
        if level < 1:
            return True
        if is_trivial_rung(theorem, k, "hint", level):
            return True
        # Design: this MUST measure the same quantity, with the same
        # tokenizer, as `_render_noise_parts` -- full PROMPT tokens via
        # `_as_full_prompt`/`TiktokenTokenizer`, not context-text tokens via
        # `_count_tokens`. If this branch and that function measured
        # different things, a rung this function calls "trivial" (so
        # `runner.sweep` skips it under ``skip_trivial: true``) could still
        # be non-trivial by `_render_noise_parts`'s own measure -- or, worse,
        # a rung called "non-trivial" here could hit `_render_noise_parts`'s
        # ``base_tokens == target_tokens`` early-return and silently render
        # unpadded. Both are the skip/render disagreement this function and
        # that one must never fall into.
        from smolbench.evals.tokenization import TiktokenTokenizer
        tokenizer = TiktokenTokenizer()
        base_text = "\n\n".join(_render_hint_parts(theorem, k, level - 1))
        target_text = "\n\n".join(_render_hint_parts(theorem, k, level))
        base_tokens = tokenizer.count(_as_full_prompt(level, base_text))
        target_tokens = tokenizer.count(_as_full_prompt(level, target_text))
        return target_tokens - base_tokens <= 0
    return False
