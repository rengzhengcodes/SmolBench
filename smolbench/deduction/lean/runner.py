"""Run the eval loop: theorem × step k × context rung × N replicates.

Two entry points, both used by `cli.py`: `run_cell` (one cell, own Lean REPL
session) and `sweep` (YAML sweep, one REPL session per (theorem, k)).

Generation goes through `ChatClient.complete` on a provider resolved per
model entry (`_provider_for`), not `INFERENCE_PROVIDER`, so one sweep can mix
providers. Shared config defaults: `seed` 0 (matches `theorems.seed` and
`run_study.py`'s driver config, so an omitted key can't disagree with either
-- `run_cell`'s own `seed` parameter keeps its own default of 1776);
`dojo_timeout` `DEFAULT_DOJO_TIMEOUT`; `request_timeout` 1800s (`ChatClient`'s
120s default truncates long CoT mid-stream); `max_retries` 4, so a wedged
endpoint can't spin forever inside an open REPL session.

This module never verifies Lean proofs itself -- `.verify` does, lazily
imported through `_default_verifier()` -- so a Lean toolchain is only needed
when no fake verifier is passed in.
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
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, TextIO

import smolbench
from smolbench.evals.provider import provider_module
from smolbench.evals.retired_markers import is_retired

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

# `lean3` imports eagerly: stdlib-only, and `write_run_analysis` always
# needs it for the `l3` column, so there is no lazy-import seam to keep.

# No top-level `from .verify import ...`: `.verify` needs `lean_interact`,
# not always installed. `_default_verifier` below is the lazy seam for it.


#: Seconds for `run_cell`/`sweep`'s Lean REPL session (also `cli`'s
#: `run-cell --timeout`). Not lower: a timeout is recorded as an
#: `"exception"` verdict, so a tight budget would silently convert
#: slow-but-real theorems into infrastructure failures.
DEFAULT_DOJO_TIMEOUT: int = 600


def results_root() -> Path:
    """Root directory for sweep/run-cell output; may not exist yet.

    ``SMOLBENCH_LEAN_RESULTS`` if set, else anchored to the installed package,
    never cwd (mirrors `corpus.data_root`); read at call time.
    """
    override = os.getenv("SMOLBENCH_LEAN_RESULTS")
    if override:
        return Path(override)
    return Path(smolbench.__file__).resolve().parents[1] / "notebooks" / "deduction" / "results"


def _default_verifier() -> Any:
    """Import `.verify` at call time; raises `ImportError` without `lean_interact`.

    Protocol: `open_at_step`, `try_tail`, `replay_ground_truth`,
    `verify_proof_tail`, `ProofResult`. Tests substitute `FakeVerifier`;
    generation-only sweeps use `NullVerifier`.
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
    verifier: Any = None,
) -> Iterable[dict]:
    """Yield one JSONL-serializable row per replicate for one (theorem, k, chain, level) cell.

    Opens its own Lean REPL session; unlike `sweep`, `complete()` is not
    wrapped in try/except here, since this is single-shot and non-resuming, so
    a generation failure propagates instead of becoming an exception row.

    Rows match the sweep row schema minus `api_model` (no display name here).

    Parameters
    ----------
    provider : str
        Provider identifier for model completion.
    model : str
        Model identifier for model completion.
    theorem : BenchmarkTheorem
        Theorem to prove.
    k : int
        Theorem context index.
    chain : Chain
        Prompt chain for rendering the theorem.
    level : int
        Prompt rung level.
    n_replicates : int
        Number of completion replicates to generate.
    temperature : float, optional
        Sampling temperature for model completion.
    max_tokens : int, optional
        Maximum generated tokens per completion.
    dojo_timeout : int, optional
        kept spelled this way, not `repl_timeout` -- pinned across
        `run_cell`, `sweep`, and `cli`'s defaults (see `DEFAULT_DOJO_TIMEOUT`).
    seed : int, optional
        replicate `i` decodes at `seed + i`, so the replicate index, not
        theorem/rung/model, is the seed-varying axis.
    request_timeout : int, optional
        Completion request timeout in seconds.
    max_retries : int, optional
        Maximum completion retry attempts.
    verifier : Any, optional
        `None` resolves `_default_verifier()`; tests pass a fake.

    Yields
    ------
    dict
        One JSONL-serializable row per replicate.
    """
    if verifier is None:
        verifier = _default_verifier()

    rendered = render(theorem, k, chain, level)
    user_prompt = build_user_prompt(rendered)

    mod = provider_module(provider)
    try:
        ctx_len = mod.get_model_context_length(model)
    except Exception as exc:  # noqa: BLE001
        # Same rationale as `_ctx_len_for`: a catalog lookup failure must not abort the cell.
        ctx_len = 10**9
        print(f"warning: context-length lookup failed for {model} on {provider}: {exc}", flush=True)

    for replicate_idx in range(n_replicates):
        replicate_seed = seed + replicate_idx
        t0 = time.monotonic()
        # sweep, not run_cell, owns exception rows (see this function's docstring).
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


def jsonl_line(row: dict) -> str:
    """The one JSONL spelling every writer here uses (handles included)."""
    return json.dumps(row, ensure_ascii=False) + "\n"


def write_jsonl(rows: Iterable[dict], path: Path) -> int:
    """Append JSONL rows to a path and return their count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a") as f:
        for r in rows:
            f.write(jsonl_line(r))
            n += 1
    return n


def new_run_id() -> str:
    """Return a timestamped, short-unique run identifier."""
    return time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]


def _require_all_postcutoff(pool: list[BenchmarkTheorem]) -> None:
    """Raise `ValueError` unless every theorem in `pool` carries `BenchmarkTheorem.postcutoff`.

    Names the first 5 offending theorems plus a total count, so a large bad
    pool doesn't dump thousands of names into the message.

    Parameters
    ----------
    pool : list[BenchmarkTheorem]
        Theorems to validate for post-cutoff status.
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

    Parameters
    ----------
    spec : dict
        Configuration `theorems` block.
    cell_whitelist : frozenset[tuple] | None, optional
        Narrows the pool to theorems owning at least one of its cell keys; it's a parameter,
        not a `spec` field, because `sweep` loads it once from `LEAN_CELL_WHITELIST` rather than
        duplicating it into config.

    Returns
    -------
    list[BenchmarkTheorem]
        Selected theorems.

    Raises
    ------
    ValueError
        For an unknown `source`, a malformed `shard`, or (when `require_postcutoff` is set) a
        pool containing a non-post-cutoff theorem.
    """
    require_postcutoff = bool(spec.get("require_postcutoff", False))
    source = spec.get("source", "replay_passing")
    kind = spec.get("kind", "random")
    split = spec.get("split", "val")
    max_tactics = int(spec.get("max_tactics", 0))
    limit = int(spec.get("limit", 0))
    seed = int(spec.get("seed", 0))

    # Runs before the pool loads, redundant with the per-theorem check below:
    # the old LeanDojo Benchmark 4 snapshot has no post-cutoff tail at all, so
    # no sampling/seed/split choice over it can ever produce a compliant item.
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

    # Checked on the raw pool, before sampling/sharding/whitelisting (which
    # only ever remove rows): `random.Random(seed).sample` is order- and
    # population-sensitive, so whether the draw misses a pre-cutoff row must
    # not decide compliance.
    if require_postcutoff:
        _require_all_postcutoff(pool)

    if max_tactics > 0:
        pool = [t for t in pool if 1 <= len(t.traced_tactics) <= max_tactics]

    if limit > 0 and len(pool) > limit:
        rng = random.Random(seed)
        pool = rng.sample(pool, limit)

    # Applied after the seeded sample: every shard computes the identical pool
    # and takes a disjoint slice, so the shards' union equals the unsharded
    # selection. Boundary is per-theorem, keeping one theorem's rungs and
    # sanity row on a single shard.
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

    # Applied last, at the theorem level (mirrors the shard above). Dropping
    # whole theorems here, not just per-cell later, skips the sanity replay
    # and REPL session for every untouched theorem -- needed for an
    # n=200-cell rerun against a 300-theorem pool.
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
# See `sweep`'s docstring for where it is consulted.
# ---------------------------------------------------------------------------


def load_cell_whitelist(path_str: str) -> frozenset[tuple]:
    """Load and validate a `LEAN_CELL_WHITELIST` JSON file into a key set.

    Entries are 5-element ``[model, theorem, k, rung, replicate_idx]`` arrays,
    matching `_row_key`'s order so keys compare equal to `sweep`'s.

    Parameters
    ----------
    path_str : str
        Path to the JSON file.

    Returns
    -------
    frozenset[tuple]
        Cell keys in `_row_key` order; duplicates collapse, source order is not preserved.

    Raises
    ------
    ValueError
        (naming `path_str`) on any read/parse/shape problem: a missing or malformed file must
        abort before generating a cell, not degrade into a full, expensive re-run.
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

    Keys are sorted and coerced to lists first, so a tuple and an equal-valued
    list (as `load_cell_whitelist` returns) fingerprint identically. Used by
    `run_study.py` to stamp "this exact set of cells" into a manifest;
    change-detection, not security.

    Parameters
    ----------
    keys : Iterable[tuple]
        Cell keys to encode canonically.

    Returns
    -------
    str
        Lowercase hex SHA-256 fingerprint.
    """
    canonical = json.dumps(
        sorted(list(key) for key in keys), separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


#: Cap on unreachable `LEAN_CELL_WHITELIST` keys `sweep` logs individually at
#: ERROR level. Bounds only the log stream -- the full list always lands in
#: `manifest.json["whitelist_missed"]` regardless.
WHITELIST_MISS_LOG_CAP: int = 50


# ---------------------------------------------------------------------------
# Sweep config files. One loader, two callers (`cli.cmd_run_sweep --config`
# and `run_study.py`'s `build_config`), kept here so the driver need not
# import the CLI or grow its own `yaml.safe_load` that could drift.
# ---------------------------------------------------------------------------


def load_sweep_config(path: str | Path) -> tuple[dict, str]:
    """Load a sweep config YAML file; return it with a SHA-256 of the raw bytes.

    Requires a YAML mapping: `sweep` indexes `config` by key, so a list or the
    `None` an empty file parses to would surface much later as a confusing
    `AttributeError`. Hashes the SAME bytes handed to the parser (one read),
    so the digest can't drift from what was parsed, and changes when a
    COMMENT changes -- deliberate, since `sweep.yaml`'s rationale comments are
    part of what a run's provenance claims. `yaml` imports locally: this
    module is also imported by callers with no reason to require PyYAML.

    Parameters
    ----------
    path : str | Path
        YAML configuration file.

    Returns
    -------
    tuple[dict, str]
        Parsed configuration and SHA-256 of its raw bytes.
    """
    import yaml

    config_path = Path(path)
    # One read: the bytes hashed are exactly the bytes yaml.safe_load() sees.
    raw = config_path.read_bytes()
    sha256_hex = hashlib.sha256(raw).hexdigest()
    config = yaml.safe_load(raw)
    if not isinstance(config, dict):
        raise ValueError(
            f"sweep config {str(config_path)!r} must be a YAML mapping of "
            f"config keys; parsed as {type(config).__name__} "
            "(an empty file parses as NoneType)"
        )
    return config, sha256_hex


def _repair_torn_tail(jsonl_path: Path) -> int:
    """Truncate a torn or unparseable FINAL line off `jsonl_path`, in place.

    Must run before `sweep` reopens `all_rows.jsonl` in append mode on resume:
    a SIGKILL mid-write can leave a half-written final line, and appending
    onto it welds the next row onto the torn prefix into one corrupt MIDDLE
    line -- recoverable as a tail, not once welded (`merge_lean_shards.py`
    hard-aborts on a mid-file parse failure). `_existing_keys` already
    tolerates a torn tail by skipping it, so the fix has to land before the
    append, not at read time.

    Repairs by checking the last line from the end (newline-terminated? does
    it parse as JSON?), truncating back and retrying on either failure, so a
    multi-line tear is still fully repaired. Reads and truncates once rather
    than rewriting surviving content back out, so a second crash can't lose
    rows that were never torn.

    Logs a WARNING on any repair.

    Parameters
    ----------
    jsonl_path : Path
        JSONL file to repair in place.

    Returns
    -------
    int
        Bytes discarded (``0`` means untouched, not "no file").
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


def read_jsonl_tolerating_torn_tail(path: Path) -> list[dict]:
    """Parse `path`'s rows, dropping a torn FINAL line; missing file -> ``[]``.

    Single reader for `all_rows.jsonl`-shaped files. Only the last line can be
    torn (a SIGKILL mid-append); dropped with a WARNING, not silently, so real
    corruption elsewhere still raises `json.JSONDecodeError` naming the line.

    Parameters
    ----------
    path : Path
        JSONL file to parse.

    Returns
    -------
    list[dict]
        Parsed rows, dropping a torn FINAL line; missing file -> ``[]``.
    """
    if not path.exists():
        return []
    # split("\n"), not splitlines(): the writer separates records on "\n" only,
    # while splitlines() also breaks on U+2028/U+0085, which json.dumps leaves
    # unescaped under ensure_ascii=False and a Lean error can carry.
    lines = path.read_text().split("\n")
    if lines and lines[-1] == "":
        lines.pop()  # the trailing "\n" terminates the last record, it is not one
    rows: list[dict] = []
    for lineno, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            if lineno != len(lines) - 1:
                raise json.JSONDecodeError(
                    f"corrupt row mid-file at line {lineno + 1}", line, exc.pos
                ) from exc
            logging.warning(
                "%s: torn (truncated) final line dropped -- the append-only "
                "writer regenerates it on resume", path,
            )
    return rows


def _cell_key(r: dict) -> tuple:
    """`_row_key` off a raw row, with the tolerant defaults resume decisions use."""
    return _row_key(
        r.get("model", ""), r.get("theorem_id", ""), int(r.get("k", -1)),
        r.get("rung", ""), int(r.get("replicate_idx", -1)),
    )


def group_cell_rows(rows: Iterable[dict], key: Callable[[dict], Any]) -> dict:
    """Group `rows` by ``key(row)``, first-seen key order (dicts preserve it)."""
    groups: dict = {}
    for row in rows:
        groups.setdefault(key(row), []).append(row)
    return groups


def _accounts_for_cell(r: dict) -> bool:
    """True if `r` is evidence its cell must NOT re-run -- see `_existing_keys`."""
    if r.get("verdict") == "exception":
        return False
    return (bool((r.get("candidate_proof") or "").strip())
            or int(r.get("prompt_tokens") or 0) > 0)


def _existing_keys(jsonl_path: Path) -> set[tuple]:
    """Read existing JSONL rows; return cell keys for cells that must NOT re-run.

    Only surviving (non-``exception``) rows count as evidence: a cell whose
    only record is an exception re-runs even with proof text, since the
    exception may have come from the verifier before the proof was checked.
    Among survivors: non-empty ``candidate_proof`` skips the cell; else
    ``prompt_tokens > 0`` also skips it (asked, returned nothing extractable
    -- that is data); else the cell re-runs. Re-running an asked-and-empty
    cell would resample until a proof happened to appear, inflating pass@1.
    ``prompt_tokens`` is also the signal `audit_run_completeness.py` uses.

    Parameters
    ----------
    jsonl_path : Path
        JSONL file containing existing rows.

    Returns
    -------
    set[tuple]
        Cell keys for cells that must NOT re-run.
    """
    cell_rows = [r for r in read_jsonl_tolerating_torn_tail(jsonl_path)
                 if r.get("kind") == "cell"]
    rows_by_key = group_cell_rows(cell_rows, _cell_key)
    return {key for key, rows in rows_by_key.items()
            if any(_accounts_for_cell(r) for r in rows)}


def dedupe_cell_rows(rows: Iterable[dict]) -> list[dict]:
    """Collapse ``kind: "cell"`` rows to one row per cell key: earliest surviving attempt.

    `_existing_keys` re-runs a cell whose only row is an exception (the
    exception may be from the verifier, so the candidate was never checked),
    and a resumed sweep APPENDS that retry -- so one cell key can carry more
    than one row. Counting rows instead of cells would inflate `cmd_analyze`'s
    pass@N (a retried cell reads as 1/2 instead of 1/1); callers aggregate
    over this function's output instead.

    Groups by `_existing_keys`' own field names/defaults, not this module's
    stricter `_row_key`, so the two agree on "same cell".

    Parameters
    ----------
    rows : Iterable[dict]
        Cell rows to deduplicate.

    Returns
    -------
    list[dict]
        The earliest non-exception row per key, or the first row if every row for that key is an
        exception (so it still counts once, not vanishes).
    """
    deduped: list[dict] = []
    for group in group_cell_rows(rows, _cell_key).values():
        surviving = next((r for r in group if r.get("verdict") != "exception"), None)
        deduped.append(surviving if surviving is not None else group[0])
    return deduped


def _sanity_done(jsonl_path: Path) -> dict[str, str]:
    """Map theorem name to its recorded sanity verdict from the JSONL (last wins).

    Verdicts, not just names, so resume can RE-APPLY the gate: a theorem whose
    ground truth failed to replay stays excluded rather than falling through
    because its gate row already exists. An `"exception"` row is the one
    verdict that does NOT stay excluded (not in `SANITY_FAILURE_VERDICTS`): an
    infra hiccup on a past run must not permanently blank a theorem out of the
    study -- the caller's gate check, not this function, lets it through.
    Never triggers a re-replay for an existing row of any verdict; a second
    sanity row per theorem would break `merge_lean_shards.py`'s `--expect-sanity` count gate.

    Parameters
    ----------
    jsonl_path : Path
        JSONL file containing sanity rows.

    Returns
    -------
    dict[str, str]
        Theorem names mapped to their recorded sanity verdicts.
    """
    return {r.get("theorem_id", ""): r.get("verdict", "")
            for r in read_jsonl_tolerating_torn_tail(jsonl_path)
            if r.get("kind") == "sanity"}


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
    fname = f"{slug_rung(row['rung'])}__{slug_model(row['model'])}.jsonl"
    write_jsonl([row], theorem_dir / "outputs" / fname)


# ---------------------------------------------------------------------------
# Summary generators (regenerable post-hoc)
# ---------------------------------------------------------------------------


#: verdict -> (glyph, sanity_failure, never_measured). Lives here, not in
#: `.verify` (which owns the taxonomy's prose and `Verdict` Literal), because
#: `.verify` imports `lean_interact` and this module must not. The two
#: derived sets below can't drift from this table.
#:
#: `sanity_failure` gates cell generation (`_process_one_theorem`): only a
#: POSITIVE finding that the recorded ground truth is unreplayable suppresses
#: it. "exception" (infra) and "skipped" (deferred NullVerifier replay) pass
#: through; "no_answer" is unreachable from `replay_ground_truth`.
VERDICTS: dict[str, tuple[str, bool, bool]] = {
    #                glyph  sanity_failure  never_measured
    "success":      ("✓",   False,          False),
    "lean_error":   ("✘",   True,           False),
    "incomplete":   ("·",   True,           False),
    "given_up":     ("?",   True,           False),
    # Distinct glyph: "answered but incomplete/given-up" differs from "answered nothing".
    "no_answer":    ("∅",   False,          False),
    "replay_failed": ("!",  True,           True),
    "exception":    ("X",   False,          True),
    # Generation-only sweeps: cells awaiting deferred verification.
    "unverified":   ("~",   False,          False),
    "skipped":      ("-",   False,          False),
}

_VERDICT_GLYPH = {v: row[0] for v, row in VERDICTS.items()}
SANITY_FAILURE_VERDICTS: frozenset[str] = frozenset(
    v for v, row in VERDICTS.items() if row[1])
#: Verdicts meaning Lean never actually ran (REPL never opened, or a
#: last-resort net fired) -- not a real pass or fail. Read by `lean_verify_rows.py`.
NEVER_MEASURED_VERDICTS: frozenset[str] = frozenset(
    v for v, row in VERDICTS.items() if row[2])

_CHAIN_ORDER = {"stepk": 0, "hint": 1, "noise": 2}


def _glyph(v: str) -> str:
    return _VERDICT_GLYPH.get(v, "?")


#: This study's S3 key prefix.
DEDUCTION_SPOOL_PREFIX: str = "deduction_postcutoff/runs"


def spool_prefix() -> str:
    """Resolve the S3 key prefix writers/readers use for deduction spool runs.

    Reads `LEAN_SPOOL_PREFIX` at call time, never cached, so a caller can flip
    the prefix between invocations within one process. Falls back to
    `DEDUCTION_SPOOL_PREFIX`; strips whitespace and a trailing "/".
    """
    raw = os.environ.get("LEAN_SPOOL_PREFIX", "").strip()
    return raw.rstrip("/") if raw else DEDUCTION_SPOOL_PREFIX


def reject_superseded_rows(paths: Iterable[str | Path]) -> None:
    """Reject any path whose FILE NAME carries a `retired_markers.RETIRED_MARKERS` marker.

    Also logs, since
    `write_theorem_summary` runs inside a per-theorem worker that -- under
    `theorem_workers > 1` -- swallows exceptions into one THEOREM-WORKER-FAIL
    line (serial runs propagate).

    Parameters
    ----------
    paths : Iterable[str | Path]
        Row-file paths to validate.

    Raises
    ------
    ValueError
        Naming every offending path, rather than warning and skipping: these files parse
        perfectly and would otherwise yield a complete, plausible, WRONG summary instead of a
        crash.
    """
    bad = [str(p) for p in paths if is_retired(p)]
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

    Regenerates wholesale; a no-op when `all_rows.jsonl` doesn't exist. `l3`
    counts cells whose `candidate_proof` holds a PARSE-LEVEL Lean 3 relic
    (`lean3.find_relics`), regardless of verdict -- the metric
    `lean3.corrupt_tail`'s repair training aims to drive to zero. Cell rows
    are deduped through `dedupe_cell_rows` first, so "N cells" and every
    per-cell `n` count distinct cells, not raw rows.

    Parameters
    ----------
    run_dir : Path
        Run directory containing `all_rows.jsonl`.
    """
    all_rows = run_dir / "all_rows.jsonl"
    if not all_rows.exists():
        return

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
    # Collected here, not aggregated inline, so `dedupe_cell_rows` can collapse
    # an exception-then-retry pair before the "N cells" count and per-cell
    # tallies below ever see the raw row count.
    cell_rows: list[dict] = []
    for r in read_jsonl_tolerating_torn_tail(all_rows):
        if r["kind"] == "sanity":
            if r.get("verdict") == "success":
                n_sanity_pass += 1
            elif r.get("verdict") in SANITY_FAILURE_VERDICTS:
                n_sanity_fail += 1
            else:
                # "skipped" (deferred) or "exception" (infra): nothing POSITIVELY failed.
                n_sanity_skipped += 1
            continue
        cell_rows.append(r)

    # Deduped cell count: a lane that resumed past an exception reads as one
    # cell, not two (see dedupe_cell_rows).
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
        if lean3.find_relics(r.get("candidate_proof") or ""):
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

    # The `l3` header cell names its own scope, so no marker line is needed.
    header = (
        f"{'rung':<10} {'model':<36} {'pass':>5}/{'N':<4} "
        f"{'rate':>6} {'lerr':>5} {'incp':>5} {'gvup':>5} {'rplf':>5} {'exc':>4} {'noans':>5} "
        f"{'l3(parse-level)':>16} "
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
            f"{c['no_answer']:>5} {c['l3']:>16} "
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
                   f"({m['tok_in']:,} in / {m['tok_out']:,} out tokens)  "
                   f"l3(parse-level)={m['l3']}")
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


def _run_cells_at_step_concurrent(
    *,
    all_rows: TextIO,
    theorem: BenchmarkTheorem,
    k: int,
    rungs: list[str],
    rendered_by_rung: dict,
    models_cfg: list[dict],
    n_replicates: int,
    temperature: float,
    max_tokens: int,
    provider_factory: Callable[[dict], tuple[Any, int]],
    base_seed: int,
    request_timeout: int,
    max_retries: int,
    done_keys: set,
    tdir: Path,
    dojo_timeout: int,
    verifier: Any,
    max_workers: int = 12,
    write_lock: threading.Lock | None = None,
    print_lock: threading.Lock | None = None,
    model_semaphores: dict[str, threading.Semaphore] | None = None,
    cell_whitelist: frozenset[tuple] | None = None,
    written_keys: set[tuple] | None = None,
) -> tuple[int, int, int]:
    """Fire all (rung, model, replicate) gen calls in parallel, verifying each
    on the shared Lean REPL session as responses arrive.

    Verify serializes (the REPL session is single-threaded); gen -- the
    dominant cost at ~1.3-3s/cell vs ~0.4s/verify -- fans out. A cell already
    in `done_keys` (or, with `cell_whitelist`, absent from it) is skipped; an
    empty pending list returns without opening the REPL session, so a
    fully-resumed (theorem, k) pays no Lean startup. Written rows
    `_existing_keys` would later count are added to `written_keys`, if given.

    Parameters
    ----------
    all_rows : TextIO
        Open JSONL output stream.
    theorem : BenchmarkTheorem
        Theorem being evaluated.
    k : int
        Tactic-step index.
    rungs : list[str]
        Rungs to evaluate.
    rendered_by_rung : dict
        Rendered prompts keyed by rung.
    models_cfg : list[dict]
        Model configuration entries.
    n_replicates : int
        Number of replicates per cell.
    temperature : float
        Generation temperature.
    max_tokens : int
        Maximum generation tokens.
    provider_factory : Callable[[dict], tuple[Any, int]]
        Creates a provider and its context length from a model configuration.
    base_seed : int
        Base seed for replicate generation.
    request_timeout : int
        Request timeout in seconds.
    max_retries : int
        Maximum request retries.
    done_keys : set
        Cell keys already completed.
    tdir : Path
        Per-theorem output directory.
    dojo_timeout : int
        Lean Dojo timeout in seconds.
    verifier : Any
        Verifier for generated proof tails.
    max_workers : int, optional
        Maximum concurrent generation workers.
    write_lock : threading.Lock | None, optional
        Serializes writes to `all_rows`.
    print_lock : threading.Lock | None, optional
        Serializes status output.
    model_semaphores : dict[str, threading.Semaphore] | None, optional
        Per-model generation semaphores.
    cell_whitelist : frozenset[tuple] | None, optional
        Allowed cell keys.
    written_keys : set[tuple] | None, optional
        Receives keys for rows `_existing_keys` would count.

    Returns
    -------
    tuple[int, int, int]
        Counts of written, successful, and skipped cells.
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
                    "key": key,
                    "rung": rung, "rendered": rendered,
                    "chain": chain, "level": level,
                    "user_prompt": user_prompt,
                    "mc": mc, "model": mc["model"], "provider": mc["provider"],
                    "replicate_idx": replicate_idx,
                    # Seed depends only on replicate index (see sweep), keeping
                    # cross-model comparisons at a cell seed-paired.
                    "seed": base_seed + replicate_idx,
                    "display_name": display_name,
                    "extra_params": mc.get("extra_params"),
                })

    if not pending:
        return n_written, n_ok, n_skipped

    # Submit slow (reasoning) cells first: the REPL session stays open until the
    # last gen completes, so front-loading them cuts per-theorem wall clock.
    # Optimisation only -- skipped at max_workers=1, where rows must land in
    # plain (rung, model, replicate) order.
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

    if max_workers > 1:
        pending.sort(key=lambda p: (
            rung_order[p["rung"]],
            0 if _is_reasoning(p["mc"]) else 1,
            model_order[id(p["mc"])],
            p["replicate_idx"],
        ))

    with verifier.open_at_step(theorem, k, timeout=dojo_timeout) as (dojo, state_at_k):
        executor = ThreadPoolExecutor(max_workers=min(max_workers, len(pending)))
        try:
            def _gated_complete(
                p: dict,
                mod: Any,
                sem: threading.Semaphore | None,
                *args: Any,
                **kwargs: Any,
            ) -> Any:
                # Stamped where generation begins, not at submit: at
                # max_workers=1 a submit-time stamp bills every earlier cell's
                # queue wait (and any semaphore wait) to this cell's gen_ms.
                if sem is None:
                    p["t_gen_start"] = time.monotonic()
                    return mod.complete(*args, **kwargs)
                with sem:
                    p["t_gen_start"] = time.monotonic()
                    return mod.complete(*args, **kwargs)

            future_to_pending = {}
            for p in pending:
                mod, ctx_len = provider_factory(p["mc"])
                # Fallback only: read if the future raises before
                # `_gated_complete` restamps, so `gen_ms` can never KeyError.
                p["t_gen_start"] = time.monotonic()
                sem = (model_semaphores or {}).get(p["display_name"])
                fut = executor.submit(
                    _gated_complete, p, mod, sem, p["user_prompt"], p["model"], p["seed"],
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

            # At max_workers=1, iterate in submission order instead of
            # `as_completed`: the latter yields finished futures in arbitrary
            # order, making the one-worker path's row order nondeterministic.
            arrivals = (list(future_to_pending) if max_workers == 1
                        else as_completed(future_to_pending))
            for fut in arrivals:
                p = future_to_pending[fut]

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
                    # Read after the wait, never before: at max_workers=1
                    # `arrivals` is submission order, so the worker may not
                    # have restamped `t_gen_start` yet at loop entry.
                    gen_ms = int((time.monotonic() - p["t_gen_start"]) * 1000)
                    row = {
                        **base_row,
                        "prompt_tokens": 0, "completion_tokens": 0,
                        "cache_read_tokens": 0, "cache_creation_tokens": 0,
                        # No server-reported stop reason since the request
                        # itself raised; key stays present so every row
                        # indexes finish_reason alike.
                        "finish_reason": None,
                        "gen_ms": gen_ms, "verify_ms": 0,
                        "candidate_proof": "", "raw_response": "",
                        "reasoning_content": None,
                        "verdict": "exception",
                        "lean_error": f"{type(exc).__name__}: {exc}",
                        "final_state_pp": None,
                    }
                else:
                    gen_ms = int((time.monotonic() - p["t_gen_start"]) * 1000)
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
                    all_rows.write(jsonl_line(row))
                    all_rows.flush()
                    if written_keys is not None and _accounts_for_cell(row):
                        written_keys.add(p["key"])
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


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------


def _provider_for(mc: dict) -> Any:
    """Resolve the provider module for one model-config entry.

    Explicit, not via the env-dispatched `provider.complete`: one process-wide
    `INFERENCE_PROVIDER` can't express a lineup mixing providers across
    `config["models"]`.

    Parameters
    ----------
    mc : dict
        Model configuration entry.

    Returns
    -------
    Any
        Provider module.
    """
    return provider_module(mc["provider"])


def _ctx_len_for(mc: dict, mod: Any) -> int:
    """Resolve a model's context window, tolerating catalog-lookup failures.

    Falls back to `10**9` on failure (timeout or unlisted model id), so
    `complete()`'s token-usage guard never fires for this model; a genuine
    overflow then surfaces later as that guard's `ValueError`, recorded
    per-cell as a resumable exception row rather than a hard abort.

    Parameters
    ----------
    mc : dict
        Model configuration entry.
    mod : Any
        Provider module.

    Returns
    -------
    int
        Model context window.
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


def sweep(config: dict, run_dir: Path, *, resume: bool = True, verifier: Any = None) -> int:
    """Run a sweep described by `config`; write per-theorem dirs under `run_dir`.

    Loops theorem, then k, then rung, then model, then replicate. One Lean REPL
    session per (theorem, k), shared across every branch from it; one further
    per-theorem session re-runs the full proof as a sanity gate.

    `LEAN_CELL_WHITELIST` (env, optional JSON file of cell keys): when set,
    only those cells generate, and a theorem owning none of them is dropped
    before its sanity gate runs. After the run, `sweep` reconciles the
    whitelist against what was written and raises `RuntimeError` on any
    unreachable key -- fatal, since `run_study.py` stamps
    `hash_cell_keys(cell_whitelist)` into `manifest.json` as a claim about
    exactly these cells; raised only after that file and `analysis.txt` are
    (re)written, so the claim's own falsification is on record.

    `traced_root_present` (in `manifest.json`): without a cached, traced
    mathlib4 checkout, `skip_trivial` judges fewer rungs trivial, so which
    cells a run produces can depend on a directory outside the results tree
    (logged as a WARNING at start).

    Parameters
    ----------
    config : dict
        Sweep configuration.
    run_dir : Path
        Directory for per-theorem outputs and run artifacts.
    resume : bool, optional
        Skips cells already recorded in `all_rows.jsonl` (`_existing_keys`).
    verifier : Any, optional
        Verifier for sanity replays and generated proof tails.

    Returns
    -------
    int
        Number of cells written.
    """
    if verifier is None:
        verifier = _default_verifier()

    # Loaded once, threaded into `_select_theorems` and
    # `_run_cells_at_step_concurrent`, so a bad file raises before spend.
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
    # Fail fast: pure module resolution, no network call, so a typo aborts
    # here instead of after the first theorem burns a real sanity replay.
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
    # Default 0, matching `theorems.seed` (see `_select_theorems`) and
    # `run_study.py`'s driver config -- not `run_cell`'s separate `seed`
    # parameter (its own default of 1776, see module docstring). Exists so a
    # config that omits `seed` can't silently disagree with the driver's value.
    base_seed = int(config.get("seed", 0))
    request_timeout = int(config.get("request_timeout", 1800))
    max_retries = int(config.get("max_retries", 4))

    # Whether a traced mathlib4 checkout (lets `body_with_proof` render full
    # premise source, so `is_trivial_rung` judges correctly) is present on
    # this box, right now. Lazy import: `premises` is otherwise reached only
    # through `context`'s own lazy imports; a top-level import here would add
    # an eager dependency edge this module doesn't otherwise have.
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
        # Provenance about the box, not `config` -- recorded unconditionally
        # so an archived run's reader can tell which regime it ran under.
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

    # (provider module, context length) cache, resolved once per unique
    # (provider, model), not per cell. Keyed on `mc["model"]` too, since
    # `ctx_len` is model-specific -- else one model's length could leak onto
    # another's token-usage guard.
    provider_cache: dict[tuple, tuple] = {}
    def _provider_and_ctx_for(mc: dict) -> tuple:
        key = (mc["provider"], mc["model"])
        if key not in provider_cache:
            mod = _provider_for(mc)
            provider_cache[key] = (mod, _ctx_len_for(mc, mod))
        return provider_cache[key]

    # `max_concurrency: N` on a model entry gets a Semaphore(N) shared across
    # all theorem workers, throttling a model that hits upstream rate limits
    # (e.g. qwen-instruct's 429s) without slowing the rest of the lineup.
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
        # `n_total_cells` is an upper bound over the whitelist-narrowed pool
        # (a theorem may own only some combos); printed separately so it
        # isn't read as the count actually selected.
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

    # Before opening for append, not after -- see `_repair_torn_tail`'s
    # docstring. Unconditional, not gated on `resume`: `run_study.py` usually
    # renames the old file aside first under `resume=False`, but if that ever
    # gets skipped, an unrepaired torn tail is just as wrong there.
    _repair_torn_tail(all_rows_path)

    # Keys this call writes that `_existing_keys` would count, accumulated in
    # the write path so whitelist reconciliation below skips re-parsing
    # all_rows.jsonl.
    written_keys: set[tuple] = set()

    with all_rows_path.open("a") as all_rows:
        write_lock = threading.Lock()
        print_lock = threading.Lock()

        def _process_one_theorem(theorem: BenchmarkTheorem) -> tuple[int, int, int]:
            """Worker function: process one theorem end-to-end (sanity + cells)."""
            n_w = n_o = n_s = 0
            tdir = _theorem_dir(run_dir, theorem)
            tdir.mkdir(parents=True, exist_ok=True)

            # ---- sanity gate per theorem (separate Lean REPL session) ----
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
                    all_rows.write(jsonl_line(sanity_row))
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
                        # concurrent_gen=False is one worker, not a second code path.
                        max_workers=max_concurrency if concurrent_gen else 1,
                        write_lock=write_lock, print_lock=print_lock,
                        model_semaphores=model_semaphores,
                        cell_whitelist=cell_whitelist,
                        written_keys=written_keys,
                    )
                except Exception as exc:  # noqa: BLE001
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

    # Reconcile against what all_rows.jsonl now accounts for: the pre-run
    # snapshot plus this run's own writes. Checked at the END, not early, so
    # reachable cells still get generated even when others in the whitelist
    # are not.
    whitelist_missed: list[tuple] = []
    if cell_whitelist is not None:
        whitelist_missed = sorted(cell_whitelist - (done_keys | written_keys))
        # List-of-lists, matching `hash_cell_keys`'s convention. Recorded even
        # when empty (`[]`), distinguishing a whitelist-free run from a
        # reconciled-and-clean one.
        manifest["whitelist_missed"] = [list(k) for k in whitelist_missed]

    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    write_run_analysis(run_dir)

    if whitelist_missed:
        # Logged individually (capped) so an operator sees which cells were
        # unreachable; the full list already survived into manifest.json above.
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
        # Fatal: `run_study.py` stamps this exact cell set into manifest.json's
        # claim (see docstring); raised only after that file is rewritten above.
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
