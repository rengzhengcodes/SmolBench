"""Measure helper-block length at each depth d, per problem.

Reuses expand_helpers() from proof_completion_helpers.py so the helper text
is exactly what the proof-completion driver would emit. No model calls —
just lean-server #print queries to walk the dep graph.

Usage:
  python -m deduction.expand_mathlib.analyze_helper_length \\
      --n-given 0 --depths 0,1,2,3 --n-problems 30 --workers 8
"""
from __future__ import annotations

import argparse
import concurrent.futures as futs
import json
import os
import sys
import time
from statistics import mean, median
from typing import Dict, List

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import BENCHMARK_DIR, load_corpus
from deduction.expand_mathlib.proof_completion_helpers import (
    CORPUS_PATH_DENY_PREFIXES, PROOFS_DIR_DEFAULT, SERVER_DEFAULT,
    expand_helpers, load_problems, build_completion_file,
)


def measure_one(prob, n_given, depths, corpus, server_url, max_per_layer):
    """Returns dict: depth -> (helpers_chars, n_helpers, file_chars)."""
    n = n_given if n_given >= 0 else len(prob.tactics)
    out = {}
    for d in depths:
        helpers, n_h = expand_helpers(prob, n, d, corpus, server_url,
                                       max_per_layer=max_per_layer)
        code = build_completion_file(prob, n, helpers)
        out[d] = (len(helpers), n_h, len(code))
    return prob.name, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-given", type=int, default=0)
    ap.add_argument("--depths", default="0,1,2,3")
    ap.add_argument("--n-problems", type=int, default=30)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-per-layer", type=int, default=64)
    ap.add_argument("--proofs-dir", default=PROOFS_DIR_DEFAULT)
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--out", default=None,
                    help="optional JSONL path for per-problem records")
    args = ap.parse_args()

    depths = [int(d) for d in args.depths.split(",")]
    print(f"Loading corpus ...")
    full_corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    corpus = {
        n: p for n, p in full_corpus.items()
        if not any(p.file_path.startswith(d) for d in CORPUS_PATH_DENY_PREFIXES)
    }
    print(f"  {len(full_corpus)} indexed, {len(corpus)} after path filter")
    problems = load_problems(args.proofs_dir)
    if args.n_problems > 0:
        problems = problems[: args.n_problems]
    print(f"Pool: {len(problems)} problems  n_given={args.n_given}  "
          f"depths={depths}  workers={args.workers}\n")

    by_depth: Dict[int, List[tuple]] = {d: [] for d in depths}
    per_problem = []
    t0 = time.time()
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {
            ex.submit(measure_one, p, args.n_given, depths, corpus,
                      args.server_url, args.max_per_layer): p
            for p in problems
        }
        done = 0
        for fut in futs.as_completed(fm):
            name, results = fut.result()
            done += 1
            row = {"problem": name}
            for d in depths:
                hc, nh, fc = results[d]
                by_depth[d].append((hc, nh, fc))
                row[f"helpers_chars_d{d}"] = hc
                row[f"n_helpers_d{d}"] = nh
                row[f"file_chars_d{d}"] = fc
            per_problem.append(row)
            if done % 5 == 0 or done == len(problems):
                print(f"  [{done:3d}/{len(problems)}] {name}", flush=True)

    print(f"\nDone in {(time.time()-t0)/60:.1f} min")

    print(f"\n{'='*78}")
    print(f"Helper block size (chars):")
    print(f"  {'d':>2s}  {'mean':>7s}  {'median':>7s}  {'p10':>6s}  "
          f"{'p90':>6s}  {'min':>5s}  {'max':>6s}  {'mean_n_helpers':>14s}")
    for d in depths:
        chars = sorted(x[0] for x in by_depth[d])
        nhs = [x[1] for x in by_depth[d]]
        if not chars:
            continue
        p10 = chars[max(0, len(chars) // 10 - 1)]
        p90 = chars[min(len(chars) - 1, 9 * len(chars) // 10)]
        print(f"  {d:>2d}  {mean(chars):>7.0f}  {median(chars):>7.0f}  "
              f"{p10:>6d}  {p90:>6d}  {chars[0]:>5d}  {chars[-1]:>6d}  "
              f"{mean(nhs):>14.1f}")

    print(f"\nFull file size (chars, includes header + theorem + sorry):")
    print(f"  {'d':>2s}  {'mean':>7s}  {'median':>7s}  {'p10':>6s}  "
          f"{'p90':>6s}  {'min':>5s}  {'max':>6s}  {'growth_vs_d0':>13s}")
    base_means = mean(x[2] for x in by_depth[depths[0]])
    for d in depths:
        sizes = sorted(x[2] for x in by_depth[d])
        p10 = sizes[max(0, len(sizes) // 10 - 1)]
        p90 = sizes[min(len(sizes) - 1, 9 * len(sizes) // 10)]
        ratio = mean(sizes) / base_means
        print(f"  {d:>2d}  {mean(sizes):>7.0f}  {median(sizes):>7.0f}  "
              f"{p10:>6d}  {p90:>6d}  {sizes[0]:>5d}  {sizes[-1]:>6d}  "
              f"{ratio:>12.2f}x")

    if args.out:
        with open(args.out, "w") as f:
            for r in per_problem:
                f.write(json.dumps(r) + "\n")
        print(f"\nPer-problem records: {args.out}")


if __name__ == "__main__":
    main()
