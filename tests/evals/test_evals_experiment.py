"""Test the neutral experiment lifecycle and tag guard."""

import dataclasses
import os
from typing import Any

import pytest

from smolbench.evals import Numeric, study_config
from smolbench.evals.experiment import Experiment, validate_experiment_tag


def make_quizzes(seed: int, model: str) -> dict[str, tuple[Numeric, ...]]:
    """Build one deterministic quiz for the requested seed and model."""
    return {"a": (Numeric(prompt=f"a/{seed}/{model}", answer=1),)}


_BASE = {
    "notebook_dir": "somewhere",
    "archetype_tags": {"stub-model": "decode"},
    "make_quizzes": make_quizzes,
    "info_types": ("a",),
}


def build(**kwargs: Any) -> Experiment:
    """Build an experiment with test defaults and overrides."""
    return Experiment(**{**_BASE, **kwargs})


def test_the_base_declares_no_study_default_for_the_info_arms() -> None:
    """Pin that ``info_types`` has no default so shared code never encodes a study's arms."""
    with pytest.raises(TypeError):
        Experiment(**{k: v for k, v in _BASE.items() if k != "info_types"})
    info_types = {f.name: f for f in dataclasses.fields(Experiment)}["info_types"]
    assert info_types.default is dataclasses.MISSING
    assert info_types.default_factory is dataclasses.MISSING


def test_a_lane_tag_and_the_standalone_tag_are_accepted() -> None:
    """Pin that standalone, spec-suffixed, and lane-suffixed tags pass the guard."""
    fleet = study_config.load_study_config().fleet
    assert validate_experiment_tag(fleet.standalone_tag, None) is None
    assert validate_experiment_tag(f"{fleet.tag_prefix}glm-4.7", None) is None
    assert validate_experiment_tag(f"{fleet.standalone_tag}-s0of3", "-s0of3") is None


@pytest.mark.parametrize(
    "tag, lane",
    [
        # A bare fleet prefix could terminate every lane.
        ("scaling-", None),
        ("scaling", None),
        ("scaling--s0of2", "-s0of2"),
        ("", None),
        ("   ", None),
    ],
)
def test_an_unsafe_tag_is_refused(tag: str, lane: str | None) -> None:
    """Pin that empty and bare-prefix tags are refused with the tag named in the error."""
    with pytest.raises(ValueError) as exc:
        validate_experiment_tag(tag, lane)
    assert repr(tag) in str(exc.value) or tag.strip() in str(exc.value)


def test_shards_partition_the_seeds() -> None:
    """Pin that shard strides partition the configured replicate seeds."""
    assert build(n_replicates=5, shard=(1, 2), state_file="s.json").seeds == (
        1777,
        1779,
    )
    assert build(n_replicates=5, shard=(0, 2), state_file="s.json").seeds == (
        1776,
        1778,
        1780,
    )
    assert build(n_replicates=5).seeds == (1776, 1777, 1778, 1779, 1780)


def test_shard_tags_and_state_files_are_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin that sharded experiments derive distinct tags and state files."""
    fleet = study_config.load_study_config().fleet
    monkeypatch.setenv("EC2_EXPERIMENT_TAG", f"{fleet.tag_prefix}x")
    first = build(shard=(0, 2))
    second = build(shard=(1, 2))

    def fake_agent_status() -> dict[str, str]:
        """Return the environment so the test can inspect exported settings."""
        return dict(os.environ)

    monkeypatch.setattr(
        "smolbench.evals.providers.ec2.agent_status",
        fake_agent_status,
    )
    first_env = first.agent_status()
    second_env = second.agent_status()
    assert first.experiment_tag.endswith("-s0of2")
    assert second.experiment_tag.endswith("-s1of2")
    assert first.experiment_tag != second.experiment_tag
    assert first_env["EC2_STATE_FILE"] != second_env["EC2_STATE_FILE"]
    assert first_env["EC2_STATE_FILE"].endswith(
        f".ec2_state_{first.experiment_tag}.json"
    )
    assert second_env["EC2_STATE_FILE"].endswith(
        f".ec2_state_{second.experiment_tag}.json"
    )


def test_shard_suffix_is_not_duplicated() -> None:
    """Pin that an existing shard suffix is preserved exactly once."""
    tag = "scaling-model-s0of2"
    experiment = build(experiment_tag=tag, shard=(0, 2))
    assert experiment.experiment_tag == tag


def test_untagged_experiment_falls_back_to_driver_then_standalone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin that untagged experiments resolve from the driver then study config."""
    fleet = study_config.load_study_config().fleet
    driver_tag = f"{fleet.tag_prefix}driver"
    monkeypatch.setenv("EC2_EXPERIMENT_TAG", driver_tag)
    assert build().experiment_tag == driver_tag
    monkeypatch.delenv("EC2_EXPERIMENT_TAG")
    assert build().experiment_tag == fleet.standalone_tag


def test_experiment_tag_is_exported_per_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin that each experiment exports its immutable tag before every live call."""
    fleet = study_config.load_study_config().fleet
    driver_tag = f"{fleet.tag_prefix}driver"
    monkeypatch.setenv("EC2_EXPERIMENT_TAG", driver_tag)
    third = build()
    first = build(experiment_tag=f"{fleet.tag_prefix}a")
    second = build(experiment_tag=f"{fleet.tag_prefix}b")

    def fake_agent_status() -> dict[str, str]:
        """Return the environment so the test can inspect exported settings."""
        return dict(os.environ)

    monkeypatch.setattr(
        "smolbench.evals.providers.ec2.agent_status",
        fake_agent_status,
    )
    assert first.agent_status()["EC2_EXPERIMENT_TAG"] == first.experiment_tag
    assert second.agent_status()["EC2_EXPERIMENT_TAG"] == second.experiment_tag
    assert third.agent_status()["EC2_EXPERIMENT_TAG"] == driver_tag


@pytest.mark.parametrize("tag", ["", "team/run", "../x", "a b", "..", "x" * 129])
def test_an_unsafe_experiment_tag_is_refused_at_construction(tag: str) -> None:
    """Pin that unsafe tags fail before any lifecycle call."""
    with pytest.raises(ValueError, match="EC2_EXPERIMENT_TAG"):
        build(experiment_tag=tag)


@pytest.mark.parametrize("state_file", ["", "  "])
def test_a_blank_state_file_is_refused(state_file: str) -> None:
    """Refuse blank state files because EC2 cannot persist at the repo root."""
    with pytest.raises(ValueError, match="state_file"):
        build(state_file=state_file)


@pytest.mark.parametrize("shard", [(0, 0), (2, 2), (-1, 1)])
def test_bad_shard_bounds_are_refused(shard: tuple[int, int]) -> None:
    """Refuse shard indices outside a positive shard-count range."""
    with pytest.raises(ValueError, match="shard"):
        build(shard=shard, state_file="s.json")


def test_sync_down_delegates_to_the_harness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin that sync_down delegates to the harness without invoking EC2."""
    exp = build()

    def fake_sync(self: Any) -> int:
        """Return a fixed sync count for the delegation test."""
        return 7

    monkeypatch.setattr(type(exp.harness), "sync_down", fake_sync)
    assert exp.sync_down() == 7


def test_archetype_tags_are_snapshotted() -> None:
    """Pin that result addressing cannot change through a caller's mapping."""
    tags = {"stub-model": "decode"}
    exp = build(archetype_tags=tags)
    tags["stub-model"] = "changed"
    assert exp.archetype_tags == {"stub-model": "decode"}
