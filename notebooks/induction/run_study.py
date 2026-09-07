"""Headless driver for the family-ladder scaling induction study.

The quiz is held fixed (the plain ``periodic_moe`` baseline, ``n=9`` harmonics)
while the MODEL varies -- 7 vendor families x 3 rungs = the 21 checkpoints in
``MODELS`` -- so accuracy reads as a function of parameter count within a
family. Deploy specs live in ``smolbench.evals.providers.ec2.EC2_DEPLOY_SPECS``;
this file is the source of truth for the study's config, and
``notebooks/induction/induction_eval.ipynb`` imports every module-level name
below instead of re-declaring it.

Info arms match ``periodic_moe``'s: ``intens``, ``extens``, ``noise_intens``
(``intens`` padded to ``extens``'s token count under the served model's own
tokenizer -- a length control, not a content control) and ``zero`` (rendered
from ``zero_template``, the range-free counterpart of ``template`` below, so
the prompt cannot leak ``seq_len``). CoT is on for all 21 checkpoints.
``request_timeout_seconds`` derives each model's per-request read timeout from
its completion budget rather than the provider's 600 s default, since a
~100k-token budget cannot finish inside it and a too-short timeout would censor
the top of the CoT-length distribution instead of re-rolling it.

Seeds: ``BASE_SEED = 0``, not the sibling studies' 1776, so this study's seed
range can never alias theirs; ``N_REPLICATES = 30``. Neither is
environment-overridable. A replicate's seed drives the quiz's label sampling
(via ``PeriodicConfig``) and the per-request decoding seed, not query
sampling: this study's generator, ``numeric_count_query_gen``, emits one count
query per label in ascending-period order and is deterministic.

Environment: ``INDUCTION_SHARD`` (``"index/count"``; splits one model's
replicates by ``r % count == index`` on the seed's index in
``range(N_REPLICATES)`` -- never stored, so a shard's seed set is reproducible
from ``(index, count)`` alone); ``INDUCTION_MODELS`` (comma-separated spec
keys; unset/empty selects all 21); ``INDUCTION_FORCE_RERUN`` (``"1"`` or
``"a-b"``; re-collects seeds past the resume-skip, superseding every existing
run for that seed's addresses -- forcing is per-seed, so it re-collects all of
``INFO_TYPES`` for that seed in one pooled call); ``INDUCTION_STATE_FILE`` (the
only way to redirect this process's repo-root-anchored EC2 state file). The
fleet MUST set a distinct state file per lane: two lanes sharing one would have
the second ``provision()`` reattach to the first's instance and swap the served
model out from under it. ``EC2_EXPERIMENT_TAG`` is honoured when exported (the
fleet does) and otherwise defaulted here, never left at ``ec2.py``'s own
retired fallback.

Lifecycle and cost: ``main()`` calls ``EXPERIMENT.teardown()`` only behind
``--teardown``, for standalone use -- the fleet supervisor
(``scripts/fleet/run_fleet.py``) owns instance lifecycle otherwise and reuses
each lane's box for a later deduction-phase lane. ``provision()``/``run()`` are
live AWS spot spend (g6e.4xlarge to p6-b200.48xlarge); standalone this serves
all 21 checkpoints in turn on one reconfigured instance, under the fleet up to
21 concurrent boxes. ``main()`` provisions only when a selected model still has
outstanding replicates, since this driver never tears down and an idle box
would otherwise bill until the watchdog fires.

Run (repo root):
    .venv/bin/python notebooks/induction/run_study.py
"""

import argparse
import logging
import os
import string
from math import ceil
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# MODULE-LEVEL ORDER IS LOAD-BEARING. Do not reorder the numbered blocks below.
# ---------------------------------------------------------------------------
# smolbench.evals.providers.ec2 freezes every EC2_* module constant from
# os.environ at import time, so anything that mutates an EC2_* variable must
# run before ec2 is imported anywhere in this process:
#
#   1. load_dotenv -- fills the environment from keys.env.
#   2. _parse_shard / _parse_force_seeds -- pure helper defs.
#   3. SHARD -- parsed here because block 5 needs it.
#   4. MODELS -- built from smolbench.evals.study_config (roster_keys/tag_for,
#      the one place the roster is written down) ahead of block 5, which
#      derives the lane label from the canonical model order. That module
#      touches no EC2_* variable, so importing it here is safe.
#   5. The EC2 tag / _LANE / _DEFAULT_STATE_FILE block -- writes
#      os.environ["EC2_EXPERIMENT_TAG"], hence must precede step 6. Also
#      imports validate_experiment_tag from smolbench.evals.experiment, which
#      imports providers.ec2 only inside method bodies, never at module scope.
#   6. from smolbench.evals.providers import ec2 and the other smolbench
#      imports -- legal at module scope only because steps 1 and 5 have
#      already resolved every EC2_* variable ec2 is about to freeze.
#   7. derive_context_limit + CONTEXT_LIMIT -- calls into ec2 at import time,
#      so it must follow step 6.
#   8. Everything else (COT_ARGS, template, the functions, EXPERIMENT, main),
#      none of which touches EC2_* env vars.

# --- 1. dotenv ------------------------------------------------------------
# Anchored via __file__, never cwd. MUST land before
# smolbench.evals.providers.ec2 is imported anywhere: ec2.py freezes its EC2_*
# constants at import time. NOT override=True: under the fleet the supervisor
# exports a per-lane environment (INDUCTION_MODELS, INDUCTION_STATE_FILE,
# EC2_EXPERIMENT_TAG, ...) before this file runs, and keys.env must not
# clobber it with this file's local defaults.
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)


# --- 2. environment-parsing helpers ---------------------------------------
def _parse_shard(var: str) -> "tuple[int, int] | None":
    """Parse environment variable `var` as ``"index/count"``; ``None`` if unset/empty.

    Sharding splits one model's replicates across N processes/instances,
    orthogonal to this study's one-model-per-box fan-out. Raises
    ``SystemExit`` on an unparseable value or a violated
    ``count >= 1`` / ``0 <= index < count``, rather than silently running
    unsharded.
    """
    raw = os.environ.get(var, "").strip()
    if not raw:
        return None
    try:
        index, count = (int(part) for part in raw.split("/", 1))
    except ValueError:
        raise SystemExit(f"{var}={raw!r}: expected 'index/count', e.g. {var}=0/3")
    if count < 1 or not (0 <= index < count):
        raise SystemExit(f"{var}={raw!r}: need count >= 1 and 0 <= index < count")
    return index, count


def _parse_force_seeds(raw: str, full_range: range) -> "frozenset[int] | None":
    """Parse ``INDUCTION_FORCE_RERUN`` into the set of seeds to re-collect.

    `raw` is ``""`` (off -> ``None``), ``"1"`` (every seed in `full_range`), or
    ``"a-b"`` (that inclusive subrange). Raises ``SystemExit`` on an
    unparseable value or an out-of-range subrange, never a silent no-op.
    """
    raw = raw.strip()
    if not raw:
        return None
    if raw == "1":
        return frozenset(full_range)
    try:
        lo, hi = (int(part) for part in raw.split("-", 1))
    except ValueError:
        raise SystemExit(
            f"INDUCTION_FORCE_RERUN={raw!r}: expected '1' or 'a-b' (e.g. '0-11')"
        )
    if lo > hi or lo < full_range.start or hi >= full_range.stop:
        raise SystemExit(
            f"INDUCTION_FORCE_RERUN={raw!r}: subrange must lie inside "
            f"{full_range.start}..{full_range.stop - 1}"
        )
    return frozenset(range(lo, hi + 1))


# --- 3. shard -------------------------------------------------------------
SHARD = _parse_shard("INDUCTION_SHARD")

# --- 4. the roster --------------------------------------------------------
# Spec key (EC2_DEPLOY_SPECS key, also vLLM's --served-model-name) -> short
# analysis tag. Exactly EC2_DEPLOY_SPECS's 21 family-ladder entries, excluding
# the "qwen2.5-1.5b" smoke entry. Declaration order is the study's canonical
# order. Declared here, above the tag block, because block 5 builds the lane
# label in this order. Read from the committed study config, the one place
# the roster is written down, instead of a second hand-maintained literal.
from smolbench.evals.study_config import load_study_config, roster_keys, tag_for  # noqa: E402

MODELS: dict[str, str] = {key: tag_for(key) for key in roster_keys()}

# --- 5. EC2 tag, lane suffix and default state file -----------------------
# A shard needs its own AWS tag and state file: without that, shard 1
# reattaches to shard 0's live box and swaps the served model out from under a
# run in progress. Unsharded runs get an empty suffix.
#
# Fleet lanes never hit the config's standalone_tag default (run_fleet.lane_env
# exports a per-lane EC2_EXPERIMENT_TAG + INDUCTION_STATE_FILE); the
# standalone tag sits outside the fleet's tag_prefix namespace so
# fleet_status/fleet_teardown never list or terminate a standalone box --
# `--teardown` owns it. This mutation fires on every run, sharded or not, but
# a roster-only importer that sees it as a side effect provisions nothing,
# so that is safe.
#
# MUST execute before the ec2 import below, for the import-time freeze the
# load_dotenv comment above describes.
_LANE = ""
if SHARD is not None:
    # Canonicalized before labelling: building the lane from the raw
    # INDUCTION_MODELS string would mint two different tags -- two boxes and
    # two state files -- for "a,b" and "b,a", splitting one lane's work in
    # half. Parsed the same way selected_models() parses it; validation stays
    # there, so unknown keys are appended in given order rather than dropped.
    _requested = [
        key.strip()
        for key in os.environ.get("INDUCTION_MODELS", "").split(",")
        if key.strip()
    ]
    _chosen = set(_requested)
    _lane_models = [model for model in MODELS if model in _chosen]
    # dict.fromkeys: de-duplicate the unknowns while preserving first-seen
    # order, so a repeated typo cannot lengthen the tag.
    _lane_models += [key for key in dict.fromkeys(_requested) if key not in MODELS]
    _LANE = ("-" + "-".join(_lane_models) if _lane_models else "") + "-s{}of{}".format(
        *SHARD
    )

# setdefault, not an unconditional write: a fleet-exported EC2_EXPERIMENT_TAG
# must still win. The lane suffix is appended to whichever tag resolved.
os.environ.setdefault("EC2_EXPERIMENT_TAG", load_study_config().fleet.standalone_tag)
if _LANE:
    os.environ["EC2_EXPERIMENT_TAG"] += _LANE

# Refuse to run under an unsafe resolved tag rather than proceed: on a lost or
# absent state file, ec2's tag-based recovery reattaches `provision()` to any
# live box carrying the tag, and `--teardown` terminates it. Checked against
# the resolved tag rather than by importing ec2, since that would freeze ec2's
# constants against the environment as it stood before the lines above.
from smolbench.evals.experiment import validate_experiment_tag  # noqa: E402

_RESOLVED_TAG = os.environ["EC2_EXPERIMENT_TAG"]
try:
    validate_experiment_tag(_RESOLVED_TAG, _LANE)
except ValueError as exc:
    # SystemExit, matching this file's other config-error convention.
    raise SystemExit(str(exc)) from exc

_DEFAULT_STATE_FILE = f".ec2_state_induction{_LANE}.json"

# --- 6. smolbench imports -------------------------------------------------
# ec2 at module scope is normally forbidden, because of the import-time
# freeze; it is safe here, and only here, because blocks 1 and 5 above have
# already resolved every EC2_* variable it captures. Do not move this line
# up, and do not add an EC2_* mutation below it.
from smolbench.evals.providers import ec2  # noqa: E402
from smolbench.evals import Numeric  # noqa: E402
from smolbench.evals.tokenization import for_model  # noqa: E402
from smolbench.induction._common import RenderedQuery, quizzes_from_prompts  # noqa: E402
from smolbench.induction.experiment import InductionExperiment  # noqa: E402
from smolbench.induction.periodic import (  # noqa: E402
    CONDITIONS,
    PeriodicConfig,
    Prompter,
    get_periodic_prompts,
    numeric_count_query_gen,
)


# --- 7. the served context window, DERIVED from the deploy specs ----------
# Defined immediately above its own call site because that call runs at IMPORT
# time; it cannot live down with the run-time functions in block 8.
def derive_context_limit(lengths: "dict[str, int]") -> int:
    """Return the single context window that every model in `lengths` shares.

    Raises ``SystemExit`` if `lengths` is empty or holds more than one
    distinct value (message names the offending keys), rather than papering
    over non-uniformity with a ``min()``/``max()``: a scaling study cannot let
    context vary with the vendor's own YaRN generosity, or a family's ceiling
    is confounded with its context budget rather than its parameter count.
    """
    if not lengths:
        raise SystemExit(
            "derive_context_limit: got an empty {model: context_length} mapping, "
            "so there is no context window to derive. Check that MODELS is "
            "non-empty."
        )
    distinct = sorted(set(lengths.values()))
    if len(distinct) > 1:
        # Grouped by length: the actionable question is which checkpoints sit
        # on the odd value, not the full 21-entry mapping.
        detail = "; ".join(
            f"{length} -> {sorted(k for k, v in lengths.items() if v == length)}"
            for length in distinct
        )
        raise SystemExit(
            f"This study's roster is served with {len(distinct)} different context "
            f"lengths ({detail}). A scaling study cannot let context vary with the "
            "vendor's own YaRN generosity: a family's ceiling would be confounded "
            "with its context budget rather than its parameter count. Align the "
            "max_model_len of every EC2_DEPLOY_SPECS entry in MODELS, or drop the "
            "outlier from the roster."
        )
    return distinct[0]


#: The served checkpoints' context window. Derived from the deploy specs
#: rather than a hand-written literal, so a spec edit on one checkpoint cannot
#: leave this study deriving completion budgets against a context it is no
#: longer served with. Uniformity is load-bearing: a scaling study cannot let
#: context vary with the vendor's own YaRN generosity, hence
#: derive_context_limit raises instead of picking one.
CONTEXT_LIMIT: int = derive_context_limit(
    {key: ec2.get_model_context_length(key) for key in MODELS}
)

# --- 8. study constants, tables, functions and entry point ----------------

#: Locked at 0, not the 1776 every prior induction study seeded from, so this
#: study's seed range can never alias theirs.
BASE_SEED: int = 0

#: Locked. 30 matches every sibling study's R, checked against
#: ``analysis/power_analysis.py``'s recommended-R section, not a computed
#: optimum. Sibling drivers expose a ``*_N_REPLICATES`` env override; this one
#: deliberately does not, since the 21-checkpoint comparison is apples-to-
#: apples only at one shared count.
N_REPLICATES: int = 30

#: Derived from ``smolbench.induction.periodic.CONDITIONS``, the one
#: declaration of these names, rather than restated as a literal that could
#: drift from it silently.
INFO_TYPES: tuple[str, ...] = tuple(CONDITIONS)

#: Tokens withheld from the completion budget, covering what a count() on one
#: seed's prompt cannot see: the chat template's special/BOS tokens (count()
#: deliberately excludes them) and cross-seed variation in the sampled labels
#: over a long extensional listing. Measured ad hoc at design time at
#: 1,500-3,700 tokens on comparable listings; sized well above that so the
#: budget stays safe when the probe below misses the longest seed.
TEMPLATE_RESERVE: int = 8_000

#: Seeds probed for the worst-case prompt in completion_budget: the endpoints
#: plus four evenly spaced interior seeds, catching a mid-range label-length
#: outlier at 6 tokenizer passes instead of 30. Must be >= 2 (the derivation
#: divides by ``PROBE_SEEDS - 1``).
PROBE_SEEDS: int = 6

#: Floor below which a run is not worth starting: a smaller budget is likely
#: to truncate a CoT checkpoint's reasoning before the final integer,
#: collecting empties rather than anything scorable. Judgment, not fitted:
#: periodic_moe's qwen3.5 needed a 65,536-token budget on a comparable
#: listing, so under ~48k is deep truncation territory, while healthy budgets
#: here land near 100k.
MIN_VIABLE_BUDGET: int = 48_000

#: Conservative floor (tokens/s of single-request decode) the per-model
#: request timeout is sized against, not a speed prediction: a faster model
#: just finishes early. What fixes the number is the fan-out -- up to 8 long
#: CoT generations (ec2.py's EC2_MAX_PARALLEL_REQUESTS default) share one
#: box's decode throughput at 100k tokens each, and 10 tok/s per in-flight
#: request sits below anything these tiers should realize even fully loaded.
#: Clearing a 100k budget inside ec2's 600 s default would need >= 167 tok/s,
#: not achievable on a 397B/236B MoE.
MIN_DECODE_TOK_S: int = 10

#: A literal: ec2's env-overridable constant could set the floor below 600 s.
REQUEST_TIMEOUT_FLOOR_SECONDS: int = 600

# Byte-identical to periodic_moe's / periodic_divisor's template: prompt
# wording is fixed across every induction study, so only the roster (model,
# quiz generator, harmonic set) varies between studies.
template = string.Template(
    "You are a precise integer counter.\n"
    "\n"
    "Task: answer the question below with a single integer and nothing else.\n"
    "\n"
    "Output format:\n"
    "Return exactly one integer and nothing else.\n"
    "Do not output any explanation, punctuation, quotes, or extra whitespace.\n"
    "Stop immediately after writing the integer.\n"
    "\n"
    "Context:\n"
    "There is a counting game. Positions are counted starting from 1. "
    "At each position, words are written according to the following rules:\n"
    "$positive_info\n"
    "Question:\n"
    "How many of the positions 1 through $seq_len include '$label'?"
)

#: The position-range clause `zero_template` strips out of `template`. Named
#: as its own constant rather than inlined into the `.replace()` call below,
#: so the substring being removed is documented at its own definition.
RANGE_CLAUSE: str = " 1 through $seq_len"

if RANGE_CLAUSE not in template.template:
    # Fails loudly at import: `.replace()` on a missing substring is a no-op,
    # so a future rewording of `template` would otherwise leave
    # `zero_template` silently byte-identical to `template` -- `zero` leaking
    # `seq_len` again.
    raise RuntimeError(
        f"RANGE_CLAUSE {RANGE_CLAUSE!r} not found in template.template; "
        "the study template's range clause was edited without updating "
        "RANGE_CLAUSE, which would silently make zero_template leak seq_len."
    )

def _zero_template(base: string.Template) -> string.Template:
    """Derive the zero condition's range-free question from `base`.

    One edit applied to `base` (`RANGE_CLAUSE` stripped out), never a second,
    independently written copy of the whole prompt that could drift out of
    sync with it. Takes `base` as a parameter rather than closing over the
    module-level `template` directly, so a caller computes it fresh against
    whichever `string.Template` is currently bound to `template` -- see
    `rendered_queries`, which calls this on every invocation instead of
    reusing the frozen `zero_template` below.
    """
    return string.Template(base.template.replace(RANGE_CLAUSE, ""))


#: The zero condition's question at import time, against the module's own
#: `template` -- exposed as a plain attribute so a caller (or a test) can
#: inspect the production range-free template directly. `rendered_queries`
#: does not read this frozen value; see `_zero_template`'s docstring for why
#: it recomputes instead.
zero_template = _zero_template(template)

# Per-request extra args that turn CoT on for each of the 21 checkpoints.
# Total over MODELS by construction (written out literally, not built from a
# prefix rule), so the table is the audit surface against ec2.py's "Reasoning
# wiring" comment, and a typo in a family prefix can never produce a silent
# KeyError deep inside main() on a billing box. Four rules:
#   1. Qwen3.5 / Nemotron-3 / Gemma-4 / GLM-4.x / EXAONE / K-EXAONE:
#      {"chat_template_kwargs": {"enable_thinking": True}}.
#   2. DeepSeek V4-Flash / V3.1 / V4-Pro: {"chat_template_kwargs":
#      {"thinking": True}} -- note the DIFFERENT kwarg name from rule 1.
#   3. Ministral-3 (3B/8B/14B): {} -- its think protocol is switched on by
#      ec2.py's injected system_prompt, not by a chat_template_kwarg.
#   4. Gemma-4-* and EXAONE-4.0-32B NEED their explicit "enable_thinking": True:
#      both ship templates defaulting thinking OFF, so omitting the kwarg would
#      silently serve them non-reasoning while every other checkpoint reasons.
COT_ARGS: dict[str, dict] = {
    "qwen3.5-27b": {"chat_template_kwargs": {"enable_thinking": True}},
    "qwen3.5-122b-a10b": {"chat_template_kwargs": {"enable_thinking": True}},
    "qwen3.5-397b-a17b": {"chat_template_kwargs": {"enable_thinking": True}},
    "nemotron-3-nano-4b": {"chat_template_kwargs": {"enable_thinking": True}},
    "nemotron-3-nano-30b-a3b": {"chat_template_kwargs": {"enable_thinking": True}},
    "nemotron-3-super-120b-a12b": {"chat_template_kwargs": {"enable_thinking": True}},
    "gemma-4-e2b": {"chat_template_kwargs": {"enable_thinking": True}},
    "gemma-4-12b": {"chat_template_kwargs": {"enable_thinking": True}},
    "gemma-4-31b": {"chat_template_kwargs": {"enable_thinking": True}},
    "glm-4.7-flash": {"chat_template_kwargs": {"enable_thinking": True}},
    "glm-4.5-air": {"chat_template_kwargs": {"enable_thinking": True}},
    "glm-4.7": {"chat_template_kwargs": {"enable_thinking": True}},
    "ministral-3-3b": {},
    "ministral-3-8b": {},
    "ministral-3-14b": {},
    "exaone-4.0-32b": {"chat_template_kwargs": {"enable_thinking": True}},
    "exaone-4.5-33b": {"chat_template_kwargs": {"enable_thinking": True}},
    "k-exaone-236b-a23b": {"chat_template_kwargs": {"enable_thinking": True}},
    "deepseek-v4-flash": {"chat_template_kwargs": {"thinking": True}},
    "deepseek-v3.1": {"chat_template_kwargs": {"thinking": True}},
    "deepseek-v4-pro": {"chat_template_kwargs": {"thinking": True}},
}

# Enforce COT_ARGS against the study config's roster, key-for-key and in the
# same ladder order, at import -- before provision() can spend: a drifted key
# would otherwise surface as a KeyError on a billing box. A `raise`, not an
# `assert`: asserts are stripped under `python -O`, which would delete this
# gate on exactly the automated invocations that most need it.
if tuple(COT_ARGS) != roster_keys():
    _cot_args_roster_diff = sorted(set(COT_ARGS) ^ set(roster_keys()))
    raise RuntimeError(
        "COT_ARGS must match study_config.roster_keys(), key-for-key and in "
        "the same ladder order. "
        + (
            f"Keys in exactly one of them: {_cot_args_roster_diff}"
            if _cot_args_roster_diff
            else "Same keys, but in a different order."
        )
    )


def rendered_queries(seed: int, model: str) -> "list[RenderedQuery]":
    """Render one replicate's queries, all four ``CONDITIONS`` arms of each.

    Uses the plain ``periodic_moe`` baseline config unmodified (the study's
    independent variable is the model, not the quiz). `model` is needed
    because ``noise_intens`` is padded under this model's tokenizer; the
    other three arms stay byte-identical across checkpoints. ``for_model`` is
    looked up as a plain module global so
    ``tests/induction/test_induction_study.py`` can monkeypatch it (and
    ``make_quizzes``/``completion_budget``, which call this) to keep the
    offline suite from downloading a tokenizer.

    Single generation call both ``make_quizzes`` and ``completion_budget``
    build on, so a replicate's prompts are generated once per call site
    instead of once for collection and again for budget-sizing.
    """
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    # `_zero_template(template)`, not the frozen `zero_template` global: see
    # that helper's docstring for why this must read the current `template`
    # fresh on every call.
    prompter = Prompter(
        template, numeric_count_query_gen, range_free_template=_zero_template(template)
    )
    return list(
        get_periodic_prompts(cfg, prompter, tokenizer=for_model(model), conditions=CONDITIONS)
    )


def make_quizzes(seed: int, model: str) -> "dict[str, tuple]":
    """Generate one replicate's four quizzes, keyed by ``INFO_TYPES`` in that order.

    Thin wrapper over :func:`rendered_queries`, turning its per-query
    ``RenderedQuery`` list into one ``Quiz`` (a tuple of ``Numeric`` QnAs) per
    condition.
    """
    return quizzes_from_prompts(rendered_queries(seed, model), Numeric, CONDITIONS)


def probe_seeds(seeds: range) -> "list[int]":
    """Return the ``PROBE_SEEDS`` evenly spaced seeds to probe, sorted and deduplicated.

    Ascending, without duplicates, so at most ``PROBE_SEEDS`` entries and as
    few as one; always contains both ``seeds[0]`` and ``seeds[-1]``. `seeds`
    must be non-empty; ``PROBE_SEEDS >= 2`` is required since the derivation
    divides by ``PROBE_SEEDS - 1``.
    """
    return sorted(
        {seeds[i * (len(seeds) - 1) // (PROBE_SEEDS - 1)] for i in range(PROBE_SEEDS)}
    )


def completion_budget(model: str, seeds: range) -> int:
    """Derive the largest completion budget that cannot overflow this model's context.

    Returns ``CONTEXT_LIMIT - worst - TEMPLATE_RESERVE``, where ``worst`` is
    the largest prompt token count over every info type of every probed seed.
    Only ``PROBE_SEEDS`` of `seeds` are probed (see ``probe_seeds``): every
    structural driver of prompt length is identical across seeds, only the
    sampled labels vary, and ``TEMPLATE_RESERVE`` covers far more than that
    residual.

    Token counts come from :func:`rendered_queries`'s own generation pass
    (every condition's prompt is already tokenized while it is built), not a
    second tokenizer pass, so this makes no ``count`` call of its own. Still
    pure CPU plus a tokenizer fetch, so it runs before anything is
    provisioned and billing.

    Returns one number per model, not a per-vendor dict: a tighter cap on one
    family would make its accuracy gap inseparable from "it had less room to
    reason," the confound a scaling study exists to avoid.

    Raises ``SystemExit`` below ``MIN_VIABLE_BUDGET``, which would truncate
    CoT and collect empties.
    """
    worst = 0
    for seed in probe_seeds(seeds):
        for query in rendered_queries(seed, model):
            worst = max(worst, max(query.token_counts.values()))
    budget = CONTEXT_LIMIT - worst - TEMPLATE_RESERVE
    if budget < MIN_VIABLE_BUDGET:
        raise SystemExit(
            f"{model}: worst prompt is {worst:,} tokens, leaving only {budget:,} for "
            f"completion against a {CONTEXT_LIMIT:,} context. That is below the "
            f"{MIN_VIABLE_BUDGET:,} floor and would collect empties, not data. "
            "Shorten the period set or investigate why this checkpoint's prompts "
            "are unusually large."
        )
    logging.info(
        f"{model}: worst prompt {worst:,} tok (+{TEMPLATE_RESERVE:,} reserve) "
        f"-> completion budget {budget:,}"
    )
    return budget


def request_timeout_seconds(budget: int) -> int:
    """Return the per-request read timeout, in seconds, that `budget` tokens need.

    ``max(REQUEST_TIMEOUT_FLOOR_SECONDS, ceil(budget / MIN_DECODE_TOK_S))``:
    never less than the provider's own default. Without this, every model
    rides ec2.py's 600 s default while handed a ~100k-token CoT budget, which
    needs >= 167 tok/s to clear in time -- not achievable on a 397B/236B MoE.

    The two failure directions are not symmetric, which is why this only
    ever errs long: retries never re-seed (ec2.py re-POSTs the byte-identical
    seeded body), so a timeout shorter than the generation times out again on
    every attempt, silently censoring the top of the CoT-length distribution
    on the arm that carries this study's headline contrast. An over-long
    timeout costs only wall-clock, on a request that was going to fail
    anyway. No upper clamp is applied: a ceiling that binds reintroduces that
    same censoring. This is a floor, never a cap.
    """
    return max(REQUEST_TIMEOUT_FLOOR_SECONDS, ceil(budget / MIN_DECODE_TOK_S))


# notebook_dir="induction" is also the S3 log's <experiment> key segment (via
# results_store.experiment_name), so every replicate lands under
# induction/<spec-key>/seed=<seed>/<info>--<run_ts>.yaml, distinct from every
# sibling study's keys.
EXPERIMENT = InductionExperiment(
    notebook_dir="induction",
    archetype_tags=MODELS,
    make_quizzes=make_quizzes,
    info_types=INFO_TYPES,
    n_replicates=N_REPLICATES,
    base_seed=BASE_SEED,
    state_file=os.environ.get("INDUCTION_STATE_FILE", _DEFAULT_STATE_FILE),
    shard=SHARD,
    # INDUCTION_FORCE_RERUN re-collects replicates past the resume-skip;
    # combines with INDUCTION_SHARD, a shard forcing only the seeds it owns.
    force_seeds=_parse_force_seeds(
        os.environ.get("INDUCTION_FORCE_RERUN", ""),
        range(BASE_SEED, BASE_SEED + N_REPLICATES),
    ),
)


def selected_models() -> "tuple[str, ...]":
    """Return the spec keys to run: ``INDUCTION_MODELS``, or all of ``MODELS``.

    Always emitted in ``MODELS`` declaration order, whatever order the
    environment listed them in, matching the lane tag's order at the top of
    this file and keeping a standalone unfiltered run deterministic.

    Raises ``SystemExit`` before any instance is provisioned if
    ``INDUCTION_MODELS`` names an unknown key, or is set but resolves to zero
    keys (e.g. ``","``): a zero-model run would otherwise exit 0 having
    quietly done nothing and hidden the typo.
    """
    wanted = os.environ.get("INDUCTION_MODELS", "").strip()
    if not wanted:
        return tuple(MODELS)
    keys = [k.strip() for k in wanted.split(",") if k.strip()]
    if not keys:
        raise SystemExit(
            f"INDUCTION_MODELS={wanted!r}: named no models (only commas/"
            "whitespace after splitting). Leave it unset to select all 21, "
            "or name at least one spec key."
        )
    unknown = [k for k in keys if k not in MODELS]
    if unknown:
        raise SystemExit(
            f"INDUCTION_MODELS: unknown key(s) {unknown}; pick from {sorted(MODELS)}"
        )
    chosen = set(keys)
    return tuple(m for m in MODELS if m in chosen)


def main(argv: "list[str] | None" = None) -> None:
    """Warm tokenizers, derive budgets, provision, run, and summarize: the entry point.

    Makes live AWS calls on every path except ``--teardown``, a failed
    argument parse, and a roster with no outstanding replicates, and never
    tears the instance down otherwise (see the module docstring's "Lifecycle
    and cost" section). `argv` is a parameter so a test or notebook cell can
    call this without a subprocess.
    """
    parser = argparse.ArgumentParser(
        description="Family-ladder scaling induction study driver."
    )
    parser.add_argument(
        "--teardown",
        action="store_true",
        help=(
            "Terminate this experiment's EC2 instance and exit immediately. "
            "STANDALONE USE ONLY: under the fleet, the supervisor owns "
            "instance lifecycle and tears down after the deduction phase "
            "has also finished with the box -- do not invoke this flag from "
            "fleet-driven automation."
        ),
    )
    args = parser.parse_args(argv)

    if args.teardown:
        EXPERIMENT.teardown()
        return

    models = selected_models()
    logging.info(f"running models: {list(models)}")

    # Warm every tokenizer and derive its completion budget before provisioning
    # anything: an HF download failure or an under-budget SystemExit must
    # never land between a billing GPU box and the first inference request.
    seeds = range(BASE_SEED, BASE_SEED + EXPERIMENT.n_replicates)
    budgets: dict[str, int] = {}
    for model in models:
        logging.info(f"warming tokenizer for {model}: {for_model(model).name}")
        budgets[model] = completion_budget(model, seeds)

    # Cost gate: provision only if there is work, since this driver never
    # tears down and re-running a completed lane would otherwise boot a spot
    # box that billed until the idle watchdog fired.
    outstanding = [m for m in models if EXPERIMENT.harness.has_outstanding(m)]
    if not outstanding:
        logging.info(
            f"no outstanding replicates for {list(models)}; nothing provisioned "
            "and nothing to run"
        )
        return

    EXPERIMENT.provision()
    # Iterate `models`, not `outstanding`: run() re-checks has_outstanding per
    # model and returns without serving when there is none, and summarize()
    # should still report the finished ones in this lane.
    for model in models:
        EXPERIMENT.run(
            model,
            extra_args={"max_completion_tokens": budgets[model], **COT_ARGS[model]},
            request_timeout=request_timeout_seconds(budgets[model]),
        )
        EXPERIMENT.summarize(model)
    # Deliberately no EXPERIMENT.teardown() here: this box may be reused by
    # the deduction phase after this process exits.
    print(f"INDUCTION STUDY RUN COMPLETE: {list(models)} (no teardown -- fleet-owned)",
          flush=True)


if __name__ == "__main__":
    main()
