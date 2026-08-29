"""Offline tests for notebooks/deduction/run_study.py, the per-lane generation driver.

No AWS, no network, no Lean: the end-to-end sweep drives a local ``StubServer``
plus ``NullVerifier``, and the S3 paths run against an injected fake client.
``scripts/deduction/lean_verify_rows.py`` is covered by test_lean_verify_resume.py.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from smolbench.deduction.lean import corpus, runner
from smolbench.deduction.lean.nullverify import NullVerifier
from conftest import StubServer, chat_completion
from tests._paths import LEAN_MINI as FIXTURE
from tests._paths import NOTEBOOKS, REPO_ROOT

DRIVER_PATH = NOTEBOOKS / "deduction" / "run_study.py"
INDUCTION_STUDY_PATH = NOTEBOOKS / "induction" / "run_study.py"
KEY = "glm-4.7"
IMAGE = "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7"
THEOREMS = {
    "source": "replay_passing", "kind": "novel_premises",
    "split": "val", "limit": 300, "seed": 0,
}


def _load_by_path(path: Path, name: str):
    """Execute `path` as a module `name`; sys.modules must be set before exec_module
    or a 3.14 @dataclass in it raises from ``dataclasses._is_type``."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def driver():
    """The driver, imported with os.environ snapshotted/restored: it calls load_dotenv
    at import time, which would otherwise pollute the whole pytest session."""
    saved = dict(os.environ)
    try:
        os.environ["LEAN_MODEL"] = KEY
        os.environ.pop("LEAN_RUN_NAME", None)
        os.environ.pop("LEAN_STATE_FILE", None)
        module = _load_by_path(DRIVER_PATH, "deduction_run_study")
        module.post_import_env = dict(os.environ)
    finally:
        os.environ.clear()
        os.environ.update(saved)
    yield module
    sys.modules.pop("deduction_run_study", None)


def test_config_is_user_locked(driver):
    """Every user-locked sweep-config value, and the exact key set, pinned."""
    cfg = driver.build_config(KEY)
    assert cfg["concurrent_gen"] is True and cfg["skip_trivial"] is True
    assert cfg == {
        "run_name": f"scaling_{KEY}", "seed": 0, "temperature": 0.7,
        "max_tokens": 32768, "request_timeout": 1800, "max_retries": 2,
        "dojo_timeout": 300, "concurrent_gen": True, "skip_trivial": True,
        "max_concurrency": 8, "theorem_workers": 4, "n_replicates": 1,
        "k": {"strategy": "last"}, "theorems": THEOREMS,
        "rungs": ["stepk:1", "hint:2", "noise:3", "hint:3"],
        "models": cfg["models"],
    }


def test_config_env_overrides(driver, monkeypatch, tmp_path):
    """LEAN_RUN_NAME / LEAN_SHARD / LEAN_CELL_WHITELIST thread into the config."""
    monkeypatch.setenv("LEAN_RUN_NAME", "scaling_custom")
    assert driver.build_config(KEY)["run_name"] == "scaling_custom"
    monkeypatch.delenv("LEAN_RUN_NAME")
    assert driver.build_config(KEY)["run_name"] == f"scaling_{KEY}"

    monkeypatch.setenv("LEAN_SHARD", "1/3")
    cfg = driver.build_config(KEY)
    assert cfg["theorems"] == dict(THEOREMS, shard="1/3")
    assert cfg["run_name"] == f"scaling_{KEY}_shard1of3"
    monkeypatch.setenv("LEAN_RUN_NAME", "scaling_custom")
    assert driver.build_config(KEY)["run_name"] == "scaling_custom"
    monkeypatch.delenv("LEAN_RUN_NAME")
    monkeypatch.delenv("LEAN_SHARD")

    path = tmp_path / "whitelist.json"
    path.write_text(json.dumps([[KEY, "T", 1, "stepk:1", 0], [KEY, "U", 2, "hint:2", 1]]))
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(path))
    cfg = driver.build_config(KEY)
    assert cfg["cell_whitelist"] == {
        "path": str(path),
        "sha256": runner.hash_cell_keys(runner.load_cell_whitelist(str(path))),
    }

    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(tmp_path / "does_not_exist.json"))
    with pytest.raises(ValueError):
        driver.build_config(KEY)


def test_build_config_does_not_mutate_shared_cot_table(driver):
    """A mutated returned config must not corrupt the module-global COT_ARGS table."""
    before = json.dumps(driver.COT_ARGS[KEY], sort_keys=True)
    cfg = driver.build_config(KEY)
    cfg["models"][0]["extra_params"]["enable_thinking"] = "CLOBBERED"
    cfg["theorems"]["limit"] = 1
    assert json.dumps(driver.COT_ARGS[KEY], sort_keys=True) == before
    assert driver.build_config(KEY)["theorems"]["limit"] == 300


def test_extra_params_all_21_keys(driver):
    """The driver reuses the induction roster and its per-model reasoning toggles."""
    saved = dict(os.environ)
    try:
        induction = _load_by_path(INDUCTION_STUDY_PATH, "induction_run_study_for_deduction")
    finally:
        os.environ.clear()
        os.environ.update(saved)
        sys.modules.pop("induction_run_study_for_deduction", None)

    assert len(driver.MODELS) == 21
    assert driver.MODELS == induction.MODELS
    for key in induction.MODELS:
        models = driver.build_config(key)["models"]
        assert len(models) == 1, key
        assert models[0] == {
            "provider": "ec2", "model": key, "display_name": key,
            "extra_params": induction.COT_ARGS[key],
        }, key


def test_lane_env_defaults(driver, tmp_path):
    """lane_env_defaults is pure and derives the fleet-compatible names."""
    import smolbench

    assert driver.REPO_ROOT == Path(smolbench.__file__).resolve().parents[1]

    before = dict(os.environ)
    got = driver.lane_env_defaults(KEY, repo_root=tmp_path)
    assert dict(os.environ) == before, "lane_env_defaults must not touch os.environ"
    assert got["EC2_EXPERIMENT_TAG"] == f"scaling-{KEY}"
    assert got["EC2_STATE_FILE"] == str(tmp_path / f".ec2_state_scaling_{KEY}.json")
    assert got["EC2_VLLM_IMAGE"] == IMAGE
    assert got["SMOLBENCH_LEAN_RESULTS"] == str(tmp_path / "notebooks" / "deduction" / "results")

    again = driver.lane_env_defaults(KEY, repo_root=tmp_path)
    assert again == got and again is not got

    bare = driver.lane_env_defaults(KEY, repo_root=tmp_path, state_file=".ec2_state_x.json")
    assert bare["EC2_STATE_FILE"] == str(tmp_path / ".ec2_state_x.json")
    assert Path(bare["EC2_STATE_FILE"]).is_absolute()
    absolute = str(tmp_path / "elsewhere" / "state.json")
    got = driver.lane_env_defaults(KEY, repo_root=tmp_path, state_file=absolute)
    assert got["EC2_STATE_FILE"] == absolute


def _run_driver(env_lines: str, checks: str):
    """Import the driver in a clean interpreter; only a fresh one can witness ordering."""
    code = (
        "import os, sys, importlib.util\n"
        "os.environ['LEAN_MODEL'] = 'glm-4.7'\n" + env_lines
        + f"spec = importlib.util.spec_from_file_location('d', r'{DRIVER_PATH}')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "sys.modules['d'] = m\n"
        "spec.loader.exec_module(m)\n" + checks
    )
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300,
    )


def test_driver_subprocess_env_contract():
    """setdefault beats ec2's freeze, yields to fleet env, refuses a foreign tag."""
    proc = _run_driver(
        "for junk in ('EC2_EXPERIMENT_TAG', 'EC2_STATE_FILE', 'LEAN_STATE_FILE'):\n"
        "    os.environ.pop(junk, None)\n"
        "assert 'smolbench.evals.providers.ec2' not in sys.modules\n",
        "from smolbench.evals.providers import ec2\n"
        "assert ec2.EC2_EXPERIMENT_TAG == 'scaling-glm-4.7', ec2.EC2_EXPERIMENT_TAG\n"
        f"assert ec2.EC2_VLLM_IMAGE == {IMAGE!r}, ec2.EC2_VLLM_IMAGE\n"
        "assert os.environ['EC2_STATE_FILE'].endswith('.ec2_state_scaling_glm-4.7.json')\n"
        "assert os.path.isabs(os.environ['EC2_STATE_FILE'])\n"
        "print('ORDERING-OK')\n",
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "ORDERING-OK" in proc.stdout

    proc = _run_driver(
        "os.environ['EC2_EXPERIMENT_TAG'] = 'fleet-owned-glm-4.7'\n"
        "os.environ['EC2_VLLM_IMAGE'] = 'fleet/image:pinned'\n"
        "os.environ['SMOLBENCH_LEAN_RESULTS'] = '/tmp/fleet-owned-results'\n",
        "assert os.environ['EC2_EXPERIMENT_TAG'] == 'fleet-owned-glm-4.7'\n"
        "assert os.environ['EC2_VLLM_IMAGE'] == 'fleet/image:pinned'\n"
        "assert os.environ['SMOLBENCH_LEAN_RESULTS'] == '/tmp/fleet-owned-results'\n"
        "print('SETDEFAULT-OK')\n",
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "SETDEFAULT-OK" in proc.stdout

    proc = _run_driver("os.environ['EC2_EXPERIMENT_TAG'] = 'scaling-standalone'\n", "")
    assert proc.returncode != 0, "a shared tag must abort, not start a box"
    assert "does not name this lane" in proc.stderr


def test_selected_model_rejects_unknown_and_missing(driver, monkeypatch):
    """LEAN_MODEL must name one of the 21 study keys."""
    monkeypatch.setenv("LEAN_MODEL", KEY)
    assert driver.selected_model() == KEY
    monkeypatch.setenv("LEAN_MODEL", "not-a-model")
    with pytest.raises(SystemExit) as excinfo:
        driver.selected_model()
    assert "not-a-model" in str(excinfo.value)
    monkeypatch.delenv("LEAN_MODEL")
    with pytest.raises(SystemExit):
        driver.selected_model()


@pytest.fixture
def stub():
    server = StubServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture
def sweep_env(stub, monkeypatch, tmp_path):
    """Point the ec2 provider at `stub` via its documented test overrides: no AWS call."""
    monkeypatch.setenv("EC2_INFERENCE_BASE_URL", stub.base_url)
    monkeypatch.setenv("EC2_VLLM_API_KEY", "stub-key")
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    monkeypatch.setenv("SMOLBENCH_LEAN_RESULTS", str(tmp_path))
    stub.default_response = chat_completion("```lean\n  simp\n```")
    corpus.reset_caches()
    yield tmp_path
    corpus.reset_caches()


def _rows(run_dir, kind):
    rows = [json.loads(x) for x in (run_dir / "all_rows.jsonl").read_text().splitlines()]
    return [r for r in rows if r.get("kind") == kind]


def _chat_posts(stub):
    return [
        r for r in stub.requests
        if r.get("body") is not None and r["path"].endswith("/chat/completions")
    ]


def test_end_to_end_sweep_offline(driver, sweep_env, stub):
    """A full sweep runs offline: right request bodies, right rows, resume skips."""
    cfg = driver.build_config(KEY)
    # The mini fixture has no replay_passing/novel_premises sidecar; every other
    # locked value runs exactly as the real lane would run it.
    cfg["theorems"] = {
        "source": "explicit", "full_names": ["Mini.theoremA"],
        "kind": "random", "split": "val",
    }
    cfg["skip_trivial"] = False
    cfg["concurrent_gen"] = False
    cfg["theorem_workers"] = 1
    run_dir = sweep_env / "runs" / cfg["run_name"]

    # one theorem x one k (strategy "last") x 4 rungs x 1 model x 1 replicate
    assert runner.sweep(cfg, run_dir, verifier=NullVerifier()) == 4

    posts = _chat_posts(stub)
    assert len(posts) == 4
    for req in posts:
        body = req["body"]
        assert body["chat_template_kwargs"] == driver.COT_ARGS[KEY]["chat_template_kwargs"]
        assert body["seed"] == 0
        assert body["temperature"] == 0.7
        assert body["max_tokens"] == 32768

    cells = _rows(run_dir, "cell")
    assert len(cells) == 4
    assert {c["rung"] for c in cells} == {"stepk:1", "hint:2", "noise:3", "hint:3"}
    for row in cells:
        assert row["replicate_idx"] == 0
        assert row["seed"] == 0
        assert row["model"] == KEY
        assert row["provider"] == "ec2"
        assert row["verdict"] == "unverified"

    # The sanity gate is deferred too, and must not suppress cell generation.
    sanity = _rows(run_dir, "sanity")
    assert sanity and all(s["verdict"] == "skipped" for s in sanity)

    before = len(_chat_posts(stub))
    assert runner.sweep(cfg, run_dir, verifier=NullVerifier()) == 0
    assert len(_chat_posts(stub)) == before
    assert len(_rows(run_dir, "cell")) == 4


class FakeS3:
    """Minimal in-memory stand-in for the boto3 S3 client surface used here."""

    def __init__(self, *, corrupt_key: str | None = None):
        self.objects: dict[str, int] = {}
        self.uploads: list[tuple[str, str, str]] = []
        self.corrupt_key = corrupt_key

    def upload_file(self, filename, bucket, key):
        self.uploads.append((str(filename), bucket, key))
        self.objects[key] = 1 if key == self.corrupt_key else Path(filename).stat().st_size

    def head_object(self, Bucket, Key):  # noqa: N803 -- boto3's parameter names
        if Key not in self.objects:
            raise KeyError(Key)
        return {"ContentLength": self.objects[Key]}


def _populate(run_dir: Path):
    nested = run_dir / "theorems" / "Mini.theoremA"
    nested.mkdir(parents=True)
    (run_dir / "manifest.json").write_text('{"run_name": "scaling_glm-4.7"}')
    (run_dir / "all_rows.jsonl").write_text('{"kind": "cell"}\n')
    (nested / "prompt_stepk-1.txt").write_text("prompt text")
    (nested / "outputs.jsonl").write_text('{"x": 1}\n')


def test_spool_uploads_preserving_paths_then_prunes(driver, tmp_path):
    """Keys come from the model key, paths are preserved, prune keeps manifest.json."""
    run_dir = tmp_path / "runs" / "some-local-name"
    _populate(run_dir)
    client = FakeS3()

    assert driver.spool_to_s3(run_dir, KEY, client=client) == 4
    assert sorted(key for _, _, key in client.uploads) == sorted(
        f"deduction/runs/scaling_{KEY}/{suffix}" for suffix in (
            "manifest.json", "all_rows.jsonl",
            "theorems/Mini.theoremA/prompt_stepk-1.txt",
            "theorems/Mini.theoremA/outputs.jsonl",
        )
    )
    assert all(bucket == "smolbench-results-414266451290" for _, bucket, _ in client.uploads)

    assert run_dir.is_dir() and (run_dir / "manifest.json").is_file()
    assert not (run_dir / "all_rows.jsonl").exists()
    assert not (run_dir / "theorems").exists()

    # A lane that produced nothing has nothing to spool; that is not a failure.
    assert driver.spool_to_s3(tmp_path / "nope", KEY, client=FakeS3()) == 0


def test_spool_does_not_prune_when_verification_fails(driver, tmp_path):
    """A size mismatch must raise and leave every local file intact."""
    run_dir = tmp_path / "runs" / f"scaling_{KEY}"
    _populate(run_dir)
    client = FakeS3(corrupt_key=f"deduction/runs/scaling_{KEY}/all_rows.jsonl")

    with pytest.raises(RuntimeError) as excinfo:
        driver.spool_to_s3(run_dir, KEY, client=client)
    assert "all_rows.jsonl" in str(excinfo.value)
    assert (run_dir / "all_rows.jsonl").is_file()
    assert (run_dir / "theorems" / "Mini.theoremA" / "outputs.jsonl").is_file()


def test_force_rerun_archives_old_rows_and_disables_resume(tmp_path, monkeypatch):
    """--force-rerun moves all_rows.jsonl aside BEFORE the sweep and passes resume=False."""
    import notebooks.deduction.run_study as rs

    run_dir = tmp_path / "runs" / "scaling_test"
    run_dir.mkdir(parents=True)
    (run_dir / "all_rows.jsonl").write_text('{"kind": "cell", "candidate_proof": "old hardware"}\n')
    seen = {}

    def fake_sweep(config, rd, *, resume=True, verifier=None):
        seen["resume"] = resume
        seen["existed_at_sweep"] = (rd / "all_rows.jsonl").exists()
        return 7

    monkeypatch.setattr(rs.runner, "sweep", fake_sweep)
    monkeypatch.setattr(rs.runner, "results_root", lambda: tmp_path)
    monkeypatch.setattr(rs.ec2, "provision_spot_instance", lambda *a, **k: {})
    monkeypatch.setattr(rs.ec2, "server_config", lambda *a, **k: None)
    monkeypatch.setattr(rs.ec2, "serve_model", lambda k: contextlib.nullcontext())
    monkeypatch.setattr(rs, "select_verifier", lambda: None)
    monkeypatch.setattr(rs, "selected_model", lambda: "test")
    monkeypatch.setattr(rs, "build_config", lambda k: {"run_name": "scaling_test"})
    monkeypatch.setattr(rs, "spool_to_s3", lambda *a, **k: 0)

    rs.main(["--force-rerun", "--no-s3"])

    assert seen["resume"] is False
    assert not seen["existed_at_sweep"], "old rows must be moved aside BEFORE the sweep"
    archived = list(run_dir.glob("all_rows_SUPERSEDED-*.jsonl"))
    assert len(archived) == 1, archived
    assert "old hardware" in archived[0].read_text(), "superseded data must survive"
