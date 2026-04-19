"""
Classify pilot trial outcomes by failure/success mode. Goes beyond the raw
pass-rate tally: what *kind* of failure is each trial? That tells us what
the model is actually doing wrong and whether different conditions steer
the model into different failure modes.

Usage:
    uv run python -m deduction.analysis data/pilot_micro.jsonl
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# Classification buckets, ordered so the first match wins.
#
# Keep these specific-to-general — `parse_error` has to lose to
# `unknown_identifier` because an unknown id shows up as a parse error too.
CATEGORY_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("empty_output",       re.compile(r"^empty proof$", re.IGNORECASE)),
    ("type_error",         re.compile(r"type mismatch|elaboration failed|expected type", re.IGNORECASE)),
    ("unknown_identifier", re.compile(r"unknown identifier|unknown constant", re.IGNORECASE)),
    ("rewrite_failed",     re.compile(r"tactic 'rewrite' failed|tactic 'rw' failed", re.IGNORECASE)),
    ("simp_failed",        re.compile(r"simp made no progress|tactic 'simp' failed", re.IGNORECASE)),
    ("tactic_failed",      re.compile(r"tactic '[^']+' failed", re.IGNORECASE)),
    ("parse_error",        re.compile(r"expected tactic|unknown tactic|(?:un)?expected end of input|expected '[^']+'|expected token", re.IGNORECASE)),
    ("incomplete_proof",   re.compile(r"^proof incomplete$", re.IGNORECASE)),
]


def classify(record: dict) -> str:
    if record.get("ok"):
        return "pass"
    err = record.get("error") or ""
    for label, pat in CATEGORY_PATTERNS:
        if pat.search(err):
            return label
    return "other"


def load_records(path: Path) -> List[dict]:
    out: List[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def summarize(records: List[dict], *, sample_errors: int = 1) -> None:
    print(f"=== {len(records)} trials ===\n")

    # Overall tally
    overall = Counter(classify(r) for r in records)
    total = sum(overall.values())
    print("Outcome distribution (overall):")
    for cat, n in overall.most_common():
        print(f"  {cat:22s} {n:4d}  ({100*n/total:.0f}%)")

    # Condition x category cross-tab
    by_cond_cat: Dict[str, Counter] = defaultdict(Counter)
    for r in records:
        by_cond_cat[r["condition"]][classify(r)] += 1
    conditions = list(by_cond_cat.keys())
    cats = [c for c, _ in overall.most_common()]
    print("\nBy condition x outcome:")
    print(f"  {'condition':15s}  " + "  ".join(f"{c:>18s}" for c in cats))
    for cond in conditions:
        cells = by_cond_cat[cond]
        n_cond = sum(cells.values())
        row = [f"{cells[c]:4d}/{n_cond:<4d}" for c in cats]
        print(f"  {cond:15s}  " + "  ".join(f"{cell:>18s}" for cell in row))

    # Sample error messages per category
    if sample_errors:
        print(f"\nSample errors per category (first {sample_errors} each):")
        samples: Dict[str, List[str]] = defaultdict(list)
        for r in records:
            cat = classify(r)
            if cat != "pass" and len(samples[cat]) < sample_errors:
                err = (r.get("error") or "").strip().split("\n")[0][:120]
                samples[cat].append(err)
        for cat in cats:
            if cat == "pass":
                continue
            for err in samples.get(cat, []):
                print(f"  [{cat}] {err!r}")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/trials.jsonl>", file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])
    records = load_records(path)
    summarize(records)


if __name__ == "__main__":
    main()
