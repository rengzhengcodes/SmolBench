"""Check the smolbench.evals.payloads on-instance payloads, offline."""

import ast
import gzip
import hashlib
import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import smolbench.evals.providers.ec2 as ec2
from smolbench.evals import payloads
from smolbench.evals.payloads import AGENT_PY, WATCHDOG_PY, pack_user_data, render_user_data

# realistic digest-length image string (size realism only; the real pin lives in test_deploy_specs)
_PINNED_IMAGE = "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7"


def _watchdog_env_default(name: str) -> str:
    """The fallback WATCHDOG_PY passes to ``os.environ.get(name, <default>)``."""
    for node in ast.walk(ast.parse(WATCHDOG_PY)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == name
            and len(node.args) == 2
            and isinstance(node.args[1], ast.Constant)
        ):
            return node.args[1].value
    raise AssertionError(f"no os.environ.get({name!r}, <literal>) in WATCHDOG_PY")


def _ec2_getenv_default(name: str) -> str:
    """The default ec2.py passes to ``os.getenv(name, <default>)`` at import."""
    match = re.search(
        rf'os\.getenv\("{name}",\s*"(\d+)"\)', inspect.getsource(ec2)
    )
    assert match, f'no os.getenv("{name}", "<digits>") in ec2.py'
    return match.group(1)


def test_payloads_are_stdlib_only_and_parse():
    """No syntax above 3.10 and no non-stdlib imports in either payload."""
    stdlib = set(sys.stdlib_module_names)
    for payload in (AGENT_PY, WATCHDOG_PY):
        for node in ast.walk(ast.parse(payload)):
            if isinstance(node, ast.Import):
                roots = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                roots = [(node.module or "").split(".")[0]]
            else:
                continue
            assert all(r in stdlib for r in roots), f"non-stdlib import in payload: {roots}"


def test_render_user_data_fills_and_packs_deterministically():
    """Live 16KB user-data cap canary."""
    rendered = render_user_data(
        control_token="x" * 43,
        vllm_api_key="y" * 43,
        hf_token="",
        idle_timeout_min=30,
        startup_grace_min=180,
        max_lifetime_min=1440,
        image=_PINNED_IMAGE,
        s3_cache_uri="s3://smolbench-model-cache-000000000000/vllm-models",
    )
    assert "@@" not in rendered
    assert AGENT_PY.rstrip("\n") in rendered
    assert WATCHDOG_PY.rstrip("\n") in rendered

    packed = pack_user_data(rendered)
    assert packed[:2] == b"\x1f\x8b", "cloud-init keys on the gzip magic"
    assert packed == pack_user_data(rendered), "pack_user_data must be byte-stable"
    assert gzip.decompress(packed).decode() == rendered

    headroom = 16384 - len(packed)
    assert headroom > 0, f"compressed user-data over the 16 KB cap: {len(packed)} bytes"
    assert headroom > 6000, (
        f"compressed headroom {headroom} fell below the 6 KB floor -- "
        "re-measure and update the doc/comment sites quoting the margin")
    print(f"user-data: raw={len(rendered.encode())} compressed={len(packed)}/16384 headroom={headroom}")


@pytest.mark.parametrize(
    "watchdog_name,env_name,expected",
    [("STARTUP_GRACE_MIN", "EC2_STARTUP_GRACE_MIN", "180"),
     ("IDLE_TIMEOUT_MIN", "EC2_IDLE_TIMEOUT_MIN", "30")],
)
def test_watchdog_and_client_defaults_are_twins(watchdog_name, env_name, expected):
    """If the user-data plumbing breaks, the watchdog's own fallback must match ec2.py."""
    assert _watchdog_env_default(watchdog_name) == _ec2_getenv_default(env_name) == expected


def test_payload_assets_are_byte_clean():
    """LF-only, no leading blank line, exactly one trailing newline."""
    asset_dir = Path(payloads.__file__).resolve().parent
    for name in ("agent.py.txt", "watchdog.py.txt", "user_data.sh"):
        raw = (asset_dir / name).read_bytes()
        assert b"\r" not in raw, f"{name}: CR byte (CRLF checkout?)"
        assert raw.endswith(b"\n"), f"{name}: missing trailing newline"
        assert not raw.endswith(b"\n\n"), f"{name}: extra trailing blank line"
        assert not raw.startswith(b"\n"), f"{name}: leading blank line"


def test_watchdog_runs_once_unprivileged(tmp_path):
    """One check must survive with no docker or vLLM present, and stamp the idle clock."""
    watchdog = tmp_path / "watchdog.py"
    watchdog.write_text(WATCHDOG_PY)
    run_dir = tmp_path / "run"
    env = os.environ | {
        "SMOLBENCH_RUN_DIR": str(run_dir),
        "SMOLBENCH_WATCHDOG_ONCE": "1",
        "IDLE_TIMEOUT_MIN": "30",
    }
    proc = subprocess.run(
        [sys.executable, str(watchdog)], env=env, capture_output=True, text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert (run_dir / "last_active").exists()


def test_agent_fingerprint_computes_weights_digest_from_a_synthetic_cache(tmp_path):
    """Run AGENT_PY's fingerprint() against a synthetic HF cache tree."""
    agent_path = tmp_path / "agent.py"
    agent_path.write_text(AGENT_PY)

    cache_hub = tmp_path / "hub"
    snap_dir = cache_hub / "models--acme--demo-7b" / "snapshots" / "deadbeefcafe"
    snap_dir.mkdir(parents=True)
    index_bytes = b'{"weight_map": {}}'
    (snap_dir / "model.safetensors.index.json").write_bytes(index_bytes)
    (snap_dir / "model-00001-of-00002.safetensors").write_bytes(b"a" * 100)
    (snap_dir / "model-00002-of-00002.safetensors").write_bytes(b"b" * 200)

    script = (
        "import importlib.util, json, os\n"
        f"spec = importlib.util.spec_from_file_location('agent', {str(agent_path)!r})\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        "mod.LAST_HF_ID = 'acme/demo-7b'\n"
        "print(json.dumps(mod.fingerprint()))\n"
    )
    env = os.environ | {
        "CONTROL_TOKEN": "tok", "VLLM_API_KEY": "key",
        "VLLM_IMAGE": "vllm/vllm-openai@sha256:deadbeef",
        "SMOLBENCH_CACHE_HUB": str(cache_hub),
    }
    proc = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    fp = json.loads(proc.stdout)

    assert fp["hf_snapshots"] == ["deadbeefcafe"]
    # digest spec: index bytes + repr of sorted (filename, size) pairs
    h = hashlib.sha256()
    h.update(index_bytes)
    sizes = sorted([
        ("model-00001-of-00002.safetensors", 100),
        ("model-00002-of-00002.safetensors", 200),
    ])
    h.update(repr(sizes).encode())
    assert fp["weights_digest"] == h.hexdigest()
    # docker/nvidia-smi degrade to None, never raise
    assert fp["image_repo_digests"] is None or isinstance(fp["image_repo_digests"], list)
    assert fp["nvidia_smi"] is None or isinstance(fp["nvidia_smi"], str)


def test_vllm_api_key_is_passed_as_one_token_not_two():
    """``--api-key=VALUE``: a token_urlsafe key starting with '-' must not parse as a flag."""
    assert '"--api-key=" + VLLM_API_KEY' in AGENT_PY
    assert '"--api-key", VLLM_API_KEY' not in AGENT_PY
