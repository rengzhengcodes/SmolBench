"""Acceptance tests for the lean-interact verifier backend (Package V).

Two layers, both fully offline -- this box has no Lean toolchain, so nothing
here starts a real REPL:

* `smolbench.deduction.lean.replbackend` -- the REPL driver. Its *pure* parts
  (statement slicing, declaration renaming, module-name derivation, mathlib
  root resolution, response classification) are exercised directly. Response
  classification is fed REAL `lean_interact` pydantic models built with
  ``model_validate`` on the **wire** keys (``proofStatus``, ``proofState``,
  ...), not hand-rolled stand-ins: a stand-in would pass even if the
  classifier read field names the REPL never sends.
* `smolbench.deduction.lean.verify` -- the unchanged public contract, driven
  against a scripted fake session so every one of the six verdicts, the
  prefix-replay `RuntimeError`, and the session-teardown guarantee are
  reached without Lean.

The fixture Lean sources under ``tests/fixtures/lean_repl_project`` encode the
two traps measured against the real mathlib4 checkout at the corpus commit
before this backend was specified:

* ``(h : Nat := by simp)`` -- an ``autoParam`` default puts a ``:=`` *inside*
  brackets. A naive "first ``:=``" split truncates the statement mid-signature.
  Real instance: ``Basis.reindexFinsetRange_self``.
* a doc comment naming ``theorem fakeName`` -- 213 of mathlib4's 106,445
  column-0 ``theorem``/``lemma`` declarations are preceded by a docstring that
  contains a ``theorem``/``lemma`` word, so a naive rename regex renames the
  docstring instead of the declaration.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

import pytest

from tests._paths import FIXTURES

lean_interact = pytest.importorskip("lean_interact")

from lean_interact.interface import LeanError, ProofStepResponse  # noqa: E402

from smolbench.deduction.lean import replbackend, verify  # noqa: E402
from smolbench.deduction.lean.corpus import BenchmarkTheorem, TracedTactic  # noqa: E402

PROJECT = FIXTURES / "lean_repl_project"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _bt(tactics: list[str], *, file_path: str = "Mini/A.lean", name: str = "Mini.theoremA",
        start: tuple[int, int] = (1, 1)) -> BenchmarkTheorem:
    """A `BenchmarkTheorem` whose tactics are `tactics` and whose source is the fixture."""
    return BenchmarkTheorem(
        url="https://github.com/leanprover-community/mathlib4",
        commit="deadbeef",
        file_path=file_path,
        full_name=name,
        start=start,
        end=(99, 0),
        traced_tactics=[
            TracedTactic(tactic=t, state_before="", state_after="", premises=[])
            for t in tactics
        ],
    )


def _proof_step(**wire) -> ProofStepResponse:
    """Build a real `ProofStepResponse` from REPL **wire** keys."""
    payload = {"proofStatus": "Incomplete", "proofState": 0, "goals": []}
    payload.update(wire)
    return ProofStepResponse.model_validate(payload)


def _msg(data: str, severity: str = "error") -> dict:
    return {"pos": {"line": 1, "column": 0}, "data": data, "severity": severity}


@dataclass
class FakeSession:
    """Scripted stand-in for `replbackend.ReplSession`.

    `script` maps a tactic string to either a `replbackend.StepOutcome` or an
    exception instance to raise. `closed` records that the caller tore the
    session down, which is what proves `verify.open_at_step`'s ``finally``.
    """

    script: dict[str, object] = field(default_factory=dict)
    closed: int = 0
    seen: list[tuple[int, str]] = field(default_factory=list)
    #: Successive proof-state ids handed back, so a caller that reuses a stale
    #: state instead of the returned one is detectable.
    _next_state: int = 100

    def step(self, proof_state: int, tactic: str):
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


_DONE = replbackend.StepOutcome(kind="success", proof_state=8, error=None, goals_pp=None)


def _install_session(monkeypatch, session, state: int = 0):
    """Point `verify` at `session` in place of a real REPL, recording open calls."""
    calls: list[dict] = []

    def fake_open(bt, timeout=600, **kwargs):
        calls.append({"bt": bt, "timeout": timeout, **kwargs})
        return session, state

    monkeypatch.setattr(replbackend, "open_session", fake_open)
    return calls


# ---------------------------------------------------------------------------
# replbackend: module name derivation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "path, expected",
    [
        ("Mathlib/Algebra/Group/Basic.lean", "Mathlib.Algebra.Group.Basic"),
        ("Mini/A.lean", "Mini.A"),
        ("Mathlib.lean", "Mathlib"),
    ],
)
def test_module_name_maps_a_corpus_file_path_to_a_lean_module(path, expected):
    assert replbackend.module_name(path) == expected


@pytest.mark.parametrize("bad", ["Mathlib/Algebra/Group/Basic", "", "Mathlib/Basic.txt"])
def test_module_name_refuses_a_path_that_is_not_a_lean_source(bad):
    with pytest.raises(ValueError):
        replbackend.module_name(bad)


# ---------------------------------------------------------------------------
# replbackend: mathlib root resolution
# ---------------------------------------------------------------------------
def test_mathlib_root_names_the_env_var_when_unset(monkeypatch):
    monkeypatch.delenv("SMOLBENCH_MATHLIB_ROOT", raising=False)
    with pytest.raises(RuntimeError) as exc:
        replbackend.mathlib_root()
    assert "SMOLBENCH_MATHLIB_ROOT" in str(exc.value)


def test_mathlib_root_rejects_a_missing_directory_naming_the_path(monkeypatch, tmp_path):
    absent = tmp_path / "not-there"
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(absent))
    with pytest.raises(RuntimeError) as exc:
        replbackend.mathlib_root()
    assert str(absent) in str(exc.value)


def test_mathlib_root_rejects_a_directory_that_is_not_a_lean_project(monkeypatch, tmp_path):
    """A plain directory must be refused BEFORE a REPL server is ever built."""
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(tmp_path))
    with pytest.raises(RuntimeError) as exc:
        replbackend.mathlib_root()
    assert "lean-toolchain" in str(exc.value)


def test_mathlib_root_accepts_a_real_lean_project(monkeypatch):
    """The positive path: the fixture project resolves and is returned."""
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(PROJECT))
    assert replbackend.mathlib_root() == PROJECT


# ---------------------------------------------------------------------------
# replbackend: statement-end detection (the depth-0 `:=` rule)
# ---------------------------------------------------------------------------
def test_find_statement_end_takes_the_first_top_level_assignment():
    text = "theorem foo : 1 = 1 := by\n  rfl"
    assert text[: replbackend.find_statement_end(text)] == "theorem foo : 1 = 1 "


def test_find_statement_end_ignores_an_autoparam_default_inside_brackets():
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
def test_find_statement_end_ignores_assignments_inside_comments(text):
    head = text[: replbackend.find_statement_end(text)]
    assert head.rstrip().endswith("theorem foo : True")


def test_find_statement_end_returns_none_without_a_top_level_assignment():
    assert replbackend.find_statement_end("theorem foo : ∀ n, n = n\n  | 0 => rfl") is None


# ---------------------------------------------------------------------------
# replbackend: declaration renaming
# ---------------------------------------------------------------------------
def test_rename_declaration_replaces_the_declaration_identifier():
    out = replbackend.rename_declaration("theorem add_comm (a b : Nat) : a + b = b + a")
    assert out.startswith(f"theorem {replbackend.TARGET_NAME} (a b : Nat)")


def test_rename_declaration_skips_a_docstring_that_names_a_theorem():
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


def test_rename_declaration_preserves_modifiers_and_attributes():
    out = replbackend.rename_declaration("@[simp]\nprotected theorem Foo.bar : True")
    assert out == f"@[simp]\nprotected theorem {replbackend.TARGET_NAME} : True"


def test_rename_declaration_accepts_lemma_as_well_as_theorem():
    out = replbackend.rename_declaration("lemma foo : True")
    assert out == f"lemma {replbackend.TARGET_NAME} : True"


def test_rename_declaration_refuses_text_with_no_declaration_keyword():
    with pytest.raises(ValueError):
        replbackend.rename_declaration("def foo : Nat := 1")


def test_rename_declaration_honours_an_explicit_target_name():
    assert replbackend.rename_declaration("theorem foo : True", "zzz") == "theorem zzz : True"


# ---------------------------------------------------------------------------
# replbackend: source slicing off a real .lean fixture
# ---------------------------------------------------------------------------
def test_declaration_text_treats_the_start_line_as_one_indexed():
    """`start[0] == 1` must select the FIRST line of the file, not the second."""
    text = replbackend.declaration_text(PROJECT, "Mini/A.lean", 1)
    assert text.startswith("theorem theoremA")


def test_declaration_text_stops_at_the_next_top_level_declaration():
    text = replbackend.declaration_text(PROJECT, "Mini/Traps.lean", 1)
    assert "trapDoc" in text
    assert "trapComment" not in text


def test_declaration_text_reports_a_missing_source_file_actionably():
    with pytest.raises(FileNotFoundError) as exc:
        replbackend.declaration_text(PROJECT, "Mini/Nope.lean", 1)
    assert "Mini/Nope.lean" in str(exc.value)


# ---------------------------------------------------------------------------
# replbackend: end-to-end statement stub
# ---------------------------------------------------------------------------
def test_theorem_statement_stub_renames_slices_and_appends_sorry():
    stub = replbackend.theorem_statement_stub(_bt(["rfl"]), PROJECT)
    assert stub.startswith(f"theorem {replbackend.TARGET_NAME} {{n : ℕ}} (hn : n > 0)")
    assert stub.rstrip().endswith(":= by sorry")
    assert "intro h" not in stub, "the proof body must not be carried into the stub"
    assert stub.count(":= by sorry") == 1


def test_theorem_statement_stub_survives_the_docstring_and_autoparam_traps():
    bt = _bt(["rfl"], file_path="Mini/Traps.lean", name="Mini.trapDoc")
    stub = replbackend.theorem_statement_stub(bt, PROJECT)
    assert "(h : Nat := by simp)" in stub, "the autoParam default must survive the slice"
    assert "1 + 1 = 2" in stub
    assert f"theorem {replbackend.TARGET_NAME}" in stub
    assert "theorem fakeName" in stub, "the docstring must be left untouched"
    assert stub.rstrip().endswith(":= by sorry")
    assert "rfl" not in stub


def test_theorem_statement_stub_prefers_a_row_carried_statement(monkeypatch):
    """A LeanDojo-v2 row carrying `theorem_statement` must not be read off disk."""
    bt = _bt(["rfl"])

    class WithStatement(BenchmarkTheorem):
        theorem_statement = "theorem carried (a : Nat) : a = a"

    carried = WithStatement(
        url=bt.url, commit=bt.commit, file_path=bt.file_path, full_name=bt.full_name,
        start=bt.start, end=bt.end, traced_tactics=bt.traced_tactics,
    )

    def explode(*a, **k):  # pragma: no cover - must never run
        raise AssertionError("declaration_text was called despite a carried statement")

    monkeypatch.setattr(replbackend, "declaration_text", explode)
    stub = replbackend.theorem_statement_stub(carried, PROJECT)
    assert stub == f"theorem {replbackend.TARGET_NAME} (a : Nat) : a = a\n  := by sorry"


def test_theorem_statement_stub_refuses_a_declaration_with_no_assignment():
    bt = _bt(["rfl"], file_path="Mini/Traps.lean", name="Mini.trapNoAssign", start=(11, 0))
    with pytest.raises(replbackend.ReplError) as exc:
        replbackend.theorem_statement_stub(bt, PROJECT)
    assert "Mini.trapNoAssign" in str(exc.value)


# ---------------------------------------------------------------------------
# replbackend: response classification, against REAL lean_interact models
# ---------------------------------------------------------------------------
def test_classify_step_reports_completed_as_success():
    out = replbackend.classify_step(_proof_step(proofStatus="Completed", proofState=4))
    assert out.kind == "success"


def test_classify_step_reports_remaining_goals_as_incomplete():
    out = replbackend.classify_step(
        _proof_step(proofStatus="Incomplete", proofState=4, goals=["⊢ Q n", "⊢ R n"])
    )
    assert out.kind == "incomplete"
    assert out.proof_state == 4
    assert "⊢ Q n" in out.goals_pp and "⊢ R n" in out.goals_pp


def test_classify_step_reports_an_error_message_as_lean_error_carrying_the_text():
    out = replbackend.classify_step(
        _proof_step(proofStatus="Error", messages=[_msg("unknown tactic 'frobnicate'")])
    )
    assert out.kind == "lean_error"
    assert "frobnicate" in out.error


def test_classify_step_reports_an_error_status_without_messages_as_lean_error():
    out = replbackend.classify_step(_proof_step(proofStatus="Error"))
    assert out.kind == "lean_error"
    assert out.error


def test_classify_step_ignores_warnings():
    """A warning is not a rejection; the step must classify on its goals."""
    out = replbackend.classify_step(
        _proof_step(proofStatus="Completed", messages=[_msg("unused variable", "warning")])
    )
    assert out.kind == "success"


def test_classify_step_reports_a_sorry_as_given_up():
    out = replbackend.classify_step(
        _proof_step(
            proofStatus="Incomplete: contains sorry",
            sorries=[{"goal": "⊢ Q n", "proofState": 9}],
        )
    )
    assert out.kind == "given_up"


def test_classify_step_prefers_given_up_over_success_when_a_sorry_closed_the_goals():
    """`Completed` with a sorry is `sorry`-shaped cheating, not a proof."""
    out = replbackend.classify_step(
        _proof_step(proofStatus="Completed", goals=[], sorries=[{"goal": "⊢ Q n"}])
    )
    assert out.kind == "given_up"


def test_classify_step_reports_a_repl_level_error_as_exception_not_lean_error():
    """`LeanError` is the REPL's own channel (bad request / unknown state): infra."""
    out = replbackend.classify_step(LeanError.model_validate({"message": "unknown proofState"}))
    assert out.kind == "exception"
    assert "unknown proofState" in out.error


# ---------------------------------------------------------------------------
# replbackend: session timeout / teardown
# ---------------------------------------------------------------------------
class _FakeServer:
    """Minimal `LeanServer` stand-in: records `run` calls, `kill` calls."""

    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.killed = 0
        self.runs: list[tuple[object, float | None]] = []

    def run(self, request, *, verbose=False, timeout=None):
        self.runs.append((request, timeout))
        nxt = self.responses.pop(0)
        if isinstance(nxt, BaseException):
            raise nxt
        return nxt

    def kill(self):
        self.killed += 1


def test_repl_session_translates_a_repl_timeout_into_a_repl_error():
    """A `TimeoutError` must not surface as a bare OSError; it must stay greppable."""
    server = _FakeServer([TimeoutError("The Lean server did not respond in time")])
    session = replbackend.ReplSession(server=server, timeout=3, theorem="Mini.theoremA")
    with pytest.raises(replbackend.ReplError) as exc:
        session.step(0, "rfl")
    assert "timeout" in str(exc.value).lower()


def test_repl_session_passes_the_call_timeout_through_to_the_server():
    server = _FakeServer([_proof_step(proofStatus="Completed")])
    session = replbackend.ReplSession(server=server, timeout=42, theorem="Mini.theoremA")
    assert session.step(0, "rfl").kind == "success"
    assert server.runs[0][1] == 42


def test_repl_session_close_kills_the_server():
    server = _FakeServer()
    replbackend.ReplSession(server=server, timeout=1, theorem="t").close()
    assert server.killed == 1


def test_repl_session_step_sends_the_proof_state_and_tactic():
    server = _FakeServer([_proof_step(proofStatus="Completed")])
    session = replbackend.ReplSession(server=server, timeout=1, theorem="t")
    session.step(17, "simp")
    request = server.runs[0][0]
    assert isinstance(request, lean_interact.ProofStep)
    assert request.proof_state == 17
    assert request.tactic == "simp"


# ---------------------------------------------------------------------------
# verify: the six-verdict taxonomy is unchanged
# ---------------------------------------------------------------------------
def test_verdict_taxonomy_keeps_exactly_the_six_recorded_strings():
    """No seventh verdict (notably no ``"timeout"``): `runner` maps only these six."""
    from typing import get_args

    assert set(get_args(verify.Verdict)) == {
        "success", "lean_error", "incomplete", "given_up", "exception", "replay_failed",
    }


def test_verify_no_longer_imports_lean_dojo():
    """The backend swap is only real if the deprecated interaction layer is gone."""
    from pathlib import Path

    src = Path(verify.__file__).read_text()
    assert "import lean_dojo" not in src
    assert "from lean_dojo" not in src


def test_verify_imports_with_lean_interact():
    """A cold import of the verifier must succeed with only `lean_interact` present.

    The pop/restore is deliberate. Re-executing the module binds a NEW module
    object onto the `smolbench.deduction.lean` package, so leaving it in place
    would make `runner._default_verifier()` return an object that is no longer
    identical to this test module's `verify` global -- a cross-test failure that
    depends purely on execution order.
    """
    pytest.importorskip("lean_interact")
    from smolbench.deduction import lean as lean_pkg

    saved = sys.modules.pop("smolbench.deduction.lean.verify", None)
    try:
        import smolbench.deduction.lean.verify  # noqa: F401
    finally:
        if saved is not None:
            sys.modules["smolbench.deduction.lean.verify"] = saved
            lean_pkg.verify = saved


def test_verify_dataclass_fields_are_unchanged():
    """`runner` reads these by name; a rename silently blanks a results column."""
    from dataclasses import fields

    assert [f.name for f in fields(verify.ReplayResult)] == [
        "theorem", "verdict", "tactics_applied", "tactics_total", "error", "final_state_pp",
    ]
    assert [f.name for f in fields(verify.ProofResult)] == [
        "theorem", "verdict", "tail_tried", "error", "final_state_pp",
    ]


# ---------------------------------------------------------------------------
# verify.try_tail
# ---------------------------------------------------------------------------
def test_try_tail_reports_success_when_the_last_tactic_closes_every_goal():
    session = FakeSession({"intro h": _ok(), "exact foo": _DONE})
    res = verify.try_tail(session, 0, "intro h\nexact foo", "Mini.theoremA")
    assert (res.verdict, res.theorem, res.tail_tried) == (
        "success", "Mini.theoremA", "intro h\nexact foo",
    )
    assert res.error is None


def test_try_tail_threads_the_returned_proof_state_between_tactics():
    """Each step must branch from the PREVIOUS step's state, not from `state_at_k`."""
    session = FakeSession({"intro h": _ok(), "exact foo": _DONE})
    verify.try_tail(session, 3, "intro h\nexact foo", "t")
    assert session.seen == [(3, "intro h"), (7, "exact foo")]


def test_try_tail_reports_lean_error_naming_the_failing_step_and_tactic():
    session = FakeSession(
        {
            "intro h": _ok(),
            "frobnicate": replbackend.StepOutcome(
                kind="lean_error", proof_state=None,
                error="unknown tactic 'frobnicate'", goals_pp=None,
            ),
        }
    )
    res = verify.try_tail(session, 0, "intro h\nfrobnicate", "t")
    assert res.verdict == "lean_error"
    assert "tail step 2/2" in res.error
    assert "'frobnicate'" in res.error
    assert "unknown tactic" in res.error


def test_try_tail_reports_given_up_for_a_sorry():
    session = FakeSession(
        {"sorry": replbackend.StepOutcome("given_up", None, None, None)}
    )
    assert verify.try_tail(session, 0, "sorry", "t").verdict == "given_up"


def test_try_tail_reports_incomplete_with_the_final_state_when_tactics_run_out():
    session = FakeSession({"intro h": _ok(["⊢ Q n"])})
    res = verify.try_tail(session, 0, "intro h", "t")
    assert res.verdict == "incomplete"
    assert res.final_state_pp == "⊢ Q n"


def test_try_tail_reports_an_empty_tail_as_lean_error():
    res = verify.try_tail(FakeSession(), 0, "   \n\n  ", "t")
    assert res.verdict == "lean_error"
    assert res.error == "empty tail"


def test_try_tail_ignores_blank_lines_when_splitting_tactics():
    session = FakeSession({"intro h": _ok(), "exact foo": _DONE})
    verify.try_tail(session, 0, "\n  intro h  \n\n exact foo \n", "t")
    assert [t for _, t in session.seen] == ["intro h", "exact foo"]


def test_try_tail_does_not_split_on_tactic_combinators():
    """``t1 <;> t2`` is ONE tactic; splitting it changes what is being verified."""
    session = FakeSession({"constructor <;> simp": _DONE})
    assert verify.try_tail(session, 0, "constructor <;> simp", "t").verdict == "success"


def test_try_tail_raises_on_a_repl_level_failure_so_the_caller_maps_it_to_exception():
    """`try_tail` never returns ``"exception"``; `runner`/`verify_proof_tail` build it."""
    session = FakeSession({"rfl": replbackend.ReplError("timeout: 30s")})
    with pytest.raises(replbackend.ReplError):
        verify.try_tail(session, 0, "rfl", "t")


def test_try_tail_maps_an_exception_kind_outcome_to_a_raise():
    session = FakeSession(
        {"rfl": replbackend.StepOutcome("exception", None, "unknown proofState", None)}
    )
    with pytest.raises(replbackend.ReplError) as exc:
        verify.try_tail(session, 0, "rfl", "t")
    assert "unknown proofState" in str(exc.value)


# ---------------------------------------------------------------------------
# verify.open_at_step
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("k", [-1, 3, 4])
def test_open_at_step_refuses_an_out_of_range_k(k, monkeypatch):
    session = FakeSession()
    _install_session(monkeypatch, session)
    bt = _bt(["a", "b", "c"])
    with pytest.raises(ValueError):
        with verify.open_at_step(bt, k):
            pass
    assert session.closed == 0, "no session may be opened for an invalid k"


def test_open_at_step_replays_the_prefix_and_yields_the_reached_state(monkeypatch):
    session = FakeSession({"a": _ok(), "b": _ok()})
    calls = _install_session(monkeypatch, session, state=5)
    with verify.open_at_step(_bt(["a", "b", "c"]), 2, timeout=99) as (s, state):
        assert s is session
        assert state == 7
    assert [t for _, t in session.seen] == ["a", "b"]
    assert session.seen[0][0] == 5
    assert calls[0]["timeout"] == 99
    assert session.closed == 1


def test_open_at_step_with_k_zero_replays_nothing(monkeypatch):
    session = FakeSession()
    _install_session(monkeypatch, session, state=5)
    with verify.open_at_step(_bt(["a", "b"]), 0) as (_s, state):
        assert state == 5
    assert session.seen == []


def test_open_at_step_raises_runtime_error_when_the_ground_truth_prefix_fails(monkeypatch):
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


def test_open_at_step_raises_when_the_prefix_closes_the_proof_early(monkeypatch):
    """A prefix shorter than the full proof must not reach `success`."""
    session = FakeSession({"a": _DONE})
    _install_session(monkeypatch, session)
    with pytest.raises(RuntimeError):
        with verify.open_at_step(_bt(["a", "b"]), 1):
            pass
    assert session.closed == 1


def test_open_at_step_closes_the_session_when_the_body_raises(monkeypatch):
    session = FakeSession({"a": _ok()})
    _install_session(monkeypatch, session)
    with pytest.raises(ZeroDivisionError):
        with verify.open_at_step(_bt(["a", "b"]), 1):
            raise ZeroDivisionError
    assert session.closed == 1


# ---------------------------------------------------------------------------
# verify.verify_proof_tail
# ---------------------------------------------------------------------------
def test_verify_proof_tail_returns_try_tails_result(monkeypatch):
    # k=1, so the ground-truth prefix ["a"] is replayed before the tail runs;
    # `FakeSession` raises KeyError on an unscripted tactic, so both must be here.
    session = FakeSession({"a": _ok(), "exact foo": _DONE})
    _install_session(monkeypatch, session)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 1, "exact foo")
    assert res.verdict == "success"
    assert [t for _, t in session.seen] == ["a", "exact foo"]
    assert session.closed == 1


@pytest.mark.parametrize("k", [-1, 2, 7])
def test_verify_proof_tail_reports_an_out_of_range_k_as_exception_without_opening(k, monkeypatch):
    session = FakeSession()
    _install_session(monkeypatch, session)
    res = verify.verify_proof_tail(_bt(["a", "b"]), k, "rfl")
    assert res.verdict == "exception"
    assert f"k={k}" in res.error
    assert session.closed == 0


def test_verify_proof_tail_reports_an_empty_tail_as_lean_error_without_opening(monkeypatch):
    session = FakeSession()
    _install_session(monkeypatch, session)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 0, "\n \n")
    assert (res.verdict, res.error) == ("lean_error", "empty tail")
    assert session.closed == 0


def test_verify_proof_tail_reports_a_broken_prefix_as_replay_failed(monkeypatch):
    session = FakeSession({"a": replbackend.StepOutcome("lean_error", None, "boom", None)})
    _install_session(monkeypatch, session)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 1, "rfl")
    assert res.verdict == "replay_failed"
    assert "Mini.theoremA" in res.error


def test_verify_proof_tail_reports_a_repl_failure_as_exception_with_the_type_prefix(monkeypatch):
    session = FakeSession({"rfl": replbackend.ReplError("timeout: 30s")})
    _install_session(monkeypatch, session)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 0, "rfl")
    assert res.verdict == "exception"
    assert res.error.startswith("ReplError: ")
    assert "timeout" in res.error


def test_verify_proof_tail_reports_a_failure_to_open_a_session_as_exception(monkeypatch):
    def boom(bt, timeout=600, **kwargs):
        raise replbackend.ReplError("elan not found on PATH")

    monkeypatch.setattr(replbackend, "open_session", boom)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 0, "rfl")
    assert res.verdict == "exception"
    assert "elan not found" in res.error


# ---------------------------------------------------------------------------
# verify.replay_ground_truth
# ---------------------------------------------------------------------------
def test_replay_ground_truth_reports_a_theorem_with_no_tactics_without_opening(monkeypatch):
    session = FakeSession()
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt([]))
    assert (res.verdict, res.tactics_applied, res.tactics_total) == ("incomplete", 0, 0)
    assert res.error == "no traced tactics"
    assert session.closed == 0


def test_replay_ground_truth_reports_success_and_counts_the_closing_tactic(monkeypatch):
    session = FakeSession({"a": _ok(), "b": _ok(), "c": _DONE})
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt(["a", "b", "c"]))
    assert (res.verdict, res.tactics_applied, res.tactics_total) == ("success", 3, 3)
    assert session.closed == 1


def test_replay_ground_truth_reports_lean_error_with_the_count_before_the_failure(monkeypatch):
    session = FakeSession(
        {"a": _ok(), "b": replbackend.StepOutcome("lean_error", None, "boom", None)}
    )
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt(["a", "b", "c"]))
    assert (res.verdict, res.tactics_applied, res.tactics_total) == ("lean_error", 1, 3)
    assert res.error == "boom"
    assert session.closed == 1


def test_replay_ground_truth_reports_given_up_counting_the_giving_tactic(monkeypatch):
    session = FakeSession({"a": _ok(), "b": replbackend.StepOutcome("given_up", None, None, None)})
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt(["a", "b", "c"]))
    assert (res.verdict, res.tactics_applied, res.tactics_total) == ("given_up", 2, 3)


def test_replay_ground_truth_reports_incomplete_with_the_final_state(monkeypatch):
    session = FakeSession({"a": _ok(), "b": _ok(["⊢ R n"])})
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt(["a", "b"]))
    assert (res.verdict, res.tactics_applied, res.tactics_total) == ("incomplete", 2, 2)
    assert res.final_state_pp == "⊢ R n"


def test_replay_ground_truth_never_propagates_an_exception(monkeypatch):
    """Callers loop over many theorems; one broken session must not abort the batch."""
    session = FakeSession({"a": replbackend.ReplError("server died")})
    _install_session(monkeypatch, session)
    res = verify.replay_ground_truth(_bt(["a", "b"]))
    assert res.verdict == "exception"
    assert res.error.startswith("ReplError: ")
    assert res.tactics_total == 2
    assert session.closed == 1


def test_replay_ground_truth_reports_a_failure_to_open_as_exception(monkeypatch):
    def boom(bt, timeout=600, **kwargs):
        raise replbackend.ReplError("no mathlib root")

    monkeypatch.setattr(replbackend, "open_session", boom)
    res = verify.replay_ground_truth(_bt(["a", "b"]))
    assert res.verdict == "exception"
    assert "no mathlib root" in res.error


def test_replay_ground_truth_never_returns_replay_failed(monkeypatch):
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


# ---------------------------------------------------------------------------
# Cross-module: the runner's verifier protocol still resolves and matches
# ---------------------------------------------------------------------------
def test_runner_default_verifier_resolves_to_this_module():
    from smolbench.deduction.lean import runner

    assert runner._default_verifier() is verify


def test_nullverifier_mirrors_the_real_result_dataclasses():
    """`runner` builds rows from either; a field drift blanks a results column."""
    from dataclasses import fields

    from smolbench.deduction.lean import nullverify

    assert [f.name for f in fields(nullverify.NullReplayResult)] == [
        f.name for f in fields(verify.ReplayResult)
    ]
    assert [f.name for f in fields(nullverify.NullProofResult)] == [
        f.name for f in fields(verify.ProofResult)
    ]


def test_verify_exposes_every_name_the_runner_protocol_needs():
    for attr in ("open_at_step", "try_tail", "replay_ground_truth", "verify_proof_tail",
                 "ProofResult", "ReplayResult"):
        assert hasattr(verify, attr), attr


# ---------------------------------------------------------------------------
# Docs / packaging seams
#
# The TEXT-ONLY guarantees (pyproject's `lean` extra, the README and the smoke
# skill) live in tests/deduction/test_lean_verify_docs.py instead: this module
# skips wholesale when `lean_interact` is absent, and the pyproject guarantee is
# precisely what must NOT vanish in that case.
# ---------------------------------------------------------------------------
def test_verify_rows_script_guard_requires_lean_interact():
    import importlib.util

    from tests._paths import SCRIPTS

    spec = importlib.util.spec_from_file_location(
        "lvr_seam", SCRIPTS / "deduction" / "lean_verify_rows.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["lvr_seam"] = module
    try:
        spec.loader.exec_module(module)
        src = (SCRIPTS / "deduction" / "lean_verify_rows.py").read_text()
        assert "lean_interact" in src
        # The guard passes here because lean_interact IS installed in this venv.
        module.require_lean_dojo()
    finally:
        sys.modules.pop("lvr_seam", None)


# ---------------------------------------------------------------------------
# open_session: configuration errors and retry policy
# ---------------------------------------------------------------------------
class _FakeTime:
    """Stand-in for the `time` module: records sleeps instead of taking them."""

    def __init__(self):
        self.slept: list[float] = []

    def sleep(self, seconds):
        self.slept.append(seconds)


def _command(**wire) -> "object":
    from lean_interact.interface import CommandResponse

    payload = {"env": 0}
    payload.update(wire)
    return CommandResponse.model_validate(payload)


def test_open_session_reports_a_misconfigured_root_as_a_repl_error(monkeypatch):
    """`mathlib_root` raises `RuntimeError`, and `verify_proof_tail` reads a bare
    `RuntimeError` as ``"replay_failed"`` -- a claim about the CORPUS. A missing
    `SMOLBENCH_MATHLIB_ROOT` must not condemn every ground-truth proof, so
    `open_session` has to translate it before it can be mistaken for one."""
    monkeypatch.delenv("SMOLBENCH_MATHLIB_ROOT", raising=False)
    with pytest.raises(replbackend.ReplError) as exc:
        replbackend.open_session(_bt(["a"]))
    assert "SMOLBENCH_MATHLIB_ROOT" in str(exc.value)


def test_verify_proof_tail_reports_a_misconfigured_root_as_exception(monkeypatch):
    """End-to-end teeth for the above: the verdict must be ``exception``."""
    monkeypatch.delenv("SMOLBENCH_MATHLIB_ROOT", raising=False)
    res = verify.verify_proof_tail(_bt(["a", "b"]), 1, "rfl")
    assert res.verdict == "exception", res
    assert "SMOLBENCH_MATHLIB_ROOT" in res.error


def test_replay_ground_truth_reports_a_misconfigured_root_as_exception(monkeypatch):
    monkeypatch.delenv("SMOLBENCH_MATHLIB_ROOT", raising=False)
    res = verify.replay_ground_truth(_bt(["a", "b"]))
    assert res.verdict == "exception"
    assert "SMOLBENCH_MATHLIB_ROOT" in res.error


class _ElaborationFailsServer:
    """Imports fine, then reports an error for the statement stub. Deterministic."""

    def __init__(self, log):
        log.append("start")
        self.killed = 0

    def run(self, request, *, verbose=False, timeout=None):
        if getattr(request, "cmd", "").startswith("import"):
            return _command(env=3)
        return _command(env=4, messages=[_msg("unknown identifier 'P'")])

    def kill(self):
        self.killed += 1


def test_open_session_does_not_retry_a_deterministic_statement_failure(monkeypatch):
    """An unelaborable statement fails identically every time.

    Under the import-only environment this backend builds, that failure is
    EXPECTED to be common, and retrying it costs 20s of sleeps plus three Lean
    startups per theorem for no chance of a different answer.
    """
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(PROJECT))
    fake_time = _FakeTime()
    monkeypatch.setattr(replbackend, "time", fake_time)
    log: list[str] = []

    with pytest.raises(replbackend.ReplError) as exc:
        replbackend.open_session(_bt(["a"]), server_factory=lambda root: _ElaborationFailsServer(log))

    assert "unknown identifier" in str(exc.value)
    assert "Mini.theoremA" in str(exc.value)
    assert log == ["start"], f"the server was started {len(log)} times, expected once"
    assert fake_time.slept == []


def test_open_session_retries_a_transient_server_start_failure(monkeypatch):
    """A racing Lean startup IS worth retrying -- that is what the backoff is for."""
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(PROJECT))
    fake_time = _FakeTime()
    monkeypatch.setattr(replbackend, "time", fake_time)
    attempts: list[int] = []

    class _Good:
        def run(self, request, *, verbose=False, timeout=None):
            if getattr(request, "cmd", "").startswith("import"):
                return _command(env=3)
            return _command(env=4, sorries=[{"goal": "⊢ Q n", "proofState": 11}])

        def kill(self):
            pass

    def factory(root):
        attempts.append(1)
        if len(attempts) < 3:
            raise OSError("Unexpected EOF from the Lean process")
        return _Good()

    session, state = replbackend.open_session(_bt(["a"]), server_factory=factory)
    assert state == 11
    assert len(attempts) == 3
    assert fake_time.slept == [5.0, 15.0]


def test_open_session_returns_the_sorrys_proof_state_on_the_happy_path(monkeypatch):
    monkeypatch.setenv("SMOLBENCH_MATHLIB_ROOT", str(PROJECT))
    sent: list[object] = []

    class _Good:
        def run(self, request, *, verbose=False, timeout=None):
            sent.append(request)
            if getattr(request, "cmd", "").startswith("import"):
                return _command(env=3)
            return _command(env=4, sorries=[{"goal": "⊢ Q n", "proofState": 11}])

        def kill(self):
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
