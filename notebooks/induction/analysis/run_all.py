"""Run the induction reports in one process, optionally ending with multiplicity_sim.

One process so the scripts share one results directory. The costly, result-free
simulation runs only behind ``--with-sim``. CHAIN order is fixed: each later script
import-time-checks invariants against the earlier ones.
"""

import argparse
import importlib
import sys
from pathlib import Path

# Add sibling scripts when imported outside ``__main__``.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# isort: off
import power_analysis  # noqa: E402
import paired_analysis  # noqa: E402
import significance_report  # noqa: E402
import extens_vs_noise  # noqa: E402

# isort: on

#: Report scripts in dependency order; each exposes ``main(results_dir)``.
CHAIN = (power_analysis, paired_analysis, significance_report, extens_vs_noise)


def _banner(name: str) -> None:
    """Print a script banner so a long combined log stays attributable.

    Parameters
    ----------
    name : str
        Script name printed between the rules.
    """
    print(f"\n{'=' * 78}\n{name}\n{'=' * 78}", flush=True)


def main(
    argv: list[str] | None = None,
    results_dir: Path = power_analysis.RESULTS_DIR,
) -> int:
    """Run analysis scripts in dependency order.

    Parameters
    ----------
    argv : list[str] | None, optional
        Command-line arguments to parse.
    results_dir : Path
        Results tree handed to every script.

    Returns
    -------
    int
        Always 0 after all analysis scripts complete successfully.
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
        # Imported here so the default chain never pays for it.
        multiplicity_sim = importlib.import_module("multiplicity_sim")
        _banner(multiplicity_sim.__name__)
        multiplicity_sim.main(results_dir=results_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
