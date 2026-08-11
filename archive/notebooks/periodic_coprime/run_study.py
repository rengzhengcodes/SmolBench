"""Headless driver for the COPRIME-period induction study.

Same three MoE checkpoints as ``notebooks/periodic_moe``, same prompt
template, same four information conditions -- one thing changes: the
harmonic periods are an explicit pairwise-coprime set instead of the
consecutive integers 1..n.

WHY THIS STUDY EXISTS
---------------------
``periodic_moe`` saturated. Intensional and noise-padded-intensional both
sit at ceiling for all three models at EVERY harmonic (Nemotron-3 is 30/30
on all nine in both arms), so there is no harmonic at which the two arms
separate -- paired McNemar over the collected R=30 gives p=0.549 for
gpt-oss and p=1.000 for the other two.

The obvious fix -- more harmonics -- does not work, because on the default
pathway sequence length is lcm(1..n), which is a step function:

    lcm(1..9)  =  2,520     extensional listing ~26k tokens
    lcm(1..10) =  2,520     IDENTICAL; n=10 lengthens nothing
    lcm(1..11) = 27,720     x11; ~341k tokens, vs a 131,072 context window

There is no n in between. So this study dials the length directly instead,
via ``PeriodicConfig(periods=...)``: a pairwise-coprime set has
lcm == prod, so the sequence length is chosen rather than inherited.

CHOICE OF PERIOD SET
--------------------
``(1, 3, 4, 5, 7, 11)`` -> 4,620 positions, a ~1.6x longer extensional
listing than the 1..9 baseline. It is the largest candidate measured that
still clears a full 65,536-token completion budget under ALL THREE served
tokenizers, which is the binding constraint and not an obvious one:

    periods                seq_len   gpt-oss  nemotron-3   qwen3.5   headroom
    (1, 3, 4, 5, 7, 11)      4,620    41,763      52,440    55,526    +10,010
    (1, 2, 3, 5, 7, 23)      4,830    45,659      57,631    60,052     +5,484
    (1, 2, 3, 5, 11, 17)     5,610    52,767      66,689    69,500     -3,964
    (1, 2, 3, 7, 11, 13)     6,006    55,743      70,655    73,664     -8,128

gpt-oss tokenizes this text ~32% more compactly than Qwen3.5, so a period
set sized against gpt-oss alone overruns the other two silently. Re-measure
(``scripts/`` has no helper for this; see the study notes) before changing
the set.

Note the density trade-off coprimality forces: it forbids keeping both 2
and 4, so this set fires ~2.02 labels per position against the baseline's
~2.83. The listing is longer AND sparser, which is a change in kind, not
only in degree -- do not read a length-only story into any gap it produces.

COMPLETION BUDGET
-----------------
DERIVED at startup by ``completion_budget``, not hardcoded -- hardcoding it
failed twice here in one day, once too small and once too large:

  65,536  truncated Qwen mid-``<think>``: empty response AND empty
          reasoning, because the reasoning parser never saw a closing tag.
  74,000  overshot by exactly ONE token. The prompt I had measured at
          55,526 arrived at vLLM as 57,073 input tokens -- ``count()``
          excludes the server-side chat template -- and 57,073 + 74,000 =
          131,073 against a 131,072 limit. vLLM 400s that, which kills the
          whole run rather than the single request.

gpt-oss and Nemotron-3 are capped at 65,536 where they have produced zero
empties, so their collected replicates stay comparable. Qwen takes whatever
the context allows, since it is the only model that has ever truncated.
Per-model budgets are the established practice in this family (periodic_moe
gave Qwen 65,536 against 8,192 for the others): a uniform budget truncates
whichever model reasons longest, which is a worse confound than an explicit
ceiling because it penalises exactly the model working hardest.

WHAT IT WILL ACTUALLY DO
------------------------
Writes to ``notebooks/periodic_coprime/results/`` under its own experiment
tag and EC2 state file, so it shares nothing with ``periodic_moe``. That
separation is mandatory, not tidiness: replicates resume-skip on
``rep_{seed}.yaml`` existence, so pointing this at periodic_moe's results
tree would skip all 30 seeds and collect nothing, and reusing its seeds
would mix two incomparable quiz generators into one directory.

Defaults to ONE replicate (seed 1776) -- a pilot. Set
COPRIME_N_REPLICATES=30 for the full run; replicates resume-skip, so the
full run extends the pilot rather than repeating it.

COST
----
Provisions a LIVE EC2 spot instance (p5e/p5 class, tens of dollars per
hour) and serves three large checkpoints in turn (~700 GB total). Teardown
runs only on SUCCESS: on failure the box is deliberately left up so a
supervised relaunch reattaches and reuses its HF cache, with the on-instance
idle watchdog as the spend backstop. Check for a stray box after any
failure.

Run (repo root, main venv):
    .venv/bin/python notebooks/periodic_coprime/run_study.py
Environment:
    COPRIME_N_REPLICATES   replicate count (default 1 = pilot)
    COPRIME_MODELS         comma-separated tags to run (default all three),
                           so a stranded run can resume one model at a time
    COPRIME_SHARD          'index/count' -- run only every count-th replicate,
                           starting at index, so N instances can collect one
                           model's replicates in parallel. Derives its own AWS
                           tag and state file, so shards cannot collide; launch
                           one process per shard, each with the same MODELS.
"""

import logging
import os
import string
from math import prod
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
# Anchored via __file__, never cwd -- and it MUST land before
# smolbench.evals.ec2 is imported anywhere, because ec2.py freezes its EC2_*
# constants from os.environ at import time. This study's keys.env carries a
# DISTINCT EC2_EXPERIMENT_TAG so its spot instance and resource tags can
# never collide with periodic_moe's.
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)

def _parse_shard(var: str) -> "tuple[int, int] | None":
    """Parses a ``index/count`` shard selector from the environment.

    Sharding splits ONE model's replicates across N instances, which is the
    last serialisation left in a study: splitting by model already runs the
    three checkpoints at once, but a single model's 30 replicates still run
    one after another, so wall-clock is set by the slowest model alone.
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


SHARD = _parse_shard("COPRIME_SHARD")

# A shard needs its OWN AWS tag and state file. Without that, shard 1
# reattaches to shard 0's live box and swaps the served model out from under a
# run in progress -- the exact collision hit when first parallelising by model.
# Deriving both from the lane, rather than asking the caller to remember two
# more environment variables, removes that footgun.
#
# This MUST execute before smolbench.evals.ec2 is imported below: ec2.py
# freezes its EC2_* constants from os.environ at import time, so a tag set
# afterwards is silently ignored. Unsharded runs get an empty suffix, leaving
# the tag and state file byte-identical to before this flag existed.
_LANE = ""
if SHARD is not None:
    _models = os.environ.get("COPRIME_MODELS", "").strip().replace(",", "-")
    _LANE = (f"-{_models}" if _models else "") + "-s{}of{}".format(*SHARD)
    os.environ["EC2_EXPERIMENT_TAG"] = (
        os.environ.get("EC2_EXPERIMENT_TAG", "periodic-coprime-induction") + _LANE
    )
_DEFAULT_STATE_FILE = f".ec2_state_periodic_coprime{_LANE}.json"

from smolbench.evals.tokenization import for_model  # noqa: E402
from smolbench.induction.experiment import InductionExperiment  # noqa: E402
from smolbench.induction.periodic import (  # noqa: E402
    PeriodicConfig,
    Prompter,
    get_periodic_numeric_quiz,
    get_periodic_zero_info_numeric_quiz,
    numeric_count_query_gen,
)

MODEL_QWEN = "qwen3.5-397b-a17b"
MODEL_NEMOTRON = "nemotron-3-super-120b-a12b"
MODEL_GPTOSS = "gpt-oss-120b"

#: Pairwise-coprime harmonic periods -> seq_len == prod == 4,620. See the
#: module docstring's table for why this set and not a longer one.
PERIODS: tuple[int, ...] = (1, 3, 4, 5, 7, 11)

#: The served checkpoints' context window (EC2_DEPLOY_SPECS max_model_len).
CONTEXT_LIMIT: int = 131_072

#: Tokens withheld from the completion budget, covering the two things a
#: count() on one seed's prompt cannot see. Both were measured, not guessed:
#:
#:  ~1,547  chat template. ``Tokenizer.count`` deliberately excludes
#:          special/BOS tokens (see the Tokenizer protocol docstring), so the
#:          server always receives more than count() reports. A prompt
#:          counting 55,526 arrived at vLLM as 57,073 input tokens.
#:  ~3,695  cross-seed variation. Sweeping all 30 seeds, the coprime study's
#:          worst extens prompt is 59,221 (seed 1793) against 55,526 for seed
#:          1776 -- the labels are random per seed and tokenize differently,
#:          which compounds over thousands of listing lines. Sizing from one
#:          seed understates the worst case by thousands of tokens.
#:
#: 8,000 covers both with margin, so the derived budget stays safe even when
#: the seed probe misses the single longest seed. It costs only completion
#: headroom that is otherwise unused.
TEMPLATE_RESERVE: int = 8_000

#: Seeds sampled when measuring the worst-case prompt. See completion_budget.
PROBE_SEEDS: int = 6

#: Floor below which a run is not worth starting: Qwen truncated mid-<think>
#: at 65,536, so anything much smaller guarantees empties rather than data.
MIN_VIABLE_BUDGET: int = 48_000

#: Ceilings, applied AFTER the derived budget below. gpt-oss and Nemotron-3
#: produced zero empties at 65,536, so they stay there and their collected
#: replicates remain comparable; Qwen is uncapped and takes whatever the
#: context allows, because it is the only model that has ever truncated.
BUDGET_CAP: dict[str, int] = {
    MODEL_GPTOSS: 65_536,
    MODEL_NEMOTRON: 65_536,
    MODEL_QWEN: CONTEXT_LIMIT,
}


def completion_budget(model: str, seeds: range) -> int:
    """Largest completion budget that cannot overflow this model's context.

    Derived, not hardcoded, because hardcoding it went wrong twice in one day:
    65,536 truncated Qwen mid-``<think>`` (empty response AND empty
    reasoning), and a hand-computed 74,000 overshot by exactly ONE token --
    57,073 input + 74,000 output = 131,073 against a 131,072 limit -- which
    vLLM rejects with a 400 that kills the whole run, not just that request.

    Both mistakes came from me doing this arithmetic against a prompt length I
    measured with ``count()``, which excludes the server-side template. So the
    arithmetic moves here, over the ACTUAL worst-case prompt across every seed
    this study will send, with TEMPLATE_RESERVE covering what count() cannot
    see. Probing runs before provisioning, so its cost is wall-clock on a
    machine that is not yet billing.
    """
    tok = for_model(model)
    # Subsample the seeds. Prompt length varies across seeds only through the
    # random labels (a couple of hundred tokens at most); the structure that
    # sets the length -- period set, sequence length, arm -- is identical for
    # every seed. Probing all 30 costs minutes per model because the noise arm
    # re-runs its token-matching search each time, and TEMPLATE_RESERVE already
    # covers far more than the residual variation. Endpoints are always
    # included so the range is bracketed rather than sampled from the middle.
    picks = sorted({seeds[0], seeds[-1],
                    *(seeds[i * (len(seeds) - 1) // (PROBE_SEEDS - 1)]
                      for i in range(PROBE_SEEDS))}) if len(seeds) > 1 else list(seeds)
    worst = 0
    for seed in picks:
        for quiz in make_quizzes(seed, model).values():
            worst = max(worst, max(tok.count(q.prompt) for q in quiz))
    budget = min(CONTEXT_LIMIT - worst - TEMPLATE_RESERVE, BUDGET_CAP[model])
    if budget < MIN_VIABLE_BUDGET:
        raise SystemExit(
            f"{model}: worst prompt is {worst:,} tokens, leaving only {budget:,} for "
            f"completion against a {CONTEXT_LIMIT:,} context. That is below the "
            f"{MIN_VIABLE_BUDGET:,} floor and would collect empties, not data. "
            "Shorten the period set."
        )
    logging.info(
        f"{model}: worst prompt {worst:,} tok (+{TEMPLATE_RESERVE:,} reserve) "
        f"-> completion budget {budget:,}"
    )
    return budget

# Byte-identical to periodic_moe's template, so the only difference between
# the two studies is the period set.
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

BASE_SEED: int = 1776
INFO_TYPES: tuple[str, ...] = ("intens", "extens", "noise_intens", "zero")


def make_quizzes(seed: int, model: str) -> dict[str, tuple]:
    """Generates one replicate's four info-type quizzes, keyed by info type.

    Takes the model because ``noise_intens`` is a TOKEN-length control: it is
    padded with whitespace until its prompt has exactly as many tokens as the
    matching extensional prompt, measured with that model's own tokenizer.
    The other three conditions are model-independent and stay byte-identical
    across the trio, so cross-model comparisons remain paired.
    """
    cfg = PeriodicConfig(n=len(PERIODS), labels=len(PERIODS), seed=seed, periods=PERIODS)
    prompter = Prompter(template, {}, numeric_count_query_gen)
    intens, extens, noise_intens = get_periodic_numeric_quiz(
        cfg, prompter, tokenizer=for_model(model)
    )
    zero = get_periodic_zero_info_numeric_quiz(cfg, prompter)
    return {"intens": intens, "extens": extens, "noise_intens": noise_intens, "zero": zero}


EXPERIMENT = InductionExperiment(
    notebook_dir="periodic_coprime",
    archetype_tags={MODEL_QWEN: "qwen35", MODEL_NEMOTRON: "nemotron3", MODEL_GPTOSS: "gptoss"},
    make_quizzes=make_quizzes,
    info_types=INFO_TYPES,
    n_replicates=int(os.environ.get("COPRIME_N_REPLICATES", "1")),
    base_seed=BASE_SEED,
    # Env-overridable so ONE MODEL PER BOX is possible. InductionExperiment
    # writes this into EC2_STATE_FILE (experiment.py), which clobbers any
    # shell-set value -- so parallelising by model has to go through here,
    # not through the environment. Pair it with a distinct
    # EC2_EXPERIMENT_TAG (that one DOES honour the shell, since load_dotenv
    # does not override) or the second run reattaches to the first run's
    # box and swaps the served model out from under it.
    state_file=os.environ.get("COPRIME_STATE_FILE", _DEFAULT_STATE_FILE),
    shard=SHARD,
)

#: Archetype tag -> model, for the COPRIME_MODELS selector.
_BY_TAG = {"gptoss": MODEL_GPTOSS, "nemotron3": MODEL_NEMOTRON, "qwen35": MODEL_QWEN}


def selected_models() -> tuple:
    """Returns the models this invocation should run, smallest checkpoint first.

    Smallest-first (gpt-oss ~60 GB -> Nemotron ~240 GB -> Qwen ~794 GB) so a
    serving problem surfaces before the biggest pull rather than after it.
    Order does not affect the data: replicates are keyed by (tag, info, seed)
    and each model's are independent.
    """
    order = (MODEL_GPTOSS, MODEL_NEMOTRON, MODEL_QWEN)
    wanted = os.environ.get("COPRIME_MODELS", "").strip()
    if not wanted:
        return order
    tags = [t.strip() for t in wanted.split(",") if t.strip()]
    unknown = [t for t in tags if t not in _BY_TAG]
    if unknown:
        raise SystemExit(f"COPRIME_MODELS: unknown tag(s) {unknown}; pick from {sorted(_BY_TAG)}")
    chosen = {_BY_TAG[t] for t in tags}
    return tuple(m for m in order if m in chosen)


def main() -> None:
    """Provisions one box, runs every outstanding replicate, tears down."""
    models = selected_models()
    logging.info(f"periods={PERIODS} -> seq_len={prod(PERIODS)}")
    logging.info(f"running models: {list(models)}")

    # Warm every tokenizer AND derive every completion budget BEFORE
    # provisioning. make_quizzes resolves a model's tokenizer from the HF hub,
    # and doing that for the first time inside the run loop would put a network
    # download -- and its failure modes -- between an already-billing GPU box
    # and the first request. Deriving budgets here has the same shape of
    # benefit: a period set that cannot fit its own context now fails on a
    # laptop rather than after a p5 has spent 40 minutes loading weights.
    seeds = range(BASE_SEED, BASE_SEED + EXPERIMENT.n_replicates)
    budgets = {}
    for model in models:
        logging.info(f"warming tokenizer for {model}: {for_model(model).name}")
        budgets[model] = completion_budget(model, seeds)

    EXPERIMENT.provision()
    for model in models:
        EXPERIMENT.run(model, extra_args={"max_completion_tokens": budgets[model]})
        EXPERIMENT.summarize(model)
    EXPERIMENT.teardown()
    print("COPRIME STUDY COMPLETE: box torn down", flush=True)


if __name__ == "__main__":
    main()
