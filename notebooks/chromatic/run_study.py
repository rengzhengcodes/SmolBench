"""Headless driver for the chromatic (succession) induction study.

``induction_eval.ipynb`` is the canonical definition of this experiment, but a
notebook needs a kernel and a human. This script is the same experiment as a
process, so a long live run can be supervised, logged, and restarted without
one -- the pattern ``notebooks/periodic_moe/run_pilot.py`` already established
for its sibling study.

Everything experiment-defining (both templates, config, model set, tags, base
seed, and the CoT tuning constants) is copied VERBATIM from the notebook, so
the replicates this produces are byte-identical to what running the notebook
would have produced and slot into the same
``results/{tag}_{info}/rep_{seed}.yaml`` tree. That equivalence is not taken on
trust: ``scripts/verify_study_drivers.py`` regenerates prompts with this
module's config and diffs them against the prompts recorded inside the
replicate YAMLs already on disk. Run it before a live run.

This driver covers the SUCCESSION experiment only (``induction_eval.ipynb``).
The one-hop sibling (``induction_eval_one_hop.ipynb``, ``prefix="one_hop_"``)
shares this results tree but has never been run -- there are no
``one_hop_*`` directories on disk -- so it is deliberately not started here.

WHAT IT WILL ACTUALLY DO
------------------------
Replicates resume-skip (see ``smolbench.evals.replicates``), so with
``intens``/``extens`` already present for seeds 1776..1805 this run evaluates
ONLY the outstanding ``noise_intens`` arm -- 3 models x 30 seeds x ~119
questions, which makes this much the largest of the three studies by request
count. That arm was cleared when noise padding moved to exact token matching;
see the notebook's intro banner.

COST
----
This provisions a LIVE EC2 spot instance (p5e/p5, tens of dollars per hour)
and serves three ~32B checkpoints in turn. Teardown runs only on SUCCESS: on
failure the box is deliberately left up so a supervised relaunch reattaches
and reuses its HF cache, with the on-instance idle watchdog as the spend
backstop. Check for a stray box after any failure.

Run (repo root, main venv):
    .venv/bin/python notebooks/chromatic/run_study.py
Environment:
    CHROMATIC_N_REPLICATES  replicate count (default 30, the notebook's R)
"""

import logging
import os
import string
from pathlib import Path
from typing import Dict, Tuple

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
# Anchored via __file__, never cwd (the notebook uses "./keys.env", which only
# works from its own directory). Must land BEFORE smolbench.evals.ec2 is
# imported anywhere -- ec2.py freezes its EC2_* constants at import time.
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)

from smolbench.evals.tokenization import for_model  # noqa: E402
from smolbench.induction.chromatic import (  # noqa: E402
    ChromaticIntervalsConfig,
    Prompter,
    get_random_exclusive_quiz,
    succession_query_gen,
)
from smolbench.induction.experiment import InductionExperiment  # noqa: E402

# Per-archetype model names: keys of EC2_DEPLOY_SPECS in smolbench/evals/ec2.py
# (each key is also vLLM's --served-model-name). An ungated ~32B English-centric
# trio. Copied verbatim from induction_eval.ipynb.
DENSE_MODEL = "olmo-3.1-32b-instruct"  # allenai/Olmo-3.1-32B-Instruct (32B dense, non-reasoning)
COT_MODEL = "olmo-3.1-32b-think"       # allenai/Olmo-3.1-32B-Think (32B dense, always reasons)
MOE_MODEL = "granite-4.0-h-small"      # ibm-granite/granite-4.0-h-small (MoE 32B/~9B active)

# CoT tuning, verbatim from the notebook: Olmo-3.1-32B-Think reasons
# unconditionally, so it needs budget to finish thinking AND answer, and the
# longest chain must finish on attempt 1 -- a tight timeout censors long-CoT
# requests, which top-truncates the measured chain-length distribution and
# makes the scored output non-deterministic.
COT_EXTRA_ARGS = {"max_completion_tokens": 16384}
COT_MAX_PARALLEL = 48
COT_REQUEST_TIMEOUT = 1200

template = string.Template(
    "You are a Boolean classifier.\n"
    "\n"
    "Task: determine whether the statement in the Question is logically "
    "possible given the Context.\n"
    "\n"
    "Output format:\n"
    "Return exactly one of these two strings and nothing else:\n"
    "True\n"
    "False\n"
    "\n"
    "Do not output any explanation, punctuation, quotes, labels, code fences, "
    "or extra whitespace."
    "Stop immediately after writing True or False."
    "\n"
    "Context:\n"
    "There is a ceremonial role called the $role, whose job it is to"
    " head the $parade parade. No one else besides the $role is able to head"
    " the $parade parade. At the end of one's term as $role, they have a ceremony where they hand off the"
    " $role ceremonial sceptre to their successor. The following lists the people who were $role and"
    " the years they were $role:\n"
    "$positive_info\n"
    "\n"
    "Question:\n"
    "Has $color1 handed the sceptre to $color2?"
)

extens_template = string.Template(
    "You are a Boolean classifier.\n"
    "\n"
    "Task: determine whether the statement in the Question is logically "
    "possible given the Context.\n"
    "\n"
    "Output format:\n"
    "Return exactly one of these two strings and nothing else:\n"
    "True\n"
    "False\n"
    "\n"
    "Do not output any explanation, punctuation, quotes, labels, code fences, "
    "or extra whitespace."
    "Stop immediately after writing True or False."
    "\n"
    "Context:\n"
    "There is a ceremonial role called the $role, whose job it is to"
    " head the $parade parade. No one else besides the $role is able to head"
    " the $parade parade. At the end of one's term as $role, they have a ceremony where they hand off the"
    " $role ceremonial sceptre to their successor. The following lists each year and who was $role"
    " that year:\n"
    "$positive_info\n"
    "\n"
    "Question:\n"
    "Has $color1 handed the sceptre to $color2?"
)

QUERY_GEN = succession_query_gen

BASE_SEED: int = 1776  # seed of the original preliminary run == replicate 0
INFO_TYPES: Tuple[str, ...] = ("intens", "extens", "noise_intens")


def make_quizzes(seed: int, model: str) -> Dict[str, tuple]:
    """Generates one replicate's three info-type quizzes, keyed by info type.

    Chromatic quizzes are large -- every prompt embeds the full interval
    history (the extens listing alone is ~3000 lines) across ~120 questions
    -- so replicates are generated on demand per seed inside EXPERIMENT.run,
    not all precomputed up front, to keep memory bounded.

    Takes the model as well as the seed because ``noise_intens`` is a TOKEN-
    length control: it is padded with whitespace until its prompt has exactly
    as many tokens as the matching extensional prompt, measured with that
    model's own tokenizer. The other conditions are model-independent and stay
    byte-identical across models.
    """
    return dict(
        zip(
            INFO_TYPES,
            get_random_exclusive_quiz(
                ChromaticIntervalsConfig(
                    n=int(12 * 250),
                    intervals=250 // 4,
                    colors=45,
                    seed=seed,
                ),
                Prompter(
                    template,
                    {
                        "role": "Twislax",
                        "parade": "Gildane",
                    },
                    QUERY_GEN,
                    extens_template,
                ),
                tokenizer=for_model(model),
            ),
        )
    )


EXPERIMENT = InductionExperiment(
    notebook_dir="chromatic",
    archetype_tags={DENSE_MODEL: "decode", COT_MODEL: "cot", MOE_MODEL: "moe"},
    make_quizzes=make_quizzes,
    info_types=INFO_TYPES,
    n_replicates=int(os.environ.get("CHROMATIC_N_REPLICATES", "30")),
    base_seed=BASE_SEED,
    state_file=".ec2_state_chromatic.json",
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
    # Non-reasoning models first: the CoT model is the long pole (a 16k
    # completion budget over ~119 questions x 30 seeds), so anything that
    # would fail for all three fails cheaply before it starts. Order does not
    # affect the data -- replicates are keyed by (tag, info, seed).
    EXPERIMENT.run(DENSE_MODEL)
    EXPERIMENT.summarize(DENSE_MODEL)

    EXPERIMENT.run(MOE_MODEL)
    EXPERIMENT.summarize(MOE_MODEL)

    EXPERIMENT.run(
        COT_MODEL,
        extra_args=COT_EXTRA_ARGS,
        max_parallel=COT_MAX_PARALLEL,
        request_timeout=COT_REQUEST_TIMEOUT,
    )
    EXPERIMENT.summarize(COT_MODEL)
    EXPERIMENT.cot_chain_lengths()  # top-truncation guardrail; see the notebook

    EXPERIMENT.teardown()
    print("CHROMATIC STUDY COMPLETE: box torn down", flush=True)


if __name__ == "__main__":
    main()
