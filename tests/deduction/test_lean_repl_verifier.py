"""Acceptance tests for the lean-interact verifier backend.

Fakes keep tests offline. Fixtures cover bracketed ``:=`` and doc-comment
renaming traps; 213 mathlib declarations have theorem/lemma doc comments.
"""

# pylint: disable=missing-function-docstring

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NoReturn

import pytest

from tests._paths import FIXTURES

lean_interact = pytest.importorskip("lean_interact")

# importorskip above must run before this third-party import.
from lean_interact.interface import (  # noqa: E402  # pylint: disable=wrong-import-order
    LeanError,
    ProofStepResponse,
)

from smolbench.deduction.lean import replbackend, verify  # noqa: E402
from smolbench.deduction.lean.corpus import BenchmarkTheorem, TracedTactic  # noqa: E402

PROJECT = FIXTURES / "lean_repl_project"


def _bt(
    tactics: list[str],
    *,
    file_path: str = "Mini/A.lean",
    name: str = "Mini.theoremA",
    start: tuple[int, int] = (1, 1),
) -> BenchmarkTheorem:
    """A `BenchmarkTheorem` whose tactics are `tactics` and whose source is the fixture."""
    return BenchmarkTheorem(
        url="https://github.com/leanprover-community/mathlib4",
        commit="deadbeef",
        file_path=file_path,
        full_name=name,
        start=start,
        end=(99, 0),
        postcutoff=False,
        traced_tactics=[
            TracedTactic(tactic=t, state_before="", state_after="", premises=[])
            for t in tactics
        ],
    )


def _proof_step(**wire: Any) -> ProofStepResponse:
    """Build a real `ProofStepResponse` from REPL **wire** keys."""
    payload = {"proofStatus": "Incomplete", "proofState": 0, "goals": []}
    payload.update(wire)
    return ProofStepResponse.model_validate(payload)


def _msg(data: str, severity: str = "error") -> dict:
    return {"pos": {"line": 1, "column": 0}, "data": data, "severity": severity}


@dataclass
class FakeSession:
    """Scripted `replbackend.ReplSession` stand-in."""

    script: dict[str, object] = field(default_factory=dict)
    closed: int = 0
    seen: list[tuple[int, str]] = field(default_factory=list)
    #: Distinct states expose stale-state reuse.
    _next_state: int = 100

    def step(self, proof_state: int, tactic: str) -> Any:
        self.seen.append((proof_state, tactic))
        outcome = self.script[tactic]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    def close(self) -> None:
        self.closed += 1


def _ok(goals: list[str] | None = None) -> replbackend.StepOutcome:
    """An `incomplete`-kind outcome carrying `goals`, i.e. "keep going"."""
    goals = goals if goals is not None else ["⊢ Q n"]
    return replbackend.StepOutcome(
        kind="incomplete", proof_state=7, error=None, goals_pp="\n\n".join(goals)
    )


_DONE = replbackend.StepOutcome(
    kind="success", proof_state=8, error=None, goals_pp=None
)


def _install_session(
    monkeypatch: pytest.MonkeyPatch,
    session: FakeSession,
    state: int = 0,
) -> list[dict[str, Any]]:
    """Point `verify` at `session` in place of a real REPL, recording open calls."""
    calls: list[dict] = []

    def fake_open(
        bt: BenchmarkTheorem,
        timeout: float | None = 600,
        **kwargs: Any,
    ) -> tuple[FakeSession, int]:
        calls.append({"bt": bt, "timeout": timeout, **kwargs})
        return session, state

    monkeypatch.setattr(replbackend, "open_session", fake_open)
    return calls


@pytest.mark.parametrize(
    "path, expected",
    [
        ("Mathlib/Algebra/Group/Basic.lean", "Mathlib.Algebra.Group.Basic"),
        ("Mini/A.lean", "Mini.A"),
        ("Mathlib.lean", "Mathlib"),
    ],
)
def test_module_name_maps_a_corpus_file_path_to_a_lean_module(
    path: str, expected: str
) -> None:
    assert replbackend.module_name(path) == expected


@pytest.mark.parametrize(
    "bad", ["Mathlib/Algebra/Group/Basic", "", "Mathlib/Basic.txt"]
)
def test_module_name_refuses_a_path_that_is_not_a_lean_source(bad: str) -> None:
    with pytest.raises(ValueError):
        replbackend.module_name(bad)


def test_mathlib_root_names_the_env_var_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SMOLBENCH_MATHLIB_ROOT", raising=False)
    with pytest.raises(RuntimeError) as exc:
        replbackend.mathlib_root()
    assert "SMOLBENCH_MATHLIB_ROOT" in str(exc.value)


def test_mathlib_root_rejects_a_missing_directory_naming_the_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    absent = tmp_path / "not-there"
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(absent))
    with pytest.raises(RuntimeError) as exc:
        replbackend.mathlib_root()
    assert str(absent) in str(exc.value)


def test_mathlib_root_rejects_a_directory_that_is_not_a_lean_project(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A plain directory must be refused BEFORE a REPL server is ever built."""
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(tmp_path))
    with pytest.raises(RuntimeError) as exc:
        replbackend.mathlib_root()
    assert "lean-toolchain" in str(exc.value)


def test_mathlib_root_accepts_a_real_lean_project(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The positive path: the fixture project resolves and is returned."""
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(PROJECT))
    assert replbackend.mathlib_root() == PROJECT


def test_find_statement_end_takes_the_first_top_level_assignment() -> None:
    text = "theorem foo : 1 = 1 := by\n  rfl"
    assert text[: replbackend.find_statement_end(text)] == "theorem foo : 1 = 1 "


def test_find_statement_end_ignores_an_autoparam_default_inside_brackets() -> None:
    """`(h := ...)` is inside parens; splitting there truncates the signature."""
    text = "theorem foo (h : Nat := by simp) :\n    1 + 1 = 2 := by\n  rfl"
    head = text[: replbackend.find_statement_end(text)]
    assert "(h : Nat := by simp)" in head
    assert head.rstrip().endswith("1 + 1 = 2")


@pytest.mark.parametrize(
    "text",
    [
        "-- a := b\ntheorem foo : True := trivial",
        "/- a := b -/\ntheorem foo : True := trivial",
        "/-- doc a := b -/\ntheorem foo : True := trivial",
    ],
)
def test_find_statement_end_ignores_assignments_inside_comments(text: str) -> None:
    head = text[: replbackend.find_statement_end(text)]
    assert head.rstrip().endswith("theorem foo : True")


def test_find_statement_end_returns_none_without_a_top_level_assignment() -> None:
    assert (
        replbackend.find_statement_end("theorem foo : ∀ n, n = n\n  | 0 => rfl") is None
    )


def test_rename_declaration_replaces_the_declaration_identifier() -> None:
    out = replbackend.rename_declaration("theorem add_comm (a b : Nat) : a + b = b + a")
    assert out.startswith(f"theorem {replbackend.TARGET_NAME} (a b : Nat)")


def test_rename_declaration_skips_a_docstring_that_names_a_theorem() -> None:
    """213 real mathlib decls are preceded by such a docstring; renaming it is a silent miss."""
    src = (
        "/-- A docstring that names theorem fakeName and lemma otherFake. -/\n"
        "@[simp]\n"
        "theorem trapDoc : 1 + 1 = 2"
    )
    out = replbackend.rename_declaration(src)
    assert "theorem fakeName" in out, "the docstring must be left untouched"
    assert f"theorem {replbackend.TARGET_NAME} : 1 + 1 = 2" in out
    assert "trapDoc" not in out


def test_rename_declaration_preserves_modifiers_and_attributes() -> None:
    out = replbackend.rename_declaration("@[simp]\nprotected theorem Foo.bar : True")
    assert out == f"@[simp]\nprotected theorem {replbackend.TARGET_NAME} : True"


def test_rename_declaration_accepts_lemma_as_well_as_theorem() -> None:
    out = replbackend.rename_declaration("lemma foo : True")
    assert out == f"lemma {replbackend.TARGET_NAME} : True"


def test_rename_declaration_refuses_text_with_no_declaration_keyword() -> None:
    with pytest.raises(ValueError):
        replbackend.rename_declaration("def foo : Nat := 1")


def test_rename_declaration_honours_an_explicit_target_name() -> None:
    assert (
        replbackend.rename_declaration("theorem foo : True", "zzz")
        == "theorem zzz : True"
    )


def test_declaration_text_treats_the_start_line_as_one_indexed() -> None:
    """`start[0] == 1` must select the FIRST line of the file, not the second."""
    text = replbackend.declaration_text(PROJECT, "Mini/A.lean", 1)
    assert text.startswith("theorem theoremA")


def test_declaration_text_stops_at_the_next_top_level_declaration() -> None:
    text = replbackend.declaration_text(PROJECT, "Mini/Traps.lean", 1)
    assert "trapDoc" in text
    assert "trapComment" not in text


def test_declaration_text_reports_a_missing_source_file_actionably() -> None:
    with pytest.raises(FileNotFoundError) as exc:
        replbackend.declaration_text(PROJECT, "Mini/Nope.lean", 1)
    assert "Mini/Nope.lean" in str(exc.value)


def test_theorem_statement_stub_renames_slices_and_appends_sorry() -> None:
    stub = replbackend.theorem_statement_stub(_bt(["rfl"]), PROJECT)
    assert stub.startswith(f"theorem {replbackend.TARGET_NAME} {{n : ℕ}} (hn : n > 0)")
    assert stub.rstrip().endswith(":= by sorry")
    assert "intro h" not in stub, "the proof body must not be carried into the stub"
    assert stub.count(":= by sorry") == 1


def test_theorem_statement_stub_survives_the_docstring_and_autoparam_traps() -> None:
    bt = _bt(["rfl"], file_path="Mini/Traps.lean", name="Mini.trapDoc")
    stub = replbackend.theorem_statement_stub(bt, PROJECT)
    assert (
        "(h : Nat := by simp)" in stub
    ), "the autoParam default must survive the slice"
    assert "1 + 1 = 2" in stub
    assert f"theorem {replbackend.TARGET_NAME}" in stub
    assert "theorem fakeName" in stub, "the docstring must be left untouched"
    assert stub.rstrip().endswith(":= by sorry")
    assert "rfl" not in stub


def test_theorem_statement_stub_refuses_a_declaration_with_no_assignment() -> None:
    bt = _bt(
        ["rfl"], file_path="Mini/Traps.lean", name="Mini.trapNoAssign", start=(11, 0)
    )
    with pytest.raises(replbackend.ReplError) as exc:
        replbackend.theorem_statement_stub(bt, PROJECT)
    assert "Mini.trapNoAssign" in str(exc.value)


def test_classify_step_reports_completed_as_success() -> None:
    out = replbackend.classify_step(_proof_step(proofStatus="Completed", proofState=4))
    assert out.kind == "success"


def test_classify_step_reports_remaining_goals_as_incomplete() -> None:
    out = replbackend.classify_step(
        _proof_step(proofStatus="Incomplete", proofState=4, goals=["⊢ Q n", "⊢ R n"])
    )
    assert out.kind == "incomplete"
    assert out.proof_state == 4
    assert "⊢ Q n" in out.goals_pp and "⊢ R n" in out.goals_pp


def test_classify_step_reports_an_error_message_as_lean_error_carrying_the_text() -> (
    None
):
    out = replbackend.classify_step(
        _proof_step(proofStatus="Error", messages=[_msg("unknown tactic 'frobnicate'")])
    )
    assert out.kind == "lean_error"
    assert "frobnicate" in out.error


def test_classify_step_reports_an_error_status_without_messages_as_lean_error() -> None:
    out = replbackend.classify_step(_proof_step(proofStatus="Error"))
    assert out.kind == "lean_error"
    assert out.error


def test_classify_step_ignores_warnings() -> None:
    """A warning is not a rejection; the step must classify on its goals."""
    out = replbackend.classify_step(
        _proof_step(
            proofStatus="Completed", messages=[_msg("unused variable", "warning")]
        )
    )
    assert out.kind == "success"


def test_classify_step_reports_a_sorry_as_given_up() -> None:
    out = replbackend.classify_step(
        _proof_step(
            proofStatus="Incomplete: contains sorry",
            sorries=[{"goal": "⊢ Q n", "proofState": 9}],
        )
    )
    assert out.kind == "given_up"


def test_classify_step_prefers_given_up_over_success_when_a_sorry_closed_the_goals() -> (
    None
):
    """`Completed` with a sorry is `sorry`-shaped cheating, not a proof."""
    out = replbackend.classify_step(
        _proof_step(proofStatus="Completed", goals=[], sorries=[{"goal": "⊢ Q n"}])
    )
    assert out.kind == "given_up"


def test_classify_step_reports_a_repl_level_error_as_exception_not_lean_error() -> None:
    """`LeanError` is the REPL's own channel (bad request / unknown state): infra."""
    out = replbackend.classify_step(
        LeanError.model_validate({"message": "unknown proofState"})
    )
    assert out.kind == "exception"
    assert "unknown proofState" in out.error


class _FakeServer:
    """Minimal `LeanServer` stand-in: records `run` calls, `kill` calls."""

    def __init__(self, responses: list[Any] | None = None) -> None:
        self.responses = list(responses or [])
        self.killed = 0
        self.runs: list[tuple[object, float | None]] = []

    def run(
        self, request: Any, *, verbose: bool = False, timeout: float | None = None
    ) -> Any:
        self.runs.append((request, timeout))
        nxt = self.responses.pop(0)
        if isinstance(nxt, BaseException):
            raise nxt
        return nxt

    def kill(self) -> None:
        self.killed += 1


def test_repl_session_translates_a_repl_timeout_into_a_repl_error() -> None:
    """A `TimeoutError` must not surface as a bare OSError; it must stay greppable."""
    server = _FakeServer([TimeoutError("The Lean server did not respond in time")])
    session = replbackend.ReplSession(server=server, timeout=3, theorem="Mini.theoremA")
    with pytest.raises(replbackend.ReplError) as exc:
        session.step(0, "rfl")
    assert "timeout" in str(exc.value).lower()


def test_repl_session_passes_the_call_timeout_through_to_the_server() -> None:
    server = _FakeServer([_proof_step(proofStatus="Completed")])
    session = replbackend.ReplSession(
        server=server, timeout=42, theorem="Mini.theoremA"
    )
    assert session.step(0, "rfl").kind == "success"
    assert server.runs[0][1] == 42


def test_repl_session_close_kills_the_server() -> None:
    server = _FakeServer()
    replbackend.ReplSession(server=server, timeout=1, theorem="t").close()
    assert server.killed == 1


def test_repl_session_step_sends_the_proof_state_and_tactic() -> None:
    server = _FakeServer([_proof_step(proofStatus="Completed")])
    session = replbackend.ReplSession(server=server, timeout=1, theorem="t")
    session.step(17, "simp")
    request = server.runs[0][0]
    assert isinstance(request, lean_interact.ProofStep)
    assert request.proof_state == 17
    assert request.tactic == "simp"


def test_verify_imports_with_lean_interact() -> None:
    """Cold import with only `lean_interact`; restore it to avoid order dependence."""
    pytest.importorskip("lean_interact")
    from smolbench.deduction import lean as lean_pkg

    saved = sys.modules.pop("smolbench.deduction.lean.verify", None)
    try:
        # popped from sys.modules above; this reimport IS the test.
        import smolbench.deduction.lean.verify  # noqa: F401  # pylint: disable=reimported,unused-import
    finally:
        if saved is not None:
            sys.modules["smolbench.deduction.lean.verify"] = saved
            lean_pkg.verify = saved


def test_verify_cold_import_does_not_pull_in_lean_dojo() -> None:
    """Check cold `verify` import in a subprocess because local modules are polluted."""
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys\n"
            "import smolbench.deduction.lean.verify\n"
            "assert 'lean_interact' in sys.modules\n"
            "assert 'lean_dojo' not in sys.modules, "
            "sorted(m for m in sys.modules if m.startswith('lean_dojo'))\n",
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"


def test_verify_dataclass_fields_are_unchanged() -> None:
    """`runner` reads these by name; a rename silently blanks a results column."""
    from dataclasses import fields

    assert [f.name for f in fields(verify.ReplayResult)] == [
        "theorem",
        "verdict",
        "tactics_applied",
        "tactics_total",
        "error",
        "final_state_pp",
    ]
    assert [f.name for f in fields(verify.ProofResult)] == [
        "theorem",
        "verdict",
        "tail_tried",
        "error",
        "final_state_pp",
    ]


def test_try_tail_reports_success_when_the_last_tactic_closes_every_goal() -> None:
    session = FakeSession({"intro h": _ok(), "exact foo": _DONE})
    res = verify.try_tail(session, 0, "intro h\nexact foo", "Mini.theoremA")
    assert (res.verdict, res.theorem, res.tail_tried) == (
        "success",
        "Mini.theoremA",
        "intro h\nexact foo",
    )
    assert res.error is None


def test_try_tail_threads_the_returned_proof_state_between_tactics() -> None:
    """Each step must branch from the PREVIOUS step's state, not from `state_at_k`."""
    session = FakeSession({"intro h": _ok(), "exact foo": _DONE})
    verify.try_tail(session, 3, "intro h\nexact foo", "t")
    assert session.seen == [(3, "intro h"), (7, "exact foo")]


def test_try_tail_reports_lean_error_naming_the_failing_step_and_tactic() -> None:
    session = FakeSession(
        {
            "intro h": _ok(),
            "frobnicate": replbackend.StepOutcome(
                kind="lean_error",
                proof_state=None,
                error="unknown tactic 'frobnicate'",
                goals_pp=None,
            ),
        }
    )
    res = verify.try_tail(session, 0, "intro h\nfrobnicate", "t")
    assert res.verdict == "lean_error"
    assert "tail step 2/2" in res.error
    assert "'frobnicate'" in res.error
    assert "unknown tactic" in res.error


def test_try_tail_reports_given_up_for_a_sorry() -> None:
    session = FakeSession(
        {"sorry": replbackend.StepOutcome("given_up", None, None, None)}
    )
    assert verify.try_tail(session, 0, "sorry", "t").verdict == "given_up"


def test_try_tail_reports_incomplete_with_the_final_state_when_tactics_run_out() -> (
    None
):
    session = FakeSession({"intro h": _ok(["⊢ Q n"])})
    res = verify.try_tail(session, 0, "intro h", "t")
    assert res.verdict == "incomplete"
    assert res.final_state_pp == "⊢ Q n"


def test_try_tail_reports_an_empty_tail_as_no_answer() -> None:
    """Empty generation is `no_answer`, not Lean rejection."""
    res = verify.try_tail(FakeSession(), 0, "   \n\n  ", "t")
    assert res.verdict == "no_answer"
    assert "empty tail" in res.error
    assert "no_answer" in verify.Verdict.__args__


def test_try_tail_ignores_blank_lines_when_splitting_tactics() -> None:
    session = FakeSession({"intro h": _ok(), "exact foo": _DONE})
    verify.try_tail(session, 0, "\n  intro h  \n\n exact foo \n", "t")
    assert [t for _, t in session.seen] == ["intro h", "exact foo"]


def test_try_tail_does_not_split_on_tactic_combinators() -> None:
    """``t1 <;> t2`` is ONE tactic; splitting it changes what is being verified."""
    session = FakeSession({"constructor <;> simp": _DONE})
    assert verify.try_tail(session, 0, "constructor <;> simp", "t").verdict == "success"


def test_try_tail_raises_on_a_repl_level_failure_so_the_caller_maps_it_to_exception() -> (
    None
):
    """`try_tail` never returns ``"exception"``; `runner`/`verify_proof_tail` build it."""
    session = FakeSession({"rfl": replbackend.ReplError("timeout: 30s")})
    with pytest.raises(replbackend.ReplError):
        verify.try_tail(session, 0, "rfl", "t")


def test_try_tail_maps_an_exception_kind_outcome_to_a_raise() -> None:
    session = FakeSession(
        {"rfl": replbackend.StepOutcome("exception", None, "unknown proofState", None)}
    )
    with pytest.raises(replbackend.ReplError) as exc:
        verify.try_tail(session, 0, "rfl", "t")
    assert "unknown proofState" in str(exc.value)


@pytest.mark.parametrize("k", [-1, 3, 4])
def test_open_at_step_refuses_an_out_of_range_k(
    k: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = FakeSession()
    _install_session(monkeypatch, session)
    bt = _bt(["a", "b", "c"])
    with pytest.raises(ValueError):
        with verify.open_at_step(bt, k):
            pass
    assert session.closed == 0, "no session may be opened for an invalid k"


def test_open_at_step_replays_the_prefix_and_yields_the_reached_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession({"a": _ok(), "b": _ok()})
    calls = _install_session(monkeypatch, session, state=5)
    with verify.open_at_step(_bt(["a", "b", "c"]), 2, timeout=99) as (cp, state):
        # `open_at_step` yields a Checkpoint wrapping the live session so a
        # killed REPL can be reopened between candidates.
        assert isinstance(cp, verify.Checkpoint)
        assert cp.session is session
        assert cp.state == state == 7
    assert [t for _, t in session.seen] == ["a", "b"]
    assert session.seen[0][0] == 5
    assert calls[0]["timeout"] == 99
    assert session.closed == 1


def test_open_at_step_with_k_zero_replays_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    _install_session(monkeypatch, session, state=5)
    with verify.open_at_step(_bt(["a", "b"]), 0) as (_s, state):
        assert state == 5
    assert not session.seen


def test_open_at_step_raises_runtime_error_when_the_ground_truth_prefix_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession(
        {"a": replbackend.StepOutcome("lean_error", None, "boom", None)}
    )
    _install_session(monkeypatch, session)
    with pytest.raises(RuntimeError) as exc:
        with verify.open_at_step(_bt(["a", "b"]), 1):
            pass
    assert "Mini.theoremA" in str(exc.value)
    assert "'a'" in str(exc.value)
    assert session.closed == 1, "the session must be torn down on the raising path too"


def test_open_at_step_raises_when_the_prefix_closes_the_proof_early(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A prefix shorter than the full proof must not reach `success`."""
    session = FakeSession({"a": _DONE})
    _install_session(monkeypatch, session)
    with pytest.raises(RuntimeError):
        with verify.open_at_step(_bt(["a", "b"]), 1):
            pass
    assert session.closed == 1


def test_open_at_step_closes_the_session_when_the_body_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession({"a": _ok()})
    _install_session(monkeypatch, session)
    with pytest.raises(ZeroDivisionError):
        with verify.open_at_step(_bt(["a", "b"]), 1):
            raise ZeroDivisionError
    assert session.closed == 1


def test_verify_proof_tail_returns_try_tails_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Prefix and tail both need scripts because k=1 replays ``a`` first.
    session = FakeSession({"a": _ok(), "exact foo": _DONE})
    _install_session(monkeypatch, session)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 1, "exact foo")
    assert res.verdict == "success"
    assert [t for _, t in session.seen] == ["a", "exact foo"]
    assert session.closed == 1


@pytest.mark.parametrize("k", [-1, 2, 7])
def test_verify_proof_tail_reports_an_out_of_range_k_as_exception_without_opening(
    k: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    _install_session(monkeypatch, session)
    res = verify.verify_proof_tail(_bt(["a", "b"]), k, "rfl")
    assert res.verdict == "exception"
    assert f"k={k}" in res.error
    assert session.closed == 0


def test_verify_proof_tail_reports_an_empty_tail_as_no_answer_without_opening(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The one-shot wrapper agrees with `try_tail`: `no_answer`, no session opened."""
    session = FakeSession()
    _install_session(monkeypatch, session)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 0, "\n \n")
    assert res.verdict == "no_answer"
    assert "empty tail" in res.error
    assert session.closed == 0


def test_verify_proof_tail_reports_a_broken_prefix_as_replay_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession(
        {"a": replbackend.StepOutcome("lean_error", None, "boom", None)}
    )
    _install_session(monkeypatch, session)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 1, "rfl")
    assert res.verdict == "replay_failed"
    assert "Mini.theoremA" in res.error


def test_verify_proof_tail_reports_a_repl_failure_as_exception_with_the_type_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession({"rfl": replbackend.ReplError("timeout: 30s")})
    _install_session(monkeypatch, session)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 0, "rfl")
    assert res.verdict == "exception"
    assert res.error.startswith("ReplError: ")
    assert "timeout" in res.error


def test_verify_proof_tail_reports_a_failure_to_open_a_session_as_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(
        bt: BenchmarkTheorem, timeout: float | None = 600, **kwargs: Any
    ) -> NoReturn:
        raise replbackend.ReplError("elan not found on PATH")

    monkeypatch.setattr(replbackend, "open_session", boom)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 0, "rfl")
    assert res.verdict == "exception"
    assert "elan not found" in res.error


def test_replay_ground_truth_reports_a_theorem_with_no_tactics_without_opening(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt([]))
    assert (res.verdict, res.tactics_applied, res.tactics_total) == ("incomplete", 0, 0)
    assert res.error == "no traced tactics"
    assert session.closed == 0


def test_replay_ground_truth_reports_success_and_counts_the_closing_tactic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession({"a": _ok(), "b": _ok(), "c": _DONE})
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt(["a", "b", "c"]))
    assert (res.verdict, res.tactics_applied, res.tactics_total) == ("success", 3, 3)
    assert session.closed == 1


def test_replay_ground_truth_reports_lean_error_with_the_count_before_the_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession(
        {"a": _ok(), "b": replbackend.StepOutcome("lean_error", None, "boom", None)}
    )
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt(["a", "b", "c"]))
    assert (res.verdict, res.tactics_applied, res.tactics_total) == ("lean_error", 1, 3)
    assert res.error == "boom"
    assert session.closed == 1


def test_replay_ground_truth_reports_given_up_counting_the_giving_tactic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession(
        {"a": _ok(), "b": replbackend.StepOutcome("given_up", None, None, None)}
    )
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt(["a", "b", "c"]))
    assert (res.verdict, res.tactics_applied, res.tactics_total) == ("given_up", 2, 3)


def test_replay_ground_truth_reports_incomplete_with_the_final_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession({"a": _ok(), "b": _ok(["⊢ R n"])})
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt(["a", "b"]))
    assert (res.verdict, res.tactics_applied, res.tactics_total) == ("incomplete", 2, 2)
    assert res.final_state_pp == "⊢ R n"


def test_replay_ground_truth_never_propagates_an_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Callers loop over many theorems; one broken session must not abort the batch."""
    session = FakeSession({"a": replbackend.ReplError("server died")})
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt(["a", "b"]))
    assert res.verdict == "exception"
    assert res.error.startswith("ReplError: ")
    assert res.tactics_total == 2
    assert session.closed == 1


def test_replay_ground_truth_reports_a_failure_to_open_as_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(
        bt: BenchmarkTheorem, timeout: float | None = 600, **kwargs: Any
    ) -> NoReturn:
        raise replbackend.ReplError("no mathlib root")

    monkeypatch.setattr(replbackend, "open_session", boom)
    res = verify.replay_ground_truth(_bt(["a", "b"]))
    assert res.verdict == "exception"
    assert "no mathlib root" in res.error


def test_replay_ground_truth_never_returns_replay_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`ReplayResult` takes 5 verdicts: a full replay has no prefix/tail split."""
    for script, tactics in (
        ({"a": _DONE}, ["a"]),
        ({"a": replbackend.StepOutcome("lean_error", None, "x", None)}, ["a"]),
        ({"a": replbackend.ReplError("x")}, ["a"]),
        ({"a": _ok()}, ["a"]),
    ):
        session = FakeSession(dict(script))
        _install_session(monkeypatch, session)
        assert verify.replay_ground_truth(_bt(tactics)).verdict != "replay_failed"


def test_nullverifier_mirrors_the_real_result_dataclasses() -> None:
    """`runner` builds rows from either; a field drift blanks a results column."""
    from dataclasses import fields

    from smolbench.deduction.lean import nullverify

    assert [f.name for f in fields(nullverify.NullReplayResult)] == [
        f.name for f in fields(verify.ReplayResult)
    ]
    assert [f.name for f in fields(nullverify.NullProofResult)] == [
        f.name for f in fields(verify.ProofResult)
    ]


def test_verify_exposes_every_name_the_runner_protocol_needs() -> None:
    for attr in (
        "open_at_step",
        "try_tail",
        "replay_ground_truth",
        "verify_proof_tail",
        "ProofResult",
        "ReplayResult",
    ):
        assert hasattr(verify, attr), attr


class _FakeTime:
    """Stand-in for the `time` module: records sleeps instead of taking them."""

    def __init__(self) -> None:
        self.slept: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)


def _command(**wire: Any) -> "object":
    from lean_interact.interface import CommandResponse

    payload = {"env": 0}
    payload.update(wire)
    return CommandResponse.model_validate(payload)


def test_open_session_reports_a_misconfigured_root_as_a_repl_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Translate missing `SMOLBENCH_MATHLIB_ROOT` so it cannot condemn the corpus."""
    monkeypatch.delenv("SMOLBENCH_MATHLIB_ROOT", raising=False)
    with pytest.raises(replbackend.ReplError) as exc:
        replbackend.open_session(_bt(["a"]))
    assert "SMOLBENCH_MATHLIB_ROOT" in str(exc.value)


def test_verify_proof_tail_reports_a_misconfigured_root_as_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end teeth for the above: the verdict must be ``exception``."""
    monkeypatch.delenv("SMOLBENCH_MATHLIB_ROOT", raising=False)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 1, "rfl")
    assert res.verdict == "exception", res
    assert "SMOLBENCH_MATHLIB_ROOT" in res.error


def test_replay_ground_truth_reports_a_misconfigured_root_as_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SMOLBENCH_MATHLIB_ROOT", raising=False)
    res = verify.replay_ground_truth(_bt(["a", "b"]))
    assert res.verdict == "exception"
    assert "SMOLBENCH_MATHLIB_ROOT" in res.error


class _ElaborationFailsServer:
    """Imports fine, then reports an error for the statement stub. Deterministic."""

    def __init__(self, log: list[str]) -> None:
        log.append("start")
        self.killed = 0

    def run(
        self, request: Any, *, verbose: bool = False, timeout: float | None = None
    ) -> Any:
        if getattr(request, "cmd", "").startswith("import"):
            return _command(env=3)
        return _command(env=4, messages=[_msg("unknown identifier 'P'")])

    def kill(self) -> None:
        self.killed += 1


def test_open_session_does_not_retry_a_deterministic_statement_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not retry deterministic statements: retries cost 20s and three startups."""
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(PROJECT))
    fake_time = _FakeTime()
    monkeypatch.setattr(replbackend, "time", fake_time)
    log: list[str] = []

    with pytest.raises(replbackend.ReplError) as exc:
        replbackend.open_session(
            _bt(["a"]), server_factory=lambda root: _ElaborationFailsServer(log)
        )

    assert "unknown identifier" in str(exc.value)
    assert "Mini.theoremA" in str(exc.value)
    assert log == ["start"], f"the server was started {len(log)} times, expected once"
    assert not fake_time.slept


def test_open_session_retries_a_transient_server_start_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A racing Lean startup IS worth retrying -- that is what the backoff is for."""
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(PROJECT))
    fake_time = _FakeTime()
    monkeypatch.setattr(replbackend, "time", fake_time)
    attempts: list[int] = []

    class _Good:
        def run(
            self, request: Any, *, verbose: bool = False, timeout: float | None = None
        ) -> Any:
            if getattr(request, "cmd", "").startswith("import"):
                return _command(env=3)
            return _command(env=4, sorries=[{"goal": "⊢ Q n", "proofState": 11}])

        def kill(self) -> None:
            pass

    def factory(root: Path) -> _Good:
        attempts.append(1)
        if len(attempts) < 3:
            raise OSError("Unexpected EOF from the Lean process")
        return _Good()

    _session, state = replbackend.open_session(_bt(["a"]), server_factory=factory)
    assert state == 11
    assert len(attempts) == 3
    assert fake_time.slept == [5.0, 15.0]


def test_open_session_returns_the_sorrys_proof_state_on_the_happy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(PROJECT))
    sent: list[object] = []

    class _Good:
        def run(
            self, request: Any, *, verbose: bool = False, timeout: float | None = None
        ) -> Any:
            sent.append(request)
            if getattr(request, "cmd", "").startswith("import"):
                return _command(env=3)
            return _command(env=4, sorries=[{"goal": "⊢ Q n", "proofState": 11}])

        def kill(self) -> None:
            pass

    session, state = replbackend.open_session(
        _bt(["a"]), timeout=17, server_factory=lambda root: _Good()
    )
    assert state == 11
    assert session.timeout == 17
    assert sent[0].cmd == "import Mini.A"
    assert sent[1].env == 3
    assert sent[1].cmd.rstrip().endswith(":= by sorry")
    assert f"theorem {replbackend.TARGET_NAME}" in sent[1].cmd


# ---------------------------------------------------------------------------
# Multi-line tactics, whole-block scoring, timeout verdict, checkpoint reopen
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "tail, expected",
    [
        ("simp", ["simp"]),
        ("intro h\nexact h", ["intro h", "exact h"]),
        # Indented continuation lines belong to the tactic above them.
        (
            "have h := foo\n    (bar baz)\n    (by simp)\nexact h",
            ["have h := foo\n    (bar baz)\n    (by simp)", "exact h"],
        ),
        # `| case => ...` arms belong to the `induction ... with` above them.
        (
            "induction n with\n| zero => simp\n| succ n ih => simp [ih]",
            ["induction n with\n| zero => simp\n| succ n ih => simp [ih]"],
        ),
        ("calc a = b := by simp\n  _ = c := by ring\nexact this",
         ["calc a = b := by simp\n  _ = c := by ring", "exact this"]),
        # Focus bullets start tactics; their indented bodies continue them.
        ("constructor\n· simp\n· intro x\n  exact x",
         ["constructor", "· simp", "· intro x\n  exact x"]),
        # A uniformly indented block (as inside a `by`) is dedented first.
        ("  intro h\n  exact h", ["intro h", "exact h"]),
        ("\n\n", []),
    ],
)
def test_split_tactics_keeps_multi_line_tactics_whole(
    tail: str, expected: list[str]
) -> None:
    assert verify._split_tactics(tail) == expected


def test_try_tail_submits_a_multi_line_tactic_as_one_step() -> None:
    """The verifier must send `induction … with` and its arms to Lean together."""
    block = "induction n with\n| zero => simp\n| succ n ih => simp [ih]"
    session = FakeSession({block: _DONE})
    assert verify.try_tail(session, 0, block, "t").verdict == "success"
    assert [t for _, t in session.seen] == [block]


def test_try_tail_rejects_tactics_after_the_goals_are_closed() -> None:
    """`simp\\nQED` does not compile in a Lean file; it must not score as success."""
    session = FakeSession({"simp": _DONE, "QED": _ok()})
    res = verify.try_tail(session, 0, "simp\nQED", "t")
    assert res.verdict == "lean_error"
    assert "1 tactic(s) follow" in (res.error or "")
    # Lean was never asked about the trailing junk: the block is already invalid.
    assert [t for _, t in session.seen] == ["simp"]


def test_try_tail_records_a_request_timeout_as_the_timeout_verdict() -> None:
    """A tactic that runs past the timeout is the model's failure, not infrastructure."""
    session = FakeSession({"decide": replbackend.ReplTimeout("timeout after 600s on t")})
    res = verify.try_tail(session, 0, "decide", "t")
    assert res.verdict == "timeout"
    assert "decide" in (res.error or "") and "timeout after 600s" in (res.error or "")


def test_try_tail_still_raises_on_a_closed_repl() -> None:
    """A dead process is infrastructure: the caller records `exception`."""
    session = FakeSession({"rfl": replbackend.ReplClosed("REPL closed on t")})
    with pytest.raises(replbackend.ReplError):
        verify.try_tail(session, 0, "rfl", "t")


def test_checkpoint_reopens_the_session_after_a_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One non-terminating candidate must not void every later candidate on the block."""
    first = FakeSession({"a": _ok(), "decide": replbackend.ReplTimeout("timeout after 1s on t")})
    second = FakeSession({"a": _ok(), "rfl": _DONE})
    sessions = iter([first, second])
    opens: list[int] = []

    def fake_open(bt: BenchmarkTheorem, timeout: float | None = 600, **kwargs: Any):
        opens.append(timeout)
        return next(sessions), 0

    monkeypatch.setattr(replbackend, "open_session", fake_open)
    bt = _bt(["a", "b"])
    with verify.open_at_step(bt, 1, timeout=42) as (cp, state):
        assert isinstance(cp, verify.Checkpoint)
        assert verify.try_tail(cp, state, "decide", "t").verdict == "timeout"
        assert cp.dead and cp.reopens == 0
        # The next candidate transparently reopens, replays the prefix `a`,
        # and verifies on the fresh session's state.
        assert verify.try_tail(cp, state, "rfl", "t").verdict == "success"
        assert cp.reopens == 1 and not cp.dead
    assert opens == [42, 42]
    assert first.closed == 1 and second.closed == 1
    assert [t for _, t in second.seen] == ["a", "rfl"]


def test_checkpoint_reopen_failure_propagates_as_repl_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = FakeSession({"rfl": replbackend.ReplClosed("REPL closed on t")})
    calls = 0

    def fake_open(bt: BenchmarkTheorem, timeout: float | None = 600, **kwargs: Any):
        nonlocal calls
        calls += 1
        if calls == 1:
            return first, 0
        raise replbackend.ReplError("server would not start")

    monkeypatch.setattr(replbackend, "open_session", fake_open)
    with verify.open_at_step(_bt(["x"]), 0) as (cp, state):
        with pytest.raises(replbackend.ReplError):
            verify.try_tail(cp, state, "rfl", "t")
        assert cp.dead
        with pytest.raises(replbackend.ReplError, match="would not start"):
            verify.try_tail(cp, state, "rfl", "t")
