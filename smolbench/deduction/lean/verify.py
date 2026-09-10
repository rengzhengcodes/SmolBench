"""Replay Lean tactics and assign verification verdicts.

`open_at_step` shares a checkpoint among tails to avoid a Lean startup per
cell; `replbackend` owns session mechanics while this module owns verdict policy.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator, Literal

try:
    import lean_interact  # noqa: F401
except ImportError as exc:
    # Keep generation and analysis importable without the Lean-only dependency.
    raise ImportError(
        "smolbench.deduction.lean.verify requires the 'lean_interact' package "
        "(the `lean` extra). Install it into the project venv with\n"
        "    uv sync --all-extras\n"
        "and run Lean-verifying commands (replay/filter/run-cell/run-sweep) "
        "via '.venv/bin/python'. Generation and analysis paths (corpus/context/"
        "prompt/runner dispatch, cli's non-verifying subcommands) work without "
        "lean_interact."
    ) from exc

# Import the module so tests can monkeypatch its backend without Lean.
from . import replbackend
from .corpus import BenchmarkTheorem


# `ProofResult` has all 7 verdicts; ground-truth replay has 5 because it has
# neither a candidate tail nor a prefix/tail split. Empty tails are `no_answer`,
# not `lean_error`, because Lean received no tactic. Timeouts remain `exception`
# rather than an eighth `timeout`: runner.py's glyph map enumerates these seven.
# `no_answer` scores 0 but is not `UNMEASURABLE_VERDICTS`: no response and a
# Lean rejection are distinct study failures. Warnings do not count as errors.
# `success` closes goals, `incomplete` leaves one, and `given_up` leaves `sorry`.
# `exception` is a Python or REPL failure rather than a Lean verdict.
# `replay_failed` means `open_at_step` failed to replay tactics 0..k-1 into an
# open goal, keeping a broken ground-truth prefix distinct from a bad tail.
Verdict = Literal[
    "success", "lean_error", "incomplete", "given_up", "no_answer", "exception", "replay_failed",
]


@dataclass
class ReplayResult:
    """Outcome of replaying a theorem's recorded proof.

    Ground-truth replay is a sanity gate before comparing candidate tails.
    """

    #: Theorem full name.
    theorem: str
    #: Ground-truth verdict; never ``"replay_failed"`` or ``"no_answer"``.
    verdict: Verdict
    #: Tactics applied before the verdict; equals ``tactics_total`` for
    #: ``"success"``/``"incomplete"`` and is less for ``"lean_error"``/``"given_up"``.
    tactics_applied: int
    #: Recorded tactic count; 0 without a proof.
    tactics_total: int
    #: Lean or Python error message.
    error: str | None = None
    #: Final goals for ``"incomplete"``.
    final_state_pp: str | None = None


def _raise_if_repl_failure(outcome: replbackend.StepOutcome) -> None:
    """Raise a returned REPL failure.

    Injectable test sessions return failures while production sessions raise them.

    Parameters
    ----------
    outcome : replbackend.StepOutcome
        REPL outcome.
    """
    if outcome.kind == "exception":
        raise replbackend.ReplError(outcome.error or "REPL-level failure with no message")


def replay_ground_truth(bt: BenchmarkTheorem, timeout: int = 600) -> ReplayResult:
    """Replay recorded tactics and report a verdict.

    Reports exceptions so one theorem cannot abort a batch.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem to replay.
    timeout : int, optional
        Session timeout.

    Returns
    -------
    ReplayResult
        Replay outcome; proofless theorems are incomplete with zero counts.
    """
    if not bt.has_proof:
        return ReplayResult(bt.full_name, "incomplete", 0, 0, error="no traced tactics")

    tactics = [tt.tactic for tt in bt.traced_tactics]

    try:
        # Open before ``finally`` so an open failure keeps its diagnosis.
        session, state = replbackend.open_session(bt, timeout=timeout)
        try:
            outcome = None
            for i, tac in enumerate(tactics):
                outcome = session.step(state, tac)
                _raise_if_repl_failure(outcome)
                if outcome.kind == "lean_error":
                    # ``i`` excludes the rejected tactic.
                    return ReplayResult(
                        bt.full_name, "lean_error", i, len(tactics),
                        error=outcome.error,
                    )
                if outcome.kind == "given_up":
                    return ReplayResult(
                        bt.full_name, "given_up", i + 1, len(tactics),
                    )
                if outcome.kind == "success":
                    return ReplayResult(
                        bt.full_name, "success", i + 1, len(tactics),
                    )
                state = outcome.proof_state
            return ReplayResult(
                bt.full_name, "incomplete", len(tactics), len(tactics),
                final_state_pp=outcome.goals_pp if outcome is not None else None,
            )
        finally:
            session.close()
    except Exception as exc:  # noqa: BLE001
        return ReplayResult(
            bt.full_name, "exception", 0, len(tactics), error=f"{type(exc).__name__}: {exc}",
        )


@dataclass
class ProofResult:
    """Outcome of trying a candidate proof tail."""

    #: Theorem full name.
    theorem: str
    #: Candidate-tail verdict.
    verdict: Verdict
    #: Attempted tail, retained for result rows.
    tail_tried: str
    #: Lean's step-prefixed error (``"lean_error"``), prefix-replay message
    #: (``"replay_failed"``), ``f"{type(exc).__name__}: {exc}"`` (``"exception"``),
    #: or a fixed empty-tail message (``"no_answer"``); otherwise None.
    error: str | None = None
    #: Final goals for ``"incomplete"``.
    final_state_pp: str | None = None


def _split_tactics(tail: str) -> list[str]:
    """Split a tail into stripped, non-blank tactic lines.

    Do not split ``;`` or ``<;>``: they are single-tactic combinators.

    Parameters
    ----------
    tail : str
        Candidate tactic text.

    Returns
    -------
    list[str]
        Tactic lines.
    """
    return [line.strip() for line in tail.splitlines() if line.strip()]


def try_tail(
    session: replbackend.ReplSession, state_at_k: int, tail: str, theorem_name: str
) -> ProofResult:
    """Try tail tactics from a checkpoint.

    Propagates `ReplError` so infrastructure failures are not Lean verdicts.
    Parameters stay positional because `runner.py` calls them positionally.

    Parameters
    ----------
    session : replbackend.ReplSession
        REPL session.
    state_at_k : int
        Starting proof state.
    tail : str
        Candidate tail.
    theorem_name : str
        Theorem name to record.

    Returns
    -------
    ProofResult
        Tail verdict; never ``"exception"`` or ``"replay_failed"``.

    Raises
    ------
    replbackend.ReplError
        REPL failure such as timeout or closed pipe.
    """
    tactics = _split_tactics(tail)
    if not tactics:
        # Empty tails are not errors because Lean received no tactic.
        return ProofResult(
            theorem_name, "no_answer", tail,
            error="empty tail: the response contained no extractable tactic lines",
        )

    state = state_at_k
    outcome = None
    for i, tac in enumerate(tactics):
        outcome = session.step(state, tac)
        _raise_if_repl_failure(outcome)
        if outcome.kind == "success":
            return ProofResult(theorem_name, "success", tail)
        if outcome.kind == "lean_error":
            return ProofResult(
                theorem_name, "lean_error", tail,
                error=f"tail step {i+1}/{len(tactics)} ({tac!r}): {outcome.error}",
            )
        if outcome.kind == "given_up":
            return ProofResult(theorem_name, "given_up", tail)
        state = outcome.proof_state
    return ProofResult(
        theorem_name, "incomplete", tail,
        final_state_pp=outcome.goals_pp if outcome is not None else None,
    )


@contextlib.contextmanager
def open_at_step(bt: BenchmarkTheorem, k: int, timeout: int = 600) -> Iterator[tuple]:
    """Replay a prefix and yield its session and state.

    Shares one replay among tails; a broken prefix raises rather than becoming a tail verdict.
    Always closes the session.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem to replay.
    k : int
        Checkpoint index.
    timeout : int, optional
        Session timeout.

    Yields
    ------
    tuple
        Session and proof state at ``k``.

    Raises
    ------
    ValueError
        ``k`` outside the recorded tactics.
    RuntimeError
        Prefix did not leave an open goal state; this is not a REPL failure.
    """
    if not (0 <= k < len(bt.traced_tactics)):
        raise ValueError(f"k={k} out of range [0, {len(bt.traced_tactics)})")

    prefix = [tt.tactic for tt in bt.traced_tactics[:k]]
    session, state = replbackend.open_session(bt, timeout=timeout)
    try:
        for tac in prefix:
            outcome = session.step(state, tac)
            if outcome.kind != "incomplete":
                # The prefix must leave a goal because ``k`` precedes the tail.
                raise RuntimeError(
                    f"prefix tactic {tac!r} -> {outcome.kind} on {bt.full_name}"
                )
            state = outcome.proof_state
        yield session, state
    finally:
        session.close()


def verify_proof_tail(bt: BenchmarkTheorem, k: int, tail: str, timeout: int = 600) -> ProofResult:
    """Replay a prefix and verify one tail.

    Opens one session per independent `runner.run_cell` call.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem to verify.
    k : int
        Tail checkpoint.
    tail : str
        Candidate tail.
    timeout : int, optional
        Session timeout.

    Returns
    -------
    ProofResult
        Tail verdict, including invalid checkpoint or failed prefix; empty tails
        return before opening a session.
    """
    if not (0 <= k < len(bt.traced_tactics)):
        return ProofResult(bt.full_name, "exception", tail, error=f"k={k} out of range")
    if not _split_tactics(tail):
        # Empty tails are not errors because Lean received no tactic.
        return ProofResult(
            bt.full_name, "no_answer", tail,
            error="empty tail: the response contained no extractable tactic lines",
        )
    try:
        with open_at_step(bt, k, timeout=timeout) as (session, state):
            return try_tail(session, state, tail, bt.full_name)
    # Catch this first to keep broken prefixes distinct from REPL failures.
    except RuntimeError as exc:
        return ProofResult(bt.full_name, "replay_failed", tail, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return ProofResult(
            bt.full_name, "exception", tail, error=f"{type(exc).__name__}: {exc}",
        )
