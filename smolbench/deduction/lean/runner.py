"""Run the eval loop: theorem × step k × context rung × N replicates.

Two entry points, both used by `cli.py`: `run_cell` (one cell, own Lean REPL
session) and `sweep` (YAML-described sweep, one REPL session per (theorem, k)).

Generation goes through `ChatClient.complete` on a provider module resolved by
`models[i].provider` per entry (`_provider_for`), NOT the `INFERENCE_PROVIDER`
env var, so one sweep can mix providers. Other optional config keys: `seed`
(sweep config default 0, matching `theorems.seed`'s own default -- see
`_select_theorems` -- and `notebooks/deduction/run_study.py`'s driver config,
so an omitted key cannot silently disagree with either; replicate `i` uses
`seed + i`; `run_cell`'s own `seed` PARAMETER is a different entry point and
keeps its separate documented default of 1776); `dojo_timeout` (config key
spelling kept for backwards compatibility -- see `DEFAULT_DOJO_TIMEOUT`'s
Design comment -- default `DEFAULT_DOJO_TIMEOUT` = 600s for the Lean REPL
session per (theorem, k); see that constant's Design comment for why 600,
not 300); `request_timeout` (default 1800s, since `ChatClient`'s 120s default
truncates long CoT mid-stream); `max_retries` (default 4, so a wedged
endpoint cannot spin forever inside an open REPL session).
`SMOLBENCH_LEAN_RESULTS` overrides the output root (`results_root()`).

Output layout (`run_dir`):

    manifest.json        config + run_name + start/finish timestamps + counts
    all_rows.jsonl       source of truth, append-only across resumes; `sweep`
                         truncates (and logs) a torn or unparseable final
                         line before reopening for append, since appending
                         onto it would weld it into a corrupt MIDDLE line
                         (`_repair_torn_tail`, fix 13-07)
    analysis.txt         `write_run_analysis` output, regenerated at end of sweep
    theorems/<theorem_slug>/
        meta.json        full_name, file_path, k, ground_truth, premises
        prompts/<rung-slug>.md                    rendered prompt per rung
        outputs/<rung-slug>__<model-slug>.jsonl   one row per replicate
        summary.md       human-readable rollup, regenerated at end

Dependency split: this module never verifies Lean proofs itself -- `.verify`
does, through `_default_verifier()` -- so `run_cell`/`sweep` only need a Lean
toolchain when `verifier=None` (the default) resolves the real one. That
needs `lean_interact` (the `lean` extra, `uv sync --all-extras`), `elan` on
`PATH`, and a mathlib4 checkout built with `elan`/`lake` and pointed to by
`SMOLBENCH_MATHLIB_ROOT` (`replbackend.mathlib_root`, read at call time).
Tests and generation-only callers pass a fake/`NullVerifier` instead and need
none of that. `lean_dojo` -- the old, deprecated `Dojo` interaction layer,
unable to drive Lean >= v4.20 and so unable to reach this corpus's mathlib4
at Lean v4.34.0-rc2 -- is NOT what the verifier needs any more; it remains a
declared dependency of the `lean` extra only for corpus tracing and for
`premises`' source slicing out of its traced-repo cache at
`~/.cache/lean_dojo` (`premises._traced_root`, read by `skip_trivial` below).
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
    data_root,
    is_postcutoff_corpus,
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
# `lean_interact`, which is not always installed; `_default_verifier` below
# is the lazy seam that resolves those names at call time.


#: Default `dojo_timeout` (seconds): `run_cell`'s parameter default, `sweep`'s
#: `config.get("dojo_timeout", ...)` fallback, and `cli.py`'s `run-cell
#: --timeout` default all resolve to this one constant (fix 13-17). Before
#: this constant existed, the three disagreed -- 600 in `run_cell` and
#: `cli --timeout`, 300 in `sweep` and in
#: `notebooks/deduction/run_study.py`'s sweep config.
#:
#: Design: 600, not 300 -- deliberately NOT "unify downward" to the smaller
#: value. `notebooks/deduction/run_study.py` passes `dojo_timeout: 300`
#: EXPLICITLY in its sweep config, so the production sweep's effective
#: timeout is unchanged by this constant either way. `run_cell` and
#: `cli --timeout` are already 600; unifying on 300 would TIGHTEN them, and a
#: Lean REPL request that times out is recorded as an `"exception"` verdict
#: (see `_execute_one_cell`) -- i.e. tightening would silently convert
#: slow-but-real theorems into infrastructure failures. Unifying on 600
#: instead only changes `sweep`'s default for a config that OMITS the key,
#: and only by allowing it MORE time. So: 600 preserves every existing
#: production path; 300 would not.
#:
#: The config key stays spelled `"dojo_timeout"` -- kept for backwards
#: compatibility with existing sweep YAML files and archived `manifest.json`
#: config blocks -- even though the verifier this sweeps against is no
#: longer LeanDojo-backed.
DEFAULT_DOJO_TIMEOUT: int = 600


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
    """Import `.verify` at call time and return it; raises `ImportError` without `lean_interact`.

    The verifier protocol is `open_at_step`, `try_tail`, `replay_ground_truth`,
    `verify_proof_tail`, `ProofResult`. The lazy import keeps `runner` usable
    without `lean_interact`; such callers pass a verifier explicitly (the tests'
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
# Single cell — used by `run-cell`. Opens its own Lean REPL session.
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
    dojo_timeout: int = DEFAULT_DOJO_TIMEOUT,
    seed: int = 1776,
    request_timeout: int = 1800,
    max_retries: int = 4,
    verifier=None,
) -> Iterable[dict]:
    """Yield one JSONL-serializable row per replicate for one (theorem, k, chain, level) cell.

    Opens its own Lean REPL session. Unlike `sweep`, this wraps `complete()`
    in no try/except: it is single-shot and non-resuming, so generation
    failures propagate rather than becoming exception rows.

    Parameters
    ----------
    provider : str
        Name resolved by `smolbench.evals.provider.provider_module` (e.g.
        "primeintellect", "openrouter", "aws", "ec2").
    theorem, k, chain, level
        As in `context.render`.
    dojo_timeout : int
        Seconds for the Lean REPL session (prefix replay plus tail check).
        Parameter/config-key spelling kept as `dojo_timeout` for backwards
        compatibility (see `DEFAULT_DOJO_TIMEOUT`'s Design comment).
    seed : int
        Base decoding seed; replicate `i` uses ``seed + i``, so the replicate
        index -- not theorem/rung/model -- is the seed-varying axis.
    verifier : optional
        Must expose `verify_proof_tail`; `None` resolves `_default_verifier()`
        (tests pass a fake to run without `lean_interact`).

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
# Sweep — multi-cell loop with per-theorem dirs and shared Lean REPL sessions.
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


def _require_all_postcutoff(pool: list[BenchmarkTheorem]) -> None:
    """Raise unless every theorem in `pool` carries `BenchmarkTheorem.postcutoff`.

    Factored out of `_select_theorems` so its two call sites -- the raw pool,
    before any sampling/sharding, and the final selection, after -- share one
    definition and cannot drift apart.

    Raises
    ------
    ValueError
        Names up to the first 5 offending theorems (by `full_name`) plus a
        total count, so a large bad pool doesn't dump thousands of names.
    """
    bad = [t.full_name for t in pool if not t.postcutoff]
    if not bad:
        return
    shown = ", ".join(bad[:5])
    suffix = f", and {len(bad) - 5} more" if len(bad) > 5 else ""
    raise ValueError(
        f"theorems.require_postcutoff: {len(bad)} theorem(s) are not flagged "
        f"postcutoff: {shown}{suffix}"
    )


def _select_theorems(
    spec: dict, *, cell_whitelist: frozenset[tuple] | None = None
) -> list[BenchmarkTheorem]:
    """Resolve a config `theorems` block into a concrete BenchmarkTheorem list.

    `cell_whitelist`, when given, narrows the pool to theorems owning at least
    one of its cell keys; it is a parameter rather than a `spec` field because
    `sweep` loads it once from ``LEAN_CELL_WHITELIST``.

    Parameters
    ----------
    spec : dict
        ``source`` (default ``"replay_passing"``), ``kind`` (default
        ``"random"``), ``split`` (default ``"val"``), ``max_tactics``,
        ``limit``, ``seed``, optional ``shard`` (``"i/n"``), and
        ``require_postcutoff`` (bool, default False). When
        `require_postcutoff` is truthy, the selection is refused unless the
        active corpus (`smolbench.deduction.lean.corpus.is_postcutoff_corpus`)
        is a post-cutoff corpus AND every selected `BenchmarkTheorem.postcutoff`
        is True; absent or False, this key never fires and every pre-existing
        caller is unaffected.

    Raises
    ------
    ValueError
        `source` is not one of ``replay_passing``/``with_proof``/``explicit``;
        or `spec["shard"]` is present but not a valid ``"i/n"`` stride; or
        `require_postcutoff` is truthy and either (1) the corpus is not a
        post-cutoff corpus, or (2) the pool or final selection contains a
        theorem not flagged `postcutoff`.
    """
    require_postcutoff = bool(spec.get("require_postcutoff", False))
    source = spec.get("source", "replay_passing")
    kind = spec.get("kind", "random")
    split = spec.get("split", "val")
    max_tactics = int(spec.get("max_tactics", 0))
    limit = int(spec.get("limit", 0))
    seed = int(spec.get("seed", 0))

    # Design: this corpus-level check runs BEFORE the pool is even loaded --
    # deliberately redundant with the per-theorem check below, but cheaper to
    # explain: the old single-snapshot LeanDojo Benchmark 4 has no post-cutoff
    # tail at all, so no sampling, seed or split change over it can ever
    # produce a compliant item. Naming `data_root()` tells the caller exactly
    # which corpus was refused.
    if require_postcutoff and not is_postcutoff_corpus():
        raise ValueError(
            f"theorems.require_postcutoff is set but {data_root()} is not a "
            "post-cutoff corpus -- the old single-snapshot LeanDojo Benchmark 4 "
            "has no post-cutoff tail, so no sampling, seed or split change over "
            "it can produce a compliant selection"
        )

    if source == "replay_passing":
        pool = list(iter_replay_passing(kind, split))
    elif source == "with_proof":
        pool = list(iter_with_proof(kind, split))
    elif source == "explicit":
        names = set(spec["full_names"])
        pool = [t for t in load_split(kind, split) if t.full_name in names]
    else:
        raise ValueError(f"unknown theorems.source: {source!r}")

    # Design: checked on the raw POOL, before sampling/sharding/whitelisting.
    # `random.Random(seed).sample` below is order- and population-sensitive,
    # so a pool containing even one pre-cutoff row must be rejected outright
    # -- otherwise whether the draw happens to miss the bad row(s) would
    # silently decide compliance.
    if require_postcutoff:
        _require_all_postcutoff(pool)

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
    # the per-(theorem, k) Lean REPL session for every untouched theorem -- the
    # efficiency an n=200-cell rerun needs against a 300-theorem pool.
    if cell_whitelist is not None:
        whitelisted_theorems = {key[1] for key in cell_whitelist}
        pool = [t for t in pool if t.full_name in whitelisted_theorems]

    if require_postcutoff:
        # Belt-and-braces: `pool` here is always a SUBSET of the pool already
        # checked above (shard/whitelist only ever remove rows), so this can
        # only ever agree with that earlier check. It stays because this is
        # the list actually handed to `sweep` -- a future filter inserted
        # between the two checks above would otherwise slip through unguarded.
        _require_all_postcutoff(pool)

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


#: Cap on how many unreachable `LEAN_CELL_WHITELIST` keys `sweep` logs
#: individually at ERROR level when it reconciles the whitelist at the end of
#: a run (fix 13-12). Bounds only the LOG stream -- the full list is always
#: recorded in `manifest.json["whitelist_missed"]` regardless of this cap, so
#: nothing is lost, only kept off an operator's screen for a large miss.
WHITELIST_MISS_LOG_CAP: int = 50


def _repair_torn_tail(jsonl_path: Path) -> int:
    """Truncate a torn or unparseable FINAL line off `jsonl_path`, in place.

    Fix 13-07 (runner half). `sweep` opens `all_rows.jsonl` in APPEND mode on
    resume (see the ``with all_rows_path.open("a")`` below), and a box
    SIGKILLed mid-write leaves a half-written final line with no trailing
    ``"\\n"``. `_existing_keys` already treats such a line as if it were never
    written -- it catches `json.JSONDecodeError` per line and skips -- so a
    torn FINAL line is harmless on its own and this module's docstring's
    promise that it "regenerates on resume" is true right up to the moment
    something appends past it. That is exactly what opening in append mode
    does: the next write lands immediately after the torn bytes with no
    separating newline, WELDING the next record onto the torn prefix into one
    line, e.g. ``{"kind": "cel{"kind": "cell", "n": 3}``. A torn FINAL line is
    recoverable -- both ``scripts/deduction/merge_lean_shards.py`` and
    ``scripts/deduction/split_lean_run_into_shards.py`` drop it with a
    warning -- but the welded MIDDLE line it turns into is not: both scripts
    hard-abort on a line that fails to parse anywhere but at the very end of
    the file. So the corruption is caused by the append, not by the crash,
    and the fix has to run before the file is reopened for append, not at
    read time (by which point `_existing_keys` has already silently
    forgiven the very state this function must not let survive).

    Parameters
    ----------
    jsonl_path : Path
        Path to a JSONL file (typically ``all_rows.jsonl``). Not required to
        exist.

    Returns
    -------
    int
        Number of bytes discarded from the end of the file. ``0`` when the
        file does not exist, is empty, or its final line was already both
        newline-terminated and valid JSON -- i.e. ``0`` means "untouched",
        not "no file".

    Notes
    -----
    Repairs at most the trailing run of bad lines, checked one at a time from
    the end: first, whether the file ends with ``"\\n"`` at all (an
    UNTERMINATED tail -- the half-write case above); then, once terminated,
    whether the last complete line parses as JSON (a torn write can also land
    exactly on a newline boundary and still leave unparseable or empty
    bytes, e.g. mid-`json.dumps` flush). Each failing check truncates back to
    the newline before it and re-checks, so a pathological multi-line tear
    -- documented here as possible even though a single SIGKILL normally
    produces at most one -- is still fully repaired rather than only
    partially. The loop is bounded because each iteration strictly shrinks
    the candidate length, terminating at 0 if every line on disk were bad.

    Reads the whole file once and truncates with a single `os.path`-relative
    `io.IOBase.truncate` call (never rewrites the file's surviving content
    back out): `all_rows.jsonl` is this run's source of truth, and turning a
    cheap trim into a read-modify-rewrite would open a window where a second
    crash loses rows that were never torn in the first place.

    Logs a WARNING naming the path and the byte count on any repair, since
    silently discarding bytes from the source of truth would hide that a row
    is being regenerated from an operator who has no other way to notice.
    """
    if not jsonl_path.exists():
        return 0
    with jsonl_path.open("r+b") as f:
        data = f.read()
        end = len(data)
        while end > 0:
            if data[end - 1] != 0x0A:  # last byte is not '\n': tail is UNTERMINATED
                newline_before = data.rfind(b"\n", 0, end)
                end = newline_before + 1  # 0 if no newline at all: whole file was torn
                continue
            # Terminated: isolate the last complete line (excluding its own
            # trailing "\n") and see if it parses.
            newline_before = data.rfind(b"\n", 0, end - 1)
            last_line = data[newline_before + 1 : end - 1]
            try:
                json.loads(last_line.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                end = newline_before + 1
                continue
            break  # terminated and parses: nothing left to repair
        discarded = len(data) - end
        if discarded:
            f.truncate(end)
    if discarded:
        logging.warning(
            "%s: discarded %d torn/unparseable byte(s) from the final line(s) "
            "on resume -- the row(s) they held will be regenerated",
            jsonl_path, discarded,
        )
    return discarded


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


def dedupe_cell_rows(rows: Iterable[dict]) -> list[dict]:
    """Collapse ``kind: "cell"`` rows to one row per cell key: earliest surviving attempt.

    ``_existing_keys`` deliberately re-runs a cell whose only recorded row is an
    ``"exception"`` verdict (the exception may have come from the VERIFIER, so
    the candidate proof was never checked), and a resumed sweep APPENDS that
    retry rather than replacing the row -- so a lane that resumed past even one
    exception legitimately carries more than one row for the same cell key.
    Counting rows instead of cells makes a retried cell read as pass 1/2 (50%)
    instead of 1/1, and inflates ``cmd_analyze``'s pass@N ``N`` to the row count
    rather than the replicate count. This function is the single place that
    undoes that: callers aggregate over its output instead of over raw rows.

    Grouping mirrors `_existing_keys`' own field names and ``.get`` defaults
    exactly (not this module's stricter ``_row_key`` call sites elsewhere,
    which coerce types and use different sentinels) so the two agree on what
    counts as "the same cell" for exactly the rows `_existing_keys` itself
    would re-run.

    Parameters
    ----------
    rows : iterable of dict
        Already-parsed ``kind: "cell"`` rows, in file order. Passing a row of
        any other ``kind`` is a caller error this function does not guard
        against -- sanity rows have no cell identity and are the callers'
        business (see the module's callers, which filter by ``kind`` first).

    Returns
    -------
    list of dict
        One row per distinct cell key, in the RELATIVE order the surviving
        (or, failing that, first) row for that key appeared in `rows`. For a
        key with at least one non-``"exception"`` row: the EARLIEST such row,
        matching ``notebooks/deduction/analysis/power_analysis.grade_verdicts``'s
        earliest-surviving-attempt-wins rule. For a key whose every row is an
        ``"exception"``: the FIRST row, so an exception-only cell still counts
        once (in the ``exc`` column) rather than vanishing from the aggregate
        entirely.

    Notes
    -----
    Does not mutate `rows` or its dict elements. O(n) in the number of rows.
    """
    rows_by_key: dict[tuple, list[dict]] = {}
    order: list[tuple] = []  # first-seen order of keys, for a stable return order
    for row in rows:
        key = _row_key(
            row.get("model", ""), row.get("theorem_id", ""),
            int(row.get("k", -1)), row.get("rung", ""),
            int(row.get("replicate_idx", -1)),
        )
        if key not in rows_by_key:
            order.append(key)
        rows_by_key.setdefault(key, []).append(row)

    deduped: list[dict] = []
    for key in order:
        group = rows_by_key[key]
        surviving = next((r for r in group if r.get("verdict") != "exception"), None)
        deduped.append(surviving if surviving is not None else group[0])
    return deduped


def _sanity_done(jsonl_path: Path) -> dict[str, str]:
    """Map theorem name to its recorded sanity verdict from the JSONL (last wins).

    Verdicts, not just names, so a resumed sweep can RE-APPLY the gate: a
    theorem whose ground truth failed to replay (`SANITY_FAILURE_VERDICTS`)
    stays excluded rather than falling through to cell generation because its
    gate row exists.

    A recorded ``"exception"`` sanity row is the one case that does NOT stay
    excluded on resume, since `SANITY_FAILURE_VERDICTS` no longer contains it
    (see that constant's Design comment) -- an infrastructure hiccup on a past
    sweep must not permanently blank the theorem out of the study. This
    function still returns that row's verdict faithfully; it is the caller's
    gate-membership check, not this function, that now lets it through. Note
    also this function does NOT trigger a re-replay of an already-recorded
    ``"exception"`` (or any other) sanity row -- resume never re-runs
    `replay_ground_truth` for a theorem with an existing row of ANY verdict,
    only the cell-generation decision changes. Re-replaying would append a
    second sanity row per theorem, which would break
    `scripts/deduction/merge_lean_shards.py`'s gate on the total sanity-row
    count against `EXPECTED_SANITY_ROWS`.
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
    # Distinct from "·"/"?"/"X": a glyph of its own so a summary reader can
    # tell "the model answered and Lean judged it incomplete/given-up" apart
    # from "the model answered nothing" at a glance, without reading the
    # verdict column.
    "no_answer": "∅",
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
#
# "exception" ALSO passes through now (it did not before). An exception from
# `replay_ground_truth` is a statement about the INFRASTRUCTURE that tried to
# replay the ground truth -- an unset `SMOLBENCH_MATHLIB_ROOT`, a REPL start
# race, a transient connection drop -- never a positive finding that the
# recorded ground truth itself is unreplayable; contrast "lean_error" (Lean
# read the proof and rejected a step). ("replay_failed" is not reachable here
# at all -- see `verify.ReplayResult`'s docstring: a full-proof replay never
# produces it.) Gating on "exception" used to punish exactly the wrong failure: a
# theorem sanity-failed once with "exception" was excluded from cell
# generation FOREVER, on every later resume (`_sanity_done` re-applies this
# frozenset, it does not just skip a re-replay), with no escape short of
# `--force-rerun` on the whole lane -- so a single unset env var on one launch
# could permanently blank a theorem out of the study. See
# `replbackend.open_session`'s own Design comment (~lines 908-917), which
# makes the identical argument for why an unset `SMOLBENCH_MATHLIB_ROOT` must
# be translated to `ReplError` (-> "exception") rather than left as the
# `RuntimeError` that `verify.verify_proof_tail` would read as
# "replay_failed": both call sites agree an infrastructure misconfiguration
# must not be recorded as -- or treated as -- a broken ground truth. This
# frozenset leaving "exception" out is what actually delivers on that
# agreement for the sanity gate; before this change it did not.
#
# Deliberately NOT changed: a recorded "exception" sanity row is NOT
# re-replayed on resume -- the gate below simply no longer EXCLUDES the
# theorem because of it, so cell generation runs the next time the theorem is
# reached in a sweep. Re-replaying it would append a SECOND sanity row for
# the same theorem, and `scripts/deduction/merge_lean_shards.py` gates the
# merge on the total sanity-row count against `EXPECTED_SANITY_ROWS` -- a
# duplicate would trip that gate. See `_sanity_done`'s docstring for where a
# reader of the resume path will find this.
#
# What remains in the set: verdicts that POSITIVELY say the recorded ground
# truth is broken (Lean rejected or could not close a REPLAYED step of the
# theorem's OWN recorded proof) -- not verdicts that merely say the attempt to
# find that out failed.
#
# "no_answer" is deliberately NOT a member either, but for an unrelated
# reason: it is unreachable from `replay_ground_truth` (a ground-truth replay
# has no LLM candidate tail to be empty -- see `verify.Verdict`'s taxonomy
# comment), so it has no meaning as a sanity verdict at all. This frozenset's
# exact contents are pinned by a test.
SANITY_FAILURE_VERDICTS: frozenset[str] = frozenset(
    {"lean_error", "incomplete", "given_up", "replay_failed"}
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

#: The re-collection's S3 key prefix. The OLD published study lives under
#: `deduction/runs` and must never be written again -- see `spool_prefix`.
DEDUCTION_SPOOL_PREFIX: str = "deduction_postcutoff/runs"
#: The published pre-cutoff study's prefix. Named only so `spool_prefix` can
#: refuse it; analysis of that study passes it explicitly on a reader's
#: --spool-prefix flag.
LEGACY_SPOOL_PREFIX: str = "deduction/runs"

#: The OLD published study's pinned shape: 300 theorems x 4 rungs, unevenly
#: rendered (not every theorem/rung pair yields a cell) -> 944 cells; one
#: sanity row per theorem. Kept as the DEFAULT for the audit/merge/split
#: scripts so today's behaviour is unchanged -- asserted rather than
#: discovered, so a shrunken spool fails loudly instead of quietly
#: re-baselining. The post-cutoff pool may differ in size, so every consumer
#: of these numbers also takes a CLI override rather than importing them
#: unconditionally.
EXPECTED_THEOREMS: int = 300
EXPECTED_CELLS: int = 944
EXPECTED_SANITY_ROWS: int = 300


def spool_prefix() -> str:
    """Resolve the S3 key prefix writers/readers use for deduction spool runs.

    Reads `LEAN_SPOOL_PREFIX` from the environment on every call -- never
    cached, never resolved at import time -- so that a caller can flip the
    prefix between invocations within one process (tests do exactly this).
    An empty or unset value falls back to `DEDUCTION_SPOOL_PREFIX`, the
    re-collection's prefix.

    The resolved value is stripped of surrounding whitespace and any
    trailing "/", so callers may append their own "/" without risking a
    doubled separator.

    Returns
    -------
    str
        The normalized prefix, never ending in "/".

    Raises
    ------
    ValueError
        If the resolved prefix equals `LEGACY_SPOOL_PREFIX` (the published
        pre-cutoff study's location) and `LEAN_ALLOW_LEGACY_PREFIX` is not
        set to `"1"`. Writing to the legacy prefix again would silently
        overwrite the published, unrecoverable record in the append-only
        results bucket -- so this is a hard refusal, not a warning, with an
        explicit escape hatch for the one legitimate case (a reader
        explicitly analysing the old study still goes through the
        `--spool-prefix` flag on that path, not this env var).
    """
    raw = os.environ.get("LEAN_SPOOL_PREFIX", "").strip()
    resolved = raw.rstrip("/") if raw else DEDUCTION_SPOOL_PREFIX
    if resolved == LEGACY_SPOOL_PREFIX:
        if os.environ.get("LEAN_ALLOW_LEGACY_PREFIX") != "1":
            raise ValueError(
                f"refusing to resolve spool_prefix() to the published "
                f"pre-cutoff study's prefix ({LEGACY_SPOOL_PREFIX!r}) -- "
                "writing there again would silently overwrite the "
                "unrecoverable published record in the append-only results "
                "bucket. Set LEAN_ALLOW_LEGACY_PREFIX=1 to override, or "
                "(for read-only analysis) pass --spool-prefix explicitly."
            )
    return resolved


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
    breakdown (``lerr``/``incp``/``gvup``/``rplf``/``exc``/``noans``), ``l3``,
    then average prompt/completion tokens and wall time. ``l3`` counts CELLS whose
    ``candidate_proof`` holds at least one Lean 3 relic (`lean3.find_relics`),
    regardless of verdict — the endpoint `lean3.corrupt_tail`'s SFT intervention
    aims to drive to zero.

    Notes
    -----
    Cell rows are deduped through `dedupe_cell_rows` before counting (a resumed
    lane may carry an exception row and its retry for the same cell key; see
    that function's docstring), so the header's "N cells" and every per-cell
    ``n`` already reflect distinct cells, not raw rows.

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
            "no_answer": 0,
            "unverified": 0,
            "tok_in": 0, "tok_out": 0, "ms": 0, "l3": 0,
        }
    )
    n_sanity_pass = 0
    n_sanity_fail = 0
    n_sanity_skipped = 0
    # Cell rows are collected here, not aggregated inline, so `dedupe_cell_rows`
    # can collapse an exception-then-retry pair for the same cell key (see its
    # docstring) BEFORE this table's "N cells" header count and per-cell tallies
    # below ever see the raw row count. A run's all_rows.jsonl is thousands of
    # rows, not millions, so materializing the cell subset is cheap next to the
    # gzip+JSON `AlignMap.load` above.
    cell_rows: list[dict] = []
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
                    # "skipped" (NullVerifier), "exception" (infrastructure --
                    # SANITY_FAILURE_VERDICTS deliberately excludes it, see
                    # that constant's Design comment), and any future
                    # pass-through verdict: the gate deferred or the attempt
                    # to check it failed, but nothing POSITIVELY failed.
                    n_sanity_skipped += 1
                continue
            cell_rows.append(r)

    # `n_rows` (this function's "N cells" header count) is the DEDUPED cell
    # count -- a lane that resumed past an exception must read as one cell,
    # not two. See `dedupe_cell_rows`'s docstring for the full rationale.
    n_rows = 0
    for r in dedupe_cell_rows(cell_rows):
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
        f"{'rate':>6} {'lerr':>5} {'incp':>5} {'gvup':>5} {'rplf':>5} {'exc':>4} {'noans':>5} {'l3':>5} "
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
            f"{c['given_up']:>5} {c['replay_failed']:>5} {c['exception']:>4} "
            f"{c['no_answer']:>5} {c['l3']:>5} "
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
# Inner cell loop — shares one Lean REPL session across all rungs/models/
# replicates at a single (theorem, k). Caller wraps in a try/except for open
# failures.
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
    """Open a Lean REPL session at (theorem, k); run all cells. Returns (n_written, n_ok, n_skipped).

    `cell_whitelist=None` applies no extra filtering; otherwise a cell whose row
    key is not a member is skipped exactly like an already-`done_keys` one and
    counted in the same `n_skipped`, indistinguishably (see `sweep` and
    `load_cell_whitelist`).

    Filtering happens BEFORE `verifier.open_at_step`, and an empty pending list
    returns without opening it (as `_run_cells_at_step_concurrent` does): a
    resumed sweep whose cells are all done would otherwise pay a full REPL
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
        `max_tokens`, `concurrent_gen`, `max_concurrency`, `skip_trivial`,
        `theorem_workers`, plus the generation defaults documented in the
        module docstring (`seed`, `dojo_timeout`, `request_timeout`,
        `max_retries`, `models[i].provider`).
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
        Returned only when every requested `LEAN_CELL_WHITELIST` key (if any)
        was reconciled -- see Raises.

    Raises
    ------
    RuntimeError
        When ``LEAN_CELL_WHITELIST`` is active and, after this call's writer
        has closed, one or more requested cell keys are still absent from
        `all_rows.jsonl` (see the whitelist paragraph under Notes). Raised
        only after `manifest.json` (with a populated ``whitelist_missed``)
        and `analysis.txt` have both been (re)written, so the record of what
        went missing survives the exception that reports it.

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

    A requested key can still be UNREACHABLE even after a well-formed
    whitelist is accepted -- e.g. it names a theorem outside the configured
    `theorems` selection, a rung this sweep's config never renders, or a
    theorem whose sanity gate fails. After the generation loop, `sweep`
    reconciles the whitelist against `_existing_keys(all_rows_path)`
    (recomputed fresh, AFTER the writer has closed) and raises `RuntimeError`
    if any requested key is still missing, rather than returning 0 silently.
    This is fatal, not a warning: `notebooks/deduction/run_study.py` stamps
    ``hash_cell_keys(cell_whitelist)`` into `manifest.json` as a claim that
    THIS EXACT SET of cells was collected, and a silent exit-0 on an
    unreachable key would make that stamped claim false with no record of the
    discrepancy. Every missed key is logged individually at ERROR level
    (capped at `WHITELIST_MISS_LOG_CAP`) and recorded verbatim, sorted, under
    ``manifest.json["whitelist_missed"]`` -- present (possibly empty)
    whenever a whitelist is active at all, so a reconciled-clean run
    (``[]``) is distinguishable from an older manifest that predates this
    check (key absent entirely).

    `traced_root_present` (bool) is always recorded in `manifest.json`,
    whether or not a whitelist or `skip_trivial` is active: it is provenance
    about the BOX this run executed on (whether `premises._traced_root()`
    resolved a cached, traced mathlib4 checkout), not about `config`, since a
    reader of an archived run has no other way to tell which regime the run
    executed under. When `skip_trivial` is on and no traced root is present,
    `sweep` also logs a WARNING at start: `premises.body_with_proof` then
    degrades to the corpus's stored `Premise.code`, under which
    `is_trivial_rung` can judge hint:2, hint:3, and noise:3 trivial, and this
    sweep will NOT generate those cells -- so which cells a run produces can
    depend on a directory (``~/.cache/lean_dojo``, independent of
    ``SMOLBENCH_LEAN_DATA``) outside the results tree.
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
    dojo_timeout = int(config.get("dojo_timeout", DEFAULT_DOJO_TIMEOUT))
    concurrent_gen = bool(config.get("concurrent_gen", True))
    max_concurrency = int(config.get("max_concurrency", 12))
    skip_trivial = bool(config.get("skip_trivial", True))
    theorem_workers = int(config.get("theorem_workers", 1))
    # Fix 13-18: default 0, matching `theorems.seed`'s own default (see
    # `_select_theorems`) and `notebooks/deduction/run_study.py`'s driver
    # config -- NOT `run_cell`'s separate `seed` PARAMETER, a different entry
    # point with its own callers, which keeps its documented default of 1776
    # (see this module's docstring). A driver-side `LEAN_SEED` (landing in a
    # different package) is meant to derive BOTH the theorem-selection seed
    # and this decode seed from one value; this default exists so a config
    # that omits `seed` cannot silently disagree with that single value.
    base_seed = int(config.get("seed", 0))
    request_timeout = int(config.get("request_timeout", 1800))
    max_retries = int(config.get("max_retries", 4))

    # Fix 13-09 (runner half): whether the traced mathlib4 checkout that lets
    # `premises.body_with_proof` render full premise source -- and therefore
    # lets `is_trivial_rung` correctly judge a rung trivial -- is present on
    # THIS box, right now. Lazy import: `premises` is otherwise reached in
    # this package only through `context`'s own lazy imports (see that
    # module's Design comments on `.premises`), so a top-level import here
    # would add a new eager dependency edge this module doesn't otherwise
    # have.
    from . import premises
    traced_root_present = premises._traced_root() is not None
    if skip_trivial and not traced_root_present:
        logging.warning(
            "skip_trivial is on but premises._traced_root() found no cached, "
            "traced mathlib4 checkout (expected a "
            "leanprover-community-mathlib4-<commit>/mathlib4 directory under "
            "~/.cache/lean_dojo -- a cache independent of SMOLBENCH_LEAN_DATA, "
            "which only controls the corpus.jsonl dataset dir). Without it, "
            "body_with_proof() degrades to the corpus's stored Premise.code, "
            "under which is_trivial_rung can judge hint:2, hint:3, and "
            "noise:3 trivial -- so this sweep will NOT generate those cells. "
            "The set of cells a run produces therefore depends on a "
            "directory outside the results tree, and two boxes running the "
            "identical config can disagree about which cells exist."
        )

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
        # Provenance about the BOX this run executed on, not about `config`
        # (see this function's Notes) -- recorded unconditionally, at the top
        # level alongside run_name/started_at, so an archived run's reader
        # can tell which regime it was collected under without re-deriving
        # it.
        "traced_root_present": traced_root_present,
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

    # Fix 13-07: repair a torn final line BEFORE opening for append, not
    # after -- see `_repair_torn_tail`'s docstring for why a append onto an
    # unrepaired torn tail welds two records into one corrupt MIDDLE line.
    # Unconditional (not gated on `resume`): `notebooks/deduction/run_study.py`
    # renames the old file aside before a `resume=False` run, which normally
    # makes this a no-op there, but if that rename is ever skipped, appending
    # onto a torn prefix would be just as wrong under `resume=False`.
    _repair_torn_tail(all_rows_path)

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
                    # Design: log marker renamed from the old `DOJO-OPEN-FAIL`
                    # (fix 13-22) -- checked `scripts/`, `.claude/skills/`,
                    # `notebooks/`, and every `README*.md` for a dependency on
                    # the old spelling before renaming; none matched anything
                    # but this line itself, unlike `dojo_timeout` (kept:
                    # see `DEFAULT_DOJO_TIMEOUT`'s Design comment) which is
                    # load-bearing in committed sweep YAML and archived
                    # `manifest.json` config blocks.
                    with print_lock:
                        print(
                            f"  REPL-OPEN-FAIL {theorem.full_name} k={k}: "
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

    # Fix 13-12: reconcile LEAN_CELL_WHITELIST against what `all_rows.jsonl`
    # now accounts for. `_existing_keys` is recomputed HERE -- after the
    # `with all_rows_path.open("a") as all_rows:` block above has exited and
    # the file is closed -- rather than reusing `done_keys` (a snapshot taken
    # BEFORE this call's own writes). Recomputing fresh is the simplest
    # correct source of truth: it is exactly "which cells the rows file now
    # accounts for", covering both this run's fresh writes and any prior
    # resume in one measurement, which is precisely what "was every
    # whitelisted cell actually collected" needs to ask. Deliberately at the
    # END, not checked early and aborted: cells that ARE reachable must still
    # get generated and banked even when others in the same whitelist are
    # not (see this function's Notes).
    whitelist_missed: list[tuple] = []
    if cell_whitelist is not None:
        actually_present = _existing_keys(all_rows_path)
        whitelist_missed = sorted(cell_whitelist - actually_present)
        # Canonical list-of-lists encoding, matching `hash_cell_keys`'s own
        # convention, so a tuple key and its JSON round-trip compare equal.
        # Recorded even when empty (`[]`) -- an ABSENT key (an older run
        # predating this check, or a whitelist-free run) must not be
        # confused with a RECONCILED-and-clean one; see this function's
        # Notes.
        manifest["whitelist_missed"] = [list(k) for k in whitelist_missed]

    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    write_run_analysis(run_dir)

    if whitelist_missed:
        # Log every missed key so an operator can see WHICH cells were
        # unreachable, not just how many; capped because a whitelist can
        # legitimately name thousands of cells and dumping all of them into
        # the log is unreadable. The full list survives the cap regardless,
        # in `manifest.json["whitelist_missed"]` (already written above).
        shown = whitelist_missed[:WHITELIST_MISS_LOG_CAP]
        for key in shown:
            logging.error("whitelist cell unreachable: %s", list(key))
        n_suppressed = len(whitelist_missed) - len(shown)
        if n_suppressed > 0:
            logging.error(
                "... %d more unreachable whitelist cell(s) suppressed above "
                "(full list in manifest.json['whitelist_missed'])",
                n_suppressed,
            )
        # Fatal, not a warning: `notebooks/deduction/run_study.py` stamps
        # `hash_cell_keys(cell_whitelist)` into manifest.json as a claim that
        # this exact set of cells was collected. Returning 0 here (the prior
        # behaviour) would make that stamped claim false with no record of
        # the discrepancy -- so this raises instead, but only AFTER
        # manifest.json (with whitelist_missed populated) and analysis.txt
        # have both been (re)written above, so the record of what went wrong
        # is not itself lost with the exception.
        raise RuntimeError(
            f"LEAN_CELL_WHITELIST={cell_whitelist_path!r}: "
            f"{len(whitelist_missed)} of {len(cell_whitelist)} requested "
            "cell(s) were never generated (unreachable by this sweep's "
            "theorems/rungs/models or dropped by a failed sanity gate); "
            f"full list recorded in {run_dir / 'manifest.json'} under "
            "'whitelist_missed'"
        )

    print(
        f"\n{n_ok}/{n_written} success  ({n_skipped} skipped)\n"
        f"output: {run_dir}\n"
        f"analysis: {run_dir / 'analysis.txt'}",
        flush=True,
    )
    return n_written
