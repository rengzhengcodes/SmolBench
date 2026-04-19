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


if __name__ == "__main__":
    r = TrialResult(
        target_id="ENNReal.le_rpow_one_div_iff",
        file_path="Mathlib/Analysis/SpecialFunctions/Pow/NNReal.lean",
        condition="ext-nodoc-d2",
        context_chars=3789,
        model="stub",
        temperature=0.0,
        k_index=0,
        proof_text="sorry",
        ok=False,
        error="contains sorry",
        tactics_applied=0,
        tokens_in=None,
        tokens_out=None,
        wall_ms=12,
        timestamp=now_iso(),
    )
    d = r.to_json_dict()
    r2 = TrialResult.from_json_dict(d)
    assert r == r2, "round-trip failed"
    print("round-trip ok")
    print(d)
