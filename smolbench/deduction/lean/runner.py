"""Run the eval loop: theorem × step k × context rung × N replicates.

Two entry points, both used by `cli.py`: `run_cell` (one cell, own Dojo
session) and `sweep` (YAML-described sweep, one Dojo session per (theorem, k)).

Generation goes through `ChatClient.complete` on a provider module resolved by
`models[i].provider` per entry (`_provider_for`), NOT the `INFERENCE_PROVIDER`
env var, so one sweep can mix providers. Other optional config keys: `seed`
(default 1776; replicate `i` uses `seed + i`); `request_timeout` (default 1800s,
since `ChatClient`'s 120s default truncates long CoT mid-stream); `max_retries`
(default 4, so a wedged endpoint cannot spin forever inside an open Dojo
session). `SMOLBENCH_LEAN_RESULTS` overrides the output root (`results_root()`).

Output layout (`run_dir`):

    manifest.json        config + run_name + start/finish timestamps + counts
    all_rows.jsonl       source of truth, append-only across resumes
    analysis.txt         `write_run_analysis` output, regenerated at end of sweep
    theorems/<theorem_slug>/
        meta.json        full_name, file_path, k, ground_truth, premises
        prompts/<rung-slug>.md                    rendered prompt per rung
        outputs/<rung-slug>__<model-slug>.jsonl   one row per replicate
        summary.md       human-readable rollup, regenerated at end
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import re
import threading
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

import smolbench
from smolbench.evals.provider import provider_module

from . import lean3
from .context import Chain, is_trivial_rung, render, validate as validate_rung
from .corpus import (
    BenchmarkTheorem,
    iter_replay_passing,
    iter_with_proof,
    load_split,
)
from .prompt import SYSTEM, build_user_prompt, extract_tactic_block

# Design: `lean3` is imported at module top (unlike `.verify` below)
# because it needs only the stdlib plus `.corpus` -- no lean_dojo/torch/
# datasets -- and `write_run_analysis` uses it unconditionally for the `l3`
# column, so there is no lazy-import seam to preserve.

# Design: NO top-level `from .verify import ...`. `.verify` imports
# `lean_dojo`, which is not always installed; `_default_verifier` below is
# the lazy seam that resolves those names at call time.


def results_root() -> Path:
    """Root directory for sweep/run-cell output; may not exist yet (writers create it).

    ``SMOLBENCH_LEAN_RESULTS`` if set, else ``notebooks/deduction/results``
    anchored to the installed ``smolbench`` package, never cwd (mirrors
    `corpus.data_root`). The env var is read at CALL time.
    """
    override = os.getenv("SMOLBENCH_LEAN_RESULTS")
    if override:
        return Path(override)
    return Path(smolbench.__file__).resolve().parents[1] / "notebooks" / "deduction" / "results"


def _default_verifier():
    """Import `.verify` at call time and return it; raises `ImportError` without `lean_dojo`.

    The verifier protocol is `open_at_step`, `try_tail`, `replay_ground_truth`,
    `verify_proof_tail`, `ProofResult`. The lazy import keeps `runner` usable
    without `lean_dojo`; such callers pass a verifier explicitly (the tests'
    `FakeVerifier`, or `NullVerifier` for generation-only sweeps).
    """
    from smolbench.deduction.lean import verify
    return verify


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
    provider: str,
    model: str,
    theorem: BenchmarkTheorem,
    k: int,
    chain: Chain,
    level: int,
    n_replicates: int,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    dojo_timeout: int = 600,
    seed: int = 1776,
    request_timeout: int = 1800,
    max_retries: int = 4,
    verifier=None,
) -> Iterable[dict]:
    """Yield one JSONL-serializable row per replicate for one (theorem, k, chain, level) cell.

    Opens its own Dojo session. Unlike `sweep`, this wraps `complete()` in no
    try/except: it is single-shot and non-resuming, so generation failures
    propagate rather than becoming exception rows.

    Parameters
    ----------
    provider : str
        Name resolved by `smolbench.evals.provider.provider_module` (e.g.
        "primeintellect", "openrouter", "aws", "ec2").
    theorem, k, chain, level
        As in `context.render`.
    dojo_timeout : int
        Seconds for the Dojo session (prefix replay plus tail check).
    seed : int
        Base decoding seed; replicate `i` uses ``seed + i``, so the replicate
        index -- not theorem/rung/model -- is the seed-varying axis.
    verifier : optional
        Must expose `verify_proof_tail`; `None` resolves `_default_verifier()`
        (tests pass a fake to run without `lean_dojo`).

    Yields
    ------
    dict
        One row per replicate, in `_execute_one_cell`'s schema minus
        ``api_model`` (there is no separate display name here).
    """
    if verifier is None:
        verifier = _default_verifier()

    rendered = render(theorem, k, chain, level)
    user_prompt = build_user_prompt(rendered)

    mod = provider_module(provider)
    try:
        ctx_len = mod.get_model_context_length(model)
    except Exception as exc:  # noqa: BLE001
        # Same rationale as `_ctx_len_for`: a catalog lookup failure must
        # not abort the cell.
        ctx_len = 10**9
        print(f"warning: context-length lookup failed for {model} on {provider}: {exc}", flush=True)

    for replicate_idx in range(n_replicates):
        replicate_seed = seed + replicate_idx
        t0 = time.monotonic()
        # No try/except here by design (see this function's docstring);
        # `sweep` owns exception rows.
        rsp = mod.complete(
            user_prompt, model, replicate_seed,
            system=SYSTEM,
            context_length=ctx_len,
            extra_args={"temperature": temperature, "max_tokens": max_tokens},
            request_timeout=request_timeout,
            max_retries=max_retries,
        )
        gen_ms = int((time.monotonic() - t0) * 1000)

        candidate = extract_tactic_block(rsp.content)

        t1 = time.monotonic()
        verdict = verifier.verify_proof_tail(theorem, k, candidate, timeout=dojo_timeout)
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
            "replicate_idx": replicate_idx,
            "seed": replicate_seed,
            "model": rsp.model or model,
            "provider": provider,
            "temperature": temperature,
            "prompt_tokens": rsp.prompt_tokens,
            "completion_tokens": rsp.completion_tokens,
            "cache_read_tokens": rsp.cached_prompt_tokens,
            "cache_creation_tokens": 0,  # no provider reports cache-creation
            "finish_reason": rsp.finish_reason,
            "context_chars": len(rendered.text),
            "gen_ms": gen_ms,
            "verify_ms": verify_ms,
            "candidate_proof": candidate,
            "raw_response": rsp.content,
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


def _select_theorems(
    spec: dict, *, cell_whitelist: frozenset[tuple] | None = None
) -> list[BenchmarkTheorem]:
    """Resolve a config `theorems` block into a concrete BenchmarkTheorem list.

    `cell_whitelist`, when given, narrows the pool to theorems owning at least
    one of its cell keys; it is a parameter rather than a `spec` field because
    `sweep` loads it once from ``LEAN_CELL_WHITELIST``.
    """
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

    # Optional "i/n" stride shard, applied AFTER the seeded sample: every
    # shard computes the identical pool and takes a disjoint slice, so the
    # n shards' union equals the unsharded selection exactly. The boundary
    # is at the THEOREM level, keeping one theorem's rungs and its sanity
    # row on a single shard.
    shard = str(spec.get("shard", "") or "")
    if shard:
        idx_str, sep, n_str = shard.partition("/")
        try:
            idx, n = int(idx_str), int(n_str)
        except ValueError:
            idx, n = -1, 0  # falls through to the range check below
        if not sep or not (0 <= idx < n):
            raise ValueError(f"theorems.shard {shard!r} must be 'i/n' with 0 <= i < n")
        pool = pool[idx::n]

    # Optional cell-level whitelist (LEAN_CELL_WHITELIST via `sweep`),
    # applied LAST and at the THEOREM level, mirroring the shard above.
    # Dropping whole theorems here, not only per-cell in
    # `_run_cells_at_step[_concurrent]`, skips the sanity-gate replay and
    # the per-(theorem, k) Dojo session for every untouched theorem -- the
    # efficiency an n=200-cell rerun needs against a 300-theorem pool.
    if cell_whitelist is not None:
        whitelisted_theorems = {key[1] for key in cell_whitelist}
        pool = [t for t in pool if t.full_name in whitelisted_theorems]

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


def _row_key(model: str, theorem: str, k: int, rung: str, replicate_idx: int) -> tuple:
    return (model, theorem, k, rung, replicate_idx)


# ---------------------------------------------------------------------------
# Cell whitelist (LEAN_CELL_WHITELIST) -- an env-gated filter scoped to
# specific (model, theorem, k, rung, replicate_idx) cells, rather than a
# stride over the theorem pool like `theorems.shard`: regenerates an exact
# small cell sample on a fresh box without re-running the rest of a lane.
# `sweep`'s Notes say where it is consulted.
# ---------------------------------------------------------------------------


def load_cell_whitelist(path_str: str) -> frozenset[tuple]:
    """Load and validate a `LEAN_CELL_WHITELIST` JSON file into a key set.

    The file must be a JSON list of exactly-5-element arrays
    ``[model, theorem, k, rung, replicate_idx]`` — `_row_key`'s order and shape,
    so keys built here compare equal to `sweep`'s. Duplicates collapse; source
    order is not preserved.

    Raises
    ------
    ValueError
        Unreadable path, invalid JSON, non-list JSON, or a malformed entry, all
        naming `path_str`. Three exception types collapse into one class because
        a missing or malformed file must abort the sweep before it generates a
        cell, never degrade into a full, expensive re-run.
    """
    path = Path(path_str)
    try:
        raw = path.read_text()
    except OSError as exc:
        raise ValueError(
            f"LEAN_CELL_WHITELIST={path_str!r} could not be read: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LEAN_CELL_WHITELIST={path_str!r} is not valid JSON: {exc}"
        ) from exc
    if not isinstance(data, list):
        raise ValueError(
            f"LEAN_CELL_WHITELIST={path_str!r} must contain a JSON list of "
            f"[model, theorem, k, rung, replicate_idx] cell keys; got "
            f"{type(data).__name__}"
        )
    keys: set[tuple] = set()
    for i, item in enumerate(data):
        if not (isinstance(item, list) and len(item) == 5):
            raise ValueError(
                f"LEAN_CELL_WHITELIST={path_str!r} entry {i} must be a "
                f"5-element [model, theorem, k, rung, replicate_idx] list; "
                f"got {item!r}"
            )
        model, theorem, k, rung, replicate_idx = item
        keys.add(_row_key(str(model), str(theorem), int(k), str(rung), int(replicate_idx)))
    return frozenset(keys)


def hash_cell_keys(keys: Iterable[tuple]) -> str:
    """Lowercase hex SHA-256 of a canonical JSON encoding of `keys`.

    `keys` are `_row_key`-shaped or any equal-valued 5-element sequences (e.g.
    the plain lists `load_cell_whitelist` reads from disk); they are SORTED and
    coerced to lists first, so a tuple and an equal list fingerprint identically
    — the two callers build keys by different paths yet must agree. Stamps "this
    exact set of cells" into a manifest sidecar (see
    `notebooks/deduction/run_study.py`). Change-detection, not security.
    """
    canonical = json.dumps(
        sorted(list(key) for key in keys), separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _existing_keys(jsonl_path: Path) -> set[tuple]:
    """Read existing JSONL rows; return cell keys for cells that must NOT re-run.

    Decides per cell on one question: did a request for this cell ever complete
    a round trip? Only SURVIVING (non-``exception``) rows count as evidence — a
    cell whose only record is an exception re-runs even when that row carries
    proof text, since the exception may have come from the VERIFIER and left the
    proof unchecked. Among survivors: any with non-empty ``candidate_proof``
    skips the cell; else any with ``prompt_tokens > 0`` also skips it (asked,
    and returned nothing extractable — that is DATA); else nothing was ever
    measured and the cell re-runs. Re-running an asked-and-empty cell would
    resample until it happened to emit a proof, inflating pass@1.
    ``prompt_tokens`` draws that line with no tuned constant, and is the signal
    `scripts/results/audit_run_completeness.py` uses.
    """
    if not jsonl_path.exists():
        return set()
    rows_by_key: dict[tuple, list[dict]] = {}
    with jsonl_path.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("kind") != "cell":
                continue
            key = _row_key(
                r.get("model", ""), r.get("theorem_id", ""),
                int(r.get("k", -1)), r.get("rung", ""),
                int(r.get("replicate_idx", -1)),
            )
            rows_by_key.setdefault(key, []).append(r)
    keys: set[tuple] = set()
    for key, rows in rows_by_key.items():
        survived = [r for r in rows if r.get("verdict") != "exception"]
        if any((r.get("candidate_proof") or "").strip() for r in survived):
            keys.add(key)  # a surviving attempt produced a proof
        elif any(int(r.get("prompt_tokens") or 0) > 0 for r in survived):
            keys.add(key)  # asked and answered emptily: this is DATA, never resample
        # else: no attempt both reached the model and survived -- re-run this cell
    return keys


def _sanity_done(jsonl_path: Path) -> dict[str, str]:
    """Map theorem name to its recorded sanity verdict from the JSONL (last wins).

    Verdicts, not just names, so a resumed sweep can RE-APPLY the gate: a
    theorem whose ground truth failed to replay stays excluded rather than
    falling through to cell generation because its gate row exists.
    """
    if not jsonl_path.exists():
        return {}
    done: dict[str, str] = {}
    with jsonl_path.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("kind") == "sanity":
                done[r.get("theorem_id", "")] = r.get("verdict", "")
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
    # Generation-only sweeps (NullVerifier): cells awaiting the deferred
    # verification pass, and sanity replays that pass never ran.
    "unverified": "~",
    "skipped": "-",
}

_CHAIN_ORDER = {"stepk": 0, "hint": 1, "noise": 2}

# Design: the sweep's per-theorem sanity gate (`_process_one_theorem`)
# suppresses cell generation only when the replay POSITIVELY says the
# ground truth failed; any other non-success verdict passes THROUGH --
# notably "skipped", the only verdict
# `smolbench.deduction.lean.nullverify.NullVerifier` produces, since a
# generation-only sweep defers the real verification pass. Membership in
# this frozenset, rather than `!= "success"`, makes that distinction.
SANITY_FAILURE_VERDICTS: frozenset[str] = frozenset(
    {"lean_error", "incomplete", "given_up", "exception", "replay_failed"}
)


def _glyph(v: str) -> str:
    return _VERDICT_GLYPH.get(v, "?")


#: Filename marker for a RETIRED row artifact. On ``--force-rerun``,
#: ``notebooks/deduction/run_study.py`` renames a superseded
#: ``all_rows.jsonl`` to ``all_rows_SUPERSEDED-<stamp>.jsonl`` instead of
#: deleting it. Anything that globs row files must refuse them by name.
#:
#: (``notebooks/deduction/analysis/power_analysis.py`` deliberately carries
#: its own copy of this marker and of the check below: it runs under
#: ``uv run --no-project --with numpy --with scipy``, an environment with
#: no smolbench installed, so it cannot import this module.)
SUPERSEDED_MARKER = "SUPERSEDED"
#: All three retirement markers the snapshot writes for this audit-trail
#: class (``*_SUPERSEDED-*``, ``*_STALE-*``, ``*_BROKEN-*``). STALE and
#: BROKEN anchor on ``_MARKER-`` so ordinary words in basenames cannot trip
#: the guard.
RETIRED_MARKERS = (SUPERSEDED_MARKER, "_STALE-", "_BROKEN-")


def reject_superseded_rows(paths) -> None:
    """Reject any path whose FILE NAME carries a `RETIRED_MARKERS` marker.

    Raises
    ------
    ValueError
        Naming every offending path -- rather than warning and skipping, since
        these files parse perfectly and one would yield a complete, plausible,
        WRONG summary instead of a crash. Also logs, because
        `write_theorem_summary` runs inside the sweep's per-theorem worker,
        which -- under ``theorem_workers > 1`` -- swallows exceptions into
        one THEOREM-WORKER-FAIL line (serial runs propagate).
    """
    bad = [str(p) for p in paths
           if any(m in Path(p).name for m in RETIRED_MARKERS)]
    if bad:
        logging.error(
            "refusing SUPERSEDED row file(s): %s", ", ".join(bad)
        )
        raise ValueError(
            "refusing SUPERSEDED row file(s) -- these are retired artifacts "
            "kept as an audit trail (see run_study.py --force-rerun), not "
            "current data: " + ", ".join(bad)
        )


def _rung_sort_key(rung: str) -> tuple[int, int]:
    """Order rungs by chain then by level: stepk, then hint, then noise."""
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
    jsonl_files = sorted(outputs_dir.glob("*.jsonl"))
    reject_superseded_rows(jsonl_files)
    for jl in jsonl_files:
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
                    f"### `{rung}` · {slug_model(m)} · replicate {r['replicate_idx']} → "
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
    """Read all_rows.jsonl; overwrite `run_dir`'s analysis.txt with a (rung, model) table.

    Regenerates wholesale (never merges with a prior analysis.txt); a no-op when
    ``all_rows.jsonl`` does not exist. Columns per cell: pass/N, rate, verdict
    breakdown (``lerr``/``incp``/``gvup``/``rplf``/``exc``), ``l3``, then average
    prompt/completion tokens and wall time. ``l3`` counts CELLS whose
    ``candidate_proof`` holds at least one Lean 3 relic (`lean3.find_relics`),
    regardless of verdict — the endpoint `lean3.corrupt_tail`'s SFT intervention
    aims to drive to zero.

    Notes
    -----
    Name-level ``l3`` detection also needs the ``lean3_align.json.gz`` asset
    (`lean3.AlignMap.load`); without it ``l3`` degrades to parse-level syntax
    relics only, and a marker line goes after the table header so an old run is
    not mistaken for leak-free.
    """
    all_rows = run_dir / "all_rows.jsonl"
    if not all_rows.exists():
        return

    # Load once per call, not per row: `AlignMap.load` is a gzip+JSON read
    # and a sweep's `all_rows.jsonl` holds thousands of rows.
    align = lean3.AlignMap.load()

    cells: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {
            "n": 0, "success": 0, "lean_error": 0, "incomplete": 0,
            "given_up": 0, "replay_failed": 0, "exception": 0,
            "unverified": 0,
            "tok_in": 0, "tok_out": 0, "ms": 0, "l3": 0,
        }
    )
    n_sanity_pass = 0
    n_sanity_fail = 0
    n_sanity_skipped = 0
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
                elif r.get("verdict") in SANITY_FAILURE_VERDICTS:
                    n_sanity_fail += 1
                else:
                    # "skipped" (NullVerifier) and any future pass-through
                    # verdict: the gate deferred, nothing positively failed.
                    n_sanity_skipped += 1
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
            if lean3.find_relics(r.get("candidate_proof") or "", align):
                c["l3"] += 1

    out: list[str] = []
    out.append(
        f"# {n_rows} cells; sanity {n_sanity_pass} pass / {n_sanity_fail} fail"
        + (f" / {n_sanity_skipped} deferred" if n_sanity_skipped else "")
        + "\n"
    )
    if n_sanity_fail:
        out.append(f"!! {n_sanity_fail} sanity-gate failures — pipeline may have rotted\n")
    if n_sanity_skipped:
        out.append(
            f"# {n_sanity_skipped} sanity replays deferred (generation-only sweep); "
            "run the verification pass before trusting cell rates\n"
        )
    if not cells:
        (run_dir / "analysis.txt").write_text("\n".join(out) + "(no cell rows)\n")
        return

    header = (
        f"{'rung':<10} {'model':<36} {'pass':>5}/{'N':<4} "
        f"{'rate':>6} {'lerr':>5} {'incp':>5} {'gvup':>5} {'rplf':>5} {'exc':>4} {'l3':>5} "
        f"{'avg_in':>7} {'avg_out':>7} {'avg_s':>6}"
    )
    out.append(header)
    out.append("-" * len(header))
    if align is None:
        # Graceful-degrade marker (see the docstring's Notes): without the
        # align asset `l3` reflects parse-level relics only, and such a run
        # must not be mistaken for a leak-free one.
        out.append(f"# l3 = parse-level only ({lean3.ALIGN_ASSET_NAME} not built)")
    for (rung, model), c in sorted(cells.items(), key=lambda kv: (_rung_sort_key(kv[0][0]), kv[0][1])):
        n = c["n"]
        rate = c["success"] / n if n else 0
        avg_in = c["tok_in"] / n if n else 0
        avg_out = c["tok_out"] / n if n else 0
        avg_s = c["ms"] / n / 1000 if n else 0
        out.append(
            f"{rung:<10} {model:<36} {c['success']:>5}/{n:<4} "
            f"{rate:>6.1%} {c['lean_error']:>5} {c['incomplete']:>5} "
            f"{c['given_up']:>5} {c['replay_failed']:>5} {c['exception']:>4} {c['l3']:>5} "
            f"{avg_in:>7.0f} {avg_out:>7.0f} {avg_s:>6.1f}"
        )

    out.append("\n# per-model totals")
    by_model: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n": 0, "success": 0, "tok_in": 0, "tok_out": 0, "l3": 0}
    )
    for (_, model), c in cells.items():
        by_model[model]["n"] += c["n"]
        by_model[model]["success"] += c["success"]
        by_model[model]["tok_in"] += c["tok_in"]
        by_model[model]["tok_out"] += c["tok_out"]
        by_model[model]["l3"] += c["l3"]
    for model, m in sorted(by_model.items()):
        rate = m["success"] / m["n"] if m["n"] else 0
        out.append(f"  {model:<36}  {m['success']:>4}/{m['n']:<4}  {rate:>6.1%}  "
                   f"({m['tok_in']:,} in / {m['tok_out']:,} out tokens)  l3={m['l3']}")
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
# Inner cell loop — shares one Dojo session across all rungs/models/replicates
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
    n_replicates: int,
    temperature: float,
    max_tokens: int,
    provider_factory,
    base_seed: int,
    request_timeout: int,
    max_retries: int,
    done_keys: set,
    tdir: Path,
    dojo_timeout: int,
    verifier,
    write_lock: threading.Lock | None = None,
    print_lock: threading.Lock | None = None,
    cell_whitelist: frozenset[tuple] | None = None,
) -> tuple[int, int, int]:
    """Open Dojo at (theorem, k); run all cells. Returns (n_written, n_ok, n_skipped).

    `cell_whitelist=None` applies no extra filtering; otherwise a cell whose row
    key is not a member is skipped exactly like an already-`done_keys` one and
    counted in the same `n_skipped`, indistinguishably (see `sweep` and
    `load_cell_whitelist`).

    Filtering happens BEFORE `verifier.open_at_step`, and an empty pending list
    returns without opening it (as `_run_cells_at_step_concurrent` does): a
    resumed sweep whose cells are all done would otherwise pay a full Dojo
    session -- tens of seconds of Lean startup -- per (theorem, k) to do nothing.
    """
    n_written = n_ok = n_skipped = 0
    write_lock = write_lock or threading.Lock()
    print_lock = print_lock or threading.Lock()

    # Pending cells in (rung, model, replicate) order -- the order rows are
    # written and printed in. No re-sort: the concurrent variant's
    # longest-first ordering is a scheduling optimisation with no serial analogue.
    pending = []
    for rung in rungs:
        rendered = rendered_by_rung[rung]
        chain, level_str = rung.split(":", 1)
        level = int(level_str)
        user_prompt = build_user_prompt(rendered)
        for mc in models_cfg:
            display_name = mc.get("display_name", mc["model"])
            for replicate_idx in range(n_replicates):
                key = _row_key(display_name, theorem.full_name, k, rung, replicate_idx)
                if key in done_keys or (
                    cell_whitelist is not None and key not in cell_whitelist
                ):
                    n_skipped += 1
                    continue
                pending.append({
                    "rung": rung, "rendered": rendered,
                    "chain": chain, "level": level,
                    "user_prompt": user_prompt,
                    "mc": mc, "model": mc["model"], "provider": mc["provider"],
                    "replicate_idx": replicate_idx,
                    # Seed threading: the replicate index is the replication
                    # axis (see `sweep`'s docstring), so the seed depends only
                    # on replicate_idx -- keeping cross-model comparisons at a
                    # given cell seed-paired.
                    "seed": base_seed + replicate_idx,
                    "display_name": display_name,
                    "extra_params": mc.get("extra_params"),
                })

    if not pending:
        return n_written, n_ok, n_skipped

    with verifier.open_at_step(theorem, k, timeout=dojo_timeout) as (dojo, state_at_k):
        for p in pending:
            mod, ctx_len = provider_factory(p["mc"])
            row = _execute_one_cell(
                verifier=verifier,
                mod=mod, model=p["model"], ctx_len=ctx_len, user_prompt=p["user_prompt"],
                rendered=p["rendered"], theorem=theorem, k=k, chain=p["chain"],
                level=p["level"], rung=p["rung"], replicate_idx=p["replicate_idx"],
                seed=p["seed"],
                provider=p["provider"], temperature=temperature,
                max_tokens=max_tokens, request_timeout=request_timeout,
                max_retries=max_retries, dojo=dojo, state_at_k=state_at_k,
                display_name=p["display_name"], extra_params=p["extra_params"],
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
                    f"  {theorem.full_name[:40]:<40}  k={k}  {p['rung']:<8}  "
                    f"{slug_model(p['model']):<24}  r{p['replicate_idx']}  "
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
    n_replicates: int,
    temperature: float,
    max_tokens: int,
    provider_factory,
    base_seed: int,
    request_timeout: int,
    max_retries: int,
    done_keys: set,
    tdir: Path,
    dojo_timeout: int,
    verifier,
    max_workers: int = 12,
    write_lock: threading.Lock | None = None,
    print_lock: threading.Lock | None = None,
    model_semaphores: dict[str, threading.Semaphore] | None = None,
    cell_whitelist: frozenset[tuple] | None = None,
) -> tuple[int, int, int]:
    """Concurrent variant: fire all (rung, model, replicate) gen calls in parallel,
    then verify each on the shared Dojo session as the API responses arrive.

    Verify still serializes on the single Lean server, since Dojo is
    single-threaded; gen -- the dominant cost at ~1.3-3s/cell versus
    ~0.4s/verify -- fans out. `cell_whitelist` is as in `_run_cells_at_step`.
    """
    n_written = n_ok = n_skipped = 0
    write_lock = write_lock or threading.Lock()
    print_lock = print_lock or threading.Lock()

    pending = []
    for rung in rungs:
        rendered = rendered_by_rung[rung]
        chain, level_str = rung.split(":", 1)
        level = int(level_str)
        user_prompt = build_user_prompt(rendered)
        for mc in models_cfg:
            display_name = mc.get("display_name", mc["model"])
            for replicate_idx in range(n_replicates):
                key = _row_key(display_name, theorem.full_name, k, rung, replicate_idx)
                if key in done_keys or (
                    cell_whitelist is not None and key not in cell_whitelist
                ):
                    n_skipped += 1
                    continue
                pending.append({
                    "rung": rung, "rendered": rendered,
                    "chain": chain, "level": level,
                    "user_prompt": user_prompt,
                    "mc": mc, "model": mc["model"], "provider": mc["provider"],
                    "replicate_idx": replicate_idx,
                    # Seed threading: see `_run_cells_at_step`.
                    "seed": base_seed + replicate_idx,
                    "display_name": display_name,
                    "extra_params": mc.get("extra_params"),
                })

    if not pending:
        return n_written, n_ok, n_skipped

    # Submit the longest-running cells first: the Dojo session stays open
    # until the last gen completes, so front-loading slow reasoning models
    # cuts per-theorem wall-clock.
    # Sort key (asc): (rung_order, is_non_reasoning, model_order, replicate_idx)
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
        p["replicate_idx"],
    ))

    with verifier.open_at_step(theorem, k, timeout=dojo_timeout) as (dojo, state_at_k):
        executor = ThreadPoolExecutor(max_workers=min(max_workers, len(pending)))
        try:
            def _gated_complete(mod, sem, *args, **kwargs):
                if sem is None:
                    return mod.complete(*args, **kwargs)
                with sem:
                    return mod.complete(*args, **kwargs)

            future_to_pending = {}
            for p in pending:
                mod, ctx_len = provider_factory(p["mc"])
                p["t_gen_start"] = time.monotonic()
                sem = (model_semaphores or {}).get(p["display_name"])
                fut = executor.submit(
                    _gated_complete, mod, sem, p["user_prompt"], p["model"], p["seed"],
                    system=SYSTEM,
                    context_length=ctx_len,
                    extra_args={
                        "temperature": temperature, "max_tokens": max_tokens,
                        **(p["extra_params"] or {}),
                    },
                    request_timeout=request_timeout,
                    max_retries=max_retries,
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
                    "replicate_idx": p["replicate_idx"],
                    "seed": p["seed"],
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
                        # The request itself raised, so there is no
                        # server-reported stop reason; the key stays
                        # present so every cell row, success or
                        # exception, indexes row["finish_reason"] alike.
                        "finish_reason": None,
                        "gen_ms": gen_ms, "verify_ms": 0,
                        "candidate_proof": "", "raw_response": "",
                        "reasoning_content": None,
                        "verdict": "exception",
                        "lean_error": f"{type(exc).__name__}: {exc}",
                        "final_state_pp": None,
                    }
                else:
                    candidate = extract_tactic_block(rsp.content)
                    t_ver = time.monotonic()
                    try:
                        verdict = verifier.try_tail(dojo, state_at_k, candidate, theorem.full_name)
                    except Exception as exc:  # noqa: BLE001
                        verdict = verifier.ProofResult(
                            theorem.full_name, "exception", candidate,
                            error=f"{type(exc).__name__}: {exc}",
                        )
                    verify_ms = int((time.monotonic() - t_ver) * 1000)
                    row = {
                        **base_row,
                        "api_model": rsp.model,
                        "prompt_tokens": rsp.prompt_tokens,
                        "completion_tokens": rsp.completion_tokens,
                        "cache_read_tokens": rsp.cached_prompt_tokens,
                        "cache_creation_tokens": 0,  # no provider reports cache-creation
                        "finish_reason": rsp.finish_reason,
                        "gen_ms": gen_ms, "verify_ms": verify_ms,
                        "candidate_proof": candidate, "raw_response": rsp.content,
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
                        f"{slug_model(row['model']):<24}  r{row['replicate_idx']}  "
                        f"{row['verdict']:<14}  "
                        f"gen={gen_ms/1000:.1f}s  ver={row['verify_ms']/1000:.1f}s",
                        flush=True,
                    )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    return n_written, n_ok, n_skipped


def _execute_one_cell(
    *,
    verifier,
    mod, model: str, ctx_len: int, user_prompt: str, rendered,
    theorem: BenchmarkTheorem, k: int, chain: str, level: int,
    rung: str, replicate_idx: int, seed: int, provider: str, temperature: float,
    max_tokens: int, request_timeout: int, max_retries: int, dojo, state_at_k,
    display_name: str | None = None,
    extra_params: dict | None = None,
) -> dict:
    """Run one (rung, model, replicate) cell and return the JSONL row dict."""
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
        "replicate_idx": replicate_idx,
        "seed": seed,
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
        rsp = mod.complete(
            user_prompt, model, seed,
            system=SYSTEM,
            context_length=ctx_len,
            extra_args={
                "temperature": temperature, "max_tokens": max_tokens,
                **(extra_params or {}),
            },
            request_timeout=request_timeout,
            max_retries=max_retries,
        )
    except Exception as exc:  # noqa: BLE001
        gen_ms = int((time.monotonic() - t_gen) * 1000)
        return {
            **base_row,
            "prompt_tokens": 0, "completion_tokens": 0,
            "cache_read_tokens": 0, "cache_creation_tokens": 0,
            # No server-reported stop reason when the request itself raised;
            # the key stays present so every cell row indexes
            # row["finish_reason"] alike.
            "finish_reason": None,
            "gen_ms": gen_ms, "verify_ms": 0,
            "candidate_proof": "", "raw_response": "",
            "reasoning_content": None,
            "verdict": "exception",
            "lean_error": f"{type(exc).__name__}: {exc}",
            "final_state_pp": None,
        }
    gen_ms = int((time.monotonic() - t_gen) * 1000)

    candidate = extract_tactic_block(rsp.content)

    t_ver = time.monotonic()
    try:
        verdict = verifier.try_tail(dojo, state_at_k, candidate, theorem.full_name)
    except Exception as exc:  # noqa: BLE001
        verdict = verifier.ProofResult(
            theorem.full_name, "exception", candidate,
            error=f"{type(exc).__name__}: {exc}",
        )
    verify_ms = int((time.monotonic() - t_ver) * 1000)

    return {
        **base_row,
        "api_model": rsp.model,
        "prompt_tokens": rsp.prompt_tokens,
        "completion_tokens": rsp.completion_tokens,
        "cache_read_tokens": rsp.cached_prompt_tokens,
        "cache_creation_tokens": 0,  # no provider reports cache-creation
        "finish_reason": rsp.finish_reason,
        "gen_ms": gen_ms, "verify_ms": verify_ms,
        "candidate_proof": candidate, "raw_response": rsp.content,
        "reasoning_content": rsp.reasoning,
        "verdict": verdict.verdict,
        "lean_error": verdict.error,
        "final_state_pp": verdict.final_state_pp,
    }


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------


def _provider_for(mc: dict):
    """Resolve the provider module for one model-config entry.

    Explicit rather than via the env-dispatched
    `smolbench.evals.provider.complete`, because one process-wide
    `INFERENCE_PROVIDER` cannot express a lineup that mixes providers across
    `config["models"]`. Unknown names propagate `provider_module`'s `ValueError`.
    """
    return provider_module(mc["provider"])


def _ctx_len_for(mc: dict, mod) -> int:
    """Resolve a model's context window, tolerating catalog-lookup failures.

    A timed-out catalog request or unlisted model id must not abort the sweep,
    so lookup failure falls back to `10**9`: `complete()`'s token-usage guard
    then never fires for this model, and a genuine overflow surfaces later as
    that guard's `ValueError`, which per-cell handling records as a resumable
    exception row -- a soft failure instead of a hard abort.
    """
    try:
        return mod.get_model_context_length(mc["model"])
    except Exception as exc:  # noqa: BLE001
        print(
            f"warning: context-length lookup failed for model={mc['model']!r} "
            f"provider={mc['provider']!r}: {type(exc).__name__}: {exc}",
            flush=True,
        )
        return 10**9


def sweep(config: dict, run_dir: Path, *, resume: bool = True, verifier=None) -> int:
    """Run a sweep described by `config`; write per-theorem dirs under `run_dir`.

    Loops theorem, then k, then rung, then model, then replicate. Per
    (theorem, k) it opens ONE Dojo session, shared by every rung/model/replicate
    branching from it; per theorem it opens ONE further sanity-gate session that
    re-runs the full ground-truth proof.

    Seed threading: replicate `i` decodes at ``config["seed"] + i``, so the
    replicate index -- not theorem/k/rung/model -- is the replication axis, and
    cross-model comparisons at a given cell stay seed-paired.

    Parameters
    ----------
    config : dict
        Keys `theorems`, `rungs`, `models`, `k`, `n_replicates`, `temperature`,
        `max_tokens`, `dojo_timeout`, `concurrent_gen`, `max_concurrency`,
        `skip_trivial`, `theorem_workers`, plus the generation defaults in the
        module docstring (`seed`, `request_timeout`, `max_retries`,
        `models[i].provider`).
    resume : bool
        Skip cells already recorded in `all_rows.jsonl` under their row key
        (model, theorem, k, rung, replicate_idx); `_existing_keys` defines what
        counts as recorded.
    verifier : optional
        `None` lazily resolves `_default_verifier()`; tests pass a fake to
        exercise the whole dispatch/schema/resume path without `lean_dojo`.

    Returns
    -------
    int
        Cell rows written this call, excluding skipped and sanity rows.

    Notes
    -----
    ``LEAN_CELL_WHITELIST`` (env, optional) points at a JSON file of cell keys
    (see `load_cell_whitelist`). When set, ONLY those cells generate: every other
    cell is skipped exactly like an already-resumed one, and theorems owning NO
    whitelisted cell are dropped before their sanity gate would run. A theorem
    that does own one still gets its full, unconditional ground-truth replay --
    the whitelist narrows WHICH cells generate, not whether a surviving theorem
    is re-checked. A missing or malformed file raises `ValueError` before any
    theorem is selected, rather than degrading into a costly full-lane run.
    """
    if verifier is None:
        verifier = _default_verifier()

    # Env-gated cell whitelist (see this function's Notes). Loaded ONCE
    # here and threaded into `_select_theorems` and
    # `_run_cells_at_step[_concurrent]`, so a malformed or missing file
    # raises before the sweep has burned real spend.
    cell_whitelist_path = os.environ.get("LEAN_CELL_WHITELIST", "").strip()
    cell_whitelist: frozenset[tuple] | None = (
        load_cell_whitelist(cell_whitelist_path) if cell_whitelist_path else None
    )

    theorems = _select_theorems(config["theorems"], cell_whitelist=cell_whitelist)
    k_strategy = config.get("k", {}).get("strategy", "last")
    rungs: list[str] = list(config.get("rungs", []))
    for r in rungs:
        if ":" not in r:
            raise ValueError(f"rung {r!r} must look like 'chain:level'")
        chain, lvl = r.split(":", 1)
        validate_rung(chain, int(lvl))  # type: ignore[arg-type]

    models_cfg = list(config["models"])
    # Fail fast on unknown provider names. Pure module resolution, no
    # network call, so a typo aborts with provider_module's actionable
    # ValueError instead of after the first theorem has burned a real
    # sanity replay inside a Dojo session.
    for mc in models_cfg:
        _provider_for(mc)
    n_replicates = int(config.get("n_replicates", 1))
    temperature = float(config.get("temperature", 0.7))
    max_tokens = int(config.get("max_tokens", 4096))
    dojo_timeout = int(config.get("dojo_timeout", 300))
    concurrent_gen = bool(config.get("concurrent_gen", True))
    max_concurrency = int(config.get("max_concurrency", 12))
    skip_trivial = bool(config.get("skip_trivial", True))
    theorem_workers = int(config.get("theorem_workers", 1))
    base_seed = int(config.get("seed", 1776))
    request_timeout = int(config.get("request_timeout", 1800))
    max_retries = int(config.get("max_retries", 4))

    run_dir.mkdir(parents=True, exist_ok=True)
    all_rows_path = run_dir / "all_rows.jsonl"

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
    sanity_done = _sanity_done(all_rows_path) if resume else {}
    if done_keys or sanity_done:
        print(
            f"resume: {len(done_keys)} cells + {len(sanity_done)} sanity rows in "
            f"{all_rows_path.name}",
            flush=True,
        )

    # (provider module, context length) cache: resolved once per unique
    # (provider, model) per sweep, not per cell. The key includes
    # `mc["model"]` because `ctx_len` is model-specific -- without it one
    # model's context length could leak onto another's token-usage guard.
    provider_cache: dict[tuple, tuple] = {}
    def _provider_and_ctx_for(mc: dict) -> tuple:
        key = (mc["provider"], mc["model"])
        if key not in provider_cache:
            mod = _provider_for(mc)
            provider_cache[key] = (mod, _ctx_len_for(mc, mod))
        return provider_cache[key]

    # Per-model concurrency caps: a model entry with `max_concurrency: N`
    # gets a Semaphore(N) shared across all theorem workers, throttling
    # models that hit upstream rate limits (e.g. qwen-instruct's 429s)
    # without slowing the rest of the lineup.
    model_semaphores: dict[str, threading.Semaphore] = {}
    for mc in models_cfg:
        cap = mc.get("max_concurrency")
        if cap is not None:
            display_name = mc.get("display_name", mc["model"])
            model_semaphores[display_name] = threading.Semaphore(int(cap))
            print(f"per-model cap: {display_name} = {int(cap)}", flush=True)

    n_total_cells = sum(
        len(_k_indices(t, k_strategy)) * len(rungs) * len(models_cfg) * n_replicates
        for t in theorems
    )
    print(
        f"sweep: {len(theorems)} theorems, {len(rungs)} rungs × "
        f"{len(models_cfg)} models × {n_replicates} replicates → {n_total_cells} cells",
        flush=True,
    )
    if cell_whitelist is not None:
        # `n_total_cells` is the naive product over the WHITELIST-NARROWED
        # theorem pool -- an upper bound, since a whitelisted theorem can
        # own only SOME of its rung/model/replicate combinations. Printed
        # separately so the inflated product is not read as the count
        # LEAN_CELL_WHITELIST actually selected.
        print(
            f"cell whitelist active: {len(cell_whitelist)} cell(s) requested "
            f"(LEAN_CELL_WHITELIST={cell_whitelist_path})",
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
            prev_sanity = sanity_done.get(theorem.full_name)
            if prev_sanity is None:
                t0 = time.monotonic()
                sanity = verifier.replay_ground_truth(theorem, timeout=dojo_timeout)
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
                if sanity.verdict in SANITY_FAILURE_VERDICTS:
                    with print_lock:
                        print(
                            f"  SANITY-FAIL {theorem.full_name}: {sanity.verdict} "
                            f"({sanity.error or ''})  — skipping cells",
                            flush=True,
                        )
                    return n_w, n_o, n_s
            elif prev_sanity in SANITY_FAILURE_VERDICTS:
                # Resume re-applies the gate rather than just skipping the
                # replay (see `_sanity_done`).
                with print_lock:
                    print(
                        f"  SANITY-FAIL {theorem.full_name}: {prev_sanity} "
                        f"(recorded) — skipping cells on resume",
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
                            models_cfg=models_cfg, n_replicates=n_replicates,
                            temperature=temperature, max_tokens=max_tokens,
                            provider_factory=_provider_and_ctx_for,
                            base_seed=base_seed, request_timeout=request_timeout,
                            max_retries=max_retries,
                            done_keys=done_keys,
                            tdir=tdir, dojo_timeout=dojo_timeout,
                            verifier=verifier,
                            max_workers=max_concurrency,
                            write_lock=write_lock, print_lock=print_lock,
                            model_semaphores=model_semaphores,
                            cell_whitelist=cell_whitelist,
                        )
                    else:
                        written_here, ok_here, skipped_here = _run_cells_at_step(
                            all_rows=all_rows,
                            theorem=theorem, k=k,
                            rungs=effective_rungs, rendered_by_rung=rendered_by_rung,
                            models_cfg=models_cfg, n_replicates=n_replicates,
                            temperature=temperature, max_tokens=max_tokens,
                            provider_factory=_provider_and_ctx_for,
                            base_seed=base_seed, request_timeout=request_timeout,
                            max_retries=max_retries,
                            done_keys=done_keys,
                            tdir=tdir, dojo_timeout=dojo_timeout,
                            verifier=verifier,
                            write_lock=write_lock, print_lock=print_lock,
                            cell_whitelist=cell_whitelist,
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
