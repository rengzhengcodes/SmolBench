"""Eval loop: theorem × step k × context rung × N rollouts → per-theorem dir.

Two entry points:
  - `run_cell(...)` — yields rows for one (theorem, k, chain, level) cell.
    Opens its own Dojo session per call. Used by the `run-cell` CLI.
  - `sweep(config, run_dir)` — runs a YAML-described sweep with per-theorem
    output directories and Dojo session reuse across all rungs/models/rollouts
    sharing a (theorem, k). Used by the `run-sweep` CLI.

Output layout (`run_dir`):

    <run_dir>/
        manifest.json        config + run_id + start/finish timestamps
        all_rows.jsonl       source of truth, append-only across resumes
        analysis.txt         `analyze` output, regenerated at end of sweep
        theorems/
            <theorem_slug>/
                meta.json    full_name, file_path, k, ground_truth, premises
                prompts/
                    <rung-slug>.md      rendered prompt per rung
                outputs/
                    <rung-slug>__<model-slug>.jsonl   one row per rollout
                summary.md   human-readable rollup, regenerated at end
"""

from __future__ import annotations

import json
import random
import re
import threading
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

from .context import Chain, is_trivial_rung, render, validate as validate_rung
from .corpus import (
    BenchmarkTheorem,
    iter_replay_passing,
    iter_with_proof,
    load_split,
)
from .llm import build_client
from .llm.base import LLMClient
from .prompt import build_messages, extract_tactic_block
from .verify import open_at_step, replay_ground_truth, try_tail, verify_proof_tail


RESULTS_ROOT = Path(__file__).resolve().parent.parent / "results"


# ---------------------------------------------------------------------------
# Slugs
# ---------------------------------------------------------------------------


def slug_theorem(name: str) -> str:
    """Filesystem-safe theorem name. Most mathlib names slug to themselves."""
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)


def slug_rung(rung: str) -> str:
    """`stepk:1` -> `stepk-1`. Avoids `:` for Win/WSL safety."""
    return rung.replace(":", "-")


def slug_model(model: str) -> str:
    """Take the last `/` segment: `anthropic/claude-haiku-4.5` -> `claude-haiku-4.5`."""
    return model.rsplit("/", 1)[-1]


# ---------------------------------------------------------------------------
# Single cell — used by `run-cell`. Opens its own Dojo session.
# ---------------------------------------------------------------------------


def run_cell(
    *,
    client: LLMClient,
    model: str,
    theorem: BenchmarkTheorem,
    k: int,
    chain: Chain,
    level: int,
    n_rollouts: int,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    dojo_timeout: int = 600,
) -> Iterable[dict]:
    """Yield one result row per rollout for a single (theorem, k, chain, level) cell."""
    rendered = render(theorem, k, chain, level)
    messages = build_messages(rendered)

    for rollout_idx in range(n_rollouts):
        t0 = time.monotonic()
        rsp = client.complete(
            messages, model=model, max_tokens=max_tokens, temperature=temperature
        )
        gen_ms = int((time.monotonic() - t0) * 1000)

        candidate = extract_tactic_block(rsp.text)

        t1 = time.monotonic()
        verdict = verify_proof_tail(theorem, k, candidate, timeout=dojo_timeout)
        verify_ms = int((time.monotonic() - t1) * 1000)

        ground_truth_remaining = "\n".join(
            tt.tactic for tt in theorem.traced_tactics[k:]
        )

        yield {
            "kind": "cell",
            "theorem_id": theorem.full_name,
            "file_path": theorem.file_path,
            "k": k,
            "n_total_tactics": len(theorem.traced_tactics),
            "chain": chain,
            "level": level,
            "rung": rendered.label,
            "rollout_idx": rollout_idx,
            "model": rsp.model or model,
            "provider": client.name,
            "temperature": temperature,
            "prompt_tokens": rsp.prompt_tokens,
            "completion_tokens": rsp.completion_tokens,
            "cache_read_tokens": rsp.cache_read_tokens,
            "cache_creation_tokens": rsp.cache_creation_tokens,
            "context_chars": len(rendered.text),
            "gen_ms": gen_ms,
            "verify_ms": verify_ms,
            "candidate_proof": candidate,
            "raw_response": rsp.text,
            "reasoning_content": rsp.reasoning,
            "verdict": verdict.verdict,
            "lean_error": verdict.error,
            "final_state_pp": verdict.final_state_pp,
            "ground_truth_remaining": ground_truth_remaining,
        }


# ---------------------------------------------------------------------------
# Sweep — multi-cell loop with per-theorem dirs and shared Dojo sessions.
# ---------------------------------------------------------------------------


def write_jsonl(rows: Iterable[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            n += 1
    return n


def new_run_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]


def _select_theorems(spec: dict) -> list[BenchmarkTheorem]:
    """Resolve a config `theorems` block into a concrete BenchmarkTheorem list."""
    source = spec.get("source", "replay_passing")
    kind = spec.get("kind", "random")
    split = spec.get("split", "val")
    max_tactics = int(spec.get("max_tactics", 0))
    limit = int(spec.get("limit", 0))
    seed = int(spec.get("seed", 0))

    if source == "replay_passing":
        pool = list(iter_replay_passing(kind, split))
    elif source == "with_proof":
        pool = list(iter_with_proof(kind, split))
    elif source == "explicit":
        names = set(spec["full_names"])
        pool = [t for t in load_split(kind, split) if t.full_name in names]
    else:
        raise ValueError(f"unknown theorems.source: {source!r}")

    if max_tactics > 0:
        pool = [t for t in pool if 1 <= len(t.traced_tactics) <= max_tactics]

    if limit > 0 and len(pool) > limit:
        rng = random.Random(seed)
        pool = rng.sample(pool, limit)

    return pool


def _k_indices(theorem: BenchmarkTheorem, strategy: str) -> list[int]:
    n = len(theorem.traced_tactics)
    if strategy == "last":
        return [n - 1]
    if strategy == "first":
        return [0]
    if strategy == "all":
        return list(range(n))
    raise ValueError(f"unknown k.strategy: {strategy!r}")


def _row_key(model: str, theorem: str, k: int, rung: str, rollout_idx: int) -> tuple:
    return (model, theorem, k, rung, rollout_idx)


def _existing_keys(jsonl_path: Path) -> set[tuple]:
    """Read existing JSONL rows; return cell keys for cells we should NOT re-run.

    Skips rows whose verdict was `exception` — those are typically transient
    API errors (rate limits, network) and should be retried on resume rather
    than treated as final answers.
    """
    keys: set[tuple] = set()
    if not jsonl_path.exists():
        return keys
    with jsonl_path.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("kind") != "cell":
                continue
            if r.get("verdict") == "exception":
                continue  # let retries re-run transient API failures
            keys.add(_row_key(
                r.get("model", ""), r.get("theorem_id", ""),
                int(r.get("k", -1)), r.get("rung", ""),
                int(r.get("rollout_idx", -1)),
            ))
    return keys


def _sanity_done(jsonl_path: Path) -> set[str]:
    """Names of theorems whose sanity-gate row is already in the JSONL."""
    if not jsonl_path.exists():
        return set()
    done: set[str] = set()
    with jsonl_path.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("kind") == "sanity":
                done.add(r.get("theorem_id", ""))
    return done


# ---------------------------------------------------------------------------
# Per-theorem directory writers
# ---------------------------------------------------------------------------


def _theorem_dir(run_dir: Path, theorem: BenchmarkTheorem) -> Path:
    return run_dir / "theorems" / slug_theorem(theorem.full_name)


def _write_meta(theorem: BenchmarkTheorem, k: int, theorem_dir: Path) -> None:
    """Write meta.json (idempotent — overwrites)."""
    theorem_dir.mkdir(parents=True, exist_ok=True)
    tt_k = theorem.traced_tactics[k] if 0 <= k < len(theorem.traced_tactics) else None
    meta = {
        "full_name": theorem.full_name,
        "file_path": theorem.file_path,
        "url": theorem.url,
        "commit": theorem.commit,
        "n_total_tactics": len(theorem.traced_tactics),
        "k": k,
        "ground_truth_full_proof": "\n".join(tt.tactic for tt in theorem.traced_tactics),
        "ground_truth_remaining_from_k": (
            "\n".join(tt.tactic for tt in theorem.traced_tactics[k:])
        ),
        "true_premises_at_k": [
            p["full_name"] for p in tt_k.premises
        ] if tt_k else [],
        "state_before_k": tt_k.state_before if tt_k else None,
    }
    (theorem_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))


def _write_prompt(rung: str, rendered_text: str, theorem_dir: Path) -> None:
    """Write prompts/<rung-slug>.md (idempotent — overwrites)."""
    pd = theorem_dir / "prompts"
    pd.mkdir(parents=True, exist_ok=True)
    (pd / f"{slug_rung(rung)}.md").write_text(rendered_text + "\n")


def _append_output(row: dict, theorem_dir: Path) -> None:
    """Append one row to outputs/<rung>__<model>.jsonl."""
    od = theorem_dir / "outputs"
    od.mkdir(parents=True, exist_ok=True)
    fname = f"{slug_rung(row['rung'])}__{slug_model(row['model'])}.jsonl"
    with (od / fname).open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Summary generators (regenerable post-hoc)
# ---------------------------------------------------------------------------


_VERDICT_GLYPH = {
    "success": "✓",
    "lean_error": "✘",
    "incomplete": "·",
    "given_up": "?",
    "replay_failed": "!",
    "exception": "X",
}

_CHAIN_ORDER = {"stepk": 0, "hint": 1}


def _glyph(v: str) -> str:
    return _VERDICT_GLYPH.get(v, "?")


def _rung_sort_key(rung: str) -> tuple[int, int]:
    """Order rungs by chain then by level: stepk:0..2 before hint:0..4."""
    if ":" not in rung:
        return (99, 0)
    chain, lvl = rung.split(":", 1)
    try:
        n = int(lvl)
    except ValueError:
        n = 99
    return (_CHAIN_ORDER.get(chain, 99), n)


def write_theorem_summary(theorem_dir: Path) -> None:
    """Build summary.md from meta.json + outputs/*.jsonl."""
    meta_path = theorem_dir / "meta.json"
    outputs_dir = theorem_dir / "outputs"
    if not meta_path.exists() or not outputs_dir.exists():
        return
    meta = json.loads(meta_path.read_text())

    cells: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for jl in sorted(outputs_dir.glob("*.jsonl")):
        # filename: <rung-slug>__<model-slug>.jsonl
        stem = jl.stem
        if "__" not in stem:
            continue
        with jl.open() as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cells[(r["rung"], r["model"])].append(r)

    rungs = sorted({r for r, _ in cells.keys()}, key=_rung_sort_key)
    models = sorted({m for _, m in cells.keys()})

    lines: list[str] = []
    lines.append(f"# {meta['full_name']}   (k={meta['k']}, {meta['n_total_tactics']} tactics total)\n")
    lines.append(f"file: `{meta['file_path']}`  \n")
    lines.append("**Ground-truth tail (from k):**")
    lines.append("```lean\n" + (meta["ground_truth_remaining_from_k"] or "(empty)") + "\n```\n")
    if meta["true_premises_at_k"]:
        lines.append("**True premises at k:** " + ", ".join(f"`{p}`" for p in meta["true_premises_at_k"]) + "\n")
    else:
        lines.append("**True premises at k:** _(none recorded)_\n")

    # Verdict matrix
    lines.append("## Verdict matrix\n")
    header = "| rung | " + " | ".join(slug_model(m) for m in models) + " |"
    sep = "| --- |" + " --- |" * len(models)
    lines.append(header)
    lines.append(sep)
    for rung in rungs:
        row = [f"| `{rung}` "]
        for m in models:
            verdicts = [r["verdict"] for r in cells.get((rung, m), [])]
            cell_str = " ".join(_glyph(v) for v in verdicts) if verdicts else "·"
            row.append(f"| {cell_str} ")
        row.append("|")
        lines.append("".join(row))
    lines.append("")

    # Per-cell detail
    lines.append("## Per-cell detail\n")
    for rung in rungs:
        for m in models:
            for r in cells.get((rung, m), []):
                lines.append(
                    f"### `{rung}` · {slug_model(m)} · rollout {r['rollout_idx']} → "
                    f"**{r['verdict']}**  "
                    f"(gen {r.get('gen_ms', 0)/1000:.1f}s, verify {r.get('verify_ms', 0)/1000:.1f}s, "
                    f"in={r.get('prompt_tokens', 0)}, out={r.get('completion_tokens', 0)})\n"
                )
                lines.append(f"prompt: [`prompts/{slug_rung(rung)}.md`](prompts/{slug_rung(rung)}.md)\n")
                lines.append("**candidate:**")
                cand = r.get("candidate_proof", "") or "(empty)"
                lines.append("```lean\n" + cand + "\n```\n")
                if r.get("lean_error"):
                    err = r["lean_error"].splitlines()[0][:300]
                    lines.append(f"**lean_error:** {err}\n")
                if r.get("final_state_pp"):
                    pp = r["final_state_pp"].splitlines()
                    lines.append("**final state (truncated):**")
                    lines.append("```\n" + "\n".join(pp[:6]) + ("\n..." if len(pp) > 6 else "") + "\n```\n")

    (theorem_dir / "summary.md").write_text("\n".join(lines))


def write_run_analysis(run_dir: Path) -> None:
    """Read all_rows.jsonl, dump a (rung, model) pass-rate table to analysis.txt."""
    all_rows = run_dir / "all_rows.jsonl"
    if not all_rows.exists():
        return

    cells: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {
            "n": 0, "success": 0, "lean_error": 0, "incomplete": 0,
            "given_up": 0, "replay_failed": 0, "exception": 0,
            "tok_in": 0, "tok_out": 0, "ms": 0,
        }
    )
    n_sanity_pass = 0
    n_sanity_fail = 0
    n_rows = 0
    with all_rows.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = r.get("kind", "cell")
            if kind == "sanity":
                if r.get("verdict") == "success":
                    n_sanity_pass += 1
                else:
                    n_sanity_fail += 1
                continue
            n_rows += 1
            key = (r.get("rung", "?"), r.get("model", "?"))
            c = cells[key]
            c["n"] += 1
            v = r.get("verdict", "exception")
            if v in c:
                c[v] += 1
            else:
                c["exception"] += 1
            c["tok_in"] += r.get("prompt_tokens", 0)
            c["tok_out"] += r.get("completion_tokens", 0)
            c["ms"] += r.get("gen_ms", 0) + r.get("verify_ms", 0)

    out: list[str] = []
    out.append(f"# {n_rows} cells; sanity {n_sanity_pass} pass / {n_sanity_fail} fail\n")
    if n_sanity_fail:
        out.append(f"!! {n_sanity_fail} sanity-gate failures — pipeline may have rotted\n")
    if not cells:
        (run_dir / "analysis.txt").write_text("\n".join(out) + "(no cell rows)\n")
        return

    header = (
        f"{'rung':<10} {'model':<36} {'pass':>5}/{'N':<4} "
        f"{'rate':>6} {'lerr':>5} {'incp':>5} {'gvup':>5} {'rplf':>5} {'exc':>4} "
        f"{'avg_in':>7} {'avg_out':>7} {'avg_s':>6}"
    )
    out.append(header)
    out.append("-" * len(header))
    for (rung, model), c in sorted(cells.items(), key=lambda kv: (_rung_sort_key(kv[0][0]), kv[0][1])):
        n = c["n"]
        rate = c["success"] / n if n else 0
        avg_in = c["tok_in"] / n if n else 0
        avg_out = c["tok_out"] / n if n else 0
        avg_s = c["ms"] / n / 1000 if n else 0
        out.append(
            f"{rung:<10} {model:<36} {c['success']:>5}/{n:<4} "
            f"{rate:>6.1%} {c['lean_error']:>5} {c['incomplete']:>5} "
            f"{c['given_up']:>5} {c['replay_failed']:>5} {c['exception']:>4} "
            f"{avg_in:>7.0f} {avg_out:>7.0f} {avg_s:>6.1f}"
        )

    out.append("\n# per-model totals")
    by_model: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n": 0, "success": 0, "tok_in": 0, "tok_out": 0}
    )
    for (_, model), c in cells.items():
        by_model[model]["n"] += c["n"]
        by_model[model]["success"] += c["success"]
        by_model[model]["tok_in"] += c["tok_in"]
        by_model[model]["tok_out"] += c["tok_out"]
    for model, m in sorted(by_model.items()):
        rate = m["success"] / m["n"] if m["n"] else 0
        out.append(f"  {model:<36}  {m['success']:>4}/{m['n']:<4}  {rate:>6.1%}  "
                   f"({m['tok_in']:,} in / {m['tok_out']:,} out tokens)")
    (run_dir / "analysis.txt").write_text("\n".join(out) + "\n")


def regenerate_run_artifacts(run_dir: Path) -> None:
    """Rebuild analysis.txt + every theorem's summary.md from durable artifacts."""
    write_run_analysis(run_dir)
    theorems_dir = run_dir / "theorems"
    if theorems_dir.exists():
        for d in sorted(theorems_dir.iterdir()):
            if d.is_dir():
                write_theorem_summary(d)


# ---------------------------------------------------------------------------
# Inner cell loop — shares one Dojo session across all rungs/models/rollouts
# at a single (theorem, k). Caller wraps in a try/except for open failures.
# ---------------------------------------------------------------------------


def _run_cells_at_step(
    *,
    all_rows,                               # open file handle, append mode
    theorem: BenchmarkTheorem,
    k: int,
    rungs: list[str],
    rendered_by_rung: dict,
    models_cfg: list[dict],
    n_rollouts: int,
    temperature: float,
    max_tokens: int,
    client_factory,
    done_keys: set,
    tdir: Path,
    dojo_timeout: int,
    write_lock: threading.Lock | None = None,
    print_lock: threading.Lock | None = None,
) -> tuple[int, int, int]:
    """Open Dojo at (theorem, k); run all cells. Returns (n_written, n_ok, n_skipped)."""
    n_written = n_ok = n_skipped = 0
    write_lock = write_lock or threading.Lock()
    print_lock = print_lock or threading.Lock()

    with open_at_step(theorem, k, timeout=dojo_timeout) as (dojo, state_at_k):
        for rung in rungs:
            rendered = rendered_by_rung[rung]
            chain, level_str = rung.split(":", 1)
            level = int(level_str)
            messages = build_messages(rendered)

            for mc in models_cfg:
                client = client_factory(mc)
                model = mc["model"]
                display_name = mc.get("display_name", model)
                extra_params = mc.get("extra_params")
                for rollout_idx in range(n_rollouts):
                    key = _row_key(display_name, theorem.full_name, k, rung, rollout_idx)
                    if key in done_keys:
                        n_skipped += 1
                        continue

                    row = _execute_one_cell(
                        client=client, model=model, messages=messages,
                        rendered=rendered, theorem=theorem, k=k, chain=chain,
                        level=level, rung=rung, rollout_idx=rollout_idx,
                        provider=mc["provider"], temperature=temperature,
                        max_tokens=max_tokens, dojo=dojo, state_at_k=state_at_k,
                        display_name=display_name, extra_params=extra_params,
                    )

                    with write_lock:
                        all_rows.write(json.dumps(row, ensure_ascii=False) + "\n")
                        all_rows.flush()
                    _append_output(row, tdir)
                    n_written += 1
                    if row["verdict"] == "success":
                        n_ok += 1

                    with print_lock:
                        print(
                            f"  {theorem.full_name[:40]:<40}  k={k}  {rung:<8}  "
                            f"{slug_model(model):<24}  r{rollout_idx}  "
                            f"{row['verdict']:<14}  "
                            f"gen={row['gen_ms']/1000:.1f}s  ver={row['verify_ms']/1000:.1f}s",
                            flush=True,
                        )
    return n_written, n_ok, n_skipped


def _run_cells_at_step_concurrent(
    *,
    all_rows,
    theorem: BenchmarkTheorem,
    k: int,
    rungs: list[str],
    rendered_by_rung: dict,
    models_cfg: list[dict],
    n_rollouts: int,
    temperature: float,
    max_tokens: int,
    client_factory,
    done_keys: set,
    tdir: Path,
    dojo_timeout: int,
    max_workers: int = 12,
    write_lock: threading.Lock | None = None,
    print_lock: threading.Lock | None = None,
    model_semaphores: dict[str, threading.Semaphore] | None = None,
) -> tuple[int, int, int]:
    """Concurrent variant: fire all (rung, model, rollout) gen calls in parallel,
    then verify each on the shared Dojo session as the API responses arrive.

    Verify still serializes on the single Lean server (Dojo is single-threaded),
    but gen — the dominant cost (~1.3-3s/cell vs ~0.4s/verify) — fans out.
    """
    n_written = n_ok = n_skipped = 0
    write_lock = write_lock or threading.Lock()
    print_lock = print_lock or threading.Lock()

    # Build the work list.
    pending = []
    for rung in rungs:
        rendered = rendered_by_rung[rung]
        chain, level_str = rung.split(":", 1)
        level = int(level_str)
        messages = build_messages(rendered)
        for mc in models_cfg:
            display_name = mc.get("display_name", mc["model"])
            for rollout_idx in range(n_rollouts):
                key = _row_key(display_name, theorem.full_name, k, rung, rollout_idx)
                if key in done_keys:
                    n_skipped += 1
                    continue
                pending.append({
                    "rung": rung, "rendered": rendered,
                    "chain": chain, "level": level,
                    "messages": messages,
                    "mc": mc, "model": mc["model"], "provider": mc["provider"],
                    "rollout_idx": rollout_idx,
                    "display_name": display_name,
                    "extra_params": mc.get("extra_params"),
                })

    if not pending:
        return n_written, n_ok, n_skipped

    # Submit longest-running cells first within each theorem so the slowest
    # reasoning models start before fast non-reasoning ones queue up. Reduces
    # per-theorem wall-clock since the Dojo session stays open until the last
    # gen completes — slow gens at the front overlap with fast tail traffic.
    # Sort key (asc): (rung_order, is_non_reasoning, model_order, rollout_idx)
    rung_order = {r: i for i, r in enumerate(rungs)}
    model_order = {id(mc): i for i, mc in enumerate(models_cfg)}

    def _is_reasoning(mc: dict) -> bool:
        if "reasoning" in mc:
            return bool(mc["reasoning"])
        eff = (mc.get("extra_params") or {}).get("reasoning_effort")
        if eff == "high":
            return True
        if eff == "none":
            return False
        name = (mc.get("model") or "").lower()
        return ("thinking" in name) or ("speciale" in name)

    pending.sort(key=lambda p: (
        rung_order[p["rung"]],
        0 if _is_reasoning(p["mc"]) else 1,
        model_order[id(p["mc"])],
        p["rollout_idx"],
    ))

    # Open Dojo + submit all gens concurrently.
    with open_at_step(theorem, k, timeout=dojo_timeout) as (dojo, state_at_k):
        executor = ThreadPoolExecutor(max_workers=min(max_workers, len(pending)))
        try:
            def _gated_complete(client, sem, *args, **kwargs):
                if sem is None:
                    return client.complete(*args, **kwargs)
                with sem:
                    return client.complete(*args, **kwargs)

            future_to_pending = {}
            for p in pending:
                client = client_factory(p["mc"])
                p["t_gen_start"] = time.monotonic()
                sem = (model_semaphores or {}).get(p["display_name"])
                fut = executor.submit(
                    _gated_complete, client, sem, p["messages"],
                    model=p["model"], max_tokens=max_tokens, temperature=temperature,
                    extra_params=p["extra_params"],
                )
                future_to_pending[fut] = p

            # Verify each gen as it arrives (serial through shared Dojo).
            for fut in as_completed(future_to_pending):
                p = future_to_pending[fut]
                gen_ms = int((time.monotonic() - p["t_gen_start"]) * 1000)

                base_row = {
                    "kind": "cell",
                    "theorem_id": theorem.full_name,
                    "file_path": theorem.file_path,
                    "k": k,
                    "n_total_tactics": len(theorem.traced_tactics),
                    "chain": p["chain"], "level": p["level"], "rung": p["rung"],
                    "rollout_idx": p["rollout_idx"],
                    "model": p["display_name"],
                    "api_model": p["model"],
                    "provider": p["provider"],
                    "temperature": temperature,
                    "context_chars": len(p["rendered"].text),
                    "ground_truth_remaining": "\n".join(
                        tt.tactic for tt in theorem.traced_tactics[k:]
                    ),
                }
                try:
                    rsp = fut.result()
                except Exception as exc:  # noqa: BLE001
                    row = {
                        **base_row,
                        "prompt_tokens": 0, "completion_tokens": 0,
                        "cache_read_tokens": 0, "cache_creation_tokens": 0,
                        "gen_ms": gen_ms, "verify_ms": 0,
                        "candidate_proof": "", "raw_response": "",
                        "verdict": "exception",
                        "lean_error": f"{type(exc).__name__}: {exc}",
                        "final_state_pp": None,
                    }
                else:
                    candidate = extract_tactic_block(rsp.text)
                    t_ver = time.monotonic()
                    try:
                        verdict = try_tail(dojo, state_at_k, candidate, theorem.full_name)
                    except Exception as exc:  # noqa: BLE001
                        from .verify import ProofResult
                        verdict = ProofResult(
                            theorem.full_name, "exception", candidate,
                            error=f"{type(exc).__name__}: {exc}",
                        )
                    verify_ms = int((time.monotonic() - t_ver) * 1000)
                    row = {
                        **base_row,
                        "api_model": rsp.model or p["model"],
                        "prompt_tokens": rsp.prompt_tokens,
                        "completion_tokens": rsp.completion_tokens,
                        "cache_read_tokens": rsp.cache_read_tokens,
                        "cache_creation_tokens": rsp.cache_creation_tokens,
                        "gen_ms": gen_ms, "verify_ms": verify_ms,
                        "candidate_proof": candidate, "raw_response": rsp.text,
                        "reasoning_content": rsp.reasoning,
                        "verdict": verdict.verdict,
                        "lean_error": verdict.error,
                        "final_state_pp": verdict.final_state_pp,
                    }

                with write_lock:
                    all_rows.write(json.dumps(row, ensure_ascii=False) + "\n")
                    all_rows.flush()
                _append_output(row, tdir)
                n_written += 1
                if row["verdict"] == "success":
                    n_ok += 1

                with print_lock:
                    print(
                        f"  {theorem.full_name[:40]:<40}  k={k}  {row['rung']:<8}  "
                        f"{slug_model(row['model']):<24}  r{row['rollout_idx']}  "
                        f"{row['verdict']:<14}  "
                        f"gen={gen_ms/1000:.1f}s  ver={row['verify_ms']/1000:.1f}s",
                        flush=True,
                    )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    return n_written, n_ok, n_skipped


def _execute_one_cell(
    *,
    client: LLMClient, model: str, messages: list, rendered,
    theorem: BenchmarkTheorem, k: int, chain: str, level: int,
    rung: str, rollout_idx: int, provider: str, temperature: float,
    max_tokens: int, dojo, state_at_k,
    display_name: str | None = None,
    extra_params: dict | None = None,
) -> dict:
    """Run one (rung, model, rollout) cell and return the JSONL row dict."""
    row_model = display_name or model
    base_row = {
        "kind": "cell",
        "theorem_id": theorem.full_name,
        "file_path": theorem.file_path,
        "k": k,
        "n_total_tactics": len(theorem.traced_tactics),
        "chain": chain,
        "level": level,
        "rung": rung,
        "rollout_idx": rollout_idx,
        "model": row_model,
        "api_model": model,
        "provider": provider,
        "temperature": temperature,
        "context_chars": len(rendered.text),
        "ground_truth_remaining": "\n".join(
            tt.tactic for tt in theorem.traced_tactics[k:]
        ),
    }

    t_gen = time.monotonic()
    try:
        rsp = client.complete(
            messages, model=model, max_tokens=max_tokens, temperature=temperature,
            extra_params=extra_params,
        )
    except Exception as exc:  # noqa: BLE001
        gen_ms = int((time.monotonic() - t_gen) * 1000)
        return {
            **base_row,
            "prompt_tokens": 0, "completion_tokens": 0,
            "cache_read_tokens": 0, "cache_creation_tokens": 0,
            "gen_ms": gen_ms, "verify_ms": 0,
            "candidate_proof": "", "raw_response": "",
            "verdict": "exception",
            "lean_error": f"{type(exc).__name__}: {exc}",
            "final_state_pp": None,
        }
    gen_ms = int((time.monotonic() - t_gen) * 1000)

    candidate = extract_tactic_block(rsp.text)

    t_ver = time.monotonic()
    try:
        verdict = try_tail(dojo, state_at_k, candidate, theorem.full_name)
    except Exception as exc:  # noqa: BLE001
        from .verify import ProofResult
        verdict = ProofResult(
            theorem.full_name, "exception", candidate,
            error=f"{type(exc).__name__}: {exc}",
        )
    verify_ms = int((time.monotonic() - t_ver) * 1000)

    return {
        **base_row,
        "api_model": rsp.model or model,
        "prompt_tokens": rsp.prompt_tokens,
        "completion_tokens": rsp.completion_tokens,
        "cache_read_tokens": rsp.cache_read_tokens,
        "cache_creation_tokens": rsp.cache_creation_tokens,
        "gen_ms": gen_ms, "verify_ms": verify_ms,
        "candidate_proof": candidate, "raw_response": rsp.text,
        "reasoning_content": rsp.reasoning,
        "verdict": verdict.verdict,
        "lean_error": verdict.error,
        "final_state_pp": verdict.final_state_pp,
    }


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------


def sweep(config: dict, run_dir: Path, *, resume: bool = True) -> int:
    """Run a sweep described by `config`. Writes per-theorem dirs under `run_dir`.

    Loop ordering: theorem → k → rung → model → rollout. Resumes by skipping
    cells whose row key (model, theorem, k, rung, rollout_idx) is already in
    all_rows.jsonl. Per (theorem, k) opens ONE Dojo session shared across all
    rungs/models/rollouts that branch from it; per theorem runs ONE separate
    sanity-gate Dojo session that re-runs the full ground-truth proof.
    """
    theorems = _select_theorems(config["theorems"])
    k_strategy = config.get("k", {}).get("strategy", "last")
    rungs: list[str] = list(config.get("rungs", []))
    for r in rungs:
        if ":" not in r:
            raise ValueError(f"rung {r!r} must look like 'chain:level'")
        chain, lvl = r.split(":", 1)
        validate_rung(chain, int(lvl))  # type: ignore[arg-type]

    models_cfg = list(config["models"])
    n_rollouts = int(config.get("n_rollouts", 1))
    temperature = float(config.get("temperature", 0.7))
    max_tokens = int(config.get("max_tokens", 4096))
    dojo_timeout = int(config.get("dojo_timeout", 300))
    concurrent_gen = bool(config.get("concurrent_gen", True))
    max_concurrency = int(config.get("max_concurrency", 12))
    skip_trivial = bool(config.get("skip_trivial", True))
    theorem_workers = int(config.get("theorem_workers", 1))

    run_dir.mkdir(parents=True, exist_ok=True)
    all_rows_path = run_dir / "all_rows.jsonl"

    # Keep a `latest` symlink alongside the run dir for convenience.
    latest = run_dir.parent / "latest"
    if latest.is_symlink():
        latest.unlink()
    if not latest.exists():
        latest.symlink_to(run_dir.name)

    manifest = {
        "run_name": config.get("run_name") or run_dir.name,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "config": config,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    done_keys = _existing_keys(all_rows_path) if resume else set()
    sanity_done = _sanity_done(all_rows_path) if resume else set()
    if done_keys or sanity_done:
        print(
            f"resume: {len(done_keys)} cells + {len(sanity_done)} sanity rows in "
            f"{all_rows_path.name}",
            flush=True,
        )

    clients: dict[tuple, LLMClient] = {}
    def _client_for(mc: dict) -> LLMClient:
        key = (mc["provider"], mc.get("base_url", ""))
        if key not in clients:
            clients[key] = build_client(mc)
        return clients[key]

    # Per-model concurrency caps: any model entry with `max_concurrency: N` gets
    # a Semaphore(N) shared globally across all theorem workers. Used to throttle
    # specific models that hit upstream rate limits (e.g. qwen-instruct's 429s)
    # without slowing other models in the lineup.
    model_semaphores: dict[str, threading.Semaphore] = {}
    for mc in models_cfg:
        cap = mc.get("max_concurrency")
        if cap is not None:
            display_name = mc.get("display_name", mc["model"])
            model_semaphores[display_name] = threading.Semaphore(int(cap))
            print(f"per-model cap: {display_name} = {int(cap)}", flush=True)

    n_total_cells = sum(
        len(_k_indices(t, k_strategy)) * len(rungs) * len(models_cfg) * n_rollouts
        for t in theorems
    )
    print(
        f"sweep: {len(theorems)} theorems, {len(rungs)} rungs × "
        f"{len(models_cfg)} models × {n_rollouts} rollouts → {n_total_cells} cells",
        flush=True,
    )
    print(f"output: {run_dir}", flush=True)

    n_written = 0
    n_skipped = 0
    n_ok = 0

    print(
        f"theorem-workers: {theorem_workers}  "
        f"(concurrent_gen={concurrent_gen}, max_concurrency={max_concurrency})",
        flush=True,
    )

    with all_rows_path.open("a") as all_rows:
        write_lock = threading.Lock()
        print_lock = threading.Lock()

        def _process_one_theorem(theorem: BenchmarkTheorem) -> tuple[int, int, int]:
            """Worker function: process one theorem end-to-end (sanity + cells)."""
            n_w = n_o = n_s = 0
            tdir = _theorem_dir(run_dir, theorem)
            tdir.mkdir(parents=True, exist_ok=True)

            # ---- sanity gate per theorem (separate Dojo session) ----
            if theorem.full_name not in sanity_done:
                t0 = time.monotonic()
                sanity = replay_ground_truth(theorem, timeout=dojo_timeout)
                sanity_row = {
                    "kind": "sanity",
                    "theorem_id": theorem.full_name,
                    "verdict": sanity.verdict,
                    "tactics_applied": sanity.tactics_applied,
                    "tactics_total": sanity.tactics_total,
                    "ms": int((time.monotonic() - t0) * 1000),
                    "error": sanity.error,
                }
                with write_lock:
                    all_rows.write(json.dumps(sanity_row, ensure_ascii=False) + "\n")
                    all_rows.flush()
                if sanity.verdict != "success":
                    with print_lock:
                        print(
                            f"  SANITY-FAIL {theorem.full_name}: {sanity.verdict} "
                            f"({sanity.error or ''})  — skipping cells",
                            flush=True,
                        )
                    return n_w, n_o, n_s

            for k in _k_indices(theorem, k_strategy):
                _write_meta(theorem, k, tdir)

                effective_rungs: list[str] = []
                for rung in rungs:
                    chain, level_str = rung.split(":", 1)
                    if skip_trivial and is_trivial_rung(theorem, k, chain, int(level_str)):  # type: ignore[arg-type]
                        with print_lock:
                            print(
                                f"  trivial-skip {theorem.full_name[:40]:<40}  k={k}  {rung}",
                                flush=True,
                            )
                        continue
                    effective_rungs.append(rung)
                if not effective_rungs:
                    continue

                rendered_by_rung: dict[str, object] = {}
                for rung in effective_rungs:
                    chain, level = rung.split(":", 1)
                    rendered = render(theorem, k, chain, int(level))  # type: ignore[arg-type]
                    rendered_by_rung[rung] = rendered
                    _write_prompt(rung, rendered.text, tdir)

                try:
                    if concurrent_gen:
                        written_here, ok_here, skipped_here = _run_cells_at_step_concurrent(
                            all_rows=all_rows,
                            theorem=theorem, k=k,
                            rungs=effective_rungs, rendered_by_rung=rendered_by_rung,
                            models_cfg=models_cfg, n_rollouts=n_rollouts,
                            temperature=temperature, max_tokens=max_tokens,
                            client_factory=_client_for, done_keys=done_keys,
                            tdir=tdir, dojo_timeout=dojo_timeout,
                            max_workers=max_concurrency,
                            write_lock=write_lock, print_lock=print_lock,
                            model_semaphores=model_semaphores,
                        )
                    else:
                        written_here, ok_here, skipped_here = _run_cells_at_step(
                            all_rows=all_rows,
                            theorem=theorem, k=k,
                            rungs=effective_rungs, rendered_by_rung=rendered_by_rung,
                            models_cfg=models_cfg, n_rollouts=n_rollouts,
                            temperature=temperature, max_tokens=max_tokens,
                            client_factory=_client_for, done_keys=done_keys,
                            tdir=tdir, dojo_timeout=dojo_timeout,
                            write_lock=write_lock, print_lock=print_lock,
                        )
                except Exception as exc:  # noqa: BLE001
                    with print_lock:
                        print(
                            f"  DOJO-OPEN-FAIL {theorem.full_name} k={k}: "
                            f"{type(exc).__name__}: {exc}",
                            flush=True,
                        )
                    continue
                n_w += written_here
                n_o += ok_here
                n_s += skipped_here

            write_theorem_summary(tdir)
            return n_w, n_o, n_s

        if theorem_workers <= 1:
            for theorem in theorems:
                w, o, s = _process_one_theorem(theorem)
                n_written += w
                n_ok += o
                n_skipped += s
        else:
            with ThreadPoolExecutor(max_workers=theorem_workers) as t_executor:
                futures = [t_executor.submit(_process_one_theorem, t) for t in theorems]
                for fut in as_completed(futures):
                    try:
                        w, o, s = fut.result()
                    except Exception as exc:  # noqa: BLE001
                        with print_lock:
                            print(
                                f"  THEOREM-WORKER-FAIL {type(exc).__name__}: {exc}",
                                flush=True,
                            )
                        continue
                    n_written += w
                    n_ok += o
                    n_skipped += s

    # Finalize manifest + analysis
    manifest["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    manifest["counts"] = {"written": n_written, "skipped": n_skipped, "success": n_ok}
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    write_run_analysis(run_dir)

    print(
        f"\n{n_ok}/{n_written} success  ({n_skipped} skipped)\n"
        f"output: {run_dir}\n"
        f"analysis: {run_dir / 'analysis.txt'}",
        flush=True,
    )
    return n_written
