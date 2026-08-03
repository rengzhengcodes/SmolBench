"""Answer extraction that separates "wrong" from "wrongly formatted".

Why this exists
---------------
The eval prompts give an explicit output contract -- chromatic's is

    Return exactly one of these two strings and nothing else:
    True
    False

and the periodic studies' is "Return exactly one integer and nothing else."
The original graders enforced that contract by *parsing strictly*, which
conflated two very different events:

* the model got the question wrong, and
* the model got the question right but ignored the output contract.

Both landed in the same bucket. ``ToF.condition`` strips non-alphabetic
characters and demands the remainder be exactly ``true``/``false``, so
``"Answer: False"`` becomes ``"AnswerFalse"`` and raises -- an invalid mark,
which counts as a failure. Meanwhile ``Numeric.condition`` failed the opposite
way: it takes the FIRST integer anywhere, so ``"2520 // 8 = 315\\n\\n315"`` is
scored as 2520, the operand rather than the result -- a mark that looks validly
graded and is simply wrong.

This module extracts the answer robustly AND reports the contract violation
separately, so an analysis can ask "how often was the model right?" and "how
often did it obey the instructions?" as two different questions. That
distinction is load-bearing for the induction benchmarks: the token-matched
whitespace pad in the ``noise_intens`` arm measurably degrades instruction
following (0% invalid under the old random-character pad, 19-28% under
whitespace on chromatic/decode), so an arm meant only to control for LENGTH was
also silently penalising format compliance.

Recovery is deliberately conservative
-------------------------------------
An early version mined a verdict from anywhere in the response and "recovered"
96% of invalids -- but it was firing on reasoning chains TRUNCATED by the
completion budget, matching a stray "no" inside thinking that never reached a
conclusion. Inventing verdicts out of unfinished reasoning is worse than
leaving them invalid. So a long response is only mined when it ENDS in a
verdict; otherwise it stays unparseable and is labelled `TRUNCATED`.

Repetition collapse gets its own label for the same reason: it is not a
parsing problem. Nemotron-Ultra-253B under the whitespace-padded noise arm
emitted 24,576 characters of "0" -- 8,192 tokens of "000", the entire
completion budget -- on every question. No parser can recover an answer that
was never produced.
"""

import ast
import re
from dataclasses import dataclass
from typing import Optional

from smolbench.evals import Answer, Numeric, QnA, ToF

# --- Violation labels -------------------------------------------------------
# None means the response obeyed the prompt's output contract exactly. Every
# other label names a specific way it did not, so the failure modes can be
# counted separately instead of collapsing into "invalid".

#: Verdict behind a lead-in, e.g. ``"Answer: False"``. Violates "nothing else".
PREFIXED = "prefixed"
#: Right meaning, wrong words: ``"Yes"``/``"No"`` when True/False was demanded.
WRONG_LEXICON = "wrong-lexicon"
#: The answer is embedded in prose or reasoning rather than returned alone.
VERBOSE = "verbose"
#: Wrapped in markup/punctuation, e.g. ``\boxed{280}`` or ``**False**``.
MARKUP = "markup"
#: Several candidate answers that disagree; the last one is taken.
MULTIPLE_VALUES = "multiple-values"
#: Repetition collapse -- a long response built from a handful of characters.
DEGENERATE = "degenerate-repetition"
#: A long response that never reaches a verdict (chain cut off mid-thought).
TRUNCATED = "truncated"
#: Nothing at all came back.
EMPTY = "empty"
#: Non-empty, but no answer could be extracted.
UNPARSEABLE = "unparseable"
#: An arithmetic expression instead of the integer it evaluates to, e.g.
#: ``"2520/2"`` where 1260 was wanted. Its own label because BOTH naive rules
#: get it wrong -- taking the first integer scores the numerator, taking the
#: last scores the divisor -- while the model actually answered correctly.
EXPRESSION = "unevaluated-expression"

#: Violations whose answer was still recovered -- the model obeyed the
#: question, just not the formatting. Useful for "how much does relaxing the
#: format contract change the score?"
RECOVERABLE_VIOLATIONS = frozenset(
    {PREFIXED, WRONG_LEXICON, VERBOSE, MARKUP, MULTIPLE_VALUES, EXPRESSION}
)

# Beyond this length a response is treated as prose/reasoning rather than an
# answer, so only a terminal verdict is trusted. See the module docstring.
_LONG_RESPONSE = 200
#: How much of the tail counts as "the concluding statement".
_TAIL_WINDOW = 60
#: A long response made of this few distinct characters is repetition collapse.
_DEGENERATE_ALPHABET = 3
_DEGENERATE_MIN_LEN = 500
#: Tail examined for a collapse that begins partway through a response. Long
#: enough that ordinary repetition (a rule of dashes, a run of newlines) does
#: not trip it, short enough to catch a model that broke down near the end.
_DEGENERATE_TAIL = 400

_TOF_TOKEN = re.compile(r"\b(true|false)\b", re.IGNORECASE)
_YES_NO = re.compile(r"\b(yes|no)\b", re.IGNORECASE)
_INT = re.compile(r"-?\d+")
_ANSWER_LEAD = re.compile(r"answer\s*[:\-=]*\s*\**\s*", re.IGNORECASE)
_TERMINAL_TOF = re.compile(
    r"(?:answer\s*[:\-=]*\s*)?\**\s*(true|false)\s*[.!*\"'`]*\s*$", re.IGNORECASE
)
_TERMINAL_YES_NO = re.compile(
    r"(?:answer\s*[:\-=]*\s*)?\**\s*(yes|no)\s*[.!*\"'`]*\s*$", re.IGNORECASE
)
_TERMINAL_INT = re.compile(
    r"(?:answer\s*[:\-=]*\s*)?\**\s*\\?boxed\{?\s*(-?\d+)\s*\}?\**\s*[.!*\"'`]*\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParseResult:
    """One response's extracted answer plus its contract compliance.

    Attributes
    ----------
    value:
        The extracted answer, or None when nothing could be extracted.
    violation:
        None when the response obeyed the output contract exactly; otherwise
        one of the labels in this module naming how it did not.
    """

    value: Optional[Answer]
    violation: Optional[str]

    @property
    def compliant(self) -> bool:
        """True when the response obeyed the prompt's output contract."""
        return self.violation is None

    @property
    def recovered(self) -> bool:
        """True when an answer was extracted *despite* a contract violation."""
        return self.value is not None and self.violation is not None


def is_degenerate(text: str) -> bool:
    """True when `text` is repetition collapse rather than an answer.

    Structural rather than pattern-based: a long stretch drawn from a tiny
    alphabet is degenerate whatever character it happens to repeat.

    Two shapes, both observed live under the whitespace-padded noise arm:

    * collapse from the start -- Nemotron-Ultra-253B emitted 24,576
      characters of "0", the whole completion budget, with nothing else;
    * collapse after a real beginning -- Olmo-3.1-32B-Think started
      reasoning and then devolved into ~16,400 repeated U+2010 hyphens until
      the budget ran out.

    The second shape is why the tail is checked separately. Judging the whole
    string would see a wide alphabet (the genuine prose at the front) and
    mislabel the response `TRUNCATED`, which would blame the completion
    budget for what is actually the model breaking down -- a materially
    different finding.
    """
    stripped = text.strip()
    if not stripped:
        return False
    if (
        len(stripped) >= _DEGENERATE_MIN_LEN
        and len(set(stripped)) <= _DEGENERATE_ALPHABET
    ):
        return True
    tail = stripped[-_DEGENERATE_TAIL:]
    return (
        len(stripped) >= _DEGENERATE_MIN_LEN
        and len(tail) >= _DEGENERATE_TAIL
        and len(set(tail)) <= _DEGENERATE_ALPHABET
    )


#: Characters a bare arithmetic expression may contain.
_ARITHMETIC_ONLY = re.compile(r"[\d\s+\-*/().]+")
#: AST nodes `_eval_arithmetic` will evaluate. Pow is deliberately excluded --
#: ``9**9**9`` is a denial-of-service, not an answer.
_ARITHMETIC_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod)


def _eval_arithmetic(text: str) -> Optional[int]:
    """Evaluates a bare arithmetic expression, or returns None.

    Models sometimes answer a counting question with the calculation rather
    than its result -- ``"2520/2"`` when 1260 was asked for. Both naive
    extraction rules mis-grade that: the first integer is the numerator, the
    last is the divisor, and neither is the answer the model actually gave.

    Evaluated by walking a validated AST rather than with ``eval``: only
    numeric literals and the operators in `_ARITHMETIC_BINOPS` are honoured,
    so nothing here can execute arbitrary code even if a response is hostile.

    Returns
    -------
    Optional[int]
        The value when the expression is well-formed and integral (2520/2 is
        1260.0, which counts); None otherwise, including for a division by
        zero or a non-integral result.
    """
    if not _ARITHMETIC_ONLY.fullmatch(text) or not any(c.isdigit() for c in text):
        return None
    try:
        tree = ast.parse(text.strip(), mode="eval")
    except (SyntaxError, ValueError, MemoryError):
        return None

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            operand = evaluate(node.operand)
            return operand if isinstance(node.op, ast.UAdd) else -operand
        if isinstance(node, ast.BinOp) and isinstance(node.op, _ARITHMETIC_BINOPS):
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Mod):
                return left % right
            if right == 0:
                raise ZeroDivisionError
            return left / right if isinstance(node.op, ast.Div) else left // right
        raise ValueError("unsupported expression")

    try:
        value = evaluate(tree)
    except (ValueError, ZeroDivisionError, OverflowError, TypeError):
        return None
    if isinstance(value, float) and not value.is_integer():
        return None
    return int(value)


def _preamble(text: str) -> Optional[str]:
    """Classifies a response that carries extra material around its answer."""
    return VERBOSE if len(text.strip()) > _LONG_RESPONSE else PREFIXED


def parse_tof(text: str) -> ParseResult:
    """Extracts a True/False verdict and classifies contract compliance.

    The contract is "return exactly one of these two strings and nothing
    else", so anything beyond a bare ``True``/``False`` is a violation even
    when the verdict is recoverable.
    """
    if not text or not text.strip():
        return ParseResult(None, EMPTY)
    if is_degenerate(text):
        return ParseResult(None, DEGENERATE)

    stripped = text.strip()

    # Fully compliant: exactly the demanded token (the original strict rule).
    if stripped.lower() in ("true", "false"):
        return ParseResult(stripped.lower() == "true", None)

    # Tolerated as compliant-ish: the bare token wearing punctuation/markup,
    # e.g. "**False**" or '"True".' -- still a violation of "nothing else",
    # but a purely cosmetic one, so it gets its own label.
    if re.fullmatch(r"[\s*_`\"'.]*(true|false)[\s*_`\"'.]*", stripped, re.IGNORECASE):
        return ParseResult(_TOF_TOKEN.search(stripped).group(1).lower() == "true", MARKUP)

    # A response that ENDS in a verdict did conclude, however much preceded
    # it. When the text also contains a DIFFERENT verdict earlier, that
    # disagreement is the more informative violation to report than whatever
    # wrapping the final verdict wore.
    terminal = _TERMINAL_TOF.search(stripped[-_TAIL_WINDOW:])
    if terminal:
        verdict = terminal.group(1).lower() == "true"
        distinct = {t.lower() for t in _TOF_TOKEN.findall(stripped)}
        violation = MULTIPLE_VALUES if len(distinct) > 1 else _preamble(stripped)
        return ParseResult(verdict, violation)

    if len(stripped) <= _LONG_RESPONSE:
        tokens = [t.lower() for t in _TOF_TOKEN.findall(stripped)]
        if tokens:
            if len(set(tokens)) == 1:
                return ParseResult(tokens[0] == "true", _preamble(stripped))
            return ParseResult(tokens[-1] == "true", MULTIPLE_VALUES)
        # Right meaning, wrong vocabulary.
        terminal_yn = _TERMINAL_YES_NO.search(stripped)
        if terminal_yn:
            return ParseResult(terminal_yn.group(1).lower() == "yes", WRONG_LEXICON)
        return ParseResult(None, UNPARSEABLE)

    # Long, and never concluded: a chain cut off mid-thought. Deliberately not
    # mined for a verdict -- see the module docstring.
    return ParseResult(None, TRUNCATED)


def parse_numeric(text: str) -> ParseResult:
    """Extracts an integer answer and classifies contract compliance.

    The contract is "return exactly one integer and nothing else", so prose,
    markup, or a worked calculation around the number are all violations --
    and the last of those is the dangerous one, because the original
    first-integer rule silently graded such answers on an operand.
    """
    if not text or not text.strip():
        return ParseResult(None, EMPTY)
    if is_degenerate(text):
        return ParseResult(None, DEGENERATE)

    stripped = text.strip()

    if re.fullmatch(r"-?\d+", stripped):
        return ParseResult(int(stripped), None)

    # A bare integer wearing markup/punctuation, e.g. "**42**" or '"42".' --
    # the number alone, so only the "no punctuation" clause was broken.
    if re.fullmatch(r"[\s*_`\"'.]*-?\d+[\s*_`\"'.]*", stripped):
        return ParseResult(int(_INT.search(stripped).group()), MARKUP)

    # A bare integer in answer markup, e.g. "\boxed{280}".
    boxed = _TERMINAL_INT.fullmatch(stripped)
    if boxed:
        return ParseResult(int(boxed.group(1)), MARKUP)

    # A calculation rather than its result, e.g. "2520/2". Tried before any
    # integer-picking rule, because every such rule scores an operand.
    arithmetic = _eval_arithmetic(stripped)
    if arithmetic is not None:
        return ParseResult(arithmetic, EXPRESSION)

    ints = _INT.findall(stripped)
    if not ints:
        return ParseResult(None, TRUNCATED if len(stripped) > _LONG_RESPONSE else UNPARSEABLE)

    if len(ints) == 1:
        return ParseResult(int(ints[0]), _preamble(stripped))

    # Several integers. A concluding "Answer: N" or a terminal integer is the
    # result; the earlier ones are working. Taking the FIRST (the old rule) is
    # what produced silent mis-grades.
    terminal = _TERMINAL_INT.search(stripped[-_TAIL_WINDOW:])
    if terminal:
        return ParseResult(int(terminal.group(1)), MULTIPLE_VALUES)
    lead = _ANSWER_LEAD.split(stripped, maxsplit=1)
    if len(lead) > 1:
        after = _INT.findall(lead[1])
        if after:
            return ParseResult(int(after[0]), MULTIPLE_VALUES)
    return ParseResult(int(ints[-1]), MULTIPLE_VALUES)


def parse_for(question: QnA, text: str) -> ParseResult:
    """Parses `text` with the extractor matching `question`'s answer type.

    Falls back to the question's own ``condition`` for any QnA subclass this
    module does not special-case, so an unknown question type degrades to the
    original strict behaviour rather than silently mis-parsing.
    """
    if isinstance(question, ToF):
        return parse_tof(text)
    if isinstance(question, Numeric):
        return parse_numeric(text)
    try:
        return ParseResult(question.condition(text), None)
    except ValueError:
        return ParseResult(None, UNPARSEABLE)
