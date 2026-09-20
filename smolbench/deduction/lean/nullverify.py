"""Provide generation-only verification without a Lean toolchain.

Never import `verify`: its top-level `lean_interact` import fails where the dependency is absent.
`"skipped"` is not a sanity failure, so generation-only sweeps still produce cells.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any, Iterator

from .corpus import BenchmarkTheorem


@dataclass(frozen=True)
class NullReplayResult:
    """Unattempted replay mirroring `verify.ReplayResult` field-for-field.

    Fields have the same names in the same order so `runner` can construct them positionally.
    """

    theorem: str
    #: Always ``"skipped"``: replay was not attempted.
    verdict: str
    tactics_applied: int
    #: Traced-tactic count, for result-shape parity.
    tactics_total: int
    error: str | None = None
    final_state_pp: str | None = None


@dataclass(frozen=True)
class NullProofResult:
    """Unattempted proof-tail result, mirroring `verify.ProofResult` for `runner`."""

    theorem: str
    verdict: str
    #: The candidate tail that was (not) attempted, recorded for parity.
    tail_tried: str
    error: str | None = None
    final_state_pp: str | None = None


class NullVerifier:
    """Injected verifier that never opens Lean; stateless for concurrent reuse."""

    #: Class attributes are not descriptors, so `runner` can call `verifier.ProofResult(...)`.
    ProofResult = NullProofResult

    def replay_ground_truth(
        self, bt: BenchmarkTheorem, timeout: int = 600
    ) -> NullReplayResult:
        """Report that the ground-truth sanity replay was not attempted."""
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
        """Yield ``(None, None)`` because no proof prefix is replayed.

        Parameters
        ----------
        bt : BenchmarkTheorem
            The theorem.
        k : int
            Step index.
        timeout : int, optional
            API-compatible timeout.

        Yields
        ------
        tuple[None, None]
            Placeholder session and state.
        """
        yield None, None

    def try_tail(
        self, dojo: Any, state_at_k: Any, tail: str, theorem_name: str
    ) -> NullProofResult:
        """Report the candidate tail as ``verdict="unverified"``, recording it verbatim."""
        return NullProofResult(
            theorem=theorem_name, verdict="unverified", tail_tried=tail
        )

    def verify_proof_tail(
        self, bt: BenchmarkTheorem, k: int, tail: str, timeout: int = 600
    ) -> NullProofResult:
        """Report an unverified tail without opening a session.

        Parameters
        ----------
        bt : BenchmarkTheorem
            The theorem.
        k : int
            Step index.
        tail : str
            Candidate tail.
        timeout : int, optional
            API-compatible timeout.

        Returns
        -------
        NullProofResult
            Unverified result.
        """
        return NullProofResult(
            theorem=bt.full_name, verdict="unverified", tail_tried=tail
        )
