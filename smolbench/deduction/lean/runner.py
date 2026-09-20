"""Run theorem × step × context-rung evaluation replicates.

Providers resolve per model so a sweep can mix them. `seed` defaults to 0 to
match `theorems.seed` and `run_study.py`; `run_cell` keeps 1776. The 1800s
request timeout prevents the client's 120s default from truncating long CoT,
and four retries bound a wedged endpoint in an open REPL session. Verification
is lazily imported so generation needs no Lean toolchain.
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
from smolbench.evals.retired_markers import retired_paths

from . import lean3
from .context import Chain, is_trivial_rung, render
from .context import validate as validate_rung
from .corpus import (
    BenchmarkTheorem,
    data_root,
    is_postcutoff_corpus,
    iter_replay_passing,
    iter_with_proof,
    load_split,
)
from .prompt import SYSTEM, build_user_prompt, extract_tactic_block

# `write_run_analysis` always needs stdlib-only `lean3`, so no lazy seam exists.

# `.verify` needs optional `lean_interact`, so `_default_verifier` imports it lazily.


#: REPL seconds for `run_cell`, `sweep`, and `cli --timeout`; lower budgets
#: would record slow real theorems as infrastructure `"exception"` verdicts.
DEFAULT_DOJO_TIMEOUT: int = 600


def results_root() -> Path:
    """Return the output root, resolving `SMOLBENCH_LEAN_RESULTS` at call time.

    Otherwise anchor to the installed package, never cwd, matching `corpus.data_root`.
    """
    override = os.getenv("SMOLBENCH_LEAN_RESULTS")
    if override:
        return Path(override)
    return (
        Path(smolbench.__file__).resolve().parents[1]
        / "notebooks"
        / "deduction"
        / "results"
    )


def _default_verifier() -> Any:
    """Import `.verify` lazily; it requires `lean_interact`.

    Substitutes must provide `open_at_step`, `try_tail`, `replay_ground_truth`,
    `verify_proof_tail`, and `ProofResult`; tests use `FakeVerifier` and generation-only
    sweeps use `NullVerifier`.
    """
    from smolbench.deduction.lean import verify

    return verify


# ---------------------------------------------------------------------------
# Slugs
# ---------------------------------------------------------------------------


def slug_theorem(name: str) -> str:
    """Return a filesystem-safe theorem name."""
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)


def slug_rung(rung: str) -> str:
    """Return a filesystem-safe rung slug; `:` is unsafe on Win/WSL."""
    return rung.replace(":", "-")


def slug_model(model: str) -> str:
    """Return a model's final `/`-separated segment."""
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

    It opens its own REPL; single-shot, non-resuming completion failures
    propagate rather than become exception rows. Rows omit `api_model` because
    this entry point has no display name.

    Parameters
    ----------
    provider : str
        Provider identifier for model completion.
    model : str
        Model identifier for model completion.
    theorem : BenchmarkTheorem
        Theorem whose tail is attempted.
    k : int
        Index of the tactic step.
    chain : Chain
    level : int
    n_replicates : int
    temperature : float, optional
    max_tokens : int, optional
    dojo_timeout : int, optional
        Name shared by `run_cell`, `sweep`, and `cli` defaults.
    seed : int, optional
        Replicate `i` uses `seed + i` for cross-model pairing.
    request_timeout : int, optional
    max_retries : int, optional
    verifier : Any, optional

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
        # Lookup failure must not abort this cell.
        ctx_len = 10**9
        print(
            f"warning: context-length lookup failed for {model} on {provider}: {exc}",
            flush=True,
        )

    for replicate_idx in range(n_replicates):
        replicate_seed = seed + replicate_idx
        t0 = time.monotonic()
        # Only `sweep` writes exception rows.
        rsp = mod.complete(
            user_prompt,
            model,
            replicate_seed,
            system=SYSTEM,
            context_length=ctx_len,
            extra_args={"temperature": temperature, "max_tokens": max_tokens},
            request_timeout=request_timeout,
            max_retries=max_retries,
        )
        gen_ms = int((time.monotonic() - t0) * 1000)

        candidate = extract_tactic_block(rsp.content)

        t1 = time.monotonic()
        verdict = verifier.verify_proof_tail(
            theorem, k, candidate, timeout=dojo_timeout
        )
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
    """Serialize one JSONL row."""
    return json.dumps(row, ensure_ascii=False) + "\n"


def write_jsonl(rows: Iterable[dict], path: Path) -> int:
    """Append rows and return their count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a") as f:
        for r in rows:
            f.write(jsonl_line(r))
            n += 1
    return n


def new_run_id() -> str:
    """Return a timestamped, short-unique run ID."""
    return time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]


def _require_all_postcutoff(pool: list[BenchmarkTheorem]) -> None:
    """Raise `ValueError` unless every theorem in `pool` carries `BenchmarkTheorem.postcutoff`.

    Name five offenders plus the total to bound large error messages.

    Parameters
    ----------
    pool : list[BenchmarkTheorem]
    """
    bad = [t.full_name for t in pool if not t.postcutoff]
    if not bad:
        return
    shown = ", ".join(bad[:5])
    suffix = f", and {len(bad) - 5} more" if len(bad) > 5 else ""
    raise ValueError(
        f"Post-cutoff gate: {len(bad)} theorem(s) are not flagged "
        f"postcutoff: {shown}{suffix}"
    )


def _select_theorems(
    spec: dict, *, cell_whitelist: frozenset[tuple] | None = None
) -> list[BenchmarkTheorem]:
    """Resolve a config `theorems` block into a concrete BenchmarkTheorem list.

    Parameters
    ----------
    spec : dict
    cell_whitelist : frozenset[tuple] | None, optional
        Theorems owning an allowed cell; loaded once from `LEAN_CELL_WHITELIST`.

    Returns
    -------
    list[BenchmarkTheorem]
        Selected theorems.

    Raises
    ------
    ValueError
        Unknown sources, malformed shards, or pre-cutoff pools.
    """
    source = spec.get("source", "replay_passing")
    kind = spec.get("kind", "random")
    split = spec.get("split", "val")
    max_tactics = int(spec.get("max_tactics", 0))
    limit = int(spec.get("limit", 0))
    seed = int(spec.get("seed", 0))

    # Check first: the old Benchmark 4 snapshot has no post-cutoff tail, so no
    # sampling, seed, or split can produce a compliant item.
    if not is_postcutoff_corpus():
        raise ValueError(
            f"{data_root()} is not a "
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

    # Check before filters: sampling is population-sensitive, so a missed
    # pre-cutoff row must not decide compliance.
    _require_all_postcutoff(pool)

    if max_tactics > 0:
        pool = [t for t in pool if 1 <= len(t.traced_tactics) <= max_tactics]

    if 0 < limit < len(pool):
        rng = random.Random(seed)
        pool = rng.sample(pool, limit)

    # Shard after sampling so identical pools make disjoint slices whose union
    # is unsharded selection; keep each theorem's rungs and sanity row together.
    shard = str(spec.get("shard", "") or "")
    if shard:
        idx_str, sep, n_str = shard.partition("/")
        try:
            idx, n = int(idx_str), int(n_str)
        except ValueError:
            # `-1, 0` fails the shared range check.
            idx, n = -1, 0
        if not sep or not 0 <= idx < n:
            raise ValueError(f"theorems.shard {shard!r} must be 'i/n' with 0 <= i < n")
        pool = pool[idx::n]

    # Filter whole theorems last to skip their sanity replay and REPL session:
    # needed for an n=200-cell rerun against a 300-theorem pool.
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
# `LEAN_CELL_WHITELIST` filters exact cells for small fresh-box reruns.
# ---------------------------------------------------------------------------


def load_cell_whitelist(path_str: str) -> frozenset[tuple]:
    """Load and validate a `LEAN_CELL_WHITELIST` JSON file into a key set.

    Five-element entries follow `_row_key` order so they compare equal to `sweep` keys.

    Parameters
    ----------
    path_str : str

    Returns
    -------
    frozenset[tuple]
        `_row_key`-ordered keys.

    Raises
    ------
    ValueError
        Read, parse, or shape errors; malformed input must abort before expensive generation.
    """
    path = Path(path_str)
    try:
        raw = path.read_text(encoding="utf-8")
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
        keys.add(
            _row_key(str(model), str(theorem), int(k), str(rung), int(replicate_idx))
        )
    return frozenset(keys)


def hash_cell_keys(keys: Iterable[tuple]) -> str:
    """Lowercase hex SHA-256 of a canonical JSON encoding of `keys`.

    Sort and list-coerce keys so equal tuples and lists fingerprint alike; this
    stamps the manifest's exact cell set for change detection, not security.

    Parameters
    ----------
    keys : Iterable[tuple]

    Returns
    -------
    str
        SHA-256 fingerprint.
    """
    canonical = json.dumps(sorted(list(key) for key in keys), separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


#: Individually logged unreachable whitelist keys; the full list always enters
#: `manifest.json["whitelist_missed"]`.
WHITELIST_MISS_LOG_CAP: int = 50


# ---------------------------------------------------------------------------
# One shared config loader prevents the driver and CLI YAML parsing from drifting.
# ---------------------------------------------------------------------------


def load_sweep_config(path: str | Path) -> tuple[dict, str]:
    """Load a sweep config YAML file; return it with a SHA-256 of the raw bytes.

    Require a mapping so malformed input fails before keyed access. Hash the
    parser's exact bytes, including rationale comments, because provenance
    claims them; import YAML locally for callers that do not need PyYAML.

    Parameters
    ----------
    path : str | Path

    Returns
    -------
    tuple[dict, str]
        Configuration and raw-byte SHA-256.
    """
    import yaml

    config_path = Path(path)
    # Hash exactly the bytes `yaml.safe_load()` sees.
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
    """Truncate torn final lines from `jsonl_path` in place.

    Run before append: a SIGKILL can leave a partial final line, and append
    would weld it into corrupt middle data that `merge_lean_shards.py` aborts
    on. Scan backward and truncate once so a second crash cannot lose intact rows.

    Parameters
    ----------
    jsonl_path : Path

    Returns
    -------
    int
        Discarded bytes; 0 if untouched.
    """
    if not jsonl_path.exists():
        return 0
    with jsonl_path.open("r+b") as f:
        data = f.read()
        end = len(data)
        while end > 0:
            if data[end - 1] != 0x0A:  # last byte is not '\n': tail is UNTERMINATED
                newline_before = data.rfind(b"\n", 0, end)
                end = newline_before + 1
                continue
            newline_before = data.rfind(b"\n", 0, end - 1)
            last_line = data[newline_before + 1 : end - 1]
            try:
                json.loads(last_line.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                end = newline_before + 1
                continue
            break
        discarded = len(data) - end
        if discarded:
            f.truncate(end)
    if discarded:
        logging.warning(
            "%s: discarded %d torn/unparseable byte(s) from the final line(s) "
            "on resume -- the row(s) they held will be regenerated",
            jsonl_path,
            discarded,
        )
    return discarded


def read_jsonl_tolerating_torn_tail(
    path: Path, *, skip_bad: bool = False
) -> list[dict]:
    """Parse rows, optionally skipping corrupt records.

    Only a SIGKILL-torn final line is dropped with a warning; interior
    corruption still names its line.

    Parameters
    ----------
    path : Path
    skip_bad : bool, optional
        Skip undecodable records for read-only reporting.

    Returns
    -------
    list[dict]
        Parsed rows, or `[]` for a missing file.
    """
    if not path.exists():
        return []
    # `splitlines()` breaks on U+2028/U+0085 that JSON leaves unescaped in Lean errors.
    lines = path.read_text().split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    rows: list[dict] = []
    for lineno, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            if skip_bad:
                continue
            if lineno != len(lines) - 1:
                raise json.JSONDecodeError(
                    f"corrupt row mid-file at line {lineno + 1}", line, exc.pos
                ) from exc
            logging.warning(
                "%s: torn (truncated) final line dropped -- the append-only "
                "writer regenerates it on resume",
                path,
            )
    return rows


def _cell_key(r: dict) -> tuple:
    """Return the tolerant row key used by resume."""
    return _row_key(
        r.get("model", ""),
        r.get("theorem_id", ""),
        int(r.get("k", -1)),
        r.get("rung", ""),
        int(r.get("replicate_idx", -1)),
    )


def group_cell_rows(rows: Iterable[dict], key: Callable[[dict], Any]) -> dict:
    """Group rows by key in first-seen order."""
    groups: dict = {}
    for row in rows:
        groups.setdefault(key(row), []).append(row)
    return groups


def _accounts_for_cell(r: dict) -> bool:
    """Return whether this row prevents its cell from rerunning."""
    if r.get("verdict") == "exception":
        return False
    return (
        bool((r.get("candidate_proof") or "").strip())
        or int(r.get("prompt_tokens") or 0) > 0
    )


def _existing_keys(jsonl_path: Path) -> set[tuple]:
    """Return existing cell keys that must not rerun.

    Exceptions rerun because verification may not have checked their candidate.
    Empty prompted cells remain data; rerunning them would inflate pass@1.
    `prompt_tokens` is `audit_run_completeness.py`'s completeness signal.

    Parameters
    ----------
    jsonl_path : Path

    Returns
    -------
    set[tuple]
        Keys that must not rerun.
    """
    cell_rows = [
        r
        for r in read_jsonl_tolerating_torn_tail(jsonl_path)
        if r.get("kind") == "cell"
    ]
    rows_by_key = group_cell_rows(cell_rows, _cell_key)
    return {
        key
        for key, rows in rows_by_key.items()
        if any(_accounts_for_cell(r) for r in rows)
    }


def dedupe_cell_rows(rows: Iterable[dict]) -> list[dict]:
    """Deduplicate cell rows, preferring the earliest surviving attempt.

    Resume appends exception retries; counting both would inflate `cmd_analyze`
    pass@N. Use `_existing_keys` fields so both define the same cell.

    Parameters
    ----------
    rows : Iterable[dict]

    Returns
    -------
    list[dict]
        Earliest surviving row, or first exception.
    """
    deduped: list[dict] = []
    for group in group_cell_rows(rows, _cell_key).values():
        surviving = next((r for r in group if r.get("verdict") != "exception"), None)
        deduped.append(surviving if surviving is not None else group[0])
    return deduped


def _sanity_done(jsonl_path: Path) -> dict[str, str]:
    """Map theorem names to their final recorded sanity verdict.

    Resume reapplies failure verdicts so failed ground truth stays excluded,
    but infrastructure exceptions must not permanently exclude a theorem. Do
    not replay existing rows: `merge_lean_shards.py --expect-sanity` requires one.

    Parameters
    ----------
    jsonl_path : Path

    Returns
    -------
    dict[str, str]
        Names mapped to verdicts.
    """
    return {
        r.get("theorem_id", ""): r.get("verdict", "")
        for r in read_jsonl_tolerating_torn_tail(jsonl_path)
        if r.get("kind") == "sanity"
    }


# ---------------------------------------------------------------------------
# Per-theorem directory writers
# ---------------------------------------------------------------------------


def _theorem_dir(run_dir: Path, theorem: BenchmarkTheorem) -> Path:
    return run_dir / "theorems" / slug_theorem(theorem.full_name)


def _write_meta(theorem: BenchmarkTheorem, k: int, theorem_dir: Path) -> None:
    """Overwrite `meta.json`."""
    theorem_dir.mkdir(parents=True, exist_ok=True)
    tt_k = theorem.traced_tactics[k] if 0 <= k < len(theorem.traced_tactics) else None
    meta = {
        "full_name": theorem.full_name,
        "file_path": theorem.file_path,
        "url": theorem.url,
        "commit": theorem.commit,
        "n_total_tactics": len(theorem.traced_tactics),
        "k": k,
        "ground_truth_full_proof": "\n".join(
            tt.tactic for tt in theorem.traced_tactics
        ),
        "ground_truth_remaining_from_k": (
            "\n".join(tt.tactic for tt in theorem.traced_tactics[k:])
        ),
        "true_premises_at_k": [p["full_name"] for p in tt_k.premises] if tt_k else [],
        "state_before_k": tt_k.state_before if tt_k else None,
    }
    (theorem_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False)
    )


def _write_prompt(rung: str, rendered_text: str, theorem_dir: Path) -> None:
    """Overwrite a rung prompt."""
    pd = theorem_dir / "prompts"
    pd.mkdir(parents=True, exist_ok=True)
    (pd / f"{slug_rung(rung)}.md").write_text(rendered_text + "\n")


def _append_output(row: dict, theorem_dir: Path) -> None:
    """Append one row to outputs/<rung>__<model>.jsonl."""
    fname = f"{slug_rung(row['rung'])}__{slug_model(row['model'])}.jsonl"
    write_jsonl([row], theorem_dir / "outputs" / fname)


# ---------------------------------------------------------------------------
# Summary generators
# ---------------------------------------------------------------------------


#: verdict -> (glyph, sanity_failure, never_measured). Keep this table here:
#: `.verify` imports `lean_interact` and this module must not. Derived sets
#: cannot drift. Only unreplayable ground truth gates cells; infrastructure
#: exceptions and deferred skips pass through; replay cannot return `no_answer`.
VERDICTS: dict[str, tuple[str, bool, bool]] = {
    #                glyph  sanity_failure  never_measured
    "success": ("✓", False, False),
    "lean_error": ("✘", True, False),
    "incomplete": ("·", True, False),
    "given_up": ("?", True, False),
    # Distinct glyph: incomplete/given-up answered, while no_answer answered nothing.
    "no_answer": ("∅", False, False),
    "replay_failed": ("!", True, True),
    "exception": ("X", False, True),
    # Generation-only sweeps: cells awaiting deferred verification.
    "unverified": ("~", False, False),
    "skipped": ("-", False, False),
}

_VERDICT_GLYPH = {v: row[0] for v, row in VERDICTS.items()}
SANITY_FAILURE_VERDICTS: frozenset[str] = frozenset(
    v for v, row in VERDICTS.items() if row[1]
)
#: Verdicts where Lean never ran; `lean_verify_rows.py` reads these as unresolved.
NEVER_MEASURED_VERDICTS: frozenset[str] = frozenset(
    v for v, row in VERDICTS.items() if row[2]
)

_CHAIN_ORDER = {"stepk": 0, "hint": 1, "noise": 2}


def _glyph(v: str) -> str:
    return _VERDICT_GLYPH.get(v, "?")


def reject_superseded_rows(paths: Iterable[str | Path]) -> None:
    """Reject row files whose names carry a retired marker.

    Log too: concurrent theorem workers reduce errors to one failure line.

    Parameters
    ----------
    paths : Iterable[str | Path]

    Raises
    ------
    ValueError
        Retired paths: silently skipping valid files would create a plausible wrong summary.
    """
    bad = retired_paths(paths)
    if bad:
        logging.error("refusing SUPERSEDED row file(s): %s", ", ".join(bad))
        raise ValueError(
            "refusing SUPERSEDED row file(s) -- these are retired artifacts "
            "kept as an audit trail (see run_study.py --force-rerun), not "
            "current data: " + ", ".join(bad)
        )


def _rung_sort_key(rung: str) -> tuple[int, int]:
    """Order `stepk`, `hint`, then `noise` rungs by level."""
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
        stem = jl.stem
        if "__" not in stem:
            continue
        for r in read_jsonl_tolerating_torn_tail(jl, skip_bad=True):
            cells[(r["rung"], r["model"])].append(r)

    rungs = sorted({r for r, _ in cells.keys()}, key=_rung_sort_key)
    models = sorted({m for _, m in cells.keys()})

    lines: list[str] = []
    lines.append(
        f"# {meta['full_name']}   (k={meta['k']}, {meta['n_total_tactics']} tactics total)\n"
    )
    lines.append(f"file: `{meta['file_path']}`  \n")
    lines.append("**Ground-truth tail (from k):**")
    lines.append(
        "```lean\n" + (meta["ground_truth_remaining_from_k"] or "(empty)") + "\n```\n"
    )
    if meta["true_premises_at_k"]:
        lines.append(
            "**True premises at k:** "
            + ", ".join(f"`{p}`" for p in meta["true_premises_at_k"])
            + "\n"
        )
    else:
        lines.append("**True premises at k:** _(none recorded)_\n")

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
                lines.append(
                    f"prompt: [`prompts/{slug_rung(rung)}.md`](prompts/{slug_rung(rung)}.md)\n"
                )
                lines.append("**candidate:**")
                cand = r.get("candidate_proof", "") or "(empty)"
                lines.append("```lean\n" + cand + "\n```\n")
                if r.get("lean_error"):
                    err = r["lean_error"].splitlines()[0][:300]
                    lines.append(f"**lean_error:** {err}\n")
                if r.get("final_state_pp"):
                    pp = r["final_state_pp"].splitlines()
                    lines.append("**final state (truncated):**")
                    lines.append(
                        "```\n"
                        + "\n".join(pp[:6])
                        + ("\n..." if len(pp) > 6 else "")
                        + "\n```\n"
                    )

    (theorem_dir / "summary.md").write_text("\n".join(lines))


def analyze_rows(
    path: Path,
) -> tuple[
    dict[tuple[str, str], dict[str, int]],
    dict[tuple[str, str, str, int], list[str]],
    tuple[int, int, int],
]:
    """Aggregate complete rows for every analysis renderer.

    Shared deduplication and counters keep the CLI and durable report aligned.

    Parameters
    ----------
    path : Path

    Returns
    -------
    tuple[dict, dict, tuple[int, int, int]]
        Counters, pass@N groups, and sanity counts.
    """
    cells: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {
            "n": 0,
            "success": 0,
            "lean_error": 0,
            "incomplete": 0,
            "given_up": 0,
            "replay_failed": 0,
            "exception": 0,
            "no_answer": 0,
            "unverified": 0,
            "tok_in": 0,
            "tok_out": 0,
            "ms": 0,
            "trunc": 0,
            "l3": 0,
        }
    )
    # pass@N needs exact (theorem, k) identity unavailable in rung/model totals.
    groups: dict[tuple[str, str, str, int], list[str]] = defaultdict(list)
    sanity = [0, 0, 0]
    # Deduplicate before counts and pass@N to collapse exception retries.
    cell_rows: list[dict] = []
    for row in read_jsonl_tolerating_torn_tail(path):
        if row.get("kind", "cell") != "sanity":
            cell_rows.append(row)
        elif row.get("verdict") == "success":
            sanity[0] += 1
        elif row.get("verdict") in SANITY_FAILURE_VERDICTS:
            sanity[1] += 1
        else:
            # Infra exceptions and generation-only skips are not ground-truth failures.
            sanity[2] += 1

    for row in dedupe_cell_rows(cell_rows):
        counter = cells[(row.get("rung", "?"), row.get("model", "?"))]
        counter["n"] += 1
        verdict = row.get("verdict", "exception")
        counter[verdict if verdict in counter else "exception"] += 1
        counter["tok_in"] += row.get("prompt_tokens", 0)
        counter["tok_out"] += row.get("completion_tokens", 0)
        counter["ms"] += row.get("gen_ms", 0) + row.get("verify_ms", 0)
        # Count cut-off reasoning separately from proof dead ends; vLLM can
        # put it in `reasoning_content` with empty `raw_response`.
        raw = row.get("raw_response", "") or row.get("content", "")
        if ("<think>" in raw and "</think>" not in raw) or (
            row.get("reasoning_content") and not (row.get("raw_response") or "").strip()
        ):
            counter["trunc"] += 1
        if lean3.find_relics(row.get("candidate_proof") or ""):
            counter["l3"] += 1
        groups[
            (
                row.get("model", "?"),
                row.get("rung", "?"),
                row.get("theorem_id", "?"),
                row.get("k", -1),
            )
        ].append(verdict)
    return dict(cells), dict(groups), (sanity[0], sanity[1], sanity[2])


def model_totals(
    cells: dict[tuple[str, str], dict[str, int]],
) -> dict[str, dict[str, int]]:
    """Roll rung counters into model totals.

    Parameters
    ----------
    cells : dict[tuple[str, str], dict[str, int]]

    Returns
    -------
    dict[str, dict[str, int]]
        Model-keyed totals.
    """
    totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"n": 0, "success": 0, "tok_in": 0, "tok_out": 0, "l3": 0}
    )
    for (_, model), counter in cells.items():
        for key in totals[model]:
            totals[model][key] += counter[key]
    return dict(totals)


def write_run_analysis(run_dir: Path) -> None:
    """Overwrite `analysis.txt` with a rung/model table.

    `l3` counts parse-level Lean 3 relics regardless of verdict; deduplication
    makes every cell count distinct cells rather than raw retry rows.

    Parameters
    ----------
    run_dir : Path
    """
    all_rows = run_dir / "all_rows.jsonl"
    if not all_rows.exists():
        return

    cells, _groups, sanity = analyze_rows(all_rows)
    n_sanity_pass, n_sanity_fail, n_sanity_skipped = sanity
    n_rows = sum(counter["n"] for counter in cells.values())

    out: list[str] = []
    out.append(
        f"# {n_rows} cells; sanity {n_sanity_pass} pass / {n_sanity_fail} fail"
        + (f" / {n_sanity_skipped} deferred" if n_sanity_skipped else "")
        + "\n"
    )
    if n_sanity_fail:
        out.append(
            f"!! {n_sanity_fail} sanity-gate failures — pipeline may have rotted\n"
        )
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
        f"{'rate':>6} {'lerr':>5} {'incp':>5} {'gvup':>5} {'rplf':>5} {'exc':>4} {'noans':>5} "
        f"{'l3(parse-level)':>16} "
        f"{'avg_in':>7} {'avg_out':>7} {'avg_s':>6}"
    )
    out.append(header)
    out.append("-" * len(header))
    for (rung, model), c in sorted(
        cells.items(), key=lambda kv: (_rung_sort_key(kv[0][0]), kv[0][1])
    ):
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
    for model, m in sorted(model_totals(cells).items()):
        rate = m["success"] / m["n"] if m["n"] else 0
        out.append(
            f"  {model:<36}  {m['success']:>4}/{m['n']:<4}  {rate:>6.1%}  "
            f"({m['tok_in']:,} in / {m['tok_out']:,} out tokens)  "
            f"l3(parse-level)={m['l3']}"
        )
    (run_dir / "analysis.txt").write_text("\n".join(out) + "\n")


# ---------------------------------------------------------------------------
# One REPL session serves all cells at a (theorem, k).
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
    """Generate cells concurrently and verify them on the shared REPL.

    Verification serializes because the REPL is single-threaded; generation at
    ~1.3–3s/cell versus ~0.4s verification fans out. Skip completed or unlisted cells, avoiding REPL startup when none
    remain; record resumable written keys when requested.

    Parameters
    ----------
    all_rows : TextIO
    theorem : BenchmarkTheorem
    k : int
    rungs : list[str]
    rendered_by_rung : dict
    models_cfg : list[dict]
    n_replicates : int
    temperature : float
    max_tokens : int
    provider_factory : Callable[[dict], tuple[Any, int]]
        Resolves a provider and context length.
    base_seed : int
    request_timeout : int
    max_retries : int
    done_keys : set
    tdir : Path
    dojo_timeout : int
    verifier : Any
    max_workers : int, optional
    write_lock : threading.Lock | None, optional
    print_lock : threading.Lock | None, optional
    model_semaphores : dict[str, threading.Semaphore] | None, optional
    cell_whitelist : frozenset[tuple] | None, optional
    written_keys : set[tuple] | None, optional

    Returns
    -------
    tuple[int, int, int]
        Written, successful, and skipped counts.
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
                pending.append(
                    {
                        "key": key,
                        "rung": rung,
                        "rendered": rendered,
                        "chain": chain,
                        "level": level,
                        "user_prompt": user_prompt,
                        "mc": mc,
                        "model": mc["model"],
                        "provider": mc["provider"],
                        "replicate_idx": replicate_idx,
                        # Replicate-only seeds keep cross-model cells paired.
                        "seed": base_seed + replicate_idx,
                        "display_name": display_name,
                        "extra_params": mc.get("extra_params"),
                    }
                )

    if not pending:
        return n_written, n_ok, n_skipped

    # Submit reasoning cells first to shorten REPL lifetime; preserve plain
    # order at one worker.
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
        pending.sort(
            key=lambda p: (
                rung_order[p["rung"]],
                0 if _is_reasoning(p["mc"]) else 1,
                model_order[id(p["mc"])],
                p["replicate_idx"],
            )
        )

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
                # Start at generation so queue and semaphore waits are not billed.
                if sem is None:
                    p["t_gen_start"] = time.monotonic()
                    return mod.complete(*args, **kwargs)
                with sem:
                    p["t_gen_start"] = time.monotonic()
                    return mod.complete(*args, **kwargs)

            future_to_pending = {}
            for p in pending:
                mod, ctx_len = provider_factory(p["mc"])
                # Fallback if the future raises before its start timestamp.
                p["t_gen_start"] = time.monotonic()
                sem = (model_semaphores or {}).get(p["display_name"])
                fut = executor.submit(
                    _gated_complete,
                    p,
                    mod,
                    sem,
                    p["user_prompt"],
                    p["model"],
                    p["seed"],
                    system=SYSTEM,
                    context_length=ctx_len,
                    extra_args={
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        **(p["extra_params"] or {}),
                    },
                    request_timeout=request_timeout,
                    max_retries=max_retries,
                )
                future_to_pending[fut] = p

            # One worker preserves submission order; `as_completed` does not.
            arrivals = (
                list(future_to_pending)
                if max_workers == 1
                else as_completed(future_to_pending)
            )
            for fut in arrivals:
                p = future_to_pending[fut]

                base_row = {
                    "kind": "cell",
                    "theorem_id": theorem.full_name,
                    "file_path": theorem.file_path,
                    "k": k,
                    "n_total_tactics": len(theorem.traced_tactics),
                    "chain": p["chain"],
                    "level": p["level"],
                    "rung": p["rung"],
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
                    # Read after waiting: one-worker tasks may not have started.
                    gen_ms = int((time.monotonic() - p["t_gen_start"]) * 1000)
                    row = {
                        **base_row,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cache_read_tokens": 0,
                        "cache_creation_tokens": 0,
                        # Keep the key so every row has `finish_reason`.
                        "finish_reason": None,
                        "gen_ms": gen_ms,
                        "verify_ms": 0,
                        "candidate_proof": "",
                        "raw_response": "",
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
                        verdict = verifier.try_tail(
                            dojo, state_at_k, candidate, theorem.full_name
                        )
                    except Exception as exc:  # noqa: BLE001
                        verdict = verifier.ProofResult(
                            theorem.full_name,
                            "exception",
                            candidate,
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
                        "gen_ms": gen_ms,
                        "verify_ms": verify_ms,
                        "candidate_proof": candidate,
                        "raw_response": rsp.content,
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
    """Resolve one model configuration's provider.

    Do not use process-wide `INFERENCE_PROVIDER`: a lineup can mix providers.

    Parameters
    ----------
    mc : dict

    Returns
    -------
    Any
        Provider module.
    """
    return provider_module(mc["provider"])


def _ctx_len_for(mc: dict, mod: Any) -> int:
    """Resolve a model context window, tolerating catalog failures.

    Fall back to `10**9` so real overflow becomes a resumable per-cell
    `ValueError`, not a hard abort.

    Parameters
    ----------
    mc : dict
    mod : Any

    Returns
    -------
    int
        Context window.
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


def sweep(
    config: dict, run_dir: Path, *, resume: bool = True, verifier: Any = None
) -> int:
    """Run a configured sweep and write per-theorem output.

    One REPL serves each (theorem, k); another replays ground truth for its
    sanity gate. Whitelists generate only listed cells; a theorem owning none
    is dropped before its sanity gate. Unreachable keys fail after artifacts
    are written because `run_study.py` manifests their exact hash. Record
    `traced_root_present`: a cached traced checkout outside results changes
    `skip_trivial` output and triggers a warning when absent.

    Parameters
    ----------
    config : dict
    run_dir : Path
    resume : bool, optional
    verifier : Any, optional

    Returns
    -------
    int
        Written cell count.
    """
    if verifier is None:
        verifier = _default_verifier()

    # Load once so a bad whitelist fails before spend.
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
    # Resolve locally first so a typo fails before a real sanity replay.
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
    # Match `theorems.seed` and `run_study.py` at 0 so omitted config cannot disagree.
    base_seed = int(config.get("seed", 0))
    request_timeout = int(config.get("request_timeout", 1800))
    max_retries = int(config.get("max_retries", 4))

    # A traced checkout lets `is_trivial_rung` judge full premises; import
    # lazily to avoid `context`'s otherwise absent eager dependency.
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
        # Record box provenance so archived readers know the rendering regime.
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

    # Cache per (provider, model): context length is model-specific and must
    # not leak into another model's token guard.
    provider_cache: dict[tuple, tuple] = {}

    def _provider_and_ctx_for(mc: dict) -> tuple:
        key = (mc["provider"], mc["model"])
        if key not in provider_cache:
            mod = _provider_for(mc)
            provider_cache[key] = (mod, _ctx_len_for(mc, mod))
        return provider_cache[key]

    # Shared per-model caps throttle upstream rate limits without slowing peers.
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
        # This is an upper bound: a theorem may own only some requested cells.
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

    # Repair before append even without resume: an unrepaired tail is corrupt.
    _repair_torn_tail(all_rows_path)

    # Accumulate resumable writes to avoid reparsing for whitelist reconciliation.
    written_keys: set[tuple] = set()

    with all_rows_path.open("a") as all_rows:
        write_lock = threading.Lock()
        print_lock = threading.Lock()

        def _process_one_theorem(theorem: BenchmarkTheorem) -> tuple[int, int, int]:
            """Process one theorem's sanity gate and cells."""
            n_w = n_o = n_s = 0
            tdir = _theorem_dir(run_dir, theorem)
            tdir.mkdir(parents=True, exist_ok=True)

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
                # Resume reapplies the recorded gate.
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
                        theorem=theorem,
                        k=k,
                        rungs=effective_rungs,
                        rendered_by_rung=rendered_by_rung,
                        models_cfg=models_cfg,
                        n_replicates=n_replicates,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        provider_factory=_provider_and_ctx_for,
                        base_seed=base_seed,
                        request_timeout=request_timeout,
                        max_retries=max_retries,
                        done_keys=done_keys,
                        tdir=tdir,
                        dojo_timeout=dojo_timeout,
                        verifier=verifier,
                        max_workers=max_concurrency if concurrent_gen else 1,
                        write_lock=write_lock,
                        print_lock=print_lock,
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

    # Reconcile at the end so reachable cells still generate despite misses.
    whitelist_missed: list[tuple] = []
    if cell_whitelist is not None:
        whitelist_missed = sorted(cell_whitelist - (done_keys | written_keys))
        # Record even `[]` to distinguish a clean whitelist run from no whitelist.
        manifest["whitelist_missed"] = [list(k) for k in whitelist_missed]

    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    write_run_analysis(run_dir)

    if whitelist_missed:
        # Cap logs; the manifest retains every unreachable key.
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
        # Fatal after writing: `run_study.py` manifests this exact cell claim.
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
