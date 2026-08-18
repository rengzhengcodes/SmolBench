#!/usr/bin/env python
"""DETERMINISM_PLAN §6.3 -- the free, biased lower bound on score flips.

The 2026-08-15 resampling bug left a handful of deduction cells with MORE
THAN ONE surviving generation attempt (attempts that reached the model and
returned; different serving processes drew them). Those are paired draws of
the same cell across processes, already collected, at zero marginal cost --
so they bound the §6.2 flip rate for free.

THE CAVEAT THAT MUST RIDE EVERY USE OF THIS NUMBER (§6.3): the sample is
selected ON CELL OUTCOME -- a cell was re-drawn precisely because its first
attempt looked empty/failed -- so the flip rate here is NOT an unbiased
estimate. Conditioning on the first draw invites regression to the mean on
the second, which argues this OVER-estimates the population flip rate; that
direction is reasoned, not measured. Treat it as a sanity check on §6.2's
design, never as the headline.

Both attempts of every pair are graded by TODAY's verifier (same machinery
as scripts/recover_dojoinit_std.py, i.e. lean_verify_rows' own code paths),
so verifier identity cancels within a pair. Reads the study S3 prefixes
READ-ONLY; writes one local JSON report. Run under .venv-lean with
~/.elan/bin on PATH:

    .venv-lean/bin/python scripts/flip_free_bound.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

#: Lanes named by the inventory's §6.3 accounting, with its expected counts
#: of >1-surviving-attempt cells (2026-08-15). Reported against, not gated
#: on: the count derivation is re-done here from all_rows directly.
LANES_EXPECTED = {"ministral-3-3b": 63, "qwen3.5-27b": 6, "gemma-4-31b": 5}
OUT = REPO / "notebooks" / "deduction" / "results" / "flip_free_bound_2026-08-18.json"
STD_PREFIX = ".lake/packages/std/"


def _rec():
    spec = importlib.util.spec_from_file_location(
        "recover_dojoinit_std", REPO / "scripts" / "recover_dojoinit_std.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def surviving(row: dict) -> bool:
    """An attempt that reached the model and returned (its output IS data).

    ``prompt_tokens > 0`` is the established discriminator (the server
    counted a prompt, so the model was asked); an ``error`` marker means the
    attempt was lost to infrastructure instead.
    """
    return (row.get("prompt_tokens") or 0) > 0 and not row.get("error")


def stream_all_rows(rec, lane):
    uri_lane = f"scaling_{lane}"
    import subprocess
    proc = subprocess.Popen(
        ["aws", "s3", "cp",
         f"s3://{rec.S3_BUCKET}/{rec.S3_RUNS_PREFIX}/{uri_lane}/all_rows.jsonl", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.stdout is not None
    for line in proc.stdout:
        if line.strip():
            yield json.loads(line)
    if proc.wait() != 0:
        raise RuntimeError(f"s3 read failed for {lane}: {proc.stderr.read()[:300]}")


def exact_binom_ci(k: int, n: int, alpha: float = 0.05):
    """Clopper-Pearson via the beta quantile (scipy-free bisection)."""
    if n == 0:
        return (0.0, 1.0)

    def beta_ppf(q, a, b):
        from math import lgamma, exp, log

        def logbeta_pdf(x):
            return (a - 1) * log(x) + (b - 1) * log(1 - x) - (
                lgamma(a) + lgamma(b) - lgamma(a + b))

        # numeric CDF by Simpson on a fine grid (adequate at n<=200)
        N = 200000
        acc, target = 0.0, q
        for i in range(1, N + 1):
            x = i / (N + 1)
            acc += exp(logbeta_pdf(x)) / (N + 1)
            if acc >= target:
                return x
        return 1.0

    lo = 0.0 if k == 0 else beta_ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta_ppf(1 - alpha / 2, k + 1, n - k)
    return (lo, hi)


def main():
    rec = _rec()
    lock = rec.take_lock()  # noqa: F841 -- exclusive vs other Dojo users
    rec.require_lake()
    report = {"caveat": "SELECTED-ON-OUTCOME sample (see module docstring): "
                        "over-estimate direction argued, not measured. "
                        "Sanity check for section 6.2, never the headline.",
              "lanes": {}}
    all_pairs = []
    for lane, expected in LANES_EXPECTED.items():
        cells = defaultdict(list)
        for row in stream_all_rows(rec, lane):
            if row.get("kind") != "cell":
                continue
            key = (row["theorem_id"], row["k"], row["rung"], row.get("replicate_idx", 0))
            cells[key].append(row)
        multi = {k: [r for r in rows if surviving(r)]
                 for k, rows in cells.items()}
        multi = {k: rows for k, rows in multi.items() if len(rows) >= 2}
        print(f"{lane}: {len(multi)} cells with >=2 surviving attempts "
              f"(inventory expected {expected})")
        # Build verification rows: one per (cell, attempt_index).
        vrows = []
        for key, rows in sorted(multi.items()):
            for ai, row in enumerate(rows):
                vrows.append({
                    "theorem_id": key[0], "k": key[1], "rung": key[2],
                    "replicate_idx": key[3], "model": lane,
                    "file_path": rows[0].get("file_path", ""),
                    "candidate_proof": row.get("candidate_proof", ""),
                    "_attempt": ai, "_cell": key,
                    "verdict": "unverified",
                })
        t0 = time.monotonic()
        rec.verify_rows_in_place(vrows)
        elapsed = time.monotonic() - t0
        by_cell = defaultdict(list)
        for v in vrows:
            by_cell[v["_cell"]].append(v)
        pairs = []
        for key, atts in sorted(by_cell.items()):
            atts.sort(key=lambda v: v["_attempt"])
            verdicts = [a["verdict"] for a in atts]
            passes = [v == "success" for v in verdicts]
            pairs.append({
                "lane": lane, "cell": list(key),
                "is_std": str(atts[0].get("file_path", "")).startswith(STD_PREFIX)
                          or key[0].split(".")[0] in ("Array", "List", "String",
                                                      "Std", "Int", "Nat"),
                "verdicts": verdicts,
                "identical_text": len({a["candidate_proof"] for a in atts}) == 1,
                "flip_first_vs_second": passes[0] != passes[1],
                "flip_first_vs_last": passes[0] != passes[-1],
            })
        all_pairs.extend(pairs)
        report["lanes"][lane] = {
            "n_multi_surviving": len(multi), "inventory_expected": expected,
            "verify_seconds": round(elapsed, 1), "pairs": pairs,
        }
    n = len(all_pairs)
    flips = sum(p["flip_first_vs_second"] for p in all_pairs)
    ident = sum(p["identical_text"] for p in all_pairs)
    lo, hi = exact_binom_ci(flips, n)
    report["summary"] = {
        "n_pairs": n, "identical_text_pairs": ident,
        "flips_first_vs_second": flips,
        "flip_rate": round(flips / n, 4) if n else None,
        "ci95": [round(lo, 4), round(hi, 4)],
        "flips_first_vs_last": sum(p["flip_first_vs_last"] for p in all_pairs),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1))
    print(json.dumps(report["summary"], indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
