"""Test the EC2 state-file lifecycle: offline, pure JSON and file logic.

The state file (see smolbench/evals/ec2.py's module docstring, "Local
state file" section) is the only thing that survives a kernel restart
between ``provision_spot_instance()`` and later notebook cells. These
tests exercise its save/load/clear/require contract in isolation from any
AWS call. No boto3 client is ever constructed here; that is
tests/test_ec2_provision.py's job, owned by a different suite. This file
only touches ``_state_path`` / ``_load_state`` / ``_save_state`` /
``_clear_state`` / ``_require_state``, which are pure functions of the
filesystem and the ``EC2_STATE_FILE`` env var.
"""

import pytest

from smolbench.evals import ec2

# A representative, but fake, state dict, shaped like what provisioning
# actually writes (instance_id/public_ip/region plus the two secrets). See
# the calls to _save_state in ec2.py's provisioning functions. Round-trip
# tests don't require this exact shape, since the state file is opaque
# JSON to _load_state/_save_state. But a realistic shape catches
# accidental type-coercion bugs (for example int vs str) that a trivial
# {"a": 1} would not.
SAMPLE_STATE = {
    "instance_id": "i-0123456789abcdef0",
    "public_ip": "203.0.113.10",
    "region": "us-east-1",
    "vllm_api_key": "vk-stub-secret",
    "control_token": "ct-stub-secret",
}


@pytest.fixture
def state_file(tmp_path, monkeypatch):
    """Point EC2_STATE_FILE at a scratch path for the duration of a test.

    monkeypatch.setenv, not os.environ directly, guarantees the override is undone after
    the test, so no test here can leak into another test or touch the repo's real
    ``.ec2_state.json``. (If a live experiment is running, that file would hold a real
    instance's secrets.) ``ec2._state_path()`` reads this env var at call time, not at
    import time (see test_state_file_env_read_at_call_time), so setting it through
    monkeypatch here is sufficient even though ``smolbench.evals.ec2`` was already
    imported when this test module was collected.
    """
    path = tmp_path / "state.json"
    monkeypatch.setenv("EC2_STATE_FILE", str(path))
    return path


def test_save_then_load_round_trips(state_file):
    """_save_state followed by _load_state returns an equal dict.

    The file exists on disk in between. This is the resumability contract
    a kernel restart (or a second notebook cell run) relies on to
    reattach, instead of provisioning a second instance.
    """
    ec2._save_state(SAMPLE_STATE)
    assert state_file.exists()
    assert ec2._load_state() == SAMPLE_STATE


def test_save_state_writes_mode_0600(state_file):
    """The state file holds the control token and vLLM api key in plaintext.

    (See the module docstring's "Security model" section.) So it must
    never be group- or world-readable. chmod sets the exact mode
    regardless of the process umask, so this check is deterministic.
    """
    ec2._save_state(SAMPLE_STATE)
    assert (state_file.stat().st_mode & 0o777) == 0o600


def test_clear_state_removes_the_file(state_file):
    ec2._save_state(SAMPLE_STATE)
    assert state_file.exists()
    ec2._clear_state()
    assert not state_file.exists()


def test_clear_state_on_missing_file_is_a_noop(state_file):
    """_clear_state must tolerate a never-written or already-cleared state file.

    shutdown_instance() calls it unconditionally, and a provisioning
    failure before the first _save_state must not turn a cleanup call
    into a crash.
    """
    assert not state_file.exists()
    ec2._clear_state()  # must not raise


def test_load_state_missing_file_returns_none(state_file):
    """Documented contract (_load_state's docstring: "or None when absent/corrupt").

    Callers (for example _require_state, provision_spot_instance) branch
    on None to decide whether to provision a fresh instance, so this
    must never raise.
    """
    assert not state_file.exists()
    assert ec2._load_state() is None


def test_load_state_corrupt_json_returns_none(state_file):
    """Documented contract: corrupt JSON degrades to None like a missing file.

    It does not raise an exception. With EC2_STATE_FILE set,
    _load_state's candidate list is just [this file]. (The legacy
    cwd-relative fallback only engages when the env override is unset;
    see test_state_file_env_read_at_call_time.) So the JSONDecodeError
    here is the only thing under test.
    """
    state_file.write_text("{not valid json, oops")
    assert ec2._load_state() is None


def test_require_state_raises_when_absent(state_file):
    """_require_state is the guard every inference/serve call goes through.

    On a fresh checkout, or after shutdown_instance(), it must raise an
    actionable RuntimeError that names provision_spot_instance() as the
    fix, not a KeyError or AttributeError from an unguarded None deref.
    """
    with pytest.raises(RuntimeError, match="provision_spot_instance"):
        ec2._require_state()


def test_require_state_returns_state_when_present(state_file):
    ec2._save_state(SAMPLE_STATE)
    assert ec2._require_state() == SAMPLE_STATE


def test_state_file_env_read_at_call_time(tmp_path, monkeypatch):
    """EC2_STATE_FILE must be honored even though ec2 was already imported.

    smolbench.evals.ec2 was already imported at collection time, by this very module,
    before this test's monkeypatch.setenv call runs. This is the load-bearing property
    the notebooks depend on: they import smolbench.evals.ec2 once, then later load
    keys.env (which may set EC2_STATE_FILE) in a subsequent cell. An import-time-cached
    path would silently keep pointing at the default location, and two notebook runs
    could clobber each other's state.
    """
    custom = tmp_path / "custom_state.json"
    assert not custom.exists()
    monkeypatch.setenv("EC2_STATE_FILE", str(custom))
    assert ec2._state_path() == custom

    ec2._save_state({"ok": True})
    assert custom.exists()  # honored by _save_state too, not only _state_path
    assert ec2._load_state() == {"ok": True}


def test_clear_state_leaves_a_different_instances_state_alone(state_file):
    """A teardown must not delete state belonging to another instance.

    The race this guards, observed live 2026-08-09: run A finishes and
    starts tearing down its box. Run B for the same experiment tag
    provisions a fresh box and writes its state. Then A's teardown reaches
    _clear_state, and if it deletes unconditionally, it removes B's state.
    B's next call raises "No EC2 instance state found," and the driver
    exits, leaving a live p5-class instance (about $21/h) billing with
    nothing driving it and no local record it exists.

    If you pass the torn-down instance id, the delete becomes conditional, so state
    naming a different instance survives.
    """
    ec2._save_state(dict(SAMPLE_STATE, instance_id="i-newbox"))
    ec2._clear_state("i-oldbox")  # the other instance's teardown
    survived = ec2._load_state()
    assert survived is not None, "a concurrent run's state was deleted by another teardown"
    assert survived["instance_id"] == "i-newbox"


def test_clear_state_removes_its_own_instances_state(state_file):
    """The guard must not stop a teardown clearing the state it does own.

    Otherwise every run would leak a stale state file pointing at a dead
    box, and the next provision would waste a reattach attempt on it.
    """
    ec2._save_state(dict(SAMPLE_STATE, instance_id="i-mine"))
    ec2._clear_state("i-mine")
    assert ec2._load_state() is None


def test_clear_state_without_an_id_stays_unconditional(state_file):
    """Callers with no resolved instance keep the old, unconditional behavior.

    Nothing was identified, so there is no ownership question to answer.
    """
    ec2._save_state(SAMPLE_STATE)
    ec2._clear_state()
    assert ec2._load_state() is None
