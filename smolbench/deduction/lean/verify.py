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
verdict policy on top of it, which is why the public contract below is unchanged
from the retired LeanDojo-backed version.
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

# Design: imported as a MODULE, and every use below goes through the module
# attribute (`replbackend.open_session`, `replbackend.ReplError`). A
# `from .replbackend import open_session` would bind the function object into
# this module's globals at import time, and monkeypatching the backend -- which
# is how every session-driving path here is tested without a Lean toolchain --
# would then have no effect.
from . import replbackend
from .corpus import BenchmarkTheorem


# ---------------------------------------------------------------------------
# Verdict taxonomy
# ---------------------------------------------------------------------------
#
# All 6 values below are valid for `ProofResult.verdict`, produced by
# `try_tail` / `verify_proof_tail` or constructed directly by
# `smolbench.deduction.lean.runner`'s exception-handling paths.
# `ReplayResult.verdict` (`replay_ground_truth`) takes only 5: replaying the
# FULL ground-truth proof has no prefix/tail split, so it never produces
# `"replay_failed"`.
#
#   success         -- `proofStatus == "Completed"`: every goal was closed.
#   lean_error      -- Lean rejected a tactic (an error-severity message, or
#                      a `proofStatus` of `Error`); `error` holds Lean's
#                      message. Warnings never count.
#   incomplete      -- every tactic ran without error, but a goal remained
#                      open when tactics ran out (`proofStatus` never reached
#                      `Completed` and no `sorry` appeared).
#   given_up        -- a tactic left a `sorry` behind (`sorries` non-empty, or
#                      a `proofStatus` such as `Incomplete: contains sorry`,
#                      e.g. an LLM emitting `sorry`).
#   exception       -- an unexpected Python exception (network, REPL, or
#                      parsing) rather than a Lean-reported outcome; `error`
#                      holds `f"{type(exc).__name__}: {exc}"`. A REPL TIMEOUT
#                      lands here too, as a `replbackend.ReplError` whose
#                      message is `timeout:`-shaped -- deliberately NOT a
#                      seventh `"timeout"` verdict, since `runner.py` owns the
#                      verdict->glyph map and the sanity-failure set and both
#                      enumerate exactly these six.
#   replay_failed   -- (`ProofResult` only) `open_at_step`'s prefix replay
#                      (tactics `0..k-1`) failed to leave an open goal state
#                      before the tail was attempted. `verify_proof_tail`
#                      catches that `RuntimeError` and reports this rather
#                      than `"exception"`, so a broken *prefix* (ground-truth
#                      problem) stays distinguishable from a broken *tail*.
Verdict = Literal["success", "lean_error", "incomplete", "given_up", "exception", "replay_failed"]


@dataclass
class ReplayResult:
    """Outcome of replaying a theorem's full recorded ground-truth proof.

    Produced by `replay_ground_truth`, the sanity gate (`cli.py`'s ``replay`` /
    ``filter``, `runner.sweep`'s per-theorem sanity row) that the ground truth is
    replayable before any LLM tail is compared against it.
    """

    #: The theorem's `full_name`.
    theorem: str
    #: Replay outcome; see the module's verdict taxonomy comment, which lists
    #: the 5 values this takes (never ``"replay_failed"``).
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
    ``"exception"``-kind outcome, so in production this never fires. It stays
    because the session is an injectable seam: any substitute backend that
    RETURNS the outcome instead must not have its infrastructure failure fall
    through the verdict branches below and be silently treated as "keep going"
    against a dead REPL.
    """
    if outcome.kind == "exception":
        raise replbackend.ReplError(outcome.error or "REPL-level failure with no message")


def replay_ground_truth(bt: BenchmarkTheorem, timeout: int = 600) -> ReplayResult:
    """Open a REPL session, apply the recorded tactics in order, report verdict.

    `timeout` is seconds per REPL request, forwarded to
    `replbackend.open_session`. Returns ``"incomplete"`` with zero counts,
    without opening a session, when `bt.has_proof` is False. Every exception
    from opening or driving the session is reported as ``verdict="exception"``
    rather than propagated: callers loop over many theorems, and one failure
    must not abort the batch. The session is always closed.
    """
    if not bt.has_proof:
        return ReplayResult(bt.full_name, "incomplete", 0, 0, error="no traced tactics")

    tactics = [tt.tactic for tt in bt.traced_tactics]

    try:
        # Opened OUTSIDE the try/finally below: if the open itself raises there
        # is no session to close, and a `finally` referencing an unbound name
        # would replace the real diagnosis with a `NameError`.
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
    #: Lean's error message, prefixed with which tail step failed (see
    #: `try_tail`, ``"lean_error"``); the prefix-replay failure message
    #: (``"replay_failed"``); or ``f"{type(exc).__name__}: {exc}"``
    #: (``"exception"``). None for every other verdict.
    error: str | None = None
    #: Pretty-printed final tactic state, only when the tail ends
    #: ``"incomplete"`` with goals still open; None otherwise.
    final_state_pp: str | None = None


def _split_tactics(tail: str) -> list[str]:
    """Split an LLM-produced tail into one stripped, non-blank line per tactic.

    The REPL's `ProofStep` takes one tactic per request. Deliberately does *not*
    split on ``;`` or ``<;>``: those are combinators, and ``t1 <;> t2`` is one
    tactic.
    """
    return [line.strip() for line in tail.splitlines() if line.strip()]


def try_tail(session, state_at_k, tail: str, theorem_name: str) -> ProofResult:
    """Apply each line of `tail` as a separate tactic from `state_at_k`.

    Proof states are immutable and `replbackend.ReplSession.step` returns a new
    one, so many calls branch independently from the same `state_at_k`
    checkpoint with no re-replay. `theorem_name` is caller-supplied (neither
    `session` nor `state_at_k` identifies a theorem for results purposes) and
    recorded verbatim as `ProofResult.theorem`.

    The four parameters are POSITIONAL: `runner.py` calls
    ``verifier.try_tail(dojo, state_at_k, candidate, theorem.full_name)``
    positionally, so their order is fixed.

    Returns
    -------
    ProofResult
        Verdict ``"success"``, ``"given_up"``, ``"incomplete"``
        (`final_state_pp` holds the last state's goals), or ``"lean_error"``
        (also when `tail` splits to no tactics; `error` names which step Lean
        rejected). Never ``"exception"`` or ``"replay_failed"`` -- wrappers
        produce those.

    Raises
    ------
    replbackend.ReplError
        The REPL itself failed (timeout, closed pipe, unknown proof state).
        Deliberately propagated rather than turned into a verdict: `runner.py`'s
        two call sites and `verify_proof_tail` both wrap this call in an
        ``except Exception -> verdict="exception"`` handler, so an
        infrastructure outage is never recorded as a Lean judgement on the
        candidate.
    """
    tactics = _split_tactics(tail)
    if not tactics:
        return ProofResult(theorem_name, "lean_error", tail, error="empty tail")

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

    The prefix ``bt.traced_tactics[:k]`` is replayed once and many `try_tail`
    calls branch from the same checkpoint. `timeout` is seconds per REPL
    request. The session is always closed on the way out, whether the
    `with`-block completes, raises, or the prefix replay raises first.

    Raises
    ------
    ValueError
        `k` is outside ``[0, len(bt.traced_tactics))``. Raised BEFORE any
        session is opened, so an out-of-range `k` costs no Lean startup.
    RuntimeError
        A prefix tactic did not leave an open goal state: the RECORDED
        ground-truth prefix does not replay cleanly. A plain builtin
        `RuntimeError`, NOT `replbackend.ReplError` -- see `verify_proof_tail`,
        which distinguishes the two. Distinct from a tail-verification failure,
        which is reported as a `ProofResult` verdict and never raised.
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
                # so the recorded prefix must NOT close the proof. Anything
                # other than an open goal state means there is no checkpoint to
                # branch tails from.
                raise RuntimeError(
                    f"prefix tactic {tac!r} -> {outcome.kind} on {bt.full_name}"
                )
            state = outcome.proof_state
        yield session, state
    finally:
        session.close()


def verify_proof_tail(bt: BenchmarkTheorem, k: int, tail: str, timeout: int = 600) -> ProofResult:
    """One-shot verifier: open a session, replay 0..k-1, run tail, return verdict.

    Opens exactly one REPL session per call -- what `runner.run_cell` needs, each
    cell being independent; contrast `runner.sweep`, which shares one session per
    ``(theorem, k)`` via `open_at_step` + `try_tail`.

    Returns
    -------
    ProofResult
        ``"exception"`` without opening a session if `k` is out of range,
        ``"lean_error"`` if `tail` splits to no tactics, ``"replay_failed"`` if
        `open_at_step`'s prefix replay raises `RuntimeError`, ``"exception"`` if
        anything else raises; otherwise `try_tail`'s result.
    """
    if not (0 <= k < len(bt.traced_tactics)):
        return ProofResult(bt.full_name, "exception", tail, error=f"k={k} out of range")
    if not _split_tactics(tail):
        return ProofResult(bt.full_name, "lean_error", tail, error="empty tail")
    try:
        with open_at_step(bt, k, timeout=timeout) as (session, state):
            return try_tail(session, state, tail, bt.full_name)
    # Design: the `RuntimeError` clause MUST come first, and
    # `replbackend.ReplError` is deliberately not a `RuntimeError` subclass. The
    # only `RuntimeError` reachable here is `open_at_step`'s prefix-replay
    # failure, a statement about the CORPUS; a REPL outage is a
    # `replbackend.ReplError` and must fall through to the clause below.
    # Inverting either half would report every infrastructure failure as a
    # broken ground truth.
    except RuntimeError as exc:
        return ProofResult(bt.full_name, "replay_failed", tail, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return ProofResult(
            bt.full_name, "exception", tail, error=f"{type(exc).__name__}: {exc}",
        )
