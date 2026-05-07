"""Probe 2: token-growth curve from probe 1 JSONL output.

Reads JSONL produced by probe_body_availability.py and computes the
abbrev-substrate file size at each depth d ∈ [0..max_depth_in_data].

Substrate model (from minif2f_v9.build_chain):
  - Depth 0 (intensional) emits no helpers; the file is just the canonical
    signature wrapped in `example : ... := by sorry`.
  - Depth k > 0 emits one `noncomputable abbrev sb_<name> := <body>` per
    unfoldable name discovered at layers 0..k-1. Layer-i helpers reference
    layer-(i+1) `sb_*` names within their bodies; layer-(k-1) bodies use the
    original Mathlib names.

Approximation: body_chars in the JSONL is the original `#print` body length.
After substitution, individual char counts shift slightly (sb_<name> vs
<name>), but the difference is small relative to the body itself, so we
report file size as canonical_sig + Σ(helper_overhead + body_chars).

Usage:
  python -m deduction.expand_mathlib.analyze_token_growth probe1_*.jsonl

Output: per-pool growth table + optional CSV for plotting.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from statistics import mean, median
from typing import List

# Boilerplate of one helper line: `noncomputable abbrev sb_<name> := <body>\n\n`
_HELPER_PREFIX = "noncomputable abbrev "
_HELPER_SEP = " := "
_BLOCK_SEP = "\n\n"
_HELPER_FIXED_OVERHEAD = (
    len(_HELPER_PREFIX) + len(_HELPER_SEP) + len(_BLOCK_SEP)
)
# `import Mathlib\n\nset_option maxHeartbeats 0\n\n` + opens line + sig wrap
_FILE_FRAME_OVERHEAD = len("import Mathlib\n\nset_option maxHeartbeats 0\n\n") + \
                       len("example  := by sorry\n")


def _sb(name: str) -> str:
    return "sb_" + re.sub(r'\W', '_', name)


def helper_chars(name: str, body_chars: int) -> int:
    """Chars contributed by one `noncomputable abbrev sb_X := <body>` block,
    including the blank-line separator that follows it in the emitted file."""
    return _HELPER_FIXED_OVERHEAD + len(_sb(name)) + body_chars


def file_chars_at(rec: dict, target_depth: int) -> int:
    """Total file char count if we expanded `rec`'s problem to `target_depth`.
    Clamped to the actually-walked depth (saturated problems plateau)."""
    total = _FILE_FRAME_OVERHEAD + rec["canonical_sig_chars"]
    if rec.get("opens"):
        total += len("open " + " ".join(rec["opens"]) + "\n")
    for layer in rec["layers"]:
        if layer["depth"] >= target_depth:
            break
        for n in layer["names"]:
            if n["has_body"]:
                total += helper_chars(n["name"], n["body_chars"])
    return total


def per_problem_curve(rec: dict, max_depth: int) -> List[int]:
    return [file_chars_at(rec, d) for d in range(max_depth + 1)]


def summarize_pool(records: List[dict], max_depth: int, label: str) -> dict:
    ok = [r for r in records if r.get("ok")]
    n = len(ok)
    print(f"\n{'='*78}")
    print(f"Pool: {label}  ({n} ok records)")

    print(f"\nFile chars at each depth (across all {n} problems):")
    print(f"  {'d':>3s}  {'mean':>7s}  {'median':>7s}  {'p10':>7s}  "
          f"{'p90':>7s}  {'min':>6s}  {'max':>6s}")
    by_depth = {}
    for d in range(max_depth + 1):
        chars = sorted(file_chars_at(r, d) for r in ok)
        p10 = chars[max(0, len(chars) // 10 - 1)]
        p90 = chars[min(len(chars) - 1, 9 * len(chars) // 10)]
        print(f"  {d:>3d}  {mean(chars):>7.0f}  {median(chars):>7.0f}  "
              f"{p10:>7d}  {p90:>7d}  {chars[0]:>6d}  {chars[-1]:>6d}")
        by_depth[d] = chars

    print(f"\nGrowth ratio chars(d)/chars(0), per-problem distribution:")
    print(f"  {'d':>3s}  {'mean':>5s}  {'median':>6s}  {'min':>5s}  {'max':>6s}  "
          f"{'frac>=1.5x':>10s}  {'frac>=5x':>8s}")
    for d in range(1, max_depth + 1):
        ratios = [
            file_chars_at(r, d) / max(file_chars_at(r, 0), 1)
            for r in ok
        ]
        n_15 = sum(1 for r in ratios if r >= 1.5)
        n_5 = sum(1 for r in ratios if r >= 5.0)
        print(f"  {d:>3d}  {mean(ratios):>5.2f}x  {median(ratios):>5.2f}x  "
              f"{min(ratios):>4.2f}x  {max(ratios):>5.2f}x  "
              f"{100*n_15/len(ratios):>9.0f}%  {100*n_5/len(ratios):>7.0f}%")

    print(f"\nProblems with ZERO growth at d={max_depth} (depth knob inert):")
    inert = [r for r in ok if file_chars_at(r, max_depth) == file_chars_at(r, 0)]
    print(f"  {len(inert)}/{n} ({100*len(inert)/n:.0f}%)")

    return by_depth


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonls", nargs="+", help="probe1 JSONL files")
    ap.add_argument("--csv-out", help="optional per-problem CSV for plotting")
    ap.add_argument("--max-depth", type=int, default=3)
    args = ap.parse_args()

    csv_rows: List[dict] = []
    for path_str in args.jsonls:
        path = Path(path_str)
        records = [json.loads(l) for l in path.open()]
        label = path.stem
        summarize_pool(records, args.max_depth, label)
        if args.csv_out:
            for r in records:
                if not r.get("ok"):
                    continue
                row = {"pool": label, "problem": r["problem"]}
                for d in range(args.max_depth + 1):
                    row[f"chars_d{d}"] = file_chars_at(r, d)
                csv_rows.append(row)

    if args.csv_out and csv_rows:
        with open(args.csv_out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            w.writeheader()
            w.writerows(csv_rows)
        print(f"\nCSV: {args.csv_out}  ({len(csv_rows)} rows)")


if __name__ == "__main__":
    main()
