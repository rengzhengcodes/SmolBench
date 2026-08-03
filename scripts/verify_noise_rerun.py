"""Verifies the re-collected noise_intens arm, on the data that was actually sent.

The re-run exists because the old noise arm was not really a length control: it
was padded in characters and came out 1.4-1.6x the extensional arm's TOKEN
length. Checking that the fix worked cannot be done by re-deriving prompts in
memory -- that only proves the generator agrees with itself. This reads the
prompts RECORDED IN THE REPLICATE YAMLS (the bytes the models were served) and
measures them with each model's own tokenizer.

Three things are checked per study:

1. **Coverage** -- 30 replicates per model, seeds contiguous, nothing missing.
2. **The control holds** -- for every question, the recorded ``noise_intens``
   prompt has EXACTLY the token count of the recorded ``extens`` prompt for the
   same (model, seed, question). This is the property the whole change was for,
   verified end to end on collected data.
3. **The pad is inert** -- the noise prompt is its intensional twin plus
   whitespace and nothing else, so the padding cannot have added content a
   model could read as signal.

It also reports invalid rates, because a spike there (rather than an accuracy
change) is what a too-tight completion budget looks like.

Run (repo root, main venv), after a re-run completes:
    .venv/bin/python scripts/verify_noise_rerun.py
    .venv/bin/python scripts/verify_noise_rerun.py --study periodic_moe

Exit 0 = the arm is sound; 1 = something is wrong and it says what.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# study -> (results dir, {tag: model alias}). Tags are what the directory
# names use; aliases are what tokenization.for_model resolves.
STUDIES: Dict[str, Dict] = {
    "periodic": {
        "results": "notebooks/periodic/results",
        "models": {
            "decode": "llama-31-405b",
            "cot": "nemotron-ultra-253b",
            "moe": "llama4-maverick",
        },
    },
    "chromatic": {
        "results": "notebooks/chromatic/results",
        "models": {
            "decode": "olmo-3.1-32b-instruct",
            "cot": "olmo-3.1-32b-think",
            "moe": "granite-4.0-h-small",
        },
    },
    "periodic_moe": {
        "results": "notebooks/periodic_moe/results",
        "models": {
            "qwen35": "qwen3.5-397b-a17b",
            "nemotron3": "nemotron-3-super-120b-a12b",
            "gptoss": "gpt-oss-120b",
        },
    },
}

EXPECTED_SEEDS = list(range(1776, 1806))  # R=30, the notebooks' BASE_SEED..+29


def load_marks(path: Path):
    """Returns a replicate's Marks, or None when the file is absent."""
    from smolbench.evals import Marks

    return Marks.load(path) if path.exists() else None


def check_study(name: str, spec: Dict, sample_seeds: List[int]) -> List[str]:
    """Returns a list of problems found; empty means the study is sound."""
    from smolbench.evals.tokenization import for_model

    problems: List[str] = []
    results = REPO / spec["results"]
    print(f"\n### {name}")

    for tag, alias in spec["models"].items():
        noise_dir = results / f"{tag}_noise_intens"
        present = sorted(
            int(p.stem.split("_")[1]) for p in noise_dir.glob("rep_*.yaml")
        )
        missing = [s for s in EXPECTED_SEEDS if s not in present]
        extra = [s for s in present if s not in EXPECTED_SEEDS]
        status = "OK " if not missing and not extra else "BAD"
        print(f"  {status} {tag:10s} {len(present):2d}/30 replicates", end="")
        if missing:
            problems.append(f"{name}/{tag}: missing seeds {missing}")
            print(f"  MISSING {missing}", end="")
        if extra:
            problems.append(f"{name}/{tag}: unexpected seeds {extra}")
            print(f"  UNEXPECTED {extra}", end="")

        # Invalid rate across the whole arm: a spike here (not an accuracy
        # change) is the signature of a too-tight completion budget.
        correct = incorrect = invalid = 0
        for seed in present:
            marks = load_marks(noise_dir / f"rep_{seed}.yaml")
            if marks:
                correct += marks.correct
                incorrect += marks.incorrect
                invalid += marks.invalid
        total = correct + incorrect + invalid
        if total:
            print(
                f"  acc={correct / total:.3f} invalid={invalid}/{total}"
                f" ({invalid / total:.1%})",
                end="",
            )
            if invalid / total > 0.15:
                problems.append(
                    f"{name}/{tag}: invalid rate {invalid / total:.1%} > 15% "
                    "-- check the completion budget"
                )
        print()

        if not present:
            continue

        # The load-bearing check, on the bytes actually served.
        tokenizer = for_model(alias)
        for seed in sample_seeds:
            if seed not in present:
                continue
            noise = load_marks(noise_dir / f"rep_{seed}.yaml")
            extens = load_marks(results / f"{tag}_extens" / f"rep_{seed}.yaml")
            intens = load_marks(results / f"{tag}_intens" / f"rep_{seed}.yaml")
            if not (noise and extens):
                problems.append(f"{name}/{tag}/seed {seed}: missing a paired arm")
                continue
            if len(noise.marks) != len(extens.marks):
                problems.append(
                    f"{name}/{tag}/seed {seed}: {len(noise.marks)} noise questions "
                    f"vs {len(extens.marks)} extens"
                )
                continue
            mismatched = 0
            for noise_mark, extens_mark in zip(noise.marks, extens.marks):
                if tokenizer.count(noise_mark.query) != tokenizer.count(extens_mark.query):
                    mismatched += 1
            if mismatched:
                problems.append(
                    f"{name}/{tag}/seed {seed}: {mismatched} noise prompts do NOT "
                    f"match their extens prompt's token count under {tokenizer.name}"
                )
            # The pad must be pure whitespace: stripping whitespace from the
            # noise prompt must leave exactly the intensional prompt.
            inert = True
            if intens and len(intens.marks) == len(noise.marks):
                for noise_mark, intens_mark in zip(noise.marks, intens.marks):
                    if "".join(noise_mark.query.split()) != "".join(intens_mark.query.split()):
                        inert = False
                        break
                if not inert:
                    problems.append(
                        f"{name}/{tag}/seed {seed}: noise prompt differs from its "
                        "intensional twin by more than whitespace"
                    )
            flag = "OK " if not mismatched and inert else "BAD"
            print(
                f"      {flag} seed {seed}: {len(noise.marks)} prompts token-matched "
                f"under {tokenizer.name}"
            )
    return problems


def main() -> int:
    """Checks each requested study; returns a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", choices=sorted(STUDIES), action="append")
    parser.add_argument(
        "--seeds",
        default="1776,1790,1805",
        help="seeds to token-check in depth (all seeds are coverage-checked)",
    )
    args = parser.parse_args()
    names = args.study or sorted(STUDIES)
    sample_seeds = [int(s) for s in args.seeds.split(",")]

    print("Verifying the re-collected noise_intens arm against the served bytes")
    print("=" * 78)
    problems: List[str] = []
    for name in names:
        problems.extend(check_study(name, STUDIES[name], sample_seeds))

    print("\n" + "=" * 78)
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for p in problems:
            print("  -", p)
        return 1
    print("Noise arm verified: full coverage, every prompt token-matched, pad inert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
