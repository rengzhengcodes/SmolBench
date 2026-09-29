"""Write every Horn table and figure from the released results folder.

    python notebooks/deduction/analysis/make_figures.py --data <results folder> --out <dir>

Checks the folder against its ``MANIFEST.json``, then runs ``horn_results.py`` (tables,
summary, ladder figures), ``horn_routes.py`` (proof routes) and
``horn_reasoning_figure.py`` (reasoning length) under each scoring mode. Outputs go to
``<out>/iclr/`` (as submitted) and ``<out>/default/``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
for p in (str(REPO), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

# pylint: disable=wrong-import-position
import horn_reasoning_figure  # noqa: E402
import horn_results  # noqa: E402
import horn_routes  # noqa: E402

from smolbench.deduction.horn.extract import SCORING_MODES  # noqa: E402
from smolbench.deduction.horn.repro import check_data  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Verify the data, then write the outputs of every script under each scoring mode."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", maxsplit=1)[0])
    ap.add_argument("--data", type=Path, required=True, help="the released results folder")
    ap.add_argument("--out", type=Path, default=horn_results.OUT)
    ap.add_argument("--scoring", choices=list(SCORING_MODES), nargs="+", default=list(SCORING_MODES))
    ap.add_argument("--skip-check", action="store_true", help="do not verify the MANIFEST checksums")
    a = ap.parse_args(argv)
    if not a.skip_check:
        problems = check_data(a.data)
        if problems:
            for p in problems:
                print(f"data: {p}")
            return 1
        print(f"data: {a.data} matches its MANIFEST")
    for mode in a.scoring:
        common = ["--data", str(a.data), "--scoring", mode, "--out", str(a.out)]
        for script in (horn_results, horn_routes, horn_reasoning_figure):
            print(f"== {script.__name__} ({mode})", flush=True)
            rc = script.main(common)
            if rc:
                return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
