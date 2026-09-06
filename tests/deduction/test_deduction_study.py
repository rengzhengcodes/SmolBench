"""Offline tests for notebooks/deduction/run_study.py: StubServer + NullVerifier, fake S3."""

import contextlib
import hashlib
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
#: The committed sweep knobs `build_config` loads and fingerprints.
SWEEP_YAML = NOTEBOOKS / "deduction" / "sweep.yaml"
#: The committed decontamination policy `build_config` also fingerprints.
DECONTAM_TOML = REPO_ROOT / "smolbench" / "deduction" / "lean" / "decontam_config.toml"
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
        "models": cfg["models"],
        # Provenance stamp: the sweep knobs above are no longer a literal in
        # the driver, they are loaded from the committed sweep.yaml, and this
        # records WHICH bytes of that file the run used. Recomputed here from
        # the file rather than pinned as a hex string, so an intentional knob
        # edit does not require touching this test -- what is pinned is that
        # the digest MATCHES the committed file, which is the claim an
        # archived manifest.json makes.
        "sweep_config": {
            "path": "notebooks/deduction/sweep.yaml",
            "sha256": hashlib.sha256(SWEEP_YAML.read_bytes()).hexdigest(),
        },
        # The second provenance stamp: the decontamination policy file's
        # premise stoplist decides which identifiers resolve to premise
        # references, and so what the `hint:3` and `hint:4` rungs -- two of
        # the four rungs this study sweeps -- actually CONTAIN. Unlike
        # `sweep_config` this is COMPUTED from a file the package ships, not
        # read from sweep.yaml, so it is in neither the required nor the
        # reserved key set.
        "decontam_config": {
            "path": "smolbench/deduction/lean/decontam_config.toml",
            "sha256": hashlib.sha256(DECONTAM_TOML.read_bytes()).hexdigest(),
        }}
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
    # 13-05: all_rows.jsonl now SURVIVES the prune. It is the only file resume
    # reads (`runner._existing_keys` and `runner._sanity_done` both parse it);
    # pruning it meant a relaunched lane saw an empty run, re-provisioned a GPU
    # box, re-served the checkpoint and regenerated every cell it had already
    # collected. manifest.json -- which the old docstring claimed resume used --
    # is overwritten by `sweep` before `done_keys` is ever read.
    assert (run_dir / "all_rows.jsonl").is_file()
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


@pytest.mark.parametrize("target_date,ok", [("2026-07-31", True), ("2026-06-03", True),
                                            ("2026-06-02", False), ("2026-04-24", False)])
def test_build_config_gates_target_date_on_roster_latest_release(
        driver, monkeypatch, tmp_path, target_date, ok):
    """T must be at or after the roster's latest release; equality passes (>=)."""
    assert driver.ROSTER_LATEST_RELEASE == "2026-06-03"
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


# ---------------------------------------------------------------------------
# 13-08: the end-to-end sweep with the PRODUCTION knobs on
# ---------------------------------------------------------------------------


def _explicit(cfg, *names):
    """Point `cfg` at named fixture theorems, keeping the corpus gate on."""
    cfg["theorems"] = {"source": "explicit", "full_names": list(names),
                       "kind": "random", "split": "val", "require_postcutoff": True}
    return cfg


def test_end_to_end_sweep_with_production_knobs_skips_the_trivial_rungs(
        driver, sweep_env, stub_server):
    """13-08: with skip_trivial ON, the mini fixture renders only TWO of four rungs.

    `test_end_to_end_sweep_offline` sets ``skip_trivial=False,
    concurrent_gen=False, theorem_workers=1`` before asserting four cells and
    four rungs, while production runs all three the other way -- so the only
    end-to-end sweep in the suite exercised a configuration the study never
    uses, and nothing covered the production path at all.

    With the production values, `Mini.theoremA`'s hint:3 1-hop premise closure
    is EMPTY (neither recorded premise's body names another corpus premise),
    so `is_trivial_rung` drops hint:3 and, with it, noise:3 -- the two rungs
    the study's information-vs-length contrast rests on. That outcome is
    asserted here explicitly rather than left implicit, and
    `test_..._renders_every_rung_when_the_closure_is_non_empty` below shows it
    is a property of THIS fixture, not of the production configuration.
    """
    cfg = _explicit(driver.build_config(KEY), "Mini.theoremA")
    assert (cfg["skip_trivial"], cfg["concurrent_gen"], cfg["theorem_workers"]) \
        == (True, True, 4), "this test is only meaningful on the production knobs"
    run_dir = sweep_env / "runs" / cfg["run_name"]
    written = runner.sweep(cfg, run_dir, verifier=NullVerifier())

    rows = [json.loads(x)
            for x in (run_dir / "all_rows.jsonl").read_text().splitlines()]
    cells = [r for r in rows if r.get("kind") == "cell"]
    assert written == 2, f"expected the two non-trivial rungs, got {written}"
    assert {c["rung"] for c in cells} == {"stepk:1", "hint:2"}
    assert "noise:3" not in {c["rung"] for c in cells}


def _corpus_with_a_transitive_premise(src: Path, dest: Path) -> Path:
    """Copy the post-cutoff fixture, making `Mini.premiseA` cite a THIRD premise.

    `hint:3` renders the 1-hop transitive closure of the next tactic's
    premises, and `premise_dep_closure` EXCLUDES its own seeds -- so a
    non-empty closure needs a premise that is referenced by a seed and is not
    itself a seed. The shipped fixture has none, which is why its hint:3 and
    noise:3 rungs are trivial. This adds `Mini.premiseC` and rewrites
    `Mini.premiseA`'s stored code to name it, which is what
    `premises.referenced_premises` scans (it tokenises `body_with_proof`, and
    with no traced repo that falls back to the corpus's stored `code`).

    Built in `tmp_path` rather than edited in place: the shipped fixture's
    trivial-rung shape is itself pinned by other tests.
    """
    shutil.copytree(src, dest)
    lines = (dest / "corpus.jsonl").read_text().splitlines()
    out = []
    for line in lines:
        rec = json.loads(line)
        if rec["path"] == "Mini/Prem.lean":
            for prem in rec["premises"]:
                if prem["full_name"] == "Mini.premiseA":
                    prem["code"] = ("theorem Mini.premiseA {n : ℕ} (h : P n) : R n := by\n"
                                    "  exact Mini.premiseC h")
            rec["premises"].append({
                "full_name": "Mini.premiseC",
                "code": "theorem Mini.premiseC {n : ℕ} (h : P n) : R n := by\n  simp",
                "start": [20, 1], "end": [21, 20], "kind": "theorem",
            })
        out.append(json.dumps(rec))
    (dest / "corpus.jsonl").write_text("\n".join(out) + "\n")
    return dest


def test_end_to_end_sweep_renders_every_rung_when_the_closure_is_non_empty(
        driver, sweep_env, stub_server, tmp_path, monkeypatch):
    """13-08: noise:3 and hint:3 DO render under skip_trivial, given a real closure.

    The companion to the test above, and the reason that one is not evidence
    that production is broken: on a corpus where the 1-hop closure is
    non-empty, all four production rungs render with `skip_trivial` ON. This
    is also the only test in the suite that renders a NOISE rung through the
    sweep -- the length-control arm the study's headline contrast depends on.
    """
    root = _corpus_with_a_transitive_premise(POSTCUTOFF, tmp_path / "corpus_c")
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(root))
    corpus.reset_caches()
    try:
        cfg = _explicit(driver.build_config(KEY), "Mini.theoremA")
        cfg["run_name"] = "closure"
        run_dir = sweep_env / "runs" / "closure"
        written = runner.sweep(cfg, run_dir, verifier=NullVerifier())
        cells = [json.loads(x) for x in
                 (run_dir / "all_rows.jsonl").read_text().splitlines()
                 if json.loads(x).get("kind") == "cell"]
        assert {c["rung"] for c in cells} == {"stepk:1", "hint:2", "noise:3", "hint:3"}
        assert written == 4
        prompts = sorted(p.name for p in (run_dir / "theorems").rglob("*.md"))
        assert any("noise-3" in n for n in prompts), prompts
    finally:
        corpus.reset_caches()


# ---------------------------------------------------------------------------
# 13-05: no outstanding work -> no box
# ---------------------------------------------------------------------------


def _no_aws(monkeypatch, driver, tmp_path, **extra):
    """Make every billable call a test failure; keep the corpus + results dirs local."""
    monkeypatch.setattr(driver.runner, "results_root", lambda: tmp_path)
    monkeypatch.setattr(driver, "selected_model", lambda: KEY)
    for obj, name in ((driver.ec2, "provision_spot_instance"),
                      (driver.ec2, "serve_model"), (driver, "spool_to_s3")):
        monkeypatch.setattr(obj, name, lambda *a, _n=name, **k: pytest.fail(
            f"{_n} ran although there was no outstanding work"))
    for obj, name, value in extra.get("allow", []):
        monkeypatch.setattr(obj, name, value)


def _sweep_to_completion(driver, sweep_env):
    """Run the production-knob sweep over one fixture theorem; return (cfg, run_dir)."""
    cfg = _explicit(driver.build_config(KEY), "Mini.theoremA")
    run_dir = sweep_env / "runs" / cfg["run_name"]
    assert runner.sweep(cfg, run_dir, verifier=NullVerifier()) > 0
    return cfg, run_dir


def test_a_completed_lane_reports_no_outstanding_cells(driver, sweep_env):
    """13-05: after a full sweep, the outstanding set is EMPTY.

    This is the assertion that makes the fix live rather than dead code. A
    naive `theorems x rungs x models x replicates` product would be 1200
    against the study's 944 actually-rendered cells (`runner.py` records that
    shape: "300 theorems x 4 rungs, unevenly rendered"), so `expected - done`
    would never empty and the no-provision path would never execute. Running
    the REAL sweep to completion and demanding an empty result is the only
    check that catches that.
    """
    cfg, run_dir = _sweep_to_completion(driver, sweep_env)
    assert driver.outstanding_cell_keys(cfg, run_dir) == set()


def test_a_lane_missing_one_cell_reports_exactly_that_cell(driver, sweep_env):
    """13-05, the other direction: the check must still see real remaining work.

    Deleting one cell's rows must surface exactly that key -- not zero (which
    would strand the lane) and not everything (which would defeat the point).
    """
    cfg, run_dir = _sweep_to_completion(driver, sweep_env)
    rows = [json.loads(x)
            for x in (run_dir / "all_rows.jsonl").read_text().splitlines()]
    victim = next(r for r in rows if r.get("kind") == "cell")
    key = (victim["model"], victim["theorem_id"], victim["k"], victim["rung"],
           victim["replicate_idx"])
    (run_dir / "all_rows.jsonl").write_text("".join(
        json.dumps(r) + "\n" for r in rows if r is not victim))
    assert driver.outstanding_cell_keys(cfg, run_dir) == {key}


def test_main_does_not_provision_when_nothing_is_outstanding(
        driver, sweep_env, monkeypatch, tmp_path):
    """13-05: a relaunch of a finished lane must not touch AWS at all.

    `main` had no outstanding-work check (the induction sibling's
    `InductionExperiment.run` does), so relaunching a spooled lane
    re-provisioned a spot box, re-served the checkpoint and regenerated every
    cell -- real money, and the regenerated rows come from a different box
    than the ones they replace.

    The stubs `pytest.fail`, so this checks ORDERING as well as the return
    value: an implementation that provisions first and exits afterwards fails
    here, while one that merely returns 0 would not.
    """
    cfg, run_dir = _sweep_to_completion(driver, sweep_env)
    monkeypatch.setattr(driver.runner, "results_root", lambda: sweep_env)
    monkeypatch.setattr(driver, "selected_model", lambda: KEY)
    # `main` rebuilds its config, and the production `theorems` block draws
    # from a `replay_passing` sidecar the fixture tree does not carry. Hand it
    # back the very config the sweep above ran, so the outstanding-work check
    # is measured against the rows that sweep actually wrote.
    monkeypatch.setattr(driver, "build_config", lambda key: cfg)
    monkeypatch.setattr(driver.runner, "sweep", lambda *a, **k: pytest.fail(
        "swept a lane with no outstanding cells"))
    for obj, name in ((driver.ec2, "provision_spot_instance"),
                      (driver.ec2, "serve_model"), (driver, "spool_to_s3")):
        monkeypatch.setattr(obj, name, lambda *a, _n=name, **k: pytest.fail(
            f"{_n} ran although there was no outstanding work"))
    driver.main([])


def test_force_rerun_provisions_even_with_nothing_outstanding(
        driver, sweep_env, monkeypatch):
    """13-05: `--force-rerun` exists to regenerate everything; it must bypass the check."""
    cfg, run_dir = _sweep_to_completion(driver, sweep_env)
    seen = {}
    monkeypatch.setattr(driver.runner, "results_root", lambda: sweep_env)
    monkeypatch.setattr(driver, "selected_model", lambda: KEY)
    monkeypatch.setattr(driver, "build_config", lambda key: cfg)  # see the test above
    monkeypatch.setattr(driver, "select_verifier", lambda: NullVerifier())
    monkeypatch.setattr(driver.ec2, "provision_spot_instance",
                        lambda *a, **k: seen.setdefault("provisioned", True))
    monkeypatch.setattr(driver.ec2, "server_config", lambda *a, **k: None)
    monkeypatch.setattr(driver.ec2, "serve_model", lambda k: contextlib.nullcontext())
    monkeypatch.setattr(driver.runner, "sweep",
                        lambda *a, **k: seen.setdefault("swept", True) or 0)
    driver.main(["--force-rerun", "--no-s3"])
    assert seen.get("provisioned") and seen.get("swept")


# ---------------------------------------------------------------------------
# 13-18: one seed for the experiment
# ---------------------------------------------------------------------------


def test_lean_seed_drives_both_seeds(driver, postcutoff_corpus, monkeypatch):
    """13-18: LEAN_SEED couples theorem selection and decoding; default 0.

    `theorems.seed` (which theorems are measured, via
    `random.Random(seed).sample`) and `cfg.seed` (the decode seed on the wire,
    replicate `i` at `seed + i`) were independent literals, neither
    env-overridable although five neighbouring knobs are, and their LIBRARY
    defaults disagreed (0 vs 1776). One knob now drives both, so "the
    experiment's seed" means one thing.
    """
    cfg = driver.build_config(KEY)
    assert (cfg["seed"], cfg["theorems"]["seed"]) == (0, 0)
    monkeypatch.setenv("LEAN_SEED", "7")
    cfg = driver.build_config(KEY)
    assert (cfg["seed"], cfg["theorems"]["seed"]) == (7, 7)


def test_a_non_integer_lean_seed_is_refused(driver, postcutoff_corpus, monkeypatch):
    """13-18: a typo'd LEAN_SEED must abort, never silently fall back to 0.

    Falling back would produce a run that looks like the pinned experiment and
    is not -- the failure mode this whole knob exists to prevent.
    """
    monkeypatch.setenv("LEAN_SEED", "abc")
    with pytest.raises(SystemExit):
        driver.build_config(KEY)


# ---------------------------------------------------------------------------
# The import-time tag guard now runs the SHARED structural validation
# (smolbench.evals.experiment.validate_experiment_tag) before its own exact
# lane-identity compare, and the spool bucket/region come from study_config.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tag, expected_phrase", [
    # Bare shared fleet prefix: names every lane at once, and fleet teardown
    # terminates BY TAG. The exact compare would also reject it, but with a
    # message about THIS lane -- the shared validator's diagnosis must win, so
    # the assertion is on the message, not merely on the exit status.
    ("scaling-", "every lane"),
    ("scaling", "every lane"),
    ("periodic-induction", "RETIRED"),
    ("   ", "empty or whitespace-only"),
])
def test_shared_tag_validation_runs_before_the_exact_compare(tag, expected_phrase):
    proc = _run_driver({"EC2_EXPERIMENT_TAG": tag})
    assert proc.returncode != 0, proc.stdout
    assert expected_phrase in proc.stderr, proc.stderr
    assert "is not this lane's tag" not in proc.stderr, (
        "the exact-match message won; the shared structural diagnosis is the "
        f"specific one for {tag!r} and must be what the operator sees:\n{proc.stderr}"
    )


def test_a_neighbouring_lanes_tag_still_gets_the_exact_match_message():
    """The strict-prefix case the shared validator cannot catch.

    ``scaling-glm-4.7-flash`` is a perfectly well-formed, non-retired,
    non-bare-prefix tag, so `validate_experiment_tag` passes it; only this
    driver's own EXACT compare rejects it. Adding the shared call must not have
    replaced that check.
    """
    proc = _run_driver({"EC2_EXPERIMENT_TAG": f"scaling-{KEY}-flash"})
    assert proc.returncode != 0
    assert "is not this lane's tag" in proc.stderr, proc.stderr


def test_spool_bucket_and_region_come_from_the_study_config(driver):
    from smolbench.evals.study_config import load_study_config

    results = load_study_config().results
    assert (driver.SPOOL_BUCKET, driver.SPOOL_REGION) == (results.bucket, results.region)


# ---------------------------------------------------------------------------
# The sweep knobs live in a committed YAML, loaded through the SAME loader the
# `cli run-sweep --config` path uses, and its digest lands in manifest.json.
# ---------------------------------------------------------------------------


def _sweep_yaml_copy(tmp_path, mutate):
    """A scratch copy of the committed sweep.yaml with `mutate` applied to the dict."""
    import yaml

    doc = yaml.safe_load(SWEEP_YAML.read_text())
    mutate(doc)
    path = tmp_path / "sweep.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False))
    return path


def test_sweep_yaml_is_the_only_place_the_knobs_are_written(driver, postcutoff_corpus):
    """No knob value is a literal in the driver any more.

    The point of the move is that a knob tweak is reviewable as a config diff
    rather than being indistinguishable from a logic change. This asserts the
    direction that can regress silently: every knob the config carries must
    come from the file, so a value re-typed into `build_config` would have to
    disagree with it to be detected -- hence the check is that EDITING the file
    changes the config.
    """
    cfg = driver.build_config(KEY)
    loaded, digest = runner.load_sweep_config(SWEEP_YAML)
    for knob in ("temperature", "max_tokens", "request_timeout", "max_retries",
                 "dojo_timeout", "concurrent_gen", "skip_trivial", "k",
                 "n_replicates", "rungs", "theorem_workers", "max_concurrency"):
        assert cfg[knob] == loaded[knob], knob
    for knob in ("source", "limit", "require_postcutoff"):
        assert cfg["theorems"][knob] == loaded["theorems"][knob], knob
    assert cfg["sweep_config"]["sha256"] == digest


def test_an_edited_sweep_yaml_changes_the_config_and_the_digest(
        driver, postcutoff_corpus, tmp_path):
    """A knob edit reaches the config, and the recorded digest moves with it."""
    edited = _sweep_yaml_copy(tmp_path, lambda d: d.__setitem__("max_retries", 9))
    cfg = driver.build_config(KEY, sweep_config_path=edited)
    assert cfg["max_retries"] == 9
    assert cfg["sweep_config"]["sha256"] != driver.build_config(KEY)["sweep_config"]["sha256"]


@pytest.mark.parametrize("mutate, named", [
    (lambda d: d.__setitem__("seed", 7), "seed"),
    (lambda d: d.__setitem__("run_name", "whatever"), "run_name"),
    (lambda d: d.__setitem__("models", []), "models"),
    (lambda d: d["theorems"].__setitem__("shard", "1/3"), "theorems.shard"),
    (lambda d: d["theorems"].__setitem__("seed", 7), "theorems.seed"),
])
def test_a_reserved_key_in_the_sweep_yaml_is_refused_by_name(
        driver, postcutoff_corpus, tmp_path, mutate, named):
    """Per-lane identity written into the file would be SILENTLY overwritten.

    Without this refusal a maintainer could set ``seed: 7`` in the sweep file,
    get seed 0, and have nothing anywhere say why -- the overlay wins and says
    nothing. The assertion is on the NAME in the message, not just the exit:
    a refusal that does not say which key is at fault sends the reader back to
    diffing the very source this change exists to stop them diffing.
    """
    path = _sweep_yaml_copy(tmp_path, mutate)
    with pytest.raises(SystemExit) as excinfo:
        driver.build_config(KEY, sweep_config_path=path)
    assert named in str(excinfo.value), str(excinfo.value)


@pytest.mark.parametrize("dropped", ["max_retries", "dojo_timeout", "rungs"])
def test_a_missing_knob_in_the_sweep_yaml_is_refused_by_name(
        driver, postcutoff_corpus, tmp_path, dropped):
    """An absent key would fall through to runner.sweep's own library default.

    That is the exact silent drift the explicit values exist to prevent
    (`runner.DEFAULT_DOJO_TIMEOUT`'s Design comment spells out the worked
    example), and it would leave nothing in the manifest to reveal it.
    """
    path = _sweep_yaml_copy(tmp_path, lambda d: d.pop(dropped))
    with pytest.raises(SystemExit) as excinfo:
        driver.build_config(KEY, sweep_config_path=path)
    assert dropped in str(excinfo.value), str(excinfo.value)


def test_a_missing_theorems_subkey_is_refused_by_name(driver, postcutoff_corpus, tmp_path):
    path = _sweep_yaml_copy(tmp_path, lambda d: d["theorems"].pop("limit"))
    with pytest.raises(SystemExit) as excinfo:
        driver.build_config(KEY, sweep_config_path=path)
    assert "theorems.limit" in str(excinfo.value), str(excinfo.value)


def test_the_sweep_digest_lands_in_the_run_manifest(driver, sweep_env, stub_server):
    """`runner.sweep` stamps the config verbatim, so the digest reaches manifest.json.

    This is the whole point of the stamp: an ARCHIVED run records which knob
    values it ran under, instead of that being recoverable only by finding the
    driver source at the matching commit.
    """
    cfg = driver.build_config(KEY)
    cfg["theorems"] = {"source": "explicit", "kind": "random", "split": "val",
                       "full_names": ["Mini.theoremA"], "require_postcutoff": True}
    cfg["rungs"] = ["stepk:1"]
    run_dir = sweep_env / "runs" / cfg["run_name"]
    runner.sweep(cfg, run_dir, verifier=NullVerifier())

    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["config"]["sweep_config"] == {
        "path": "notebooks/deduction/sweep.yaml",
        "sha256": hashlib.sha256(SWEEP_YAML.read_bytes()).hexdigest(),
    }


def test_the_cli_run_sweep_path_uses_the_same_loader(tmp_path):
    """One schema, one reader: `cli run-sweep --config` goes through the loader too.

    The issue this closes is that the driver's knobs were a literal dict while
    `cli run-sweep` already defined a config-FILE schema for exactly that dict.
    Two readers would have re-created the split; this pins that a
    non-mapping document is refused by the SAME named check on both paths,
    rather than surfacing as an `AttributeError` inside a sweep that has
    already started.
    """
    from smolbench.deduction.lean import cli

    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    with pytest.raises(ValueError, match=str(empty)):
        runner.load_sweep_config(empty)

    assert cli.cmd_run_sweep.__doc__ and "load_sweep_config" in cli.cmd_run_sweep.__doc__
    config, digest = runner.load_sweep_config(SWEEP_YAML)
    assert isinstance(config, dict)
    assert digest == hashlib.sha256(SWEEP_YAML.read_bytes()).hexdigest()


def test_the_decontam_digest_lands_in_the_run_manifest(driver, sweep_env, stub_server):
    """The stoplist that shaped the prompts is recorded beside the sweep knobs.

    `premises._LEAN_NOISE` decides which identifiers resolve to premise
    references, so `decontam_config.toml` is what the `hint:3`/`hint:4` rungs
    are rendered from. An archived run has to say WHICH stoplist produced its
    prompts, for the same reason it says which knobs it ran under.
    """
    cfg = driver.build_config(KEY)
    cfg["theorems"] = {"source": "explicit", "kind": "random", "split": "val",
                       "full_names": ["Mini.theoremA"], "require_postcutoff": True}
    cfg["rungs"] = ["stepk:1"]
    run_dir = sweep_env / "runs" / cfg["run_name"]
    runner.sweep(cfg, run_dir, verifier=NullVerifier())

    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["config"]["decontam_config"] == {
        "path": "smolbench/deduction/lean/decontam_config.toml",
        "sha256": hashlib.sha256(DECONTAM_TOML.read_bytes()).hexdigest(),
    }


def test_the_stamped_decontam_path_is_the_file_actually_loaded(driver, postcutoff_corpus):
    """The stamp must name the file the loader read, not a re-spelled guess.

    A provenance stamp whose path and digest can disagree is worse than none:
    it asserts a claim about a file nothing verified. This pins them to the
    same source by checking the stamped path resolves to the loader's own.
    """
    from smolbench.deduction.lean.decontam_config import load_decontam_config

    stamp = driver.build_config(KEY)["decontam_config"]
    loaded = load_decontam_config()
    assert (REPO_ROOT / stamp["path"]).resolve() == DECONTAM_TOML.resolve()
    assert stamp["sha256"] == loaded.sha256
