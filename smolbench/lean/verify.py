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
    # Design: lean_dojo pins `python<3.13` (it wraps traced-repo tooling that
    # hasn't caught up to newer CPython), so it cannot live in this project's
    # main `.venv` (Python 3.14 — see pyproject.toml). Generation/analysis
    # code (`corpus`, `context`, `prompt`, `runner`'s dispatch) must still
    # import cleanly on the main venv; only this module — the Lean-side
    # verifier — needs the dedicated `.venv-lean` environment. Re-raising
    # with an actionable message here (instead of letting the bare
    # ModuleNotFoundError propagate) means anyone who accidentally imports
    # `smolbench.lean.verify` from the wrong interpreter gets pointed at the
    # fix instead of a bare "no module named lean_dojo".
    raise ImportError(
        "smolbench.lean.verify requires the 'lean_dojo' package, which is "
        "only installable in the dedicated '.venv-lean' environment (the "
        "upstream package pins python<3.13, incompatible with this "
        "project's main .venv). Build it once with:\n"
        "    UV_PROJECT_ENVIRONMENT=.venv-lean uv sync --python 3.12 "
        "--extra lean --extra notebook --extra dev\n"
        "and run Lean-verifying commands (replay/filter/run-cell/run-sweep) "
        "via '.venv-lean/bin/python' instead of the main venv's python. "
        "Generation and analysis paths (corpus/context/prompt/runner "
        "dispatch, cli's non-verifying subcommands) work fine on the main "
        "venv without lean_dojo."
    ) from exc

from .corpus import BenchmarkTheorem


# LeanDojo's Dojo init occasionally fails with "Unexpected EOF" or similar
# transient errors when several sessions open concurrently — the underlying
# Lean subprocess startup races on the build cache. Manual reopen of the same
# theorem typically succeeds within seconds. Retry with backoff before giving up.
_DOJO_OPEN_RETRIES = 3
_DOJO_OPEN_BACKOFF_S = (5.0, 15.0, 45.0)


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
# All 6 values below are valid for `ProofResult.verdict` (produced by
# `try_tail` / `verify_proof_tail`, or constructed directly by
# `smolbench.lean.runner`'s exception-handling paths when generation or
# verification raises). `ReplayResult.verdict` (`replay_ground_truth`) only
# ever takes 5 of them -- it never produces `"replay_failed"`, since
# replaying the FULL ground-truth proof has no prefix/tail split for a
# prefix-replay step to fail independently of (see each dataclass's
# docstring for its own applicable subset).
#
#   success         -- ProofFinished: every goal was closed.
#   lean_error      -- Lean rejected a tactic (LeanError); `error` holds
#                      Lean's message.
#   incomplete      -- every tactic ran without error, but a goal remained
#                      open when tactics ran out (a `TacticState`, never
#                      reaching `ProofFinished`/`ProofGivenUp`).
#   given_up        -- a tactic explicitly gave up (`ProofGivenUp`, e.g. an
#                       LLM emitting `sorry`).
#   exception       -- an unexpected Python exception was caught (network,
#                      Dojo, or parsing failure) rather than a Lean-reported
#                      outcome; `error` holds `f"{type(exc).__name__}: {exc}"`.
#   replay_failed   -- (`ProofResult` only) `open_at_step`'s prefix replay
#                      (tactics `0..k-1`) itself failed to reach a
#                      `TacticState` before the tail was ever attempted.
#                      `verify_proof_tail` catches `open_at_step`'s
#                      `RuntimeError` and reports this instead of
#                      `"exception"`, so a broken *prefix* (a ground-truth
#                      replay problem) is distinguishable from a broken
#                      *tail* (the candidate's own failure).
Verdict = Literal["success", "lean_error", "incomplete", "given_up", "exception", "replay_failed"]


@dataclass
class ReplayResult:
    """Outcome of replaying a theorem's full recorded ground-truth proof.

    Produced by `replay_ground_truth`, which re-runs every tactic LeanDojo
    originally traced, in order. This is the "sanity gate": a pre-flight
    check (`cli.py`'s `replay`/`filter` subcommands, and `runner.sweep`'s
    per-theorem sanity row) that the ground truth is actually replayable
    before trusting any comparison of an LLM-generated tail against it.

    See the "Verdict taxonomy" comment above `Verdict` for the full 6-value
    verdict set; `ReplayResult.verdict` only ever takes 5 of those values --
    never `"replay_failed"`, since replaying the entire proof has no
    prefix/tail split for a prefix step to fail independently of (any such
    failure surfaces as `"exception"` here instead).
    """

    #: The theorem's `full_name`.
    theorem: str
    #: Replay outcome; see the module's verdict taxonomy comment (excludes
    #: ``"replay_failed"`` -- see this class's docstring).
    verdict: Verdict
    #: Number of tactics successfully applied before `verdict` was reached.
    #: Equals `tactics_total` for ``"success"``/``"incomplete"``; less than
    #: it for ``"lean_error"``/``"given_up"``, which stop mid-replay.
    tactics_applied: int
    #: Total number of tactics in the theorem's recorded proof
    #: (``len(bt.traced_tactics)``). 0 when `bt.has_proof` is False.
    tactics_total: int
    #: Lean's error message (``"lean_error"``) or
    #: ``f"{type(exc).__name__}: {exc}"`` (``"exception"``); None for every
    #: other verdict.
    error: str | None = None
    #: Pretty-printed final tactic state, populated only when replay ends
    #: ``"incomplete"`` with an open `TacticState` remaining; None for every
    #: other verdict.
    final_state_pp: str | None = None


def _to_dojo_theorem(bt: BenchmarkTheorem) -> Theorem:
    """Build a `lean_dojo.Theorem` handle for a `BenchmarkTheorem`.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Benchmark theorem to open a handle for. Only `url`, `commit`,
        `file_path`, and `full_name` are consumed -- `bt`'s position fields
        (`start`/`end`) are not needed to address a theorem in Dojo.

    Returns
    -------
    Theorem
        A `lean_dojo.Theorem` referencing `bt.full_name` inside
        ``LeanGitRepo(bt.url, bt.commit)`` at `bt.file_path`. Constructing
        this handle performs no I/O; opening it (via `Dojo(...)`, see
        `_open_dojo_with_retry`) is what actually pulls or reuses the
        cached traced repo.
    """
    repo = LeanGitRepo(bt.url, bt.commit)
    return Theorem(repo, Path(bt.file_path), bt.full_name)


def replay_ground_truth(bt: BenchmarkTheorem, timeout: int = 600) -> ReplayResult:
    """Open Dojo, apply the recorded tactics in order, report verdict.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem whose full recorded proof is replayed.
    timeout : int, default 600
        Seconds allowed for the Dojo session (opening it, per
        `_open_dojo_with_retry`, plus applying every tactic).

    Returns
    -------
    ReplayResult
        See `ReplayResult` for field documentation and the verdict subset
        it can take. Returns ``"incomplete"`` immediately, without opening
        Dojo at all, when `bt.has_proof` is False (no traced tactics to
        replay) -- with ``tactics_applied=0`` and ``tactics_total=0``.

    Notes
    -----
    Every exception raised while opening or driving the Dojo session
    (including an exhausted `_open_dojo_with_retry`) is caught and reported
    as ``verdict="exception"`` rather than propagating: this function is
    called across many theorems in a loop (`cli.py`'s `filter` subcommand,
    `runner.sweep`'s per-theorem sanity row), and one theorem's failure
    must not abort the whole batch.
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

    Produced by `try_tail` (and its one-shot wrapper `verify_proof_tail`),
    and also constructed directly by `smolbench.lean.runner`'s exception
    handlers when generation or Dojo verification itself raises. See the
    "Verdict taxonomy" comment above `Verdict` for the full 6-value verdict
    set -- `ProofResult` is the only one of the two result classes that can
    carry ``"replay_failed"``.
    """

    #: The theorem's `full_name`.
    theorem: str
    #: Outcome of trying `tail_tried`; see the module's verdict taxonomy
    #: comment.
    verdict: Verdict
    #: The candidate tail text that was attempted (as passed to `try_tail`
    #: / `verify_proof_tail`), recorded even on failure so result rows and
    #: summaries can show what was actually tried.
    tail_tried: str
    #: Lean's error message, prefixed with which tail step failed (see
    #: `try_tail`, ``"lean_error"``); the prefix-replay failure message
    #: (``"replay_failed"``); or ``f"{type(exc).__name__}: {exc}"``
    #: (``"exception"``). None for every other verdict.
    error: str | None = None
    #: Pretty-printed final tactic state, populated only when the tail ends
    #: ``"incomplete"`` with an open `TacticState` remaining; None for
    #: every other verdict.
    final_state_pp: str | None = None


def _split_tactics(tail: str) -> list[str]:
    """Split an LLM-produced tail into individual tactics.

    Dojo's `run_tac` expects a single tactic per call. LLMs typically emit
    one tactic per line. We split on newlines and drop empty lines; we do
    *not* split on `;` or `<;>` since those are valid Lean tactic combinators
    (`t1 <;> t2` and `t1 ; t2` are each one tactic that Dojo parses fine).

    Parameters
    ----------
    tail : str
        Raw candidate tail text (typically `extract_tactic_block`'s output).

    Returns
    -------
    list of str
        Each non-blank line of `tail`, stripped of surrounding whitespace,
        in original order. Empty if `tail` is blank or whitespace-only.
    """
    return [line.strip() for line in tail.splitlines() if line.strip()]


def try_tail(dojo, state_at_k, tail: str, theorem_name: str) -> ProofResult:
    """Apply each line of `tail` as a separate tactic from `state_at_k`.

    Dojo states are immutable and `run_tac` returns a new state, so it's safe
    to call this multiple times against the same `state_at_k` checkpoint —
    each call branches independently, no re-replay needed.

    Parameters
    ----------
    dojo : lean_dojo.Dojo
        Open Dojo session (from `open_at_step`) to run tactics against.
    state_at_k : lean_dojo.TacticState
        Checkpoint state to branch the tail from. Immutable, so it is safe
        to reuse across many `try_tail` calls without any of them mutating
        it.
    tail : str
        Candidate proof tail; split into individual tactics via
        `_split_tactics`.
    theorem_name : str
        Recorded verbatim as `ProofResult.theorem`. Caller-supplied rather
        than derived from `dojo`/`state_at_k` (neither carries a theorem
        name), so this function never needs a `BenchmarkTheorem` itself.

    Returns
    -------
    ProofResult
        `verdict` is one of ``"lean_error"`` (`tail` splits to no tactics,
        or a tactic step Lean rejects -- `error` names which step and
        Lean's message), ``"success"`` (a tactic reaches `ProofFinished`),
        ``"given_up"`` (a tactic reaches `ProofGivenUp`), or
        ``"incomplete"`` (every tactic ran without error but neither
        `ProofFinished` nor `ProofGivenUp` was reached; `final_state_pp`
        holds the last state's pretty-print). Never ``"exception"`` or
        ``"replay_failed"`` -- those verdicts are produced by callers that
        wrap this function (`verify_proof_tail`'s except-blocks;
        `smolbench.lean.runner`'s per-cell exception handling), not by
        `try_tail` itself.
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

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem to open a session for.
    k : int
        0-indexed step to replay up to (exclusive); the prefix replayed is
        ``bt.traced_tactics[:k]``. Must satisfy
        ``0 <= k < len(bt.traced_tactics)``.
    timeout : int, default 600
        Seconds allowed for the Dojo session, per `_open_dojo_with_retry`.

    Yields
    ------
    tuple of (lean_dojo.Dojo, lean_dojo.TacticState)
        ``dojo`` -- the open session, for further ``dojo.run_tac`` calls
        (see `try_tail`). ``state_at_k`` -- the tactic state reached after
        replaying the prefix, to branch candidate tails from.

    Raises
    ------
    ValueError
        If `k` is outside ``[0, len(bt.traced_tactics))``.
    RuntimeError
        If any prefix tactic fails to produce a `TacticState` -- i.e. the
        RECORDED ground-truth prefix itself does not replay cleanly. This
        is distinct from a tail-verification failure (which is instead
        reported as a `ProofResult` verdict by callers, never raised);
        `verify_proof_tail` catches this specifically and reports
        ``"replay_failed"``.

    Notes
    -----
    The Dojo session is always closed (``cm.__exit__``) on the way out,
    whether the `with`-block body completes normally, raises, or this
    function's own prefix replay raises `RuntimeError` first.
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

    Parameters
    ----------
    bt : BenchmarkTheorem
        Theorem to verify against.
    k : int
        0-indexed step the tail is proposed to complete from; forwarded to
        `open_at_step`.
    tail : str
        Candidate proof tail (e.g. an LLM's generated tactics).
    timeout : int, default 600
        Seconds allowed for the Dojo session; forwarded to `open_at_step`.

    Returns
    -------
    ProofResult
        ``"exception"`` immediately, without opening Dojo, if `k` is out of
        range; ``"lean_error"`` immediately if `tail` splits to no tactics
        (`_split_tactics` empty); otherwise whatever `try_tail` returns
        (``"success"``/``"lean_error"``/``"given_up"``/``"incomplete"``);
        ``"replay_failed"`` if `open_at_step`'s prefix replay raises
        `RuntimeError`; or ``"exception"`` if anything else raises. See the
        module's verdict taxonomy comment (above `Verdict`) for the full
        set and each verdict's meaning.

    Notes
    -----
    Opens exactly one Dojo session per call -- unlike `open_at_step` +
    `try_tail`, which let a caller share one session across many tails at
    the same `(theorem, k)`. This is the entry point `runner.run_cell`
    uses, where each cell is independent and no session reuse across cells
    is wanted (contrast `runner.sweep`, which reuses one session per
    `(theorem, k)` via `open_at_step` directly).
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
