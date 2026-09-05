"""The study-NEUTRAL experiment lifecycle facade and the experiment-tag guard.

``smolbench.evals.experiment.Experiment`` carries the whole
provision/run/agent_status/teardown lifecycle that used to live in
``smolbench.induction.experiment``, so a second study's driver inherits it
instead of re-implementing it inline. Offline: nothing here touches AWS.
"""

import dataclasses
import inspect

import pytest

from smolbench.evals import Numeric, study_config
from smolbench.evals.experiment import Experiment, validate_experiment_tag
from smolbench.evals.replicates import ReplicateHarness
from smolbench.induction.experiment import InductionExperiment


def make_quizzes(seed: int, model: str):
    return {"a": (Numeric(prompt=f"a/{seed}/{model}", answer=1),)}


def build(**kwargs) -> Experiment:
    base = dict(
        notebook_dir="somewhere",
        archetype_tags={"stub-model": "decode"},
        make_quizzes=make_quizzes,
        info_types=("a",),
    )
    return Experiment(**{**base, **kwargs})


def test_the_base_carries_the_whole_lifecycle():
    """Everything a driver needs is on the neutral class, not on a subclass."""
    for name in ("provision", "run", "summarize", "cot_chain_lengths",
                 "agent_status", "teardown", "_apply_env", "seeds",
                 "results_dir", "harness"):
        assert hasattr(Experiment, name), name
    exp = build(n_replicates=3, base_seed=100)
    assert exp.seeds == (100, 101, 102)
    assert isinstance(exp.harness, ReplicateHarness)
    assert exp.harness.info_types == ("a",)


def test_the_base_declares_no_study_default_for_the_info_arms():
    """`info_types` is REQUIRED on the neutral class: there is no study-neutral
    set of information conditions, so the base must not carry one study's.

    A default here is how the induction arm names ended up spelled into a
    shared module in the first place.
    """
    with pytest.raises(TypeError):
        Experiment(notebook_dir="somewhere", archetype_tags={},
                   make_quizzes=make_quizzes)
    info_types = {f.name: f for f in dataclasses.fields(Experiment)}["info_types"]
    assert info_types.default is dataclasses.MISSING
    assert info_types.default_factory is dataclasses.MISSING


def test_the_induction_subclass_only_supplies_defaults():
    """`InductionExperiment` adds induction's two defaults and no new fields.

    The lifecycle it used to own now lives on the base; anything else it
    declared would be study prose back in a place a second study inherits.
    """
    assert issubclass(InductionExperiment, Experiment)
    assert [f.name for f in dataclasses.fields(InductionExperiment)] == [
        f.name for f in dataclasses.fields(Experiment)
    ]
    # Default 1: the induction information arms.
    assert InductionExperiment(
        notebook_dir="periodic", archetype_tags={}, make_quizzes=make_quizzes
    ).info_types
    # Default 2: the CoT archetype tag, which the base makes an explicit
    # argument (a study that has no CoT archetype must not inherit one).
    assert (inspect.signature(InductionExperiment.cot_chain_lengths)
            .parameters["tag"].default == "cot")
    assert (inspect.signature(Experiment.cot_chain_lengths)
            .parameters["tag"].default is inspect.Parameter.empty)


# ---------------------------------------------------------------------------
# validate_experiment_tag
# ---------------------------------------------------------------------------

def test_a_lane_tag_and_the_standalone_tag_are_accepted():
    """The two shapes a driver legitimately resolves to must pass."""
    fleet = study_config.load_study_config().fleet
    assert validate_experiment_tag(fleet.standalone_tag, None) is None
    assert validate_experiment_tag(f"{fleet.tag_prefix}glm-4.7", None) is None
    assert validate_experiment_tag(
        f"{fleet.standalone_tag}-s0of3", "-s0of3"
    ) is None


@pytest.mark.parametrize("tag, lane", [
    # The retired study's tag: tag-based recovery would reattach to any live
    # box carrying it, and a teardown would terminate it.
    ("periodic-induction", None),
    # ... including behind a lane suffix, which an exact-match guard misses.
    ("periodic-induction-s0of2", "-s0of2"),
    ("periodic-induction-deepseek-v3.1-s1of2", "-deepseek-v3.1-s1of2"),
    # A BARE shared fleet prefix names every lane at once: fleet_teardown
    # terminates by tag, so this would take the whole fleet down.
    ("scaling-", None),
    ("scaling", None),
    ("scaling--s0of2", "-s0of2"),
    # Nothing at all is not a tag.
    ("", None),
    ("   ", None),
])
def test_an_unsafe_tag_is_refused(tag, lane):
    """Each refusal names the tag, so an operator can see what to export."""
    with pytest.raises(ValueError) as exc:
        validate_experiment_tag(tag, lane)
    assert repr(tag) in str(exc.value) or tag.strip() in str(exc.value)


def test_the_retired_set_is_a_parameter():
    """`retired` defaults to the one retired study but is caller-overridable,
    so a later study can retire its own tag without editing this module."""
    assert validate_experiment_tag("old-study", None) is None
    with pytest.raises(ValueError):
        validate_experiment_tag("old-study", None, retired=("old-study",))
    # An empty override disables only the RETIRED check; the bare-prefix and
    # empty-tag checks are structural and always apply.
    with pytest.raises(ValueError):
        validate_experiment_tag("scaling-", None, retired=())
