"""Run the induction reports in one process, optionally ending with multiplicity_sim.

One process so the scripts share one results directory. The costly simulation,
which reads the tree only for PART 2's measured design effect and writes its
checkpoint beside it, runs only behind ``--with-sim``. CHAIN order is report
order: every report imports ``study_design`` and the later ones import
``paired_analysis``.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Bare-name imports: sibling scripts from this directory, ``_power_common`` from ``notebooks/``.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import extens_vs_noise
import paired_analysis
import power_analysis
import significance_report
import study_design

#: Report scripts in report order; each exposes ``main(results_dir)``.
CHAIN = (power_analysis, paired_analysis, significance_report, extens_vs_noise)


def _banner(name: str) -> None:
    """Print a script banner so a long combined log stays attributable."""
    print(f"\n{'=' * 78}\n{name}\n{'=' * 78}", flush=True)


def main(
    argv: Optional[list[str]] = None,
    results_dir: Path = study_design.RESULTS_DIR,
) -> int:
    """Run analysis scripts in report order.

    Parameters
    ----------
    argv : Optional[list[str]], optional
        Command-line arguments to parse.
    results_dir : Path
        Results tree handed to every script.

    Returns
    -------
    int
        Zero; every failure propagates as an exception.
    """
    parser = argparse.ArgumentParser(
        prog="run_all.py",
        description="Run the induction analysis chain in one process under the "
        "project venv: " + " -> ".join(m.__name__ for m in CHAIN) + ".",
    )
    parser.add_argument(
        "--with-sim",
        action="store_true",
        help=(
            "Also run multiplicity_sim.main() last. Off by default: it is a "
            "slow Monte Carlo study, not a report on this study's data."
        ),
    )
    args = parser.parse_args(argv)

    for module in CHAIN:
        _banner(module.__name__)
        module.main(results_dir)
    if args.with_sim:
        # Imported on request: its import-time SCENARIO_RUNGS check and cost
        # belong to the simulation, not to the reports.
        import multiplicity_sim

        _banner(multiplicity_sim.__name__)
        multiplicity_sim.main(results_dir=results_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
