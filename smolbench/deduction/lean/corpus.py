"""Load post-cutoff LeanDojo-v2 theorem traces.

Benchmark 4 is a March 2024 ``fe4454af`` mathlib4 trace; its premise corpus is
``smolbench.deduction.lean.premises``. The ~700 MB corpus is not shipped;
missing files name the ``notebooks/deduction/README.md`` bootstrap remedy.
Post-cutoff corpora require recent-trace name-set difference from an older
commit, matching metadata, and row flags so plain Benchmark 4 exports cannot
silently pass as post-cutoff.
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
    """Return ``SMOLBENCH_LEAN_DATA`` or the installed package's dataset root.

    Never use cwd. Read per call so late environment changes apply; call
    `reset_caches` for cached loaders.
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

    #: Proof tactic text.
    tactic: str
    #: State before the tactic.
    state_before: str
    #: State after the tactic.
    state_after: str
    #: Referenced ``{full_name, def_path, def_pos, def_end_pos}`` records, lighter than
    #: ``premises.Premise`` because they omit ``code``/``kind``; ``full_name`` is the
    #: join key to ``premises.lookup``. Empty when none.
    premises: list[dict]


@dataclass(frozen=True)
class BenchmarkTheorem:
    """One theorem entry from a LeanDojo Benchmark 4 ``<kind>/<split>.json`` file."""

    #: Traced repository URL.
    url: str
    #: Traced commit hash.
    commit: str
    #: Declaring path relative to the repository.
    file_path: str
    #: Fully qualified declaration name.
    full_name: str
    #: Trace start position; opaque because this module never slices source.
    start: tuple[int, int]
    #: Trace end position.
    end: tuple[int, int]
    #: Tactics in proof order; empty for untraceable proofs.
    traced_tactics: list[TracedTactic]
    #: Name-set-difference post-cutoff flag, not a date heuristic.
    postcutoff: bool

    @property
    def has_proof(self) -> bool:
        """Whether LeanDojo recorded a tactic step."""
        return len(self.traced_tactics) > 0


def _from_json(rec: dict) -> BenchmarkTheorem:
    """Parse one raw split-file JSON record into a `BenchmarkTheorem`.

    Single-item ``annotated_tactic`` values normalize to empty premises.

    Parameters
    ----------
    rec : dict

    Returns
    -------
    BenchmarkTheorem
        Parsed theorem.
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
def load_split(
    kind: SplitKind = "random", split: Split = "val"
) -> list[BenchmarkTheorem]:
    """Load a split in file order.

    The cache excludes `data_root()`, so call `reset_caches` after repointing
    ``SMOLBENCH_LEAN_DATA``.

    Parameters
    ----------
    kind : SplitKind, optional
    split : Split, optional

    Returns
    -------
    list[BenchmarkTheorem]
        Theorems in file order.

    Raises
    ------
    FileNotFoundError
        Missing split file with bootstrap remedy.
    """
    path = data_root() / kind / f"{split}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — the LeanDojo Benchmark 4 dataset is not "
            'bootstrapped; see notebooks/deduction/README.md\'s "Data bootstrap"'
        )
    raw = json.loads(path.read_text())
    return [_from_json(r) for r in raw]


def iter_with_proof(
    kind: SplitKind = "random", split: Split = "val"
) -> Iterator[BenchmarkTheorem]:
    """Yield traced theorems in file order.

    Parameters
    ----------
    kind : SplitKind, optional
    split : Split, optional

    Yields
    ------
    BenchmarkTheorem
        Traced theorem.
    """
    for t in load_split(kind, split):
        if t.has_proof:
            yield t


#: Fixed order keeps holdout indexes machine-independent.
def metadata() -> dict:
    """Load ``metadata.json`` keys ``dataset_name``, ``creation_time``, ``from_repo``
    (``{url, commit}``), and ``leandojo_version``; raise `FileNotFoundError` if absent.
    """
    path = data_root() / "metadata.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — the LeanDojo Benchmark 4 dataset is not "
            'bootstrapped; see notebooks/deduction/README.md\'s "Data bootstrap"'
        )
    return json.loads(path.read_text())


def postcutoff_metadata() -> dict | None:
    """Return the ``postcutoff`` block, if present.

    Do not cache across roots. Reject a mismatched ``new_commit`` because the
    name-set difference and trace would otherwise describe different corpora.
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
    """Whether the corpus has post-cutoff metadata.

    Propagate incoherence rather than silently returning false.
    """
    return postcutoff_metadata() is not None


def replay_passing_path(kind: SplitKind, split: Split) -> Path:
    """Return the `filter` replay-passing sidecar path.

    The sidecar sits beside the dataset so it stays outside the gitignored
    ~700 MB download.

    Parameters
    ----------
    kind : SplitKind
    split : Split

    Returns
    -------
    Path
        Replay-passing sidecar path.
    """
    return data_root().parent / f"replay_passing_{kind}_{split}.jsonl"


def iter_replay_passing(
    kind: SplitKind = "random", split: Split = "val"
) -> Iterator[BenchmarkTheorem]:
    """Yield replay-success theorems in split-file order.

    Parameters
    ----------
    kind : SplitKind, optional
    split : Split, optional

    Yields
    ------
    BenchmarkTheorem
        Replay-success theorem.

    Raises
    ------
    FileNotFoundError
        Missing sidecar with the required `filter` command.
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
    """Clear corpus and premises caches after repointing ``SMOLBENCH_LEAN_DATA``."""
    load_split.cache_clear()

    # Avoid the corpus <-> premises import cycle.
    from . import premises  # lazy to keep corpus cheap; pylint: disable=cyclic-import

    premises._index.cache_clear()
    premises._traced_root.cache_clear()
    premises.slice_full_decl.cache_clear()
    premises._short_name_index.cache_clear()
    premises.referenced_premises.cache_clear()
