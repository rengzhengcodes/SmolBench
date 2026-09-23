"""Score `examples/<cell>/<rung>/answer.md` files with the REPL verifier.

Twin of the pilot's LeanDojo scorer for the lean-interact backend: one REPL
session per cell, opened at step k (the prefix is replayed once), every
rung's answer tried as the proof tail from that checkpoint, identical answers
verified once. Each rung directory gets ``verdict.json``;
``<examples>/verdicts.jsonl`` collects every row; a pass/N table per rung is
printed at the end.

Re-runnable: rungs that already have ``verdict.json`` are skipped unless
``--force``.

    SMOLBENCH_LEAN_DATA=<corpus> SMOLBENCH_MATHLIB_ROOT=<built mathlib at the corpus commit> \\
      .venv/bin/python scripts/deduction/verify_examples.py --examples <abs dir> --workers 3

Each worker is a Lean process holding Mathlib; budget several GB each.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from smolbench.deduction.lean import corpus  # noqa: E402
from smolbench.deduction.lean.replbackend import ReplError  # noqa: E402
from smolbench.deduction.lean.verify import ProofResult, open_at_step, try_tail  # noqa: E402

RUNG_ORDER = [
    "stepk-2", "hint-0", "hint-1", "hint-2", "hint-3", "hint-4",
    "noise-1", "noise-2", "noise-3", "noise-4",
    "sig-0", "sig-1", "sig-2", "sig-3", "sig-4",
    "signoise-1", "signoise-2", "signoise-3", "signoise-4",
    "hoponly-1", "hoponly-2", "hoponly-3", "hoponly-4",
    "proof-0", "proof-1", "proof-2", "proof-3", "proof-4",
    "proofnoise-0", "proofnoise-1", "proofnoise-2", "proofnoise-3", "proofnoise-4",
]


_SAMPLE_RE = re.compile(r"^answer(?:\.s(\d+))?\.md$")


def _samples(rd: Path) -> list[tuple[Path, Path, int]]:
    """(answer file, verdict file, sample index) for every answer in a rung directory.

    ``answer.md`` / ``verdict.json`` is sample 0; extra independent samples are
    ``answer.s<i>.md`` / ``verdict.s<i>.json``.
    """
    out = []
    for p in sorted(rd.iterdir()):
        m = _SAMPLE_RE.match(p.name)
        if not m:
            continue
        i = int(m.group(1) or 0)
        out.append((p, rd / ("verdict.json" if i == 0 else f"verdict.s{i}.json"), i))
    return out


def _pending(cell_dir: Path, force: bool, rungs: set[str] | None) -> list[tuple[Path, Path, int]]:
    out = []
    for rd in sorted(p for p in cell_dir.iterdir() if p.is_dir()):
        if rungs and rd.name not in rungs:
            continue
        for ans_path, ver_path, i in _samples(rd):
            if ver_path.exists() and not force:
                continue
            out.append((ans_path, ver_path, i))
    return out


def _write_verdict(ver_path: Path, sample: int, answer: str, result: ProofResult, ms: int) -> dict:
    rd = ver_path.parent
    row = {
        "cell": rd.parent.name,
        "rung": rd.name,
        "sample": sample,
        "verdict": result.verdict,
        "error": (result.error or "")[:2000] or None,
        "final_state_pp": result.final_state_pp,
        "verify_ms": ms,
        "answer_sha1": hashlib.sha1(answer.encode()).hexdigest(),
        "answer_lines": len(answer.strip().splitlines()),
    }
    ver_path.write_text(json.dumps(row, indent=2, ensure_ascii=False))
    return row


def verify_cell(
    thm: corpus.BenchmarkTheorem, k: int, pending: list[tuple[Path, Path, int]], timeout: int
) -> tuple[list[dict], str | None]:
    """Verify every pending answer of one cell from a single checkpoint."""
    answers = [(ver, i, ans.read_text()) for ans, ver, i in pending]
    rows: list[dict] = []
    try:
        with open_at_step(thm, k, timeout=timeout) as (ckpt, state_at_k):
            cache: dict[str, tuple[ProofResult, int]] = {}
            for ver, i, ans in answers:
                key = ans.strip()
                if key not in cache:
                    t0 = time.monotonic()
                    try:
                        res = try_tail(ckpt, state_at_k, ans, thm.full_name)
                    except ReplError as exc:  # infrastructure: recorded, never a Lean verdict
                        res = ProofResult(thm.full_name, "exception", ans, error=f"{type(exc).__name__}: {exc}")
                    cache[key] = (res, int((time.monotonic() - t0) * 1000))
                res, ms = cache[key]
                rows.append(_write_verdict(ver, i, ans, res, ms))
        return rows, None
    except Exception as exc:  # noqa: BLE001 -- the checkpoint itself failed
        msg = f"{type(exc).__name__}: {exc}"
        verdict = "replay_failed" if "prefix tactic" in str(exc) else "exception"
        for ver, i, ans in answers:
            rows.append(_write_verdict(ver, i, ans, ProofResult(thm.full_name, verdict, ans, error=msg), 0))
        return rows, msg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--examples", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--rungs", nargs="*", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--kind", default="random")
    ap.add_argument("--split", default="val")
    args = ap.parse_args(argv)

    root = args.examples.resolve()
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

    print(f"verify: {sum(len(j[3]) for j in jobs)} answers across {len(jobs)} cells, {args.workers} workers", flush=True)
    lock = threading.Lock()
    all_rows: list[dict] = []
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(verify_cell, t, k, p, args.timeout): c for c, t, k, p in jobs}
        for fut in as_completed(futs):
            cell_dir = futs[fut]
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

    print_tables(root)
    return 0


def print_tables(root: Path) -> None:
    """Per-rung pass/N over every sample, plus pass@k where rungs have extra samples."""
    tally: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    by_prompt: dict[tuple[str, str], list[bool]] = collections.defaultdict(list)
    for vp in root.glob("*/*/verdict*.json"):
        r = json.loads(vp.read_text())
        tally[r["rung"]][r["verdict"]] += 1
        by_prompt[(r["cell"], r["rung"])].append(r["verdict"] == "success")
    order = RUNG_ORDER + sorted(set(tally) - set(RUNG_ORDER))
    print(f"\n{'rung':13s} {'pass/N':>9s} {'rate':>6s}  lerr incp gvup tmout exc rplf   (every sample)")
    for rung in order:
        c = tally.get(rung)
        if not c:
            continue
        n = sum(c.values())
        s = c["success"]
        print(f"{rung:13s} {s:4d}/{n:<4d} {100*s/n:5.1f}%  {c['lean_error']:4d} {c['incomplete']:4d} "
              f"{c['given_up']:4d} {c['timeout']:5d} {c['exception']:3d} {c['replay_failed']:4d}")
    multi = {k: v for k, v in by_prompt.items() if len(v) > 1}
    if not multi:
        return
    print(f"\n{'rung':13s} {'prompts':>7s} {'k':>3s} {'mean pass@1':>11s} {'pass@k':>7s}   (prompts with >1 sample)")
    for rung in order:
        ps = {k: v for k, v in multi.items() if k[1] == rung}
        if not ps:
            continue
        ks = sorted({len(v) for v in ps.values()})
        k_s = str(ks[0]) if len(ks) == 1 else f"{ks[0]}-{ks[-1]}"
        p1 = sum(sum(v) / len(v) for v in ps.values()) / len(ps)
        pk = sum(any(v) for v in ps.values())
        print(f"{rung:13s} {len(ps):7d} {k_s:>3s} {100*p1:10.1f}% {pk:3d}/{len(ps):<3d}")


if __name__ == "__main__":
    raise SystemExit(main())
