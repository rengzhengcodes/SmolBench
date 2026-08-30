"""Load LeanDojo Benchmark 4 splits (per-theorem tactic traces).

`LeanDojo Benchmark 4 <https://zenodo.org/records/10929138>`_ is a mathlib4
snapshot (commit ``fe4454af``, March 2024) traced by LeanDojo; the parallel
corpus of every premise declared in that repo lives in
``smolbench.deduction.lean.premises``. See ``notebooks/deduction/README.md``
for pool sizes and bootstrap instructions.

Loaders are keyed by ``(kind, split)``: ``kind`` is ``"random"`` (i.i.d.) or
``"novel_premises"`` (val/test theorems whose premises are under-represented
in train -- the harder generalization slice); ``split`` is ``"train"``,
``"val"`` or ``"test"``. The ~700 MB dataset is not shipped here; loaders
raise ``FileNotFoundError`` naming the remedy when a file is missing.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Literal

import smolbench


def data_root() -> Path:
    """Root of the LeanDojo Benchmark 4 dataset; not guaranteed to exist.

    ``SMOLBENCH_LEAN_DATA`` if set, else
    ``notebooks/deduction/data/leandojo_benchmark_4`` anchored off the
    installed ``smolbench`` package rather than cwd (importers run from
    arbitrary directories). The env var is read at *call* time, so callers
    may set it late; call `reset_caches` afterwards to drop results memoized
    under a stale value.
    """
    override = os.getenv("SMOLBENCH_LEAN_DATA")
    if override:
        return Path(override)
    return (
        Path(smolbench.__file__).resolve().parents[1]
        / "notebooks"
        / "deduction"
        / "data"
        / "leandojo_benchmark_4"
    )


Split = Literal["train", "val", "test"]
SplitKind = Literal["random", "novel_premises"]


@dataclass(frozen=True)
class TracedTactic:
    """One tactic application from LeanDojo's trace: one ``traced_tactics`` entry."""

    #: The tactic text as written in the proof (e.g. ``"simp"``,
    #: ``"exact Mini.premiseA h"``).
    tactic: str
    #: Pretty-printed Lean tactic state (hypotheses followed by goal(s),
    #: separated by a line starting with ``⊢``) immediately before `tactic`
    #: is applied. See ``smolbench.deduction.lean.context.split_state``.
    state_before: str
    #: Pretty-printed Lean tactic state immediately after `tactic` is
    #: applied (``"no goals"`` when the tactic closes the last goal).
    state_after: str
    #: Premises referenced by name inside `tactic`, one dict per reference:
    #: ``{full_name, def_path, def_pos, def_end_pos}``. This is a lighter,
    #: distinct shape from ``smolbench.deduction.lean.premises.Premise``
    #: (no ``code``/``kind``). ``full_name`` is the join key used to look
    #: the full premise up via ``smolbench.deduction.lean.premises.lookup``
    #: (see ``context._render_hint_parts``). Empty when the tactic
    #: references no known premise (most tactics -- e.g. ``intro h``, bare
    #: ``simp``). See ``_from_json`` for how this is extracted from the
    #: raw ``annotated_tactic`` field.
    premises: list[dict]


@dataclass(frozen=True)
class BenchmarkTheorem:
    """One theorem entry from a LeanDojo Benchmark 4 ``<kind>/<split>.json`` file."""

    #: GitHub URL of the traced repo (mathlib4).
    url: str
    #: Commit hash the theorem was traced at (e.g. ``fe4454af...``).
    commit: str
    #: Path to the theorem's declaring file, relative to the repo root
    #: (e.g. ``Mathlib/Algebra/Group/Basic.lean``).
    file_path: str
    #: Fully-qualified Lean declaration name (e.g. ``Nat.add_comm``).
    full_name: str
    #: ``(line, column)`` of the declaration's start, as recorded in the
    #: LeanDojo trace. Nothing in this codebase consumes these fields for
    #: source slicing. This differs from the parallel
    #: ``smolbench.deduction.lean.premises.Premise.start``/``.end``, whose
    #: *line* is provably 1-indexed (see ``premises.slice_full_decl``'s
    #: explicit ``start_line - 1`` conversion before list-indexing a
    #: file's lines). So this field's indexing convention is not
    #: independently exercised here. The fixture data is consistent with
    #: a 1-indexed line (``start == (1, 1)`` for a declaration at the very
    #: top of its file), but the column's indexing is not distinguishable
    #: from that alone. Treat both as opaque LeanDojo trace positions,
    #: unless a caller adds code that depends on the exact convention.
    start: tuple[int, int]
    #: ``(line, column)`` of the declaration's end. See `start`.
    end: tuple[int, int]
    #: The theorem's tactic-by-tactic trace, in proof order. Empty for
    #: theorems LeanDojo could not trace (see `has_proof`).
    traced_tactics: list[TracedTactic]

    @property
    def has_proof(self) -> bool:
        """True if LeanDojo recorded at least one traced tactic step.

        Empty usually means a term-mode or otherwise untraceable proof;
        `iter_with_proof` skips those theorems.
        """
        return len(self.traced_tactics) > 0


def _from_json(rec: dict) -> BenchmarkTheorem:
    """Parse one raw split-file JSON record into a `BenchmarkTheorem`.

    A raw tactic's ``annotated_tactic`` is nominally an ``[text, premises]``
    pair but some records give only ``[text]``; that and an explicit empty
    list both normalize to ``TracedTactic.premises == []``.
    """
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
    """Every theorem in ``<data_root()>/<kind>/<split>.json``, in file order.

    Memoized per ``(kind, split)`` (maxsize 8 covers all 6 combinations). The
    cache key does NOT include `data_root`'s current value, so repointing
    ``SMOLBENCH_LEAN_DATA`` mid-process keeps serving theorems from whichever
    root was active first; call `reset_caches` to force a re-read.

    Raises
    ------
    FileNotFoundError
        Split file missing -- the dataset is not bootstrapped; see
        ``notebooks/deduction/README.md``'s "Data bootstrap".
    """
    path = data_root() / kind / f"{split}.json"
    raw = json.loads(path.read_text())
    return [_from_json(r) for r in raw]


def iter_with_proof(kind: SplitKind = "random", split: Split = "val") -> Iterator[BenchmarkTheorem]:
    """Yield ``load_split(kind, split)``'s traced theorems, in file order.

    Skips theorems whose `has_proof` is False (typically term-mode).
    """
    for t in load_split(kind, split):
        if t.has_proof:
            yield t


def metadata() -> dict:
    """Load the benchmark's top-level ``metadata.json``.

    Keys include ``dataset_name``, ``creation_time``, ``from_repo``
    (``{url, commit}``) and ``leandojo_version``. Raises
    ``FileNotFoundError`` if the dataset is not bootstrapped.
    """
    return json.loads((data_root() / "metadata.json").read_text())


def replay_passing_path(kind: SplitKind, split: Split) -> Path:
    """Path to the `filter`-generated replay-passing sidecar for ``(kind, split)``.

    ``<data_root().parent>/replay_passing_<kind>_<split>.jsonl`` -- beside the
    dataset directory, so these small committed sidecars stay out of the
    wholesale-gitignored ~700 MB download. Not guaranteed to exist.
    """
    return data_root().parent / f"replay_passing_{kind}_{split}.jsonl"


def iter_replay_passing(kind: SplitKind = "random", split: Split = "val") -> Iterator[BenchmarkTheorem]:
    """Yield theorems recorded ``verdict == "success"`` in the replay sidecar.

    Membership comes from `replay_passing_path`; yielded in `load_split` file
    order.

    Raises
    ------
    FileNotFoundError
        Sidecar missing; produce it with `python -m
        smolbench.deduction.lean.cli filter --kind <kind> --split <split>`.
    """
    path = replay_passing_path(kind, split)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — run `python -m smolbench.deduction.lean.cli filter "
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

    Those loaders key only on their own arguments, never on `data_root()`, so
    call this after repointing ``SMOLBENCH_LEAN_DATA`` to force a re-read.
    `premises` is imported inside the body because it imports `data_root` from
    here; a top-level import would be a cycle that fails at package import.
    """
    load_split.cache_clear()

    # Lazy import to avoid the corpus <-> premises import cycle (see above).
    from . import premises

    premises._index.cache_clear()
    premises._traced_root.cache_clear()
    premises.slice_full_decl.cache_clear()
    premises._short_name_index.cache_clear()
    premises.referenced_premises.cache_clear()
