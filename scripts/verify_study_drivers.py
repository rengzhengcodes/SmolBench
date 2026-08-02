"""Proves the headless study drivers reproduce the replicates already on disk.

Why this exists
---------------
The induction studies' ``noise_intens`` arm has to be re-collected, but the
``intens``/``extens`` arms it will be compared against were generated months
ago by the notebooks. New noise data is only worth anything if it PAIRS with
that existing data -- same labels, same queries, same prompt wording, same
seeds. A driver that duplicates a notebook's config (the pattern
``run_pilot.py`` established, and the one ``run_study.py`` follows) is one
stray character away from silently producing an arm that pairs with nothing.

So this does not compare source code or templates. It regenerates each
driver's prompts and diffs them against the prompts RECORDED INSIDE the
replicate YAMLs on disk, which are the actual bytes those models were asked.
If every recorded prompt comes back identical, the driver provably continues
the same experiment.

The noise arm is deliberately NOT checked: it is the arm that changed, and it
has no on-disk data left to compare against.

Run (repo root, main venv), before any live run:
    .venv/bin/python scripts/verify_study_drivers.py
    .venv/bin/python scripts/verify_study_drivers.py --seeds 1776,1790,1805

Exit code 0 = every checked prompt matched; 1 = a driver has drifted.
"""

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO = Path(__file__).resolve().parents[1]

# (label, driver path, results dir, {model alias: tag}) per study. periodic_moe
# is included even though its driver predates this check -- it is the same
# duplication risk.
STUDIES: Tuple[Tuple[str, str, str], ...] = (
    ("periodic", "notebooks/periodic/run_study.py", "notebooks/periodic/results"),
    ("chromatic", "notebooks/chromatic/run_study.py", "notebooks/chromatic/results"),
    ("periodic_moe", "notebooks/periodic_moe/run_pilot.py", "notebooks/periodic_moe/results"),
)

# Arms with data on disk to compare against. "noise_intens" is excluded by
# design (see the module docstring); "zero" has no counterpart in the tuple a
# quiz factory returns for the other studies, but periodic_moe's factory does
# emit it, so it is checked wherever present.
CHECKED_ARMS = ("intens", "extens", "zero")


def load_driver(path: str):
    """Imports a driver module by path WITHOUT running its main().

    Drivers call ``load_dotenv`` at import time (they must, before
    ``smolbench.evals.ec2`` is imported) but only provision inside
    ``main()``, so importing one is inert -- no AWS calls, no spend.
    """
    spec = importlib.util.spec_from_file_location(f"driver_{Path(path).stem}", REPO / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recorded_prompts(results_dir: Path, tag: str, arm: str, seed: int) -> List[str]:
    """Returns the prompts recorded in one replicate YAML, in order.

    Uses ``Marks.load`` rather than a regex so the comparison is against the
    same deserialization the analysis path uses.
    """
    from smolbench.evals import Marks

    path = results_dir / f"{tag}_{arm}" / f"rep_{seed}.yaml"
    if not path.exists():
        return []
    return [mark.query for mark in Marks.load(path).marks]


def check_study(label: str, driver_path: str, results_path: str, seeds: List[int]) -> Dict:
    """Regenerates and diffs one study's prompts. Returns a result summary."""
    driver = load_driver(driver_path)
    results_dir = REPO / results_path
    checked = 0
    mismatches: List[str] = []
    skipped: List[str] = []

    for model, tag in driver.EXPERIMENT.archetype_tags.items():
        for seed in seeds:
            wanted = {
                arm: recorded_prompts(results_dir, tag, arm, seed) for arm in CHECKED_ARMS
            }
            if not any(wanted.values()):
                skipped.append(f"{tag}/seed {seed}: nothing on disk")
                continue
            # One generation call per (model, seed) covers every arm.
            quizzes = driver.make_quizzes(seed, model)
            for arm, expected in wanted.items():
                if not expected:
                    continue
                got = [q.prompt for q in quizzes.get(arm, ())]
                if len(got) != len(expected):
                    mismatches.append(
                        f"{label}/{tag}/{arm}/seed {seed}: "
                        f"{len(got)} questions generated vs {len(expected)} recorded"
                    )
                    continue
                for i, (a, b) in enumerate(zip(got, expected)):
                    if a != b:
                        mismatches.append(
                            f"{label}/{tag}/{arm}/seed {seed} q{i}: prompt differs "
                            f"(generated {len(a)} chars vs recorded {len(b)} chars)"
                        )
                        break
                checked += len(expected)

    return {"label": label, "checked": checked, "mismatches": mismatches, "skipped": skipped}


def main() -> int:
    """Checks every study; returns a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        default="1776,1790,1805",
        help="comma-separated replicate seeds to check (default: first, middle, last)",
    )
    args = parser.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]

    print(f"Verifying study drivers reproduce on-disk prompts, seeds {seeds}")
    print("=" * 78)
    failed = False
    for label, driver_path, results_path in STUDIES:
        result = check_study(label, driver_path, results_path, seeds)
        status = "FAIL" if result["mismatches"] else "OK"
        print(f"{status:4s} {label:14s} {result['checked']:6d} prompts byte-identical")
        for note in result["skipped"]:
            print(f"       skipped: {note}")
        for mismatch in result["mismatches"]:
            print(f"       MISMATCH: {mismatch}")
        failed = failed or bool(result["mismatches"])

    print("=" * 78)
    if failed:
        print("DRIFT DETECTED -- a driver would NOT continue the same experiment.")
        return 1
    print("All drivers reproduce the recorded prompts exactly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
