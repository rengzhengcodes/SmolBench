"""Load LeanDojo Benchmark 4 splits (per-theorem tactic traces).

`LeanDojo Benchmark 4 <https://zenodo.org/records/10929138>`_ is a mathlib4
snapshot (commit ``fe4454af``, March 2024) traced by LeanDojo; its parallel
premise corpus lives in ``smolbench.deduction.lean.premises``. Pool sizes and
bootstrap instructions: ``notebooks/deduction/README.md``.

Loaders are keyed by ``(kind, split)``; ``kind="novel_premises"`` is the harder
generalization slice (val/test theorems whose premises are under-represented in
train), ``"random"`` is i.i.d. The ~700 MB dataset is not shipped here; loaders
raise ``FileNotFoundError`` naming the remedy when a file is missing.

Loaders also accept a *post-cutoff* corpus: one traced at a recent mathlib4
commit and restricted, by declaration-name set difference against an older
commit, to theorems provably absent from that older snapshot. Such a corpus
carries an extra ``postcutoff`` block in `metadata()` and a per-row
``"postcutoff": true`` flag; see `postcutoff_metadata`.
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
    #: ``{full_name, def_path, def_pos, def_end_pos}`` -- lighter than
    #: ``smolbench.deduction.lean.premises.Premise`` (no ``code``/``kind``).
    #: ``full_name`` is the join key into ``premises.lookup`` (see
    #: ``context._render_hint_parts``). Empty for most tactics. Extracted from
    #: the raw ``annotated_tactic`` field by ``_from_json``.
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
    #: LeanDojo trace. Nothing here slices source with it, so its indexing
    #: convention is untested -- unlike
    #: ``smolbench.deduction.lean.premises.Premise.start``, whose *line* is
    #: provably 1-indexed (``premises.slice_full_decl`` converts with an
    #: explicit ``start_line - 1``). Treat both as opaque trace positions.
    start: tuple[int, int]
    #: ``(line, column)`` of the declaration's end. See `start`.
    end: tuple[int, int]
    #: The theorem's tactic-by-tactic trace, in proof order. Empty for
    #: theorems LeanDojo could not trace (see `has_proof`).
    traced_tactics: list[TracedTactic]
    #: True when this theorem's declaration NAME is absent from the corpus's
    #: `postcutoff` metadata block's ``old_commit`` trace -- i.e. it is
    #: provably post-cutoff by name-set difference, not by any date heuristic.
    #: Defaults False (no other field here has a default) so the ordinary
    #: 2024-03-24 benchmark, whose rows carry no ``postcutoff`` key, still
    #: parses. Must stay the LAST field: `BenchmarkTheorem` is frozen and every
    #: other field is required.
    postcutoff: bool = False

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
        # A row that omits the key predates the post-cutoff contract (or
        # simply isn't post-cutoff); treat that as False, not an error.
        postcutoff=bool(rec.get("postcutoff", False)),
    )


@lru_cache(maxsize=8)
def load_split(kind: SplitKind = "random", split: Split = "val") -> list[BenchmarkTheorem]:
    """Every theorem in ``<data_root()>/<kind>/<split>.json``, in file order.

    Memoized per ``(kind, split)`` (maxsize 8 covers all 6 combinations); the
    key excludes `data_root()`, so repointing ``SMOLBENCH_LEAN_DATA``
    mid-process keeps serving the first root until `reset_caches` runs.

    Raises
    ------
    FileNotFoundError
        Split file missing -- the dataset is not bootstrapped; see
        ``notebooks/deduction/README.md``'s "Data bootstrap".
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
    """
    for t in load_split(kind, split):
        if t.has_proof:
            yield t


#: Canonical order `eval_split_specs` reports its splits in. Fixed here rather
#: than read from directory-listing order, which is filesystem- and
#: machine-dependent: a holdout index built from these specs must index the same
#: theorems in the same order everywhere, or two machines' manifests disagree
#: over an ordering nobody chose.
_SPLIT_ORDER: tuple[Split, ...] = ("train", "val", "test")

#: The one split family `eval_split_specs` scans. ``novel_premises`` is
#: deliberately excluded: ``scripts/deduction/build_postcutoff_corpus.py`` writes
#: a ``novel_premises/`` directory for the post-cutoff corpus, but it is a real
#: COPY of ``random/``'s rows rather than an independently curated slice (see
#: ``notebooks/deduction/README.md``, "What's not in scope"), so indexing it
#: would re-index the same theorems for no gain. ``random`` is also the family
#: ``notebooks/deduction/run_study.py``'s ``build_config`` defaults to and the
#: one every sweep this study runs draws from.
_EVAL_SPLIT_KIND: SplitKind = "random"


def eval_split_specs() -> tuple[tuple[SplitKind, Split], ...]:
    """The ``(kind, split)`` pairs an eval holdout should cover in the ACTIVE corpus.

    Reports every ``<split>.json`` present under ``data_root() / "random"``, in
    the fixed `_SPLIT_ORDER`. See `_EVAL_SPLIT_KIND` for why only the ``random``
    family is scanned.

    Reads the filesystem on EVERY call and memoizes nothing -- not even in a
    module-level constant. Several callers repoint ``SMOLBENCH_LEAN_DATA``
    mid-process and rely on the next call seeing the new root, exactly as
    `metadata` / `postcutoff_metadata` already do; a cached result (or an
    import-time constant) would freeze the first corpus the process ever saw.

    Returns
    -------
    tuple of (SplitKind, Split)
        Non-empty, ordered ``train``, ``val``, ``test``, restricted to the split
        files that actually exist. Every pair is directly usable as
        `load_split`'s arguments.

    Raises
    ------
    FileNotFoundError
        ``data_root() / "random"`` does not exist -- the corpus is not
        bootstrapped.
    ValueError
        The directory exists but holds none of the recognised split files.
        Returning an empty tuple instead would be a silent no-op: a holdout
        index built from it would decontaminate nothing while still reporting
        success.
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
            "decontaminates nothing; re-bootstrap the corpus (see "
            "notebooks/deduction/README.md's \"Data bootstrap\")"
        )
    return specs


def metadata() -> dict:
    """Load the benchmark's top-level ``metadata.json``.

    Returns
    -------
    dict
        Keys include ``dataset_name``, ``creation_time``, ``from_repo``
        (``{url, commit}``) and ``leandojo_version``.

    Raises
    ------
    FileNotFoundError
        Dataset not bootstrapped.
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

    Reads through `metadata()` on every call rather than caching separately --
    `metadata()` itself is deliberately uncached (several callers repoint
    ``SMOLBENCH_LEAN_DATA`` mid-process and rely on a fresh read), and adding a
    cache here would let a stale block survive a root switch.

    Returns
    -------
    dict | None
        The block verbatim (``method``, ``new_commit``, ``new_commit_date``,
        ``old_commit``, ``old_commit_date``, ``target_date``, ``n_new_decls``,
        ``n_old_decls``, ``n_postcutoff_decls``), or None for an ordinary
        (non-post-cutoff) corpus.

    Raises
    ------
    FileNotFoundError
        Propagated from `metadata()`: dataset not bootstrapped.
    ValueError
        The block is present but `metadata()`'s ``from_repo.commit`` disagrees
        with the block's ``new_commit`` -- a corpus traced at one commit cannot
        be a name-set difference computed at another, so the file is
        internally incoherent and must not be trusted silently.
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

    Note this can still raise: an incoherent corpus (see `postcutoff_metadata`'s
    ``Raises``) must not silently report False, so this function propagates
    `postcutoff_metadata`'s `ValueError` rather than swallowing it.

    Raises
    ------
    FileNotFoundError
        Propagated from `postcutoff_metadata`.
    ValueError
        Propagated from `postcutoff_metadata`.
    """
    return postcutoff_metadata() is not None


def replay_passing_path(kind: SplitKind, split: Split) -> Path:
    """Path to the `filter`-generated replay-passing sidecar for ``(kind, split)``.

    ``<data_root().parent>/replay_passing_<kind>_<split>.jsonl`` -- beside the
    dataset directory, so these small committed sidecars stay out of the
    gitignored ~700 MB download. Not guaranteed to exist.
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
    """
    load_split.cache_clear()

    # Lazy import to avoid the corpus <-> premises import cycle.
    from . import premises

    premises._index.cache_clear()
    premises._traced_root.cache_clear()
    premises.slice_full_decl.cache_clear()
    premises._short_name_index.cache_clear()
    premises.referenced_premises.cache_clear()
