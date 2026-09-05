"""Single driver over the induction study's ``analysis/`` report chain.

Runs the four result-reading scripts in their dependency order -- each later
script imports (and, at import time, invariant-checks against) the ones
before it, so this is the only order in which the chain is meaningful:

    power_analysis -> paired_analysis -> significance_report -> extens_vs_noise

All four run IN PROCESS (plain function calls, not subprocess), which is what
makes the chain testable end to end and keeps ``power_analysis.RESULTS_DIR``
resolved once for the whole run rather than once per subprocess. Each
script's own ``main()`` still works standalone; this only sequences them and
prints a banner before each so a long combined log says whose numbers are
whose.

``multiplicity_sim`` is a Monte Carlo study of test/correction choice -- it
reads no replicate tree and its simulation runs far longer than the rest of
this chain combined -- so it is NOT part of the default chain. Pass
``--with-sim`` to run it last.

Run under the project venv, from the repo root or anywhere else (the sibling
imports below are ``__file__``-anchored):
    .venv/bin/python notebooks/induction/analysis/run_all.py [--with-sim]
"""

import argparse
import sys
from pathlib import Path

# The analysis dir itself: needed when this file is loaded by path or as a
# plain sibling import (only __main__ gets its own directory on sys.path for
# free). Every script in this directory performs the identical insert for the
# identical reason -- see e.g. paired_analysis.py's or significance_report.py's
# copy of this same comment -- so the driver follows the same convention
# rather than inventing a second way to reach its siblings.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import power_analysis  # noqa: E402  (path shim above must precede the import)
import paired_analysis  # noqa: E402
import significance_report  # noqa: E402
import extens_vs_noise  # noqa: E402

# Design: imported at MODULE scope, not lazily inside main(), because
# importing multiplicity_sim is cheap -- its top-level code only defines
# functions and constants (ALPHA_BONF, N_REDUCED, ...); it reads no
# replicate tree and simulates nothing until its main()/part*() functions are
# actually called. The expense the module docstring warns about is entirely
# in CALLING multiplicity_sim.main(), which only happens below, behind
# --with-sim. A lazy import here would only defer this already-cheap step
# with no benefit, and it would cost the one property a test needs: calling
# `multiplicity_sim.main()` (an attribute lookup at call time, not a name
# bound at import time) resolves through the SAME module object a test's
# ``monkeypatch.setattr(sys.modules["multiplicity_sim"], "main", ...)``
# mutates, so a stubbed main() is honoured without this driver knowing it was
# stubbed.
import multiplicity_sim  # noqa: E402

#: The chain, in the order this driver must run it. Module objects (not
#: names), so `main` below calls each one directly without a name -> module
#: lookup; `_banner` reads each module's own `__name__` for the printed label,
#: which is the bare sibling name whether this script is imported or run as
#: __main__ (see `tests.analysis._trees.load_analysis`, which registers each
#: sibling in `sys.modules` under exactly that name).
CHAIN = (power_analysis, paired_analysis, significance_report, extens_vs_noise)


def _banner(name: str) -> None:
    """Print a delimited banner naming the script about to run.

    Parameters
    ----------
    name : str
        The script's module name, printed so a long combined log line says
        whose output follows.
    """
    rule = "=" * 78
    print(f"\n{rule}\n{name}\n{rule}", flush=True)


def main(argv: list[str] | None = None) -> int:
    """Run the analysis chain in dependency order, printing a banner per script.

    Parameters
    ----------
    argv : list of str, optional
        Command-line arguments, excluding the program name. `None` (the
        default) reads `sys.argv[1:]`, as `argparse` normally does; tests pass
        an explicit list instead.

    Returns
    -------
    int
        Always 0: every script's own `main()` raises (``SystemExit`` or
        otherwise) rather than returning a failure code, so reaching the end
        of this function means the whole chain printed successfully.
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
