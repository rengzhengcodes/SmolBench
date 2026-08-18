"""Offline checks of the smolbench.evals.payloads on-instance payloads.

The control agent and idle watchdog ride to the instance inside cloud-init
user-data; nothing on the client ever imports them as modules (they live as
.py.txt/.sh assets in smolbench/evals/payloads/), so these tests are the only
pre-launch validation they get. They must stay stdlib-only and Python
3.10-compatible (the instance's system python).
"""

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

import smolbench.evals.ec2 as ec2
from smolbench.evals import payloads
from smolbench.evals.payloads import AGENT_PY, WATCHDOG_PY, pack_user_data, render_user_data


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


def test_agent_fingerprint_addition_compiles_and_is_present():
    """The /status ``fingerprint`` object (server_config §5 provenance
    extension, DETERMINISM_PLAN_2026-08-16.md section 5) is new code in
    AGENT_PY. ``compile()`` it directly -- a stricter check than
    ``test_payloads_parse``'s ``ast.parse`` (catches anything a plain parse
    would not, e.g. a bytecode-level issue) -- and confirm the addition
    actually landed in the rendered payload rather than only in a local
    draft.
    """
    compile(AGENT_PY, "<agent.py.txt>", "exec")
    assert "fingerprint" in AGENT_PY
    assert '"fingerprint": fingerprint()' in AGENT_PY


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
    """The cap now binds on ``pack_user_data``'s COMPRESSED output, not the
    raw rendered text -- render_user_data itself no longer asserts a size
    bound (see its docstring), so this test's own size check moved with it.
    """
    rendered = render_user_data(
        control_token="tok",
        vllm_api_key="key",
        hf_token="",
        idle_timeout_min=30,
        startup_grace_min=180,
        max_lifetime_min=1440,
        image=_PINNED_IMAGE,
        s3_cache_uri="s3://bucket/hf",
    )
    assert "@@" not in rendered  # every placeholder substituted
    assert len(pack_user_data(rendered)) < 16384  # EC2 user-data cap (pre-base64, post-gzip)
    assert AGENT_PY.rstrip("\n") in rendered
    assert WATCHDOG_PY.rstrip("\n") in rendered


def test_pack_user_data_is_byte_stable_and_round_trips():
    """``pack_user_data`` must be a pure, byte-reproducible compressor.

    Two calls on identical input must be byte-for-byte IDENTICAL (this is
    what ``mtime=0`` buys -- gzip's header otherwise embeds the compression
    wall-clock time, which would make two calls a second apart differ even
    though the payload is unchanged). Also checks the round trip: gunzipping
    the packed bytes must reproduce the original rendered string exactly,
    which is the same transparent-decompression property cloud-init relies
    on when it gunzips this on the instance.
    """
    rendered = render_user_data(
        control_token="tok",
        vllm_api_key="key",
        hf_token="",
        idle_timeout_min=30,
        startup_grace_min=180,
        max_lifetime_min=1440,
        image=_PINNED_IMAGE,
        s3_cache_uri="s3://bucket/hf",
    )
    packed_1 = pack_user_data(rendered)
    packed_2 = pack_user_data(rendered)
    assert packed_1[:2] == b"\x1f\x8b", "packed user-data must carry the gzip magic (cloud-init keys on it)"
    assert packed_1 == packed_2, "pack_user_data must be byte-stable across calls on identical input"
    assert gzip.decompress(packed_1).decode() == rendered, "gunzipping packed bytes must reproduce rendered exactly"


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


# The digest literal on purpose, NOT ec2.EC2_VLLM_IMAGE: that constant honors
# the EC2_VLLM_IMAGE env var, so a developer shell with a short tag exported
# would silently weaken the size tests below (same env-independence rationale
# as test_deploy_specs.test_ec2_vllm_image_default_is_digest_pinned).
_PINNED_IMAGE = "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7"


def test_render_user_data_headroom_with_realistic_inputs():
    """Headroom canary: render with realistically sized inputs (43-char
    tokens, the real digest-pinned image, a long S3 URI) so the assert
    message shows how close the payload sits to EC2's 16 KB user-data cap.

    The cap now binds on the GZIP-COMPRESSED bytes (``pack_user_data``), not
    the raw rendered text: the digest-pinned ``EC2_VLLM_IMAGE`` (an 88-char
    ``vllm/vllm-openai@sha256:<64 hex>`` string, versus the old ~24-char
    ``vllm/vllm-openai:v0.11.1`` tag) alone pushed the RAW size over 16 KB --
    this test prints both numbers so that fact stays visible rather than
    silently fixed by compression. Any net growth in AGENT_PY / WATCHDOG_PY /
    USER_DATA_TEMPLATE now eats into the compressed headroom instead.
    """
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
    raw_size = len(rendered.encode())
    packed = pack_user_data(rendered)
    compressed_size = len(packed)
    compressed_headroom = 16384 - compressed_size
    assert compressed_size < 16384, f"compressed user-data over the 16 KB cap: {compressed_size} bytes"
    assert compressed_headroom > 0, f"no compressed headroom left ({compressed_size} bytes packed)"
    # Floor at 6 KB: the docs quote the live headroom, and it has silently
    # drifted once already (10,615 -> 9,025 when the section-5 fingerprint
    # landed, leaving stale "~11 KB" claims in three files). Tripping this
    # floor is the signal to re-measure and update every doc site, not to
    # lower the floor.
    assert compressed_headroom > 6000, (
        f"compressed headroom {compressed_headroom} fell below the 6 KB floor -- "
        "re-measure and update the doc/comment sites quoting the margin")
    print(
        f"user-data size: raw={raw_size} bytes (cap {'EXCEEDED' if raw_size >= 16384 else 'OK'}), "
        f"compressed={compressed_size}/16384 bytes (headroom {compressed_headroom})"
    )


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


def test_agent_fingerprint_computes_weights_digest_from_a_synthetic_cache(tmp_path):
    """Actually RUNS AGENT_PY's fingerprint() (via importlib, same shape as
    test_watchdog_runs_once_unprivileged's subprocess pattern) against a
    synthetic HF cache tree, so the weights_digest/hf_snapshots composition
    is exercised rather than merely proven syntactically present.
    test_payloads_parse and test_agent_fingerprint_addition_compiles_and_is_present
    above would both pass even with a typo in the digest math; this test
    would not. Also exercises the "docker/nvidia-smi degrade to None, never
    raise" path for real, since this sandbox has no docker socket.
    """
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
    # Independently recomputed expected digest -- proves the field is
    # actually the spec's "index bytes + sorted (filename,size) repr", not
    # just some 64-hex-char string.
    h = hashlib.sha256()
    h.update(index_bytes)
    sizes = sorted([
        ("model-00001-of-00002.safetensors", 100),
        ("model-00002-of-00002.safetensors", 200),
    ])
    h.update(repr(sizes).encode())
    assert fp["weights_digest"] == h.hexdigest()
    # docker/nvidia-smi: must degrade to None or a well-typed value, never
    # raise (proc.returncode == 0 above already proves no exception escaped).
    assert fp["image_repo_digests"] is None or isinstance(fp["image_repo_digests"], list)
    assert fp["nvidia_smi"] is None or isinstance(fp["nvidia_smi"], str)


def test_vllm_api_key_is_passed_as_one_token_not_two():
    """`--api-key=VALUE`, never `--api-key VALUE`.

    The key is `secrets.token_urlsafe(32)`, whose alphabet includes '-', so
    ~1.5% of generated keys START with a hyphen. Passed as two argv entries,
    argparse reads such a key as the next option and the server dies at
    startup with:

        vllm serve: error: argument --api-key: expected at least one argument

    That is a ~1-in-65 random box-launch death that looks exactly like flaky
    infrastructure -- it killed a ministral-3-3b relaunch on 2026-08-15 and
    would have been dismissed as capacity noise. The `=` form binds the value
    to the option, so a leading hyphen is just data.
    """
    from smolbench.evals.payloads import AGENT_PY

    assert '"--api-key=" + VLLM_API_KEY' in AGENT_PY, (
        "the api key must be bound with '=' so a leading-hyphen key cannot "
        "be parsed as a flag"
    )
    assert '"--api-key", VLLM_API_KEY' not in AGENT_PY
