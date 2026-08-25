"""Load LeanDojo Benchmark 4 splits and the premise corpus.

`LeanDojo Benchmark 4 <https://zenodo.org/records/10929138>`_ is a
snapshot of mathlib4 (commit ``fe4454af``, March 2024), traced by
`LeanDojo <https://leandojo.org>`_. It provides two things: every
theorem's tactic-by-tactic proof state transitions (this module), and a
corpus of every premise (theorem/def/etc.) declared in the traced repo,
with source position and containing file
(``smolbench.deduction.lean.premises``). See
``notebooks/deduction/README.md`` for the full dataset description, pool
sizes, and bootstrap instructions.

Two independent axes select which slice of the benchmark to load. Every
loader in this module threads both through as ``(kind, split)``:

- ``SplitKind`` (``kind``) -- ``"random"`` (an i.i.d. train/val/test
  split) or ``"novel_premises"`` (val/test theorems chosen so their
  premises are under-represented in train -- the harder generalization
  slice).
- ``Split`` (``split``) -- ``"train"``, ``"val"``, or ``"test"`` within a
  ``kind``.

The dataset itself is not shipped in this repo (it is a ~700 MB external
download). Every loader here raises ``FileNotFoundError`` with an
actionable remedy when the expected file is missing, rather than failing
with a bare "file not found".
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
    """Get the root directory of the LeanDojo Benchmark 4 dataset.

    Resolution order:
      1. The ``SMOLBENCH_LEAN_DATA`` environment variable, if set.
      2. ``notebooks/deduction/data/leandojo_benchmark_4`` under the repo root.

    The default is anchored to the installed ``smolbench`` package
    (``Path(smolbench.__file__).resolve().parents[1]`` is the repo root),
    not to the current working directory. This anchors off the top-level
    package, instead of counting ``parents`` up from *this* file, which
    keeps the resolution correct no matter how deeply this module is
    nested. So moving the subpackage (e.g. ``smolbench/lean`` ->
    ``smolbench/deduction/lean``) cannot silently break it. This mirrors
    the repo-anchoring pattern used for ``_DEFAULT_STATE_FILE`` in
    ``smolbench/evals/ec2.py`` and ``repo_root()`` in
    ``smolbench/induction/experiment.py``. Notebook
    kernels and test runners invoke this module from arbitrary cwds
    (temp dirs included), so a cwd-relative default would silently
    resolve to the wrong place, or nowhere at all, depending on who
    imports the module.

    This reads the env var at *call* time, not import time. So callers
    (including tests) may set ``SMOLBENCH_LEAN_DATA`` at any point before
    calling this function, or before calling `reset_caches` to drop any
    memoized results computed under a stale value.

    Returns
    -------
    Path
        Directory containing ``metadata.json``, ``corpus.jsonl``, and the
        ``random``/``novel_premises`` split subdirectories. Not
        guaranteed to exist; callers that read files under it raise on a
        missing path.
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
    """One tactic application recorded during LeanDojo's trace of a proof.

    Corresponds to one entry of a benchmark JSON record's ``traced_tactics``
    list (see ``_from_json``).
    """

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

        Theorems with an empty `traced_tactics` are typically term-mode
        proofs or otherwise untraceable by LeanDojo's tactic-mode tracer
        (see ``notebooks/deduction/README.md``'s "What's not in scope"); such
        theorems are excluded by `iter_with_proof`.

        Returns
        -------
        bool
            ``len(self.traced_tactics) > 0``.
        """
        return len(self.traced_tactics) > 0


def _from_json(rec: dict) -> BenchmarkTheorem:
    """Parse one raw split-file JSON record into a `BenchmarkTheorem`.

    Parameters
    ----------
    rec : dict
        One element of a ``<kind>/<split>.json`` array, in the LeanDojo
        Benchmark 4 schema: ``url``, ``commit``, ``file_path``,
        ``full_name``, ``start``, ``end``, and ``traced_tactics`` (each with
        ``tactic``, ``annotated_tactic``, ``state_before``, ``state_after``).

    Returns
    -------
    BenchmarkTheorem
        The parsed theorem, with each ``traced_tactics`` entry converted to
        a `TracedTactic`.

    Notes
    -----
    Premise-extraction contract: each raw tactic's ``annotated_tactic`` is
    nominally a ``[annotated_text, premises]`` pair. But some records give
    only ``[annotated_text]`` (length 1, no premises element at all),
    rather than an explicit ``[annotated_text, []]``. This function reads
    ``annotated[1] if len(annotated) > 1 else []``, which normalizes both
    no-premise shapes -- a missing second element, or an explicit empty
    list -- to ``TracedTactic.premises == []``. So no caller downstream
    needs to length-check ``annotated_tactic`` itself.
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
    """Load and parse one ``<kind>/<split>.json`` benchmark split file.

    Parameters
    ----------
    kind : {"random", "novel_premises"}, default "random"
        Which split axis to load (see the module docstring).
    split : {"train", "val", "test"}, default "val"
        Which train/val/test partition of `kind` to load.

    Returns
    -------
    list of BenchmarkTheorem
        Every theorem record in ``<data_root()>/<kind>/<split>.json``,
        parsed via `_from_json`, in file order.

    Raises
    ------
    FileNotFoundError
        If ``<data_root()>/<kind>/<split>.json`` does not exist -- the
        dataset has not been bootstrapped yet. See ``notebooks/deduction/
        README.md``'s "Data bootstrap" section for the Zenodo download and
        unpack steps. (Distinct from `iter_replay_passing`'s
        ``FileNotFoundError``, which reports a missing `filter`-generated
        sidecar rather than a missing raw split file.)

    Notes
    -----
    This memoizes per ``(kind, split)`` argument pair, via
    `functools.lru_cache` (``maxsize=8`` comfortably covers all 6
    combinations, plus slack). The cache key does NOT include
    `data_root`'s current return value. So repointing
    ``SMOLBENCH_LEAN_DATA`` mid-process (as tests do, via
    ``monkeypatch.setenv``) keeps returning theorems loaded from whichever
    root was active the first time a given ``(kind, split)`` pair was
    requested. Call `reset_caches` after changing the environment
    variable, to force this loader (and the other memoized loaders it
    clears) to re-read from disk.
    """
    path = data_root() / kind / f"{split}.json"
    raw = json.loads(path.read_text())
    return [_from_json(r) for r in raw]


def iter_with_proof(kind: SplitKind = "random", split: Split = "val") -> Iterator[BenchmarkTheorem]:
    """Yield theorems in ``(kind, split)`` that LeanDojo successfully traced.

    Parameters
    ----------
    kind : {"random", "novel_premises"}, default "random"
        Forwarded to `load_split`.
    split : {"train", "val", "test"}, default "val"
        Forwarded to `load_split`.

    Yields
    ------
    BenchmarkTheorem
        Each theorem from ``load_split(kind, split)`` whose `has_proof` is
        True, in file order; untraced (typically term-mode) theorems are
        skipped.
    """
    for t in load_split(kind, split):
        if t.has_proof:
            yield t


def metadata() -> dict:
    """Load the benchmark's top-level ``metadata.json``.

    Returns
    -------
    dict
        Parsed JSON with keys including ``dataset_name``, ``creation_time``,
        ``from_repo`` (``{url, commit}``), and ``leandojo_version``.

    Raises
    ------
    FileNotFoundError
        If ``<data_root()>/metadata.json`` does not exist (dataset not
        bootstrapped -- see `load_split`'s ``Raises`` section for the
        remedy).
    """
    return json.loads((data_root() / "metadata.json").read_text())


def replay_passing_path(kind: SplitKind, split: Split) -> Path:
    """Path to the `filter`-generated replay-passing sidecar for ``(kind, split)``.

    Parameters
    ----------
    kind : SplitKind
        Split kind the sidecar covers.
    split : Split
        Split partition the sidecar covers.

    Returns
    -------
    Path
        ``<data_root().parent>/replay_passing_<kind>_<split>.jsonl``. Not
        guaranteed to exist -- see `iter_replay_passing`'s precondition.

    Notes
    -----
    Design: this path anchors on ``data_root().parent`` (the ``data/``
    directory that contains ``leandojo_benchmark_4/``), not on
    `data_root` itself. This matches the pre-move layout, where
    ``replay_passing_*.jsonl`` sidecars sat alongside the
    ``leandojo_benchmark_4/`` directory rather than inside it. It also
    keeps these small, committed sidecars out of the large,
    wholesale-gitignored dataset directory (see ``notebooks/deduction/
    README.md``'s "Data bootstrap": the sidecars are committed once
    generated, unlike the raw ~700 MB dataset download).
    """
    return data_root().parent / f"replay_passing_{kind}_{split}.jsonl"


def iter_replay_passing(kind: SplitKind = "random", split: Split = "val") -> Iterator[BenchmarkTheorem]:
    """Yield theorems whose ground-truth replay was recorded as `success`.

    Parameters
    ----------
    kind : {"random", "novel_premises"}, default "random"
        Forwarded to `load_split` and `replay_passing_path`.
    split : {"train", "val", "test"}, default "val"
        Forwarded to `load_split` and `replay_passing_path`.

    Yields
    ------
    BenchmarkTheorem
        Each theorem from ``load_split(kind, split)`` whose ``full_name``
        appears with ``verdict == "success"`` in
        `data/replay_passing_<kind>_<split>.jsonl`.

    Raises
    ------
    FileNotFoundError
        If the sidecar file does not exist. Produce it first with
        `python -m smolbench.deduction.lean.cli filter --kind <kind> --split <split>`.
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

    `data_root()` re-reads `SMOLBENCH_LEAN_DATA` on every call. But the
    lru_cache-memoized loaders in this module (`load_split`), and in
    `smolbench.deduction.lean.premises` (`_index`, `_traced_root`,
    `slice_full_decl`, `_short_name_index`,
    `referenced_premises`), key their results only on their own
    arguments, not on the current `data_root()` value. A test that
    repoints `SMOLBENCH_LEAN_DATA` to a fixture directory mid-run would
    otherwise keep seeing theorems/premises loaded from whatever root was
    active the first time each cache was populated. Call this after
    changing `SMOLBENCH_LEAN_DATA` (directly or via
    `monkeypatch.setenv`), to force every cache to re-read from disk on
    next use.

    Notes
    -----
    This function imports `smolbench.deduction.lean.premises` inside its
    own body, not at module level, because `premises` imports `data_root`
    from `corpus` (this module). A top-level `from . import premises`
    here would create an import cycle (`corpus` -> `premises` ->
    `corpus`) that fails at package-import time. This function defers the
    import to call time, which sidesteps that: by the time anything calls
    `reset_caches()`, both modules are already fully initialized.
    """
    load_split.cache_clear()

    # Lazy import to avoid the corpus <-> premises import cycle (see above).
    from . import premises

    premises._index.cache_clear()
    premises._traced_root.cache_clear()
    premises.slice_full_decl.cache_clear()
    premises._short_name_index.cache_clear()
    premises.referenced_premises.cache_clear()
