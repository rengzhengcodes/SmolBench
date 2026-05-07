"""Load LeanDojo Benchmark 4 splits and the premise corpus."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Literal

DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "leandojo_benchmark_4"

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
    path = DATA_ROOT / kind / f"{split}.json"
    raw = json.loads(path.read_text())
    return [_from_json(r) for r in raw]


def iter_with_proof(kind: SplitKind = "random", split: Split = "val") -> Iterator[BenchmarkTheorem]:
    for t in load_split(kind, split):
        if t.has_proof:
            yield t


def metadata() -> dict:
    return json.loads((DATA_ROOT / "metadata.json").read_text())


def replay_passing_path(kind: SplitKind, split: Split) -> Path:
    return DATA_ROOT.parent / f"replay_passing_{kind}_{split}.jsonl"


def iter_replay_passing(kind: SplitKind = "random", split: Split = "val") -> Iterator[BenchmarkTheorem]:
    """Yield theorems whose ground-truth replay was recorded as `success`.

    Reads `data/replay_passing_<kind>_<split>.jsonl`, produced by
    `python -m leaneval.cli filter --kind <kind> --split <split>`.
    """
    path = replay_passing_path(kind, split)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — run `python -m leaneval.cli filter "
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
