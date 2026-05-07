"""Open a Dojo session, replay tactics, return a verdict.

Two patterns:
  - `verify_proof_tail(bt, k, tail)` — opens a Dojo session, replays prefix,
    runs the tail. One full session per call. Used by `run-cell`.
  - `open_at_step(bt, k)` + `try_tail(dojo, state, tail)` — opens once and
    yields the state at step k; many `try_tail` calls can branch from the
    same checkpoint without re-replaying the prefix. Used by `sweep`, where
    multiple rungs × models × rollouts share a single Dojo session per
    (theorem, k) — saves a Lean process startup per cell.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

from lean_dojo import (
    Dojo,
    LeanError,
    LeanGitRepo,
    ProofFinished,
    ProofGivenUp,
    TacticState,
    Theorem,
)

from .corpus import BenchmarkTheorem

Verdict = Literal["success", "lean_error", "incomplete", "given_up", "exception", "replay_failed"]


@dataclass
class ReplayResult:
    theorem: str
    verdict: Verdict
    tactics_applied: int
    tactics_total: int
    error: str | None = None
    final_state_pp: str | None = None


def _to_dojo_theorem(bt: BenchmarkTheorem) -> Theorem:
    repo = LeanGitRepo(bt.url, bt.commit)
    return Theorem(repo, Path(bt.file_path), bt.full_name)


def replay_ground_truth(bt: BenchmarkTheorem, timeout: int = 600) -> ReplayResult:
    """Open Dojo, apply the recorded tactics in order, report verdict."""
    if not bt.has_proof:
        return ReplayResult(bt.full_name, "incomplete", 0, 0, error="no traced tactics")

    thm = _to_dojo_theorem(bt)
    tactics = [tt.tactic for tt in bt.traced_tactics]

    try:
        with Dojo(thm, timeout=timeout) as (dojo, state):
            for i, tac in enumerate(tactics):
                state = dojo.run_tac(state, tac)
                if isinstance(state, LeanError):
                    return ReplayResult(
                        bt.full_name, "lean_error", i, len(tactics),
                        error=state.error,
                    )
                if isinstance(state, ProofGivenUp):
                    return ReplayResult(
                        bt.full_name, "given_up", i + 1, len(tactics),
                    )
                if isinstance(state, ProofFinished):
                    return ReplayResult(
                        bt.full_name, "success", i + 1, len(tactics),
                    )
            pp = state.pp if isinstance(state, TacticState) else None
            return ReplayResult(
                bt.full_name, "incomplete", len(tactics), len(tactics),
                final_state_pp=pp,
            )
    except Exception as exc:  # noqa: BLE001
        return ReplayResult(
            bt.full_name, "exception", 0, len(tactics), error=f"{type(exc).__name__}: {exc}",
        )


@dataclass
class ProofResult:
    theorem: str
    verdict: Verdict
    tail_tried: str
    error: str | None = None
    final_state_pp: str | None = None


def _split_tactics(tail: str) -> list[str]:
    """Split an LLM-produced tail into individual tactics.

    Dojo's `run_tac` expects a single tactic per call. LLMs typically emit
    one tactic per line. We split on newlines and drop empty lines; we do
    *not* split on `;` or `<;>` since those are valid Lean tactic combinators
    (`t1 <;> t2` and `t1 ; t2` are each one tactic that Dojo parses fine).
    """
    return [line.strip() for line in tail.splitlines() if line.strip()]


def try_tail(dojo, state_at_k, tail: str, theorem_name: str) -> ProofResult:
    """Apply each line of `tail` as a separate tactic from `state_at_k`.

    Dojo states are immutable and `run_tac` returns a new state, so it's safe
    to call this multiple times against the same `state_at_k` checkpoint —
    each call branches independently, no re-replay needed.
    """
    tactics = _split_tactics(tail)
    if not tactics:
        return ProofResult(theorem_name, "lean_error", tail, error="empty tail")

    state = state_at_k
    for i, tac in enumerate(tactics):
        state = dojo.run_tac(state, tac)
        if isinstance(state, ProofFinished):
            return ProofResult(theorem_name, "success", tail)
        if isinstance(state, LeanError):
            return ProofResult(
                theorem_name, "lean_error", tail,
                error=f"tail step {i+1}/{len(tactics)} ({tac!r}): {state.error}",
            )
        if isinstance(state, ProofGivenUp):
            return ProofResult(theorem_name, "given_up", tail)
    pp = state.pp if isinstance(state, TacticState) else None
    return ProofResult(theorem_name, "incomplete", tail, final_state_pp=pp)


@contextlib.contextmanager
def open_at_step(bt: BenchmarkTheorem, k: int, timeout: int = 600) -> Iterator[tuple]:
    """Open Dojo, replay tactics 0..k-1, yield `(dojo, state_at_k)`.

    Use as `with open_at_step(bt, k) as (dojo, state): ... try_tail(dojo, state, tail)`.
    Replays prefix once; multiple `try_tail` calls then branch from the same
    checkpoint. Raises `RuntimeError` if the prefix replay fails.
    """
    if not (0 <= k < len(bt.traced_tactics)):
        raise ValueError(f"k={k} out of range [0, {len(bt.traced_tactics)})")

    thm = _to_dojo_theorem(bt)
    prefix = [tt.tactic for tt in bt.traced_tactics[:k]]
    with Dojo(thm, timeout=timeout) as (dojo, state):
        for tac in prefix:
            state = dojo.run_tac(state, tac)
            if not isinstance(state, TacticState):
                raise RuntimeError(
                    f"prefix tactic {tac!r} -> {type(state).__name__} on {bt.full_name}"
                )
        yield dojo, state


def verify_proof_tail(bt: BenchmarkTheorem, k: int, tail: str, timeout: int = 600) -> ProofResult:
    """One-shot verifier: open Dojo, replay 0..k-1, run tail, return verdict."""
    if not (0 <= k < len(bt.traced_tactics)):
        return ProofResult(bt.full_name, "exception", tail, error=f"k={k} out of range")
    if not _split_tactics(tail):
        return ProofResult(bt.full_name, "lean_error", tail, error="empty tail")
    try:
        with open_at_step(bt, k, timeout=timeout) as (dojo, state):
            return try_tail(dojo, state, tail, bt.full_name)
    except RuntimeError as exc:
        return ProofResult(bt.full_name, "replay_failed", tail, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return ProofResult(
            bt.full_name, "exception", tail, error=f"{type(exc).__name__}: {exc}",
        )
