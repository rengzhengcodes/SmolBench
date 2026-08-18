"""Offline tests for the deduction (Lean) family-ladder scaling study.

Covers the two new pieces of the deduction lane and nothing else:

* ``notebooks/deduction/run_study.py`` -- the per-lane, generation-only driver.
* ``scripts/lean_verify_rows.py`` -- the deferred, ``.venv-lean``-only
  verification pass.

Everything here runs OFFLINE on BOTH interpreters (the main ``.venv``, Python
3.14 without ``lean_dojo``, and ``.venv-lean``, Python 3.12 with it). No AWS
call, no network, no Lean process. The end-to-end sweep talks to a local
``StubServer`` (the same fixture ``tests/test_lean_runner.py`` uses) and a
``NullVerifier``; the S3 paths are exercised against an injected fake client.

Import hygiene
--------------
Both files under test are loaded BY PATH via ``importlib`` rather than as
packages -- ``notebooks/`` and ``scripts/`` are not importable packages, and
both studies ship a file literally named ``run_study.py``, so a bare
``import run_study`` would be ambiguous about which one it got.

The driver additionally calls ``load_dotenv(keys.env)`` at import time (it
must -- it has to populate the environment before ``smolbench.evals.ec2``
freezes its ``EC2_*`` constants). That mutates this pytest process's
``os.environ`` for the whole session, including credential-shaped variables
other test modules read. The ``driver`` fixture below therefore snapshots
``os.environ`` and restores it IMMEDIATELY after ``exec_module`` returns,
keeping the pollution inside a few microseconds of one fixture rather than
leaking into the rest of the suite. It keeps the post-import snapshot around
so the tests can still assert on what the import DID to the environment.
(``tests/test_induction_study.py`` contains the same fixture for the same
reason; this is a deliberate copy, not shared code, so neither study's test
module can break the other's by editing a common helper.)
"""

from __future__ import annotations

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
from tests.conftest import StubServer, chat_completion

REPO_ROOT = Path(__file__).resolve().parents[1]
DRIVER_PATH = REPO_ROOT / "notebooks" / "deduction" / "run_study.py"
VERIFY_PATH = REPO_ROOT / "scripts" / "lean_verify_rows.py"
INDUCTION_STUDY_PATH = REPO_ROOT / "notebooks" / "induction" / "run_study.py"
FIXTURE = Path(__file__).parent / "fixtures" / "lean_mini"

#: The spec key every single-model test drives. A real key (not a synthetic
#: one) so `COT_ARGS[KEY]` is a real reasoning-toggle payload and the
#: request-body assertions below have something to check.
KEY = "glm-4.7"


# ---------------------------------------------------------------------------
# Module loading
# ---------------------------------------------------------------------------


def _load_by_path(path: Path, name: str):
    """Execute `path` as a module named `name`, registered in ``sys.modules``.

    Parameters
    ----------
    path : Path
        Absolute path to the ``.py`` file to execute.
    name : str
        Private module name to register under.

    Returns
    -------
    ModuleType
        The executed module.

    Notes
    -----
    The ``sys.modules[name] = module`` line before ``exec_module`` is NOT
    optional: on Python 3.14, a ``@dataclass`` declared inside a module that
    is absent from ``sys.modules`` raises ``AttributeError: 'NoneType' object
    has no attribute '__dict__'`` from ``dataclasses._is_type``, because the
    decorator looks its own module up by ``cls.__module__``.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def driver():
    """The deduction driver, imported with ``os.environ`` snapshotted+restored.

    Yields a ``SimpleNamespace``-like module object with an extra attribute
    ``post_import_env`` (a ``dict`` copy of ``os.environ`` taken the instant
    ``exec_module`` returned, before the restore). Tests assert against that
    snapshot rather than the live environment, which by then is clean again.
    """
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


@pytest.fixture(scope="module")
def induction_tables():
    """``MODELS``/``COT_ARGS`` read straight from the induction study.

    Loaded independently of the driver so the "the driver reuses the induction
    table" assertions compare against the real source of truth rather than
    against the driver's own copy of it (which would make the test vacuous).
    """
    saved = dict(os.environ)
    try:
        module = _load_by_path(INDUCTION_STUDY_PATH, "induction_run_study_for_deduction_tests")
    finally:
        os.environ.clear()
        os.environ.update(saved)
    yield module
    sys.modules.pop("induction_run_study_for_deduction_tests", None)


@pytest.fixture(scope="module")
def lvr():
    """``scripts/lean_verify_rows.py``. Pure helpers only -- no Lean, no AWS."""
    module = _load_by_path(VERIFY_PATH, "lean_verify_rows_under_test")
    yield module
    sys.modules.pop("lean_verify_rows_under_test", None)


# ---------------------------------------------------------------------------
# (1) Config pins -- USER-LOCKED values
# ---------------------------------------------------------------------------


def test_config_is_user_locked(driver):
    """Every user-locked sweep-config value, pinned exactly.

    These are not style preferences: `seed` and `n_replicates` fix
    reproducibility and the replication axis, and `theorems` fixes WHICH 300
    theorems every one of the 21 lanes runs. A silent change to any of them
    makes two lanes incomparable, which is the entire point of the study.
    """
    cfg = driver.build_config(KEY)

    assert cfg["run_name"] == f"scaling_{KEY}"
    assert cfg["seed"] == 0
    assert cfg["temperature"] == 0.7
    assert cfg["max_tokens"] == 32768
    assert cfg["request_timeout"] == 1800
    assert cfg["max_retries"] == 2
    assert cfg["dojo_timeout"] == 300
    assert cfg["concurrent_gen"] is True
    assert cfg["skip_trivial"] is True
    assert cfg["k"] == {"strategy": "last"}
    assert cfg["n_replicates"] == 1
    assert cfg["theorem_workers"] == 4
    assert cfg["max_concurrency"] == 8

    # Exact dict equality, not a subset check: an EXTRA key here (say a
    # stray `max_tactics`) would silently change which theorems are drawn.
    assert cfg["theorems"] == {
        "source": "replay_passing",
        "kind": "novel_premises",
        "split": "val",
        "limit": 300,
        "seed": 0,
    }

    # Order matters -- rungs are a difficulty ladder, and the analysis pairs
    # cells on rung identity.
    assert cfg["rungs"] == ["stepk:1", "hint:2", "noise:3", "hint:3"]


def test_config_keys_are_all_accepted_by_the_harness(driver):
    """No config key is silently ignored by ``runner.sweep``.

    A typo'd or renamed key would not raise -- `sweep` reads its config with
    `.get()` and defaults -- so a wrong name degrades silently into the
    harness default. This asserts the driver's key set is a subset of the
    names `sweep` actually reads.
    """
    accepted = {
        "run_name", "seed", "temperature", "max_tokens", "request_timeout",
        "max_retries", "dojo_timeout", "concurrent_gen", "max_concurrency",
        "skip_trivial", "theorem_workers", "k", "n_replicates", "theorems",
        "rungs", "models",
    }
    assert set(driver.build_config(KEY)) <= accepted


def test_run_name_honours_fleet_override(driver, monkeypatch):
    """``LEAN_RUN_NAME`` (exported per lane by the fleet) wins over the default."""
    monkeypatch.setenv("LEAN_RUN_NAME", "scaling_custom")
    assert driver.build_config(KEY)["run_name"] == "scaling_custom"
    monkeypatch.delenv("LEAN_RUN_NAME")
    assert driver.build_config(KEY)["run_name"] == f"scaling_{KEY}"


def test_lean_shard_threads_into_theorems_and_run_name(driver, monkeypatch):
    """``LEAN_SHARD=i/n`` must (a) add ``theorems.shard`` verbatim and (b)
    suffix the DEFAULT run_name so two live shards can never share a run
    directory (concurrent appends from separate processes would interleave
    large rows inside one ``all_rows.jsonl``). An explicit ``LEAN_RUN_NAME``
    still wins verbatim. With LEAN_SHARD unset, ``test_config_is_user_locked``
    above already pins the theorems block to the exact shard-free dict."""
    monkeypatch.setenv("LEAN_SHARD", "1/3")
    cfg = driver.build_config(KEY)
    assert cfg["theorems"]["shard"] == "1/3"
    assert cfg["run_name"] == f"scaling_{KEY}_shard1of3"
    # Everything else in the theorems block stays byte-identical.
    assert {k: v for k, v in cfg["theorems"].items() if k != "shard"} == {
        "source": "replay_passing",
        "kind": "novel_premises",
        "split": "val",
        "limit": 300,
        "seed": 0,
    }
    monkeypatch.setenv("LEAN_RUN_NAME", "scaling_custom")
    assert driver.build_config(KEY)["run_name"] == "scaling_custom"


def test_lean_cell_whitelist_stamps_manifest_sidecar(driver, monkeypatch, tmp_path):
    """``LEAN_CELL_WHITELIST=<path>`` must add a conditional ``cell_whitelist``
    entry (the path + sha256 of the sorted key list) to the returned config --
    mirroring how ``LEAN_SHARD`` stamps ``theorems.shard`` above. Purely
    documentary: ``runner.sweep`` reads ``LEAN_CELL_WHITELIST`` directly from
    the environment itself (see that function's own docstring), so this key
    exists only so a run's ``manifest.json`` sidecar (``sweep`` stamps
    ``{"config": config, ...}`` verbatim) records WHICH whitelist file was in
    effect, without ``runner.sweep`` needing to consume this key at all. With
    ``LEAN_CELL_WHITELIST`` unset, ``test_config_keys_are_all_accepted_by_the_harness``
    above already pins that this key is absent from the returned config."""
    whitelist_path = tmp_path / "whitelist.json"
    keys = [[KEY, "T", 1, "stepk:1", 0], [KEY, "U", 2, "hint:2", 1]]
    whitelist_path.write_text(json.dumps(keys))
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(whitelist_path))

    cfg = driver.build_config(KEY)
    assert cfg["cell_whitelist"]["path"] == str(whitelist_path)
    expected_sha = runner.hash_cell_keys(runner.load_cell_whitelist(str(whitelist_path)))
    assert cfg["cell_whitelist"]["sha256"] == expected_sha
    # Everything else in the config is untouched by the whitelist.
    assert cfg["run_name"] == f"scaling_{KEY}"
    assert cfg["theorems"] == {
        "source": "replay_passing",
        "kind": "novel_premises",
        "split": "val",
        "limit": 300,
        "seed": 0,
    }


def test_lean_cell_whitelist_missing_file_raises_before_provisioning(driver, monkeypatch, tmp_path):
    """A missing/malformed whitelist must raise `ValueError` out of
    ``build_config`` itself -- BEFORE any AWS call, matching this driver's
    "fail fast before billing" pattern (module docstring, LIFECYCLE step 3;
    ``main`` calls ``build_config`` before ``select_verifier``/provisioning)."""
    monkeypatch.setenv("LEAN_CELL_WHITELIST", str(tmp_path / "does_not_exist.json"))
    with pytest.raises(ValueError):
        driver.build_config(KEY)


def test_build_config_does_not_mutate_shared_cot_table(driver):
    """Mutating a returned config must not corrupt the shared ``COT_ARGS`` table.

    `build_config` is called once per process today, but the table it draws
    from is module-global and shared with the induction study's module object;
    handing out a live reference would let one caller's edit leak into every
    later config in the same kernel (notably a notebook kernel, where several
    configs are built in one session).
    """
    before = json.dumps(driver.COT_ARGS[KEY], sort_keys=True)
    cfg = driver.build_config(KEY)
    cfg["models"][0]["extra_params"]["enable_thinking"] = "CLOBBERED"
    cfg["theorems"]["limit"] = 1
    assert json.dumps(driver.COT_ARGS[KEY], sort_keys=True) == before
    assert driver.build_config(KEY)["theorems"]["limit"] == 300


# ---------------------------------------------------------------------------
# (2) COT_ARGS identity across all 21 keys
# ---------------------------------------------------------------------------


def test_models_table_is_the_induction_table(driver, induction_tables):
    """The driver reuses the induction roster rather than duplicating it."""
    assert driver.MODELS == induction_tables.MODELS
    assert driver.COT_ARGS == induction_tables.COT_ARGS
    assert len(driver.MODELS) == 21
    assert set(driver.COT_ARGS) == set(driver.MODELS)


def test_extra_params_is_the_induction_cot_entry_for_all_21_keys(driver, induction_tables):
    """Per-model ``extra_params`` IS the induction table's entry, for every key.

    This is the cross-study coupling that matters: the deduction lane must
    switch reasoning on for exactly the same checkpoints, with exactly the
    same kwarg names, as the induction lane. DeepSeek uses `thinking` where
    everyone else uses `enable_thinking`, and the three Ministral entries are
    deliberately empty (their think protocol arrives via an injected system
    prompt) -- all of which this catches if it ever drifts.
    """
    for key in induction_tables.MODELS:
        models = driver.build_config(key)["models"]
        assert len(models) == 1, f"{key}: expected exactly one model config"
        mc = models[0]
        assert mc["provider"] == "ec2"
        assert mc["model"] == key
        assert mc["display_name"] == key
        assert mc["extra_params"] == induction_tables.COT_ARGS[key], key


# ---------------------------------------------------------------------------
# (3) Environment derivation + import ordering
# ---------------------------------------------------------------------------


def test_repo_root_path_arithmetic(driver):
    """``REPO_ROOT`` resolves to the real repo root.

    Path arithmetic (`parents[2]`) silently returns SOME directory no matter
    how wrong the count is, so this compares against a root derived a
    completely different way -- from the installed `smolbench` package -- and
    checks a landmark file actually lives there.
    """
    import smolbench

    expected = Path(smolbench.__file__).resolve().parents[1]
    assert driver.REPO_ROOT == expected
    assert (driver.REPO_ROOT / "pyproject.toml").is_file()
    assert (driver.REPO_ROOT / "notebooks" / "deduction").is_dir()


def test_lane_env_defaults_values_and_purity(driver, tmp_path):
    """``lane_env_defaults`` is pure and derives the fleet-compatible names.

    The tag and state-file names are a CONTRACT with ``scripts/run_fleet.py``
    (which builds ``scaling-<key>`` / ``.ec2_state_scaling_<key>.json``
    independently); if these drift, a deduction lane provisions a second box
    instead of reattaching to the one the induction phase already paid for.
    """
    before = dict(os.environ)
    got = driver.lane_env_defaults(KEY, repo_root=tmp_path)
    assert dict(os.environ) == before, "lane_env_defaults must not touch os.environ"

    assert got["EC2_EXPERIMENT_TAG"] == f"scaling-{KEY}"
    assert got["EC2_STATE_FILE"] == str(tmp_path / f".ec2_state_scaling_{KEY}.json")
    # Digest-pinned since the 2026-08-18 determinism change (was the mutable
    # "vllm/vllm-openai:nightly" tag before it) -- see ec2.py's own
    # EC2_VLLM_IMAGE comment for the full provenance.
    assert got["EC2_VLLM_IMAGE"] == (
        "vllm/vllm-openai@sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7"
    )
    assert got["SMOLBENCH_LEAN_RESULTS"] == str(tmp_path / "notebooks" / "deduction" / "results")

    again = driver.lane_env_defaults(KEY, repo_root=tmp_path)
    assert again == got and again is not got


def test_lane_env_defaults_resolves_bare_state_filename_against_repo_root(driver, tmp_path):
    """A bare ``LEAN_STATE_FILE`` resolves against the repo root, not the cwd.

    The fleet exports ``LEAN_STATE_FILE=.ec2_state_scaling_<key>.json`` -- a
    bare NAME. Resolving that relative to the subprocess's cwd would point at
    a different (usually nonexistent) file, and the lane would provision a
    fresh box instead of reattaching. An absolute override passes through
    untouched.
    """
    bare = driver.lane_env_defaults(KEY, repo_root=tmp_path, state_file=".ec2_state_x.json")
    assert bare["EC2_STATE_FILE"] == str(tmp_path / ".ec2_state_x.json")
    assert Path(bare["EC2_STATE_FILE"]).is_absolute()

    absolute = str(tmp_path / "elsewhere" / "state.json")
    got = driver.lane_env_defaults(KEY, repo_root=tmp_path, state_file=absolute)
    assert got["EC2_STATE_FILE"] == absolute


def test_import_sets_env_before_ec2_freezes_it():
    """The pre-import ``setdefault`` block beats ``ec2``'s import-time freeze.

    ``smolbench.evals.ec2`` binds ``EC2_EXPERIMENT_TAG`` (and
    ``EC2_VLLM_IMAGE``) as MODULE CONSTANTS at import time, so a tag exported
    after that import is silently ignored and the lane tags its instance
    wrongly -- which in turn means it never finds the box again, and the
    fleet's reattach/teardown both miss it.

    This runs in a FRESH SUBPROCESS deliberately. Asserting on
    ``ec2.EC2_EXPERIMENT_TAG`` inside the pytest process would prove nothing:
    some earlier test may already have imported ``ec2``, freezing the constant
    long before the driver ever ran. Only a clean interpreter can witness the
    ordering.
    """
    code = (
        "import os, sys, importlib.util\n"
        "os.environ['LEAN_MODEL'] = 'glm-4.7'\n"
        "for junk in ('EC2_EXPERIMENT_TAG', 'EC2_STATE_FILE', 'LEAN_STATE_FILE'):\n"
        "    os.environ.pop(junk, None)\n"
        "assert 'smolbench.evals.ec2' not in sys.modules\n"
        f"spec = importlib.util.spec_from_file_location('d', r'{DRIVER_PATH}')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "sys.modules['d'] = m\n"
        "spec.loader.exec_module(m)\n"
        "from smolbench.evals import ec2\n"
        "assert ec2.EC2_EXPERIMENT_TAG == 'scaling-glm-4.7', ec2.EC2_EXPERIMENT_TAG\n"
        "assert ec2.EC2_VLLM_IMAGE == ("
        "'vllm/vllm-openai@sha256:"
        "26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7'"
        "), ec2.EC2_VLLM_IMAGE\n"
        "assert os.environ['EC2_STATE_FILE'].endswith('.ec2_state_scaling_glm-4.7.json')\n"
        "assert os.path.isabs(os.environ['EC2_STATE_FILE'])\n"
        "print('ORDERING-OK')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "ORDERING-OK" in proc.stdout


def test_fleet_exported_env_wins_over_driver_defaults():
    """Every driver default is a ``setdefault``, so the supervisor's value wins.

    Under ``scripts/run_fleet.py`` the supervisor materialises a per-lane
    environment before invoking this driver. If the driver used bare
    assignment anywhere, it would clobber the supervisor's per-lane tag and
    two lanes could converge on ONE box, each swapping the served checkpoint
    out from under the other mid-run.
    """
    code = (
        "import os, sys, importlib.util\n"
        "os.environ['LEAN_MODEL'] = 'glm-4.7'\n"
        # Names the lane: the driver refuses a tag that does not, because a
        # tag shared across lanes is exactly how two lanes converge on one box.
        "os.environ['EC2_EXPERIMENT_TAG'] = 'fleet-owned-glm-4.7'\n"
        "os.environ['EC2_VLLM_IMAGE'] = 'fleet/image:pinned'\n"
        "os.environ['SMOLBENCH_LEAN_RESULTS'] = '/tmp/fleet-owned-results'\n"
        f"spec = importlib.util.spec_from_file_location('d', r'{DRIVER_PATH}')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "sys.modules['d'] = m\n"
        "spec.loader.exec_module(m)\n"
        "assert os.environ['EC2_EXPERIMENT_TAG'] == 'fleet-owned-glm-4.7'\n"
        "assert os.environ['EC2_VLLM_IMAGE'] == 'fleet/image:pinned'\n"
        "assert os.environ['SMOLBENCH_LEAN_RESULTS'] == '/tmp/fleet-owned-results'\n"
        "print('SETDEFAULT-OK')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "SETDEFAULT-OK" in proc.stdout


def test_selected_model_rejects_unknown_and_missing(driver, monkeypatch):
    """``LEAN_MODEL`` must name one of the 21 study keys."""
    monkeypatch.setenv("LEAN_MODEL", KEY)
    assert driver.selected_model() == KEY

    monkeypatch.setenv("LEAN_MODEL", "not-a-model")
    with pytest.raises(SystemExit) as excinfo:
        driver.selected_model()
    assert "not-a-model" in str(excinfo.value)

    monkeypatch.delenv("LEAN_MODEL")
    with pytest.raises(SystemExit):
        driver.selected_model()


def test_no_rollout_terminology():
    """The repo migrated off "rollout"; the replication axis is "replicates"."""
    for path in (DRIVER_PATH, VERIFY_PATH):
        assert "rollout" not in path.read_text().lower(), path


# ---------------------------------------------------------------------------
# (4) End-to-end offline sweep against a stub server
# ---------------------------------------------------------------------------


@pytest.fixture
def stub():
    """One OpenAI-compatible stub server the ``ec2`` provider is pointed at."""
    server = StubServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture
def sweep_env(stub, monkeypatch, tmp_path):
    """Point the ``ec2`` provider at `stub` and the corpus at the mini fixture.

    ``EC2_INFERENCE_BASE_URL`` + ``EC2_VLLM_API_KEY`` are the provider's
    documented test overrides (see ``ec2._connection``): with both set it
    never reads the state file, so no AWS call and no provisioned instance is
    involved anywhere in this test.
    """
    monkeypatch.setenv("EC2_INFERENCE_BASE_URL", stub.base_url)
    monkeypatch.setenv("EC2_VLLM_API_KEY", "stub-key")
    monkeypatch.setenv("SMOLBENCH_LEAN_DATA", str(FIXTURE))
    monkeypatch.setenv("SMOLBENCH_LEAN_RESULTS", str(tmp_path))
    stub.default_response = chat_completion("```lean\n  simp\n```")
    corpus.reset_caches()
    yield tmp_path
    corpus.reset_caches()


def _explicit_config(driver, key=KEY):
    """The driver's real config, retargeted at the two-theorem mini fixture.

    Only the `theorems` block is swapped (the fixture has no
    `replay_passing`/`novel_premises` sidecar). Every other locked value --
    seed, rungs, replicates, temperature -- is exercised exactly as the real
    lane would run it; the `theorems` block itself is pinned separately by
    ``test_config_is_user_locked``.
    """
    cfg = driver.build_config(key)
    cfg["theorems"] = {
        "source": "explicit",
        "full_names": ["Mini.theoremA"],
        "kind": "random",
        "split": "val",
    }
    cfg["skip_trivial"] = False  # deterministic cell count on the tiny fixture
    cfg["concurrent_gen"] = False
    cfg["theorem_workers"] = 1
    return cfg


def _cells(run_dir):
    rows = [json.loads(x) for x in (run_dir / "all_rows.jsonl").read_text().splitlines()]
    return [r for r in rows if r.get("kind") == "cell"]


def _chat_posts(stub):
    return [
        r for r in stub.requests
        if r.get("body") is not None and r["path"].endswith("/chat/completions")
    ]


def test_end_to_end_sweep_offline(driver, sweep_env, stub):
    """A full sweep runs offline: right request bodies, right rows, resume skips."""
    cfg = _explicit_config(driver)
    run_dir = sweep_env / "runs" / cfg["run_name"]

    written = runner.sweep(cfg, run_dir, verifier=NullVerifier())

    # one theorem x one k (strategy "last") x 4 rungs x 1 model x 1 replicate
    assert written == 4

    posts = _chat_posts(stub)
    assert len(posts) == 4
    for req in posts:
        body = req["body"]
        # The reasoning toggle must reach the wire, unwrapped, per model.
        assert body["chat_template_kwargs"] == driver.COT_ARGS[KEY]["chat_template_kwargs"]
        # seed is reproducibility-critical: base seed 0 + replicate_idx 0.
        assert body["seed"] == 0
        assert body["temperature"] == 0.7
        assert body["max_tokens"] == 32768

    cells = _cells(run_dir)
    assert len(cells) == 4
    assert {c["rung"] for c in cells} == {"stepk:1", "hint:2", "noise:3", "hint:3"}
    for row in cells:
        assert row["replicate_idx"] == 0
        assert row["seed"] == 0
        assert row["model"] == KEY
        assert row["provider"] == "ec2"
        # NullVerifier defers every judgement to the later real pass.
        assert row["verdict"] == "unverified"

    # The sanity gate is deferred too, and must NOT suppress cell generation.
    rows = [json.loads(x) for x in (run_dir / "all_rows.jsonl").read_text().splitlines()]
    sanity = [r for r in rows if r.get("kind") == "sanity"]
    assert sanity and all(s["verdict"] == "skipped" for s in sanity)

    # Resume: a second identical call re-writes nothing and re-requests nothing.
    before = len(_chat_posts(stub))
    assert runner.sweep(cfg, run_dir, verifier=NullVerifier()) == 0
    assert len(_chat_posts(stub)) == before
    assert len(_cells(run_dir)) == 4


def test_noise_rung_is_token_matched_to_its_hint_counterpart():
    """``noise:3`` matches ``hint:3``'s token count EXACTLY, on the real corpus.

    This is the whole basis of the noise arm: it is a pure LENGTH control, so
    any difference between `hint:3` and `noise:3` scores must come from the
    hint's content, not from prompt length.

    The theorem is chosen as the first one whose `hint:3` is strictly longer
    than `hint:2`, and that strictness is ASSERTED. Without it the test would
    pass vacuously on any theorem where `hint:3` adds nothing: the padding
    path short-circuits, `noise:3` is returned as a byte-identical copy of the
    baseline, and "the token counts match" would be true for a reason that has
    nothing to do with the padding logic under test.
    """
    from smolbench.deduction.lean import context

    corpus.reset_caches()
    chosen = None
    for theorem in list(corpus.iter_replay_passing("novel_premises", "val"))[:60]:
        k = len(theorem.traced_tactics) - 1
        hint2 = context._count_tokens(context.render(theorem, k, "hint", 2).text)
        hint3 = context._count_tokens(context.render(theorem, k, "hint", 3).text)
        if hint3 > hint2:
            chosen = (theorem, k, hint3)
            break

    assert chosen is not None, "no theorem exercised the noise padding path"
    theorem, k, hint3_tokens = chosen
    noise3_tokens = context._count_tokens(context.render(theorem, k, "noise", 3).text)
    assert noise3_tokens == hint3_tokens, (
        f"{theorem.full_name} k={k}: noise:3 is {noise3_tokens} tokens but "
        f"hint:3 is {hint3_tokens}"
    )


# ---------------------------------------------------------------------------
# (5) lean_verify_rows -- pure units
# ---------------------------------------------------------------------------


def _cell(theorem, k, rung, verdict, candidate, replicate_idx=0):
    return {
        "kind": "cell", "theorem_id": theorem, "k": k, "rung": rung,
        "model": KEY, "replicate_idx": replicate_idx, "seed": 0,
        "candidate_proof": candidate, "verdict": verdict,
    }


def test_group_unverified_groups_by_theorem_and_k(lvr):
    """Only ``unverified`` CELL rows are grouped, keyed by (theorem, k)."""
    rows = [
        _cell("T.a", 1, "stepk:1", "unverified", "simp"),
        _cell("T.a", 1, "hint:2", "unverified", "ring"),
        _cell("T.a", 2, "stepk:1", "unverified", "simp"),
        _cell("T.b", 0, "stepk:1", "unverified", "rfl"),
        # already verified, and a non-cell row: both excluded
        _cell("T.a", 1, "hint:3", "success", "aesop"),
        {"kind": "sanity", "theorem_id": "T.a", "verdict": "skipped"},
    ]
    groups = lvr.group_unverified(rows)
    assert list(groups) == [("T.a", 1), ("T.a", 2), ("T.b", 0)]
    assert groups[("T.a", 1)] == [0, 1]
    assert groups[("T.a", 2)] == [2]
    assert groups[("T.b", 0)] == [3]


def test_group_unverified_coerces_k_to_int(lvr):
    """``k`` arrives from JSON and must key as an int, not a str."""
    groups = lvr.group_unverified([_cell("T.a", "3", "stepk:1", "unverified", "simp")])
    assert list(groups) == [("T.a", 3)]


def test_unique_candidates_dedups_and_fans_out(lvr):
    """Identical candidate strings replay once; the verdict reaches every row.

    Lean replay is deterministic, so two rows carrying byte-identical
    candidate text cannot disagree -- collapsing them is what makes the pass
    affordable. The fan-out is the other half of that bargain: skipping it
    would leave duplicate rows still marked `unverified`.
    """
    rows = [
        _cell("T.a", 1, "stepk:1", "unverified", "simp"),
        _cell("T.a", 1, "hint:2", "unverified", "ring"),
        _cell("T.a", 1, "hint:3", "unverified", "simp"),
    ]
    uniq = lvr.unique_candidates(rows, [0, 1, 2])
    assert list(uniq) == ["simp", "ring"]
    assert uniq["simp"] == [0, 2]
    assert uniq["ring"] == [1]

    lvr.fan_out_verdict(rows, uniq["simp"], {
        "verdict": "success", "lean_error": None,
        "final_state_pp": None, "verify_ms": 12,
    })
    assert rows[0]["verdict"] == "success" and rows[2]["verdict"] == "success"
    assert rows[0]["verify_ms"] == 12 and rows[2]["verify_ms"] == 12
    # untouched row keeps its placeholder, and identity fields survive
    assert rows[1]["verdict"] == "unverified"
    assert rows[0]["seed"] == 0 and rows[0]["rung"] == "stepk:1"


def test_unique_candidates_treats_missing_candidate_as_empty(lvr):
    rows = [{"kind": "cell", "theorem_id": "T.a", "k": 0, "verdict": "unverified"}]
    assert list(lvr.unique_candidates(rows, [0])) == [""]


def test_resume_done_groups(lvr):
    """A resumed pass skips groups that already carry a real verdict."""
    verified = [
        _cell("T.a", 1, "stepk:1", "success", "simp"),
        _cell("T.b", 0, "stepk:1", "unverified", "rfl"),
        {"kind": "sanity", "theorem_id": "T.a", "verdict": "success"},
    ]
    assert lvr.resume_done_groups(verified) == {("T.a", 1)}


def test_available_ram_and_worker_cap(lvr):
    """RAM parsing and the worker cap read a SUPPLIED meminfo, never the host's.

    Reading the real ``/proc/meminfo`` here would make the assertion depend on
    whatever else is running on the machine -- green on a big box, red in CI,
    for reasons that have nothing to do with the code.
    """
    meminfo = "MemTotal:       65788432 kB\nMemAvailable:   12582912 kB\nSwapFree: 0 kB\n"
    assert lvr.available_ram_gb(meminfo) == pytest.approx(12.0)
    assert lvr.max_workers_allowed(meminfo) == 2

    with pytest.raises(ValueError):
        lvr.available_ram_gb("MemTotal: 100 kB\n")


def test_check_workers_refuses_oversubscription(lvr):
    """Oversubscribing gets the pass OOM-killed hours in -- refuse up front."""
    meminfo = "MemAvailable:   12582912 kB\n"  # 12 GiB -> cap 2
    lvr.check_workers(1, meminfo)
    lvr.check_workers(2, meminfo)
    with pytest.raises(SystemExit) as excinfo:
        lvr.check_workers(3, meminfo)
    message = str(excinfo.value)
    assert "3" in message and "2" in message

    with pytest.raises(SystemExit):
        lvr.check_workers(0, meminfo)


def test_s3_path_mapping(lvr):
    """URI parsing and key construction -- the run layout is a fleet contract."""
    assert lvr.parse_s3_uri("s3://bucket/deduction/runs") == ("bucket", "deduction/runs")
    assert lvr.parse_s3_uri("s3://bucket/deduction/runs/") == ("bucket", "deduction/runs")
    assert lvr.parse_s3_uri("s3://bucket") == ("bucket", "")
    for bad in ("bucket/key", "s3://", "https://bucket/key"):
        with pytest.raises(ValueError):
            lvr.parse_s3_uri(bad)

    key = lvr.run_object_key("deduction/runs", "scaling_glm-4.7", "verified_rows.jsonl")
    assert key == "deduction/runs/scaling_glm-4.7/verified_rows.jsonl"
    assert "//" not in key and not key.startswith("/")


def test_require_py312_matches_interpreter(lvr):
    """The real verifier needs ``lean_dojo``, which pins ``python<3.13``."""
    if sys.version_info >= (3, 13):
        with pytest.raises(SystemExit) as excinfo:
            lvr.require_py312()
        assert ".venv-lean" in str(excinfo.value)
    else:
        assert lvr.require_py312() is None


def test_verify_module_imports_without_lean_dojo():
    """``lean_verify_rows`` must import on an interpreter with no ``lean_dojo``.

    Its pure helpers are unit-tested on both venvs, and an operator inspects
    ``--dry-run`` from the main venv. A module-scope ``import ...verify``
    would make both impossible.
    """
    code = (
        "import sys, importlib.util\n"
        f"spec = importlib.util.spec_from_file_location('lvr', r'{VERIFY_PATH}')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "sys.modules['lvr'] = m\n"
        "spec.loader.exec_module(m)\n"
        "assert 'smolbench.deduction.lean.verify' not in sys.modules\n"
        "assert 'boto3' not in sys.modules\n"
        "print('LAZY-OK')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "LAZY-OK" in proc.stdout


# ---------------------------------------------------------------------------
# (6) S3 spool: upload, verify, prune
# ---------------------------------------------------------------------------


class FakeS3:
    """Minimal in-memory stand-in for the boto3 S3 client surface used here."""

    def __init__(self, *, corrupt_key: str | None = None):
        self.objects: dict[str, int] = {}
        self.uploads: list[tuple[str, str, str]] = []
        self.corrupt_key = corrupt_key

    def upload_file(self, filename, bucket, key):
        size = Path(filename).stat().st_size
        self.uploads.append((str(filename), bucket, key))
        # Simulate a truncated upload for the failure-path test.
        self.objects[key] = 1 if key == self.corrupt_key else size

    def head_object(self, Bucket, Key):  # noqa: N803 -- boto3's parameter names
        if Key not in self.objects:
            raise KeyError(Key)
        return {"ContentLength": self.objects[Key]}


def _populate(run_dir: Path):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text('{"run_name": "scaling_glm-4.7"}')
    (run_dir / "all_rows.jsonl").write_text('{"kind": "cell"}\n')
    nested = run_dir / "theorems" / "Mini.theoremA"
    nested.mkdir(parents=True)
    (nested / "prompt_stepk-1.txt").write_text("prompt text")
    (nested / "outputs.jsonl").write_text('{"x": 1}\n')


def test_spool_uploads_preserving_paths_then_prunes(driver, tmp_path):
    """Upload preserves relative paths; prune keeps only ``manifest.json``.

    ``manifest.json`` stays behind on purpose: it is the run's config record,
    and leaving it is what lets a later resume recognise the run exists
    without re-downloading the whole spool from S3 just to check.
    """
    run_dir = tmp_path / "runs" / f"scaling_{KEY}"
    _populate(run_dir)
    client = FakeS3()

    uploaded = driver.spool_to_s3(run_dir, KEY, client=client)

    assert uploaded == 4
    keys = sorted(key for _, _, key in client.uploads)
    assert keys == sorted([
        f"deduction/runs/scaling_{KEY}/manifest.json",
        f"deduction/runs/scaling_{KEY}/all_rows.jsonl",
        f"deduction/runs/scaling_{KEY}/theorems/Mini.theoremA/prompt_stepk-1.txt",
        f"deduction/runs/scaling_{KEY}/theorems/Mini.theoremA/outputs.jsonl",
    ])
    assert all(bucket == "smolbench-results-414266451290" for _, bucket, _ in client.uploads)

    # Pruned: everything gone except the manifest; run_dir itself survives.
    assert run_dir.is_dir()
    assert (run_dir / "manifest.json").is_file()
    assert not (run_dir / "all_rows.jsonl").exists()
    assert not (run_dir / "theorems").exists()


def test_spool_uses_the_model_key_not_the_directory_name(driver, tmp_path):
    """The destination prefix comes from the model key, not ``run_dir.name``."""
    run_dir = tmp_path / "runs" / "some-local-name"
    _populate(run_dir)
    client = FakeS3()
    driver.spool_to_s3(run_dir, KEY, client=client)
    assert all(key.startswith(f"deduction/runs/scaling_{KEY}/") for _, _, key in client.uploads)


def test_spool_does_not_prune_when_verification_fails(driver, tmp_path):
    """A size mismatch must raise and leave every local file intact.

    Pruning is irreversible and the local tree is the only other copy. If the
    head_object check disagrees with the local size, the upload did not land
    and deleting would destroy the run.
    """
    run_dir = tmp_path / "runs" / f"scaling_{KEY}"
    _populate(run_dir)
    client = FakeS3(corrupt_key=f"deduction/runs/scaling_{KEY}/all_rows.jsonl")

    with pytest.raises(RuntimeError) as excinfo:
        driver.spool_to_s3(run_dir, KEY, client=client)
    assert "all_rows.jsonl" in str(excinfo.value)

    assert (run_dir / "all_rows.jsonl").is_file()
    assert (run_dir / "theorems" / "Mini.theoremA" / "outputs.jsonl").is_file()


def test_spool_missing_run_dir_is_not_an_error(driver, tmp_path):
    """A lane that produced nothing has nothing to spool -- not a failure."""
    client = FakeS3()
    assert driver.spool_to_s3(tmp_path / "nope", KEY, client=client) == 0
    assert client.uploads == []


def test_driver_refuses_a_tag_that_does_not_name_its_lane():
    """A tag shared across lanes must abort the run, not start a box.

    ``setdefault`` means an exported EC2_EXPERIMENT_TAG wins -- correct for a
    supervisor, catastrophic when the value is shared. keys.env ships
    ``EC2_EXPERIMENT_TAG=scaling-standalone`` as a standalone default, and a
    launcher sourcing it with ``set -a`` exports that into every lane; boxes
    are then discovered by tag (``_recover_tagged_instance``) and the second
    lane adopts the first lane's instance, serving its own model on top. Three
    lanes converged on one g6e.12xlarge this way on 2026-08-14.
    """
    code = (
        "import os, sys, importlib.util\n"
        "os.environ['LEAN_MODEL'] = 'glm-4.7'\n"
        "os.environ['EC2_EXPERIMENT_TAG'] = 'scaling-standalone'\n"
        f"spec = importlib.util.spec_from_file_location('d', r'{DRIVER_PATH}')\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "sys.modules['d'] = m\n"
        "spec.loader.exec_module(m)\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300,
    )
    assert proc.returncode != 0, "a shared tag must abort, not proceed"
    assert "does not name this lane" in proc.stderr
    assert "scaling-glm-4.7" in proc.stderr, "error must state the fix"


def test_force_rerun_archives_old_rows_and_disables_resume(tmp_path, monkeypatch):
    """--force-rerun must move all_rows.jsonl aside AND pass resume=False.

    Both halves matter. resume=False alone regenerates every cell but still
    APPENDS, leaving the superseded row and the fresh row for each key in one
    file on different hardware, distinguishable only by line order -- which is
    the very confound the flag exists to remove. Archiving alone would leave
    resume skipping every cell that already has content, so nothing would be
    regenerated at all.

    The archive is written INSIDE run_dir so spool_to_s3 carries it to S3 under
    its own key: superseded data is preserved and labelled, never dropped.
    """
    import notebooks.deduction.run_study as rs

    run_dir = tmp_path / "runs" / "scaling_test"
    run_dir.mkdir(parents=True)
    old = run_dir / "all_rows.jsonl"
    old.write_text('{"kind": "cell", "candidate_proof": "old hardware"}\n')

    seen = {}

    def fake_sweep(config, rd, *, resume=True, verifier=None):
        seen["resume"] = resume
        seen["existed_at_sweep"] = (rd / "all_rows.jsonl").exists()
        return 7

    monkeypatch.setattr(rs.runner, "sweep", fake_sweep)
    monkeypatch.setattr(rs.runner, "results_root", lambda: tmp_path)
    monkeypatch.setattr(rs.ec2, "provision_spot_instance", lambda *a, **k: {})
    monkeypatch.setattr(rs.ec2, "server_config", lambda *a, **k: None)
    monkeypatch.setattr(rs, "select_verifier", lambda: None)
    monkeypatch.setattr(rs, "selected_model", lambda: "test")
    monkeypatch.setattr(rs, "build_config", lambda k: {"run_name": "scaling_test"})
    monkeypatch.setattr(rs, "spool_to_s3", lambda *a, **k: 0)

    import contextlib
    monkeypatch.setattr(rs.ec2, "serve_model", lambda k: contextlib.nullcontext())

    rs.main(["--force-rerun", "--no-s3"])

    assert seen["resume"] is False, "force-rerun must disable resume"
    assert not seen["existed_at_sweep"], "old rows must be moved aside BEFORE the sweep"
    archived = list(run_dir.glob("all_rows_SUPERSEDED-*.jsonl"))
    assert len(archived) == 1, archived
    assert "old hardware" in archived[0].read_text(), "superseded data must survive"
