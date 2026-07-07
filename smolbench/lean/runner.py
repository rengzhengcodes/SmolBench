"""Eval loop: theorem × step k × context rung × N rollouts → per-theorem dir.

Two entry points:
  - `run_cell(...)` — yields rows for one (theorem, k, chain, level) cell.
    Opens its own Dojo session per call. Used by the `run-cell` CLI
    subcommand (`python -m smolbench.lean.cli run-cell`).
  - `sweep(config, run_dir)` — runs a YAML-described sweep with per-theorem
    output directories and Dojo session reuse across all rungs/models/rollouts
    sharing a (theorem, k). Used by the `run-sweep` CLI subcommand
    (`python -m smolbench.lean.cli run-sweep`).

Generation dispatch: both entry points resolve a `smolbench.evals` provider
module (`smolbench.evals.provider.provider_module`) per model config and call
its shared `ChatClient.complete` (see `smolbench.evals.openai_compat`) rather
than a bespoke per-model client. Relevant config keys (all optional, sane
defaults below):
  - `models[i].provider` — provider name resolved via `provider_module`
    (e.g. "primeintellect", "openrouter", "aws", "ec2"). Resolved explicitly
    per model (bypassing the `INFERENCE_PROVIDER` env var) so a single sweep
    can mix providers across its model lineup — see `_provider_for`.
  - `seed` (default 1776) — base decoding seed; each rollout's actual seed is
    `seed + rollout_idx` (see `sweep`'s "Seed threading" note below).
  - `request_timeout` (default 1800) — per-request read-timeout override
    forwarded to every `complete()` call; the `ChatClient` default (120s)
    would truncate long chain-of-thought generations mid-stream.
  - `max_retries` (default 4) — caps retryable failures (HTTP 429/5xx,
    connection errors) per `complete()` call; without a cap a wedged
    endpoint could spin forever inside an open Dojo session.

Results root: `results_root()` resolves the sweep/run-cell output root,
overridable via the `SMOLBENCH_LEAN_RESULTS` environment variable and
otherwise anchored to this file's own location (repo-root-relative, never
cwd-relative) — see `results_root`'s docstring and `corpus.data_root` for
the mirrored pattern.

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

from smolbench.evals.provider import provider_module

from .context import Chain, is_trivial_rung, render, validate as validate_rung
from .corpus import (
    BenchmarkTheorem,
    iter_replay_passing,
    iter_with_proof,
    load_split,
)
from .prompt import SYSTEM, build_user_prompt, extract_tactic_block

# Design: NO top-level `from .verify import ...` here. `.verify` imports
# `lean_dojo`, which is only installable in the dedicated `.venv-lean`
# environment (see `verify.py`'s import guard). Importing `runner` — which
# also hosts pure dispatch/schema logic exercised by the offline test suite
# on the main venv (Python 3.14, no lean_dojo) — must not drag that
# dependency in. See `_default_verifier` below for the lazy import seam that
# replaces these names at call time instead.


def results_root() -> Path:
    """Resolve the root directory for sweep/run-cell output.

    Resolution order:
      1. The ``SMOLBENCH_LEAN_RESULTS`` environment variable, if set.
      2. ``notebooks/lean/results`` under the repo root.

    Repo-anchored via this file's own location (``parents[2]`` from
    ``smolbench/lean/runner.py`` is the repo root), never cwd-relative —
    mirrors the pattern used by ``corpus.data_root()``: callers (CLI
    invocations, notebook kernels, test runners) may run from arbitrary
    working directories, so a cwd-relative default would silently resolve
    to the wrong place depending on who calls it.

    The environment variable is read at CALL time (not import time), so
    tests may set ``SMOLBENCH_LEAN_RESULTS`` (e.g. to a ``tmp_path``) any
    time before calling this function or any function that calls it.

    Returns
    -------
    Path
        The results root directory. Not guaranteed to exist; callers that
        write under it create parents as needed (see `sweep`).
    """
    override = os.getenv("SMOLBENCH_LEAN_RESULTS")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "notebooks" / "lean" / "results"


def _default_verifier():
    """Lazily resolve the real Lean verifier module.

    Deferred (call-time, not module-top) import of `smolbench.lean.verify`,
    which requires `lean_dojo` and therefore only works under the dedicated
    `.venv-lean` environment (see that module's import guard). Callers on
    the main venv that need a verifier must pass one explicitly (e.g. the
    offline test suite's `FakeVerifier`); callers on `.venv-lean` (the real
    `run-sweep`/`run-cell` CLI invocations) get the real thing here.

    Returns
    -------
    ModuleType
        The `smolbench.lean.verify` module, exposing `open_at_step`,
        `try_tail`, `replay_ground_truth`, `verify_proof_tail`, and
        `ProofResult`.

    Raises
    ------
    ImportError
        Propagated from `smolbench.lean.verify` when `lean_dojo` is not
        installed in the current interpreter (see that module's guard for
        the actionable remedy message).
    """
    from smolbench.lean import verify
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
    n_rollouts: int,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    dojo_timeout: int = 600,
    seed: int = 1776,
    request_timeout: int = 1800,
    max_retries: int = 4,
    verifier=None,
) -> Iterable[dict]:
    """Yield one result row per rollout for a single (theorem, k, chain, level) cell.

    Parameters
    ----------
    provider : str
        Provider name resolved via `smolbench.evals.provider.provider_module`
        (e.g. "primeintellect", "openrouter", "aws", "ec2"). Replaces the
        pre-refactor `client: LLMClient` parameter — see the module
        docstring's "Generation dispatch" note.
    model : str
        Provider-specific model id.
    theorem, k, chain, level : see `smolbench.lean.context.render`.
    n_rollouts : int
        Number of independent generations to run against the same rendered
        prompt.
    temperature : float, default 0.7
        Sampling temperature forwarded as `extra_args["temperature"]`.
    max_tokens : int, default 4096
        Output token cap forwarded as `extra_args["max_tokens"]`.
    dojo_timeout : int, default 600
        Seconds allowed for the Dojo session (prefix replay + tail check).
    seed : int, default 1776
        Base decoding seed. Rollout `i`'s actual seed is `seed + i` — see
        `sweep`'s "Seed threading" design note for why rollouts (not
        theorem/rung/model) are the seed-varying replicate axis.
    request_timeout : int, default 1800
        Per-request read-timeout override forwarded to `complete()`; the
        `ChatClient` default (120s) would truncate long CoT generations.
    max_retries : int, default 4
        Retryable-failure cap forwarded to `complete()`.
    verifier : ModuleType or None
        Verifier module exposing `verify_proof_tail`. `None` (the default)
        lazily resolves the real `smolbench.lean.verify` module via
        `_default_verifier()` — see that function's docstring. Tests pass a
        fake here to run on interpreters without `lean_dojo`.

    Yields
    ------
    dict
        One JSONL-serializable row per rollout; see `_execute_one_cell`'s
        row schema (same keys, since both paths share the same wire format).
    """
    if verifier is None:
        verifier = _default_verifier()

    rendered = render(theorem, k, chain, level)
    user_prompt = build_user_prompt(rendered)

    mod = provider_module(provider)
    try:
        ctx_len = mod.get_model_context_length(model)
    except Exception as exc:  # noqa: BLE001
        # Best-effort guard (see module docstring / `_ctx_len_for`): a
        # catalog lookup failure must not abort the whole cell. Falling
        # back to a huge context length means a genuine overflow surfaces
        # later as a ValueError from `complete()`'s token guard instead,
        # which is caught below and recorded as a normal exception row.
        ctx_len = 10**9
        print(f"warning: context-length lookup failed for {model} on {provider}: {exc}", flush=True)

    for rollout_idx in range(n_rollouts):
        rollout_seed = seed + rollout_idx
        t0 = time.monotonic()
        # Design: no try/except around `complete()` here — matches the
        # pre-refactor `run_cell`, which let generation failures propagate
        # to its caller (the `run-cell` CLI command) rather than recording
        # an exception row. That resumable-exception-row behavior is
        # `sweep`'s concern (see `_execute_one_cell` / the concurrent path
        # below); `run_cell` is a single-shot, non-resuming entry point.
        rsp = mod.complete(
            user_prompt, model, rollout_seed,
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
            "rollout_idx": rollout_idx,
            "seed": rollout_seed,
            "model": rsp.model or model,
            "provider": provider,
            "temperature": temperature,
            "prompt_tokens": rsp.prompt_tokens,
            "completion_tokens": rsp.completion_tokens,
            "cache_read_tokens": rsp.cached_prompt_tokens,
            "cache_creation_tokens": 0,  # vestigial: no provider reports cache-creation now
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


def _sanity_done(jsonl_path: Path) -> dict[str, str]:
    """Map theorem name -> recorded sanity verdict from the JSONL (last wins).

    Returns verdicts (not just names) so a resumed sweep can re-apply the
    sanity gate's early return: a theorem whose ground truth failed to
    replay must stay excluded on resume, not silently fall through to cell
    generation just because its gate row already exists.
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
) -> tuple[int, int, int]:
    """Open Dojo at (theorem, k); run all cells. Returns (n_written, n_ok, n_skipped)."""
    n_written = n_ok = n_skipped = 0
    write_lock = write_lock or threading.Lock()
    print_lock = print_lock or threading.Lock()

    with verifier.open_at_step(theorem, k, timeout=dojo_timeout) as (dojo, state_at_k):
        for rung in rungs:
            rendered = rendered_by_rung[rung]
            chain, level_str = rung.split(":", 1)
            level = int(level_str)
            user_prompt = build_user_prompt(rendered)

            for mc in models_cfg:
                mod, ctx_len = provider_factory(mc)
                model = mc["model"]
                display_name = mc.get("display_name", model)
                extra_params = mc.get("extra_params")
                for rollout_idx in range(n_rollouts):
                    key = _row_key(display_name, theorem.full_name, k, rung, rollout_idx)
                    if key in done_keys:
                        n_skipped += 1
                        continue

                    # Seed threading: rollouts are the replicate axis (see
                    # `sweep`'s docstring), so the decoding seed depends only
                    # on rollout_idx, not on theorem/k/rung/model — this keeps
                    # cross-model comparisons at a given cell seed-paired.
                    seed = base_seed + rollout_idx
                    row = _execute_one_cell(
                        verifier=verifier,
                        mod=mod, model=model, ctx_len=ctx_len, user_prompt=user_prompt,
                        rendered=rendered, theorem=theorem, k=k, chain=chain,
                        level=level, rung=rung, rollout_idx=rollout_idx, seed=seed,
                        provider=mc["provider"], temperature=temperature,
                        max_tokens=max_tokens, request_timeout=request_timeout,
                        max_retries=max_retries, dojo=dojo, state_at_k=state_at_k,
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
        user_prompt = build_user_prompt(rendered)
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
                    "user_prompt": user_prompt,
                    "mc": mc, "model": mc["model"], "provider": mc["provider"],
                    "rollout_idx": rollout_idx,
                    # Seed threading: rollouts are the replicate axis, so the
                    # seed depends only on rollout_idx — see `sweep`'s
                    # docstring and the matching comment in `_run_cells_at_step`.
                    "seed": base_seed + rollout_idx,
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
                    "rollout_idx": p["rollout_idx"],
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
                        "gen_ms": gen_ms, "verify_ms": 0,
                        "candidate_proof": "", "raw_response": "",
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
                        "cache_creation_tokens": 0,  # vestigial: no provider reports cache-creation now
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
    verifier,
    mod, model: str, ctx_len: int, user_prompt: str, rendered,
    theorem: BenchmarkTheorem, k: int, chain: str, level: int,
    rung: str, rollout_idx: int, seed: int, provider: str, temperature: float,
    max_tokens: int, request_timeout: int, max_retries: int, dojo, state_at_k,
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
            "gen_ms": gen_ms, "verify_ms": 0,
            "candidate_proof": "", "raw_response": "",
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
        "cache_creation_tokens": 0,  # vestigial: no provider reports cache-creation now
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

    Design: resolves `provider_module(mc["provider"])` EXPLICITLY rather
    than going through the env-dispatched `smolbench.evals.provider.complete`
    (which reads `INFERENCE_PROVIDER`). A sweep's model lineup can mix
    providers across entries in `config["models"]` (e.g. one model served
    via `primeintellect`, another via `ec2`); a single process-wide env var
    cannot express "this model via X, that one via Y" simultaneously, so
    each model config must resolve its own provider independently. Unknown
    provider names propagate `provider_module`'s `ValueError` unchanged.
    """
    return provider_module(mc["provider"])


def _ctx_len_for(mc: dict, mod) -> int:
    """Resolve a model's context window, tolerating catalog-lookup failures.

    Best-effort guard: a transient failure fetching the context length (a
    catalog request timing out, an unlisted model id) must not abort the
    whole sweep. Falling back to a huge context length (`10**9`) means
    `complete()`'s token-usage guard simply never fires for this model; a
    *genuine* overflow then surfaces later as a `ValueError` from that
    guard, which the existing per-cell exception handling already catches
    and records as a resumable exception row — so the fallback trades a
    hard abort for a soft, retryable failure mode instead of silently
    hiding real problems.
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
    """Run a sweep described by `config`. Writes per-theorem dirs under `run_dir`.

    Loop ordering: theorem → k → rung → model → rollout. Resumes by skipping
    cells whose row key (model, theorem, k, rung, rollout_idx) is already in
    all_rows.jsonl. Per (theorem, k) opens ONE Dojo session shared across all
    rungs/models/rollouts that branch from it; per theorem runs ONE separate
    sanity-gate Dojo session that re-runs the full ground-truth proof.

    Config keys (all optional; sane defaults below — see the module
    docstring's "Generation dispatch" section for the rationale behind
    each):
      - `seed` (default 1776) — base decoding seed. Each rollout's actual
        seed is `seed + rollout_idx`; rollouts are the replicate axis, so
        this is independent of theorem/k/rung/model (cross-model
        comparisons at a given cell stay seed-paired).
      - `request_timeout` (default 1800) — per-request read-timeout
        override forwarded to every `complete()` call.
      - `max_retries` (default 4) — retryable-failure cap forwarded to
        every `complete()` call, so a sweep never spins forever inside an
        open Dojo session against a wedged endpoint.
      - `models[i].provider` — resolved per model via `provider_module`,
        NOT the `INFERENCE_PROVIDER` env var, so one sweep can mix
        providers across its model lineup (see `_provider_for`).

    Parameters
    ----------
    config : dict
        Sweep configuration; see the keys above plus `theorems`, `rungs`,
        `models`, `k`, `n_rollouts`, `temperature`, `max_tokens`,
        `dojo_timeout`, `concurrent_gen`, `max_concurrency`,
        `skip_trivial`, `theorem_workers` (all pre-existing, unchanged).
    run_dir : Path
        Output directory; see the module docstring's "Output layout".
    resume : bool, default True
        When True, skip cells already recorded in `all_rows.jsonl`
        (excluding rows whose verdict is `exception`, which always re-run).
    verifier : ModuleType or None
        Verifier module exposing `open_at_step`, `try_tail`,
        `replay_ground_truth`, `verify_proof_tail`, and `ProofResult`.
        `None` (the default) lazily resolves the real
        `smolbench.lean.verify` module via `_default_verifier()` — tests
        pass a fake here to run the whole sweep dispatch/schema/resume
        logic on interpreters without `lean_dojo`.

    Returns
    -------
    int
        Total number of cell rows written this call (excludes skipped and
        sanity rows).
    """
    if verifier is None:
        verifier = _default_verifier()

    theorems = _select_theorems(config["theorems"])
    k_strategy = config.get("k", {}).get("strategy", "last")
    rungs: list[str] = list(config.get("rungs", []))
    for r in rungs:
        if ":" not in r:
            raise ValueError(f"rung {r!r} must look like 'chain:level'")
        chain, lvl = r.split(":", 1)
        validate_rung(chain, int(lvl))  # type: ignore[arg-type]

    models_cfg = list(config["models"])
    # Fail fast on unknown provider names: pure module resolution (no
    # network), so a typo'd or legacy provider (e.g. the retired
    # "openai_compat"/"anthropic") aborts here with provider_module's
    # actionable ValueError instead of after the first theorem has already
    # burned a real sanity replay inside a Dojo session.
    for mc in models_cfg:
        _provider_for(mc)
    n_rollouts = int(config.get("n_rollouts", 1))
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
    sanity_done = _sanity_done(all_rows_path) if resume else {}
    if done_keys or sanity_done:
        print(
            f"resume: {len(done_keys)} cells + {len(sanity_done)} sanity rows in "
            f"{all_rows_path.name}",
            flush=True,
        )

    # (provider module, context length) cache, resolved once per unique
    # (provider, model) per sweep, not once per cell. `ctx_len` (from
    # `_ctx_len_for`) is model-specific — two model configs on the same
    # provider can have different context windows — so the key includes
    # `mc["model"]`; omitting it would let one model's context length
    # silently leak onto another's token-usage guard. (The pre-refactor
    # `clients` cache also keyed on a per-model `base_url` override; that
    # key is dead now — endpoints are resolved inside each provider module
    # from its own env vars.) See `_provider_for` for why provider
    # resolution is explicit-per-model rather than env-dispatched.
    provider_cache: dict[tuple, tuple] = {}
    def _provider_and_ctx_for(mc: dict) -> tuple:
        key = (mc["provider"], mc["model"])
        if key not in provider_cache:
            mod = _provider_for(mc)
            provider_cache[key] = (mod, _ctx_len_for(mc, mod))
        return provider_cache[key]

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
                if sanity.verdict != "success":
                    with print_lock:
                        print(
                            f"  SANITY-FAIL {theorem.full_name}: {sanity.verdict} "
                            f"({sanity.error or ''})  — skipping cells",
                            flush=True,
                        )
                    return n_w, n_o, n_s
            elif prev_sanity != "success":
                # Resume must re-apply the gate, not just skip the replay: a
                # theorem recorded as sanity-failed stays excluded, otherwise
                # resuming would generate cells the first pass refused to run.
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
                            models_cfg=models_cfg, n_rollouts=n_rollouts,
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
                        )
                    else:
                        written_here, ok_here, skipped_here = _run_cells_at_step(
                            all_rows=all_rows,
                            theorem=theorem, k=k,
                            rungs=effective_rungs, rendered_by_rung=rendered_by_rung,
                            models_cfg=models_cfg, n_rollouts=n_rollouts,
                            temperature=temperature, max_tokens=max_tokens,
                            provider_factory=_provider_and_ctx_for,
                            base_seed=base_seed, request_timeout=request_timeout,
                            max_retries=max_retries,
                            done_keys=done_keys,
                            tdir=tdir, dojo_timeout=dojo_timeout,
                            verifier=verifier,
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
