"""Separate "wrong" from "wrongly formatted" when extracting an answer.

Why this exists
----------------
The eval prompts give an explicit output contract. Chromatic's contract is

    Return exactly one of these two strings and nothing else:
    True
    False

and the periodic studies' contract is "Return exactly one integer and
nothing else." The original graders enforced that contract by *parsing
strictly*. Strict parsing conflated two very different events:

* the model got the question wrong, and
* the model got the question right but ignored the output contract.

Both events landed in the same bucket. ``ToF.condition`` strips
non-alphabetic characters and demands the remainder be exactly
``true``/``false``. So ``"Answer: False"`` becomes ``"AnswerFalse"`` and
raises -- an invalid mark, which counts as a failure. ``Numeric.condition``
failed the opposite way: it takes the FIRST integer anywhere. So
``"2520 // 8 = 315\\n\\n315"`` is scored as 2520, the operand rather than
the result -- a mark that looks validly graded and is simply wrong.

This module extracts the answer robustly, and reports the contract
violation separately. An analysis can then ask "how often was the model
right?" and "how often did it obey the instructions?" as two different
questions. That distinction is load-bearing for the induction benchmarks:
the token-matched whitespace pad in the ``noise_intens`` arm measurably
degrades instruction following (0% invalid under the old random-character
pad, 19-28% under whitespace on chromatic/decode). An arm meant only to
control for LENGTH was also silently penalizing format compliance.

Recovery is deliberately conservative
---------------------------------------
An early version mined a verdict from anywhere in the response, and
"recovered" 96% of invalids. But it fired on reasoning chains TRUNCATED by
the completion budget, matching a stray "no" inside thinking that never
reached a conclusion. Inventing verdicts out of unfinished reasoning is
worse than leaving them invalid. So a long response is only mined when it
ENDS in a verdict; otherwise it stays unparseable and gets the
`TRUNCATED` label.

Repetition collapse gets its own label for the same reason: it is not a
parsing problem. Nemotron-Ultra-253B, under the whitespace-padded noise
arm, emitted 24,576 characters of "0" on every question -- 8,192 tokens
of "000", the entire completion budget. No parser can recover an answer
that was never produced.
"""

import ast
import re
from dataclasses import dataclass
from typing import Optional

from smolbench.evals import Answer, Numeric, QnA, ToF

# --- Violation labels -------------------------------------------------------
# None means the response obeyed the prompt's output contract exactly. Every
# other label names one specific way it did not. This lets the failure modes
# get counted separately, instead of collapsing into "invalid".

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
#: ``"2520/2"`` where 1260 was wanted. It gets its own label because BOTH
#: naive rules get it wrong: taking the first integer scores the numerator,
#: taking the last scores the divisor, while the model actually answered
#: correctly.
EXPRESSION = "unevaluated-expression"

#: Violations whose answer was still recovered -- the model obeyed the
#: question, just not the formatting. Useful for "how much does relaxing the
#: format contract change the score?"
RECOVERABLE_VIOLATIONS = frozenset(
    {PREFIXED, WRONG_LEXICON, VERBOSE, MARKUP, MULTIPLE_VALUES, EXPRESSION}
)

# Beyond this length, treat a response as prose/reasoning rather than an
# answer. Only a terminal verdict is trusted past this length. See the
# module docstring.
_LONG_RESPONSE = 200
#: How much of the tail counts as "the concluding statement".
_TAIL_WINDOW = 60
#: A long response built from this few distinct characters is repetition
#: collapse.
_DEGENERATE_ALPHABET = 3
_DEGENERATE_MIN_LEN = 500
#: Tail examined for a collapse that starts partway through a response.
#: This window is long enough that ordinary repetition (a rule of dashes,
#: a run of newlines) does not trip it. It is short enough to catch a
#: model that broke down near the end.
_DEGENERATE_TAIL = 400
#: Word-level collapse: how many trailing words to examine, and how few
#: distinct words among them mean the model is looping on a phrase rather
#: than writing. This size keeps ordinary prose from qualifying: 60
#: consecutive words of genuine text carry far more than 8 distinct
#: tokens.
_DEGENERATE_MIN_WORDS = 60
_DEGENERATE_WORD_ALPHABET = 8
#: Whole-response vocabulary collapse. Llama-4-Maverick looped
#: "## Step 1" for thousands of words, then drifted into unrelated
#: hallucinated text. Neither its tail nor its character alphabet looks
#: wrong, but it used only 67 distinct words across 4,746 (1.4%). Genuine
#: reasoning of that length runs an order of magnitude richer, so a
#: ratio this low means the model stopped composing.
_DEGENERATE_RATIO_MIN_WORDS = 200
_DEGENERATE_WORD_RATIO = 0.05

#: Longest integer this module will convert. Python raises ValueError
#: above 4,300 digits (the int/str conversion limit), and a degenerating
#: model really does emit numbers that long: one response carried a
#: 20,379-digit run, which crashed grading and took a live run down with
#: it. The eval's answers are counts bounded by lcm(1..9) = 2520, so
#: anything past this many digits is not an answer under any reading.
_MAX_ANSWER_DIGITS = 40

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
    """One response's extracted answer, plus its contract compliance.

    Attributes
    ----------
    value : Answer or None
        The extracted answer, or None when this module could extract
        nothing.
    violation : str or None
        None when the response obeyed the output contract exactly.
        Otherwise, one of this module's labels, naming how the response
        broke the contract.
    """

    value: Optional[Answer]
    violation: Optional[str]

    @property
    def compliant(self) -> bool:
        """Whether the response obeyed the prompt's output contract."""
        return self.violation is None

    @property
    def recovered(self) -> bool:
        """Whether an answer was extracted despite a contract violation."""
        return self.value is not None and self.violation is not None


def is_degenerate(text: str) -> bool:
    """Return whether `text` is repetition collapse rather than an answer.

    This check is structural, not pattern-based. A long stretch drawn
    from a tiny alphabet is degenerate, whatever character it happens to
    repeat.

    Three shapes have been observed live, all under the whitespace-padded
    noise arm:

    * Collapse from the start. Nemotron-Ultra-253B emitted 24,576
      characters of "0", the whole completion budget, with nothing else.
    * Collapse after a real beginning. Olmo-3.1-32B-Think started
      reasoning, then broke down into about 16,400 repeated U+2010
      hyphens until the budget ran out.
    * Collapse onto a PHRASE rather than a character. Llama-4-Maverick
      looped ``"## Step 1\\n\\n"`` for the whole budget. Its alphabet is
      wide (letters, digits, punctuation), so a character-level test sees
      nothing wrong, and the response gets mislabeled as a mere
      formatting problem.

    The second shape is why this function checks the tail separately.
    The third shape is why it checks words as well as characters. Getting
    this wrong is not cosmetic: labeling a collapse `TRUNCATED` blames
    the completion budget, and labeling it `MULTIPLE_VALUES` blames the
    parser, when the real finding is that the condition breaks the model
    outright.
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
    if (
        len(stripped) >= _DEGENERATE_MIN_LEN
        and len(tail) >= _DEGENERATE_TAIL
        and len(set(tail)) <= _DEGENERATE_ALPHABET
    ):
        return True
    # Phrase-level looping: a long stretch of text drawing on only a handful
    # of distinct words.
    words = stripped.split()
    if len(words) < _DEGENERATE_MIN_WORDS:
        return False
    word_tail = words[-_DEGENERATE_MIN_WORDS:]
    if len(set(word_tail)) <= _DEGENERATE_WORD_ALPHABET:
        return True
    # Vocabulary collapse across the whole response, for a model that loops
    # and then wanders instead of looping all the way to the end.
    return (
        len(words) >= _DEGENERATE_RATIO_MIN_WORDS
        and len(set(words)) / len(words) <= _DEGENERATE_WORD_RATIO
    )


#: Characters a bare arithmetic expression may contain.
_ARITHMETIC_ONLY = re.compile(r"[\d\s+\-*/().]+")
#: AST nodes `_eval_arithmetic` will evaluate. Pow is deliberately excluded --
#: ``9**9**9`` is a denial-of-service, not an answer.
_ARITHMETIC_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod)


def _eval_arithmetic(text: str) -> Optional[int]:
    """Evaluate a bare arithmetic expression, or return None.

    A model sometimes answers a counting question with the calculation
    rather than its result -- ``"2520/2"`` when 1260 was asked for. Both
    naive extraction rules mis-grade that case: the first integer is the
    numerator, the last is the divisor, and neither is the answer the
    model actually gave.

    This function walks a validated AST, instead of calling ``eval``. It
    honors only numeric literals and the operators in
    `_ARITHMETIC_BINOPS`, so nothing here can execute arbitrary code, even
    if a response is hostile.

    Returns
    -------
    Optional[int]
        The value, when the expression is well-formed and integral
        (2520/2 is 1260.0, which counts). None otherwise, including for a
        division by zero or a non-integral result.
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


def _safe_int(digits: str) -> Optional[int]:
    """Convert `digits` to int, or return None when it is absurdly long.

    This function guards two things at once. Python refuses int/str
    conversion beyond 4,300 digits and raises ValueError, so an unguarded
    ``int()`` in the grading path would crash rather than produce a bad
    grade. That crash took a live run down once, when a model emitted a
    20,379-digit run. A number that long is also not a plausible answer:
    these quizzes count occurrences, bounded by lcm(1..9) = 2520.
    """
    stripped = digits.lstrip("-")
    if len(stripped) > _MAX_ANSWER_DIGITS:
        return None
    try:
        return int(digits)
    except ValueError:  # pragma: no cover -- length check already covers it
        return None


def _preamble(text: str) -> Optional[str]:
    """Classify a response that carries extra material around its answer."""
    return VERBOSE if len(text.strip()) > _LONG_RESPONSE else PREFIXED


def parse_tof(text: str) -> ParseResult:
    """Extract a True/False verdict, and classify contract compliance.

    The contract is "return exactly one of these two strings and nothing
    else". So anything beyond a bare ``True``/``False`` is a violation,
    even when this function can still recover the verdict.
    """
    if not text or not text.strip():
        return ParseResult(None, EMPTY)
    if is_degenerate(text):
        return ParseResult(None, DEGENERATE)

    stripped = text.strip()

    # Fully compliant: exactly the demanded token (the original strict rule).
    if stripped.lower() in ("true", "false"):
        return ParseResult(stripped.lower() == "true", None)

    # Tolerated as compliant-ish: the bare token wearing punctuation or
    # markup, e.g. "**False**" or '"True".' This still violates "nothing
    # else", but it is a purely cosmetic violation, so it gets its own
    # label.
    if re.fullmatch(r"[\s*_`\"'.]*(true|false)[\s*_`\"'.]*", stripped, re.IGNORECASE):
        return ParseResult(_TOF_TOKEN.search(stripped).group(1).lower() == "true", MARKUP)

    # A response that ENDS in a verdict did conclude, however much text
    # came before it. When the text also contains a DIFFERENT verdict
    # earlier, that disagreement is the more informative violation to
    # report -- more informative than whatever wrapping the final verdict
    # wore.
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

    # Long, and never concluded: a chain cut off mid-thought. This function
    # deliberately does not mine it for a verdict -- see the module
    # docstring.
    return ParseResult(None, TRUNCATED)


def parse_numeric(text: str) -> ParseResult:
    """Extract an integer answer, and classify contract compliance.

    The contract is "return exactly one integer and nothing else". So
    prose, markup, or a worked calculation around the number are all
    violations. The worked-calculation case is the dangerous one: the
    original first-integer rule silently graded such an answer on an
    operand.
    """
    if not text or not text.strip():
        return ParseResult(None, EMPTY)
    if is_degenerate(text):
        return ParseResult(None, DEGENERATE)

    stripped = text.strip()

    if re.fullmatch(r"-?\d+", stripped):
        value = _safe_int(stripped)
        return ParseResult(value, None if value is not None else DEGENERATE)

    # A bare integer wearing markup or punctuation, e.g. "**42**" or
    # '"42".' Only the number is present, so only the "no punctuation"
    # clause was broken.
    if re.fullmatch(r"[\s*_`\"'.]*-?\d+[\s*_`\"'.]*", stripped):
        return ParseResult(_safe_int(_INT.search(stripped).group()), MARKUP)

    # A bare integer in answer markup, e.g. "\boxed{280}".
    boxed = _TERMINAL_INT.fullmatch(stripped)
    if boxed:
        return ParseResult(_safe_int(boxed.group(1)), MARKUP)

    # A calculation rather than its result, e.g. "2520/2". This check runs
    # before any integer-picking rule, because every such rule would score
    # an operand instead.
    arithmetic = _eval_arithmetic(stripped)
    if arithmetic is not None:
        return ParseResult(arithmetic, EXPRESSION)

    ints = _INT.findall(stripped)
    if not ints:
        return ParseResult(None, TRUNCATED if len(stripped) > _LONG_RESPONSE else UNPARSEABLE)

    if len(ints) == 1:
        return ParseResult(_safe_int(ints[0]), _preamble(stripped))

    # Several integers appear. A concluding "Answer: N", or a terminal
    # integer, is the result; the earlier ones are working. Taking the
    # FIRST integer (the old rule) is what produced silent mis-grades.
    terminal = _TERMINAL_INT.search(stripped[-_TAIL_WINDOW:])
    if terminal:
        return ParseResult(_safe_int(terminal.group(1)), MULTIPLE_VALUES)
    lead = _ANSWER_LEAD.split(stripped, maxsplit=1)
    if len(lead) > 1:
        after = _INT.findall(lead[1])
        if after:
            return ParseResult(_safe_int(after[0]), MULTIPLE_VALUES)
    return ParseResult(_safe_int(ints[-1]), MULTIPLE_VALUES)


def parse_for(question: QnA, text: str) -> ParseResult:
    """Parse `text` with the extractor matching `question`'s answer type.

    For any QnA subclass this module does not special-case, this
    function falls back to the question's own ``condition``. An unknown
    question type then degrades to the original strict behavior, instead
    of being silently mis-parsed.
    """
    if isinstance(question, ToF):
        return parse_tof(text)
    if isinstance(question, Numeric):
        return parse_numeric(text)
    try:
        return ParseResult(question.condition(text), None)
    except ValueError:
        return ParseResult(None, UNPARSEABLE)
