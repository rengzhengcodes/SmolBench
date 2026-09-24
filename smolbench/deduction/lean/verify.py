"""Replay Lean tactics and assign verification verdicts.

`open_at_step` shares a checkpoint among tails to avoid a Lean startup per
cell; `replbackend` owns session mechanics while this module owns verdict policy.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator, Literal

try:
    import lean_interact  # noqa: F401 -- optional-dependency probe  # pylint: disable=unused-import
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

# `ProofResult` has all 8 verdicts; ground-truth replay has 5 because it has
# neither a candidate tail nor a prefix/tail split. Empty tails are `no_answer`,
# not `lean_error`, because Lean received no tactic. `timeout` is a candidate
# tactic that ran past the per-request timeout: the model chose a
# non-terminating tactic, so it scores 0 like `lean_error` (it is NOT
# unmeasurable). `no_answer` scores 0 but is not `UNMEASURABLE_VERDICTS`: no
# response and a Lean rejection are distinct study failures. Warnings do not
# count as errors. `success` closes goals, `incomplete` leaves one, and
# `given_up` leaves `sorry`. `exception` is a Python or REPL failure rather
# than a Lean verdict. `replay_failed` means `open_at_step` failed to replay
# tactics 0..k-1 into an open goal, keeping a broken ground-truth prefix
# distinct from a bad tail. runner.py's `VERDICTS` table enumerates these.
Verdict = Literal[
    "success",
    "lean_error",
    "incomplete",
    "given_up",
    "no_answer",
    "timeout",
    "exception",
    "replay_failed",
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
    """
    if outcome.kind == "exception":
        raise replbackend.ReplError(
            outcome.error or "REPL-level failure with no message"
        )


def replay_ground_truth(bt: BenchmarkTheorem, timeout: int = 600) -> ReplayResult:
    """Replay recorded tactics and report a verdict.

    Reports exceptions so one theorem cannot abort a batch.

    Parameters
    ----------
    bt : BenchmarkTheorem
    timeout : int, optional

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
                        bt.full_name,
                        "lean_error",
                        i,
                        len(tactics),
                        error=outcome.error,
                    )
                if outcome.kind == "given_up":
                    return ReplayResult(
                        bt.full_name,
                        "given_up",
                        i + 1,
                        len(tactics),
                    )
                if outcome.kind == "success":
                    return ReplayResult(
                        bt.full_name,
                        "success",
                        i + 1,
                        len(tactics),
                    )
                state = outcome.proof_state
            return ReplayResult(
                bt.full_name,
                "incomplete",
                len(tactics),
                len(tactics),
                final_state_pp=outcome.goals_pp if outcome is not None else None,
            )
        finally:
            session.close()
    except Exception as exc:  # noqa: BLE001
        return ReplayResult(
            bt.full_name,
            "exception",
            0,
            len(tactics),
            error=f"{type(exc).__name__}: {exc}",
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
    """Split a tail into tactics, keeping multi-line tactics whole.

    A single Lean tactic can span lines: an indented continuation
    (``have h := foo\\n  bar``), ``induction … with`` followed by ``| case => …``
    arms, ``calc`` chains, or a ``·`` focus block. Splitting on every newline
    sent each fragment to Lean separately and failed ~96% of multi-line
    candidates while single-line ones failed ~19% (measured on the 2026-05
    sweeps), so the artifact was correlated with prompt length.

    Rule: after removing the common indentation, a line starts a new tactic
    unless it is indented or begins with ``|``, in which case it continues the
    previous one. Relative indentation inside a tactic is preserved because
    Lean is whitespace-sensitive there. Do not split ``;`` or ``<;>``: they are
    single-tactic combinators.

    Parameters
    ----------
    tail : str

    Returns
    -------
    list[str]
        Tactics, each possibly multi-line.
    """
    lines = [line.rstrip() for line in tail.splitlines()]
    lines = [line for line in lines if line.strip()]
    if not lines:
        return []
    indent = min(len(line) - len(line.lstrip()) for line in lines)
    lines = [line[indent:] for line in lines]

    tactics: list[str] = []
    for line in lines:
        continues = tactics and (line[0].isspace() or line.startswith("|"))
        if continues:
            tactics[-1] += "\n" + line
        else:
            tactics.append(line.strip())
    return tactics


class Checkpoint:
    """A ``(theorem, k)`` proof state that survives a killed REPL.

    `lean_interact` kills the server on a request timeout, and a crash closes
    the pipe; every later candidate on that session would otherwise fail as
    ``"exception"`` and be dropped from the denominators. `try_tail` marks the
    checkpoint dead on those failures and `ensure_alive` reopens the session
    and replays the prefix before the next candidate, so one bad candidate
    costs one verdict, not the whole block.
    """

    def __init__(
        self,
        bt: BenchmarkTheorem,
        k: int,
        timeout: int,
        session: replbackend.ReplSession,
        state: int,
    ) -> None:
        self.bt = bt
        self.k = k
        self.timeout = timeout
        self.session = session
        #: Proof-state id at step ``k``; changes on every reopen.
        self.state = state
        self.dead = False
        #: Reopens performed, for diagnostics.
        self.reopens = 0

    def mark_dead(self) -> None:
        """Record that the underlying REPL process is unusable."""
        self.dead = True

    def ensure_alive(self) -> None:
        """Reopen the session and replay the prefix if the REPL died.

        Raises
        ------
        replbackend.ReplError
            The REPL could not be reopened.
        RuntimeError
            The prefix no longer replays into an open goal.
        """
        if not self.dead:
            return
        self.session.close()
        self.session, self.state = _replay_prefix(self.bt, self.k, self.timeout)
        self.dead = False
        self.reopens += 1

    def close(self) -> None:
        """Kill the REPL process. Safe to call more than once."""
        self.session.close()


def try_tail(
    session: replbackend.ReplSession | Checkpoint,
    state_at_k: int,
    tail: str,
    theorem_name: str,
) -> ProofResult:
    """Try a candidate tail from a checkpoint.

    The tail is scored as a whole block, the way it would appear in a Lean
    source file: every tactic must apply, and once the goals are closed no
    tactic may follow (Lean rejects a tactic with no goals). Returning
    ``"success"`` at the first closing step, as before, passed candidates
    such as ``simp\\nQED`` that do not compile.

    Propagates `ReplError` so infrastructure failures are not Lean verdicts,
    except a request timeout, which is the model's verdict ``"timeout"``.
    When ``session`` is a `Checkpoint`, a dead REPL is reopened first and
    ``state_at_k`` is taken from the checkpoint (it changes on reopen).
    Parameters stay positional because `runner.py` calls them positionally.

    Parameters
    ----------
    session : replbackend.ReplSession | Checkpoint
    state_at_k : int
    tail : str
    theorem_name : str

    Returns
    -------
    ProofResult
        Tail verdict; never ``"exception"`` or ``"replay_failed"``.

    Raises
    ------
    replbackend.ReplError
        REPL failure such as a closed pipe, or a failed reopen.
    """
    checkpoint: Checkpoint | None = None
    if isinstance(session, Checkpoint):
        checkpoint = session
        checkpoint.ensure_alive()
        live, state_at_k = checkpoint.session, checkpoint.state
    else:
        live = session

    tactics = _split_tactics(tail)
    if not tactics:
        # Empty tails are not errors because Lean received no tactic.
        return ProofResult(
            theorem_name,
            "no_answer",
            tail,
            error="empty tail: the response contained no extractable tactic lines",
        )

    state = state_at_k
    outcome = None
    i, tac = 0, tactics[0]
    try:
        for i, tac in enumerate(tactics):
            outcome = live.step(state, tac)
            _raise_if_repl_failure(outcome)
            if outcome.kind == "success":
                remaining = len(tactics) - i - 1
                if remaining:
                    return ProofResult(
                        theorem_name,
                        "lean_error",
                        tail,
                        error=(
                            f"tail step {i+1}/{len(tactics)} ({tac!r}) closed every "
                            f"goal but {remaining} tactic(s) follow it; Lean rejects "
                            "a tactic with no goals"
                        ),
                    )
                return ProofResult(theorem_name, "success", tail)
            if outcome.kind == "lean_error":
                return ProofResult(
                    theorem_name,
                    "lean_error",
                    tail,
                    error=f"tail step {i+1}/{len(tactics)} ({tac!r}): {outcome.error}",
                )
            if outcome.kind == "given_up":
                return ProofResult(theorem_name, "given_up", tail)
            state = outcome.proof_state
    except replbackend.ReplTimeout as exc:
        if checkpoint is not None:
            checkpoint.mark_dead()
        return ProofResult(
            theorem_name,
            "timeout",
            tail,
            error=f"tail step {i+1}/{len(tactics)} ({tac!r}): {exc}",
        )
    except replbackend.ReplClosed:
        if checkpoint is not None:
            checkpoint.mark_dead()
        raise
    return ProofResult(
        theorem_name,
        "incomplete",
        tail,
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
    k : int
    timeout : int, optional

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
    if not 0 <= k < len(bt.traced_tactics):
        raise ValueError(f"k={k} out of range [0, {len(bt.traced_tactics)})")

    session, state = _replay_prefix(bt, k, timeout)
    checkpoint = Checkpoint(bt, k, timeout, session, state)
    try:
        yield checkpoint, state
    finally:
        checkpoint.close()


def _replay_prefix(
    bt: BenchmarkTheorem, k: int, timeout: int
) -> tuple[replbackend.ReplSession, int]:
    """Open a session and replay tactics ``0..k-1``; return ``(session, state)``.

    Closes the session if the prefix fails, so a raise never leaks a process.

    Raises
    ------
    RuntimeError
        Prefix did not leave an open goal state; this is not a REPL failure.
    """
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
    except BaseException:
        session.close()
        raise
    return session, state


def verify_proof_tail(
    bt: BenchmarkTheorem, k: int, tail: str, timeout: int = 600
) -> ProofResult:
    """Replay a prefix and verify one tail.

    Opens one session per independent `runner.run_cell` call.

    Parameters
    ----------
    bt : BenchmarkTheorem
    k : int
    tail : str
    timeout : int, optional

    Returns
    -------
    ProofResult
        Tail verdict, including invalid checkpoint or failed prefix; empty tails
        return before opening a session.
    """
    if not 0 <= k < len(bt.traced_tactics):
        return ProofResult(bt.full_name, "exception", tail, error=f"k={k} out of range")
    if not _split_tactics(tail):
        # Empty tails are not errors because Lean received no tactic.
        return ProofResult(
            bt.full_name,
            "no_answer",
            tail,
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
            bt.full_name,
            "exception",
            tail,
            error=f"{type(exc).__name__}: {exc}",
        )
