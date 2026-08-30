"""Headless driver for the FAMILY-LADDER SCALING induction study.

The quiz is held fixed (the plain ``periodic_moe`` baseline, ``n=9``
harmonics, unmodified) while the MODEL varies -- 7 vendor families x 3 rungs =
the 21 checkpoints in ``MODELS`` -- so accuracy reads as a function of
parameter count within a family. Deployment facts live in
``smolbench.evals.providers.ec2.EC2_DEPLOY_SPECS``; this file is the single
source of truth for the STUDY's config, and
``notebooks/induction/induction_eval.ipynb`` imports every module-level name
below instead of re-declaring it (pinned by
``tests/induction/test_induction_study.py``). Info arms match
``periodic_moe``'s: ``intens``, ``extens``, ``noise_intens`` (``intens``
whitespace-padded to ``extens``'s token count under the SERVED model's own
tokenizer -- a length control, not a content control), and ``zero`` (empty
context, chance floor). CoT is ON for all 21 checkpoints.

Environment: ``INDUCTION_SHARD`` (``"index/count"``; splits ONE model's
replicates); ``INDUCTION_MODELS`` (comma-separated SPEC KEYS, not analysis
tags; unset/empty selects all 21); ``INDUCTION_STATE_FILE`` (the only way to
redirect this process's repo-root-anchored EC2 state file --
``InductionExperiment._apply_env`` overwrites the bare ``EC2_STATE_FILE``
shell variable from the ``state_file`` constructor argument on every
provision/run/teardown). The fleet MUST set a distinct state file per lane:
two lanes sharing one would have the second ``provision()`` reattach to the
first's instance and swap the served model out from under it.

LIFECYCLE and COST: ``main()`` calls ``EXPERIMENT.teardown()`` only behind
``--teardown``, which is for STANDALONE use only -- the fleet supervisor
(``scripts/fleet/run_fleet.py``) owns instance lifecycle and reuses each lane's
box for a later deduction-phase lane, so a teardown here would terminate an
instance that phase is about to reattach to. ``provision()`` and ``run()`` are
LIVE AWS spot spend, billed while each box is up, on tiers from g6e.4xlarge to
p6-b200.48xlarge; standalone this serves all 21 checkpoints in turn on ONE
reconfigured instance, under the fleet up to 21 concurrent boxes. Verify
``INDUCTION_MODELS`` before invoking outside the fleet.

Run (repo root):
    .venv/bin/python notebooks/induction/run_study.py
"""

import argparse
import logging
import os
import string
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
# Anchored via __file__, never cwd. This MUST land before
# smolbench.evals.providers.ec2 is imported anywhere: ec2.py freezes its EC2_*
# constants at import time (see InductionExperiment's module docstring,
# "CRITICAL: no smolbench.evals.providers.ec2 import at module scope"). NOT
# override=True: under the fleet, the supervisor sets up a per-lane
# environment (INDUCTION_MODELS, INDUCTION_STATE_FILE, EC2_EXPERIMENT_TAG,
# ...) before this file runs. keys.env populating already-set variables
# would clobber that per-lane config with this file's own local
# defaults.
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)


def _parse_shard(var: str) -> "tuple[int, int] | None":
    """Parse environment variable `var` as ``"index/count"``; ``None`` if unset/empty.

    Sharding splits ONE model's replicates across N processes/instances,
    orthogonally to this study's one-model-per-box fan-out. Raises
    ``SystemExit`` immediately at import if `var` is set but is not parseable
    as ``"int/int"``, or fails ``count >= 1`` / ``0 <= index < count`` --
    rather than silently running unsharded or crashing deep inside
    ``InductionExperiment``.
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

    `raw` is ``""`` (off -> ``None``), ``"1"`` (every seed in `full_range`),
    or ``"a-b"`` (that inclusive subrange, validated against `full_range`).
    Raises ``SystemExit`` immediately at import on an unparseable value or a
    subrange outside `full_range`, never silently as a no-op resume.
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


SHARD = _parse_shard("INDUCTION_SHARD")

# A shard needs its OWN AWS tag and state file -- without that, shard 1
# reattaches to shard 0's live box and swaps the served model out from under
# a run in progress (the exact collision the periodic_divisor driver hit
# first). This code derives both from the lane, rather than asking every
# caller to remember two more environment variables, which removes that
# footgun.
#
# This MUST execute before smolbench.evals.providers.ec2 is imported below: ec2.py
# freezes its EC2_* constants from os.environ at import time, so a tag set
# afterwards is silently ignored. Unsharded runs get an empty suffix.
_LANE = ""
if SHARD is not None:
    _models = os.environ.get("INDUCTION_MODELS", "").strip().replace(",", "-")
    _LANE = (f"-{_models}" if _models else "") + "-s{}of{}".format(*SHARD)
    os.environ["EC2_EXPERIMENT_TAG"] = (
        os.environ.get("EC2_EXPERIMENT_TAG", "induction-scaling") + _LANE
    )
_DEFAULT_STATE_FILE = f".ec2_state_induction{_LANE}.json"

from smolbench.evals.tokenization import for_model  # noqa: E402
from smolbench.induction.experiment import InductionExperiment  # noqa: E402
from smolbench.induction.periodic import (  # noqa: E402
    PeriodicConfig,
    Prompter,
    get_periodic_numeric_quiz,
    get_periodic_zero_info_numeric_quiz,
    numeric_count_query_gen,
)

#: USER-LOCKED. Every prior induction study seeded from 1776. This study
#: deliberately uses 0, so its seed range (0..29) can never silently
#: alias a sibling study's. See the module docstring's "Seeds" section.
BASE_SEED: int = 0

#: USER-LOCKED. Unlike every sibling driver's ``*_N_REPLICATES``
#: environment override, this value is NOT environment-overridable: the
#: family-ladder comparison across 21 checkpoints is only
#: apples-to-apples if every checkpoint collects the same replicate
#: count.
N_REPLICATES: int = 30

#: The four amounts-of-positive-information conditions, matching
#: periodic_moe's exactly. See the module docstring's "The four info
#: arms" section.
INFO_TYPES: tuple[str, ...] = ("intens", "extens", "noise_intens", "zero")

#: The served checkpoints' context window. Every EC2_DEPLOY_SPECS entry
#: in this study's roster serves at max_model_len=131072 uniformly (see
#: that table's roster comment). A scaling study cannot let context vary
#: with the vendor's own YaRN generosity, or a family's ceiling would be
#: confounded with its context budget, rather than its parameter count.
CONTEXT_LIMIT: int = 131_072

#: Tokens withheld from the completion budget. This covers what a
#: count() on one seed's prompt cannot see. That includes the chat
#: template's own special/BOS tokens (count() deliberately excludes
#: them -- see the Tokenizer protocol docstring in tokenization.py). It
#: also includes cross-seed variation in the randomly-sampled labels,
#: which compounds over a long extensional listing. It is sized
#: generously (sibling studies measured this reserve in the 1,500-3,700
#: token range on comparable listings), so the derived budget stays
#: safe even when the seed probe below misses the single longest seed
#: across all 30. It costs only completion headroom that would
#: otherwise go unused.
TEMPLATE_RESERVE: int = 8_000

#: Seeds sampled when measuring the worst-case prompt in
#: completion_budget. See that function's docstring for why bracketed
#: subsampling suffices.
PROBE_SEEDS: int = 6

#: Floor below which a run is not worth starting. A completion budget
#: below this is likely to truncate a CoT checkpoint's reasoning before
#: it reaches the final integer. That collects empties (no completion AND
#: no reasoning trace), not data that can be scored, marked invalid, or
#: even diagnosed after the fact.
MIN_VIABLE_BUDGET: int = 48_000

#: Ceiling applied AFTER the derived per-model budget below. A single
#: plain int, NOT a per-model dict -- see completion_budget's docstring
#: for why a cross-vendor SCALING study cannot let this vary by vendor.
BUDGET_CAP: int = CONTEXT_LIMIT

# Byte-identical to periodic_moe's / periodic_divisor's template. The
# prompt WORDING stays fixed across every induction study to date. So the
# only thing that ever varies between studies is the roster (model, quiz
# generator, or, in periodic_divisor's case, the harmonic set) that fills
# in $positive_info / $seq_len / $label.
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

# Spec key (smolbench.evals.providers.ec2.EC2_DEPLOY_SPECS key, also vLLM's
# --served-model-name) -> short analysis tag used in result directory
# names and figure legends. This is exactly EC2_DEPLOY_SPECS's 21
# family-ladder entries: every key except the "qwen2.5-1.5b" single-GPU
# smoke entry. Order is the study's canonical order -- see
# selected_models' docstring for why this matters beyond mere
# readability.
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

# Per-request extra args that turn CoT ON for each of the 21 checkpoints.
# This table is TOTAL over MODELS by construction (written out literally,
# not built from a prefix rule). That makes the table itself the audit
# surface against ec2.py's "Reasoning wiring" comment, and it means a
# typo in a family prefix can never produce a silent KeyError deep inside
# main() on a billing box. Four rules, summarized here (full rationale
# for each is in the module docstring):
#   1. Qwen3.5 / Nemotron-3 / Gemma-4 / GLM-4.x / EXAONE / K-EXAONE:
#      {"chat_template_kwargs": {"enable_thinking": True}}.
#   2. DeepSeek V4-Flash / V3.1 / V4-Pro: {"chat_template_kwargs":
#      {"thinking": True}} -- note the DIFFERENT kwarg name from rule 1.
#   3. Ministral-3 (3B/8B/14B): {} -- its think protocol is switched on by
#      ec2.py's injected system_prompt, not by a chat_template_kwarg.
#   4. Gemma-4-* and EXAONE-4.0-32B in particular NEED their explicit
#      "enable_thinking": True: both checkpoints' shipped templates default
#      thinking OFF, so omitting the kwarg would silently serve them
#      non-reasoning while every other checkpoint in the study reasons.
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


def make_quizzes(seed: int, model: str) -> "dict[str, tuple]":
    """Generate one replicate's four quizzes, keyed by ``INFO_TYPES`` in that order.

    Uses the plain ``periodic_moe`` baseline config (``n=9`` harmonics, default
    consecutive-integer periods 1..9, lcm==2,520), unmodified: the study's
    independent variable is the MODEL, not the quiz. `seed` drives label
    sampling and, downstream in ``ReplicateHarness``, the per-request decoding
    seed. `model` is the checkpoint's ``EC2_DEPLOY_SPECS``/``MODELS`` spec key,
    required because ``noise_intens`` is a TOKEN-LENGTH control padded to the
    matching ``extens`` prompt's token count under THIS model's own tokenizer
    (``for_model(model)``); a character-matched pad would systematically over-
    or under-pad. The other three arms are model-independent and stay
    byte-identical across checkpoints.

    ``for_model`` is called by plain module-global lookup, so
    ``tests/induction/test_induction_study.py`` can monkeypatch it (and this
    function) to keep the offline suite from downloading a tokenizer.
    """
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    prompter = Prompter(template, {}, numeric_count_query_gen)
    intens, extens, noise_intens = get_periodic_numeric_quiz(
        cfg, prompter, tokenizer=for_model(model)
    )
    zero = get_periodic_zero_info_numeric_quiz(cfg, prompter)
    return {"intens": intens, "extens": extens, "noise_intens": noise_intens, "zero": zero}


def completion_budget(model: str, seeds: range) -> int:
    """Derive the largest completion budget that cannot overflow this model's context.

    Returns ``min(CONTEXT_LIMIT - worst - TEMPLATE_RESERVE, BUDGET_CAP)``,
    where ``worst`` is the largest prompt token count over every info type of
    every probed seed. `seeds` is the full seed range this study will send to
    `model`, but only ``PROBE_SEEDS`` of them are probed, always including both
    endpoints: every structural driver of prompt length is identical across
    seeds, only the sampled labels vary, and ``TEMPLATE_RESERVE`` covers far
    more than that residual. Pure CPU plus a HuggingFace tokenizer fetch, so
    this runs before anything is provisioned and billing. ``BUDGET_CAP`` is a
    single ``int`` (== ``CONTEXT_LIMIT``), not a per-model dict: a tighter cap
    on one family would make its accuracy gap inseparable from "it had less
    room to finish its reasoning", so the ``min()`` is a documented no-op guard
    against a future edit reintroducing a per-vendor cap. Raises
    ``SystemExit`` if the derived budget falls below ``MIN_VIABLE_BUDGET``;
    such a run would truncate CoT and collect empties, not scorable data.
    """
    tok = for_model(model)
    picks = sorted({seeds[0], seeds[-1],
                    *(seeds[i * (len(seeds) - 1) // (PROBE_SEEDS - 1)]
                      for i in range(PROBE_SEEDS))}) if len(seeds) > 1 else list(seeds)
    worst = 0
    for seed in picks:
        for quiz in make_quizzes(seed, model).values():
            worst = max(worst, max(tok.count(q.prompt) for q in quiz))
    budget = min(CONTEXT_LIMIT - worst - TEMPLATE_RESERVE, BUDGET_CAP)
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


# notebook_dir="induction" is what makes results_store.experiment_name()
# derive this experiment's S3 log path segment as "induction". So every
# replicate this study collects lands under S3 keys shaped
# induction/<spec-key>/seed=<seed>/<info>--<run_ts>.yaml, distinct from
# every sibling study's own notebook_dir-derived prefix.
EXPERIMENT = InductionExperiment(
    notebook_dir="induction",
    archetype_tags=MODELS,
    make_quizzes=make_quizzes,
    info_types=INFO_TYPES,
    n_replicates=N_REPLICATES,
    base_seed=BASE_SEED,
    state_file=os.environ.get("INDUCTION_STATE_FILE", _DEFAULT_STATE_FILE),
    shard=SHARD,
    # INDUCTION_FORCE_RERUN: re-collect replicates past the resume-skip.
    # NOTE: reads are EARLIEST-wins (see smolbench/evals/results_store.py),
    # so a forced re-run appends to the S3 log but does NOT supersede the
    # original on read -- voiding data requires explicit exclusion.
    # "1" forces the full seed range. "a-b" forces the inclusive seed
    # subrange a..b. Combines with INDUCTION_SHARD (a shard forces only the
    # forced seeds it owns).
    force_seeds=_parse_force_seeds(
        os.environ.get("INDUCTION_FORCE_RERUN", ""),
        range(BASE_SEED, BASE_SEED + N_REPLICATES),
    ),
)


def selected_models() -> "tuple[str, ...]":
    """Return the spec keys to run: ``INDUCTION_MODELS``, or all of ``MODELS``.

    Always emitted in ``MODELS`` declaration order, whatever order the
    environment variable listed them in. That family-grouped order is this
    study's canonical order (matching ``ec2.py``'s roster), which keeps a
    standalone unfiltered run deterministic.

    Raises ``SystemExit`` -- before any instance is provisioned -- if
    ``INDUCTION_MODELS`` names a key not in ``MODELS``, or is SET but resolves
    to ZERO keys (e.g. ``","``, which is non-empty and so misses the "unset
    selects all" branch). The empty case matters because ``main()`` provisions
    unconditionally and never tears down, so it would leave a GPU box billing
    with nothing driving it.
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

    Makes LIVE AWS calls on every path except ``--teardown`` and a failed
    argument parse, and never tears the instance down otherwise (see the module
    docstring's LIFECYCLE and COST note). `argv` is a parameter so a test or
    notebook cell can call this without a subprocess.
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

    # Warm every model's tokenizer and derive its completion budget
    # BEFORE provisioning anything. An HF tokenizer-download failure or
    # an under-budget SystemExit must never land between a billing GPU
    # box and the first inference request.
    seeds = range(BASE_SEED, BASE_SEED + EXPERIMENT.n_replicates)
    budgets: dict[str, int] = {}
    for model in models:
        logging.info(f"warming tokenizer for {model}: {for_model(model).name}")
        budgets[model] = completion_budget(model, seeds)

    EXPERIMENT.provision()
    for model in models:
        EXPERIMENT.run(
            model,
            extra_args={"max_completion_tokens": budgets[model], **COT_ARGS[model]},
        )
        EXPERIMENT.summarize(model)
    # NOTE: deliberately NO EXPERIMENT.teardown() here. See the module
    # docstring's "Lifecycle contract" section. The fleet supervisor owns
    # instance lifecycle, and this box may be reused by the deduction
    # phase after this process exits. A teardown here would terminate it
    # out from under that reattachment.
    print(f"INDUCTION STUDY RUN COMPLETE: {list(models)} (no teardown -- fleet-owned)",
          flush=True)


if __name__ == "__main__":
    main()
