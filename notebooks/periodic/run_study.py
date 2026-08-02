"""Headless driver for the periodic (decode/cot/moe archetype) induction study.

``induction_eval.ipynb`` is the canonical definition of this experiment, but a
notebook needs a kernel and a human. This script is the same experiment as a
process, so a long live run can be supervised, logged, and restarted without
one -- the pattern ``notebooks/periodic_moe/run_pilot.py`` already established
for its sibling study.

Everything experiment-defining (template, config, model set, tags, base seed)
is copied VERBATIM from the notebook, so the replicates this produces are
byte-identical to what running the notebook would have produced and slot into
the same ``results/{tag}_{info}/rep_{seed}.yaml`` tree. That equivalence is not
taken on trust: ``scripts/verify_study_drivers.py`` regenerates prompts with
this module's config and diffs them against the prompts recorded inside the
replicate YAMLs already on disk. Run it before a live run.

WHAT IT WILL ACTUALLY DO
------------------------
Replicates resume-skip (see ``smolbench.evals.replicates``), so with
``intens``/``extens`` already present for seeds 1776..1805 this run evaluates
ONLY the outstanding ``noise_intens`` arm -- 3 models x 30 seeds x 9 questions.
That arm was cleared when noise padding moved to exact token matching; see the
notebook's intro banner.

COST
----
This provisions a LIVE EC2 spot instance (p5/p5e class, tens of dollars per
hour) and serves three large checkpoints in turn. Teardown runs only on
SUCCESS: on failure the box is deliberately left up so a supervised relaunch
reattaches and reuses its HF cache instead of re-downloading, with the
on-instance idle watchdog as the spend backstop. Check for a stray box after
any failure.

Run (repo root, main venv):
    .venv/bin/python notebooks/periodic/run_study.py
Environment:
    PERIODIC_N_REPLICATES  replicate count (default 30, the notebook's R)
"""

import logging
import os
import string
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
# Anchored via __file__, never cwd: a supervisor runs this from the repo root
# while notebook kernels run with a temp cwd, and both must hit THIS study's
# keys.env. Must land BEFORE smolbench.evals.ec2 is imported anywhere --
# ec2.py freezes its EC2_* constants from os.environ at import time.
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)

from smolbench.evals.tokenization import for_model  # noqa: E402
from smolbench.induction.experiment import InductionExperiment  # noqa: E402
from smolbench.induction.periodic import (  # noqa: E402
    PeriodicConfig,
    Prompter,
    get_periodic_numeric_quiz,
    numeric_count_query_gen,
)

# Per-archetype model names: keys of EC2_DEPLOY_SPECS in smolbench/evals/ec2.py.
# Each key is also vLLM's --served-model-name. All three are FP8 checkpoints
# from UNGATED repos. Copied verbatim from induction_eval.ipynb.
DENSE_MODEL = "llama-31-405b"      # RedHatAI/Meta-Llama-3.1-405B-Instruct-FP8-dynamic (dense)
COT_MODEL = "nemotron-ultra-253b"  # nvidia/Llama-3_1-Nemotron-Ultra-253B-v1-FP8 (dense CoT)
MOE_MODEL = "llama4-maverick"      # RedHatAI/Llama-4-Maverick-17B-128E-Instruct-FP8 (MoE)

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

BASE_SEED: int = 1776  # seed of the original preliminary run == replicate 0
INFO_TYPES: tuple[str, ...] = ("intens", "extens", "noise_intens")


def make_quizzes(seed: int, model: str) -> dict[str, tuple]:
    """Generates one replicate's three info-type quizzes, keyed by info type.

    Takes the model as well as the seed because ``noise_intens`` is a TOKEN-
    length control: it is padded with whitespace until its prompt has exactly
    as many tokens as the matching extensional prompt, measured with that
    model's own tokenizer. The other conditions are model-independent and stay
    byte-identical across models.
    """
    return dict(
        zip(
            INFO_TYPES,
            get_periodic_numeric_quiz(
                PeriodicConfig(
                    n=9,
                    labels=9,
                    seed=seed,
                ),
                Prompter(
                    template,
                    {},
                    numeric_count_query_gen,
                ),
                tokenizer=for_model(model),
            ),
        )
    )


EXPERIMENT = InductionExperiment(
    notebook_dir="periodic",
    archetype_tags={DENSE_MODEL: "decode", COT_MODEL: "cot", MOE_MODEL: "moe"},
    make_quizzes=make_quizzes,
    info_types=INFO_TYPES,
    n_replicates=int(os.environ.get("PERIODIC_N_REPLICATES", "30")),
    base_seed=BASE_SEED,
)


def main() -> None:
    """Provisions one box, runs every outstanding replicate, tears down."""
    # Warm every tokenizer BEFORE provisioning. make_quizzes resolves a
    # model's tokenizer from the HF hub, and doing that for the first time
    # inside the run loop would put a network download -- and its failure
    # modes -- between an already-billing GPU box and the first request.
    for model in (DENSE_MODEL, COT_MODEL, MOE_MODEL):
        logging.info(f"warming tokenizer for {model}: {for_model(model).name}")

    EXPERIMENT.provision()
    # Smallest checkpoint first (Nemotron-Ultra ~253GB, then the two ~410GB
    # models), so a serving problem surfaces before the biggest pull rather
    # than after it. Order does not affect the data: replicates are keyed by
    # (tag, info, seed) and each model's are independent.
    #
    # extra_args mirror the notebook exactly -- only the CoT model gets a
    # completion budget (cells 9/12/16 of induction_eval.ipynb). Nemotron-
    # Ultra's chain-of-thought comes from the "detailed thinking on" system
    # prompt its EC2_DEPLOY_SPECS entry injects, so user prompts stay
    # byte-identical across archetypes.
    for model, extra_args in (
        (COT_MODEL, {"max_completion_tokens": 8192}),
        (MOE_MODEL, None),
        (DENSE_MODEL, None),
    ):
        EXPERIMENT.run(model, **({"extra_args": extra_args} if extra_args else {}))
        EXPERIMENT.summarize(model)
    EXPERIMENT.teardown()
    print("PERIODIC STUDY COMPLETE: box torn down", flush=True)


if __name__ == "__main__":
    main()
