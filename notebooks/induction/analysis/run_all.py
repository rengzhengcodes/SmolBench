"""Run the induction study's four analysis reports, then optionally multiplicity_sim.

Order is fixed -- power_analysis -> paired_analysis -> significance_report ->
extens_vs_noise -- because each later script import-time-checks invariants
against the ones before it. Runs in process (not subprocess) so the chain is
testable end to end and ``power_analysis.RESULTS_DIR`` resolves once for the
whole run. ``multiplicity_sim`` is excluded by default (pass ``--with-sim``):
it reads no replicate tree and its Monte Carlo run outlasts the rest of the
chain combined.

    .venv/bin/python notebooks/induction/analysis/run_all.py [--with-sim]
"""

import argparse
import sys
from pathlib import Path

# Only __main__ gets its own directory on sys.path for free; needed for the sibling imports below.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import power_analysis  # noqa: E402  (path shim above must precede the import)
import paired_analysis  # noqa: E402
import significance_report  # noqa: E402
import extens_vs_noise  # noqa: E402

# Imported at module scope, not lazily: the import itself is cheap (only defines functions and
# constants), and calling multiplicity_sim.main() below then resolves through the same module
# object a test's monkeypatch.setattr(sys.modules["multiplicity_sim"], "main", ...) mutates.
import multiplicity_sim  # noqa: E402

#: Module objects, not names, so `main` calls each directly and `_banner` reads its `__name__`.
CHAIN = (power_analysis, paired_analysis, significance_report, extens_vs_noise)


def _banner(name: str) -> None:
    """Print a delimited banner naming the script about to run."""
    rule = "=" * 78
    print(f"\n{rule}\n{name}\n{rule}", flush=True)


def main(argv: list[str] | None = None) -> int:
    """Run the analysis chain in dependency order, printing a banner per script.

    Parameters
    ----------
    argv : list[str] | None, optional
        command-line arguments to parse.

    Returns
    -------
    int
        always 0: each script's own `main()` raises rather than returning a failure code.
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
