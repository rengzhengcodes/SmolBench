"""Re-score a finished run offline from its stored rows.

Applies the current verdict taxonomy and tactic splitter to a run's
`all_rows.jsonl` with no model calls. Every cell row keeps its raw response,
so scoring can be redone whenever the verifier changes.

Per cell row:
  1. `exception` caused by `DojoTacticTimeoutError` -> `timeout` (model failure).
  2. `exception` caused by `DojoCrashError` -> re-verified in Lean.
  3. Any other `exception` (API transport / HTTP) -> kept; it is missing data.
  4. Candidate that splits differently under the current `_split_tactics`
     (multi-line tactics) -> re-verified in Lean.
  5. Non-success rows whose completion hit `max_tokens` -> `truncated`.

Output is a new run dir with `all_rows.jsonl` (same schema plus
`verdict_orig`, `lean_error_orig`, `rescore_reason`), `manifest.json`,
`analysis.txt`, and `rescore_report.txt`. The source run is never modified.
"""

from __future__ import annotations

import json
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .corpus import BenchmarkTheorem, iter_replay_passing, iter_with_proof
from .runner import hit_output_cap, write_run_analysis
from .verify import ProofResult, _split_tactics, open_at_step, try_tail


def _legacy_split(tail: str) -> list[str]:
    """The pre-fix splitter: one tactic per non-empty line."""
    return [line.strip() for line in tail.splitlines() if line.strip()]


def _load_theorems(config: dict) -> dict[str, BenchmarkTheorem]:
    spec = config.get("theorems", {})
    kind = spec.get("kind", "random")
    split = spec.get("split", "val")
    source = spec.get("source", "replay_passing")
    it = iter_replay_passing(kind, split) if source == "replay_passing" else iter_with_proof(kind, split)
    return {t.full_name: t for t in it}


def _classify(row: dict, max_tokens: int) -> str:
    """Return the action for a cell row: keep | relabel_timeout | reverify | truncate."""
    verdict = row.get("verdict")
    err = row.get("lean_error") or ""
    if verdict == "exception":
        if "DojoTacticTimeoutError" in err:
            return "relabel_timeout"
        if "DojoCrashError" in err:
            return "reverify"
        return "keep"
    cand = row.get("candidate_proof") or ""
    if _split_tactics(cand) != _legacy_split(cand):
        return "reverify"
    if verdict != "success" and hit_output_cap(
        row.get("finish_reason"), int(row.get("completion_tokens") or 0), max_tokens
    ):
        return "truncate"
    return "keep"


def _finalize(row: dict, result: ProofResult, max_tokens: int, reason: str) -> None:
    """Write a re-verification result into the row, applying truncation."""
    verdict = result.verdict
    error = result.error
    if verdict != "success" and hit_output_cap(
        row.get("finish_reason"), int(row.get("completion_tokens") or 0), max_tokens
    ):
        note = f"truncated: completion_tokens={row.get('completion_tokens')} (max_tokens={max_tokens})"
        error = f"{note}; {error}" if error else note
        verdict = "truncated"
    row["verdict"] = verdict
    row["lean_error"] = error
    row["final_state_pp"] = result.final_state_pp
    row["rescore_reason"] = reason


def rescore_run(
    run_dir: Path,
    out_dir: Path,
    *,
    workers: int = 8,
    dojo_timeout: int | None = None,
) -> Path:
    """Re-score `run_dir` into `out_dir`. Returns `out_dir`."""
    manifest = json.loads((run_dir / "manifest.json").read_text())
    config = manifest["config"]
    max_tokens = int(config.get("max_tokens", 4096))
    dojo_timeout = dojo_timeout or int(config.get("dojo_timeout", 300))

    rows: list[dict] = []
    with (run_dir / "all_rows.jsonl").open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

    actions: dict[int, str] = {}
    for i, r in enumerate(rows):
        if r.get("kind") != "cell":
            continue
        actions[i] = _classify(r, max_tokens)
        r["verdict_orig"] = r.get("verdict")
        r["lean_error_orig"] = r.get("lean_error")

    # Cheap relabels first.
    for i, action in actions.items():
        r = rows[i]
        if action == "relabel_timeout":
            r["verdict"] = "timeout"
            r["rescore_reason"] = "relabel_timeout"
        elif action == "truncate":
            note = f"truncated: completion_tokens={r.get('completion_tokens')} (max_tokens={max_tokens})"
            r["lean_error"] = f"{note}; {r['lean_error']}" if r.get("lean_error") else note
            r["verdict"] = "truncated"
            r["rescore_reason"] = "relabel_truncated"
        elif action == "keep":
            r["rescore_reason"] = "keep"

    # Lean re-verification, grouped by (theorem, k) so each checkpoint opens once.
    groups: dict[tuple[str, int], list[int]] = defaultdict(list)
    for i, action in actions.items():
        if action == "reverify":
            groups[(rows[i]["theorem_id"], int(rows[i]["k"]))].append(i)

    theorems = _load_theorems(config) if groups else {}
    print_lock = threading.Lock()
    n_groups = len(groups)
    done_groups = 0

    def _reverify_group(key: tuple[str, int]) -> tuple[int, int, str | None]:
        """Returns (n_rows, n_changed, open_error)."""
        name, k = key
        idxs = groups[key]
        thm = theorems.get(name)
        if thm is None:
            return len(idxs), 0, "theorem not found in corpus"
        n_changed = 0
        try:
            with open_at_step(thm, k, timeout=dojo_timeout) as (dojo, state_at_k):
                for i in idxs:
                    r = rows[i]
                    cand = r.get("candidate_proof") or ""
                    t0 = time.monotonic()
                    try:
                        result = try_tail(dojo, state_at_k, cand, name)
                    except Exception as exc:  # noqa: BLE001
                        result = ProofResult(name, "exception", cand, error=f"{type(exc).__name__}: {exc}")
                    r["verify_ms"] = int((time.monotonic() - t0) * 1000)
                    _finalize(r, result, max_tokens, "reverify")
                    n_changed += r["verdict"] != r["verdict_orig"]
        except Exception as exc:  # noqa: BLE001
            for i in idxs:
                rows[i]["rescore_reason"] = f"reverify_open_failed: {type(exc).__name__}"
            return len(idxs), 0, f"{type(exc).__name__}: {exc}"
        return len(idxs), n_changed, None

    if groups:
        print(f"rescore: {sum(len(v) for v in groups.values())} rows to re-verify "
              f"across {n_groups} (theorem, k) checkpoints, {workers} workers", flush=True)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_reverify_group, key): key for key in groups}
            for fut in as_completed(futs):
                key = futs[fut]
                n_rows_g, n_changed, err = fut.result()
                done_groups += 1
                with print_lock:
                    status = f"OPEN-FAIL {err}" if err else f"{n_changed}/{n_rows_g} verdicts changed"
                    print(f"  [{done_groups}/{n_groups}] {key[0][:50]:<50} k={key[1]}  {status}", flush=True)

    # Write output run dir.
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "all_rows.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    manifest["rescored_from"] = str(run_dir)
    manifest["rescored_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    write_run_analysis(out_dir)

    # Report.
    transitions: Counter = Counter()
    reasons: Counter = Counter()
    for i in actions:
        r = rows[i]
        reasons[r.get("rescore_reason", "?").split(":")[0]] += 1
        if r["verdict"] != r["verdict_orig"]:
            transitions[(r["verdict_orig"], r["verdict"])] += 1
    lines = [f"# rescore of {run_dir} -> {out_dir}", f"# {len(actions)} cell rows", ""]
    lines.append("## actions")
    for k_, v in sorted(reasons.items()):
        lines.append(f"  {k_:<24} {v:>6}")
    lines.append("")
    lines.append("## verdict transitions (orig -> new)")
    for (a, b), n in sorted(transitions.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {a:<12} -> {b:<12} {n:>6}")
    report = "\n".join(lines) + "\n"
    (out_dir / "rescore_report.txt").write_text(report)
    print(report, flush=True)
    return out_dir
