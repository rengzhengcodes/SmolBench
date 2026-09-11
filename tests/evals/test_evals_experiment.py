"""Test the neutral experiment lifecycle and tag guard."""

import dataclasses
from typing import Any

import pytest

from smolbench.evals import Numeric, study_config
from smolbench.evals.experiment import Experiment, validate_experiment_tag


def make_quizzes(seed: int, model: str) -> dict[str, tuple[Numeric, ...]]:
    """Build one deterministic quiz for the requested seed and model."""
    return {"a": (Numeric(prompt=f"a/{seed}/{model}", answer=1),)}


def build(**kwargs: Any) -> Experiment:
    """Build an experiment with test defaults and overrides."""
    base = {
        "notebook_dir": "somewhere",
        "archetype_tags": {"stub-model": "decode"},
        "make_quizzes": make_quizzes,
        "info_types": ("a",),
    }
    return Experiment(**{**base, **kwargs})


def test_the_base_declares_no_study_default_for_the_info_arms() -> None:
    """Require info types to avoid study defaults in shared code."""
    with pytest.raises(TypeError):
        # The missing arg is under test.
        # pylint: disable=no-value-for-parameter
        Experiment(
            notebook_dir="somewhere", archetype_tags={}, make_quizzes=make_quizzes
        )
    info_types = {f.name: f for f in dataclasses.fields(Experiment)}["info_types"]
    assert info_types.default is dataclasses.MISSING
    assert info_types.default_factory is dataclasses.MISSING


def test_a_lane_tag_and_the_standalone_tag_are_accepted() -> None:
    """Accept valid lane and standalone tags."""
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
    """Name rejected tags in errors."""
    with pytest.raises(ValueError) as exc:
        validate_experiment_tag(tag, lane)
    assert repr(tag) in str(exc.value) or tag.strip() in str(exc.value)
