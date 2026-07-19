"""Headless PILOT driver for the all-MoE induction study.

Runs exactly ONE replicate -- seed 1776, the pilot ``power_analysis.py``
sizes R from -- of each info type against each of the three MoE models,
then tears the box down. Everything experiment-defining (template, quiz
factory, model set, tags, state-file namespace) is copied VERBATIM from
``induction_eval.ipynb`` so the pilot artifact
(``results/{tag}_{info}/rep_1776.yaml``) is byte-identical to what running
the notebook would have produced, and the notebook's later full replicate
run resume-skips it.

Differences from the notebook, both deliberate:

- ``n_replicates=1``: the harness runs "every outstanding replicate", so a
  pilot-only pass is expressed as a 1-replicate experiment (seeds ==
  (base_seed,) == (1776,)). The notebook's placeholder R=30 stays untouched
  there; the real R comes from ``power_analysis.py`` over this pilot.
- Model order is smallest-first (gpt-oss ~60GB -> Nemotron ~240GB -> Qwen
  ~794GB): the vLLM image's support for the 2026 architectures is only
  proven live, so fail fast before the 794GB pull, not after.

Teardown runs only on SUCCESS. On failure the box is left up so a
supervised relaunch reattaches and reuses its HF cache instead of
re-downloading; the on-box idle watchdog is the spend backstop if nothing
relaunches.

Run (repo root, main venv):
    .venv/bin/python notebooks/periodic_moe/run_pilot.py
"""

import logging
import os
import string
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
# Anchored via __file__, never cwd: the supervisor runs this from the repo
# root, notebook kernels run with a temp cwd, and both must hit THIS
# study's keys.env (distinct experiment tag + p5e pin + vLLM image).
load_dotenv(Path(__file__).resolve().parent / "keys.env", verbose=True)

from smolbench.induction.periodic import (  # noqa: E402  (env first; see notebook cell 1)
    PeriodicConfig,
    Prompter,
    get_periodic_numeric_quiz,
    get_periodic_zero_info_numeric_quiz,
    numeric_count_query_gen,
)
from smolbench.induction.experiment import InductionExperiment  # noqa: E402

MODEL_QWEN = "qwen3.5-397b-a17b"
MODEL_NEMOTRON = "nemotron-3-super-120b-a12b"
MODEL_GPTOSS = "gpt-oss-120b"

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
# 4 conditions = 3 amounts of positive information (intensional rules /
# extensional full listing / noise-padded intensional, a length control) + a
# ZERO-info baseline (empty context -> chance floor). Adding "zero" is
# non-breaking for the existing intens/extens/noise replicates: those three come
# from the same get_periodic_numeric_quiz call as before, and the zero quiz is a
# separate deterministic call, so rep_1776..1803 resume-skip unchanged.
INFO_TYPES: tuple[str, ...] = ("intens", "extens", "noise_intens", "zero")


def make_quizzes(seed: int) -> dict[str, tuple]:
    """Generates one replicate's four info-type quizzes, keyed by info type."""
    cfg = PeriodicConfig(n=9, labels=9, seed=seed)
    prompter = Prompter(template, {}, numeric_count_query_gen)
    intens, extens, noise_intens = get_periodic_numeric_quiz(cfg, prompter)
    zero = get_periodic_zero_info_numeric_quiz(cfg, prompter)
    return {"intens": intens, "extens": extens, "noise_intens": noise_intens, "zero": zero}


EXPERIMENT = InductionExperiment(
    notebook_dir="periodic_moe",
    archetype_tags={MODEL_QWEN: "qwen35", MODEL_NEMOTRON: "nemotron3", MODEL_GPTOSS: "gptoss"},
    make_quizzes=make_quizzes,
    info_types=INFO_TYPES,  # 4 conditions incl. the zero-info baseline
    # 1 = pilot (seed 1776 only). Set MOE_N_REPLICATES=30 for the full run:
    # replicates resume-skip, so it extends the existing intens/extens/noise
    # 1776..1803, adds seeds 1804/1805, and fills the new zero-info condition.
    n_replicates=int(os.environ.get("MOE_N_REPLICATES", "1")),
    base_seed=BASE_SEED,
    state_file=".ec2_state_periodic_moe.json",
)


def main() -> None:
    EXPERIMENT.provision()
    # Smallest model first -- see module docstring. Now on the vLLM NIGHTLY image
    # (keys.env), which supports Qwen3.5's arch, so all three run. gpt-oss serves
    # first (smallest) -> the cheap fail-fast smoke of the nightly image. gpt-oss
    # + nemotron replicates already exist from the v0.25.1 pilot so they
    # resume-skip (their serve still re-validates the nightly), and Qwen3.5 (FP8
    # ~397GB, fits p5) produces the missing 3rd pilot -> unblocks R-sizing.
    for model in (MODEL_GPTOSS, MODEL_NEMOTRON, MODEL_QWEN):
        # Qwen3.5's think-chain on the ~21k-token EXTENS prompts blew past 8192
        # tokens (truncated before it could close <think> / emit the integer ->
        # empty completion -> invalid on 8/9 extens marks; gpt-oss/nemotron fit
        # 8192 fine). Give Qwen room to finish reasoning and answer.
        mct = 65536 if model == MODEL_QWEN else 8192
        EXPERIMENT.run(model, extra_args={"max_completion_tokens": mct})
        EXPERIMENT.summarize(model)
    EXPERIMENT.teardown()
    print("PILOT COMPLETE: gpt-oss + nemotron-3 + qwen3.5 (nightly), seed 1776, box torn down", flush=True)


if __name__ == "__main__":
    main()
