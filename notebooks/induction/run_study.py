"""Run the family-ladder scaling induction study.

Each lane needs a distinct state file and tag to prevent EC2 reattachment from
switching its served model. Completion budgets reserve template overhead and
timeouts scale with them to avoid censoring long CoT responses.
"""

import argparse
import logging
import os
import string
from math import ceil
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

# EC2 reads environment constants at import time, so mutations precede its import.
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)


def _parse_shard(var: str) -> "tuple[int, int] | None":
    """Parse environment variable `var` as ``"index/count"``; ``None`` if unset/empty.

    Parameters
    ----------
    var : str
        Environment variable name.

    Returns
    -------
    tuple[int, int] | None
        Shard index and count, or ``None``.

    Raises
    ------
    SystemExit
        Invalid shard syntax or bounds.
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

    Parameters
    ----------
    raw : str
        Rerun setting.
    full_range : range
        Valid seeds.

    Returns
    -------
    frozenset[int] | None
        Rerun seeds, or ``None``.

    Raises
    ------
    SystemExit
        Invalid rerun setting or bounds.
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

# Use the canonical roster to prevent duplicate-map drift.
from smolbench.evals.study_config import load_study_config, roster_keys, tag_for  # noqa: E402

MODELS: dict[str, str] = {key: tag_for(key) for key in roster_keys()}

# Shards need distinct tags and state files to prevent model swaps.
_LANE = ""
if SHARD is not None:
    # Canonical order makes equivalent model selections share a lane.
    _requested = [
        key.strip()
        for key in os.environ.get("INDUCTION_MODELS", "").split(",")
        if key.strip()
    ]
    _chosen = set(_requested)
    _lane_models = [model for model in MODELS if model in _chosen]
    _lane_models += [key for key in dict.fromkeys(_requested) if key not in MODELS]
    _LANE = ("-" + "-".join(_lane_models) if _lane_models else "") + "-s{}of{}".format(
        *SHARD
    )

# Preserve a fleet-provided tag.
os.environ.setdefault("EC2_EXPERIMENT_TAG", load_study_config().fleet.standalone_tag)
if _LANE:
    os.environ["EC2_EXPERIMENT_TAG"] += _LANE

# Validate before EC2 imports freeze the environment.
from smolbench.evals.experiment import validate_experiment_tag  # noqa: E402

_RESOLVED_TAG = os.environ["EC2_EXPERIMENT_TAG"]
try:
    validate_experiment_tag(_RESOLVED_TAG, _LANE)
except ValueError as exc:
    raise SystemExit(str(exc)) from exc

_DEFAULT_STATE_FILE = f".ec2_state_induction{_LANE}.json"

from smolbench.evals.providers import ec2  # noqa: E402
from smolbench.evals import Numeric  # noqa: E402
from smolbench.evals.tokenization import for_model  # noqa: E402
from smolbench.induction._common import Prompter, RenderedQuery, quizzes_from_prompts  # noqa: E402
from smolbench.induction.experiment import InductionExperiment  # noqa: E402
from smolbench.induction.periodic import (  # noqa: E402
    CONDITIONS,
    PeriodicConfig,
    get_periodic_prompts,
    numeric_count_query_gen,
)


def derive_context_limit(lengths: "dict[str, int]") -> int:
    """Return the single context window that every model in `lengths` shares.

    Parameters
    ----------
    lengths : dict[str, int]
        Model context lengths.

    Returns
    -------
    int
        Shared context length.

    Raises
    ------
    SystemExit
        Empty or non-uniform lengths; varying context confounds model scaling.
    """
    if not lengths:
        raise SystemExit(
            "derive_context_limit: got an empty {model: context_length} mapping, "
            "so there is no context window to derive. Check that MODELS is "
            "non-empty."
        )
    distinct = sorted(set(lengths.values()))
    if len(distinct) > 1:
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


#: Derived from specs so model context cannot confound scaling.
CONTEXT_LIMIT: int = derive_context_limit(
    {key: ec2.get_model_context_length(key) for key in MODELS}
)

#: Distinct from sibling-study seed ranges.
BASE_SEED: int = 0

#: Fixed shared replicate count prevents unequal comparisons.
N_REPLICATES: int = 30

#: Derived from the canonical condition mapping.
INFO_TYPES: tuple[str, ...] = tuple(CONDITIONS)

#: Covers special tokens and cross-seed prompt variation missed by probes.
TEMPLATE_RESERVE: int = 8_000

#: Must be at least 2 for evenly spaced endpoint probes.
PROBE_SEEDS: int = 6

#: Avoids CoT truncation that yields unscorable responses.
MIN_VIABLE_BUDGET: int = 48_000

#: Conservative per-request decode rate under shared-box fan-out.
MIN_DECODE_TOK_S: int = 10

#: Avoids an EC2 environment override below its default timeout.
REQUEST_TIMEOUT_FLOOR_SECONDS: int = 600

# Prompt wording is shared across induction studies.
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

#: Kept separate so a changed template cannot silently leak its range.
RANGE_CLAUSE: str = " 1 through $seq_len"

if RANGE_CLAUSE not in template.template:
    # ``replace`` would otherwise silently retain the range.
    raise RuntimeError(
        f"RANGE_CLAUSE {RANGE_CLAUSE!r} not found in template.template; "
        "the study template's range clause was edited without updating "
        "RANGE_CLAUSE, which would silently make the zero arm leak seq_len."
    )

def _zero_template(base: string.Template) -> string.Template:
    """Derive the zero condition's range-free question from `base`.

    Uses one source template so the range-free form cannot drift.

    Parameters
    ----------
    base : string.Template
        Template to make range-free.

    Returns
    -------
    string.Template
        Range-free template.
    """
    return string.Template(base.template.replace(RANGE_CLAUSE, ""))


# Explicit per-model entries prevent incorrect family-prefix inference.
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

# Raise rather than assert: optimization must not remove this billing gate.
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

    The quiz is fixed so the model is the independent variable.

    Parameters
    ----------
    seed : int
        Replicate seed.
    model : str
        Tokenizer model for the padded arm.

    Returns
    -------
    list[RenderedQuery]
        Rendered replicate queries.
    """
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    prompter = Prompter(
        template, numeric_count_query_gen, range_free_template=_zero_template(template)
    )
    return list(
        get_periodic_prompts(cfg, prompter, tokenizer=for_model(model), conditions=CONDITIONS)
    )


def make_quizzes(seed: int, model: str) -> "dict[str, tuple]":
    """Generate one replicate's four quizzes, keyed by ``INFO_TYPES`` in that order.

    Parameters
    ----------
    seed : int
        Replicate seed.
    model : str
        Rendering model.

    Returns
    -------
    dict[str, tuple]
        Quizzes by information type.
    """
    return quizzes_from_prompts(rendered_queries(seed, model), Numeric, CONDITIONS)


def probe_seeds(seeds: range) -> "list[int]":
    """Return the ``PROBE_SEEDS`` evenly spaced seeds to probe, sorted and deduplicated.

    Includes both endpoints; ``PROBE_SEEDS`` must be at least 2.

    Parameters
    ----------
    seeds : range
        Non-empty seed range.

    Returns
    -------
    list[int]
        Sorted unique probe seeds.
    """
    return sorted(
        {seeds[i * (len(seeds) - 1) // (PROBE_SEEDS - 1)] for i in range(PROBE_SEEDS)}
    )


def completion_budget(model: str, seeds: range) -> int:
    """Derive the largest completion budget that cannot overflow this model's context.

    The reserve covers label variation between seed probes.

    Parameters
    ----------
    model : str
        Model to budget.
    seeds : range
        Seed range for probes.

    Returns
    -------
    int
        Model completion budget.

    Raises
    ------
    SystemExit
        Budget below the viable CoT floor.
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

    It is a floor, not a cap, because short retries censor long CoT responses.

    Parameters
    ----------
    budget : int
        Completion budget.

    Returns
    -------
    int
        Read timeout in seconds.
    """
    return max(REQUEST_TIMEOUT_FLOOR_SECONDS, ceil(budget / MIN_DECODE_TOK_S))


# Separates this study's result-store keys from sibling studies.
EXPERIMENT = InductionExperiment(
    notebook_dir="induction",
    archetype_tags=MODELS,
    make_quizzes=make_quizzes,
    info_types=INFO_TYPES,
    n_replicates=N_REPLICATES,
    base_seed=BASE_SEED,
    state_file=os.environ.get("INDUCTION_STATE_FILE", _DEFAULT_STATE_FILE),
    shard=SHARD,
    # Sharding limits forced reruns to owned seeds.
    force_seeds=_parse_force_seeds(
        os.environ.get("INDUCTION_FORCE_RERUN", ""),
        range(BASE_SEED, BASE_SEED + N_REPLICATES),
    ),
)


def selected_models() -> "tuple[str, ...]":
    """Return the spec keys to run: ``INDUCTION_MODELS``, or all of ``MODELS``.

    Canonical order keeps lane selection deterministic; invalid selections fail.
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

    Provisions only when selected models have outstanding replicates.

    Parameters
    ----------
    argv : list[str] | None, optional
        Optional command-line arguments.
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

    # Fail before provisioning if tokenizer or budget setup fails.
    seeds = range(BASE_SEED, BASE_SEED + EXPERIMENT.n_replicates)
    budgets: dict[str, int] = {}
    for model in models:
        logging.info(f"warming tokenizer for {model}: {for_model(model).name}")
        budgets[model] = completion_budget(model, seeds)

    # Avoid provisioning an idle billing instance.
    outstanding = [m for m in models if EXPERIMENT.harness.has_outstanding(m)]
    if not outstanding:
        logging.info(
            f"no outstanding replicates for {list(models)}; nothing provisioned "
            "and nothing to run"
        )
        return

    EXPERIMENT.provision()
    for model in models:
        EXPERIMENT.run(
            model,
            extra_args={"max_completion_tokens": budgets[model], **COT_ARGS[model]},
            request_timeout=request_timeout_seconds(budgets[model]),
        )
        EXPERIMENT.summarize(model)
    # The fleet may reuse this instance for deduction.
    print(f"INDUCTION STUDY RUN COMPLETE: {list(models)} (no teardown -- fleet-owned)",
          flush=True)


if __name__ == "__main__":
    main()
