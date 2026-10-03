"""Audit induction seed coverage against the configured model and arm grid.

Exits 1 for an empty grid or any missing or unexpected seed.
    scripts/results/audit_run_completeness.py
"""

import argparse
import functools
import importlib.util
import os
import pathlib
import sys
from typing import Any, Dict, List, Optional, Tuple

from smolbench.evals.results_store import S3ResultsStore, resolve_results_location

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: Induction study ``S3ResultsStore.experiment`` segment.
INDUCTION_EXPERIMENT = "induction"


@functools.lru_cache(maxsize=1)
def _induction_driver() -> Any:
    """Load ``notebooks/induction/run_study.py`` by file path; cached.

    Load lazily until the audit needs the configured seed grid; path loading
    avoids ambiguity with other ``run_study.py`` modules.
    """
    path = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
    spec = importlib.util.spec_from_file_location("induction_run_study", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _induction_store() -> S3ResultsStore:
    """Build the ``S3ResultsStore`` `audit_induction` reads real seeds from.

    Region follows ``SMOLBENCH_RESULTS_S3_REGION``, then ``AWS_REGION``.
    """
    bucket, base_prefix = resolve_results_location()
    region = (
        os.environ.get("SMOLBENCH_RESULTS_S3_REGION")
        or os.environ.get("AWS_REGION")
        or None
    )
    return S3ResultsStore(
        bucket=bucket,
        base_prefix=base_prefix,
        experiment=INDUCTION_EXPERIMENT,
        region=region,
    )


def audit_induction(
    models: Optional[List[str]] = None, *, store: Any = None
) -> Tuple[Dict[str, Dict[str, Dict[str, List[int]]]], int]:
    """Report induction ``(model, arm)`` seed-set mismatches against the pinned grid.

    Walk the expected grid so absent S3 cells are reported; backend errors
    propagate rather than reading as zero seeds. Unrecognized `models` raise
    `SystemExit` rather than silently auditing nothing.

    Parameters
    ----------
    models : Optional[List[str]], optional
        Model keys to audit.
    store : Any, optional
        Store providing ``list_seeds``.

    Returns
    -------
    Tuple[Dict[str, Dict[str, Dict[str, List[int]]]], int]
        Mismatches by model and arm, plus grid cells examined.
    """
    driver = _induction_driver()
    roster: Dict[str, str] = driver.MODELS
    info_types: Tuple[str, ...] = tuple(driver.INFO_TYPES)
    base_seed: int = driver.BASE_SEED
    n_replicates: int = driver.N_REPLICATES

    selected = list(roster) if models is None else list(models)
    bad = [m for m in selected if m not in roster]
    if bad:
        raise SystemExit(
            f"audit_induction: unknown induction model key(s) {bad!r} -- valid "
            f"MODELS keys are {sorted(roster)!r}"
        )

    if store is None:
        store = _induction_store()

    expected = set(range(base_seed, base_seed + n_replicates))
    out: Dict[str, Dict[str, Dict[str, List[int]]]] = {}
    for model in selected:
        tag = roster[model]
        for info in info_types:
            # Propagate backend errors; never read them as empty seeds.
            landed = set(store.list_seeds(model, tag, info))
            missing = sorted(expected - landed)
            unexpected = sorted(landed - expected)
            if missing or unexpected:
                out.setdefault(model, {})[info] = {
                    "missing": missing,
                    "unexpected": unexpected,
                }
    return out, len(selected) * len(info_types)


def main() -> int:
    """Audit induction seed coverage."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()

    gaps, examined = audit_induction()
    print("\nINDUCTION seed coverage:")
    failures: List[str] = []
    if examined == 0:
        print("\n*** AUDITED NOTHING: the induction model/arm grid was empty ***")
        print("An empty grid is not a pass. Check the configured induction roster.")
        failures.append("induction: audited 0 (model, arm) cells")
    elif gaps:
        for model, arms in sorted(gaps.items()):
            worst_missing = max(len(a["missing"]) for a in arms.values())
            unexpected_seeds = sorted(
                {s for a in arms.values() for s in a["unexpected"]}
            )
            failures.append(
                f"{model}: induction missing up to {worst_missing} seed(s) per arm"
                + (
                    f", unexpected seed(s) {unexpected_seeds}"
                    if unexpected_seeds
                    else ""
                )
            )
            print(f"  FAULT {model}: missing/unexpected seeds per arm -> {arms}")
    else:
        driver = _induction_driver()
        base_seed, n_replicates = driver.BASE_SEED, driver.N_REPLICATES
        print(
            f"  ok: every (model, arm) of the {examined} examined has seeds "
            f"{base_seed}..{base_seed + n_replicates - 1}"
        )

    if failures:
        print("\n*** COMPLETENESS FAULTS ***")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nAll audited induction seeds are complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
