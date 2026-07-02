"""
Generation machinery shared by the induction benchmarks (periodic, chromatic).

The two benchmarks must stay CALIBRATED against each other: the noise-padding
ablation is only comparable across evals if the noise profile is identical,
and the random-label sampler fixes how fresh seeds map to fresh label sets.
Keeping these here, once, is what enforces that.
"""

import string
from dataclasses import dataclass
from typing import Any, Callable, Collection, Dict, Iterable, Optional, Tuple

import numpy as np
from ordered_set import OrderedSet

from smolbench.evals import Answer, QnA, Quiz


@dataclass(frozen=True, slots=True)
class Prompter:
    """Everything needed to prompt an LLM given a generated context.

    Contract: ``template`` MUST reference ``$positive_info`` (filled with the
    intensional / extensional / noise-padded context) plus every key produced
    by ``query_gen`` and ``substitution``. Rendering uses
    ``string.Template.safe_substitute``, so an unmatched or misspelled
    placeholder is SILENTLY left verbatim in the prompt rather than raising --
    validate templates against a sample query before an expensive run.
    """

    #: Prompt template; see the placeholder contract in the class docstring.
    template: string.Template
    #: Static placeholder values merged into every query's substitutions.
    substitution: Dict[str, str]
    #: (generated context mappings..., seed) -> iterable of
    #: (substitution_dict, answer) pairs; the exact mapping arguments are
    #: benchmark-specific (see each benchmark's built-in query generators).
    query_gen: Callable[..., Iterable[Tuple[Dict[str, str], Any]]]
    #: Optional template for extensional prompts, so the query representation
    #: can match the extensional context (e.g. chromatic's $query_years).
    #: Falls back to ``template`` when None.
    extens_template: Optional[string.Template] = None


def random_unique_strings(
    n: int,
    l: int,
    rng: np.random.Generator,
    charset: Collection[str],
) -> OrderedSet[str]:
    """
    Generates n unique random strings of length l over ``charset``.

    Strings are sampled as integers in [0, base**l) without replacement and
    base-expanded, so uniqueness is exact and the cost is O(n*l) regardless
    of how densely the space is sampled.

    Parameters
    ----------
    n:
        Number of strings to generate.
    l:
        Length of each string.
    rng:
        The RNG being used.
    charset:
        Character set to draw from (callers must exclude any separator in
        use downstream).

    Returns
    -------
    OrderedSet of n unique strings.

    Raises
    ------
    ValueError if l < ceil(log_{len(charset)}(n)): the space is too small to
    hold n unique strings.
    """
    charset = tuple(charset)
    base: int = len(charset)
    min_len = np.ceil(np.emath.logn(base, n))
    if l < min_len:
        raise ValueError(
            f"l={l} < {min_len} = ceil(log_{base}({n})): "
            f"insufficient length to generate {n} unique strings."
        )
    indices: np.ndarray = rng.choice(base ** l, size=n, replace=False)
    digits: np.ndarray = np.empty((n, l), dtype=np.int64)
    for idx in range(l - 1, -1, -1):
        indices, digits[:, idx] = np.divmod(indices, base)
    charset_array: np.ndarray = np.asarray(charset)
    return OrderedSet("".join(row) for row in charset_array[digits])


def make_noise(length: int, rng: np.random.Generator) -> str:
    """Generates a random noise string of the given character length.

    Draws uniformly from ASCII letters, digits, spaces, and newlines. This
    profile is the length-matching pad for the noise-intensional ablation;
    changing it de-calibrates every benchmark at once, which is exactly why
    it lives here and nowhere else.
    """
    charset = list(string.ascii_letters + string.digits + "   \n")
    return "".join(charset[i] for i in rng.integers(len(charset), size=length))


def quizzes_from_prompts(
    prompts: Iterable[Tuple[str, str, str, Answer]],
    qna_cls: type[QnA],
) -> Tuple[Quiz, Quiz, Quiz]:
    """Wraps (intens, extens, noise_intens, answer) tuples into three quizzes.

    Parameters
    ----------
    prompts:
        The benchmark's prompt generator output, one tuple per query.
    qna_cls:
        The question type to wrap each prompt in (``ToF`` for True/False
        answers, ``Numeric`` for integers) -- the class's ``__post_init__``
        validates that the answers actually match.

    Returns
    -------
    (intensional Quiz, extensional Quiz, noise-padded intensional Quiz)
    """
    intens_quiz: list = []
    extens_quiz: list = []
    noise_intens_quiz: list = []
    for intens, extens, noise_intens, answer in prompts:
        intens_quiz.append(qna_cls(prompt=intens, answer=answer))
        extens_quiz.append(qna_cls(prompt=extens, answer=answer))
        noise_intens_quiz.append(qna_cls(prompt=noise_intens, answer=answer))
    return tuple(intens_quiz), tuple(extens_quiz), tuple(noise_intens_quiz)
