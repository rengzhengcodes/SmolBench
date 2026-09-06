"""Induction's study-specific defaults over the neutral experiment facade.

The whole provision/run/agent_status/teardown/``_apply_env`` lifecycle now
lives on :class:`~smolbench.evals.experiment.Experiment` -- see that module's
docstring for the seed convention, the results/resume contract, the COST
notes and the CRITICAL "never import ``providers.ec2`` at module scope" rule,
all of which apply here unchanged. :class:`InductionExperiment` only narrows
two fields to induction's own defaults, keeping this module importable
exactly as it was for existing callers (``from
smolbench.induction.experiment import InductionExperiment, repo_root``).
"""

from dataclasses import dataclass
from typing import Tuple

from smolbench.evals.experiment import Experiment, repo_root  # noqa: F401 -- re-exported
from smolbench.induction import periodic


@dataclass(frozen=True)
class InductionExperiment(Experiment):
    """:class:`Experiment`, defaulted to induction's information conditions.

    Adds no new fields and overrides no lifecycle method (except
    :meth:`cot_chain_lengths`, which only supplies a default ``tag``); see
    ``smolbench.evals.experiment.Experiment`` for everything else.
    """

    #: Info types evaluated per replicate, in serialization order. Derived
    #: from ``periodic.CONDITIONS`` -- the ONE declaration of the arm names
    #: (see that mapping's own docstring in ``periodic.py``'s "Information
    #: conditions" module docstring section) -- rather than a second literal
    #: here that could drift from it. A study wanting a different subset or
    #: order passes its own tuple.
    info_types: Tuple[str, ...] = tuple(periodic.CONDITIONS)

    def cot_chain_lengths(self, tag: str = "cot") -> None:
        """Print reasoning-chain word-count stats from the stored CoT replicates.

        Thin override of :meth:`Experiment.cot_chain_lengths` that only
        defaults ``tag``: every induction CoT archetype is tagged "cot", so a
        caller need not repeat it at every call site.
        """
        super().cot_chain_lengths(tag)
