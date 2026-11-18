"""``serve_model(capture=True)``, the ``/attn`` helpers and the lazily read plugin asset, offline.

Ported from the capture branch's provisioning tests and adapted to this branch, where every
spec already carries ``--enforce-eager`` (``DETERMINISM_ARGS``), so capture adds only the
un-chunked prefill ceiling and must never duplicate the eager flag.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

from smolbench.evals import payloads
from smolbench.evals.providers import ec2

_S5_STATE = {
    "instance_type": "g7.24xlarge", "region": "us-east-2", "availability_zone": "us-east-2c",
    "instance_id": "i-abc123", "public_ip": "203.0.113.10", "vllm_api_key": "vk-stub-secret",
    "control_token": "ct-stub-secret",
}
_CAPTURE_ENV = {
    "PYTHONPATH": "/root/.cache/huggingface/attn_plugin",
    "VLLM_PLUGINS": "smolbench_attn",
    "SMOLBENCH_ATTN_DIR": "/root/.cache/huggingface/attn",
    "SMOLBENCH_ATTN_MODEL": "ministral-3-14b",
    # Always set for a capture serve: one prefill of a long cell can outlast vLLM's default
    # 300 s bound on a model step, which kills the engine.
    "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS": "3600",
}
_DIST = "attn_plugin/smolbench_attn-0.1.dist-info"
def _capture_harness(monkeypatch, state):
    """Stub the agent round-trip and return the list of (method, path, payload) calls."""
    calls = []

    def fake_agent(state_arg, method, path, payload=None, timeout=120, connect_retries=40):
        calls.append((method, path, payload))
        if path == "/status":
            return {"healthy": True, "attn": {"running": False, "done": 3}}
        return {"ok": True}

    monkeypatch.setattr(ec2, "EC2_REQUIRE_GPU", "")
    monkeypatch.setattr(ec2, "_require_state", lambda: state)
    monkeypatch.setattr(ec2, "_load_state", lambda: dict(state))
    monkeypatch.setattr(ec2, "_agent", fake_agent)
    monkeypatch.setattr(ec2, "_wait_model_ready", lambda *a, **k: None)
    monkeypatch.setattr(ec2, "list_models", lambda: ["ministral-3-14b"])
    monkeypatch.setattr(ec2, "_save_state", lambda s: state.update(s))
    # serve_model imports the reader lazily from the payloads module, so patch it there.
    monkeypatch.setattr(payloads, "attention_capture_plugin_py", lambda: "PLUGIN SOURCE\n")
    return calls


def test_serve_model_capture_ships_the_plugin_and_the_eager_prefill_args(monkeypatch):
    """capture=True adds the un-chunked eager prefill args, the plugin env, and the package files."""
    state = dict(_S5_STATE)
    calls = _capture_harness(monkeypatch, state)
    with ec2.serve_model("ministral-3-14b", capture=True) as served:
        assert served == "ministral-3-14b"
    (payload,) = [p for _m, path, p in calls if path == "/serve"]

    spec_args = ec2.EC2_DEPLOY_SPECS["ministral-3-14b"]["vllm_args"]
    spec_before = copy.deepcopy(spec_args)
    assert payload["vllm_args"] == list(spec_args) + ["--max-num-batched-tokens", "131072"]
    assert payload["vllm_args"].count("--enforce-eager") == 1
    assert ec2.EC2_DEPLOY_SPECS["ministral-3-14b"]["vllm_args"] == spec_before
    assert payload["env"] == _CAPTURE_ENV
    assert sorted(payload["files"]) == [
        f"{_DIST}/METADATA", f"{_DIST}/entry_points.txt",
        "attn_plugin/smolbench_attn/__init__.py"]
    assert payload["files"]["attn_plugin/smolbench_attn/__init__.py"] == "PLUGIN SOURCE\n"
    assert payload["files"][f"{_DIST}/METADATA"] == (
        "Metadata-Version: 2.1\nName: smolbench-attn\nVersion: 0.1\n")
    assert payload["files"][f"{_DIST}/entry_points.txt"] == (
        "[vllm.general_plugins]\nsmolbench_attn = smolbench_attn:register\n")
    # The generation serve is untouched by any of this.
    state.pop("serving", None)
    calls.clear()
    with ec2.serve_model("ministral-3-14b"):
        pass
    (plain,) = [p for m, path, p in calls if path == "/serve"]
    assert plain["vllm_args"] == list(spec_args)
    assert "env" not in plain and "files" not in plain


def test_a_capture_serve_is_not_satisfied_by_a_generation_serve(monkeypatch):
    """The already-serving fast path must not mistake the generation container for a capture one."""
    state = dict(_S5_STATE)
    calls = _capture_harness(monkeypatch, state)
    with ec2.serve_model("ministral-3-14b"):
        pass
    assert [path for _, path, _ in calls].count("/serve") == 1

    # Same model, same box, already healthy: the plain re-serve is skipped ...
    calls.clear()
    with ec2.serve_model("ministral-3-14b"):
        pass
    assert "/serve" not in [path for _, path, _ in calls]

    # ... but the capture serve carries a different payload, so it must swap.
    calls.clear()
    with ec2.serve_model("ministral-3-14b", capture=True):
        pass
    assert [path for _, path, _ in calls].count("/serve") == 1
    # And a plain serve after a capture serve swaps back.
    calls.clear()
    with ec2.serve_model("ministral-3-14b"):
        pass
    assert [path for _, path, _ in calls].count("/serve") == 1


def test_attn_helpers_post_and_poll_the_agent(monkeypatch):
    """attn_start posts the batch; attn_status returns the /status attn block."""
    calls = []

    def fake_agent(state_arg, method, path, payload=None, timeout=120, connect_retries=40):
        calls.append((method, path, payload, timeout))
        if path == "/status":
            return {"healthy": True, "attn": {"running": True, "total": 4, "done": 1}}
        return {"ok": True, "jobs": 2}

    monkeypatch.setattr(ec2, "_agent", fake_agent)
    state = dict(_S5_STATE)
    batch = {"served_model_name": "ministral-3-14b", "tp": 4, "jobs": [{"job_id": "q0"}]}
    assert ec2.attn_start(state, batch) == {"ok": True, "jobs": 2}
    assert ec2.attn_status(state) == {"running": True, "total": 4, "done": 1}
    assert [(m, p) for m, p, _, _ in calls] == [("POST", "/attn"), ("GET", "/status")]
    assert calls[0][2] == batch

    # A box that has never run a capture reports no block; the helper must not raise.
    monkeypatch.setattr(ec2, "_agent",
                        lambda *a, **k: {"healthy": True})
    assert ec2.attn_status(state) == {}


def test_the_plugin_asset_is_read_lazily_not_at_import(tmp_path):
    """payloads must import even when the plugin asset is absent (it is written separately)."""
    import ast

    assert payloads.attention_capture_plugin_py().startswith('"""')
    assert "SMOLBENCH_ATTN_DIR" in payloads.attention_capture_plugin_py()
    source = Path(payloads.__file__).read_text()
    tree = ast.parse(source)
    reads = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_asset"
        and node.args and getattr(node.args[0], "value", "") == "attention_capture_plugin.py.txt"
    ]
    assert reads, "no _asset('attention_capture_plugin.py.txt') call at all"
    module_level = [
        node for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(getattr(c.func, "id", "") == "_asset"
                and getattr(c.args[0], "value", "") == "attention_capture_plugin.py.txt"
                for c in ast.walk(node) if isinstance(c, ast.Call) and c.args)
    ]
    assert module_level == [], "the plugin asset must not be read at module import"


def test_a_capture_serve_refuses_kv_sharing_fast_prefill(monkeypatch):
    """The contract forbids the flag under capture: shared layers would skip the positions."""
    state = dict(_S5_STATE)
    _capture_harness(monkeypatch, state)
    spec = dict(ec2.EC2_DEPLOY_SPECS["ministral-3-14b"])
    spec["vllm_args"] = list(spec["vllm_args"]) + ["--kv-sharing-fast-prefill"]
    monkeypatch.setitem(ec2.EC2_DEPLOY_SPECS, "ministral-3-14b", spec)
    with pytest.raises(ValueError, match="kv-sharing-fast-prefill"):
        with ec2.serve_model("ministral-3-14b", capture=True):
            pass


def test_a_capture_serve_refuses_a_chunked_prefill_ceiling(monkeypatch):
    """A spec that pins a batched-token ceiling below the context would chunk the prefill."""
    _capture_harness(monkeypatch, dict(_S5_STATE))
    spec = dict(ec2.EC2_DEPLOY_SPECS["ministral-3-14b"])
    spec["vllm_args"] = list(spec["vllm_args"]) + ["--max-num-batched-tokens", "8192"]
    monkeypatch.setitem(ec2.EC2_DEPLOY_SPECS, "ministral-3-14b", spec)
    with pytest.raises(ValueError, match="un-chunked prefill"):
        with ec2.serve_model("ministral-3-14b", capture=True):
            pass


def test_a_capture_serve_refuses_prefix_caching(monkeypatch):
    """Without --no-enable-prefix-caching a cached prefix splits the prefill into two forwards.

    The capture hook would then record one job as two sequences, so the capture
    branch must refuse a spec that does not switch prefix caching off.
    """
    _capture_harness(monkeypatch, dict(_S5_STATE))
    spec = dict(ec2.EC2_DEPLOY_SPECS["ministral-3-14b"])
    spec["vllm_args"] = [a for a in spec["vllm_args"] if a != "--no-enable-prefix-caching"]
    monkeypatch.setitem(ec2.EC2_DEPLOY_SPECS, "ministral-3-14b", spec)
    with pytest.raises(ValueError, match="prefix-caching"):
        with ec2.serve_model("ministral-3-14b", capture=True):
            pass


def test_every_spec_switches_prefix_caching_off_for_capture():
    """Invariant: DETERMINISM_ARGS puts the flag on every spec, so no capture serve trips the check."""
    for key, spec in ec2.EC2_DEPLOY_SPECS.items():
        assert "--no-enable-prefix-caching" in spec["vllm_args"], key


# ------------------------------------------------------------------ per-serve context override
def test_a_capture_serve_can_shorten_the_context_for_that_serve_only(monkeypatch):
    """max_model_len= overrides the payload's context and the un-chunked prefill ceiling for
    one serve; the global spec and later serves are untouched."""
    state = dict(_S5_STATE)
    calls = _capture_harness(monkeypatch, state)
    spec_before = copy.deepcopy(ec2.EC2_DEPLOY_SPECS["ministral-3-14b"])
    assert spec_before["max_model_len"] > 49152
    with ec2.serve_model("ministral-3-14b", capture=True, max_model_len=49152):
        pass
    (payload,) = [p for _m, path, p in calls if path == "/serve"]
    assert payload["max_model_len"] == 49152
    assert payload["vllm_args"] == list(spec_before["vllm_args"]) + ["--max-num-batched-tokens", "49152"]
    assert ec2.EC2_DEPLOY_SPECS["ministral-3-14b"] == spec_before
    # The next capture serve without the keyword uses the spec's context again (and swaps,
    # since the payload differs).
    calls.clear()
    with ec2.serve_model("ministral-3-14b", capture=True):
        pass
    (again,) = [p for _m, path, p in calls if path == "/serve"]
    assert again["max_model_len"] == spec_before["max_model_len"]
    assert again["vllm_args"][-2:] == ["--max-num-batched-tokens", str(spec_before["max_model_len"])]


def test_no_override_leaves_the_capture_payload_exactly_as_before(monkeypatch):
    state = dict(_S5_STATE)
    calls = _capture_harness(monkeypatch, state)
    with ec2.serve_model("ministral-3-14b", capture=True, max_model_len=None):
        pass
    (payload,) = [p for _m, path, p in calls if path == "/serve"]
    spec = ec2.EC2_DEPLOY_SPECS["ministral-3-14b"]
    assert payload["max_model_len"] == spec["max_model_len"]
    assert payload["vllm_args"] == list(spec["vllm_args"]) + [
        "--max-num-batched-tokens", str(spec["max_model_len"])]


@pytest.mark.parametrize("bad", [0, -1, 10 ** 7])
def test_a_context_override_outside_the_spec_is_refused_before_serving(monkeypatch, bad):
    """Only a shorter context than the spec's is accepted; nothing is posted otherwise."""
    state = dict(_S5_STATE)
    calls = _capture_harness(monkeypatch, state)
    with pytest.raises(ValueError, match="max_model_len"):
        with ec2.serve_model("ministral-3-14b", capture=True, max_model_len=bad):
            pass
    assert "/serve" not in [path for _, path, _ in calls]


def test_an_override_conflicting_with_a_spec_batched_token_flag_is_refused(monkeypatch):
    """A spec that pins --max-num-batched-tokens to another value cannot keep the ceiling
    equal to the overridden context, so the serve is refused."""
    state = dict(_S5_STATE)
    calls = _capture_harness(monkeypatch, state)
    spec = copy.deepcopy(ec2.EC2_DEPLOY_SPECS["ministral-3-14b"])
    spec["vllm_args"] = list(spec["vllm_args"]) + ["--max-num-batched-tokens", str(spec["max_model_len"])]
    monkeypatch.setitem(ec2.EC2_DEPLOY_SPECS, "ministral-3-14b", spec)
    with pytest.raises(ValueError, match="max-num-batched-tokens"):
        with ec2.serve_model("ministral-3-14b", capture=True, max_model_len=49152):
            pass
    assert "/serve" not in [path for _, path, _ in calls]


# ------------------------------------------------------------------ capture serve settings
def _served_payload(monkeypatch, **kw):
    """Serve ministral-3-14b in capture mode with `kw` and return the /serve payload."""
    calls = _capture_harness(monkeypatch, dict(_S5_STATE))
    with ec2.serve_model("ministral-3-14b", capture=True, **kw):
        pass
    (payload,) = [p for _m, path, p in calls if path == "/serve"]
    return payload


def _gmu(args):
    """Return every value that follows --gpu-memory-utilization in an argv list."""
    return [args[i + 1] for i, a in enumerate(args) if a == "--gpu-memory-utilization"]


def test_a_capture_serve_sets_the_execute_timeout_by_default_and_nothing_optional(monkeypatch):
    payload = _served_payload(monkeypatch)
    assert payload["env"]["VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS"] == "3600"
    assert ec2.DEFAULT_CAPTURE_EXECUTE_TIMEOUT_S == 3600
    assert "SMOLBENCH_ATTN_GATE_TOL" not in payload["env"]
    assert "SMOLBENCH_ATTN_FILL" not in payload["env"]
    # The spec's own share (appended at import) is the only one, unchanged.
    spec = ec2.EC2_DEPLOY_SPECS["ministral-3-14b"]["vllm_args"]
    assert _gmu(payload["vllm_args"]) == _gmu(spec) == ["0.92"]


def test_a_capture_serve_carries_the_optional_settings_when_given(monkeypatch):
    spec_before = copy.deepcopy(ec2.EC2_DEPLOY_SPECS["ministral-3-14b"])
    payload = _served_payload(
        monkeypatch, execute_model_timeout_s=7200, gate_tol=0.05, fill=True,
        gpu_memory_utilization=0.95)
    env = payload["env"]
    assert env["VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS"] == "7200"
    assert float(env["SMOLBENCH_ATTN_GATE_TOL"]) == 0.05
    assert env["SMOLBENCH_ATTN_FILL"] == "1"
    # Replaced in the payload copy, never appended a second time; the global spec is untouched.
    assert _gmu(payload["vllm_args"]) == ["0.95"]
    assert payload["vllm_args"].count("--gpu-memory-utilization") == 1
    assert ec2.EC2_DEPLOY_SPECS["ministral-3-14b"] == spec_before
    # Every other key of the default capture env is still there.
    for key, value in _CAPTURE_ENV.items():
        if key != "VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS":
            assert env[key] == value


def test_fill_false_adds_no_fill_variable(monkeypatch):
    payload = _served_payload(monkeypatch, fill=False)
    assert "SMOLBENCH_ATTN_FILL" not in payload["env"]


def test_a_gpu_share_is_appended_when_the_spec_carries_none(monkeypatch):
    spec = copy.deepcopy(ec2.EC2_DEPLOY_SPECS["ministral-3-14b"])
    args = spec["vllm_args"]
    at = args.index("--gpu-memory-utilization")
    del args[at:at + 2]
    monkeypatch.setitem(ec2.EC2_DEPLOY_SPECS, "ministral-3-14b", spec)
    payload = _served_payload(monkeypatch, gpu_memory_utilization=0.9)
    assert _gmu(payload["vllm_args"]) == ["0.9"]


@pytest.mark.parametrize("kw", [
    {"execute_model_timeout_s": 299},
    {"execute_model_timeout_s": 0},
    {"execute_model_timeout_s": True},
    {"execute_model_timeout_s": 600.5},
    {"execute_model_timeout_s": "3600"},
    {"gpu_memory_utilization": 0},
    {"gpu_memory_utilization": 1},
    {"gpu_memory_utilization": 1.2},
    {"gpu_memory_utilization": -0.1},
    {"gpu_memory_utilization": True},
    {"gpu_memory_utilization": float("nan")},
    {"gate_tol": 0},
    {"gate_tol": -0.01},
    {"gate_tol": 1.0},
    {"gate_tol": float("nan")},
    {"gate_tol": float("inf")},
    {"gate_tol": True},
    {"fill": 1},
    {"fill": "yes"},
])
def test_bad_capture_settings_are_refused_before_serving(monkeypatch, kw):
    calls = _capture_harness(monkeypatch, dict(_S5_STATE))
    with pytest.raises(ValueError):
        with ec2.serve_model("ministral-3-14b", capture=True, **kw):
            pass
    assert "/serve" not in [path for _, path, _ in calls]


def test_the_lowest_execute_timeout_accepted_is_300(monkeypatch):
    payload = _served_payload(monkeypatch, execute_model_timeout_s=300)
    assert payload["env"]["VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS"] == "300"


@pytest.mark.parametrize("kw", [
    {"execute_model_timeout_s": 3600},
    {"gate_tol": 0.05},
    {"fill": True},
    {"gpu_memory_utilization": 0.95},
])
def test_capture_only_settings_are_refused_on_a_generation_serve(monkeypatch, kw):
    calls = _capture_harness(monkeypatch, dict(_S5_STATE))
    with pytest.raises(ValueError):
        with ec2.serve_model("ministral-3-14b", **kw):
            pass
    assert "/serve" not in [path for _, path, _ in calls]


def test_the_guards_still_hold_with_the_new_settings(monkeypatch):
    """Prefix caching and the batched-token ceiling are still checked when settings are given."""
    _capture_harness(monkeypatch, dict(_S5_STATE))
    spec = dict(ec2.EC2_DEPLOY_SPECS["ministral-3-14b"])
    spec["vllm_args"] = [a for a in spec["vllm_args"] if a != "--no-enable-prefix-caching"]
    monkeypatch.setitem(ec2.EC2_DEPLOY_SPECS, "ministral-3-14b", spec)
    with pytest.raises(ValueError, match="prefix-caching"):
        with ec2.serve_model("ministral-3-14b", capture=True, fill=True, gate_tol=0.05,
                             gpu_memory_utilization=0.95, execute_model_timeout_s=3600):
            pass


def test_attn_full_status_returns_the_whole_reply_with_its_log_tail(monkeypatch):
    calls = []
    reply = {"healthy": False, "container": "exited", "log_tail": "EngineDeadError ...",
             "serve_log_tail": "", "attn": {"running": False}}

    def fake_agent(state_arg, method, path, payload=None, timeout=120, connect_retries=40):
        calls.append((state_arg, method, path))
        return dict(reply)

    monkeypatch.setattr(ec2, "_agent", fake_agent)
    # It takes the state explicitly, like attn_status: it must never re-read the state file.
    monkeypatch.setattr(ec2, "_require_state", lambda: pytest.fail("state file re-read"))
    state = dict(_S5_STATE)
    assert ec2.attn_full_status(state) == reply
    assert calls == [(state, "GET", "/status")]
