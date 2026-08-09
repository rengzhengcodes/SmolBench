"""Headless driver for the DIVISOR-period induction study.

The dual of ``notebooks/periodic_coprime``. That study lengthens the
EXTENSIONAL listing and holds the rule list still; this one lengthens the
INTENSIONAL rule list and holds the listing still.

HOW IT WORKS
------------
A harmonic whose period DIVIDES the existing sequence length adds a rule and
a question without moving lcm at all. Every period here divides 2,520, so
the sequence stays exactly 2,520 positions -- the same listing the
``periodic_moe`` baseline used -- while the intensional prompt roughly
doubles.

It is nearly free on the extensional side because a period d contributes
only seq_len/d occurrences to the listing. The 17 largest proper divisors
of 2,520 add 179 occurrences to a listing that already carries 7,129.
Measured with nested labels (so the comparison isn't confounded by
different random label strings tokenizing differently):

    harmonics  questions   intens      extens
            9          9    1.00x      1.000x   <- periodic_moe baseline
           18         18    1.45x      1.004x
           26         26    1.83x      1.014x   <- THIS STUDY
           34         34    2.19x      1.049x

26 harmonics doubles the rule list for ~1.5% on the listing. Going further
stops being "held fixed": at 34 the listing has grown 5%, and taking all 48
divisors of 2,520 grows it 31%, because the small divisors fire constantly.

WHY THIS IS THE INTERESTING CONTRAST
------------------------------------
``periodic_moe`` saturated with intens and noise_intens both at ceiling for
all three models at every harmonic. Coprime mode attacks that by making the
evidence longer. This attacks it from the other side: more RULES to hold
simultaneously, against an unchanged body of evidence. If intensional
accuracy falls here while the extensional arm stays put, the limit is rule
tracking rather than context length -- a claim the noise arm alone cannot
separate, since noise adds length without adding rules.

A bonus that matters for cost: 26 questions per replicate against the
baseline's 9, so each replicate carries ~2.9x the data at nearly the same
prompt cost.

Read the added harmonics carefully when interpreting: a large-period
harmonic is EASY intensionally (2520/2520 = 1 is trivial division) but HARD
extensionally (find the single position out of 2,520 that carries it). The
same harmonic therefore sits at opposite ends of the difficulty range in
the two arms, which is a feature -- it is where the two representations
should come apart -- but it is not a uniform difficulty increase.

WHAT IT WILL ACTUALLY DO
------------------------
Writes to ``notebooks/periodic_divisor/results/`` under its own experiment
tag and EC2 state file, sharing nothing with periodic_moe or
periodic_coprime. That separation is mandatory: replicates resume-skip on
``rep_{seed}.yaml`` existence, so writing into a sibling study's tree would
skip its seeds and collect nothing.

Defaults to ONE replicate (seed 1776) -- a pilot, gated the same way its
sibling is (see scripts/coprime_pilot_gate.py). Set
DIVISOR_N_REPLICATES=30 for the full run.

COST
----
Provisions a LIVE EC2 spot instance (p5/p5e class, tens of dollars per hour)
and serves three checkpoints in turn. Teardown runs only on SUCCESS; on
failure the box is left up so a relaunch reuses its HF cache, with the
on-instance idle watchdog as the spend backstop.

Run (repo root, main venv):
    .venv/bin/python notebooks/periodic_divisor/run_study.py
Environment:
    DIVISOR_N_REPLICATES   replicate count (default 1 = pilot)
    DIVISOR_MODELS         comma-separated tags (default all three)
"""

import logging
import os
import string
from math import lcm
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
# Anchored via __file__, never cwd, and MUST land before smolbench.evals.ec2 is
# imported anywhere -- ec2.py freezes its EC2_* constants at import time. This
# study's keys.env carries a DISTINCT EC2_EXPERIMENT_TAG so its spot instance
# and resource tags can never collide with the two sibling studies, which may
# be running at the same time.
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)

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

#: The sequence length this study pins. Identical to the periodic_moe
#: baseline's lcm(1..9), which is what makes the extensional listings
#: comparable across the two studies.
SEQ_LEN: int = 2520

#: The nine baseline harmonics, plus the 17 largest proper divisors of 2,520.
#: Every one divides SEQ_LEN, so lcm is unmoved; the large ones are chosen
#: because a period d costs only SEQ_LEN/d occurrences in the listing.
PERIODS: tuple[int, ...] = tuple(sorted(
    tuple(range(1, 10))
    + (105, 120, 126, 140, 168, 180, 210, 252, 280, 315, 360, 420, 504, 630, 840, 1260, 2520)
))

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

# Byte-identical to periodic_moe's and periodic_coprime's template, so the
# period set is the only thing that differs across the three studies.
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

    ``expect_seq_len`` is what makes this the divisor pathway: it waives the
    pairwise-coprimality requirement (these periods share factors on purpose)
    and asserts instead that lcm(PERIODS) is exactly SEQ_LEN. If a period
    that did not divide 2,520 ever crept into the set, the extensional
    listing would silently resize -- the one thing this study exists to hold
    fixed -- and every answer would still look self-consistent.

    Takes the model because ``noise_intens`` is a TOKEN-length control,
    padded with whitespace to its extensional counterpart's token count under
    that model's own tokenizer.
    """
    cfg = PeriodicConfig(
        n=len(PERIODS),
        labels=len(PERIODS),
        seed=seed,
        periods=PERIODS,
        expect_seq_len=SEQ_LEN,
    )
    prompter = Prompter(template, {}, numeric_count_query_gen)
    intens, extens, noise_intens = get_periodic_numeric_quiz(
        cfg, prompter, tokenizer=for_model(model)
    )
    zero = get_periodic_zero_info_numeric_quiz(cfg, prompter)
    return {"intens": intens, "extens": extens, "noise_intens": noise_intens, "zero": zero}


EXPERIMENT = InductionExperiment(
    notebook_dir="periodic_divisor",
    archetype_tags={MODEL_QWEN: "qwen35", MODEL_NEMOTRON: "nemotron3", MODEL_GPTOSS: "gptoss"},
    make_quizzes=make_quizzes,
    info_types=INFO_TYPES,
    n_replicates=int(os.environ.get("DIVISOR_N_REPLICATES", "1")),
    base_seed=BASE_SEED,
    # Env-overridable so ONE MODEL PER BOX is possible. InductionExperiment
    # writes this into EC2_STATE_FILE (experiment.py), which clobbers any
    # shell-set value -- so parallelising by model has to go through here,
    # not through the environment. Pair it with a distinct
    # EC2_EXPERIMENT_TAG (that one DOES honour the shell, since load_dotenv
    # does not override) or the second run reattaches to the first run's
    # box and swaps the served model out from under it.
    state_file=os.environ.get("DIVISOR_STATE_FILE", ".ec2_state_periodic_divisor.json"),
)

_BY_TAG = {"gptoss": MODEL_GPTOSS, "nemotron3": MODEL_NEMOTRON, "qwen35": MODEL_QWEN}


def selected_models() -> tuple:
    """Returns the models to run, smallest checkpoint first so a serving
    problem surfaces before the biggest pull rather than after it."""
    order = (MODEL_GPTOSS, MODEL_NEMOTRON, MODEL_QWEN)
    wanted = os.environ.get("DIVISOR_MODELS", "").strip()
    if not wanted:
        return order
    tags = [t.strip() for t in wanted.split(",") if t.strip()]
    unknown = [t for t in tags if t not in _BY_TAG]
    if unknown:
        raise SystemExit(f"DIVISOR_MODELS: unknown tag(s) {unknown}; pick from {sorted(_BY_TAG)}")
    chosen = {_BY_TAG[t] for t in tags}
    return tuple(m for m in order if m in chosen)


def main() -> None:
    """Provisions one box, runs every outstanding replicate, tears down."""
    models = selected_models()
    # Fail loudly here rather than after provisioning if the period set ever
    # stops pinning the length -- this is the study's defining invariant.
    assert lcm(*PERIODS) == SEQ_LEN, f"periods no longer pin seq_len {SEQ_LEN}"
    logging.info(f"{len(PERIODS)} harmonics, seq_len={SEQ_LEN} (unmoved), "
                 f"{len(PERIODS)} questions/replicate")
    logging.info(f"running models: {list(models)}")

    # Warm tokenizers BEFORE provisioning: an HF download failure must never
    # land between a billing GPU box and the first request.
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
    print("DIVISOR STUDY COMPLETE: box torn down", flush=True)


if __name__ == "__main__":
    main()
