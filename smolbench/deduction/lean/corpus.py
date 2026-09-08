"""Load required post-cutoff LeanDojo-v2 theorem traces.

`LeanDojo Benchmark 4 <https://zenodo.org/records/10929138>`_ is a mathlib4
snapshot (commit ``fe4454af``, March 2024) traced by LeanDojo; its parallel
premise corpus lives in ``smolbench.deduction.lean.premises``. Pool sizes and
bootstrap instructions: ``notebooks/deduction/README.md``.

Loaders are keyed by ``(kind, split)``; the sole ``"random"`` family is i.i.d.
The ~700 MB dataset is not shipped here; loaders raise ``FileNotFoundError``
naming the remedy when a file is missing. A corpus must be traced at a recent
mathlib4 commit, restricted by declaration-name set difference against an
older commit, and carry both the `metadata()` ``postcutoff`` block and each
row's ``"postcutoff": true`` flag. A plain LeanDojo Benchmark 4 export is
refused; see `postcutoff_metadata`.
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
    ``notebooks/deduction/data/leandojo_benchmark_4`` anchored off the installed
    ``smolbench`` package, never cwd. Read at *call* time, so a late-set env var
    takes effect -- but call `reset_caches` to drop stale memoized results.
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
SplitKind = Literal["random"]


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
    #: ``{full_name, def_path, def_pos, def_end_pos}`` -- lighter than
    #: ``premises.Premise`` (no ``code``/``kind``). ``full_name`` joins into
    #: ``premises.lookup``. Empty for most tactics.
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
    #: LeanDojo trace. Nothing here slices source with it, unlike
    #: ``premises.Premise.start`` (provably 1-indexed); treat both as opaque
    #: trace positions.
    start: tuple[int, int]
    #: ``(line, column)`` of the declaration's end. See `start`.
    end: tuple[int, int]
    #: The theorem's tactic-by-tactic trace, in proof order. Empty for
    #: theorems LeanDojo could not trace (see `has_proof`).
    traced_tactics: list[TracedTactic]
    #: True when this theorem's name is absent from the corpus's `postcutoff`
    #: metadata block's ``old_commit`` trace -- i.e. provably post-cutoff by
    #: name-set difference, not a date heuristic.
    postcutoff: bool

    @property
    def has_proof(self) -> bool:
        """True if LeanDojo recorded at least one traced tactic step.

        Empty usually means a term-mode or otherwise untraceable proof.
        """
        return len(self.traced_tactics) > 0


def _from_json(rec: dict) -> BenchmarkTheorem:
    """Parse one raw split-file JSON record into a `BenchmarkTheorem`.

    ``annotated_tactic`` is nominally an ``[text, premises]`` pair but some
    records give only ``[text]``; both normalize to ``premises == []``.

    Parameters
    ----------
    rec : dict
        Raw split-file JSON record.

    Returns
    -------
    BenchmarkTheorem
        Parsed benchmark theorem.
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
        postcutoff=bool(rec["postcutoff"]),
    )


@lru_cache(maxsize=8)
def load_split(kind: SplitKind = "random", split: Split = "val") -> list[BenchmarkTheorem]:
    """Every theorem in ``<data_root()>/<kind>/<split>.json``, in file order.

    Memoized per ``(kind, split)`` (maxsize 8 covers all 6 combinations); the
    key excludes `data_root()`, so repointing ``SMOLBENCH_LEAN_DATA``
    mid-process keeps serving the first root until `reset_caches` runs.

    Parameters
    ----------
    kind : SplitKind, optional
        Corpus split family.
    split : Split, optional
        Corpus partition to load.

    Returns
    -------
    list[BenchmarkTheorem]
        Every theorem in ``<data_root()>/<kind>/<split>.json``, in file order.

    Raises
    ------
    FileNotFoundError
        If the split file is missing, naming the remedy.
    """
    path = data_root() / kind / f"{split}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — the LeanDojo Benchmark 4 dataset is not "
            "bootstrapped; see notebooks/deduction/README.md's \"Data bootstrap\""
        )
    raw = json.loads(path.read_text())
    return [_from_json(r) for r in raw]


def iter_with_proof(kind: SplitKind = "random", split: Split = "val") -> Iterator[BenchmarkTheorem]:
    """Yield ``load_split(kind, split)``'s traced theorems, in file order.

    Skips theorems whose `has_proof` is False (typically term-mode).

    Parameters
    ----------
    kind : SplitKind, optional
        Corpus split family.
    split : Split, optional
        Corpus partition to scan.

    Yields
    ------
    BenchmarkTheorem
        Traced theorem in file order.
    """
    for t in load_split(kind, split):
        if t.has_proof:
            yield t


#: Canonical order `eval_split_specs` reports splits in, fixed here rather
#: than read from directory-listing order (filesystem- and
#: machine-dependent): a holdout index built from these specs must index the
#: same theorems in the same order everywhere.
_SPLIT_ORDER: tuple[Split, ...] = ("train", "val", "test")

#: The one split family `eval_split_specs` scans. The post-cutoff builder emits
#: no duplicate compatibility family, and this is the family the study runs.
_EVAL_SPLIT_KIND: SplitKind = "random"


def eval_split_specs() -> tuple[tuple[SplitKind, Split], ...]:
    """The ``(kind, split)`` pairs an eval holdout should cover in the active corpus.

    Reports every ``<split>.json`` present under ``data_root() / "random"``,
    in the fixed `_SPLIT_ORDER` (see `_EVAL_SPLIT_KIND` for why only
    ``random`` is scanned).

    Reads the filesystem on every call and memoizes nothing, not even in a
    module-level constant: several callers repoint ``SMOLBENCH_LEAN_DATA``
    mid-process and rely on the next call seeing the new root, as `metadata`
    already does.

    Raises `FileNotFoundError` if ``data_root() / "random"`` doesn't exist, or
    `ValueError` if it exists but holds none of the recognised split files --
    an empty tuple would be a silent no-op, protecting nothing while
    still reporting success.
    """
    root = data_root()
    kind_dir = root / _EVAL_SPLIT_KIND
    if not kind_dir.is_dir():
        raise FileNotFoundError(
            f"{kind_dir} not found — the corpus at data_root()={root} is not "
            "bootstrapped; see notebooks/deduction/README.md's \"Data bootstrap\""
        )
    specs = tuple(
        (_EVAL_SPLIT_KIND, split)
        for split in _SPLIT_ORDER
        if (kind_dir / f"{split}.json").is_file()
    )
    if not specs:
        expected = ", ".join(f"{split}.json" for split in _SPLIT_ORDER)
        raise ValueError(
            f"{kind_dir} holds no recognised split file (expected at least one of "
            f"{expected}) — an eval holdout built from an empty spec list "
            "protects nothing; re-bootstrap the corpus (see "
            "notebooks/deduction/README.md's \"Data bootstrap\")"
        )
    return specs


def metadata() -> dict:
    """Load the benchmark's top-level ``metadata.json``.

    Keys include ``dataset_name``, ``creation_time``, ``from_repo``
    (``{url, commit}``) and ``leandojo_version``. Raises `FileNotFoundError`
    if not bootstrapped.
    """
    path = data_root() / "metadata.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — the LeanDojo Benchmark 4 dataset is not "
            "bootstrapped; see notebooks/deduction/README.md's \"Data bootstrap\""
        )
    return json.loads(path.read_text())


def postcutoff_metadata() -> dict | None:
    """The `metadata()`'s ``postcutoff`` block, or None when absent.

    Reads through `metadata()` on every call rather than caching separately:
    `metadata()` is deliberately uncached (callers repoint
    ``SMOLBENCH_LEAN_DATA`` mid-process), and a cache here would let a stale
    block survive a root switch.

    Raises `ValueError` if the block's ``new_commit`` disagrees with
    `metadata()`'s ``from_repo.commit`` -- a corpus traced at one commit can't
    be a name-set difference computed at another, so the file is internally
    incoherent and must not be trusted silently.
    """
    meta = metadata()
    block = meta.get("postcutoff")
    if block is None:
        return None
    traced_commit = meta["from_repo"]["commit"]
    if traced_commit != block["new_commit"]:
        raise ValueError(
            f"{data_root() / 'metadata.json'} is incoherent: from_repo.commit="
            f"{traced_commit!r} but postcutoff.new_commit={block['new_commit']!r} "
            "-- a corpus traced at one commit cannot be a name-set difference "
            "computed at another"
        )
    return block


def is_postcutoff_corpus() -> bool:
    """True if the current corpus carries a `postcutoff_metadata` block.

    Propagates `postcutoff_metadata`'s exceptions rather than swallowing
    them: an incoherent corpus must not silently report False.
    """
    return postcutoff_metadata() is not None


def replay_passing_path(kind: SplitKind, split: Split) -> Path:
    """Path to the `filter`-generated replay-passing sidecar for ``(kind, split)``.

    ``<data_root().parent>/replay_passing_<kind>_<split>.jsonl`` -- beside the
    dataset directory, so these small committed sidecars stay out of the
    gitignored ~700 MB download. Not guaranteed to exist.

    Parameters
    ----------
    kind : SplitKind
        Corpus split family.
    split : Split
        Corpus partition.

    Returns
    -------
    Path
        `filter`-generated replay-passing sidecar path.
    """
    return data_root().parent / f"replay_passing_{kind}_{split}.jsonl"


def iter_replay_passing(kind: SplitKind = "random", split: Split = "val") -> Iterator[BenchmarkTheorem]:
    """Yield theorems recorded ``verdict == "success"`` in the replay sidecar.

    Membership comes from `replay_passing_path`; yielded in `load_split` file
    order.

    Parameters
    ----------
    kind : SplitKind, optional
        Corpus split family.
    split : Split, optional
        Corpus partition to scan.

    Yields
    ------
    BenchmarkTheorem
        Theorem recorded with ``verdict == "success"`` in the replay sidecar.

    Raises
    ------
    FileNotFoundError
        If the sidecar is missing, naming the `filter` command to run.
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
    """
    load_split.cache_clear()

    # Lazy import to avoid the corpus <-> premises import cycle.
    from . import premises

    premises._index.cache_clear()
    premises._traced_root.cache_clear()
    premises.slice_full_decl.cache_clear()
    premises._short_name_index.cache_clear()
    premises.referenced_premises.cache_clear()
