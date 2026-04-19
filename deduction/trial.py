"""
Result of a single LLM proof-synthesis trial: one (target, condition, k_index)
tuple. Stored to JSONL for analysis.

Condition strings:
  "intensional"
  "ext-nodoc-d{1..4}"  — extensional, Lean comments/docstrings stripped
  "ext-doc-d{1..4}"    — extensional, docstrings kept

All fields are immutable; use `TrialResult.from_json_dict` to load persisted
records. The schema deliberately lives independent of the harness so downstream
analysis can import it without pulling in lean_dojo.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True, slots=True)
class TrialResult:
    target_id: str
    file_path: str

    condition: str
    context_chars: int

    model: str
    temperature: float
    k_index: int
    proof_text: str

    ok: bool
    error: Optional[str]
    tactics_applied: int

    tokens_in: Optional[int]
    tokens_out: Optional[int]
    wall_ms: int
    timestamp: str

    def to_json_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json_dict(cls, d: dict) -> "TrialResult":
        return cls(**d)


def now_iso() -> str:
    """Wall-clock timestamp for trial records."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
