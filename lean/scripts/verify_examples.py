"""Score `examples/<cell>/<rung>/answer.md` files with the LeanDojo verifier.

One Dojo session per cell, opened at step k (the prefix is replayed once);
every rung's answer is then tried as the proof tail from that checkpoint.
Identical answers within a cell are verified once. Each rung directory gets
``verdict.json``; ``<examples>/verdicts.jsonl`` collects every row and the
run prints a pass/N table per rung.

Re-runnable: rungs that already have ``verdict.json`` are skipped unless
``--force``. Run it while answers are still being written and again later.

    PYTHONPATH=. uv run python scripts/verify_examples.py --examples <abs dir> --workers 3

Keep ``--workers`` small: each Dojo session is a Lean process with several
GB of resident memory, and this box tolerates at most about six.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from leaneval import corpus  # noqa: E402
from leaneval.verify import ProofResult, open_at_step, try_tail  # noqa: E402

RUNG_ORDER = ["stepk-2", "hint-0", "hint-1", "hint-2", "hint-3", "hint-4",
              "noise-1", "noise-2", "noise-3", "noise-4",
              "sig-0", "sig-1", "sig-2", "sig-3", "sig-4",
              "signoise-1", "signoise-2", "signoise-3", "signoise-4",
              "proof-0", "proof-1", "proof-2", "proof-3", "proof-4",
              "proofnoise-0", "proofnoise-1", "proofnoise-2", "proofnoise-3", "proofnoise-4"]


def _pending(cell_dir: Path, force: bool, rungs: set[str] | None) -> list[Path]:
    out = []
    for rd in sorted(p for p in cell_dir.iterdir() if p.is_dir()):
        if rungs and rd.name not in rungs:
            continue
        if not (rd / "answer.md").exists():
            continue
        if (rd / "verdict.json").exists() and not force:
            continue
        out.append(rd)
    return out


def _write_verdict(rd: Path, answer: str, result: ProofResult, ms: int) -> dict:
    row = {
        "cell": rd.parent.name,
        "rung": rd.name,
        "verdict": result.verdict,
        "error": (result.error or "")[:2000] or None,
        "final_state_pp": result.final_state_pp,
        "verify_ms": ms,
        "answer_sha1": hashlib.sha1(answer.encode()).hexdigest(),
        "answer_lines": len(answer.strip().splitlines()),
    }
    (rd / "verdict.json").write_text(json.dumps(row, indent=2, ensure_ascii=False))
    return row


def verify_cell(cell_dir: Path, thm: corpus.BenchmarkTheorem, k: int,
                pending: list[Path], timeout: int) -> tuple[list[dict], str | None]:
    """Verify every pending rung of one cell from a single checkpoint."""
    answers = {rd: (rd / "answer.md").read_text() for rd in pending}
    rows: list[dict] = []
    try:
        with open_at_step(thm, k, timeout=timeout) as (dojo, state_at_k):
            cache: dict[str, tuple[ProofResult, int]] = {}
            for rd, ans in answers.items():
                key = ans.strip()
                if key not in cache:
                    t0 = time.monotonic()
                    try:
                        res = try_tail(dojo, state_at_k, ans, thm.full_name)
                    except Exception as exc:  # noqa: BLE001 -- infra, recorded on the row
                        res = ProofResult(thm.full_name, "exception", ans,
                                          error=f"{type(exc).__name__}: {exc}")
                    cache[key] = (res, int((time.monotonic() - t0) * 1000))
                res, ms = cache[key]
                rows.append(_write_verdict(rd, ans, res, ms))
        return rows, None
    except Exception as exc:  # noqa: BLE001 -- the checkpoint itself failed
        msg = f"{type(exc).__name__}: {exc}"
        verdict = "replay_failed" if "prefix tactic" in str(exc) else "exception"
        for rd, ans in answers.items():
            rows.append(_write_verdict(rd, ans, ProofResult(thm.full_name, verdict, ans, error=msg), 0))
        return rows, msg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--examples", type=Path, required=True, help="absolute path to examples/")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--rungs", nargs="*", default=None, help="only these rung dirs")
    ap.add_argument("--force", action="store_true", help="re-verify rungs that have a verdict")
    ap.add_argument("--kind", default="random")
    ap.add_argument("--split", default="val")
    args = ap.parse_args(argv)

    root = args.examples.resolve()  # Dojo chdir()s into its cache; never use relative paths
    by_name = {t.full_name: t for t in corpus.load_split(args.kind, args.split)}
    rungs = set(args.rungs) if args.rungs else None

    jobs = []
    for cell_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        meta_path = cell_dir / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        pending = _pending(cell_dir, args.force, rungs)
        if not pending:
            continue
        thm = by_name.get(meta["theorem"])
        if thm is None:
            print(f"  SKIP {cell_dir.name}: theorem not in corpus", flush=True)
            continue
        jobs.append((cell_dir, thm, int(meta["k"]), pending))

    n_rungs = sum(len(j[3]) for j in jobs)
    print(f"verify: {n_rungs} answers across {len(jobs)} cells, {args.workers} workers", flush=True)
    lock = threading.Lock()
    all_rows: list[dict] = []
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(verify_cell, c, t, k, p, args.timeout): (c, p) for c, t, k, p in jobs}
        for fut in as_completed(futs):
            cell_dir, pending = futs[fut]
            rows, err = fut.result()
            with lock:
                all_rows.extend(rows)
                done += 1
                ok = sum(r["verdict"] == "success" for r in rows)
                status = f"OPEN-FAIL {err[:80]}" if err else f"{ok}/{len(rows)} success"
                print(f"  [{done}/{len(jobs)}] {cell_dir.name[:55]:<55} {status}", flush=True)

    with (root / "verdicts.jsonl").open("a") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Table over everything verified so far (this run and earlier ones).
    tally: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for vp in root.glob("*/*/verdict.json"):
        r = json.loads(vp.read_text())
        tally[r["rung"]][r["verdict"]] += 1
    print(f"\n{'rung':13s} {'pass/N':>9s} {'rate':>6s}  lerr incp gvup tmout exc rplf")
    for rung in RUNG_ORDER + sorted(set(tally) - set(RUNG_ORDER)):
        c = tally.get(rung)
        if not c:
            continue
        n = sum(c.values()); s = c["success"]
        print(f"{rung:13s} {s:4d}/{n:<4d} {100*s/n:5.1f}%  {c['lean_error']:4d} {c['incomplete']:4d} "
              f"{c['given_up']:4d} {c['timeout']:5d} {c['exception']:3d} {c['replay_failed']:4d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
