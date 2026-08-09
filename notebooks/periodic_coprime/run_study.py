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
All three models get 65,536 tokens, not just Qwen. Every one of the 21
invalids in ``periodic_moe`` was ``compliance=empty`` with a zero-length
response -- truncation, at gpt-oss's and Nemotron's 8,192 budget against a
~26k-token prompt. Prompts here are ~2x longer again, so the budget rises
for everyone. Whether 65,536 is actually enough is an empirical question
this study's PILOT answers; check the invalid count before scaling R.

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

#: Completion budget, PER MODEL. See COMPLETION BUDGET above.
#:
#: Qwen3.5 gets more than the others because it needs more: at 65,536 it
#: truncated one extens mark in the pilot (period 11), returning an empty
#: response AND empty reasoning -- its <think> block never closed, so the
#: reasoning parser had nothing to hand back. gpt-oss and Nemotron-3 produced
#: zero empties at 65,536 in the same pilot, so they keep it and their
#: already-collected replicates stay comparable.
#:
#: Qwen's 74,000 is essentially the ceiling this context allows: its worst
#: prompt here is 55,526 tokens against a 131,072 window, leaving 75,546. If a
#: request still truncates at 74,000 then no budget fits it on this
#: checkpoint, and that is a finding about the model rather than a
#: misconfiguration.
#:
#: Per-model budgets are the established practice in this benchmark family
#: (periodic_moe gave Qwen 65,536 against 8,192 for the others) precisely
#: because a uniform budget truncates some models and not others -- a worse
#: confound than an explicit per-model ceiling.
MAX_COMPLETION_TOKENS: dict[str, int] = {
    MODEL_GPTOSS: 65_536,
    MODEL_NEMOTRON: 65_536,
    MODEL_QWEN: 74_000,
}

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
    state_file=".ec2_state_periodic_coprime.json",
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

    # Warm every tokenizer BEFORE provisioning. make_quizzes resolves a model's
    # tokenizer from the HF hub, and doing that for the first time inside the
    # run loop would put a network download -- and its failure modes -- between
    # an already-billing GPU box and the first request.
    for model in models:
        logging.info(f"warming tokenizer for {model}: {for_model(model).name}")

    EXPERIMENT.provision()
    for model in models:
        EXPERIMENT.run(model, extra_args={"max_completion_tokens": MAX_COMPLETION_TOKENS[model]})
        EXPERIMENT.summarize(model)
    EXPERIMENT.teardown()
    print("COPRIME STUDY COMPLETE: box torn down", flush=True)


if __name__ == "__main__":
    main()
