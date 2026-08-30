"""A verifier that verifies nothing -- for generation-only sweeps with no Lean toolchain.

`runner.sweep` / `runner.run_cell` reach Lean only through an injected
`verifier`, so ``sweep(config, run_dir, verifier=NullVerifier())`` runs phase 1
-- call the model, write every row -- with no `lean_dojo`, elan, or traced
mathlib4 checkout. Phase 2 (replaying the recorded tails against a real Dojo)
is a separate pass, not implemented here.

Never import `smolbench.deduction.lean.verify` here, even lazily inside a method
body: that module's unconditional top-level ``import lean_dojo`` raises
`ImportError` wherever `lean_dojo` is absent. Hence the local mirror dataclasses.

``"skipped"``, the only verdict `replay_ground_truth` produces, is deliberately
absent from `runner.SANITY_FAILURE_VERDICTS`: this module never replays, so it
cannot claim a ground truth failed, and suppressing those theorems would leave a
generation-only sweep with zero cells.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator

from .corpus import BenchmarkTheorem


@dataclass(frozen=True)
class NullReplayResult:
    """Placeholder outcome of a (never-attempted) ground-truth replay.

    Field-for-field mirror of `verify.ReplayResult` (same names, same order), so
    `runner.py`'s per-theorem sanity-row code works unchanged.
    """

    #: The theorem's `full_name`.
    theorem: str
    #: Always ``"skipped"``: replay was not attempted.
    verdict: str
    #: Always ``0``.
    tactics_applied: int
    #: ``len(bt.traced_tactics)``, for parity though no tactics were run.
    tactics_total: int
    #: Always ``None``.
    error: str | None = None
    #: Always ``None``.
    final_state_pp: str | None = None


@dataclass(frozen=True)
class NullProofResult:
    """Placeholder outcome of a (never-attempted) proof-tail verification.

    Field-for-field mirror of `verify.ProofResult`, so `runner.py`'s
    generation-exception handlers can construct one exactly as they construct a
    real `ProofResult`, bypassing `try_tail`/`verify_proof_tail`. `verdict` is
    therefore NOT restricted to ``"unverified"``; only this module's own methods
    always set that.
    """

    #: The theorem's `full_name`.
    theorem: str
    #: ``"unverified"`` from this module's own methods; `runner.py`'s exception
    #: handlers may construct any other verdict (see the class docstring).
    verdict: str
    #: The candidate tail that was (not) attempted, recorded for parity.
    tail_tried: str
    #: Always ``None`` from this module's own methods; `runner.py` may set it.
    error: str | None = None
    #: Always ``None``.
    final_state_pp: str | None = None


class NullVerifier:
    """A verifier seam implementation that never touches Lean or `lean_dojo`.

    Duck-types the surface `runner` calls on an injected `verifier`. The real
    `verify` is a module of top-level functions where these are instance
    methods, so callers pass an *instance*; `timeout` and `k` arguments exist
    for interface parity and are unused.

    Stateless and I/O-free, so one instance is reusable across a whole sweep,
    including across the runner's concurrent-generation worker threads.
    """

    #: See `NullProofResult`; `runner.py` calls it as `verifier.ProofResult(...)`.
    #: A class attribute that is itself a class is not a descriptor, so no implicit
    #: `self` is injected -- matching the real `verify` module's plain function.
    ProofResult = NullProofResult

    def replay_ground_truth(self, bt: BenchmarkTheorem, timeout: int = 600) -> NullReplayResult:
        """Report that the ground-truth sanity replay was not attempted.

        Returns ``verdict="skipped"``, which deliberately does not trip
        `runner.sweep`'s per-theorem sanity gate (see the module docstring).
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

        Unlike `verify.open_at_step`, never raises `ValueError` for out-of-range
        `k` -- there is no prefix to replay. The `contextmanager` wrapping exists
        only for `runner.py`'s ``with ... as (dojo, state):`` protocol.
        """
        yield None, None

    def try_tail(self, dojo, state_at_k, tail: str, theorem_name: str) -> NullProofResult:
        """Report the candidate tail as ``verdict="unverified"``, recording it verbatim."""
        return NullProofResult(theorem=theorem_name, verdict="unverified", tail_tried=tail)

    def verify_proof_tail(
        self, bt: BenchmarkTheorem, k: int, tail: str, timeout: int = 600
    ) -> NullProofResult:
        """One-shot `try_tail` variant, for the `run-cell` CLI's session-per-call path.

        Returns ``verdict="unverified"``; `k` is never range-checked, since no
        session is opened.
        """
        return NullProofResult(theorem=bt.full_name, verdict="unverified", tail_tried=tail)
