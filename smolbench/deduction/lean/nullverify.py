"""A verifier that verifies nothing -- for generation-only sweeps on the main venv.

`smolbench.deduction.lean.runner.sweep` (and `run_cell`) never call into
Lean directly. Every Dojo interaction goes through an injected `verifier`
object (see `runner._default_verifier`). This lets the runner itself
import and run on the main Python 3.14 `.venv`, where
`smolbench.deduction.lean.verify` is not importable at all (it requires
`lean_dojo`, which pins ``python<3.13`` -- see `verify.py`'s import
guard). `NullVerifier` is a second concrete implementation of that same
seam, alongside the real `smolbench.deduction.lean.verify` module and the
offline test suite's fake verifiers. It duck-types every attribute
`runner.py` calls on `verifier`, but every method returns an
"unverified"/"skipped" placeholder instead of opening a Dojo session.

Two-phase workflow
-------------------
This exists to split a sweep into two independently-schedulable phases:

1. **Generation**, on the main venv (no `lean_dojo`, no elan, no traced
   mathlib4 checkout needed): run
   `sweep(config, run_dir, verifier=NullVerifier())`. Every cell still
   calls the configured model and writes a row. `verdict` is just always
   `"unverified"` (or `"exception"`, for the same generation failures a
   real verifier would also report as `"exception"`, since `runner.py`
   itself constructs those, not the verifier).
2. **Verification**, on `.venv-lean`, as a separate later pass: replay the
   candidate tails recorded by phase 1 against the real Dojo. This module
   does not implement that replay -- its job stops at making phase 1
   possible without `lean_dojo` installed.

Why `smolbench.deduction.lean.verify` is never imported here
--------------------------------------------------------------
That is the entire point of this module. If `nullverify.py` imported
`.verify` -- even lazily, even only inside a method nobody calls on the
main venv -- Python would still need to resolve the
`smolbench.deduction.lean.verify` module object, to define the
function/method that references it. That resolution reruns `.verify`'s
top-level `import lean_dojo` and raises `ImportError` on any interpreter
without `lean_dojo` installed (see `verify.py`'s own import guard for why
that import is unconditional there). A lazy *function-body* import only
defers *executing* the import to call time; it does not change that
importing `nullverify` itself must stay independent of it. So this module
defines its own small result dataclasses (`NullReplayResult`,
`NullProofResult`) that mirror the field names of `verify.ReplayResult` /
`verify.ProofResult` exactly, rather than importing or subclassing the
real ones.

Why "unverified" / "skipped" are deliberately excluded from `runner.py`'s failure set
----------------------------------------------------------------------------------------
`runner.SANITY_FAILURE_VERDICTS` is the set of sanity-replay verdicts that
suppress cell generation for a theorem. It intentionally does NOT contain
`"skipped"` (the only verdict `replay_ground_truth` below can produce). A
verdict that is neither `"success"` nor a positive, explicit failure must
pass *through* the sanity gate rather than exclude the theorem. This
module never actually replays anything, so it has no basis to claim the
ground truth failed. If it excluded every theorem instead (because none
of them are ever `"success"`), a generation-only sweep would produce zero
cells.
The real verification pass, run later under `.venv-lean`, is what
actually answers the sanity question.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator

from .corpus import BenchmarkTheorem


@dataclass(frozen=True)
class NullReplayResult:
    """Placeholder outcome of a (never-attempted) ground-truth replay.

    This is a field-for-field mirror of
    `smolbench.deduction.lean.verify.ReplayResult` -- same names, same
    order. `runner.py` code that reads a real `ReplayResult`'s attributes
    (``sanity.verdict``, ``sanity.tactics_applied``, ``sanity.tactics_total``,
    ``sanity.error``, when building the sweep's per-theorem sanity row)
    works against this class. `NullVerifier.replay_ground_truth`
    returns this exclusively, always with ``verdict="skipped"``.
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

    This is a field-for-field mirror of
    `smolbench.deduction.lean.verify.ProofResult` -- same three positional
    fields (`theorem`, `verdict`, `tail_tried`), followed by the same two
    optional keyword fields (`error`, `final_state_pp`). This lets
    `runner.py` construct one exactly as it constructs a real
    `ProofResult`:
    ``verifier.ProofResult(theorem_full_name, "exception", candidate_tail, error="...")``.

    That call shape is not hypothetical. `runner.py`'s own generation-
    exception handlers build a `ProofResult` (real or null) directly,
    bypassing `try_tail`/`verify_proof_tail` entirely. So this class's
    `verdict` is not restricted to ``"unverified"`` in practice: a
    generation failure still reports whatever verdict `runner.py` chooses
    (typically ``"exception"``). Only the *actual proof-checking* verdicts
    (`NullVerifier.try_tail` / `NullVerifier.verify_proof_tail`) are always
    ``"unverified"``.
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

    Duck-types the exact surface `smolbench.deduction.lean.runner` calls on
    an injected `verifier`: `ProofResult` (as a class attribute, since
    `runner.py` constructs results directly via `verifier.ProofResult(...)`
    in its generation-exception handlers -- see `NullProofResult`),
    `replay_ground_truth`, `open_at_step`, `try_tail`, and
    `verify_proof_tail`. Every method is a real instance method. This
    differs from the real `smolbench.deduction.lean.verify`, which is a
    plain module of top-level functions. Callers pass an *instance* of
    this class as `sweep`'s/`run_cell`'s `verifier=` argument, e.g.
    ``sweep(config, run_dir, verifier=NullVerifier())``.

    Notes
    -----
    This class is stateless. Every method's output depends only on its
    own arguments; no instance attributes are read or written, and no I/O
    of any kind happens (no Dojo session, no filesystem, no network).
    A caller can therefore always construct a single `NullVerifier()` and
    reuse it across an entire sweep safely, including across threads (the
    runner's concurrent-generation path shares one `verifier` object
    across worker threads regardless of which concrete verifier is in
    use).
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

        Parameters
        ----------
        bt : BenchmarkTheorem
            Theorem a real verifier would replay. Only `bt.full_name` and
            `bt.traced_tactics` are read (for `NullReplayResult.theorem` /
            `.tactics_total`); no Dojo session is opened.
        timeout : int, default 600
            Accepted for interface parity with
            `smolbench.deduction.lean.verify.replay_ground_truth`; unused,
            since no session is opened to time out.

        Returns
        -------
        NullReplayResult
            ``verdict="skipped"``, ``tactics_applied=0``,
            ``tactics_total=len(bt.traced_tactics)``, ``error=None``. See
            the module docstring for why ``"skipped"`` deliberately does
            not suppress `runner.sweep`'s per-theorem sanity gate.
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
        """Yield a placeholder `(dojo, state_at_k)` pair without opening anything.

        Parameters
        ----------
        bt : BenchmarkTheorem
            Accepted for interface parity with
            `smolbench.deduction.lean.verify.open_at_step`; unused.
        k : int
            Accepted for interface parity; unused. Unlike the real
            `open_at_step`, this never raises `ValueError` for an
            out-of-range `k`. There is no prefix to replay against, so an
            out-of-range `k` has nothing to break.
        timeout : int, default 600
            Accepted for interface parity; unused.

        Yields
        ------
        (None, None)
            A placeholder pair standing in for `(lean_dojo.Dojo,
            lean_dojo.TacticState)`. Callers use it exactly as they would
            the real pair -- `with verifier.open_at_step(...) as (dojo,
            state_at_k):` -- and then pass `dojo`/`state_at_k` on to
            `try_tail`, which (on this class) ignores both.

        Notes
        -----
        This opens no resource, so there is nothing to clean up on exit.
        The `contextmanager` wrapping exists only so this callable
        supports the `with ... as (dojo, state):` protocol `runner.py`
        uses, matching the real `open_at_step`'s calling convention
        exactly.
        """
        yield None, None

    def try_tail(self, dojo, state_at_k, tail: str, theorem_name: str) -> NullProofResult:
        """Report a candidate tail as unverified, without running it through Dojo.

        Parameters
        ----------
        dojo, state_at_k
            Accepted for interface parity with
            `smolbench.deduction.lean.verify.try_tail`'s positional
            signature (typically the placeholder `(None, None)` yielded by
            `open_at_step`); unused.
        tail : str
            The candidate proof tail text. Recorded verbatim as
            `NullProofResult.tail_tried`, never split into tactics or run.
        theorem_name : str
            Recorded verbatim as `NullProofResult.theorem`.

        Returns
        -------
        NullProofResult
            ``verdict="unverified"``, ``tail_tried=tail``, ``error=None``,
            ``final_state_pp=None``.
        """
        return NullProofResult(theorem=theorem_name, verdict="unverified", tail_tried=tail)

    def verify_proof_tail(
        self, bt: BenchmarkTheorem, k: int, tail: str, timeout: int = 600
    ) -> NullProofResult:
        """One-shot variant of `try_tail`, for `runner.run_cell`.

        Parameters
        ----------
        bt : BenchmarkTheorem
            Theorem the tail is proposed against. `bt.full_name` is recorded
            as `NullProofResult.theorem`; no Dojo session is opened, so `k`
            is never checked against `bt.traced_tactics`.
        k : int
            Accepted for interface parity with
            `smolbench.deduction.lean.verify.verify_proof_tail`; unused.
        tail : str
            The candidate proof tail text; recorded verbatim, never run.
        timeout : int, default 600
            Accepted for interface parity; unused.

        Returns
        -------
        NullProofResult
            Same shape as `try_tail`'s return: ``verdict="unverified"``,
            ``tail_tried=tail``, ``error=None``, ``final_state_pp=None``.

        Notes
        -----
        Included so `run_cell` (the `run-cell` CLI subcommand's single-cell,
        session-per-call entry point) also works against a `NullVerifier`,
        not just `sweep`'s shared-session path (`open_at_step` + `try_tail`).
        """
        return NullProofResult(theorem=bt.full_name, verdict="unverified", tail_tried=tail)
