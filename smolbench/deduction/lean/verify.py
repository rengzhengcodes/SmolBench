"""Open a Dojo session, replay tactics, return a verdict.

Two patterns:
  - `verify_proof_tail(bt, k, tail)` — one Dojo session per call: replay
    the prefix, then run the tail. Used by `run-cell`.
  - `open_at_step(bt, k)` + `try_tail(dojo, state, tail)` — open once and
    branch many tails from the same checkpoint, without re-replaying the
    prefix. Used by `sweep`, where the rungs, models, and replicates of a
    (theorem, k) share one session, saving a Lean process startup per cell.
"""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

try:
    from lean_dojo import (
        Dojo,
        LeanError,
        LeanGitRepo,
        ProofFinished,
        ProofGivenUp,
        TacticState,
        Theorem,
    )
except ImportError as exc:
    # Only this module -- the Lean-side verifier -- needs lean_dojo; the
    # generation/analysis modules import without it. Re-raise with the fix.
    raise ImportError(
        "smolbench.deduction.lean.verify requires the 'lean_dojo' package "
        "(the `lean` extra). Install it into the project venv with\n"
        "    uv sync --all-extras\n"
        "and run Lean-verifying commands (replay/filter/run-cell/run-sweep) "
        "via '.venv/bin/python'. Generation and analysis paths (corpus/context/"
        "prompt/runner dispatch, cli's non-verifying subcommands) work without "
        "lean_dojo."
    ) from exc

from .corpus import BenchmarkTheorem


# LeanDojo's Dojo init occasionally fails ("Unexpected EOF" and similar) when
# several sessions open concurrently: the Lean subprocess startup races on the
# build cache. A reopen usually succeeds within seconds, so retry with backoff.
_DOJO_OPEN_RETRIES = 3
#: One entry per SLEEP, i.e. `_DOJO_OPEN_RETRIES - 1`: the last attempt raises
#: instead of sleeping.
_DOJO_OPEN_BACKOFF_S = (5.0, 15.0)


def _open_dojo_with_retry(thm: Theorem, timeout: int):
    """Enter the Dojo context manager, retrying on transient init failures."""
    last_exc: Exception | None = None
    for attempt in range(_DOJO_OPEN_RETRIES):
        try:
            cm = Dojo(thm, timeout=timeout)
            entered = cm.__enter__()
            return cm, entered
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt + 1 < _DOJO_OPEN_RETRIES:
                time.sleep(_DOJO_OPEN_BACKOFF_S[attempt])
    assert last_exc is not None
    raise last_exc

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
#   success         -- ProofFinished: every goal was closed.
#   lean_error      -- Lean rejected a tactic (LeanError); `error` holds
#                      Lean's message.
#   incomplete      -- every tactic ran without error, but a goal remained
#                      open when tactics ran out (a `TacticState`, never
#                      reaching `ProofFinished`/`ProofGivenUp`).
#   given_up        -- a tactic explicitly gave up (`ProofGivenUp`, e.g. an
#                      LLM emitting `sorry`).
#   exception       -- an unexpected Python exception (network, Dojo, or
#                      parsing) rather than a Lean-reported outcome; `error`
#                      holds `f"{type(exc).__name__}: {exc}"`.
#   replay_failed   -- (`ProofResult` only) `open_at_step`'s prefix replay
#                      (tactics `0..k-1`) failed to reach a `TacticState`
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
    #: ``"incomplete"`` with an open `TacticState`; None otherwise.
    final_state_pp: str | None = None


def _to_dojo_theorem(bt: BenchmarkTheorem) -> Theorem:
    """Build a `lean_dojo.Theorem` handle for a `BenchmarkTheorem`.

    Constructing the handle performs no I/O; opening it
    (`_open_dojo_with_retry`) pulls or reuses the cached traced repo.
    """
    repo = LeanGitRepo(bt.url, bt.commit)
    return Theorem(repo, Path(bt.file_path), bt.full_name)


def replay_ground_truth(bt: BenchmarkTheorem, timeout: int = 600) -> ReplayResult:
    """Open Dojo, apply the recorded tactics in order, report verdict.

    `timeout` is seconds for the whole Dojo session (opening it, per
    `_open_dojo_with_retry`, plus every tactic). Returns ``"incomplete"`` with
    zero counts, without opening Dojo, when `bt.has_proof` is False. Every
    exception from opening or driving the session is reported as
    ``verdict="exception"`` rather than propagated: callers loop over many
    theorems, and one failure must not abort the batch.
    """
    if not bt.has_proof:
        return ReplayResult(bt.full_name, "incomplete", 0, 0, error="no traced tactics")

    thm = _to_dojo_theorem(bt)
    tactics = [tt.tactic for tt in bt.traced_tactics]

    try:
        cm, (dojo, state) = _open_dojo_with_retry(thm, timeout)
        try:
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
        finally:
            cm.__exit__(None, None, None)
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
    #: ``"incomplete"`` with an open `TacticState`; None otherwise.
    final_state_pp: str | None = None


def _split_tactics(tail: str) -> list[str]:
    """Split an LLM-produced tail into one stripped, non-blank line per tactic.

    Dojo's `run_tac` takes one tactic per call. Deliberately does *not* split on
    ``;`` or ``<;>``: those are combinators, and ``t1 <;> t2`` is one tactic.
    """
    return [line.strip() for line in tail.splitlines() if line.strip()]


def try_tail(dojo, state_at_k, tail: str, theorem_name: str) -> ProofResult:
    """Apply each line of `tail` as a separate tactic from `state_at_k`.

    Dojo states are immutable and `run_tac` returns a new state, so many calls
    branch independently from the same `state_at_k` checkpoint with no re-replay.
    `theorem_name` is caller-supplied (neither `dojo` nor `state_at_k` carries
    one) and recorded verbatim as `ProofResult.theorem`.

    Returns
    -------
    ProofResult
        Verdict ``"success"``, ``"given_up"``, ``"incomplete"``
        (`final_state_pp` holds the last state), or ``"lean_error"`` (also when
        `tail` splits to no tactics; `error` names which step Lean rejected).
        Never ``"exception"`` or ``"replay_failed"`` -- wrappers produce those.
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

    The prefix ``bt.traced_tactics[:k]`` is replayed once and many `try_tail`
    calls branch from the same checkpoint. `timeout` is seconds for the session,
    per `_open_dojo_with_retry`. The session is always closed on the way out,
    whether the `with`-block completes, raises, or the prefix replay raises
    first.

    Raises
    ------
    ValueError
        `k` is outside ``[0, len(bt.traced_tactics))``.
    RuntimeError
        A prefix tactic failed to produce a `TacticState`: the RECORDED
        ground-truth prefix does not replay cleanly. Distinct from a
        tail-verification failure, which is reported as a `ProofResult` verdict
        and never raised; `verify_proof_tail` catches this as
        ``"replay_failed"``.
    """
    if not (0 <= k < len(bt.traced_tactics)):
        raise ValueError(f"k={k} out of range [0, {len(bt.traced_tactics)})")

    thm = _to_dojo_theorem(bt)
    prefix = [tt.tactic for tt in bt.traced_tactics[:k]]
    cm, (dojo, state) = _open_dojo_with_retry(thm, timeout)
    try:
        for tac in prefix:
            state = dojo.run_tac(state, tac)
            if not isinstance(state, TacticState):
                raise RuntimeError(
                    f"prefix tactic {tac!r} -> {type(state).__name__} on {bt.full_name}"
                )
        yield dojo, state
    finally:
        cm.__exit__(None, None, None)


def verify_proof_tail(bt: BenchmarkTheorem, k: int, tail: str, timeout: int = 600) -> ProofResult:
    """One-shot verifier: open Dojo, replay 0..k-1, run tail, return verdict.

    Opens exactly one Dojo session per call -- what `runner.run_cell` needs, each
    cell being independent; contrast `runner.sweep`, which shares one session per
    ``(theorem, k)`` via `open_at_step` + `try_tail`.

    Returns
    -------
    ProofResult
        ``"exception"`` without opening Dojo if `k` is out of range,
        ``"lean_error"`` if `tail` splits to no tactics, ``"replay_failed"`` if
        `open_at_step`'s prefix replay raises `RuntimeError`, ``"exception"`` if
        anything else raises; otherwise `try_tail`'s result.
    """
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
