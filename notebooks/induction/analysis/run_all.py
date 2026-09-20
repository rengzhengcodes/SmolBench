"""Run induction reports, optionally including multiplicity_sim.

Run in process so imports share one results directory. Exclude the costly,
result-free simulation unless ``--with-sim`` is passed.
CHAIN order is fixed: each later script import-time-checks invariants against the earlier ones.
"""

import argparse
import importlib
import sys
from pathlib import Path

# Add sibling scripts when imported outside ``__main__``.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import extens_vs_noise  # noqa: E402
import paired_analysis  # noqa: E402
import power_analysis  # noqa: E402
import significance_report  # noqa: E402

#: Modules permit direct calls and banner names.
CHAIN = (power_analysis, paired_analysis, significance_report, extens_vs_noise)

#: Imported only behind ``--with-sim`` so the default chain never pays for it.
SIM_MODULE = "multiplicity_sim"


def _banner(name: str) -> None:
    """Print a script banner."""
    rule = "=" * 78
    print(f"\n{rule}\n{name}\n{rule}", flush=True)


def main(
    argv: list[str] | None = None,
    results_dir: Path = power_analysis.RESULTS_DIR,
) -> int:
    """Run analysis scripts in dependency order.

    Parameters
    ----------
    argv : list[str] | None, optional
        Command-line arguments to parse.

    Returns
    -------
    int
        Always 0 after all analysis scripts complete successfully.
    """
    parser = argparse.ArgumentParser(
        prog="run_all.py",
        description=(
            "Run the induction analysis chain in one process under the "
            "project venv: power_analysis -> paired_analysis -> "
            "significance_report -> extens_vs_noise."
        ),
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
        multiplicity_sim = importlib.import_module(SIM_MODULE)
        _banner(multiplicity_sim.__name__)
        multiplicity_sim.main(results_dir=results_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
