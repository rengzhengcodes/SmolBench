"""Test the determinism probes' pure comparison and verdict logic, offline.

The four probes (`scripts/hardware_equivalence_probe.py`, `hinge_probe.py`,
`tp4_hinge_probe.py`, `tp8_hinge_probe.py`, `moe_tp8_probe.py`) cannot run
end-to-end without provisioning an 8-GPU box. So this file pins the logic
that decides what a run means. That logic covers the empty-row rule that
sets the identity denominator, and the per-arm sensitivity control that
decides whether a k/k result is a HOLD or an UNMEASURED. It also covers
the throughput fallback flag and the row serialization every committed
SHA table was recorded against.

Three of these guard defects that already put a wrong number in a published
result (2026-08-23 repair):

* The empty-row rule excluded a row when either pass was empty, so a real
  wire-level divergence (P1 = 83,661 chars vs P2 = a discarded
  106,545-char reasoning-only cap-hit) was published as "excluded (empty)"
  and the positive control was reported 0/3 instead of 0/4.
* Nothing tied a HOLD verdict to a control that had actually fired, so a
  tp=8 dense HOLD was banked alongside a 0-row control.
* `fallback_rate_used` was written into a dict that the very next
  statement reassigned, so the flag never survived into any report.

``scripts/`` is not an importable package, so each probe loads by path
(mirroring ``tests/test_flip_probe.py`` and ``tests/test_delivery_probe.py``).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str, filename: str):
    """Load a `scripts/*.py` probe by path, without leaking its sys.path edit.

    `tp4_hinge_probe`, `tp8_hinge_probe`, and `moe_tp8_probe` each run
    ``sys.path.insert(0, "/workspace/SmolBench")`` at module scope. Inside
    the repo that has no effect, but it is still an import-time mutation of
    global interpreter state. It outlives this module and reorders
    `sys.path` for every test that runs afterwards. It has a concrete
    false-green mode. If you run this suite against a copy of the tree,
    for example a `git archive HEAD` baseline used to prove a test fails
    pre-change, the live `/workspace/SmolBench` ends up ahead of the
    copy. So `import smolbench...` in any later test silently resolves to
    the live, already-fixed package, and the baseline run passes.
    Measured: the same baseline copy reported 3 failures with this file
    absent, and 0 with it collected first.

    `sys.path` is therefore snapshotted and restored around the exec. By
    then the probe modules are fully loaded, and they resolve `smolbench`
    through the entry pytest already provides for the tree under test.
    """
    saved = list(sys.path)
    try:
        spec = importlib.util.spec_from_file_location(name, _SCRIPTS / filename)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path[:] = saved


hwprobe = _load("hardware_equivalence_probe", "hardware_equivalence_probe.py")
hinge = _load("hinge_probe", "hinge_probe.py")
tp4 = _load("tp4_hinge_probe", "tp4_hinge_probe.py")
tp8 = _load("tp8_hinge_probe", "tp8_hinge_probe.py")
moe = _load("moe_tp8_probe", "moe_tp8_probe.py")


# ---------------------------------------------------------------------------
# D6 -- the empty-row rule: exclude only when both passes are empty
# ---------------------------------------------------------------------------
# A row is "empty" at length <= 1, because the stored text is
# `reasoning + "\x00" + content`: a row with neither channel is exactly the
# one separator byte. If either side was excluded, a one-sided empty row
# (a pass that delivered 83k characters against a pass that delivered
# nothing) would silently vanish from the denominator. That is the single
# most divergent outcome possible, and it was being scored as "unmeasured".


#: One fixture exercising all four cases at once:
#:   p_same       both non-empty and identical  -> identical, in n
#:   p_diff       both non-empty and different  -> divergent,  in n
#:   p_one_sided  A empty, B a real generation  -> divergent,  in n   (the fix)
#:   p_both_empty neither pass delivered        -> excluded,   not in n
_A = {"p_same": "AAA", "p_diff": "BBB", "p_one_sided": "\x00", "p_both_empty": ""}
_B = {"p_same": "AAA", "p_diff": "CCC", "p_one_sided": "a real 83k generation",
      "p_both_empty": "\x00"}


@pytest.mark.parametrize("mod", [tp4, tp8], ids=["tp4_copy", "tp8_copy"])
def test_guarded_compare_excludes_only_both_empty_rows(mod):
    """Both copies of the rule must agree; a fix to only one is still a bug.

    tp4 and tp8 carry independent copies of ``guarded_compare``, and
    ``moe_tp8_probe`` reuses tp8's. So parametrizing over both is what
    stops a half-applied fix from passing.
    """
    out = mod.guarded_compare(hwprobe, _A, _B)

    # The denominator now contains the one-sided row: 3, not 2.
    assert out["n"] == 3
    assert out["identical"] == 1
    assert out["n_before_exclusion"] == 4

    # Only the row where neither pass delivered is excluded.
    assert out["excluded_empty_rows"] == ["p_both_empty"]
    assert out["one_sided_empty_rows"] == ["p_one_sided"]

    # The one-sided row is reported as a divergence, not merely counted.
    assert {d["prompt"] for d in out["diffs"]} == {"p_diff", "p_one_sided"}


@pytest.mark.parametrize("mod", [tp4, tp8], ids=["tp4_copy", "tp8_copy"])
def test_guarded_compare_one_sided_row_can_never_be_identical(mod):
    """A one-sided empty row entering n must always lower the rate.

    This pins the property the rule rests on: one side <= 1 char and the
    other side longer cannot be byte-equal. So admitting the row to the
    denominator can only ever reduce `identical/n`; it can never
    manufacture agreement.
    """
    a = {"only": "\x00"}
    b = {"only": "x" * 500}
    out = mod.guarded_compare(hwprobe, a, b)
    assert out["n"] == 1
    assert out["identical"] == 0
    assert out["rate"] == 0.0
    assert out["one_sided_empty_rows"] == ["only"]
    assert out["excluded_empty_rows"] == []


@pytest.mark.parametrize("mod", [tp4, tp8], ids=["tp4_copy", "tp8_copy"])
def test_guarded_compare_all_clean_rows_is_unchanged(mod):
    """The common case must not move: no empties, nothing excluded or flagged."""
    a = {"x": "same", "y": "left"}
    b = {"x": "same", "y": "right"}
    out = mod.guarded_compare(hwprobe, a, b)
    assert (out["n"], out["identical"]) == (2, 1)
    assert out["excluded_empty_rows"] == []
    assert out["one_sided_empty_rows"] == []


# ---------------------------------------------------------------------------
# D6 -- row serialization + per-row token metadata
# ---------------------------------------------------------------------------


class _FakeChatResult(SimpleNamespace):
    pass


def _fake_ec2(responses, monkeypatch, allow_query=False):
    """Point the probes' `ec2` module at canned ChatResults.

    ``_CLIENT`` is a frozen dataclass, so this function replaces it
    wholesale instead of mutating it. ``ec2.complete`` is patched
    separately, because it is a bound method captured at import time.

    ``allow_query`` decides whether ``ec2.query`` is a working narrowing
    wrapper over the same queue, or a tripwire. The comparison passes must
    go through ``complete()``: ``query()`` discards the finish reason and
    token counters that D6 exists to record. So those tests leave it a
    tripwire, and get a diagnostic failure instead of a confusing one. The
    throughput warm-up probe discards its output entirely and has no such
    requirement, so its tests allow either call and pin only the behavior
    actually specified.
    """
    from smolbench.evals import ec2

    calls = []

    def fake_complete(prompt, model, seed, context_length=0, extra_args=None,
                      request_timeout=None, **kw):
        calls.append({"prompt": prompt, "model": model, "seed": seed,
                      "context_length": context_length, "extra_args": extra_args})
        return responses.pop(0)

    def fake_query(prompt, model, seed, context_length=0, **kw):
        rsp = fake_complete(prompt, model, seed, context_length=context_length, **kw)
        return rsp.content, rsp.reasoning

    def _refuse_query(*a, **kw):
        raise AssertionError(
            "the probe COMPARISON passes must call ec2.complete(): query() "
            "narrows the ChatResult to (content, reasoning) and DISCARDS "
            "finish_reason and the token counters, which is the metadata D6 "
            "exists to record."
        )

    monkeypatch.setattr(ec2, "_CLIENT", SimpleNamespace(context_length=lambda m: 4096))
    monkeypatch.setattr(ec2, "complete", fake_complete)
    monkeypatch.setattr(ec2, "query", fake_query if allow_query else _refuse_query)
    return ec2, calls


def _result(content="", reasoning=None, finish_reason="stop",
            completion_tokens=0, prompt_tokens=0):
    return _FakeChatResult(content=content, reasoning=reasoning,
                           finish_reason=finish_reason,
                           completion_tokens=completion_tokens,
                           prompt_tokens=prompt_tokens,
                           cached_prompt_tokens=0, total_tokens=None, model="m")


def test_run_pass_row_serialization_is_byte_identical(monkeypatch):
    """`reasoning + "\\x00" + content`, unchanged.

    Every committed `sha_table_P1/P2` and every `cross_tp` / `_vs_head`
    comparison is recorded against this exact byte layout. A change in
    separator, field order, or None handling would read downstream as a
    kernel change, not a serialization change.
    """
    responses = [
        _result(content="C", reasoning="R"),
        _result(content="", reasoning=None),
        _result(content="", reasoning="R-only"),
    ]
    _fake_ec2(responses, monkeypatch)
    out = hwprobe.run_pass("m", [("a", "pa"), ("b", "pb"), ("c", "pc")], "L")
    assert out["a"] == "R\x00C"
    assert out["b"] == "\x00"          # the empty-row signature: ONE byte
    assert out["c"] == "R-only\x00"


def test_run_pass_records_finish_reason_and_completion_tokens(monkeypatch):
    """D6: the metadata that identifies a cap-hit must survive into the report.

    `finish_reason == "length"` with a large `completion_tokens` is what
    distinguishes "the model stopped" from "the model ran out of budget in
    the reasoning channel." This is the population the empty-row bug was
    hiding.
    """
    responses = [_result(content="", reasoning="R" * 40,
                         finish_reason="length", completion_tokens=32768,
                         prompt_tokens=11)]
    _fake_ec2(responses, monkeypatch)
    meta: dict = {}
    out = hwprobe.run_pass("m", [("a", "pa")], "L", meta=meta)
    assert meta["a"]["finish_reason"] == "length"
    assert meta["a"]["completion_tokens"] == 32768
    assert meta["a"]["prompt_tokens"] == 11
    assert meta["a"]["chars"] == len(out["a"])


def test_run_pass_meta_is_optional(monkeypatch):
    """Without `meta`, the historical Dict[str, str] return shape must hold."""
    _fake_ec2([_result(content="C", reasoning="R")], monkeypatch)
    out = hwprobe.run_pass("m", [("a", "pa")], "L")
    assert out == {"a": "R\x00C"}
    assert all(isinstance(v, str) for v in out.values())



# ---------------------------------------------------------------------------
# D5 -- the throughput-probe fallback flag must survive
# ---------------------------------------------------------------------------


def test_throughput_probe_fallback_flag_survives_the_write(monkeypatch):
    """`fallback_rate_used` and the measurement must coexist in one dict.

    The flag was written with `setdefault(...)[...] = rate` and then
    destroyed by a full reassignment on the very next statement. So no
    report ever recorded that a hardcoded rate had been substituted for a
    measured one. That is exactly the provenance that k, chosen from that
    rate, depends on.
    """
    _fake_ec2([_result(content="", reasoning=None)], monkeypatch, allow_query=True)
    from smolbench.evals import ec2

    entry: dict = {}
    rate = moe.throughput_probe(ec2, hwprobe, "nemotron-3-super-120b-a12b",
                                "prompt", entry)
    tp = entry["throughput_probe"]
    assert tp["fallback_rate_used"] == rate          # the flag survived
    assert rate == 9.1                               # the 120b fallback
    assert "approx_tok_s" in tp                      # the measurement is still there
    assert tp["chars"] == 0


def test_throughput_probe_measured_rate_sets_no_fallback_flag(monkeypatch):
    """A real measurement must not claim a fallback was used."""
    _fake_ec2([_result(content="x" * 4000, reasoning=None)], monkeypatch,
              allow_query=True)
    from smolbench.evals import ec2

    entry: dict = {}
    rate = moe.throughput_probe(ec2, hwprobe, "ministral-3-3b", "prompt", entry)
    assert rate > 0
    assert "fallback_rate_used" not in entry["throughput_probe"]
    assert entry["throughput_probe"]["chars"] == 4000


# ---------------------------------------------------------------------------
# D5 -- a config claim may not rest on an empty serve-log capture
# ---------------------------------------------------------------------------
# The tp=8 dense arm banked a "custom all-reduce ACTIVE" claim in a commit
# title on a capture that was in fact empty (the pre-fix `/status` call was
# unauthenticated and returned HTTP 401, so the field was empty by
# construction, not because the box was quiet). The byte result stays
# reportable; the mechanism claim must be marked UNMEASURED.


def test_mechanism_evidence_present_when_engine_config_parsed():
    sl = {"vllm_log_chars": 14000,
          "engine_config_parsed": {"tensor_parallel_size": "8",
                                   "disable_custom_all_reduce": "False"}}
    assert hwprobe.mechanism_evidence(sl) == "engine_config"


@pytest.mark.parametrize("sl", [
    None,
    {},
    {"vllm_log_chars": 0},
    {"error": "HTTPError: 401"},
    # Log captured, but nothing parsed out of it: the config claim has no basis.
    {"vllm_log_chars": 14000, "engine_config_parsed": {}},
    {"vllm_log_chars": 14000},
], ids=["none", "empty", "zero-chars", "http-error", "chars-but-no-parse", "no-parse-key"])
def test_mechanism_evidence_unmeasured_without_a_parsed_config(sl):
    assert hwprobe.mechanism_evidence(sl) == "UNMEASURED"


# ---------------------------------------------------------------------------
# D5 -- the tp gate must read the container, not the driver's own readback
# ---------------------------------------------------------------------------
# tp4's gate asserted `state["last_serve"]["tp"]`, which is the value the
# driver itself computed and posted. It can only ever confirm the driver
# agrees with itself. If tp=4 were certified from a tp=1 container, that
# would be exactly the failure the gate exists to prevent, and the
# payload readback could not detect it. The gate now reads vLLM's own
# engine-config line.


def test_tp_gate_passes_on_matching_engine_config():
    out = tp8.tp_gate({"vllm_log_chars": 9000,
                       "engine_config_parsed": {"tensor_parallel_size": "4"}},
                      expect_tp=4, payload_tp=4)
    assert out["gate_basis"] == "engine_config"
    assert out["engine_tp"] == 4
    assert out["payload_tp"] == 4
    assert out["payload_agrees"] is True


def test_tp_gate_rejects_a_container_serving_a_different_tp():
    """The payload says 4, the container says 1: this must abort the arm."""
    with pytest.raises(RuntimeError) as exc:
        tp8.tp_gate({"vllm_log_chars": 9000,
                     "engine_config_parsed": {"tensor_parallel_size": "1"}},
                    expect_tp=4, payload_tp=4)
    assert "1" in str(exc.value) and "4" in str(exc.value)


@pytest.mark.parametrize("sl", [
    None,
    {},
    {"vllm_log_chars": 0},
    {"vllm_log_chars": 9000, "engine_config_parsed": {}},
    {"vllm_log_chars": 9000, "engine_config_parsed": {"enforce_eager": "True"}},
], ids=["none", "empty", "zero-chars", "nothing-parsed", "no-tp-key"])
def test_tp_gate_aborts_rather_than_falling_back_to_the_payload(sl):
    """An unparseable log must abort, never silently re-gate on the payload.

    A silent fallback would restore exactly the blindness this change
    removes, while leaving a `gate_basis` field that claims the container
    was checked.
    """
    with pytest.raises(RuntimeError):
        tp8.tp_gate(sl, expect_tp=4, payload_tp=4)


def test_tp_gate_rejects_payload_disagreeing_with_the_container():
    """Two records of the same fact that disagree: bank neither."""
    with pytest.raises(RuntimeError):
        tp8.tp_gate({"vllm_log_chars": 9000,
                     "engine_config_parsed": {"tensor_parallel_size": "8"}},
                    expect_tp=8, payload_tp=4)


# ---------------------------------------------------------------------------
# D5 -- n_prompts_compared must be written AFTER P2 lands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mod", [tp8, moe], ids=["tp8", "moe"])
def test_n_prompts_compared_is_assigned_after_the_p2_pass(mod):
    """A source-order pin, because this defect is purely one of ordering.

    `n_prompts_compared` was set to `len(p2_prompts)` before P2 ran. P2 can
    stop early on its wall-clock deadline, so a truncated pass left a stale
    k in the report that overstated how many rows were actually compared,
    the number a k/k verdict is quoted against. There is no pure function
    to test here. The fix is that the assignment happens after the pass
    returns, so that is what this test pins.
    """
    import inspect
    import re

    src = inspect.getsource(mod.main)
    m = re.search(r'entry\["n_prompts_compared"\]\s*=', src)
    assert m, "the n_prompts_compared assignment vanished"
    assign = m.start()
    p2_call = re.search(r'\bp2 = ', src).start()
    assert assign > p2_call, (
        "n_prompts_compared is still assigned before the P2 pass runs; a "
        "deadline-truncated P2 would leave a stale k in the report"
    )


# ---------------------------------------------------------------------------
# D8 -- the per-arm sensitivity control
# ---------------------------------------------------------------------------
# Nothing tied a HOLD verdict to a control that had actually fired. The rule
# was "k/k identical => HOLDS," full stop, and the tp=8 dense HOLD was
# banked alongside a stock control that collected zero rows. A same-model
# stock control cannot fix this in general: nemotron-3-nano-4b's own tp=1
# STOCK arm was 8/8 identical (prefix-cache replay, 15,258 cache queries),
# so "stock must diverge" can never gate that model. Each arm therefore
# carries its own in-process control: one extra row from a deterministically
# perturbed copy of the arm's first prompt, which must come back different.


def test_sensitivity_verdict_differing_output_is_sensitive():
    sens = hwprobe.evaluate_sensitivity(perturbed="totally different text",
                                        base="a real 83k generation")
    assert sens["differs"] is True
    assert hwprobe.control_status(sens) == "SENSITIVE"


def test_sensitivity_verdict_identical_output_is_blind():
    """Same bytes out for a perturbed prompt in: the probe is not measuring."""
    sens = hwprobe.evaluate_sensitivity(perturbed="identical", base="identical")
    assert sens["differs"] is False
    assert hwprobe.control_status(sens) == "BLIND"


def test_sensitivity_truncated_prefix_is_blind_not_sensitive():
    """The discriminating case: a perturbed row that is a strict prefix of base.

    A plain `perturbed != base` test calls this SENSITIVE purely because
    the lengths differ. That makes the whole control vacuous whenever the
    sensitivity row is generated under a smaller token cap than the passes
    it controls. Sensitivity means the bytes diverged, not that one
    generation stopped earlier.
    """
    base = "the model said this and then a great deal more"
    sens = hwprobe.evaluate_sensitivity(perturbed="the model said this", base=base)
    assert sens["differs"] is False
    assert sens["common_prefix_chars"] == len("the model said this")
    assert hwprobe.control_status(sens) == "BLIND"


def test_sensitivity_divergence_inside_the_common_span_is_sensitive():
    """Shorter than base, but it diverged before it stopped -> SENSITIVE."""
    base = "the model said this and then a great deal more"
    sens = hwprobe.evaluate_sensitivity(perturbed="the model said THAT", base=base)
    assert sens["differs"] is True
    assert sens["common_prefix_chars"] == len("the model said ")


def test_sensitivity_empty_perturbed_row_is_blind():
    """An empty perturbed row is a delivery fault, never proof of sensitivity."""
    sens = hwprobe.evaluate_sensitivity(perturbed="\x00", base="a real generation")
    assert sens["differs"] is False
    assert hwprobe.control_status(sens) == "BLIND"


def test_sensitivity_empty_base_row_is_blind():
    """Nothing to compare against is not evidence either."""
    sens = hwprobe.evaluate_sensitivity(perturbed="a real generation", base="\x00")
    assert sens["differs"] is False
    assert hwprobe.control_status(sens) == "BLIND"


def test_sensitivity_missing_row_is_blind():
    """No control row at all is no evidence. It must not default to SENSITIVE."""
    assert hwprobe.control_status(None) == "BLIND"
    assert hwprobe.control_status({}) == "BLIND"
    assert hwprobe.control_status({"error": "RuntimeError: boom"}) == "BLIND"


def test_run_sensitivity_row_perturbs_the_prompt_deterministically(monkeypatch):
    """The perturbation is a fixed prefix on the arm's own first prompt.

    This is deterministic by construction: no randomness and no timestamp.
    So the control row is reproducible across arms, runs, and boxes, and
    two arms on the same model control with the same stimulus.
    """
    _, calls = _fake_ec2([_result(content="a quite different output"),
                          _result(content="a quite different output")], monkeypatch)
    from smolbench.evals import ec2

    row = hwprobe.run_sensitivity_row(ec2, "m", "pid-1", "BASE PROMPT",
                                      "\x00the unperturbed P1 row 1 output")
    again = hwprobe.run_sensitivity_row(ec2, "m", "pid-1", "BASE PROMPT",
                                        "\x00the unperturbed P1 row 1 output")

    assert calls[0]["prompt"] == hwprobe.SENSITIVITY_PREFIX + "BASE PROMPT"
    assert calls[0]["prompt"] == calls[1]["prompt"]      # deterministic
    assert calls[0]["prompt"] != "BASE PROMPT"           # actually perturbed
    assert row["prompt_id"] == "pid-1"
    assert row["perturbation"] == hwprobe.SENSITIVITY_PREFIX
    assert row["differs"] is True
    assert len(row["sha12"]) == 12
    assert row["chars"] == len("\x00a quite different output")
    assert row == again


def test_run_sensitivity_row_uses_the_studys_seed_and_temperature(monkeypatch):
    """The control row must be generated under the arm's own sampling regime."""
    _, calls = _fake_ec2([_result(content="different")], monkeypatch)
    from smolbench.evals import ec2

    hwprobe.run_sensitivity_row(ec2, "m", "pid-1", "BASE", "\x00base out")
    assert calls[0]["seed"] == hwprobe.SEED
    assert calls[0]["extra_args"]["temperature"] == hwprobe.TEMPERATURE


def test_run_sensitivity_row_identical_output_reports_blind(monkeypatch):
    """A model that ignores the perturbation must be caught, not excused."""
    base = "\x00the unperturbed output"
    _fake_ec2([_result(content="the unperturbed output")], monkeypatch)
    from smolbench.evals import ec2

    row = hwprobe.run_sensitivity_row(ec2, "m", "pid-1", "BASE", base)
    assert row["differs"] is False
    assert hwprobe.control_status(row) == "BLIND"


# ---------------------------------------------------------------------------
# D8 -- the verdict line: a HOLD must name the control that earned it
# ---------------------------------------------------------------------------


def test_verdict_line_blind_control_reports_unmeasured_never_hold():
    """k/k identical plus a BLIND control equals UNMEASURED. This is the whole gate."""
    line = hwprobe.verdict_line(arm="det", identical=8, n=8,
                                control_status="BLIND",
                                model="ministral-3-3b", instance_id="i-abc")
    assert "UNMEASURED" in line
    assert "HOLD" not in line


def test_verdict_line_sensitive_control_holds_and_names_its_scope():
    line = hwprobe.verdict_line(arm="det", identical=8, n=8,
                                control_status="SENSITIVE",
                                model="ministral-3-3b", instance_id="i-abc",
                                stock_control="0/4")
    assert "HOLDS" in line
    assert "UNMEASURED" not in line
    # D8.4: the control's scope is named inside the verdict string itself.
    assert "SENSITIVE" in line
    assert "ministral-3-3b" in line
    assert "i-abc" in line
    assert "0/4" in line


def test_verdict_line_names_an_absent_stock_control():
    """An unrun stock control must be visible in the verdict, not omitted."""
    line = hwprobe.verdict_line(arm="det", identical=8, n=8,
                                control_status="SENSITIVE",
                                model="m", instance_id="i-1", stock_control=None)
    assert "HOLDS" in line
    assert "absent" in line


def test_verdict_line_divergence_does_not_hold():
    line = hwprobe.verdict_line(arm="det", identical=7, n=8,
                                control_status="SENSITIVE",
                                model="m", instance_id="i-1")
    assert "HOLDS" not in line
    assert "7/8" in line


def test_verdict_line_zero_rows_is_unmeasured():
    """0/0 is not a HOLD: an arm that compared nothing certifies nothing.

    The tp=8 stock control recorded n=0 and was still summarized as a
    fired control. An arm that compared no rows must say so.
    """
    line = hwprobe.verdict_line(arm="det", identical=0, n=0,
                                control_status="SENSITIVE",
                                model="m", instance_id="i-1")
    assert "UNMEASURED" in line
    assert "HOLDS" not in line


def test_verdict_line_unmeasured_mechanism_evidence_is_named():
    """D5.1: the byte result stays reportable.

    But the config claim cannot ride on an empty serve-log capture. The
    word must appear in the verdict.
    """
    line = hwprobe.verdict_line(arm="B", identical=1, n=1,
                                control_status="SENSITIVE",
                                model="m", instance_id="i-1",
                                mechanism_evidence="UNMEASURED")
    assert "1/1" in line
    assert "UNMEASURED" in line


def test_verdict_line_measured_mechanism_evidence_adds_no_caveat():
    line = hwprobe.verdict_line(arm="B", identical=1, n=1,
                                control_status="SENSITIVE",
                                model="m", instance_id="i-1",
                                mechanism_evidence="engine_config")
    assert "HOLDS" in line
    assert "UNMEASURED" not in line


@pytest.mark.parametrize("mod,label", [(tp4, "tp4"), (tp8, "tp8"), (moe, "moe")])
def test_drivers_emit_a_verdict_line_and_a_sensitivity_row(mod, label):
    """Every probe driver must wire the control, not merely have it available.

    This is a source pin. The shared helpers existing while no driver
    calls them is exactly the shape of the defect being fixed: a control
    that is available but never gates anything.
    """
    import inspect

    src = inspect.getsource(mod.main)
    assert "run_sensitivity_row" in src, f"{label} never generates a sensitivity row"
    assert "control_status" in src, f"{label} never records a control status"
    assert "verdict_line" in src, f"{label} never emits a scoped verdict line"


@pytest.mark.parametrize("mod,label", [(tp4, "tp4"), (tp8, "tp8"), (moe, "moe")])
def test_sensitivity_row_is_kept_out_of_the_identity_denominator(mod, label):
    """The control row has no P2 twin and must never reach the sha table or gz.

    This is pinned as a source property. The sensitivity row is produced
    by `run_sensitivity_row` and stored under `entry["sensitivity_row"]`,
    never fed through `sha_table(...)`, the gz archive, or the compared
    pass dicts.
    """
    import inspect
    import re

    src = inspect.getsource(mod.main)
    for m in re.finditer(r"sha_table\(([^)]*)\)", src):
        assert "sensitivity" not in m.group(1)
    for m in re.finditer(r"guarded_compare\(([^)]*)\)", src):
        assert "sensitivity" not in m.group(1)

# ---------------------------------------------------------------------------
# D5.1 follow-up (2026-08-23) -- the config gate must be arm-agnostic
# ---------------------------------------------------------------------------
# The first pass wired `mechanism_evidence` into tp4 and moe only, because
# the directive named those two files. That left tp8, the arm of the
# motivating incident, ungated: a tp=8 dense arm banked a "custom
# all-reduce ACTIVE" claim in a commit title on a serve-log capture that
# was empty by construction (the pre-fix /status call was unauthenticated
# and returned HTTP 401). tp8 already captured the log; it simply never
# asked whether the capture supported a claim, and
# `entry.get("mechanism_evidence")` returned None, which verdict_line
# correctly reads as "append no caveat." The gate is arm-agnostic: every
# driver that can emit a config claim must compute it.


@pytest.mark.parametrize("mod,label", [(tp4, "tp4"), (tp8, "tp8"), (moe, "moe")])
def test_every_driver_gates_its_config_claim_on_the_serve_log(mod, label):
    """All three drivers must compute mechanism_evidence and pass it on.

    This is a symmetric census. Before this fix the counts were tp4
    computes:1 passes:2, moe computes:1 passes:2, but tp8 computes:0
    passes:1, with the lone `passes` hit being
    `entry.get("mechanism_evidence")`, which can only ever yield None
    there. An asymmetric census is the signature of a gate applied
    file-by-file instead of to the behavior.
    """
    import inspect

    src = inspect.getsource(mod.main)
    assert "mechanism_evidence(" in src, (
        f"{label} never COMPUTES mechanism_evidence, so a config claim in this "
        "driver can still rest on an empty serve-log capture")
    assert "mechanism_evidence=" in src, (
        f"{label} never PASSES mechanism_evidence to verdict_line, so the "
        "UNMEASURED caveat can never reach the verdict string")


@pytest.mark.parametrize("serve_log", [
    None,
    {},
    {"vllm_log_chars": 0},
    {"error": "HTTPError: 401 bad token"},
    {"vllm_log_chars": 14000, "engine_config_parsed": {}},
], ids=["none", "empty", "zero-chars", "http-401", "chars-but-no-parse"])
def test_empty_capture_forces_unmeasured_into_the_verdict_line(serve_log):
    """The end-to-end composition the drivers must perform, pinned directly.

    `mechanism_evidence(capture)` -> `verdict_line(..., mechanism_evidence=)`
    is the whole gate. A k/k arm still reports its byte result, but the
    word UNMEASURED must be present, so no config claim can be read off it.
    """
    evidence = hwprobe.mechanism_evidence(serve_log)
    assert evidence == "UNMEASURED"
    line = hwprobe.verdict_line(
        arm="det", identical=8, n=8, control_status="SENSITIVE",
        model="ministral-3-3b", instance_id="i-abc", mechanism_evidence=evidence)
    assert "8/8" in line          # the byte result stays reportable
    assert "UNMEASURED" in line   # the config claim does not


# ---------------------------------------------------------------------------
# D8 follow-up (2026-08-23) -- the sensitivity index must not be last-arm-wins
# ---------------------------------------------------------------------------
# The report-level index was keyed `f"{model}@{instance_id}"`, taken
# literally from the spec's "keyed by (model, instance_id)." But every
# driver runs several arms against the same model on the same box: tp4/tp8
# run det and stock, and moe runs B and C on the dense model and A/A2 on
# the MoE. So each arm's control row overwrote the previous one, and the
# top-level index retained only the last. Per-arm
# `entry["sensitivity_row"]` was always complete, so no verdict was ever
# wrong; the audit trail was.


def test_sensitivity_key_separates_arms_on_the_same_model_and_box():
    """Two arms with the same model and instance give two distinct index entries."""
    det = hwprobe.sensitivity_key("ministral-3-3b", "i-abc", "det")
    stock = hwprobe.sensitivity_key("ministral-3-3b", "i-abc", "stock")
    assert det != stock

    index = {}
    index[det] = {"differs": True, "sha12": "aaaaaaaaaaaa"}
    index[stock] = {"differs": False, "sha12": "bbbbbbbbbbbb"}
    assert len(index) == 2, "one arm clobbered the other in the report index"
    assert index[det]["differs"] is True
    assert index[stock]["differs"] is False


def test_sensitivity_key_still_names_model_instance_and_arm():
    """The key stays human-readable: all three identifiers are recoverable."""
    key = hwprobe.sensitivity_key("nemotron-3-super-120b-a12b", "i-047406b", "A2")
    assert "nemotron-3-super-120b-a12b" in key
    assert "i-047406b" in key
    assert "A2" in key


def test_sensitivity_key_distinguishes_boxes_and_models_too():
    """The original (model, instance) discrimination must not be lost."""
    base = hwprobe.sensitivity_key("m", "i-1", "det")
    assert base != hwprobe.sensitivity_key("m", "i-2", "det")   # other box
    assert base != hwprobe.sensitivity_key("n", "i-1", "det")   # other model


@pytest.mark.parametrize("mod,label", [(tp4, "tp4"), (tp8, "tp8"), (moe, "moe")])
def test_drivers_key_the_sensitivity_index_by_arm(mod, label):
    """Every driver must build the index key through the shared helper.

    This is pinned at source level, because the alternative, three
    hand-rolled f-strings, is exactly how the three copies drifted into a
    last-arm-wins key in the first place.
    """
    import inspect

    src = inspect.getsource(mod.main)
    assert "sensitivity_key(" in src, (
        f"{label} still hand-builds its sensitivity index key; arms on the "
        "same model+box will clobber each other")


# ---------------------------------------------------------------------------
# Import hygiene
# ---------------------------------------------------------------------------


def test_loading_the_probes_does_not_mutate_sys_path():
    """The probes' module-scope `sys.path.insert` must not leak into the session.

    See `_load`'s docstring: the leak makes a `git archive HEAD` baseline
    run resolve `smolbench` to the live tree, which turns a should-fail
    baseline proof into a false green.
    """
    before = list(sys.path)
    _load("moe_tp8_probe_hygiene_check", "moe_tp8_probe.py")
    assert sys.path == before
