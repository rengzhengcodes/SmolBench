"""Test the EC2 state-file lifecycle: offline, pure JSON and file logic."""

import os

import pytest

from smolbench.evals.providers import ec2
from tests._paths import REPO_ROOT

SAMPLE_STATE = {
    "instance_id": "i-0123456789abcdef0",
    "public_ip": "203.0.113.10",
    "region": "us-east-1",
    "vllm_api_key": "vk-stub-secret",
    "control_token": "ct-stub-secret",
}


@pytest.fixture
def state_file(tmp_path, monkeypatch):
    """Point EC2_STATE_FILE at a scratch path for the duration of a test."""
    path = tmp_path / "state.json"
    monkeypatch.setenv("EC2_STATE_FILE", str(path))
    return path


def test_save_load_round_trip_and_mode_0600(state_file):
    """Resume contract: state survives on disk, owner-readable only."""
    ec2._save_state(SAMPLE_STATE)
    assert state_file.exists()
    assert (state_file.stat().st_mode & 0o777) == 0o600
    assert ec2._load_state() == SAMPLE_STATE
    assert ec2._require_state() == SAMPLE_STATE
    state_file.chmod(0o666)  # a file an older version left loose is re-tightened
    ec2._save_state(SAMPLE_STATE)
    assert (state_file.stat().st_mode & 0o777) == 0o600


def test_save_state_mode_comes_from_creation_not_a_later_chmod(state_file, monkeypatch):
    """The token and api key are never world-readable, not even briefly."""
    monkeypatch.setattr(ec2.os, "fchmod", lambda fd, mode: None)  # neutralize the re-assert
    umask = os.umask(0)  # the most permissive default a caller could have
    try:
        ec2._save_state(SAMPLE_STATE)
    finally:
        os.umask(umask)
    assert (state_file.stat().st_mode & 0o777) == 0o600


@pytest.mark.parametrize("kind", ["missing", "corrupt"])
def test_load_state_degrades_to_none(state_file, kind):
    """Absent or corrupt state reads as None; _require_state raises actionably."""
    if kind == "corrupt":
        state_file.write_text("{not json")
    assert ec2._load_state() is None
    if kind == "missing":
        with pytest.raises(RuntimeError, match="provision_spot_instance"):
            ec2._require_state()


@pytest.mark.parametrize(
    "saved_id,clear_arg,expect_file",
    [("i-newbox", "i-oldbox", True), ("i-mine", "i-mine", False), ("i-mine", None, False)],
)
def test_clear_state_is_ownership_scoped(state_file, saved_id, clear_arg, expect_file):
    """A teardown deletes only state it owns; an unidentified caller stays unconditional."""
    ec2._save_state(dict(SAMPLE_STATE, instance_id=saved_id))
    ec2._clear_state(clear_arg)
    survived = ec2._load_state()
    if expect_file:
        assert survived is not None and survived["instance_id"] == saved_id
    else:
        assert survived is None
    ec2._clear_state()  # no-op when already cleared


def test_state_file_env_read_at_call_time(tmp_path, monkeypatch):
    """EC2_STATE_FILE must be honored even though ec2 was already imported."""
    custom = tmp_path / "custom_state.json"
    assert not custom.exists()
    monkeypatch.setenv("EC2_STATE_FILE", str(custom))
    assert ec2._state_path() == custom

    ec2._save_state({"ok": True})
    assert custom.exists()
    assert ec2._load_state() == {"ok": True}


def test_default_state_file_anchors_to_the_repo_root():
    """Pin ``_DEFAULT_STATE_FILE`` to ``<repo root>/.ec2_state.json``."""
    assert ec2._DEFAULT_STATE_FILE.resolve() == (REPO_ROOT / ".ec2_state.json").resolve()
