"""Offline tests for ``scripts/annotate_lean_cot.py`` (Package D of the
2026-07-12 CoT SFT plan) -- the Bedrock Converse CoT annotator.

Everything here mocks the Converse client with a plain `StubClient` (a
``.converse`` method returning canned/controlled responses) rather than a
real ``boto3``/``botocore`` client. The one place a real
``botocore.exceptions.ClientError`` is constructed (to exercise the
retry/backoff error-code classification) is guarded with
``pytest.importorskip("botocore")`` -- boto3/botocore happen to be
installed in both project venvs, but this module and its tests are
designed not to *require* them to be importable, per the module's own
"boto3 import goes inside main/the client class" design.

Decontam tests build a bare, empty `HoldoutIndex()` (or one with a single
hand-planted key) directly, rather than depending on the committed
``lean_mini`` fixture -- these tests are about THIS script's own control
flow (QC gates, resume, manifest/QC-report shape, the preflight-before-spend
ordering), not about `HoldoutIndex`'s own key-family matching, which
``tests/test_lean_decontam.py`` already covers against that fixture.
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts import annotate_lean_cot as ac  # noqa: E402
from smolbench.deduction.lean import corpus  # noqa: E402
from smolbench.deduction.lean.decontam import HoldoutIndex, normalize_text  # noqa: E402
from smolbench.deduction.lean.prompt import extract_tactic_block  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------


def _row(full_name: str, k: int, tail: str, user: str | None = None) -> dict:
    """One synthetic bare-tail SFT row, shaped like build_lean_sft.py's output."""
    return {
        "system": "SYS",
        "user": user or f"## Current goal\n```\n⊢ {full_name}_goal x y\n```\n\nProduce the remaining tactics.",
        "assistant": tail,
        "meta": {"full_name": full_name, "k": k, "n_tail": 1},
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


class StubClient:
    """Converse-shaped stub standing in for a real boto3 bedrock-runtime client.

    ``respond(user_text) -> str`` is invoked for every `.converse` call and
    either returns the response text or raises to simulate a failure.
    Thread-safe call recording, since `_run_annotation` calls `.converse`
    from a worker thread pool.
    """

    def __init__(self, respond) -> None:
        self._respond = respond
        self._lock = threading.Lock()
        self.calls: list[str] = []

    def converse(self, *, modelId, system, messages, inferenceConfig):  # noqa: N803 (matches boto3's casing)
        text = messages[0]["content"][0]["text"]
        with self._lock:
            self.calls.append(text)
        result = self._respond(text)
        return {"output": {"message": {"content": [{"text": result}]}}}


#: A rationale that passes every QC gate against any of this file's short,
#: distinctively-named synthetic tails (no accidental substring overlap
#: with common English words -- see the restatement-gate tests for why that
#: matters).
_GOOD_RATIONALE = (
    "We inspect the goal and the local hypotheses, and the completion below closes it "
    "directly by combining them in the natural order."
)


@pytest.fixture()
def empty_index(monkeypatch):
    """Monkeypatch `HoldoutIndex.build` to skip the real eval-corpus load and
    return an empty index. `ac.HoldoutIndex` is the same class object as
    `smolbench.deduction.lean.decontam.HoldoutIndex` (imported by name), so
    patching the class here also affects `ac.main`'s ``HoldoutIndex.build()``
    call.
    """
    monkeypatch.setattr(HoldoutIndex, "build", classmethod(lambda cls, *a, **kw: cls()))


@pytest.fixture()
def dataset_file(tmp_path):
    """A tiny synthetic 4-row source JSONL, shaped like the real dataset."""
    rows = [
        _row("Alpha.thm1", 1, "exact alpha_lemma_one"),
        _row("Beta.thm2", 3, "simp [beta_helper]\nrfl"),
        _row("Gamma.thm3", 2, "omega"),
        _row("Delta.thm4", 1, "linarith [delta_bound]"),
    ]
    path = tmp_path / "src.jsonl"
    _write_jsonl(path, rows)
    return path, rows


# ---------------------------------------------------------------------------
# compose_target: exact shape + round-trip through extract_tactic_block
# ---------------------------------------------------------------------------


def test_compose_target_think_shape():
    assert ac.compose_target("think", "R", "T") == "<think>\nR\n</think>\n\nT"


def test_compose_target_fenced_shape():
    assert ac.compose_target("fenced", "R", "T") == "R\n\n```lean\nT\n```"


def test_compose_target_rejects_unknown_style():
    with pytest.raises(ValueError):
        ac.compose_target("bogus", "R", "T")


@pytest.mark.parametrize("style", ["think", "fenced"])
def test_compose_target_round_trips_tail_byte_identical(style):
    tail = "rw [Nat.add_comm]\nomega"
    rationale = "We reorder the addition using commutativity, then close the linear goal."
    composed = ac.compose_target(style, rationale, tail)
    assert extract_tactic_block(composed) == tail


@pytest.mark.parametrize("style", ["think", "fenced"])
def test_compose_target_round_trips_single_line_tail(style):
    tail = "omega"
    composed = ac.compose_target(style, _GOOD_RATIONALE, tail)
    assert extract_tactic_block(composed) == tail


# ---------------------------------------------------------------------------
# QC gates
# ---------------------------------------------------------------------------


def test_qc_gate_passes_a_clean_rationale():
    assert ac._qc_gate(_GOOD_RATIONALE, "omega", max_rationale_chars=2500) is None


def test_qc_gate_empty_rationale():
    assert ac._qc_gate("", "omega", max_rationale_chars=2500) == "empty_rationale"
    assert ac._qc_gate("   ", "omega", max_rationale_chars=2500) == "empty_rationale"


@pytest.mark.parametrize(
    "bad",
    ["contains a ``` fence right here", "opens a <think> tag", "closes a </think> tag"],
)
def test_qc_gate_forbidden_markup(bad):
    assert ac._qc_gate(bad, "omega", max_rationale_chars=2500) == "forbidden_markup"


def test_qc_gate_too_long():
    assert ac._qc_gate("x" * 2501, "omega", max_rationale_chars=2500) == "too_long"
    assert ac._qc_gate("x" * 2500, "omega", max_rationale_chars=2500) is None


@pytest.mark.parametrize(
    "hedged",
    [
        "This rewrites via the lemma `foo_comm` or similar, closing the goal.",
        "The lemma likely states that addition commutes, so `simp` closes it.",
        "Probably the hypothesis h gives the bound we need for the final step.",
        "PERHAPS the coercion is stripped first; then the equality is direct.",
    ],
)
def test_qc_gate_hedging_rejected(hedged):
    assert ac._qc_gate(hedged, "omega", max_rationale_chars=2500) == "hedging"


def test_qc_gate_hedging_no_interior_word_match():
    # "unlikely" must NOT trip the \b-anchored "likely" pattern -- committed
    # mathematical prose legitimately uses it.
    ok = "It is unlikely simplification alone suffices, so we invoke the hypothesis h directly to conclude."
    assert ac._qc_gate(ok, "omega", max_rationale_chars=2500) is None


def test_qc_gate_hedging_checked_after_size_gates():
    # Gate ordering: a hedged rationale that is ALSO too long counts against
    # the earlier reason (histogram attribution is first-trip-only).
    hedged_long = ("perhaps " * 400).strip()
    assert ac._qc_gate(hedged_long, "omega", max_rationale_chars=2500) == "too_long"


def test_qc_gate_restatement_single_line_tail_needs_exact_match():
    tail = "omega"
    assert ac._qc_gate("omega", tail, max_rationale_chars=2500) == "restatement"
    # Merely CONTAINING the one-line tail as a substring is NOT a restatement
    # for single-line tails (spec: exact-match only) -- a rationale that
    # names the tactic in passing is a legitimate explanation.
    assert ac._qc_gate("we close this goal with omega directly here.", tail, max_rationale_chars=2500) is None


def test_qc_gate_restatement_multiline_all_lines_verbatim():
    tail = "intro h\nsimp only [foo]\nexact bar"
    assert ac._qc_gate(tail, tail, max_rationale_chars=2500) == "restatement"


def test_qc_gate_restatement_exact_half_boundary_triggers():
    # 2 of 4 tail lines verbatim = 50% -- the spec's ">=50%" threshold.
    tail = "line_a\nline_b\nline_c\nline_d"
    rationale = "Some prose containing line_a and also line_b somewhere in here for good measure."
    assert ac._qc_gate(rationale, tail, max_rationale_chars=2500) == "restatement"


def test_qc_gate_restatement_below_half_boundary_passes():
    # 1 of 4 tail lines verbatim = 25% -- under the threshold.
    tail = "line_a\nline_b\nline_c\nline_d"
    rationale = "Some prose containing only line_a and nothing else relevant to the rest here."
    assert ac._qc_gate(rationale, tail, max_rationale_chars=2500) is None


# ---------------------------------------------------------------------------
# _is_restatement directly (edge cases)
# ---------------------------------------------------------------------------


def test_is_restatement_single_line_false_on_non_exact_match():
    assert ac._is_restatement("this mentions rfl in passing", "rfl") is False


def test_is_restatement_single_line_true_on_exact_match():
    assert ac._is_restatement("rfl", "rfl") is True
    assert ac._is_restatement("  rfl  ", "rfl") is True  # whitespace-insensitive


# ---------------------------------------------------------------------------
# _process_annotation: rationale-content decontam (K2 exact+near-dup, K3
# exact-vs-prose) + grounding
# ---------------------------------------------------------------------------


def test_process_annotation_drops_rationale_that_leaks_an_eval_state():
    idx = HoldoutIndex()
    leaked_state = "n : Nat\nh : n > 0\n⊢ SomeSecretEvalGoal n"
    idx.states[normalize_text(leaked_state)] = "Eval.secretThm"

    row = _row("Real.thm", 1, "omega")
    reason, kept = ac._process_annotation(row, leaked_state, style="think", index=idx, max_rationale_chars=2500)
    assert kept is None
    # Hand-planted directly into idx.states (not via _add_theorem), so
    # idx.statements is empty -- the statement= branch itself falls through
    # to a self.states lookup (see HoldoutIndex.check's own docstring: "a
    # statement...may be a mid-proof eval state"), landing on key="state"
    # either way. Confirmed empirically: this fix does not change this
    # particular test's expected reason.
    assert reason == "rationale_leak_state"


def test_process_annotation_drops_rationale_that_near_duplicates_an_eval_statement():
    """Fix 4: `_process_annotation` now passes `statement=rationale` (not
    just `states=[rationale]`) to `index.check` -- reaching the K2
    NEAR-DUPLICATE (MinHash/LSH) family, which the plain `states=` exact
    sweep never reaches at all. Same long-statement / single-hypothesis-
    rename recipe as tests/test_lean_decontam.py's own
    `test_k2_near_duplicate_alpha_rename_hit` (proven there to clear the
    0.85 Jaccard threshold), just driven through this script's own
    _process_annotation call site: a rationale that PARAPHRASES a memorized
    eval statement (one hypothesis alpha-renamed), rather than quoting it
    byte-for-byte, must still be dropped.
    """
    long_stmt = (
        "F : Type u_1\ninst : Field F\ns t : Set F\nm : F ≃+* F\n"
        "hs : s ⊆ Set.range ↑m\nht : t ⊆ Set.range ↑m\n⊢ s / t ⊆ Set.range ↑m"
    )
    idx = HoldoutIndex()
    fake = corpus.BenchmarkTheorem(
        url="https://github.com/leanprover-community/mathlib4",
        commit="fe4454af900584467d21f4fd4fe951d29d9332a7",
        file_path="Mini/Long.lean",
        full_name="Eval.longStatement",
        start=(1, 1),
        end=(1, 1),
        traced_tactics=[
            corpus.TracedTactic(tactic="simp", state_before=long_stmt, state_after="no goals", premises=[])
        ],
    )
    idx._add_theorem(fake)
    renamed = long_stmt.replace("hs :", "h1 :")

    row = _row("Real.thm", 1, "omega")
    reason, kept = ac._process_annotation(row, renamed, style="think", index=idx, max_rationale_chars=2500)
    assert kept is None
    assert reason == "rationale_leak_statement_near"


def test_process_annotation_keeps_clean_rationale_and_reports_name_mentions():
    idx = HoldoutIndex()
    idx.names.add("Real.helperLemma")

    row = _row("Real.thm", 1, "omega")
    rationale = f"{_GOOD_RATIONALE} This mirrors the classic Real.helperLemma pattern."
    reason, kept = ac._process_annotation(row, rationale, style="think", index=idx, max_rationale_chars=2500)

    assert reason is None
    assert kept is not None
    # A name mention is informational, NOT a drop -- see decontam.count_name_mentions.
    assert kept["mentions"] == 1
    assert kept["record"]["meta"]["holdout_name_mentions"] == 1
    assert kept["record"]["assistant"] == ac.compose_target("think", rationale.strip(), "omega")
    assert extract_tactic_block(kept["record"]["assistant"]) == "omega"


def test_process_annotation_marks_grounded_when_rationale_mentions_goal_identifier():
    idx = HoldoutIndex()
    user = "## Current goal\n```\n⊢ myWeirdIdentifier n = otherThing n\n```\n\nProduce tactics."
    row = {"system": "s", "user": user, "assistant": "omega", "meta": {"full_name": "T", "k": 0}}
    rationale = "The goal mentions myWeirdIdentifier, and omega finishes the arithmetic directly here today."

    reason, kept = ac._process_annotation(row, rationale, style="think", index=idx, max_rationale_chars=2500)
    assert reason is None
    assert kept["grounded"] is True


def test_process_annotation_not_grounded_without_identifier_overlap():
    idx = HoldoutIndex()
    user = "## Current goal\n```\n⊢ myWeirdIdentifier n = otherThing n\n```\n\nProduce tactics."
    row = {"system": "s", "user": user, "assistant": "omega", "meta": {"full_name": "T", "k": 0}}
    rationale = "This closes via straightforward reasoning about the local context and nothing fancy needed."

    reason, kept = ac._process_annotation(row, rationale, style="think", index=idx, max_rationale_chars=2500)
    assert reason is None
    assert kept["grounded"] is False


# ---------------------------------------------------------------------------
# Preflight (hard-error) BARE-facet re-scan
# ---------------------------------------------------------------------------


def test_preflight_bare_facet_check_passes_clean_rows():
    idx = HoldoutIndex()
    row = _row("Real.thm", 1, "omega")
    ac._preflight_bare_facet_check([row], idx)  # must not raise


def test_preflight_bare_facet_check_raises_on_leak():
    from scripts.build_lean_synth_sft import _facets_from_rendered

    idx = HoldoutIndex()
    row = _row("Real.thm", 1, "exact leaked_tactic_call")
    states, tactics, pairs = _facets_from_rendered(row["user"], row["assistant"])
    idx.pairs[(normalize_text(states[0]), normalize_text(tactics[0]))] = "Eval.leakedThm"

    with pytest.raises(SystemExit):
        ac._preflight_bare_facet_check([row], idx)


# ---------------------------------------------------------------------------
# Seeded subsample: determinism, order-independence, limit=0
# ---------------------------------------------------------------------------


def _keys(rows):
    return {(r["meta"]["full_name"], r["meta"]["k"]) for r in rows}


def test_select_subsample_is_independent_of_file_order():
    import random

    rows = [_row(f"T{i}", i % 3, "tac") for i in range(40)]
    shuffled = rows[:]
    random.Random(7).shuffle(shuffled)

    a = ac._select_subsample(rows, seed=1776, limit=10)
    b = ac._select_subsample(shuffled, seed=1776, limit=10)
    assert _keys(a) == _keys(b)
    assert len(_keys(a)) == 10


def test_select_subsample_zero_limit_keeps_everything():
    rows = [_row(f"T{i}", 0, "tac") for i in range(5)]
    assert ac._select_subsample(rows, seed=1, limit=0) == rows


def test_select_subsample_limit_ge_len_keeps_everything():
    rows = [_row(f"T{i}", 0, "tac") for i in range(5)]
    assert ac._select_subsample(rows, seed=1, limit=100) == rows


def test_select_subsample_different_seed_gives_different_set():
    rows = [_row(f"T{i}", i % 3, "tac") for i in range(200)]
    a = ac._select_subsample(rows, seed=1, limit=20)
    b = ac._select_subsample(rows, seed=2, limit=20)
    assert _keys(a) != _keys(b)


def test_default_out_naming():
    assert ac._default_out("think", 8000).name == "cot_stepk1_think_8k.jsonl"
    assert ac._default_out("think", 0).name == "cot_stepk1_think_full.jsonl"
    assert ac._default_out("fenced", 0).name == "cot_stepk1_fenced_full.jsonl"
    assert ac._default_out("fenced", 250).name == "cot_stepk1_fenced_250.jsonl"


# ---------------------------------------------------------------------------
# Resume done-set
# ---------------------------------------------------------------------------


def test_read_done_keys_empty_when_missing(tmp_path):
    assert ac._read_done_keys(tmp_path / "nope.jsonl") == set()


def test_read_done_keys_reads_existing(tmp_path):
    path = tmp_path / "out.jsonl"
    _write_jsonl(
        path,
        [
            {"system": "s", "user": "u", "assistant": "a", "meta": {"full_name": "Foo", "k": 1}},
            {"system": "s", "user": "u", "assistant": "a", "meta": {"full_name": "Bar", "k": 2}},
        ],
    )
    assert ac._read_done_keys(path) == {("Foo", 1), ("Bar", 2)}


# ---------------------------------------------------------------------------
# Paired bare-control sibling (Fix 1: _sibling_bare_path / _write_bare_sibling)
# ---------------------------------------------------------------------------


def test_sibling_bare_path_replaces_style_segment():
    assert ac._sibling_bare_path(Path("/x/cot_stepk1_think_8k.jsonl"), "think").name == "cot_stepk1_bare_8k.jsonl"
    assert ac._sibling_bare_path(Path("/x/cot_stepk1_fenced_full.jsonl"), "fenced").name == "cot_stepk1_bare_full.jsonl"
    # Parent directory is preserved.
    assert ac._sibling_bare_path(Path("/x/y/cot_stepk1_think_8k.jsonl"), "think").parent == Path("/x/y")


def test_sibling_bare_path_matches_style_by_segment_not_position():
    # The style token located anywhere among the '_'-delimited segments
    # (not hardcoded to index 2) still resolves correctly.
    assert ac._sibling_bare_path(Path("/x/prefix_extra_think_8k.jsonl"), "think").name == "prefix_extra_bare_8k.jsonl"


def test_sibling_bare_path_raises_on_nonconforming_name():
    with pytest.raises(ValueError, match="bare-control sibling"):
        ac._sibling_bare_path(Path("/x/out.jsonl"), "think")


def test_write_bare_sibling_byte_identical_rows_same_order(tmp_path):
    """The sibling's rows are the ORIGINAL source rows (untouched system/
    user/assistant/meta -- no cot_style key added), in the SAME ORDER as
    the annotated --out file."""
    source_a = _row("Alpha.thm1", 1, "exact alpha_lemma_one")
    source_b = _row("Beta.thm2", 3, "simp [beta_helper]\nrfl")
    out_path = tmp_path / "cot_stepk1_think_2.jsonl"
    # Annotated output written in Beta-then-Alpha order (deliberately NOT
    # dataset order) -- the sibling must mirror THIS order.
    _write_jsonl(
        out_path,
        [
            {**source_b, "assistant": ac.compose_target("think", _GOOD_RATIONALE, source_b["assistant"]),
             "meta": {**source_b["meta"], "cot_style": "think"}},
            {**source_a, "assistant": ac.compose_target("think", _GOOD_RATIONALE, source_a["assistant"]),
             "meta": {**source_a["meta"], "cot_style": "think"}},
        ],
    )
    source_rows_by_key = {
        (source_a["meta"]["full_name"], source_a["meta"]["k"]): source_a,
        (source_b["meta"]["full_name"], source_b["meta"]["k"]): source_b,
    }

    sibling_path, n_written = ac._write_bare_sibling(out_path, style="think", source_rows_by_key=source_rows_by_key)

    assert sibling_path == tmp_path / "cot_stepk1_bare_2.jsonl"
    assert n_written == 2
    sibling_rows = [json.loads(line) for line in sibling_path.read_text(encoding="utf-8").splitlines()]
    assert [r["meta"]["full_name"] for r in sibling_rows] == ["Beta.thm2", "Alpha.thm1"]  # matches --out's order
    assert sibling_rows[0] == source_b  # byte-identical to the ORIGINAL (pre-annotation) row
    assert sibling_rows[1] == source_a
    assert "cot_style" not in sibling_rows[0]["meta"]


def test_write_bare_sibling_is_resume_safe_reflects_union(tmp_path):
    """The sibling is regenerated from --out's CURRENT content every call --
    so calling it again after --out gained more rows (simulating a resumed
    invocation) yields the UNION, not just the delta."""
    source_a = _row("Alpha.thm1", 1, "exact alpha_lemma_one")
    source_b = _row("Beta.thm2", 3, "simp [beta_helper]\nrfl")
    source_rows_by_key = {
        (source_a["meta"]["full_name"], source_a["meta"]["k"]): source_a,
        (source_b["meta"]["full_name"], source_b["meta"]["k"]): source_b,
    }
    out_path = tmp_path / "cot_stepk1_think_2.jsonl"

    # "Run 1": only Alpha has been annotated so far.
    _write_jsonl(
        out_path,
        [{**source_a, "assistant": ac.compose_target("think", _GOOD_RATIONALE, source_a["assistant"]),
          "meta": {**source_a["meta"], "cot_style": "think"}}],
    )
    _sibling_path, n1 = ac._write_bare_sibling(out_path, style="think", source_rows_by_key=source_rows_by_key)
    assert n1 == 1

    # "Run 2" (a resume): Beta gets appended to --out.
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({**source_b, "assistant": ac.compose_target("think", _GOOD_RATIONALE, source_b["assistant"]),
                             "meta": {**source_b["meta"], "cot_style": "think"}}) + "\n")
    sibling_path, n2 = ac._write_bare_sibling(out_path, style="think", source_rows_by_key=source_rows_by_key)

    assert n2 == 2  # union of both runs, not just this call's delta
    sibling_rows = [json.loads(line) for line in sibling_path.read_text(encoding="utf-8").splitlines()]
    assert {r["meta"]["full_name"] for r in sibling_rows} == {"Alpha.thm1", "Beta.thm2"}


def test_write_bare_sibling_missing_out_path_writes_empty_sibling(tmp_path):
    out_path = tmp_path / "cot_stepk1_think_8k.jsonl"  # never created
    sibling_path, n_written = ac._write_bare_sibling(out_path, style="think", source_rows_by_key={})
    assert n_written == 0
    assert sibling_path == tmp_path / "cot_stepk1_bare_8k.jsonl"
    assert sibling_path.exists()
    assert sibling_path.read_text() == ""


def test_write_bare_sibling_raises_keyerror_on_dataset_mismatch(tmp_path):
    """A key present in --out but absent from source_rows_by_key means the
    current --dataset no longer matches what was annotated -- fail loudly
    rather than silently de-pairing the two arms."""
    out_path = tmp_path / "cot_stepk1_think_1.jsonl"
    _write_jsonl(out_path, [_row("Ghost.thm", 9, "omega")])
    with pytest.raises(KeyError):
        ac._write_bare_sibling(out_path, style="think", source_rows_by_key={})


# ---------------------------------------------------------------------------
# BedrockAnnotator: retry/backoff classification
# ---------------------------------------------------------------------------


def test_annotator_retries_throttling_then_succeeds():
    pytest.importorskip("botocore")
    from botocore.exceptions import ClientError

    throttle = ClientError({"Error": {"Code": "ThrottlingException", "Message": "slow down"}}, "Converse")
    calls = {"n": 0}

    def respond(_text):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise throttle
        return "final rationale text"

    client = StubClient(respond)
    delays: list[float] = []
    annotator = ac.BedrockAnnotator(client=client, model="m", max_tokens=100, max_retries=6, sleep_fn=delays.append)

    assert annotator.annotate("prompt") == "final rationale text"
    assert calls["n"] == 3
    assert delays == [5.0, 10.0]  # exponential backoff, base 5s: 5, 10, ...


def test_annotator_raises_immediately_on_fatal_error_code():
    pytest.importorskip("botocore")
    from botocore.exceptions import ClientError

    fatal = ClientError({"Error": {"Code": "AccessDeniedException", "Message": "nope"}}, "Converse")

    def respond(_text):
        raise fatal

    client = StubClient(respond)
    delays: list[float] = []
    annotator = ac.BedrockAnnotator(client=client, model="m", max_tokens=100, max_retries=6, sleep_fn=delays.append)

    with pytest.raises(ClientError):
        annotator.annotate("prompt")
    assert delays == []  # never retried
    assert len(client.calls) == 1


def test_annotator_validation_exception_is_also_fatal():
    pytest.importorskip("botocore")
    from botocore.exceptions import ClientError

    fatal = ClientError({"Error": {"Code": "ValidationException", "Message": "bad request"}}, "Converse")

    def respond(_text):
        raise fatal

    client = StubClient(respond)
    delays: list[float] = []
    annotator = ac.BedrockAnnotator(client=client, model="m", max_tokens=100, max_retries=6, sleep_fn=delays.append)

    with pytest.raises(ClientError):
        annotator.annotate("prompt")
    assert delays == []


def test_annotator_exhausts_retries_and_raises():
    pytest.importorskip("botocore")
    from botocore.exceptions import ClientError

    throttle = ClientError({"Error": {"Code": "ServiceUnavailableException", "Message": "x"}}, "Converse")

    def respond(_text):
        raise throttle

    client = StubClient(respond)
    delays: list[float] = []
    annotator = ac.BedrockAnnotator(client=client, model="m", max_tokens=100, max_retries=2, sleep_fn=delays.append)

    with pytest.raises(ClientError):
        annotator.annotate("prompt")
    assert len(client.calls) == 3  # initial attempt + 2 retries
    assert delays == [5.0, 10.0]


def test_annotator_backoff_delay_is_capped_at_60s():
    pytest.importorskip("botocore")
    from botocore.exceptions import ClientError

    throttle = ClientError({"Error": {"Code": "ThrottlingException", "Message": "x"}}, "Converse")

    def respond(_text):
        raise throttle

    client = StubClient(respond)
    delays: list[float] = []
    annotator = ac.BedrockAnnotator(client=client, model="m", max_tokens=100, max_retries=5, sleep_fn=delays.append)

    with pytest.raises(ClientError):
        annotator.annotate("prompt")
    assert delays == [5.0, 10.0, 20.0, 40.0, 60.0]  # 80 would be uncapped; 60 is the cap


def test_annotator_retries_connection_errors():
    pytest.importorskip("botocore")
    from botocore.exceptions import EndpointConnectionError

    err = EndpointConnectionError(endpoint_url="https://example.com")
    calls = {"n": 0}

    def respond(_text):
        calls["n"] += 1
        if calls["n"] == 1:
            raise err
        return "ok"

    client = StubClient(respond)
    delays: list[float] = []
    annotator = ac.BedrockAnnotator(client=client, model="m", max_tokens=100, max_retries=3, sleep_fn=delays.append)

    assert annotator.annotate("prompt") == "ok"
    assert delays == [5.0]


class MultiBlockStubClient:
    """Converse stub returning a caller-supplied content-block list verbatim,
    for testing reply shapes StubClient can't produce (reasoning models)."""

    def __init__(self, blocks) -> None:
        self._blocks = blocks

    def converse(self, *, modelId, system, messages, inferenceConfig):  # noqa: N803
        return {"output": {"message": {"content": self._blocks}}}


def test_annotator_skips_reasoning_blocks_and_joins_text_blocks():
    """Reasoning models (DeepSeek-R1) prepend a reasoningContent block; the
    annotation is the concatenation of the text blocks only."""
    client = MultiBlockStubClient(
        [
            {"reasoningContent": {"reasoningText": {"text": "scratchwork the caller must never see"}}},
            {"text": "the actual "},
            {"text": "rationale"},
        ]
    )
    annotator = ac.BedrockAnnotator(client=client, model="m", max_tokens=100, max_retries=0)
    assert annotator.annotate("prompt") == "the actual rationale"


def test_annotator_returns_empty_when_reply_has_no_text_block():
    """A reasoning model that hits maxTokens mid-think yields only a
    reasoningContent block -- annotate() returns "" (QC rejects downstream)
    rather than raising."""
    client = MultiBlockStubClient(
        [{"reasoningContent": {"reasoningText": {"text": "never finished thinking"}}}]
    )
    annotator = ac.BedrockAnnotator(client=client, model="m", max_tokens=100, max_retries=0)
    assert annotator.annotate("prompt") == ""


# ---------------------------------------------------------------------------
# _run_annotation: abort-on-fatal-error, partial-progress reporting
# ---------------------------------------------------------------------------


def test_run_annotation_aborts_on_fatal_error_and_reports_partial_progress(tmp_path):
    rows = [_row(f"T{i}", 0, "omega") for i in range(6)]
    calls = {"n": 0}
    lock = threading.Lock()

    def respond(_text):
        with lock:
            calls["n"] += 1
            n = calls["n"]
        if n == 3:
            raise RuntimeError("boom")
        return _GOOD_RATIONALE

    client = StubClient(respond)
    annotator = ac.BedrockAnnotator(client=client, model="m", max_tokens=100, max_retries=0)

    n_completed, n_emitted, n_skipped, drop_reasons, kept, abort_error = ac._run_annotation(
        rows,
        annotator=annotator,
        index=HoldoutIndex(),
        style="think",
        max_rationale_chars=2500,
        workers=1,  # single worker: deterministic FIFO completion order
        out_path=tmp_path / "out.jsonl",
        done=set(),
    )

    assert abort_error is not None
    assert "boom" in abort_error
    # Only the rows completed strictly before the fatal one were processed.
    assert n_completed == 2
    assert n_emitted == 2
    assert len(kept) == 2


# ---------------------------------------------------------------------------
# main(): end-to-end with a stubbed client + an empty decontam index
# ---------------------------------------------------------------------------


def test_main_missing_dataset_skips_gracefully(tmp_path, capsys):
    missing = tmp_path / "does_not_exist.jsonl"
    rc = ac.main(["--dataset", str(missing), "--style", "think", "--out", str(tmp_path / "out.jsonl")])
    assert rc == 0
    assert "not found" in capsys.readouterr().err
    assert not (tmp_path / "out.jsonl").exists()


def test_main_judge_sample_not_implemented(capsys):
    rc = ac.main(["--style", "think", "--judge-sample", "50"])
    assert rc == 1
    assert "not implemented in round 1" in capsys.readouterr().err


def test_main_dry_run_constructs_no_client(tmp_path, monkeypatch, capsys, dataset_file):
    dataset_path, _rows = dataset_file

    def _boom(region):
        raise AssertionError("build_client must not be called in --dry-run")

    monkeypatch.setattr(ac, "build_client", _boom)

    rc = ac.main(
        [
            "--dataset", str(dataset_path), "--style", "think", "--limit", "5",
            "--out", str(tmp_path / "unused.jsonl"), "--dry-run",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "no AWS client constructed" in out
    assert "SAMPLE composed target" in out
    assert not (tmp_path / "unused.jsonl").exists()


def test_main_aborts_before_client_construction_on_preflight_leak(tmp_path, monkeypatch, dataset_file):
    from scripts.build_lean_synth_sft import _facets_from_rendered

    dataset_path, rows = dataset_file
    leaked_row = rows[0]
    states, tactics, _pairs = _facets_from_rendered(leaked_row["user"], leaked_row["assistant"])

    def _leaking_build(cls, *_a, **_kw):
        idx = cls()
        idx.pairs[(normalize_text(states[0]), normalize_text(tactics[0]))] = "Eval.leakedThm"
        return idx

    monkeypatch.setattr(HoldoutIndex, "build", classmethod(_leaking_build))

    def _boom(region):
        raise AssertionError("build_client must not be called when the preflight check fails")

    monkeypatch.setattr(ac, "build_client", _boom)

    with pytest.raises(SystemExit):
        ac.main(
            ["--dataset", str(dataset_path), "--style", "think", "--out", str(tmp_path / "out.jsonl"), "--limit", "0"]
        )


def test_main_resume_skips_done_keys(tmp_path, monkeypatch, empty_index, dataset_file):
    dataset_path, rows = dataset_file
    # Named per the 'cot_stepk1_<style>_<tag>' coordination convention (not
    # an arbitrary "out.jsonl") -- main() now also writes a paired
    # bare-control sibling derived from this name (see
    # _sibling_bare_path), which requires the style token to appear as a
    # '_'-delimited stem segment.
    out_path = tmp_path / "cot_stepk1_think_8k.jsonl"

    already_done = {
        "system": "SYS",
        "user": rows[0]["user"],
        "assistant": ac.compose_target("think", _GOOD_RATIONALE, rows[0]["assistant"]),
        "meta": {**rows[0]["meta"], "cot_style": "think"},
    }
    _write_jsonl(out_path, [already_done])

    stub = StubClient(lambda _t: _GOOD_RATIONALE)
    monkeypatch.setattr(ac, "build_client", lambda region: stub)

    rc = ac.main(
        ["--dataset", str(dataset_path), "--style", "think", "--out", str(out_path), "--limit", "0", "--workers", "2"]
    )
    assert rc == 0

    # Only the 3 not-already-done rows were sent to the annotator.
    assert len(stub.calls) == 3
    assert not any("alpha_lemma_one" in c for c in stub.calls)

    out_lines = out_path.read_text().splitlines()
    assert len(out_lines) == 4  # 1 pre-existing + 3 newly annotated

    manifest = json.loads(out_path.with_name(out_path.stem + ".manifest.json").read_text())
    assert manifest["stats"]["already_done_skipped"] == 1
    assert manifest["stats"]["emitted_this_run"] == 3
    assert manifest["stats"]["total_rows_in_out"] == 4

    # Fix 1: the bare-control sibling reflects the UNION after a resumed
    # run -- all 4 keys now in --out (the 1 pre-existing + 3 newly
    # annotated this run), not just this invocation's 3.
    assert manifest["bare_sibling"]["path"] == "cot_stepk1_bare_8k.jsonl"
    assert manifest["bare_sibling"]["rows"] == 4
    sibling_path = out_path.with_name("cot_stepk1_bare_8k.jsonl")
    sibling_rows = [json.loads(line) for line in sibling_path.read_text().splitlines()]
    assert len(sibling_rows) == 4
    assert {r["meta"]["full_name"] for r in sibling_rows} == {r["meta"]["full_name"] for r in rows}
    # Every sibling row is the ORIGINAL bare row -- byte-identical assistant
    # (the pre-annotation tail), no cot_style meta key.
    by_name = {r["meta"]["full_name"]: r for r in rows}
    for sib in sibling_rows:
        original = by_name[sib["meta"]["full_name"]]
        assert sib["assistant"] == original["assistant"]
        assert sib["user"] == original["user"]
        assert "cot_style" not in sib["meta"]


def test_main_writes_manifest_and_qc_report_with_expected_keys(tmp_path, monkeypatch, empty_index, dataset_file):
    dataset_path, _rows = dataset_file
    out_path = tmp_path / "cot_stepk1_fenced_full.jsonl"

    stub = StubClient(lambda _t: _GOOD_RATIONALE)
    monkeypatch.setattr(ac, "build_client", lambda region: stub)

    rc = ac.main(["--dataset", str(dataset_path), "--style", "fenced", "--out", str(out_path), "--limit", "0"])
    assert rc == 0

    manifest = json.loads(out_path.with_name(out_path.stem + ".manifest.json").read_text())
    assert manifest["config"]["style"] == "fenced"
    assert manifest["config"]["prompt_template_sha256"] == ac._TEMPLATE_SHA256
    assert manifest["stats"]["emitted_this_run"] == 4
    assert manifest["stats"]["dropped_this_run_total"] == 0
    assert manifest["stats"]["total_rows_in_out"] == 4
    assert manifest["decontamination"]["preflight_bare_facet_rescan"] == "passed"
    assert manifest["aborted"] is False
    assert manifest["abort_error"] is None
    assert manifest["bare_sibling"] == {"path": "cot_stepk1_bare_full.jsonl", "rows": 4}

    qc = json.loads(out_path.with_name(out_path.stem + ".qc.json").read_text())
    assert qc["kept_this_run"] == 4
    assert set(qc["rationale_length_chars"]) == {"min", "p10", "p25", "p50", "p75", "p90", "p99", "max", "mean"}
    assert qc["distinct_5gram_ratio"]["sample_size"] == 4
    assert qc["grounding_rate"]["total"] == 4
    assert "drop_histogram" in qc

    # Every emitted row round-trips its (bare) tail through extract_tactic_block.
    out_rows = [json.loads(line) for line in out_path.read_text().splitlines()]
    for row in out_rows:
        assert extract_tactic_block(row["assistant"]) != ""


def test_main_records_drop_reasons_in_manifest_and_qc_report(tmp_path, monkeypatch, empty_index):
    # One row whose annotator response is empty (dropped) and one clean row.
    rows = [_row("Empty.thm", 0, "omega"), _row("Good.thm", 0, "rfl")]
    dataset_path = tmp_path / "src.jsonl"
    _write_jsonl(dataset_path, rows)
    out_path = tmp_path / "cot_stepk1_think_2.jsonl"

    def respond(text):
        return "" if "Empty.thm" in text else _GOOD_RATIONALE

    stub = StubClient(respond)
    monkeypatch.setattr(ac, "build_client", lambda region: stub)

    rc = ac.main(["--dataset", str(dataset_path), "--style", "think", "--out", str(out_path), "--limit", "0"])
    assert rc == 0

    manifest = json.loads(out_path.with_name(out_path.stem + ".manifest.json").read_text())
    assert manifest["stats"]["emitted_this_run"] == 1
    assert manifest["stats"]["dropped_this_run"] == {"empty_rationale": 1}

    qc = json.loads(out_path.with_name(out_path.stem + ".qc.json").read_text())
    assert qc["drop_histogram"] == {"empty_rationale": 1}
    assert qc["kept_this_run"] == 1

    # The dropped row (Empty.thm, empty rationale) never made it into --out,
    # so it must NOT appear in the bare sibling either -- the pairing is
    # exact against what the CoT arm actually ended up with, not the full
    # candidate set.
    assert manifest["bare_sibling"] == {"path": "cot_stepk1_bare_2.jsonl", "rows": 1}
    sibling_rows = [
        json.loads(line) for line in out_path.with_name("cot_stepk1_bare_2.jsonl").read_text().splitlines()
    ]
    assert [r["meta"]["full_name"] for r in sibling_rows] == ["Good.thm"]
    assert sibling_rows[0]["assistant"] == "rfl"  # bare -- byte-identical to the source row's tail
