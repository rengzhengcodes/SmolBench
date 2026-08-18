#!/usr/bin/env python
"""Additive recovery of the 151 DojoInit ``std`` cells per deduction lane.

Background (notebooks/DEDUCTION_COVERAGE_DIAGNOSIS_2026-08-16.md + the
2026-08-18 diagnosis): 151 cells/lane (45 theorems, byte-identical across all
21 lanes, 100% ``.lake/packages/std/``) were graded ``replay_failed`` with
``DojoInitError: Cannot find the *.ast.json file`` because the grading box's
LeanDojo traced cache (under ``/root/.cache``) lacked the std build tree.
Today's local cache verifies them: 45/45 sanity replays succeed, and a
micro-proof recovered real verdicts (6/6 Mathlib control cells reproduce
their recorded verdicts exactly across both grading waves).

ADDITIVE CONTRACT -- the load-bearing property of this tool:
  * The study's ``scaling_*`` S3 prefixes are READ-ONLY here. Nothing is ever
    overwritten, deleted, or written under them; the results bucket stays an
    append-only experiment log (standing user directive).
  * Recovered verdicts are NEW rows: the original row's fields verbatim plus
    ``recovered_*`` fields appended, written to
    ``notebooks/deduction/results/dojoinit_recovery_2026-08-18/<lane>/`` and
    uploaded ONLY under ``deduction/runs/dojoinit_recovery_2026-08-18/``
    (guarded by an assertion in :func:`s3_put`).
  * The study headline (Mathlib-only) is closed; joining these rows is a
    SCOPE EXTENSION performed by ``--stage report`` and the addendum doc.

Stages (run under ``.venv-lean`` with ``~/.elan/bin`` on PATH):
  gate      lake-on-PATH + 45/45 sanity content gate (``--sanity-json``).
  controls  re-verify ~30 Mathlib control cells across 5 lanes spanning both
            grading waves; EXACT agreement with recorded verdicts required.
  recover   one lane (``--lane``) or all 21 (``--all``, 2 lanes in parallel):
            re-verify the 151 std rows, write/upload recovered_rows.jsonl.
  report    join recovered + study rows: per-lane extended-scope table +
            cross-lane identity assertions; writes report.json.

Verification code paths are ``scripts/lean_verify_rows.py``'s own
(``group_unverified`` / ``_lookup_theorem`` / ``unique_candidates`` /
``fan_out_verdict`` + the verifier's ``open_at_step``/``try_tail``), so a
recovered verdict is produced by exactly the machinery that graded the 712.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import logging
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

RECOVERY_NAME = "dojoinit_recovery_2026-08-18"
RECOVERY_SOURCE = "dojoinit-recovery-2026-08-18"
S3_BUCKET = "smolbench-results-414266451290"
S3_RUNS_PREFIX = "deduction/runs"
#: The ONLY key prefix this tool may PUT under (see :func:`s3_put`).
RECOVERY_S3_PREFIX = f"{S3_RUNS_PREFIX}/{RECOVERY_NAME}/"
LOCAL_ROOT = REPO / "notebooks" / "deduction" / "results" / RECOVERY_NAME
STD_PREFIX = ".lake/packages/std/"
STD_ROWS_PER_LANE = 151
STD_GROUPS_PER_LANE = 45
LOCK_FILE = Path.home() / ".cache" / "lean_dojo" / ".smolbench_verify.lock"

LANES: List[str] = [
    "qwen3.5-27b", "qwen3.5-122b-a10b", "qwen3.5-397b-a17b",
    "nemotron-3-nano-4b", "nemotron-3-nano-30b-a3b", "nemotron-3-super-120b-a12b",
    "gemma-4-e2b", "gemma-4-12b", "gemma-4-31b",
    "glm-4.7-flash", "glm-4.5-air", "glm-4.7",
    "ministral-3-3b", "ministral-3-8b", "ministral-3-14b",
    "exaone-4.0-32b", "exaone-4.5-33b", "k-exaone-236b-a23b",
    "deepseek-v4-flash", "deepseek-v3.1", "deepseek-v4-pro",
]
#: Lanes re-verified in the 2026-08-16 grading wave (the six re-collected
#: lanes, per the coverage diagnosis); the other 15 were graded 2026-08-14.
WAVE_0816 = {"nemotron-3-nano-4b", "deepseek-v3.1", "exaone-4.5-33b",
             "gemma-4-31b", "ministral-3-3b", "qwen3.5-27b"}
#: 3 lanes from the 08-14 wave + 2 from the 08-16 wave, fixed deterministically.
CONTROL_LANES = ["gemma-4-e2b", "glm-4.5-air", "ministral-3-8b",
                 "qwen3.5-27b", "nemotron-3-nano-4b"]
CONTROL_VERDICTS = ("success", "lean_error", "incomplete")
MEASURABLE_VERDICTS = frozenset(CONTROL_VERDICTS)

log = logging.getLogger("recover_dojoinit")


# ---------------------------------------------------------------------------
# lean_verify_rows is imported lazily: the gate/report/S3 plumbing must work
# (and the module must import) in environments without lean_dojo (.venv).
_LVR = None


def lvr():
    global _LVR
    if _LVR is None:
        spec = importlib.util.spec_from_file_location(
            "lvr", REPO / "scripts" / "lean_verify_rows.py")
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        _LVR = mod
    return _LVR


# ---------------------------------------------------------------------------
# S3 plumbing (aws CLI subprocess: creds from the ambient chain, streaming)
def s3_stream_rows(lane: str) -> Iterator[Dict[str, Any]]:
    """Yields the lane's study ``verified_rows.jsonl`` rows, read-only."""
    uri = f"s3://{S3_BUCKET}/{S3_RUNS_PREFIX}/scaling_{lane}/verified_rows.jsonl"
    proc = subprocess.Popen(["aws", "s3", "cp", uri, "-"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.strip()
        if line:
            yield json.loads(line)
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"s3 read failed for {uri}: {proc.stderr.read()[:500]}")


def s3_put(local: Path, key: str) -> None:
    """Uploads `local` to the recovery prefix -- and ONLY the recovery prefix.

    The assertion below is the additive-contract guard: this tool must be
    physically incapable of writing anywhere else in the results bucket.
    """
    assert key.startswith(RECOVERY_S3_PREFIX), (
        f"ADDITIVE-CONTRACT VIOLATION: refusing to PUT s3 key {key!r}; only "
        f"{RECOVERY_S3_PREFIX!r} is writable by this tool")
    subprocess.run(["aws", "s3", "cp", str(local), f"s3://{S3_BUCKET}/{key}"],
                   check=True, capture_output=True)


# ---------------------------------------------------------------------------
# Golden std key set
def load_std45() -> List[Dict[str, Any]]:
    p = LOCAL_ROOT / "inputs" / "std_45.json"
    if not p.exists():
        sys.exit(f"missing {p} -- copy the diagnosis std_45.json there first")
    return json.loads(p.read_text())


def golden_std_keys(std45: List[Dict[str, Any]]) -> set:
    """The (theorem_id, k) group set every lane's 151 std rows must span."""
    return {(t["theorem_id"], k) for t in std45 for k in t["ks"]}


# ---------------------------------------------------------------------------
# Shared verification core (the prototype's loop, factored)
def verify_rows_in_place(rows: List[Dict[str, Any]]) -> None:
    """Re-verifies `rows` (their ``verdict`` pre-set to ``"unverified"``).

    Writes the fresh verdict/error/final_state_pp/verify_ms back onto each
    row via ``fan_out_verdict`` -- exactly the prototype's logic: one Dojo
    session per (theorem_id, k) group, candidate-text dedup inside it, and
    the ``prefix tactic ... -> ProofFinished`` RuntimeError captured as the
    F8-class ``replay_failed`` reason.
    """
    L = lvr()
    groups = L.group_unverified(rows)
    verifier = L._default_verifier()
    for (theorem_id, k), indices in groups.items():
        t_group = time.monotonic()
        try:
            bt = L._lookup_theorem(theorem_id)
        except Exception as exc:  # noqa: BLE001
            L.fan_out_verdict(rows, indices, {
                "verdict": "replay_failed", "lean_error": f"lookup: {exc}",
                "final_state_pp": None, "verify_ms": 0})
            continue
        try:
            with verifier.open_at_step(bt, k) as (dojo, state_at_k):
                for cand, idx in L.unique_candidates(rows, indices).items():
                    t0 = time.monotonic()
                    try:
                        res = verifier.try_tail(dojo, state_at_k, cand, theorem_id)
                        payload = {"verdict": res.verdict, "lean_error": res.error,
                                   "final_state_pp": res.final_state_pp,
                                   "verify_ms": int((time.monotonic() - t0) * 1000)}
                    except Exception as exc:  # noqa: BLE001
                        payload = {"verdict": "exception",
                                   "lean_error": f"{type(exc).__name__}: {exc}",
                                   "final_state_pp": None,
                                   "verify_ms": int((time.monotonic() - t0) * 1000)}
                    L.fan_out_verdict(rows, idx, payload)
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            if isinstance(exc, RuntimeError) and message.startswith("prefix tactic "):
                lean_error = f"{type(exc).__name__}: {exc}"
            else:
                lean_error = L.dojo_failure_hint(exc)
            L.fan_out_verdict(rows, indices, {
                "verdict": "replay_failed", "lean_error": lean_error,
                "final_state_pp": None, "verify_ms": 0})
        log.info("group %s k=%d done in %.1fs", theorem_id, k,
                 time.monotonic() - t_group)


def take_lock():
    """Advisory exclusive lock against a concurrent lean_verify_rows sweep.

    Children spawned by ``--all`` inherit the parent's lock via the
    RECOVERY_HAS_LOCK env instead of contending for it.
    """
    if os.environ.get("RECOVERY_HAS_LOCK") == "1":
        return None
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    fh = LOCK_FILE.open("w")
    fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return fh


def require_lake():
    if shutil.which("lake") is None:
        sys.exit("FATAL: `lake` is not on PATH. The known trap: elan lives at "
                 "~/.elan/bin (or /root/.elan/bin) and non-login shells miss it "
                 "-- run with PATH=$HOME/.elan/bin:$PATH (README trap #1; this "
                 "silently produced 160 bogus replay_failed groups on 2026-08-16).")


# ---------------------------------------------------------------------------
# Stages
def stage_gate(args) -> None:
    require_lake()
    sanity = json.loads(Path(args.sanity_json).read_text())
    assert len(sanity) == STD_GROUPS_PER_LANE, f"sanity has {len(sanity)} entries, want 45"
    bad = [s for s in sanity if s["verdict"] != "success"
           or "DojoInit" in str(s.get("error") or "")]
    if bad:
        sys.exit(f"CONTENT GATE FAILED: {len(bad)} sanity replays not clean: "
                 + json.dumps(bad[:5]))
    std45 = load_std45()
    assert sum(t["n_cells"] for t in std45) == STD_ROWS_PER_LANE
    assert len(golden_std_keys(std45)) == STD_GROUPS_PER_LANE
    print(f"GATE OK: lake on PATH; 45/45 sanity success, zero DojoInit; "
          f"golden set {STD_GROUPS_PER_LANE} groups / {STD_ROWS_PER_LANE} cells")


def stage_controls(args) -> None:
    require_lake()
    lock = take_lock()  # noqa: F841 -- held for the stage's lifetime
    rng = random.Random(0)
    picked: List[Dict[str, Any]] = []
    for lane in CONTROL_LANES:
        by_verdict: Dict[str, List[Dict[str, Any]]] = {v: [] for v in CONTROL_VERDICTS}
        for row in s3_stream_rows(lane):
            if (not row["file_path"].startswith(STD_PREFIX)
                    and row.get("verdict") in by_verdict):
                by_verdict[row["verdict"]].append(row)
        for verdict in CONTROL_VERDICTS:
            pool = sorted(by_verdict[verdict],
                          key=lambda r: (r["theorem_id"], r["k"], r["rung"]))
            for row in rng.sample(pool, min(2, len(pool))):
                row["_lane"] = lane
                picked.append(row)
    recorded = [{"lane": r["_lane"], "theorem_id": r["theorem_id"], "k": r["k"],
                 "rung": r["rung"], "recorded": r["verdict"]} for r in picked]
    for r in picked:
        r["verdict"] = "unverified"
    verify_rows_in_place(picked)
    diffs = [dict(rec, new=row["verdict"])
             for rec, row in zip(recorded, picked) if rec["recorded"] != row["verdict"]]
    report = {"n_controls": len(picked), "lanes": CONTROL_LANES,
              "waves": {"0814": [l for l in CONTROL_LANES if l not in WAVE_0816],
                        "0816": [l for l in CONTROL_LANES if l in WAVE_0816]},
              "agreement": len(picked) - len(diffs), "disagreements": diffs,
              "results": [dict(rec, new=row["verdict"])
                          for rec, row in zip(recorded, picked)]}
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    (LOCAL_ROOT / "controls_report.json").write_text(json.dumps(report, indent=1))
    if diffs:
        print(json.dumps(diffs, indent=1))
        sys.exit(f"CONTROL GATE FAILED: {len(diffs)}/{len(picked)} disagree -- "
                 "a recovery would be a regrade; stopping (not authorized).")
    print(f"CONTROLS OK: {len(picked)}/{len(picked)} exact verdict agreement "
          f"across {len(CONTROL_LANES)} lanes / both grading waves")


def recover_lane(lane: str, force: bool = False) -> Dict[str, Any]:
    out_dir = LOCAL_ROOT / lane
    out_file = out_dir / "recovered_rows.jsonl"
    if out_file.exists() and not force:
        rows = [json.loads(x) for x in out_file.read_text().splitlines() if x]
        if len(rows) == STD_ROWS_PER_LANE:
            log.info("%s: already recovered (%d rows), skipping", lane, len(rows))
            return {"lane": lane, "skipped": True}
    require_lake()
    std45 = load_std45()
    golden = golden_std_keys(std45)
    originals = [r for r in s3_stream_rows(lane)
                 if r["file_path"].startswith(STD_PREFIX)]
    assert len(originals) == STD_ROWS_PER_LANE, (
        f"{lane}: expected {STD_ROWS_PER_LANE} std rows, found {len(originals)}")
    got_keys = {(r["theorem_id"], r["k"]) for r in originals}
    assert got_keys == golden, (
        f"{lane}: std (theorem,k) set diverges from golden: "
        f"missing={sorted(golden - got_keys)[:3]} extra={sorted(got_keys - golden)[:3]}")
    work = [dict(r, verdict="unverified") for r in originals]
    t0 = time.monotonic()
    verify_rows_in_place(work)
    elapsed = time.monotonic() - t0
    out_dir.mkdir(parents=True, exist_ok=True)
    with out_file.open("w") as fh:
        for orig, w in zip(originals, work):
            rec = dict(orig)
            rec.update({
                "recovered_verdict": w["verdict"],
                "recovered_error": w.get("lean_error"),
                "recovered_final_state_pp": w.get("final_state_pp"),
                "recovered_verify_ms": w.get("verify_ms"),
                "recovery_source": RECOVERY_SOURCE,
            })
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    s3_put(out_file, f"{RECOVERY_S3_PREFIX}{lane}/recovered_rows.jsonl")
    dist: Dict[str, int] = {}
    for w in work:
        dist[w["verdict"]] = dist.get(w["verdict"], 0) + 1
    log.info("%s: recovered in %.1f min; verdicts %s", lane, elapsed / 60, dist)
    return {"lane": lane, "seconds": round(elapsed, 1), "verdicts": dist}


def stage_recover(args) -> None:
    if args.lane:
        lock = take_lock()  # noqa: F841
        print(json.dumps(recover_lane(args.lane, force=args.force)))
        return
    # --all: parent holds the lock; 2 self-invocations at a time.
    assert args.all, "recover needs --lane <key> or --all"
    avail_kb = int(next(l for l in Path("/proc/meminfo").read_text().splitlines()
                        if l.startswith("MemAvailable")).split()[1])
    workers = min(args.workers, 3)
    assert avail_kb >= workers * 6 * 1024 * 1024, (
        f"RAM refusal: {avail_kb/1e6:.1f} GB available < {workers}x6 GB")
    lock = take_lock()  # noqa: F841
    env = dict(os.environ, RECOVERY_HAS_LOCK="1")
    pending = list(LANES)
    running: List[Tuple[str, subprocess.Popen]] = []
    failures: List[str] = []
    while pending or running:
        while pending and len(running) < workers:
            lane = pending.pop(0)
            p = subprocess.Popen(
                [sys.executable, __file__, "--stage", "recover", "--lane", lane]
                + (["--force"] if args.force else []),
                env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            running.append((lane, p))
            log.info("launched %s (%d running, %d pending)", lane, len(running), len(pending))
        time.sleep(5)
        still = []
        for lane, p in running:
            if p.poll() is None:
                still.append((lane, p))
                continue
            out = p.stdout.read() if p.stdout else ""
            if p.returncode == 0:
                log.info("%s DONE: %s", lane, out.strip().splitlines()[-1] if out.strip() else "")
            else:
                failures.append(lane)
                log.error("%s FAILED rc=%d:\n%s", lane, p.returncode, out[-2000:])
        running = still
    if failures:
        sys.exit(f"recover --all: {len(failures)} lanes failed: {failures}")
    print(f"RECOVER OK: all {len(LANES)} lanes")


def stage_report(args) -> None:
    std45 = load_std45()
    report: Dict[str, Any] = {"lanes": {}, "recovery": RECOVERY_SOURCE}
    ref_keys: Optional[set] = None
    ref_unrecovered: Optional[set] = None
    for lane in LANES:
        f = LOCAL_ROOT / lane / "recovered_rows.jsonl"
        rec_rows = [json.loads(x) for x in f.read_text().splitlines() if x]
        assert len(rec_rows) == STD_ROWS_PER_LANE, (lane, len(rec_rows))
        keys = {(r["theorem_id"], r["k"], r["rung"]) for r in rec_rows}
        unrec = {(r["theorem_id"], r["k"], r["rung"]) for r in rec_rows
                 if r["recovered_verdict"] not in MEASURABLE_VERDICTS}
        if ref_keys is None:
            ref_keys, ref_unrecovered = keys, unrec
        else:
            assert keys == ref_keys, f"{lane}: recovered key set diverges"
            assert unrec == ref_unrecovered, (
                f"{lane}: unrecoverable set diverges ({len(unrec)} vs "
                f"{len(ref_unrecovered)}) -- the F8 class must be model-independent")
        study = {"success": 0, "lean_error": 0, "incomplete": 0, "other": 0}
        for row in s3_stream_rows(lane):
            if row["file_path"].startswith(STD_PREFIX):
                continue
            v = row.get("verdict")
            study[v if v in study else "other"] = study.get(v if v in study else "other", 0) + 1
        m_study = sum(study[v] for v in MEASURABLE_VERDICTS)
        rdist: Dict[str, int] = {}
        for r in rec_rows:
            rdist[r["recovered_verdict"]] = rdist.get(r["recovered_verdict"], 0) + 1
        m_rec = sum(rdist.get(v, 0) for v in MEASURABLE_VERDICTS)
        lane_rep = {
            "study_mathlib": study, "measurable_mathlib": m_study,
            "recovered_dist": rdist, "recovered_measurable": m_rec,
            "measurable_extended": m_study + m_rec,
            "rate_mathlib": round(study["success"] / m_study, 4) if m_study else None,
            "rate_extended": round(
                (study["success"] + rdist.get("success", 0)) / (m_study + m_rec), 4)
                if (m_study + m_rec) else None,
        }
        report["lanes"][lane] = lane_rep
        print(f"{lane:28s} mathlib {lane_rep['rate_mathlib']!s:7s} "
              f"({m_study}) -> extended {lane_rep['rate_extended']!s:7s} "
              f"({lane_rep['measurable_extended']})  recovered={m_rec}")
    report["unrecovered_cells"] = sorted(ref_unrecovered or [])
    report["n_unrecovered"] = len(ref_unrecovered or [])
    (LOCAL_ROOT / "report.json").write_text(json.dumps(report, indent=1))
    print(f"\nreport.json written; unrecovered (F8/exception) cells per lane: "
          f"{len(ref_unrecovered or [])} (identical across all lanes)")


def main(argv=None):
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", required=True,
                    choices=["gate", "controls", "recover", "report"])
    ap.add_argument("--lane", help="single lane key for --stage recover")
    ap.add_argument("--all", action="store_true", help="recover all 21 lanes")
    ap.add_argument("--force", action="store_true", help="redo a finished lane")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--sanity-json",
                    default=str(LOCAL_ROOT / "inputs" / "sanity_sweep_std45.json"))
    args = ap.parse_args(argv)
    {"gate": stage_gate, "controls": stage_controls,
     "recover": stage_recover, "report": stage_report}[args.stage](args)


if __name__ == "__main__":
    main()
