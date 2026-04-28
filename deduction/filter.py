"""Build the replay-passing target pool.

For each candidate full_name in the LeanDojo corpus, render the canonical
proof through `lean_file.build_lean_view` (K=0, full canonical continuation)
and submit to the local kimina-lean-server. Targets whose canonical proof
verifies cleanly enter the pool; others are logged + dropped per DESIGN.md.

Output: a JSONL log at `data/replay_pool.jsonl` containing one record per
attempted target. Each record has the verification outcome plus enough
diagnostics to triage drops.

This replaces the existing `data/replay_filter.json`, which was built against
a different toolchain and import scope.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, List, Optional

from deduction.corpus import load_corpus, load_traced_lookup
from deduction.errors import classify_messages
from deduction.kimina import KIMINA_URL_DEFAULT, is_up, verify
from deduction.lean_file import build_lean_view, replay_continuation
from deduction.targets import Target, build_target, candidate_full_names


def _record_for(t: Target, ok: bool, transport_error: Optional[str],
                messages: list, wall_ms: int) -> dict:
    classified = classify_messages(messages)
    return {
        "full_name": t.full_name,
        "file_path": t.file_path,
        "n_tactics": len(t.tactics),
        "ok": ok,
        "transport_error": transport_error,
        "wall_ms": wall_ms,
        "errors": [
            {
                "class": c.error_class.value,
                "detail": c.detail,
                "missing_identifier": c.missing_identifier,
            }
            for c in classified
        ],
        "n_messages": len(messages),
    }


def replay_one(t: Target, server_url: str, timeout: int) -> dict:
    src = build_lean_view(t, body=replay_continuation(t, K=0))
    t0 = time.perf_counter()
    res = verify(src, server_url=server_url, timeout=timeout)
    wall = int((time.perf_counter() - t0) * 1000)
    return _record_for(t, res.ok, res.transport_error, res.messages, wall)


def iter_targets(
    names: Iterable[str],
    *,
    min_tactics: int,
    max_tactics: int,
) -> Iterable[Target]:
    """Build Target objects from full_names, applying tractability filters."""
    corpus = load_corpus()
    traced = load_traced_lookup()
    for name in names:
        try:
            t = build_target(name, corpus, traced)
        except Exception as e:
            yield None  # signal: build failed; caller may want to log
            continue
        n = len(t.tactics)
        if not (min_tactics <= n <= max_tactics):
            continue
        yield t


def candidate_iter(*, min_tactics: int, max_tactics: int, limit: Optional[int],
                   seed: Optional[int] = None):
    """Stream Targets that pass the tractability filter.

    Skips term-mode proofs: LeanDojo records inner-`by` tactics from
    term-mode bodies, but those are proof fragments that don't compose
    into a tactic-mode replay. They would fail with `unknown identifier`
    or `unsolved goals` when our renderer assembles them as
    `theorem T sig := by <traced_tactics>`.

    When `seed` is given, candidates are uniformly shuffled before the
    filter pass — yielding a representative sample of Mathlib targets
    rather than the alphabetically-first prefix. The seed is logged so
    a pool can be reproduced."""
    import random
    corpus = load_corpus()
    traced = load_traced_lookup()
    names = list(candidate_full_names(corpus, traced))
    if seed is not None:
        random.Random(seed).shuffle(names)
        print(f"  candidates: {len(names)} (shuffled, seed={seed})", flush=True)
    else:
        print(f"  candidates: {len(names)} (sequential, alphabetical)", flush=True)
    n_emitted = 0
    n_skipped_term_mode = 0
    n_skipped_tactic_count = 0
    n_build_error = 0
    for name in names:
        try:
            t = build_target(name, corpus, traced)
        except Exception:
            n_build_error += 1
            continue
        if not t.is_tactic_mode:
            n_skipped_term_mode += 1
            continue
        n = len(t.tactics)
        if not (min_tactics <= n <= max_tactics):
            n_skipped_tactic_count += 1
            continue
        yield t
        n_emitted += 1
        if limit is not None and n_emitted >= limit:
            print(f"  filtered: term-mode skipped={n_skipped_term_mode}, "
                  f"tactic-count skipped={n_skipped_tactic_count}, "
                  f"build errors={n_build_error}", flush=True)
            return
    print(f"  filtered: term-mode skipped={n_skipped_term_mode}, "
          f"tactic-count skipped={n_skipped_tactic_count}, "
          f"build errors={n_build_error}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="Path to JSONL output log.")
    ap.add_argument("--limit", type=int, default=100,
                    help="Cap candidate count after tractability filter.")
    ap.add_argument("--min-tactics", type=int, default=1)
    ap.add_argument("--max-tactics", type=int, default=8)
    ap.add_argument("--seed", type=int, default=None,
                    help="If set, uniformly shuffle candidates before "
                         "filtering — gives a representative random sample "
                         "across Mathlib namespaces rather than the "
                         "alphabetically-first prefix. Logged for reproducibility.")
    ap.add_argument("--workers", type=int, default=4,
                    help="Concurrent verify requests to Kimina.")
    ap.add_argument("--server-url", default=KIMINA_URL_DEFAULT)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--names", nargs="*",
                    help="Optional: specific full_names to test, bypassing the candidate scan.")
    args = ap.parse_args()

    # Cold-start tolerant: kimina's first verify can take 30+s while it
    # loads Mathlib oleans into the REPL.
    if not is_up(args.server_url, timeout=120):
        print(f"ERROR: kimina-lean-server not reachable at {args.server_url}",
              file=sys.stderr)
        sys.exit(2)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build the candidate stream
    if args.names:
        corpus = load_corpus()
        traced = load_traced_lookup()
        targets: List[Target] = []
        for name in args.names:
            if name not in corpus:
                print(f"  skip {name}: not in corpus", file=sys.stderr)
                continue
            try:
                t = build_target(name, corpus, traced)
            except Exception as e:
                print(f"  skip {name}: build failed: {e}", file=sys.stderr)
                continue
            if not t.is_tactic_mode:
                print(f"  skip {name}: term-mode proof", file=sys.stderr)
                continue
            targets.append(t)
    else:
        targets = list(candidate_iter(
            min_tactics=args.min_tactics,
            max_tactics=args.max_tactics,
            limit=args.limit,
            seed=args.seed,
        ))

    print(f"Replay-testing {len(targets)} target(s) "
          f"(workers={args.workers}, timeout={args.timeout}s)")
    print(f"Log: {out_path}")

    n_pass = 0
    n_fail = 0
    n_done = 0
    t0 = time.time()

    with out_path.open("w") as f, ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(replay_one, t, args.server_url, args.timeout): t
                   for t in targets}
        for fut in as_completed(futures):
            rec = fut.result()
            f.write(json.dumps(rec) + "\n")
            f.flush()
            n_done += 1
            if rec["ok"]:
                n_pass += 1
            else:
                n_fail += 1
            if n_done % 10 == 0 or n_done == len(targets):
                pct = 100 * n_pass / max(n_done, 1)
                print(f"  [{n_done:4d}/{len(targets)}] pass={n_pass} fail={n_fail} "
                      f"({pct:.0f}% pass rate)", flush=True)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s. {n_pass}/{len(targets)} pass "
          f"({100 * n_pass / max(len(targets), 1):.0f}%).")


if __name__ == "__main__":
    main()
