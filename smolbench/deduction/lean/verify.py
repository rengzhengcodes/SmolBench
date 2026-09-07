"""Open a lean-interact REPL session, replay tactics, return a verdict.

Two patterns:
  - `verify_proof_tail(bt, k, tail)` — one REPL session per call: replay
    the prefix, then run the tail. Used by `run-cell`.
  - `open_at_step(bt, k)` + `try_tail(session, state, tail)` — open once and
    branch many tails from the same checkpoint, without re-replaying the
    prefix. Used by `sweep`, where the rungs, models, and replicates of a
    (theorem, k) share one session, saving a Lean process startup per cell.

The session itself -- starting a Lean REPL on a mathlib4 checkout, deriving the
theorem's statement, and turning a REPL reply into a `replbackend.StepOutcome`
-- lives in `smolbench.deduction.lean.replbackend`. This module owns only the
verdict policy on top of it.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator, Literal

try:
    import lean_interact  # noqa: F401
except ImportError as exc:
    # Only this module -- the Lean-side verifier -- needs lean_interact; the
    # generation/analysis modules import without it. Re-raise with the fix.
    raise ImportError(
        "smolbench.deduction.lean.verify requires the 'lean_interact' package "
        "(the `lean` extra). Install it into the project venv with\n"
        "    uv sync --all-extras\n"
        "and run Lean-verifying commands (replay/filter/run-cell/run-sweep) "
        "via '.venv/bin/python'. Generation and analysis paths (corpus/context/"
        "prompt/runner dispatch, cli's non-verifying subcommands) work without "
        "lean_interact."
    ) from exc

# Imported as a MODULE, not `from .replbackend import open_session`: every
# call below goes through `replbackend.open_session`/`ReplError`, so tests
# can monkeypatch the backend without a Lean toolchain.
from . import replbackend
from .corpus import BenchmarkTheorem


# ---------------------------------------------------------------------------
# Verdict taxonomy
# ---------------------------------------------------------------------------
#
# All 7 values are valid for `ProofResult.verdict`. `ReplayResult.verdict`
# (`replay_ground_truth`) only takes 5: a full ground-truth replay has no
# prefix/tail split and no LLM candidate to be empty, so it never produces
# "replay_failed" or "no_answer" -- both describe a candidate tail.
#
#   success       -- proofStatus == "Completed": every goal closed.
#   lean_error    -- Lean rejected a tactic (error-severity message, or
#                    proofStatus == Error); `error` holds Lean's message.
#                    Warnings don't count. A tail that splits to no tactics
#                    is "no_answer", not this -- Lean never saw anything to
#                    reject.
#   incomplete    -- every tactic ran without error, but a goal remained
#                    open when tactics ran out.
#   given_up      -- a tactic left a `sorry` behind.
#   no_answer     -- (ProofResult only) `tail` split to zero tactics: the
#                    model returned nothing extractable, most often a
#                    reasoning model truncated inside an unclosed `<think>`
#                    block (see `prompt.extract_tactic_block`). Scored 0 by
#                    `power_analysis.grade_verdicts` (not in
#                    `UNMEASURABLE_VERDICTS`) but kept out of `lean_error`'s
#                    bucket: "Lean said no" and "there was nothing to say"
#                    are different failure modes for the axis this study
#                    measures.
#   exception     -- an unexpected Python exception (network, REPL, or
#                    parsing) rather than a Lean-reported outcome; `error`
#                    holds `f"{type(exc).__name__}: {exc}"`. A REPL timeout
#                    lands here too (a `replbackend.ReplError` with a
#                    `timeout:`-shaped message) rather than an eighth
#                    `"timeout"` verdict, since `runner.py`'s verdict->glyph
#                    map enumerates exactly these seven. Distinct from
#                    "no_answer": here the candidate was never run to a
#                    verdict at all.
#   replay_failed -- (ProofResult only) `open_at_step`'s prefix replay
#                    (tactics 0..k-1) failed to leave an open goal state.
#                    `verify_proof_tail` catches that `RuntimeError` and
#                    reports this rather than "exception", so a broken
#                    ground-truth prefix stays distinguishable from a broken
#                    candidate tail.
Verdict = Literal[
    "success", "lean_error", "incomplete", "given_up", "no_answer", "exception", "replay_failed",
]


@dataclass
class ReplayResult:
    """Outcome of replaying a theorem's full recorded ground-truth proof.

    Produced by `replay_ground_truth`, the sanity gate (`cli.py`'s ``replay`` /
    ``filter``, `runner.sweep`'s per-theorem sanity row) that the ground truth is
    replayable before any LLM tail is compared against it.
    """

    #: The theorem's `full_name`.
    theorem: str
    #: One of the 5 values a ground-truth replay can take (see the module's
    #: verdict taxonomy comment); never "replay_failed" or "no_answer".
    verdict: Verdict
    #: Tactics successfully applied before `verdict` was reached. Equals
    #: `tactics_total` for ``"success"``/``"incomplete"``, less for
    #: ``"lean_error"``/``"given_up"``, which stop mid-replay.
    tactics_applied: int
    #: Total number of tactics in the theorem's recorded proof
    #: (``len(bt.traced_tactics)``). 0 when `bt.has_proof` is False.
    tactics_total: int
    #: Lean's error message (``"lean_error"``) or
    #: ``f"{type(exc).__name__}: {exc}"`` (``"exception"``); None for every
    #: other verdict.
    error: str | None = None
    #: Pretty-printed final tactic state, only when replay ends
    #: ``"incomplete"`` with goals still open; None otherwise.
    final_state_pp: str | None = None


def _raise_if_repl_failure(outcome: replbackend.StepOutcome) -> None:
    """Re-raise a REPL-level outcome as `replbackend.ReplError`.

    `replbackend.ReplSession.step` already raises rather than returning an
    "exception"-kind outcome, so this never fires in production. Kept because
    the session is an injectable seam: a substitute backend that returns the
    outcome instead must not have its infrastructure failure silently treated
    as "keep going" against a dead REPL.

    Parameters
    ----------
    outcome : replbackend.StepOutcome
        REPL-level outcome to inspect.
    """
    if outcome.kind == "exception":
        raise replbackend.ReplError(outcome.error or "REPL-level failure with no message")


def replay_ground_truth(bt: BenchmarkTheorem, timeout: int = 600) -> ReplayResult:
    """Open a REPL session, apply the recorded tactics in order, report verdict.

    Every exception from opening or driving the session is reported as
    `verdict="exception"` rather than propagated:
    callers loop over many theorems, and one failure must not abort the
    batch.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem whose recorded tactics are replayed.
    timeout : int, optional
        REPL session timeout.

    Returns
    -------
    ReplayResult
        "incomplete" with zero counts, without opening a session, when
        `bt.has_proof` is False.
    """
    if not bt.has_proof:
        return ReplayResult(bt.full_name, "incomplete", 0, 0, error="no traced tactics")

    tactics = [tt.tactic for tt in bt.traced_tactics]

    try:
        # Opened OUTSIDE the try/finally: if open() itself raises, there is no
        # session to close, and a `finally` referencing an unbound name would
        # replace the real diagnosis with a `NameError`.
        session, state = replbackend.open_session(bt, timeout=timeout)
        try:
            outcome = None
            for i, tac in enumerate(tactics):
                outcome = session.step(state, tac)
                _raise_if_repl_failure(outcome)
                if outcome.kind == "lean_error":
                    # `i` counts the tactics applied BEFORE the failure.
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
                # "incomplete": thread the new proof state into the next step.
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
    """Outcome of trying a candidate proof tail from a specific proof step.

    Produced by `try_tail` (and its wrapper `verify_proof_tail`), and
    constructed directly by `runner`'s exception handlers.
    """

    #: The theorem's `full_name`.
    theorem: str
    #: Outcome of trying `tail_tried`; see the module's verdict taxonomy
    #: comment.
    verdict: Verdict
    #: The candidate tail text attempted, recorded even on failure so result
    #: rows and summaries can show what was actually tried.
    tail_tried: str
    #: Lean's error message, prefixed with which tail step failed
    #: ("lean_error"); the prefix-replay failure message ("replay_failed");
    #: `f"{type(exc).__name__}: {exc}"` ("exception"); or a fixed string
    #: naming the tail as empty ("no_answer"). None otherwise.
    error: str | None = None
    #: Pretty-printed final tactic state, only when the tail ends
    #: ``"incomplete"`` with goals still open; None otherwise.
    final_state_pp: str | None = None


def _split_tactics(tail: str) -> list[str]:
    """Split an LLM-produced tail into one stripped, non-blank line per tactic.

    The REPL's `ProofStep` takes one tactic per request. Deliberately does *not*
    split on ``;`` or ``<;>``: those are combinators, and ``t1 <;> t2`` is one
    tactic.

    Parameters
    ----------
    tail : str
        LLM-produced tactic text.

    Returns
    -------
    list[str]
        Stripped, non-blank tactic lines.
    """
    return [line.strip() for line in tail.splitlines() if line.strip()]


def try_tail(
    session: replbackend.ReplSession, state_at_k: int, tail: str, theorem_name: str
) -> ProofResult:
    """Apply each line of `tail` as a separate tactic from `state_at_k`.

    Proof states are immutable and `replbackend.ReplSession.step` returns a
    new one, so many calls branch independently from the same `state_at_k`
    checkpoint with no re-replay. The four parameters are positional:
    `runner.py` calls them positionally.

    `replbackend.ReplError` is deliberately propagated rather than turned
    into a verdict, so callers' `except Exception -> "exception"` handlers
    never record an infrastructure outage as a Lean judgement.

    Parameters
    ----------
    session : replbackend.ReplSession
        REPL session that applies the candidate tactics.
    state_at_k : int
        Proof-state checkpoint from which to start.
    tail : str
        Candidate proof-tail text.
    theorem_name : str
        Caller-supplied (neither `session` nor `state_at_k` identifies a theorem) and
        recorded verbatim.

    Returns
    -------
    ProofResult
        "success", "given_up", "incomplete" (`final_state_pp` holds the last
        goals), "lean_error" (`error` names which step Lean rejected), or
        "no_answer" (`tail` splits to no tactics). Never "exception" or
        "replay_failed" -- wrappers produce those.

    Raises
    ------
    replbackend.ReplError
        If the REPL itself fails (timeout, closed pipe, unknown proof state).
    """
    tactics = _split_tactics(tail)
    if not tactics:
        # Not "lean_error": Lean was never handed a tactic to reject, so
        # recording one would misattribute a truncated/empty generation.
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
        # "incomplete": branch the next tactic off the state just reached, not
        # off `state_at_k`.
        state = outcome.proof_state
    return ProofResult(
        theorem_name, "incomplete", tail,
        final_state_pp=outcome.goals_pp if outcome is not None else None,
    )


@contextlib.contextmanager
def open_at_step(bt: BenchmarkTheorem, k: int, timeout: int = 600) -> Iterator[tuple]:
    """Open a REPL session, replay tactics 0..k-1, yield `(session, state_at_k)`.

    The prefix is replayed once so many `try_tail` calls can branch from the
    same checkpoint. The session always closes, whether the `with`-block
    completes, raises, or the prefix replay raises first.

    That is a ground-truth problem, distinct from a tail-verification failure, which is
    reported as a `ProofResult` verdict, never raised.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem whose tactic prefix is replayed.
    k : int
        Index of the proof-state checkpoint to open.
    timeout : int, optional
        REPL session timeout.

    Yields
    ------
    tuple
        REPL session and proof state at step `k`.

    Raises
    ------
    ValueError
        If `k` is outside ``[0, len(bt.traced_tactics))``, before any session
        opens.
    RuntimeError
        If a prefix tactic doesn't leave an open goal state; a plain `RuntimeError`, not
        `replbackend.ReplError`.
    """
    if not (0 <= k < len(bt.traced_tactics)):
        raise ValueError(f"k={k} out of range [0, {len(bt.traced_tactics)})")

    prefix = [tt.tactic for tt in bt.traced_tactics[:k]]
    session, state = replbackend.open_session(bt, timeout=timeout)
    try:
        for tac in prefix:
            outcome = session.step(state, tac)
            if outcome.kind != "incomplete":
                # "success" counts as a failure here: k < len(traced_tactics),
                # so the recorded prefix must not close the proof.
                raise RuntimeError(
                    f"prefix tactic {tac!r} -> {outcome.kind} on {bt.full_name}"
                )
            state = outcome.proof_state
        yield session, state
    finally:
        session.close()


def verify_proof_tail(bt: BenchmarkTheorem, k: int, tail: str, timeout: int = 600) -> ProofResult:
    """One-shot verifier: open a session, replay 0..k-1, run tail, return verdict.

    Opens exactly one REPL session per call -- what `runner.run_cell` needs,
    each cell being independent; contrast `runner.sweep`, which shares one
    session per ``(theorem, k)`` via `open_at_step` + `try_tail`.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem whose proof tail is verified.
    k : int
        Proof-state checkpoint at which to start the tail.
    tail : str
        Candidate proof-tail text.
    timeout : int, optional
        REPL session timeout.

    Returns
    -------
    ProofResult
        "exception" without opening a session if `k` is out of range,
        "no_answer" if `tail` splits to no tactics (checked before opening a
        session, same reason), "replay_failed" if the prefix replay raises
        `RuntimeError`, "exception" if anything else raises, otherwise
        `try_tail`'s result.
    """
    if not (0 <= k < len(bt.traced_tactics)):
        return ProofResult(bt.full_name, "exception", tail, error=f"k={k} out of range")
    if not _split_tactics(tail):
        # Mirrors `try_tail`'s own empty-tail check: not "lean_error", since
        # Lean never saw a tactic to reject.
        return ProofResult(
            bt.full_name, "no_answer", tail,
            error="empty tail: the response contained no extractable tactic lines",
        )
    try:
        with open_at_step(bt, k, timeout=timeout) as (session, state):
            return try_tail(session, state, tail, bt.full_name)
    # `RuntimeError` must be caught before `Exception`: `replbackend.ReplError`
    # is not a `RuntimeError` subclass, so a REPL outage falls through to the
    # clause below while a broken ground-truth prefix does not. Inverting
    # either half would report infrastructure failures as broken ground truth.
    except RuntimeError as exc:
        return ProofResult(bt.full_name, "replay_failed", tail, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return ProofResult(
            bt.full_name, "exception", tail, error=f"{type(exc).__name__}: {exc}",
        )
