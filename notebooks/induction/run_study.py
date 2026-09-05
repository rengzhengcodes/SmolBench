"""Headless driver for the FAMILY-LADDER SCALING induction study.

The quiz is held fixed (the plain ``periodic_moe`` baseline, ``n=9`` harmonics)
while the MODEL varies -- 7 vendor families x 3 rungs = the 21 checkpoints in
``MODELS`` -- so accuracy reads as a function of parameter count within a
family. Deployment facts live in
``smolbench.evals.providers.ec2.EC2_DEPLOY_SPECS``; this file is the single
source of truth for the STUDY's config, and
``notebooks/induction/induction_eval.ipynb`` imports every module-level name
below instead of re-declaring it; the constants themselves are pinned by
``tests/induction/test_induction_study.py``.

The four info arms match ``periodic_moe``'s: ``intens``, ``extens``,
``noise_intens`` (``intens`` whitespace-padded to ``extens``'s token count under
the SERVED model's own tokenizer -- a length control, not a content control) and
``zero`` (empty context, chance floor). CoT is ON for all 21 checkpoints, and
each model's per-request read timeout is DERIVED from its completion budget by
``request_timeout_seconds`` rather than left at the provider's 600 s default: a
~100k-token budget cannot finish inside 600 s, and a too-short timeout censors
the top of the CoT-length distribution instead of re-rolling it.

Seeds: ``BASE_SEED = 0``, not the sibling studies' 1776, so this study's seed
range (0..29) can never alias theirs; ``N_REPLICATES = 30``, and neither is
environment-overridable.

Environment: ``INDUCTION_SHARD`` (``"index/count"``; splits ONE model's
replicates); ``INDUCTION_MODELS`` (comma-separated SPEC KEYS, not analysis tags;
unset/empty selects all 21); ``INDUCTION_FORCE_RERUN`` (``"1"`` or ``"a-b"``;
re-collect seeds past the resume-skip -- forced attempts APPEND to the S3 log
and earliest-wins reads never return them; see ``force_seeds=`` in ``main()``); ``INDUCTION_STATE_FILE`` (the only way
to redirect this process's repo-root-anchored EC2 state file --
``InductionExperiment._apply_env`` overwrites the bare ``EC2_STATE_FILE`` shell
variable on every provision/run/teardown). The fleet MUST set a distinct state
file per lane: two lanes sharing one would have the second ``provision()``
reattach to the first's instance and swap the served model out from under it.
``EC2_EXPERIMENT_TAG`` is honoured when exported (the fleet does) and otherwise
DEFAULTED here, never left at ``ec2.py``'s own retired fallback.

Lifecycle contract and COST: ``main()`` calls ``EXPERIMENT.teardown()`` only
behind ``--teardown``, for STANDALONE use only -- the fleet supervisor
(``scripts/fleet/run_fleet.py``) owns instance lifecycle and reuses each lane's
box for a later deduction-phase lane, so a teardown here would terminate an
instance that phase is about to reattach to. ``provision()`` and ``run()`` are
LIVE AWS spot spend, billed while each box is up, on tiers from g6e.4xlarge to
p6-b200.48xlarge; standalone this serves all 21 checkpoints in turn on ONE
reconfigured instance, under the fleet up to 21 concurrent boxes. ``main()``
provisions ONLY when at least one selected model still has outstanding
replicates: a completed lane re-run logs and exits 0 without spending, because
this driver never tears down and an idle box would bill until the watchdog
fires. Verify ``INDUCTION_MODELS`` before invoking outside the fleet.

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
# ``smolbench.evals.providers.ec2`` freezes every ``EC2_*`` module constant
# from ``os.environ`` at IMPORT time (see InductionExperiment's module
# docstring, CRITICAL section), so anything that MUTATES an ``EC2_*``
# environment variable must run before ``ec2`` is imported anywhere in this
# process. That single constraint fixes the whole order:
#
#   1. ``load_dotenv`` -- fills the environment from keys.env.
#   2. ``_parse_shard`` / ``_parse_force_seeds`` -- pure helper defs.
#   3. ``SHARD`` -- parsed here because block 5 needs it.
#   4. ``MODELS`` -- moved ABOVE the tag block (it used to sit next to
#      ``COT_ARGS``): block 5 derives the lane label from the CANONICAL model
#      order, so it needs ``MODELS`` already bound. The dict is a plain
#      literal with no imports and no dependencies, so it can sit anywhere.
#   5. The EC2 tag / ``_LANE`` / ``_DEFAULT_STATE_FILE`` block -- WRITES
#      ``os.environ["EC2_EXPERIMENT_TAG"]``, hence must precede step 6.
#   6. ``from smolbench.evals.providers import ec2`` and the other smolbench
#      imports -- legal at module scope ONLY because steps 1 and 5 have
#      already resolved every ``EC2_*`` variable ec2 is about to freeze.
#   7. ``derive_context_limit`` + ``CONTEXT_LIMIT`` -- calls into ec2 at
#      import time, so it must follow step 6.
#   8. Everything else (``COT_ARGS``, ``template``, the functions,
#      ``EXPERIMENT``, ``main``), none of which touches ``EC2_*`` env vars.

# --- 1. dotenv ------------------------------------------------------------
# Anchored via __file__, never cwd. MUST land before
# smolbench.evals.providers.ec2 is imported anywhere: ec2.py freezes its EC2_*
# constants at import time (see InductionExperiment's module docstring,
# CRITICAL section). NOT override=True: under the fleet the supervisor exports a
# per-lane environment (INDUCTION_MODELS, INDUCTION_STATE_FILE,
# EC2_EXPERIMENT_TAG, ...) before this file runs, and keys.env must not clobber
# it with this file's local defaults.
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)


# --- 2. environment-parsing helpers ---------------------------------------
def _parse_shard(var: str) -> "tuple[int, int] | None":
    """Parse environment variable `var` as ``"index/count"``; ``None`` if unset/empty.

    Sharding splits ONE model's replicates across N processes/instances,
    orthogonally to this study's one-model-per-box fan-out. Raises
    ``SystemExit`` at import on an unparseable value or a violation of
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
    ``"a-b"`` (that inclusive subrange, validated against `full_range`). Raises
    ``SystemExit`` at import on an unparseable value or an out-of-range
    subrange, never silently as a no-op resume.
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
# Spec key (smolbench.evals.providers.ec2.EC2_DEPLOY_SPECS key, also vLLM's
# --served-model-name) -> short analysis tag used in result directory names and
# figure legends. Exactly EC2_DEPLOY_SPECS's 21 family-ladder entries: every key
# except the "qwen2.5-1.5b" single-GPU smoke entry. Declaration order is the
# study's canonical order -- see selected_models' docstring.
#
# Declared HERE, above the tag block, rather than beside COT_ARGS: the lane
# label below must be built in this canonical order (see block 5), and this
# literal has no imports and no dependencies, so hoisting it costs nothing.
MODELS: dict[str, str] = {
    # -- Qwen3.5 (Alibaba, CN): 27B dense / 122B-A10B / 397B-A17B (FP8) --
    "qwen3.5-27b": "qwen35_27b",
    "qwen3.5-122b-a10b": "qwen35_122b",
    "qwen3.5-397b-a17b": "qwen35_397b",
    # -- Nemotron 3 (NVIDIA, US): Nano-4B / Nano-30B-A3B / Super-120B-A12B --
    "nemotron-3-nano-4b": "nemo3_4b",
    "nemotron-3-nano-30b-a3b": "nemo3_30b",
    "nemotron-3-super-120b-a12b": "nemo3_120b",
    # -- Gemma 4 (Google, US): E2B / 12B / 31B instruction-tuned --
    "gemma-4-e2b": "gemma4_e2b",
    "gemma-4-12b": "gemma4_12b",
    "gemma-4-31b": "gemma4_31b",
    # -- GLM-4.x (Zhipu/Z.ai, CN): 4.7-Flash / 4.5-Air / 4.7 (cross-gen) --
    "glm-4.7-flash": "glm_flash",
    "glm-4.5-air": "glm_air",
    "glm-4.7": "glm_47",
    # -- Ministral-3 Reasoning (Mistral, FR): 3B / 8B / 14B --
    "ministral-3-3b": "min3_3b",
    "ministral-3-8b": "min3_8b",
    "ministral-3-14b": "min3_14b",
    # -- EXAONE (LG AI Research, KR): 4.0-32B / 4.5-33B / K-EXAONE-236B (x-gen) --
    "exaone-4.0-32b": "exaone_32b",
    "exaone-4.5-33b": "exaone_33b",
    "k-exaone-236b-a23b": "exaone_236b",
    # -- DeepSeek (CN): V4-Flash / V3.1 / V4-Pro (cross-generation) --
    "deepseek-v4-flash": "ds_flash",
    "deepseek-v3.1": "ds_v31",
    "deepseek-v4-pro": "ds_pro",
}

# --- 5. EC2 tag, lane suffix and default state file -----------------------
# A shard needs its OWN AWS tag and state file -- without that, shard 1
# reattaches to shard 0's live box and swaps the served model out from under a
# run in progress (the collision the periodic_divisor driver hit first). Both
# are derived from the lane rather than asking callers to remember two more
# environment variables. Unsharded runs get an empty suffix.
#
# FLEET lanes never hit the "induction-scaling" default (run_fleet.lane_env
# exports a per-lane EC2_EXPERIMENT_TAG "scaling-<spec-key>" +
# INDUCTION_STATE_FILE); it covers STANDALONE runs only. The standalone tag
# sits outside the fleet's "scaling-" prefix on purpose, so
# fleet_status/fleet_teardown never list -- or terminate -- a standalone box;
# `--teardown` owns it.
#
# The import-time env mutation is deliberate (it must precede ec2's
# import-time freeze) and now fires on EVERY run, sharded or not. It used to
# fire only under INDUCTION_SHARD, which left the documented STANDALONE
# invocation on ec2.py's own "periodic-induction" fallback -- a RETIRED
# study's tag. A roster-only importer (notebooks/deduction/run_study.py, lands
# in slice 5) therefore now also sees EC2_EXPERIMENT_TAG set as a side effect.
# That is the safe direction: such an importer provisions nothing, and it can
# no longer inherit the retired default either.
#
# MUST execute before the ec2 import below, for the import-time freeze the
# load_dotenv comment above describes.
_LANE = ""
if SHARD is not None:
    # Canonicalize the model list before labelling with it. selected_models()
    # emits MODELS declaration order whatever order the environment listed, so
    # building the lane from the RAW INDUCTION_MODELS string minted two
    # different tags -- and so two boxes and two state files -- for "a,b" and
    # "b,a", splitting one lane's work in half. Parsed exactly the way
    # selected_models() parses it; VALIDATION stays there (an unknown key
    # still raises when the roster is resolved), so unknown keys are appended
    # in their given order rather than dropped, keeping the label a faithful,
    # deterministic description of what was asked for.
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

# setdefault, NOT an unconditional write: a fleet-exported EC2_EXPERIMENT_TAG
# must still win. The lane suffix is then appended to whichever tag resolved,
# fleet-exported or defaulted, which is exactly the behaviour the sharded
# branch already had ("get(..., 'induction-scaling') + _LANE").
os.environ.setdefault("EC2_EXPERIMENT_TAG", "induction-scaling")
if _LANE:
    os.environ["EC2_EXPERIMENT_TAG"] += _LANE

# Refuse to run under the RESOLVED retired tag rather than proceed with it: on
# a lost or absent state file, ec2's tag-based recovery reattaches to ANY live
# box carrying the tag and serve_model swaps that box's model out from under
# whatever driver owns it, while `--teardown` terminates it. Compared against
# the literal instead of ec2.EC2_EXPERIMENT_TAG on purpose -- importing ec2
# here would freeze its constants against the environment as it stood BEFORE
# the lines above (see the ordering block at the top of this file).
_RESOLVED_TAG = os.environ["EC2_EXPERIMENT_TAG"]
if _RESOLVED_TAG == "periodic-induction":
    raise SystemExit(
        f"EC2_EXPERIMENT_TAG={_RESOLVED_TAG!r} is the RETIRED periodic-induction "
        "study's default tag (smolbench.evals.providers.ec2's own fallback), not "
        "this study's. Running under it would let tag-based recovery reattach to "
        "any live box carrying it -- swapping that box's served model out from "
        "under another driver -- and would make `--teardown` terminate it. Export "
        "a distinct EC2_EXPERIMENT_TAG (or unset it to get 'induction-scaling')."
    )

_DEFAULT_STATE_FILE = f".ec2_state_induction{_LANE}.json"

# --- 6. smolbench imports -------------------------------------------------
# ec2 at MODULE scope is normally forbidden (InductionExperiment's CRITICAL
# note) precisely because of the import-time freeze; it is safe HERE, and only
# here, because blocks 1 and 5 above have already resolved every EC2_*
# variable it captures. Do not move this line up, and do not add an EC2_*
# mutation below it.
from smolbench.evals.providers import ec2  # noqa: E402
from smolbench.evals.tokenization import for_model  # noqa: E402
from smolbench.induction.experiment import InductionExperiment  # noqa: E402
from smolbench.induction.periodic import (  # noqa: E402
    PeriodicConfig,
    Prompter,
    get_periodic_numeric_quiz,
    get_periodic_zero_info_numeric_quiz,
    numeric_count_query_gen,
)


# --- 7. the served context window, DERIVED from the deploy specs ----------
# Defined immediately above its own call site because that call runs at IMPORT
# time; it cannot live down with the run-time functions in block 8.
def derive_context_limit(lengths: "dict[str, int]") -> int:
    """Return the single context window that every model in `lengths` shares.

    Parameters
    ----------
    lengths : dict[str, int]
        ``{model_key: context_length}`` -- in production
        ``{key: ec2.get_model_context_length(key) for key in MODELS}``, i.e.
        each spec's ``max_model_len``, which is exactly what vLLM was launched
        with.

    Returns
    -------
    int
        The one value every entry agrees on.

    Raises
    ------
    SystemExit
        If `lengths` is EMPTY (there is nothing to derive a limit from), or if
        it holds more than one distinct value; the message names the offending
        keys and the lengths they disagree on. ``SystemExit`` matches this
        file's other config-error convention (``_parse_shard``,
        ``completion_budget``), and a ``raise`` rather than an ``assert``
        survives ``python -O``.

    Notes
    -----
    Non-uniformity is a study-design error, not something to paper over with a
    ``min()`` or a ``max()``: a scaling study cannot let context vary with the
    vendor's own YaRN generosity, or a family's ceiling is confounded with its
    context budget rather than its parameter count. Pure arithmetic over an
    already-materialized mapping; no I/O, no AWS calls.

    Examples
    --------
    >>> derive_context_limit({"a": 131072, "b": 131072})
    131072
    """
    if not lengths:
        raise SystemExit(
            "derive_context_limit: got an empty {model: context_length} mapping, "
            "so there is no context window to derive. Check that MODELS is "
            "non-empty."
        )
    distinct = sorted(set(lengths.values()))
    if len(distinct) > 1:
        # Report grouped BY LENGTH: the actionable question is which
        # checkpoints sit on the odd value, not the full 21-entry mapping.
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


#: The served checkpoints' context window. DERIVED from the deploy specs
#: rather than restated as a literal: it used to be a hand-written 131_072
#: standing in for all 21 EC2_DEPLOY_SPECS entries, so a spec edit on one
#: checkpoint would silently leave this study deriving completion budgets
#: against a context that checkpoint is no longer served with. Deriving it
#: means the two can no longer disagree. Uniformity is load-bearing, not
#: incidental: a scaling study cannot let context vary with the vendor's own
#: YaRN generosity, or a family's ceiling is confounded with its context
#: budget rather than its parameters -- hence derive_context_limit RAISES
#: instead of picking one.
CONTEXT_LIMIT: int = derive_context_limit(
    {key: ec2.get_model_context_length(key) for key in MODELS}
)

# --- 8. study constants, tables, functions and entry point ----------------

#: USER-LOCKED at 0, not the 1776 every prior induction study seeded from -- see
#: the module docstring's "Seeds" section.
BASE_SEED: int = 0

#: USER-LOCKED. 30 is a budget ruling matching every sibling study's R, not a
#: computed optimum; the prospective sizing it was checked against is
#: ``analysis/power_analysis.py``'s recommended-R section. Sibling drivers
#: expose a ``*_N_REPLICATES`` env override; this one deliberately does NOT:
#: the 21-checkpoint comparison is apples-to-apples only at one shared count.
N_REPLICATES: int = 30

#: The four amounts-of-positive-information conditions, matching periodic_moe's
#: exactly. See the module docstring's "The four info arms" section.
INFO_TYPES: tuple[str, ...] = ("intens", "extens", "noise_intens", "zero")

#: Tokens withheld from the completion budget, covering what a count() on one
#: seed's prompt cannot see: the chat template's special/BOS tokens (count()
#: deliberately excludes them -- see tokenization.py's Tokenizer protocol) and
#: cross-seed variation in the sampled labels, compounding over a long
#: extensional listing. Measured ad hoc at design time for this study, on
#: comparable listings, at 1,500-3,700 tokens; sized well above that, so the
#: budget stays safe when the probe below misses the longest seed, at the cost
#: of headroom that would go unused anyway.
TEMPLATE_RESERVE: int = 8_000

#: Seeds probed for the worst-case prompt in completion_budget: the endpoints
#: plus four evenly spaced interior seeds -- catches a mid-range label-length
#: outlier at 6 tokenizer passes instead of 30. Must be >= 2 (the derivation
#: divides by ``PROBE_SEEDS - 1``); completion_budget's docstring says why
#: subsampling suffices.
PROBE_SEEDS: int = 6

#: Floor below which a run is not worth starting: a smaller budget is likely to
#: truncate a CoT checkpoint's reasoning before the final integer, collecting
#: empties (no completion AND no reasoning trace) rather than anything
#: scorable or diagnosable. 48k is judgment, not fitted: periodic_moe's
#: qwen3.5 needed a 65,536-token budget on a comparable listing, so under
#: ~48k is deep truncation territory, while healthy budgets here land near
#: 100k. The floor catches config mistakes; it does not tune throughput.
MIN_VIABLE_BUDGET: int = 48_000

#: TOKENS PER SECOND of single-request decode, the conservative FLOOR the
#: per-model request timeout is sized against (see request_timeout_seconds).
#: Not a prediction of any checkpoint's speed: a faster model simply finishes
#: early and the timeout never fires. What fixes the number is the fan-out --
#: ``evaluate()``'s default concurrency is ec2.py's EC2_MAX_PARALLEL_REQUESTS
#: (default 8) and ``main()`` passes no ``max_parallel``, so up to 8 long CoT
#: generations share ONE box's decode throughput at 100k tokens each. 10 tok/s
#: per in-flight request sits below anything these tiers should realize even
#: fully loaded, which is the point: the derived timeout may only ever err
#: long. For contrast, clearing a 100k budget inside ec2's 600 s default would
#: need >= 167 tok/s, which is not achievable on a 397B/236B MoE.
MIN_DECODE_TOK_S: int = 10

#: ec2.py's own EC2_REQUEST_TIMEOUT_SECONDS default, restated as the floor the
#: derivation may never go BELOW: deriving a SHORTER timeout than the provider
#: already grants would be a regression, not a fix.
REQUEST_TIMEOUT_FLOOR_SECONDS: int = 600

# Byte-identical to periodic_moe's / periodic_divisor's template: the prompt
# WORDING is fixed across every induction study to date, so only the roster
# (model, quiz generator, harmonic set) varies between studies.
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

# Per-request extra args that turn CoT ON for each of the 21 checkpoints.
# TOTAL over MODELS by construction (written out literally, not built from a
# prefix rule): that makes the table itself the audit surface against ec2.py's
# "Reasoning wiring" comment, and a typo in a family prefix can never produce a
# silent KeyError deep inside main() on a billing box. Four rules:
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

# Enforce "TOTAL over MODELS" at import, BEFORE provision() can spend: a
# drifted key would otherwise surface as a KeyError on a billing box. A
# `raise`, not the `assert` this used to be: asserts are stripped under
# `python -O`, which would delete the gate on exactly the automated
# invocations that most need it. The test suite pins the same equality; this
# covers direct invocations.
if COT_ARGS.keys() != MODELS.keys():
    raise RuntimeError(
        "COT_ARGS must be total over MODELS; keys in exactly one of them: "
        f"{sorted(COT_ARGS.keys() ^ MODELS.keys())}"
    )


def make_quizzes(seed: int, model: str) -> "dict[str, tuple]":
    """Generate one replicate's four quizzes, keyed by ``INFO_TYPES`` in that order.

    Uses the plain ``periodic_moe`` baseline config (``n=9`` harmonics, default
    periods 1..9, lcm==2,520), unmodified: the study's independent variable is
    the MODEL, not the quiz. `seed` drives label sampling and, downstream, the
    per-request decoding seed. `model` is the ``EC2_DEPLOY_SPECS``/``MODELS``
    spec key, needed because ``noise_intens`` is padded under THIS model's
    tokenizer; the other three arms stay byte-identical across checkpoints.
    ``for_model`` is looked up as a plain module global, so
    ``tests/induction/test_induction_study.py`` can monkeypatch it (and this
    function) to keep the offline suite from downloading a tokenizer.
    """
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    # Two positional fields (template, query_gen): Prompter's third
    # `substitution` field was removed as dead -- every construction site
    # passed `{}`, and its only consumer was chromatic's retired query_years
    # mechanism -- so the old `Prompter(template, {}, ...)` no longer type-checks.
    prompter = Prompter(template, numeric_count_query_gen)
    intens, extens, noise_intens = get_periodic_numeric_quiz(
        cfg, prompter, tokenizer=for_model(model)
    )
    zero = get_periodic_zero_info_numeric_quiz(cfg, prompter)
    return {"intens": intens, "extens": extens, "noise_intens": noise_intens, "zero": zero}


def probe_seeds(seeds: range) -> "list[int]":
    """Return the ``PROBE_SEEDS`` evenly spaced seeds to probe, sorted and deduplicated.

    Parameters
    ----------
    seeds : range
        The replicate seed range, e.g. ``range(BASE_SEED, BASE_SEED + 30)``.
        Must be non-empty; ``PROBE_SEEDS >= 2`` is required by the derivation
        (it divides by ``PROBE_SEEDS - 1``) and is stated at that constant.

    Returns
    -------
    list[int]
        Ascending, without duplicates, so at most ``PROBE_SEEDS`` entries and
        as few as one. Always contains both ``seeds[0]`` and ``seeds[-1]``.

    Raises
    ------
    IndexError
        If `seeds` is empty (``seeds[0]`` on an empty range).

    Notes
    -----
    This replaces a longer expression that unioned ``seeds[0]`` and
    ``seeds[-1]`` into the same generator and guarded it with a
    ``len(seeds) > 1`` branch. Both extras were provably redundant: the
    generator already yields ``seeds[0]`` at ``i == 0`` (index
    ``0 * (len - 1) // (PROBE_SEEDS - 1) == 0``) and ``seeds[-1]`` at
    ``i == PROBE_SEEDS - 1`` (index ``len - 1``), and at ``len(seeds) == 1``
    every index collapses to 0, so the ``len(seeds) > 1`` branch produced
    ``[seeds[0]]`` exactly as this expression does. The equality is not merely
    argued here: ``tests/induction/test_induction_study.py::
    test_probe_seeds_matches_the_legacy_expression`` vendors the old
    expression verbatim and checks it at every length 1..119.

    Examples
    --------
    >>> probe_seeds(range(0, 30))
    [0, 5, 11, 17, 23, 29]
    """
    return sorted(
        {seeds[i * (len(seeds) - 1) // (PROBE_SEEDS - 1)] for i in range(PROBE_SEEDS)}
    )


def completion_budget(model: str, seeds: range) -> int:
    """Derive the largest completion budget that cannot overflow this model's context.

    Returns ``CONTEXT_LIMIT - worst - TEMPLATE_RESERVE``, where ``worst`` is
    the largest prompt token count over every info type of every probed seed.
    Only ``PROBE_SEEDS`` of `seeds` are probed (see ``probe_seeds``), always
    including both endpoints: every structural driver of prompt length is
    identical across seeds, only the sampled labels vary, and
    ``TEMPLATE_RESERVE`` covers far more than that residual. Pure CPU plus a
    HuggingFace tokenizer fetch, so it runs before anything is provisioned and
    billing.

    The result is ONE number for every model, deliberately not a per-vendor
    dict: a tighter cap on one family would make its accuracy gap inseparable
    from "it had less room to reason", which is precisely the confound a
    scaling study exists to avoid.

    Raises ``SystemExit`` below ``MIN_VIABLE_BUDGET``, which would truncate CoT
    and collect empties.
    """
    tok = for_model(model)
    worst = 0
    for seed in probe_seeds(seeds):
        for quiz in make_quizzes(seed, model).values():
            worst = max(worst, max(tok.count(q.prompt) for q in quiz))
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

    Parameters
    ----------
    budget : int
        The model's ``max_completion_tokens``, i.e. ``completion_budget``'s
        return value -- near 100,000 for this study's checkpoints.

    Returns
    -------
    int
        ``max(REQUEST_TIMEOUT_FLOOR_SECONDS, ceil(budget / MIN_DECODE_TOK_S))``:
        the time `budget` tokens take at the floor decode rate, never less
        than the provider's own default. Monotone non-decreasing in `budget`.

    Notes
    -----
    Without this, every model rides ec2.py's 600 s ``EC2_REQUEST_TIMEOUT_SECONDS``
    default while being handed a ~100k-token CoT budget; clearing 100k tokens
    in 600 s needs >= 167 tok/s of single-request decode on a 397B/236B MoE,
    which is not achievable.

    WARNING -- the two failure directions are NOT symmetric, which is what
    justifies erring long. Retries never re-seed (ec2.py re-POSTs the
    byte-identical seeded body), so a timeout SHORTER than the generation
    times out again on EVERY attempt: the longest chains are silently censored
    and the CoT-length distribution is truncated at the top, on the arm that
    carries this study's headline contrast. An over-long timeout costs only
    wall-clock, and only on a request that was going to fail anyway.

    NO upper clamp is applied, on purpose. A ceiling that never binds is dead
    code -- exactly what ``BUDGET_CAP`` was before it was deleted in this same
    pass -- and a ceiling that DOES bind reintroduces the censoring this
    function exists to remove. This is a floor, never a cap.

    Examples
    --------
    >>> request_timeout_seconds(1)          # floored at the provider default
    600
    >>> request_timeout_seconds(100_000)    # 100k tokens at 10 tok/s
    10000
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
    # INDUCTION_FORCE_RERUN: re-collect replicates past the resume-skip (syntax
    # in _parse_force_seeds); combines with INDUCTION_SHARD, a shard forcing
    # only the seeds it owns. Reads are EARLIEST-wins (see
    # smolbench/evals/results_store.py), so a forced re-run appends to the S3
    # log but does NOT supersede the original on read.
    force_seeds=_parse_force_seeds(
        os.environ.get("INDUCTION_FORCE_RERUN", ""),
        range(BASE_SEED, BASE_SEED + N_REPLICATES),
    ),
)


def selected_models() -> "tuple[str, ...]":
    """Return the spec keys to run: ``INDUCTION_MODELS``, or all of ``MODELS``.

    Always emitted in ``MODELS`` declaration order, whatever order the
    environment listed them in; that family-grouped order is this study's
    canonical order (matching ``ec2.py``'s roster), keeps a standalone
    unfiltered run deterministic, and is the same order the lane tag at the top
    of this file is built in.

    Raises ``SystemExit`` -- before any instance is provisioned -- if
    ``INDUCTION_MODELS`` names an unknown key, or is SET but resolves to ZERO
    keys (e.g. ``","``, non-empty and so past the "unset selects all" branch).
    The empty case is a config mistake, not a no-op: ``main()`` no longer
    provisions when nothing is outstanding, so a zero-model run would no longer
    leave a GPU box billing, but it WOULD exit 0 having quietly done nothing
    and hidden the typo.
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

    Makes LIVE AWS calls on every path except ``--teardown``, a failed argument
    parse, and a roster with NO outstanding replicates (which returns before
    provisioning), and never tears the instance down otherwise -- see the
    module docstring's "Lifecycle contract and COST" section. Each model's
    ``request_timeout`` is DERIVED from its completion budget by
    ``request_timeout_seconds`` rather than left at the provider's 600 s
    default, which a ~100k-token CoT budget cannot fit inside. `argv` is a
    parameter so a test or notebook cell can call this without a subprocess.
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

    # Warm every tokenizer and derive its completion budget BEFORE provisioning
    # anything: an HF download failure or an under-budget SystemExit must never
    # land between a billing GPU box and the first inference request.
    seeds = range(BASE_SEED, BASE_SEED + EXPERIMENT.n_replicates)
    budgets: dict[str, int] = {}
    for model in models:
        logging.info(f"warming tokenizer for {model}: {for_model(model).name}")
        budgets[model] = completion_budget(model, seeds)

    # COST GATE: provision only if there is work. EXPERIMENT.run() already
    # skips the serve for a finished model, but provision() ran before it and
    # unconditionally, and this driver deliberately never tears down -- so
    # re-running a completed lane booted a spot box that did nothing and then
    # billed until the idle watchdog fired. The check is free: run() calls the
    # same has_outstanding() per model anyway.
    outstanding = [m for m in models if EXPERIMENT.harness.has_outstanding(m)]
    if not outstanding:
        logging.info(
            f"no outstanding replicates for {list(models)}; nothing provisioned "
            "and nothing to run"
        )
        return

    EXPERIMENT.provision()
    # Iterate `models`, not `outstanding`: run() re-checks has_outstanding per
    # model and returns without serving when there is none, the budgets are
    # already warmed for every selected model, and summarize() should still
    # report the finished ones in this lane.
    for model in models:
        EXPERIMENT.run(
            model,
            extra_args={"max_completion_tokens": budgets[model], **COT_ARGS[model]},
            request_timeout=request_timeout_seconds(budgets[model]),
        )
        EXPERIMENT.summarize(model)
    # Deliberately NO EXPERIMENT.teardown() here -- see the module docstring's
    # "Lifecycle contract and COST" section. This box may be reused by the
    # deduction phase after this process exits.
    print(f"INDUCTION STUDY RUN COMPLETE: {list(models)} (no teardown -- fleet-owned)",
          flush=True)


if __name__ == "__main__":
    main()
