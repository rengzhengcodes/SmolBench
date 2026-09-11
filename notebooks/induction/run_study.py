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
# Not ``override=True``: the fleet exports a per-lane environment that
# ``keys.env`` must not clobber.
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)


def _parse_shard(var: str) -> "tuple[int, int] | None":
    """Parse environment variable `var` as ``"index/count"``; ``None`` if unset/empty.

    Parameters
    ----------
    var : str
    Returns
    -------
    tuple[int, int] | None
    Raises
    ------
    SystemExit
    """
    raw = os.environ.get(var, "").strip()
    if not raw:
        return None
    try:
        index, count = (int(part) for part in raw.split("/", 1))
    except ValueError as exc:
        raise SystemExit(
            f"{var}={raw!r}: expected 'index/count', e.g. {var}=0/3"
        ) from exc
    if count < 1 or not 0 <= index < count:
        raise SystemExit(f"{var}={raw!r}: need count >= 1 and 0 <= index < count")
    return index, count


def _parse_force_seeds(raw: str, full_range: range) -> "frozenset[int] | None":
    """Parse ``INDUCTION_FORCE_RERUN`` into the set of seeds to re-collect.

    Parameters
    ----------
    raw : str
    full_range : range
    Returns
    -------
    frozenset[int] | None
    Raises
    ------
    SystemExit
    """
    raw = raw.strip()
    if not raw:
        return None
    if raw == "1":
        return frozenset(full_range)
    try:
        lo, hi = (int(part) for part in raw.split("-", 1))
    except ValueError as exc:
        raise SystemExit(
            f"INDUCTION_FORCE_RERUN={raw!r}: expected '1' or 'a-b' (e.g. '0-11')"
        ) from exc
    if lo > hi or lo < full_range.start or hi >= full_range.stop:
        raise SystemExit(
            f"INDUCTION_FORCE_RERUN={raw!r}: subrange must lie inside "
            f"{full_range.start}..{full_range.stop - 1}"
        )
    return frozenset(range(lo, hi + 1))


SHARD = _parse_shard("INDUCTION_SHARD")

# Use the canonical roster to prevent duplicate-map drift.
from smolbench.evals.study_config import (  # noqa: E402
    load_study_config,
    roster_keys,
    tag_for,
)

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
    _LANE = ("-" + "-".join(_lane_models) if _lane_models else "") + (
        f"-s{SHARD[0]}of{SHARD[1]}"
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

from smolbench.evals import Numeric  # noqa: E402
from smolbench.evals.providers import ec2  # noqa: E402
from smolbench.evals.tokenization import for_model  # noqa: E402
from smolbench.induction._common import (  # noqa: E402
    Prompter,
    RenderedQuery,
    quizzes_from_prompts,
)
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
    Returns
    -------
    int
    Raises
    ------
    SystemExit
    """
    if not lengths:
        raise SystemExit("derive_context_limit: empty {model: context_length} mapping")
    distinct = sorted(set(lengths.values()))
    if len(distinct) > 1:
        # A family's ceiling must differ from its siblings' by parameter
        # count, not by the vendor's served context budget.
        detail = "; ".join(
            f"{length} -> {sorted(k for k, v in lengths.items() if v == length)}"
            for length in distinct
        )
        raise SystemExit(
            f"roster is served with {len(distinct)} different context lengths "
            f"({detail}); align EC2_DEPLOY_SPECS max_model_len or drop the outlier."
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

#: Endpoints plus four interior seeds: 6 tokenizer passes instead of 30. Must be >= 2.
PROBE_SEEDS: int = 6

#: Avoids CoT truncation that yields unscorable responses; periodic_moe's
#: qwen3.5 needed a 65,536-token budget on a comparable listing, so under
#: ~48k is deep truncation territory.
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
    raise RuntimeError(f"RANGE_CLAUSE {RANGE_CLAUSE!r} not found in template.template.")


def _zero_template(base: string.Template) -> string.Template:
    """Derive the zero condition's range-free question from `base`.

    Uses one source template so the range-free form cannot drift.

    Parameters
    ----------
    base : string.Template
    Returns
    -------
    string.Template
    """
    return string.Template(base.template.replace(RANGE_CLAUSE, ""))


# Derived from the roster so omissions cannot reach a billing box.
# Ministral needs no toggle; DeepSeek spells it ``thinking``; the rest take
# ``enable_thinking`` -- Gemma-4-* and EXAONE default thinking OFF, so their
# True is load-bearing.
COT_ARGS: dict[str, dict] = {
    key: (
        {}
        if key.startswith("ministral")
        else {
            "chat_template_kwargs": {
                "thinking" if key.startswith("deepseek") else "enable_thinking": True
            }
        }
    )
    for key in roster_keys()
}


def rendered_queries(seed: int, model: str) -> "list[RenderedQuery]":
    """Render one replicate's queries, all four ``CONDITIONS`` arms of each.

    The quiz is fixed so the model is the independent variable.

    Parameters
    ----------
    seed : int
    model : str
    Returns
    -------
    list[RenderedQuery]
    """
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    prompter = Prompter(
        template, numeric_count_query_gen, range_free_template=_zero_template(template)
    )
    return list(
        get_periodic_prompts(
            cfg, prompter, tokenizer=for_model(model), conditions=CONDITIONS
        )
    )


def make_quizzes(seed: int, model: str) -> "dict[str, tuple]":
    """Generate one replicate's four quizzes, keyed by ``INFO_TYPES`` in that order.

    Parameters
    ----------
    seed : int
    model : str
    Returns
    -------
    dict[str, tuple]
    """
    return quizzes_from_prompts(rendered_queries(seed, model), Numeric, CONDITIONS)


def probe_seeds(seeds: range) -> "list[int]":
    """Return the ``PROBE_SEEDS`` evenly spaced seeds to probe, sorted and deduplicated.

    Includes both endpoints; ``PROBE_SEEDS`` must be at least 2.

    Parameters
    ----------
    seeds : range
    Returns
    -------
    list[int]
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
    seeds : range
    Returns
    -------
    int
    Raises
    ------
    SystemExit
    """
    worst = 0
    for seed in probe_seeds(seeds):
        for query in rendered_queries(seed, model):
            worst = max(worst, *query.token_counts.values())
    budget = CONTEXT_LIMIT - worst - TEMPLATE_RESERVE
    if budget < MIN_VIABLE_BUDGET:
        raise SystemExit(
            f"{model}: worst prompt {worst:,} tokens leaves {budget:,} for "
            f"completion against a {CONTEXT_LIMIT:,} context -- below the "
            f"{MIN_VIABLE_BUDGET:,} floor."
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
    Returns
    -------
    int
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
            f"INDUCTION_MODELS={wanted!r}: named no models; leave unset to "
            "select all."
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
    """
    parser = argparse.ArgumentParser(
        description="Family-ladder scaling induction study driver."
    )
    parser.add_argument(
        "--teardown",
        action="store_true",
        help=(
            "Terminate this experiment's EC2 instance and exit. Standalone "
            "use only: under the fleet the supervisor owns lifecycle."
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
    print(
        f"INDUCTION STUDY RUN COMPLETE: {list(models)} (no teardown -- fleet-owned)",
        flush=True,
    )


if __name__ == "__main__":
    main()
