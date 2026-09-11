"""Induction defaults over the neutral experiment facade."""

from dataclasses import dataclass
from typing import Tuple

from smolbench.evals.experiment import Experiment
from smolbench.induction import periodic


@dataclass(frozen=True)
class InductionExperiment(Experiment):
    """:class:`Experiment` with induction information defaults."""

    #: Derive conditions from periodic to prevent duplicate-list drift.
    info_types: Tuple[str, ...] = tuple(periodic.CONDITIONS)
