"""Offline checks of ec2.py's embedded on-instance payloads.

The control agent and idle watchdog ride to the instance inside cloud-init
user-data; nothing on the client ever imports them, so these tests are the
only pre-launch validation they get. They must stay stdlib-only and
Python 3.10-compatible (the instance's system python).
"""

import ast
import os
import subprocess
import sys

from smolbench.evals.ec2 import AGENT_PY, WATCHDOG_PY, _render_user_data


def test_payloads_parse():
    ast.parse(AGENT_PY)
    ast.parse(WATCHDOG_PY)


def test_payloads_are_310_compatible():
    """No syntax above 3.10 and no non-stdlib imports in either payload."""
    stdlib = set(sys.stdlib_module_names)
    for payload in (AGENT_PY, WATCHDOG_PY):
        tree = ast.parse(payload)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                roots = [(node.module or "").split(".")[0]]
            else:
                continue
            for root in roots:
                assert root in stdlib, f"non-stdlib import in payload: {root}"


def test_render_user_data_fills_and_fits():
    rendered = _render_user_data(
        control_token="tok",
        vllm_api_key="key",
        hf_token="",
        idle_timeout_min=30,
        startup_grace_min=180,
        max_lifetime_min=1440,
        image="vllm/vllm-openai:v0.11.1",
        s3_cache_uri="s3://bucket/hf",
    )
    assert "@@" not in rendered  # every placeholder substituted
    assert len(rendered.encode()) < 16384  # EC2 user-data cap (pre-base64)
    assert AGENT_PY.rstrip("\n") in rendered
    assert WATCHDOG_PY.rstrip("\n") in rendered


def test_watchdog_runs_once_unprivileged(tmp_path):
    """The SMOLBENCH_WATCHDOG_ONCE/RUN_DIR hooks let one check run as a
    normal user with no docker/vLLM present; it must survive that (a
    transient probe failure must never kill the safety net) and stamp the
    idle clock."""
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
    assert (run_dir / "last_active").exists()  # boot starts the idle clock
