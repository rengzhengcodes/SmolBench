"""Review-round control arms (rep, tjunk) next to the paper's four arms, on Bedrock and Haiku.

Reads the per-cell verdicts in ``notebooks/deduction/review/`` and writes
``notebooks/deduction/review/review_table.md``:

* Bedrock: one row per model at its paper chain length m. Pass rates of lem, pad, disc
  and both (the September 2026 cells behind the paper table) and of rep and tjunk (run
  in November 2026 with the same settings and the iclr scoring rule), followed by the
  seed-paired deltas rep - lem, rep - pad, tjunk - pad and both - tjunk.
* Haiku 4.5 at m = 160: pass rate per arm over the cells that completed (one replicate),
  and the lem calibration ladder.

Statistics are those of ``horn_results.py``: the unit is the per-seed pass rate (mean over
replicates), a delta is the mean seed-paired difference in points with a 95% percentile
bootstrap CI and a sign-flip p-value (``smolbench.deduction.horn.stats.contrast``).

usage: horn_review_arms.py [--review DIR]
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

from smolbench.deduction.horn.stats import contrast, format_p, pass_rate

REVIEW = Path(__file__).resolve().parents[1] / "review"
BEDROCK_ARMS = ("lem", "pad", "disc", "both", "rep", "tjunk")
HAIKU_ARMS = ("lem", "pad", "disc", "both", "fwd", "tjunk", "rep", "marked-lemma")
CONTRASTS = (("rep", "lem"), ("rep", "pad"), ("tjunk", "pad"), ("both", "tjunk"))
BELOW_FLOOR = {"ministral-3-8b", "ministral-3-3b"}


def bedrock_table(path: Path, rng: random.Random) -> list[str]:
    """Markdown rows for the Bedrock models, in file order."""
    cells: dict[str, dict[str, dict[int, list[bool]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    m_of: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cells[r["model"]][r["arm"]][int(r["seed"])].append(r["verdict"] == "success")
            m_of[r["model"]] = int(r["m"])
    head = "| model | m | " + " | ".join(BEDROCK_ARMS) + " | " + " | ".join(
        f"{a} − {b}" for a, b in CONTRASTS
    ) + " |"
    out = [head, "|" + "---|" * (2 + len(BEDROCK_ARMS) + len(CONTRASTS))]
    for model, arms in cells.items():
        flag = " †" if model in BELOW_FLOOR else ""
        rates = [f"{pass_rate(arms[a]):.1f}" for a in BEDROCK_ARMS]
        deltas = []
        for a, b in CONTRASTS:
            mean, lo, hi, p, n = contrast(arms[a], arms[b], rng)
            deltas.append(f"{mean:+.1f} [{lo:+.1f}, {hi:+.1f}] {format_p(p, n)}")
        out.append(f"| {model}{flag} | {m_of[model]} | " + " | ".join(rates + deltas) + " |")
    return out


def haiku_tables(cells_path: Path, calib_path: Path) -> list[str]:
    """Markdown for the Haiku m = 160 arms and the lem calibration ladder."""
    by_arm: dict[str, list[bool]] = defaultdict(list)
    with cells_path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            by_arm[r["arm"]].append(r["verdict"] == "success")
    out = ["| arm | pass | n |", "|---|---|---|"]
    for a in HAIKU_ARMS:
        v = by_arm.get(a, [])
        out.append(f"| {a} | {100 * sum(v) / max(1, len(v)):.1f} | {len(v)} |")
    ladder: dict[int, list[bool]] = defaultdict(list)
    with calib_path.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            ladder[int(r["m"])].append(r["verdict"] == "success")
    out += ["", "| m | lem pass |", "|---|---|"]
    out += [f"| {m} | {sum(v)}/{len(v)} |" for m, v in sorted(ladder.items())]
    return out


def main(argv: list[str] | None = None) -> None:
    """Write ``review_table.md`` next to the cell files."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", type=Path, default=REVIEW)
    a = ap.parse_args(argv)
    rng = random.Random(0)
    lines = ["# Review-round arms", "", "## Bedrock (300 cells per arm, 100 seeds × 3 replicates)", ""]
    lines += bedrock_table(a.review / "bedrock_cells.csv", rng)
    lines += ["", "† below the calibration floor (lem < 60% at m = 1).", ""]
    lines += ["## Haiku 4.5, m = 160 (completed cells, 1 replicate)", ""]
    lines += haiku_tables(a.review / "haiku_m160_cells.csv", a.review / "haiku_calibration.csv")
    (a.review / "review_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
