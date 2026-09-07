"""Induction's study-specific defaults over the neutral experiment facade.

:class:`InductionExperiment` narrows two fields to induction's own defaults;
:class:`~smolbench.evals.experiment.Experiment` carries the lifecycle, seed
convention and results/resume contract unchanged.
"""

from dataclasses import dataclass
from typing import Tuple

from smolbench.evals.experiment import Experiment
from smolbench.induction import periodic


@dataclass(frozen=True)
class InductionExperiment(Experiment):
    """:class:`Experiment`, defaulted to induction's information conditions.

    Adds no new fields and overrides no lifecycle method (except
    :meth:`cot_chain_lengths`, which only supplies a default ``tag``); see
    ``smolbench.evals.experiment.Experiment`` for everything else.
    """

    #: Info types evaluated per replicate. Derived from ``periodic.CONDITIONS``
    #: rather than a second literal that could drift from it; a study wanting
    #: a different subset or order passes its own tuple.
    info_types: Tuple[str, ...] = tuple(periodic.CONDITIONS)

    def cot_chain_lengths(self, tag: str = "cot") -> None:
        """Print reasoning-chain word-count stats from the stored CoT replicates.

        Thin override of :meth:`Experiment.cot_chain_lengths` that only
        defaults ``tag``: every induction CoT archetype is tagged "cot", so a
        caller need not repeat it at every call site.
        """
        super().cot_chain_lengths(tag)
