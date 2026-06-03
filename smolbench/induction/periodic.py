"""
Generates periodic patterns.
"""

import string
import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import TypeAlias, Collection, Iterable, Tuple, Dict, Callable, Optional
from ordered_set import OrderedSet

import numpy as np

from smolbench.evals import Quiz, ToF, Numeric

@dataclass(frozen=True)
class PeriodicConfig:
    """Config for generating some periodic pattern."""

    # Number of harmonics
    n: int
    # RNG seed for reproducibility.
    seed: int

    def __post_init__(self):
        """Generates an adequate number of harmonics"""
        # The count of the harmonics
        harmonics = np.array(range(1, self.n+1))


if __name__ == "__main__":
    PeriodicConfig(1, 42)