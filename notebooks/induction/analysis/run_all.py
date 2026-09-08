"""Run induction reports, optionally including multiplicity_sim.

Run in process so imports share one results directory. Exclude the costly,
result-free simulation unless ``--with-sim`` is passed.
"""

import argparse
import sys
from pathlib import Path

# Add sibling scripts when imported outside ``__main__``.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import power_analysis  # noqa: E402  (path shim above must precede the import)
import paired_analysis  # noqa: E402
import significance_report  # noqa: E402
import extens_vs_noise  # noqa: E402

# Keep this module-level import patchable in tests.
import multiplicity_sim  # noqa: E402

#: Modules permit direct calls and banner names.
CHAIN = (power_analysis, paired_analysis, significance_report, extens_vs_noise)


def _banner(name: str) -> None:
    """Print a script banner."""
    rule = "=" * 78
    print(f"\n{rule}\n{name}\n{rule}", flush=True)


def main(argv: list[str] | None = None) -> int:
    """Run analysis scripts in dependency order.

    Parameters
    ----------
    argv : list[str] | None, optional
        Command-line arguments.

    Returns
    -------
    int
        Success status; scripts raise on failure.
    """
    parser = argparse.ArgumentParser(
        prog="run_all.py",
        description=(
            "Run the induction study's analysis/ report chain in one process: "
            "power_analysis -> paired_analysis -> significance_report -> "
            "extens_vs_noise, in that dependency order. Must run under the "
            "project venv (.venv/bin/python), which is where numpy, scipy, "
            "statsmodels and this repo's own packages are installed."
        ),
    )
    parser.add_argument(
        "--with-sim",
        action="store_true",
        help=(
            "Also run multiplicity_sim.main() last, after the four scripts "
            "above. Off by default: multiplicity_sim reads no results tree "
            "(it is a Monte Carlo study of test/correction choice, not a "
            "report on this study's data) and its simulation takes far "
            "longer than the rest of this chain combined."
        ),
    )
    args = parser.parse_args(argv)

    for module in CHAIN:
        _banner(module.__name__)
        module.main()
    if args.with_sim:
        _banner(multiplicity_sim.__name__)
        multiplicity_sim.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
