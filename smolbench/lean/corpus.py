"""Load LeanDojo Benchmark 4 splits and the premise corpus."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Literal


def data_root() -> Path:
    """Root directory of the LeanDojo Benchmark 4 dataset.

    Resolution order:
      1. The ``SMOLBENCH_LEAN_DATA`` environment variable, if set.
      2. ``notebooks/lean/data/leandojo_benchmark_4`` under the repo root.

    The default is anchored to this file's own location
    (``parents[2]`` from ``smolbench/lean/corpus.py`` is the repo root) rather
    than the current working directory. This mirrors the repo-anchoring
    pattern used for ``_DEFAULT_STATE_FILE`` in ``smolbench/evals/ec2.py``:
    notebook kernels and test runners invoke this module from arbitrary
    cwds (temp dirs included), so a cwd-relative default would silently
    resolve to the wrong place — or nowhere at all — depending on who
    imports the module.

    The env var is read at *call* time (not import time), so callers
    (including tests) may set ``SMOLBENCH_LEAN_DATA`` at any point before
    calling this function, or before calling `reset_caches` to drop any
    memoized results computed under a stale value.

    Returns
    -------
    Path
        Directory containing ``metadata.json``, ``corpus.jsonl``, and the
        ``random``/``novel_premises`` split subdirectories. Not guaranteed
        to exist; callers that read files under it will raise on a missing
        path.
    """
    override = os.getenv("SMOLBENCH_LEAN_DATA")
    if override:
        return Path(override)
    return (
        Path(__file__).resolve().parents[2]
        / "notebooks"
        / "lean"
        / "data"
        / "leandojo_benchmark_4"
    )


Split = Literal["train", "val", "test"]
SplitKind = Literal["random", "novel_premises"]


@dataclass(frozen=True)
class TracedTactic:
    tactic: str
    state_before: str
    state_after: str
    premises: list[dict]   # [{full_name, def_path, def_pos, def_end_pos}, ...]


@dataclass(frozen=True)
class BenchmarkTheorem:
    url: str
    commit: str
    file_path: str
    full_name: str
    start: tuple[int, int]
    end: tuple[int, int]
    traced_tactics: list[TracedTactic]

    @property
    def has_proof(self) -> bool:
        return len(self.traced_tactics) > 0


def _from_json(rec: dict) -> BenchmarkTheorem:
    tts = []
    for tt in rec["traced_tactics"]:
        annotated = tt["annotated_tactic"]
        tts.append(
            TracedTactic(
                tactic=tt["tactic"],
                state_before=tt["state_before"],
                state_after=tt["state_after"],
                premises=annotated[1] if len(annotated) > 1 else [],
            )
        )
    return BenchmarkTheorem(
        url=rec["url"],
        commit=rec["commit"],
        file_path=rec["file_path"],
        full_name=rec["full_name"],
        start=tuple(rec["start"]),
        end=tuple(rec["end"]),
        traced_tactics=tts,
    )


@lru_cache(maxsize=8)
def load_split(kind: SplitKind = "random", split: Split = "val") -> list[BenchmarkTheorem]:
    path = data_root() / kind / f"{split}.json"
    raw = json.loads(path.read_text())
    return [_from_json(r) for r in raw]


def iter_with_proof(kind: SplitKind = "random", split: Split = "val") -> Iterator[BenchmarkTheorem]:
    for t in load_split(kind, split):
        if t.has_proof:
            yield t


def metadata() -> dict:
    return json.loads((data_root() / "metadata.json").read_text())


def replay_passing_path(kind: SplitKind, split: Split) -> Path:
    # Design: anchored on data_root().parent (the `data/` dir), matching the
    # pre-move layout where replay_passing_*.jsonl sat alongside the
    # leandojo_benchmark_4/ directory rather than inside it.
    return data_root().parent / f"replay_passing_{kind}_{split}.jsonl"


def iter_replay_passing(kind: SplitKind = "random", split: Split = "val") -> Iterator[BenchmarkTheorem]:
    """Yield theorems whose ground-truth replay was recorded as `success`.

    Reads `data/replay_passing_<kind>_<split>.jsonl`, produced by
    `python -m smolbench.lean.cli filter --kind <kind> --split <split>`.
    """
    path = replay_passing_path(kind, split)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — run `python -m smolbench.lean.cli filter "
            f"--kind {kind} --split {split}` first"
        )
    passing: set[str] = set()
    with path.open() as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("verdict") == "success":
                passing.add(rec["full_name"])
    for t in load_split(kind, split):
        if t.full_name in passing:
            yield t


def reset_caches() -> None:
    """Clear every `functools.lru_cache` in `corpus` and `premises`.

    `data_root()` re-reads `SMOLBENCH_LEAN_DATA` on every call, but the
    lru_cache-memoized loaders in this module (`load_split`) and in
    `smolbench.lean.premises` (`_index`, `_traced_root`, `slice_full_decl`,
    `_file_records`, `_short_name_index`, `referenced_premises`) key their
    results only on their own arguments — not on the current `data_root()`
    value. A test that repoints `SMOLBENCH_LEAN_DATA` to a fixture directory
    mid-run would otherwise keep seeing theorems/premises loaded from
    whatever root was active the first time each cache was populated. Call
    this after changing `SMOLBENCH_LEAN_DATA` (directly or via
    `monkeypatch.setenv`) to force every cache to re-read from disk on next
    use.

    Notes
    -----
    `smolbench.lean.premises` is imported inside this function body, not at
    module level, because `premises` imports `data_root` from `corpus`
    (this module): a top-level `from . import premises` here would create
    an import cycle (`corpus` -> `premises` -> `corpus`) that fails at
    package-import time. Deferring the import to call time sidesteps this —
    by the time anything calls `reset_caches()`, both modules are already
    fully initialized.
    """
    load_split.cache_clear()

    # Lazy import to avoid the corpus <-> premises import cycle (see above).
    from . import premises

    premises._index.cache_clear()
    premises._traced_root.cache_clear()
    premises.slice_full_decl.cache_clear()
    premises._file_records.cache_clear()
    premises._short_name_index.cache_clear()
    premises.referenced_premises.cache_clear()
