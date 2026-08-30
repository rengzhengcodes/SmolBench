"""Offline tests for notebooks/deduction/run_study.py: StubServer + NullVerifier, fake S3."""

import contextlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from smolbench.deduction.lean import corpus, runner
from smolbench.deduction.lean.nullverify import NullVerifier
from conftest import chat_completion
from tests._paths import (LEAN_MINI as FIXTURE, LEAN_MINI_POSTCUTOFF as POSTCUTOFF,
                         NOTEBOOKS, REPO_ROOT)

DRIVER_PATH = NOTEBOOKS / "deduction" / "run_study.py"
INDUCTION_PATH = NOTEBOOKS / "induction" / "run_study.py"
KEY = "glm-4.7"
IMAGE = "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7"
BUCKET = "smolbench-results-414266451290"
LANE_KEYS = ("EC2_EXPERIMENT_TAG", "EC2_STATE_FILE", "EC2_VLLM_IMAGE", "LEAN_STATE_FILE",
             "SMOLBENCH_LEAN_RESULTS")
#: A fleet-supervisor export: its tag is the lane's own (run_fleet's
#: `Lane.experiment_tag`), the other two are values only it knows.
FLEET = {"EC2_EXPERIMENT_TAG": f"scaling-{KEY}", "EC2_VLLM_IMAGE": "fleet/image:pinned",
         "SMOLBENCH_LEAN_RESULTS": "/tmp/fleet-owned-results"}
#: `build_config`'s locked `theorems` block. `kind`/`split` are the NEW corpus's
#: single `random`/`val` split family (env-overridable); `require_postcutoff`
#: makes `runner._select_theorems` refuse a pre-cutoff pool.
THEOREMS = {"source": "replay_passing", "kind": "random", "split": "val",
            "limit": 300, "seed": 0, "require_postcutoff": True}
#: The old corpus's trace commit, which `build_config` must name when it refuses.
OLD_CORPUS_COMMIT = "fe4454af900584467d21f4fd4fe951d29d9332a7"
#: The re-collection's S3 spool prefix. NOT `deduction/runs`, which holds the
#: published pre-cutoff study and must never be overwritten.
SPOOL_PREFIX = "deduction_postcutoff/runs"
RUN_FILES = {"manifest.json": '{"run_name": "scaling_glm-4.7"}',
             "all_rows.jsonl": '{"kind": "cell"}\n',
             "theorems/Mini.theoremA/prompt_stepk-1.txt": "prompt text",
             "theorems/Mini.theoremA/outputs.jsonl": '{"x": 1}\n'}


def _load_isolated(path: Path, name: str, **env):
    """Exec `path` as module `name`; these files load_dotenv() and read LEAN_* at import."""
    saved = dict(os.environ)
    # Scrub the lane variables the ambient shell may carry (as _run_driver does
    # for its child): a stray EC2_EXPERIMENT_TAG trips the driver's import-time
    # lane guard and every test in this module fails at collection instead.
    for stale in LANE_KEYS + ("LEAN_RUN_NAME", "LEAN_SHARD", "LEAN_CELL_WHITELIST"):
        os.environ.pop(stale, None)
    os.environ.update(env)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module  # must precede exec_module: 3.14 @dataclass needs it
        spec.loader.exec_module(module)
        return module
    finally:
        os.environ.clear()
        os.environ.update(saved)


@pytest.fixture(scope="module")
def driver():
    return _load_isolated(DRIVER_PATH, "deduction_run_study", LEAN_MODEL=KEY)


@pytest.fixture
def postcutoff_corpus(monkeypatch):
    """Repoint the dataset root at the post-cutoff fixture.

    `build_config` validates the corpus at CALL time, so every test that calls
    it needs one -- an unbootstrapped root raises `FileNotFoundError` instead.
    """
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(POSTCUTOFF))
    corpus.reset_caches()
    yield POSTCUTOFF
    corpus.reset_caches()


def test_build_config_locked_overridable_and_unshared(
        driver, postcutoff_corpus, monkeypatch, tmp_path):
    cfg = driver.build_config(KEY)
    assert cfg == {
        "run_name": f"scaling_{KEY}", "seed": 0, "temperature": 0.7, "max_tokens": 32768,
        "request_timeout": 1800, "max_retries": 2, "dojo_timeout": 300,
        "concurrent_gen": True, "skip_trivial": True, "max_concurrency": 8,
        "theorem_workers": 4, "n_replicates": 1, "k": {"strategy": "last"},
        "theorems": THEOREMS, "rungs": ["stepk:1", "hint:2", "noise:3", "hint:3"],
        "models": cfg["models"]}
    before = json.dumps(driver.COT_ARGS[KEY], sort_keys=True)
    cfg["models"][0]["extra_params"]["enable_thinking"] = "CLOBBERED"
    cfg["theorems"]["limit"] = 1
    assert json.dumps(driver.COT_ARGS[KEY], sort_keys=True) == before
    assert driver.build_config(KEY)["theorems"] == THEOREMS
    monkeypatch.setenv("LEAN_RUN_NAME", "scaling_custom")
    assert driver.build_config(KEY)["run_name"] == "scaling_custom"
    monkeypatch.setenv("LEAN_SHARD", "1/3")
    assert driver.build_config(KEY)["run_name"] == "scaling_custom"
    monkeypatch.delenv("LEAN_RUN_NAME")
    cfg = driver.build_config(KEY)
    assert cfg["run_name"] == f"scaling_{KEY}_shard1of3"
    assert cfg["theorems"] == dict(THEOREMS, shard="1/3")
    monkeypatch.delenv("LEAN_SHARD")
    assert driver.build_config(KEY)["run_name"] == f"scaling_{KEY}"
    path = tmp_path / "whitelist.json"
    path.write_text(json.dumps([[KEY, "T", 1, "stepk:1", 0], [KEY, "U", 2, "hint:2", 1]]))
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(path))
    assert driver.build_config(KEY)["cell_whitelist"] == {
        "path": str(path),
        "sha256": runner.hash_cell_keys(runner.load_cell_whitelist(str(path)))}
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(tmp_path / "does_not_exist.json"))
    with pytest.raises(ValueError):
        driver.build_config(KEY)


def test_roster_is_induction_roster_and_lane_key_validated(
        driver, postcutoff_corpus, monkeypatch):
    induction = _load_isolated(INDUCTION_PATH, "induction_run_study_for_deduction")
    sys.modules.pop("induction_run_study_for_deduction", None)
    assert len(driver.MODELS) == 21
    assert driver.MODELS == induction.MODELS
    for key in induction.MODELS:
        assert driver.build_config(key)["models"] == [
            {"provider": "ec2", "model": key, "display_name": key,
             "extra_params": induction.COT_ARGS[key]}], key
    monkeypatch.setenv("LEAN_MODEL", KEY)
    assert driver.selected_model() == KEY
    for value in ("not-a-model", None):
        monkeypatch.delenv("LEAN_MODEL")
        if value is not None:
            monkeypatch.setenv("LEAN_MODEL", value)
        with pytest.raises(SystemExit):
            driver.selected_model()


def test_lane_env_defaults_are_pure_and_anchored(driver, tmp_path):
    import smolbench
    assert driver.REPO_ROOT == Path(smolbench.__file__).resolve().parents[1]
    before = dict(os.environ)
    got = driver.lane_env_defaults(KEY, repo_root=tmp_path)
    assert dict(os.environ) == before, "lane_env_defaults must not touch os.environ"
    assert got == {"EC2_EXPERIMENT_TAG": f"scaling-{KEY}", "EC2_VLLM_IMAGE": IMAGE,
                   "EC2_STATE_FILE": str(tmp_path / f".ec2_state_scaling_{KEY}.json"),
                   "SMOLBENCH_LEAN_RESULTS": str(tmp_path / "notebooks" / "deduction" / "results")}
    again = driver.lane_env_defaults(KEY, repo_root=tmp_path)
    assert again == got and again is not got
    absolute = str(tmp_path / "elsewhere" / "state.json")
    for state_file, want in ((".ec2_state_x.json", str(tmp_path / ".ec2_state_x.json")),
                             (absolute, absolute)):
        assert driver.lane_env_defaults(KEY, repo_root=tmp_path, state_file=state_file) == \
            dict(got, EC2_STATE_FILE=want)


def _run_driver(env: dict, checks: str = ""):
    """Import the driver in a clean interpreter; only a fresh one can witness ordering."""
    child = {k: v for k, v in os.environ.items() if k not in LANE_KEYS}
    child["LEAN_MODEL"] = KEY
    child.update(env)
    code = (
        "import os, sys, importlib.util\n"
        "assert 'smolbench.evals.providers.ec2' not in sys.modules\n"
        f"spec = importlib.util.spec_from_file_location('d', r'{DRIVER_PATH}')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "sys.modules['d'] = m\n"
        "spec.loader.exec_module(m)\n" + checks)
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          cwd=str(REPO_ROOT), timeout=300, env=child)


@pytest.mark.parametrize("env,checks,ok", [
    ({}, "from smolbench.evals.providers import ec2\n"
         f"assert ec2.EC2_EXPERIMENT_TAG == 'scaling-{KEY}', ec2.EC2_EXPERIMENT_TAG\n"
         f"assert ec2.EC2_VLLM_IMAGE == {IMAGE!r}, ec2.EC2_VLLM_IMAGE\n"
         f"assert os.environ['EC2_STATE_FILE'].endswith('.ec2_state_scaling_{KEY}.json')\n"
         "assert os.path.isabs(os.environ['EC2_STATE_FILE'])\n", True),
    (FLEET, "".join(f"assert os.environ[{k!r}] == {v!r}, os.environ[{k!r}]\n"
                    for k, v in FLEET.items()), True),
    ({"EC2_EXPERIMENT_TAG": "scaling-standalone"}, "", False),
    # A NEIGHBOURING lane's tag: rejected only because the guard compares
    # exactly -- "glm-4.7" is a substring of "scaling-glm-4.7-flash".
    ({"EC2_EXPERIMENT_TAG": f"scaling-{KEY}-flash"}, "", False)])
def test_driver_subprocess_env_contract(env, checks, ok):
    proc = _run_driver(env, checks)
    assert (proc.returncode == 0) is ok, f"stdout={proc.stdout}\nstderr={proc.stderr}"


@pytest.fixture
def sweep_env(stub_server, monkeypatch, tmp_path):
    monkeypatch.setenv("EC2_INFERENCE_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("EC2_VLLM_API_KEY", "stub-key")
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(POSTCUTOFF))
    monkeypatch.setenv("SMOLBENCH_LEAN_RESULTS", str(tmp_path))
    stub_server.default_response = chat_completion("```lean\n  simp\n```")
    corpus.reset_caches()
    yield tmp_path
    corpus.reset_caches()


def test_end_to_end_sweep_offline(driver, sweep_env, stub_server):
    def rows(kind):
        raw = (run_dir / "all_rows.jsonl").read_text().splitlines()
        return [r for r in map(json.loads, raw) if r.get("kind") == kind]

    def posts():
        return [r for r in stub_server.requests
                if r.get("body") is not None and r["path"].endswith("/chat/completions")]

    cfg = driver.build_config(KEY)
    # The mini fixture has no replay_passing sidecar; the rest stays locked, and
    # `require_postcutoff` rides along so the sweep exercises the corpus gate.
    cfg["theorems"] = {"source": "explicit", "full_names": ["Mini.theoremA"],
                       "kind": "random", "split": "val", "require_postcutoff": True}
    cfg.update(skip_trivial=False, concurrent_gen=False, theorem_workers=1)
    run_dir = sweep_env / "runs" / cfg["run_name"]
    # one theorem x one k (strategy "last") x 4 rungs x 1 model x 1 replicate
    assert runner.sweep(cfg, run_dir, verifier=NullVerifier()) == 4
    want = {"chat_template_kwargs": driver.COT_ARGS[KEY]["chat_template_kwargs"], "seed": 0,
            "temperature": 0.7, "max_tokens": 32768}
    assert len(posts()) == 4
    assert all({k: p["body"][k] for k in want} == want for p in posts()), posts()
    cells = rows("cell")
    want = {"replicate_idx": 0, "seed": 0, "model": KEY, "provider": "ec2",
            "verdict": "unverified"}
    assert len(cells) == 4
    assert {c["rung"] for c in cells} == {"stepk:1", "hint:2", "noise:3", "hint:3"}
    assert all({k: c[k] for k in want} == want for c in cells), cells
    assert rows("sanity") and all(s["verdict"] == "skipped" for s in rows("sanity"))
    assert runner.sweep(cfg, run_dir, verifier=NullVerifier()) == 0
    assert len(posts()) == 4
    assert len(rows("cell")) == 4


class FakeS3:
    """In-memory stand-in for the boto3 S3 client surface used by spool_to_s3."""

    def __init__(self, corrupt_key=None):
        self.objects, self.uploads, self.corrupt_key = {}, [], corrupt_key

    def upload_file(self, filename, bucket, key):
        self.uploads.append((str(filename), bucket, key))
        self.objects[key] = 1 if key == self.corrupt_key else Path(filename).stat().st_size

    def head_object(self, Bucket, Key):  # noqa: N803 -- boto3's parameter names
        return {"ContentLength": self.objects[Key]}


def test_spool_uploads_preserving_paths_then_prunes(driver, tmp_path):
    def populate(run_dir):
        for rel, text in RUN_FILES.items():
            (run_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            (run_dir / rel).write_text(text)
        return run_dir

    run_dir = populate(tmp_path / "runs" / "some-local-name")
    client = FakeS3()
    assert driver.spool_to_s3(run_dir, KEY, client=client) == 4
    assert sorted(client.uploads, key=lambda u: u[2]) == sorted(
        (str(run_dir / rel), BUCKET, f"{SPOOL_PREFIX}/scaling_{KEY}/{rel}")
        for rel in RUN_FILES)
    assert run_dir.is_dir() and (run_dir / "manifest.json").is_file()
    assert not (run_dir / "all_rows.jsonl").exists()
    assert not (run_dir / "theorems").exists()
    assert driver.spool_to_s3(tmp_path / "nope", KEY, client=FakeS3()) == 0
    run_dir = populate(tmp_path / "runs" / f"scaling_{KEY}")
    with pytest.raises(RuntimeError):
        driver.spool_to_s3(run_dir, KEY,
                           client=FakeS3(f"{SPOOL_PREFIX}/scaling_{KEY}/all_rows.jsonl"))
    assert all((run_dir / rel).is_file() for rel in RUN_FILES)


def test_sharded_lane_refuses_to_spool(driver, postcutoff_corpus, monkeypatch, tmp_path):
    """LEAN_SHARD without --no-s3 exits before any AWS call; with it, the sweep runs."""
    monkeypatch.setenv("LEAN_SHARD", "1/3")
    monkeypatch.setattr(driver.runner, "results_root", lambda: tmp_path)
    monkeypatch.setattr(driver, "selected_model", lambda: KEY)
    monkeypatch.setattr(driver.ec2, "provision_spot_instance",
                        lambda *a, **k: pytest.fail("provisioned before the shard guard"))
    with pytest.raises(SystemExit, match="--no-s3"):
        driver.main([])
    for obj, name, value in ((driver.runner, "sweep", lambda *a, **k: 0),
                             (driver.ec2, "provision_spot_instance", lambda *a, **k: {}),
                             (driver.ec2, "server_config", lambda *a, **k: None),
                             (driver.ec2, "serve_model", lambda k: contextlib.nullcontext()),
                             (driver, "select_verifier", lambda: None),
                             (driver, "spool_to_s3",
                              lambda *a, **k: pytest.fail("spooled a shard"))):
        monkeypatch.setattr(obj, name, value)
    driver.main(["--no-s3"])


def test_force_rerun_archives_old_rows_and_disables_resume(tmp_path, monkeypatch):
    import notebooks.deduction.run_study as rs
    run_dir = tmp_path / "runs" / "scaling_test"
    run_dir.mkdir(parents=True)
    (run_dir / "all_rows.jsonl").write_text('{"kind": "cell", "candidate_proof": "old hardware"}\n')
    seen = {}

    def fake_sweep(config, rd, *, resume=True, verifier=None):
        seen.update(resume=resume, existed=(rd / "all_rows.jsonl").exists())
        return 7

    for obj, name, value in ((rs.runner, "sweep", fake_sweep),
                             (rs.runner, "results_root", lambda: tmp_path),
                             (rs.ec2, "provision_spot_instance", lambda *a, **k: {}),
                             (rs.ec2, "server_config", lambda *a, **k: None),
                             (rs.ec2, "serve_model", lambda k: contextlib.nullcontext()),
                             (rs, "select_verifier", lambda: None),
                             (rs, "selected_model", lambda: "test"),
                             (rs, "build_config",
                              lambda k: {"run_name": "scaling_test", "theorems": {}})):
        monkeypatch.setattr(obj, name, value)
    rs.main(["--force-rerun", "--no-s3"])
    assert seen["resume"] is False
    assert not seen["existed"], "old rows must be moved aside BEFORE the sweep"
    archived = list(run_dir.glob("all_rows_SUPERSEDED-*.jsonl"))
    assert len(archived) == 1, archived
    assert "old hardware" in archived[0].read_text(), "superseded data must survive"


# ---------------------------------------------------------------------------
# The post-cutoff corpus gate (A2): build_config refuses before any AWS call
# ---------------------------------------------------------------------------


def _retarget(tmp_path, **block):
    """Copy the post-cutoff fixture with `metadata.postcutoff` fields overridden."""
    root = tmp_path / "corpus"
    shutil.copytree(POSTCUTOFF, root)
    meta = json.loads((root / "metadata.json").read_text())
    meta["postcutoff"].update(block)
    (root / "metadata.json").write_text(json.dumps(meta, indent=2))
    return root


def test_build_config_refuses_a_pre_cutoff_corpus(driver, monkeypatch):
    """The old 2024-03-24 benchmark is refused, and the refusal names its commit."""
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    corpus.reset_caches()
    with pytest.raises(SystemExit, match=OLD_CORPUS_COMMIT):
        driver.build_config(KEY)
    corpus.reset_caches()


@pytest.mark.parametrize("target_date,ok", [("2026-07-31", True), ("2026-04-24", True),
                                            ("2026-04-23", False), ("2025-12-31", False)])
def test_build_config_gates_target_date_on_roster_latest_release(
        driver, monkeypatch, tmp_path, target_date, ok):
    """T must be at or after the roster's latest release; equality passes (>=)."""
    assert driver.ROSTER_LATEST_RELEASE == "2026-04-24"
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA",
                       str(_retarget(tmp_path, target_date=target_date)))
    corpus.reset_caches()
    if ok:
        assert driver.build_config(KEY)["theorems"]["require_postcutoff"] is True
    else:
        with pytest.raises(SystemExit, match=target_date):
            driver.build_config(KEY)
    corpus.reset_caches()


def test_corpus_kind_and_split_are_env_configurable(driver, postcutoff_corpus, monkeypatch):
    """The new corpus has one `random`/`val` family; the source stays replay_passing."""
    assert (driver.build_config(KEY)["theorems"]["kind"],
            driver.build_config(KEY)["theorems"]["split"]) == ("random", "val")
    monkeypatch.setenv("LEAN_CORPUS_KIND", "novel_premises")
    monkeypatch.setenv("LEAN_CORPUS_SPLIT", "test")
    got = driver.build_config(KEY)["theorems"]
    assert (got["kind"], got["split"], got["source"]) == (
        "novel_premises", "test", "replay_passing")


def test_main_refuses_a_pre_cutoff_corpus_before_provisioning(monkeypatch, tmp_path):
    """`--no-s3` is not a bypass: the corpus gate runs before any billable call."""
    import notebooks.deduction.run_study as rs

    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    corpus.reset_caches()
    monkeypatch.setattr(rs.runner, "results_root", lambda: tmp_path)
    monkeypatch.setattr(rs, "selected_model", lambda: KEY)
    for obj, name in ((rs.ec2, "provision_spot_instance"), (rs.ec2, "serve_model"),
                      (rs.runner, "sweep"), (rs, "spool_to_s3"), (rs, "select_verifier")):
        monkeypatch.setattr(obj, name, lambda *a, _n=name, **k: pytest.fail(
            f"{_n} ran past the corpus gate"))
    for argv in ([], ["--no-s3"], ["--no-s3", "--force-rerun"]):
        with pytest.raises(SystemExit, match=OLD_CORPUS_COMMIT):
            rs.main(argv)
    corpus.reset_caches()


def test_spool_destination_follows_the_env_override(driver, monkeypatch, tmp_path):
    """`LEAN_SPOOL_PREFIX` is read at spool time, so a lane can be redirected."""
    run_dir = tmp_path / "runs" / f"scaling_{KEY}"
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text("{}")
    monkeypatch.setenv("LEAN_SPOOL_PREFIX", "deduction_scratch/runs")
    client = FakeS3()
    assert driver.spool_to_s3(run_dir, KEY, client=client) == 1
    assert client.uploads[0][2] == f"deduction_scratch/runs/scaling_{KEY}/manifest.json"
