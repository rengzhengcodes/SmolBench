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
