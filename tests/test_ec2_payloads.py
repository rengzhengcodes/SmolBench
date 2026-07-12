"""Offline checks of the smolbench.evals.payloads on-instance payloads.

The control agent and idle watchdog ride to the instance inside cloud-init
user-data; nothing on the client ever imports them as modules (they live as
.py.txt/.sh assets in smolbench/evals/payloads/), so these tests are the only
pre-launch validation they get. They must stay stdlib-only and Python
3.10-compatible (the instance's system python).
"""

import ast
import inspect
import os
import re
import subprocess
import sys
from pathlib import Path

import smolbench.evals.ec2 as ec2
from smolbench.evals import payloads
from smolbench.evals.payloads import AGENT_PY, WATCHDOG_PY, render_user_data


def _watchdog_env_default(name: str) -> str:
    """The fallback WATCHDOG_PY passes to ``os.environ.get(name, <default>)``.

    Extracted via ast so the pin survives reformatting of the payload; fails
    loudly if the lookup disappears or stops being a plain string literal.
    """
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
    rendered = render_user_data(
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


def test_startup_grace_default_invariant():
    """ec2.py's EC2_STARTUP_GRACE_MIN default and WATCHDOG_PY's own
    STARTUP_GRACE_MIN fallback are enforced-by-comment twins (the client
    threads the value through user-data, but if that plumbing ever breaks the
    watchdog silently falls back to its literal); pin them equal mechanically.
    """
    assert _watchdog_env_default("STARTUP_GRACE_MIN") == _ec2_getenv_default(
        "EC2_STARTUP_GRACE_MIN"
    ) == "180"


def test_idle_timeout_default_invariant():
    """Same twin-literal invariant as STARTUP_GRACE_MIN, for the idle timeout."""
    assert _watchdog_env_default("IDLE_TIMEOUT_MIN") == _ec2_getenv_default(
        "EC2_IDLE_TIMEOUT_MIN"
    ) == "30"


def test_render_user_data_headroom_with_realistic_inputs():
    """Headroom canary: render with realistically sized inputs (43-char
    tokens, a real image tag, a long S3 URI) so the assert message shows how
    close the payload sits to EC2's 16 KB user-data cap. As of this pin the
    headroom is ~160 bytes -- any net growth in AGENT_PY / WATCHDOG_PY /
    USER_DATA_TEMPLATE eats it directly.
    """
    rendered = render_user_data(
        control_token="x" * 43,
        vllm_api_key="y" * 43,
        hf_token="",
        idle_timeout_min=30,
        startup_grace_min=180,
        max_lifetime_min=1440,
        image="vllm/vllm-openai:v0.11.1",
        s3_cache_uri="s3://smolbench-model-cache-000000000000/vllm-models",
    )
    size = len(rendered.encode())
    assert size < 16384, f"user-data over the 16 KB cap: {size} bytes"
    headroom = 16384 - size
    assert headroom > 0, f"no headroom left ({size} bytes rendered)"
    print(f"user-data headroom: {headroom} bytes ({size}/16384)")


def test_payload_assets_are_byte_clean():
    """The .py.txt/.sh assets are byte-exact payloads: LF-only, no leading
    blank line, exactly one trailing newline. The templates' trailing bytes
    flow into the rendered user-data verbatim, so an editor-added blank line
    or a CRLF checkout is real byte drift against the 16 KB cap."""
    asset_dir = Path(payloads.__file__).resolve().parent
    for name in ("agent.py.txt", "watchdog.py.txt", "user_data.sh", "train_user_data.sh"):
        raw = (asset_dir / name).read_bytes()
        assert b"\r" not in raw, f"{name}: CR byte (CRLF checkout?)"
        assert raw.endswith(b"\n"), f"{name}: missing trailing newline"
        assert not raw.endswith(b"\n\n"), f"{name}: extra trailing blank line"
        assert not raw.startswith(b"\n"), f"{name}: leading blank line"


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
