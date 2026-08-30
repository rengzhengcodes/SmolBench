"""A verifier that verifies nothing -- for generation-only sweeps that need no Lean toolchain.

`runner.sweep` / `runner.run_cell` reach Lean only through an injected
`verifier` object, so ``sweep(config, run_dir, verifier=NullVerifier())``
runs phase 1 -- call the model, write every row -- with no `lean_dojo`,
elan, or traced mathlib4 checkout. Phase 2, replaying the recorded tails
against a real Dojo, is a separate slow pass not implemented here.

This module must never import `smolbench.deduction.lean.verify`, even
lazily inside a method body: merely resolving that module object reruns
its unconditional top-level ``import lean_dojo``, which raises
`ImportError` wherever `lean_dojo` is absent. Hence the local mirror
dataclasses below.

``"skipped"`` -- the only verdict `replay_ground_truth` produces -- is
deliberately absent from `runner.SANITY_FAILURE_VERDICTS`: this module
never replays anything, so it has no basis to claim a ground truth
failed, and suppressing those theorems would leave a generation-only
sweep with zero cells.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator

from .corpus import BenchmarkTheorem


@dataclass(frozen=True)
class NullReplayResult:
    """Placeholder outcome of a (never-attempted) ground-truth replay.

    Field-for-field mirror of `verify.ReplayResult` -- same names, same
    order -- so `runner.py`'s per-theorem sanity-row code works unchanged.
    """

    #: The theorem's `full_name`.
    theorem: str
    #: Always ``"skipped"`` -- this class never represents an actual replay
    #: outcome, only the fact that replay was not attempted.
    verdict: str
    #: Always ``0``: no tactics were applied, since nothing was replayed.
    tactics_applied: int
    #: ``len(bt.traced_tactics)`` -- recorded for parity with the real
    #: `ReplayResult` (whose `tactics_total` a caller might sanity-check
    #: against the theorem), even though no tactics were actually run.
    tactics_total: int
    #: Always ``None`` -- there is no error to report when nothing ran.
    error: str | None = None
    #: Always ``None`` -- there is no final state to report when nothing ran.
    final_state_pp: str | None = None


@dataclass(frozen=True)
class NullProofResult:
    """Placeholder outcome of a (never-attempted) proof-tail verification.

    Field-for-field mirror of `verify.ProofResult` -- same three
    positional fields, then the same two optional keyword fields -- so
    `runner.py`'s generation-exception handlers can construct one exactly
    as they construct a real `ProofResult`, bypassing
    `try_tail`/`verify_proof_tail`. `verdict` is therefore not restricted
    to ``"unverified"``; only this module's own methods always set that.
    """

    #: The theorem's `full_name`.
    theorem: str
    #: Outcome placeholder. `NullVerifier.try_tail` / `.verify_proof_tail`
    #: always set this to ``"unverified"``; `runner.py`'s own exception
    #: handlers may construct this class directly with any other verdict
    #: string (see the class docstring).
    verdict: str
    #: The candidate tail text that was (not) attempted, recorded for parity
    #: with the real `ProofResult` even though it was never run through Dojo.
    tail_tried: str
    #: Always ``None`` when constructed by this module's own methods; a
    #: direct construction by `runner.py` may set this.
    error: str | None = None
    #: Always ``None`` -- there is no final Lean tactic state to report when
    #: nothing was verified.
    final_state_pp: str | None = None


class NullVerifier:
    """A verifier seam implementation that never touches Lean or `lean_dojo`.

    Duck-types the surface `runner` calls on an injected `verifier`: the
    `ProofResult` class attribute plus `replay_ground_truth`,
    `open_at_step`, `try_tail` and `verify_proof_tail` -- here real
    instance methods, where the real `verify` is a module of top-level
    functions, so callers pass an *instance*. `timeout` and `k` arguments
    are accepted for interface parity and unused throughout.

    Stateless and I/O-free (no Dojo session, filesystem, or network), so
    one instance can be reused across a whole sweep, including across the
    runner's concurrent-generation worker threads.
    """

    #: See `NullProofResult`. `runner.py`'s generation-exception handlers
    #: access this as `verifier.ProofResult(...)`. A class attribute that
    #: is itself a class (not a function) is not subject to Python's
    #: descriptor/method-binding protocol, so `some_instance.ProofResult(...)`
    #: calls `NullProofResult(...)` directly. No implicit `self` argument
    #: is injected, exactly matching how `verify.ProofResult(...)` is
    #: called when `verifier` is the real `verify` module instead of an
    #: instance of this class.
    ProofResult = NullProofResult

    def replay_ground_truth(self, bt: BenchmarkTheorem, timeout: int = 600) -> NullReplayResult:
        """Report that the ground-truth sanity replay was not attempted.

        Returns ``verdict="skipped"``, ``tactics_applied=0``,
        ``tactics_total=len(bt.traced_tactics)``. See the module docstring
        for why ``"skipped"`` deliberately does not suppress
        `runner.sweep`'s per-theorem sanity gate.
        """
        return NullReplayResult(
            theorem=bt.full_name,
            verdict="skipped",
            tactics_applied=0,
            tactics_total=len(bt.traced_tactics),
            error=None,
        )

    @contextlib.contextmanager
    def open_at_step(
        self, bt: BenchmarkTheorem, k: int, timeout: int = 600
    ) -> Iterator[tuple[None, None]]:
        """Yield ``(None, None)`` in place of a `(dojo, state_at_k)` pair.

        Unlike `verify.open_at_step`, never raises `ValueError` for an
        out-of-range `k` -- there is no prefix to replay. Nothing is
        opened, so the `contextmanager` wrapping exists only for the
        ``with ... as (dojo, state):`` protocol `runner.py` uses; callers
        pass the yielded pair on to `try_tail`, which ignores it.
        """
        yield None, None

    def try_tail(self, dojo, state_at_k, tail: str, theorem_name: str) -> NullProofResult:
        """Report the candidate tail as ``verdict="unverified"``, recording it verbatim."""
        return NullProofResult(theorem=theorem_name, verdict="unverified", tail_tried=tail)

    def verify_proof_tail(
        self, bt: BenchmarkTheorem, k: int, tail: str, timeout: int = 600
    ) -> NullProofResult:
        """One-shot `try_tail` variant, so the `run-cell` CLI's session-per-call path works too.

        Returns ``verdict="unverified"``; `k` is never checked against
        `bt.traced_tactics`, since no session is opened.
        """
        return NullProofResult(theorem=bt.full_name, verdict="unverified", tail_tried=tail)
