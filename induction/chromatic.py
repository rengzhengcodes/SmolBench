"""
Generates chromatic intervals.
"""

from collections import defaultdict
import string
from typing import TypeAlias
from typing import Collection, Set, Tuple, Iterable, Callable
import numpy as np

# A color in the mathematical sense of some label.
Color: TypeAlias = str
# Interval of the form [start, end) as indices of some Sequence.
Interval: TypeAlias = Tuple[int, int]
# A collection of intervals.
Intervals: TypeAlias = Collection[Interval]



def _get_random_colors(
    n: int, l: int, rng: np.random.Generator,
    charset: Collection[str] = string.ascii_letters
) -> Set[Color]:
    """
    Generates n unique random colors of l length.

    Parameters
    ----------
    n:
        Number of colors to generate.
    l:
        Length of each color.
    rng:
        The rng being used.
    charset:
        The characters to include in each color.

    Return
    ------
    Set of unique colors.

    Exceptions
    ----------
    ValueError if l < ceil(log_{len(charset)}(n)) as cannot generate n unique colors.
    """
    charset = tuple(charset)
    base: int = len(charset)
    min_len: int = np.ceil(np.emath.logn(base, n))
    if l < min_len:
        raise ValueError(
            f"l < {min_len} = "
            f"ceil(log_{{{base}}}({n}))\n"
            f"Insufficient expressivity for labels in charset for the given length."
        )
    
    # Colors represented as an integer so it could be quickly exhaustively generated.
    colors: np.ndarray[int] = rng.choice(base ** l, size=n, replace=False)
    digits: np.ndarray[int] = np.empty((n, l), dtype=np.int64)
    for idx in range(l - 1, -1, -1):
        colors, digits[:, idx] = np.divmod(colors, base)

    charset_array: np.ndarray[str] = np.asarray(charset)
    return {"".join(color) for color in charset_array[digits]}



def _assign_colors(
    intervals: Collection[Interval],
    colors: Collection[Color],
    labeler: Callable[[Color, Intervals], Intervals],
    cleanser: Callable[[Intervals, Intervals], Intervals]
) -> Tuple[Dict[Color, Intervals], Dict[Interval, Color]]:
    """
    Given a set of intervals, assign colors to each interval.

    Parameters
    ----------
    intervals:
        A collection of intervals that need to be assigned a color.
    colors:
        The assignable interval colors.
    labeler:
        The arbitrator of which intervals get assigned for a color.
    cleanser:
        Cleans up what the labeler has access to on the next iteration of assignment.
    
    Returns
    -------
    A dictionary of every color to its intervals and every interval to its color.
    """
    label_to_intervals: Dict[Color, Intervals] = {}
    intervals_to_label: Dict[Interval, Color] = defaultdict(tuple)
    for color in colors:
        # Assigns to remaining intervals.
        assignment: Intervals = labeler(color, intervals)

        # Return bookkeeping.
        label_to_intervals[color] = assignment
        for interval in assignment:
            intervals_to_label[tuple(interval.tolist())] += (color,)
        
        # Cleanses assignable intervals.
        intervals = cleanser(intervals, assignment)

    return label_to_intervals, intervals_to_label


def _get_random_exclusive_intervals(n: int, intervaler: Iterable[int]) -> Interval:
    """
    Generates intervals from [0, n) where each interval does not overlap the
    previous.

    Parameters
    ----------
    n:
        The total length of intervals to generate.
    intervaler:
        The structure used to generate the next element of an interval.
    
    Yields
    ------
    A series of intervals from [0, n) generated off rng.
    """
    start: int = 0
    end: int = 0

    while end < n:
        end = min(n, next(intervaler, n))
        yield (start, end)
        start = end


def _get_exclusive_chromatic_intervals(
    n: int,
    colors: Collection[Color],
    intervaler: Iterable[int], 
    labeler: Callable[[Color, Intervals],Intervals],
    cleanser: Callable[[Color]]
) -> Tuple[Dict[Color, Intervals], Dict[Interval, Color]]:
    """
    Generates chromatic intervals from [0, n), where each i in [0, n) has exactly
    one color (i.e., no intervals overlap).

    Parameters
    ----------
    n:
        The length the intervals can span.
    colors:
        The colors to assign to the intervals.
    intervaler:
        The generator of intervals.
    labeler:
        Assigns colors to each interval.
    cleanser:
        Cleans up what the labeler has access to between colors.
    
    Returns
    -------
    A dictionary of every color to its intervals and every interval to its color.
    """
    intervals: Set[Interval] = np.array(tuple(_get_random_exclusive_intervals(n, intervaler)))
    return _assign_colors(intervals, colors, labeler, cleanser)


def get_random_exclusive_chromatic_intervals(
    n: int, intervals: int, colors: Collection[Color] | int, seed: int
) -> Tuple[Dict[Color, Collection[Interval]], Dict[Interval, Color]]:
    """
    Generates a number of intervals from [0, n) and each interval has equal
    probability of being any color.
    """

    # Seeds and generates the interval demarcations.
    rng: np.random.Generator = np.random.default_rng(seed)
    markers: np.ndarray[int] = rng.choice(range(n+1), intervals, replace=False)
    markers.sort()
    
    # Generates the colors if needed.
    if isinstance(colors, int):
        length: int = int(
            np.ceil(np.emath.logn(len(string.ascii_letters), colors))
        ) * 2
        colors: Sequence[Color] = tuple(_get_random_colors(
            colors, length, np.random.default_rng(seed)
        ))
    
    # Defines a uniform labeler.
    num_colors: int = len(colors)
    labels = rng.integers(num_colors, size=intervals)
    def labeler(color: Color, intervals: np.ndarray[Interval]) -> np.ndarray(Interval):
        color_idx: int = colors.index(color)
        return intervals[labels[labels == color_idx]]

    # Defines a null cleanser.
    def cleanser(original: Intervals, prune: Intervals) -> Intervals:
        """Does not prune anything due to how the labeler works."""
        return original
    
    return _get_exclusive_chromatic_intervals(n, colors, iter(markers), labeler, cleanser)


if __name__ == "__main__":
    print(get_random_exclusive_chromatic_intervals(250, 250 // 4, 46, 1776))
