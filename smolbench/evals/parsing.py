"""Separate "wrong" from "wrongly formatted" when extracting an answer.

The eval prompts carry an explicit output contract ("exactly one of True/False
and nothing else" for ToF quizzes, "exactly one integer and nothing else" for
the periodic studies). The strict graders in ``smolbench.evals.quiz`` conflate a
wrong answer with a right answer in the wrong format, in both directions:
``ToF.condition`` raises on ``"Answer: False"``, while ``Numeric.condition``
takes the FIRST integer, silently scoring ``"2520 // 8 = 315\\n\\n315"`` as 2520.

This module extracts the answer robustly and reports the contract violation
SEPARATELY (see the label constants below), so "how often was the model right?"
and "how often did it obey the instructions?" can be asked independently. That
split is load-bearing for the induction benchmarks: the ``noise_intens`` arm's
token-matched whitespace pad, meant to control only for LENGTH, measurably
degrades instruction following too.

Recovery is deliberately conservative: mining a verdict from anywhere would
invent verdicts out of chains cut off by the completion budget, so a long
response is mined only when it ENDS in a verdict and otherwise gets `TRUNCATED`.
Repetition collapse gets its own `DEGENERATE` label for the same reason --
calling it a parse failure would misattribute the finding.
"""

import ast
import re
from dataclasses import dataclass
from typing import Optional

from smolbench.evals import Answer, Numeric, QnA, ToF

# --- Violation labels -------------------------------------------------------
# None means the response obeyed the contract exactly; every other label names
# one specific way it did not, so the failure modes are counted separately
# instead of collapsing into "invalid".

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
#: get it wrong: first-integer scores the numerator, last-integer the divisor,
#: while the model actually answered correctly.
EXPRESSION = "unevaluated-expression"

# Beyond this length a response is prose/reasoning, not an answer: only a
# terminal verdict is trusted past it (see the module docstring).
_LONG_RESPONSE = 200
#: How much of the tail counts as "the concluding statement".
_TAIL_WINDOW = 60
# Collapse is detected by these alphabet/vocabulary thresholds, NOT by a
# repeated-substring regex like (.+?)\1{9,}: a backreference only sees EXACT
# repeats, so it false-positives on benign formatting runs ("-" rules, "\n"
# pads -- shapes test_not_degenerate pins) yet misses vocabulary collapse that
# never repeats verbatim, and on long genuine prose (the common case) its
# backtracking measured ~100x slower than these set-size counts.
#: A long response built from this few distinct characters is collapse.
_DEGENERATE_ALPHABET = 3
_DEGENERATE_MIN_LEN = 500
#: Tail examined for a collapse that starts partway through a response: long
#: enough that ordinary repetition (a rule of dashes, a run of newlines) does
#: not trip it, short enough to catch a model that broke down near the end.
_DEGENERATE_TAIL = 400
#: Word-level collapse: how many trailing words to examine, and how few
#: distinct words among them mean the model is looping on a phrase. 60
#: consecutive words of genuine prose carry far more than 8 distinct tokens.
_DEGENERATE_MIN_WORDS = 60
_DEGENERATE_WORD_ALPHABET = 8
#: Whole-response vocabulary collapse. Llama-4-Maverick looped "## Step 1" for
#: thousands of words, then drifted into hallucinated text: neither its tail nor
#: its character alphabet looks wrong, yet it used 67 distinct words across
#: 4,746 (1.4%). Genuine reasoning of that length runs an order of magnitude
#: richer, so a ratio this low means the model stopped composing.
_DEGENERATE_RATIO_MIN_WORDS = 200
_DEGENERATE_WORD_RATIO = 0.05

#: Longest integer this module will convert. Python raises ValueError above
#: 4,300 digits (the int/str conversion limit) and a degenerating model does
#: emit numbers that long: one 20,379-digit run crashed grading and took a live
#: run down. The eval's answers are counts bounded by lcm(1..9) = 2520, so more
#: digits than this is not an answer under any reading.
_MAX_ANSWER_DIGITS = 40

_TOF_TOKEN = re.compile(r"\b(true|false)\b", re.IGNORECASE)
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
#: The multi-integer tail check: like ``_TERMINAL_INT`` but the ``boxed``
#: markup itself is optional, so a plain concluding integer ("... = 315")
#: also counts as the stated result. ``_TERMINAL_INT`` keeps ``boxed``
#: mandatory because its fullmatch branch labels the whole response MARKUP.
_TERMINAL_ANSWER_INT = re.compile(
    r"(?:answer\s*[:\-=]*\s*)?\**\s*(?:\\?boxed\{?\s*)?(-?\d+)\s*\}?\**\s*[.!*\"'`]*\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParseResult:
    """One response's extracted answer plus its contract compliance.

    ``value`` is None when nothing could be extracted; ``violation`` is None when
    the response obeyed the contract exactly, else one of the labels above.
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

    Structural, not pattern-based: a long stretch drawn from a tiny alphabet is
    degenerate whatever it repeats. Three shapes seen live, all under the
    whitespace-padded noise arm, motivate the three tests -- collapse from the
    start (Nemotron-Ultra-253B: 24,576 characters of "0"), collapse after a real
    beginning (Olmo-3.1-32B-Think: ~16,400 U+2010 hyphens, the TAIL check), and
    collapse onto a PHRASE with a wide character alphabet (Llama-4-Maverick
    looping ``"## Step 1\\n\\n"``, the WORD checks). Misclassifying these would
    blame the completion budget (`TRUNCATED`) or the parser (`MULTIPLE_VALUES`)
    for a finding about the condition breaking the model.
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
    # Phrase-level looping: a long stretch drawing on a handful of words.
    words = stripped.split()
    if len(words) < _DEGENERATE_MIN_WORDS:
        return False
    word_tail = words[-_DEGENERATE_MIN_WORDS:]
    if len(set(word_tail)) <= _DEGENERATE_WORD_ALPHABET:
        return True
    # Whole-response vocabulary collapse, for a model that loops and then
    # wanders instead of looping all the way to the end.
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
    """Evaluate a bare arithmetic expression (``"2520/2"`` -> 1260), or None.

    Walks a validated AST instead of calling ``eval``, honoring only numeric
    literals and `_ARITHMETIC_BINOPS`, so a hostile response cannot run code.
    Deliberately not a third-party evaluator (simpleeval, asteval): those
    accept a far wider surface (pow, names, comprehensions) than the "one
    integer" contract wants, and the repo keeps runtime dependencies minimal.

    Returns
    -------
    int or None
        None for a malformed expression, division by zero, or a non-integral
        result (2520/2 = 1260.0 counts as integral).
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
    """Convert `digits` to int, or return None past `_MAX_ANSWER_DIGITS`.

    Python raises ValueError on int/str conversion beyond 4,300 digits, so an
    unguarded ``int()`` crashes grading -- a 20,379-digit run took a live run
    down.
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

    The contract is "exactly one of these two strings and nothing else", so
    anything beyond a bare ``True``/``False`` is a violation even when the verdict
    is still recovered.
    """
    if not text or not text.strip():
        return ParseResult(None, EMPTY)
    if is_degenerate(text):
        return ParseResult(None, DEGENERATE)

    stripped = text.strip()

    # Fully compliant: exactly the demanded token.
    if stripped.lower() in ("true", "false"):
        return ParseResult(stripped.lower() == "true", None)

    # The bare token wearing punctuation or markup, e.g. "**False**" or
    # '"True".' Still violates "nothing else", but only cosmetically, so it
    # gets its own label.
    if re.fullmatch(r"[\s*_`\"'.]*(true|false)[\s*_`\"'.]*", stripped, re.IGNORECASE):
        return ParseResult(_TOF_TOKEN.search(stripped).group(1).lower() == "true", MARKUP)

    # A response that ENDS in a verdict did conclude, however much text came
    # before it. An earlier DIFFERENT verdict is the more informative violation
    # to report than whatever wrapping the final verdict wore.
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

    # Long and never concluded: a chain cut off mid-thought, deliberately not
    # mined for a verdict -- see the module docstring.
    return ParseResult(None, TRUNCATED)


def parse_numeric(text: str) -> ParseResult:
    """Extract an integer answer, and classify contract compliance.

    The contract is "exactly one integer and nothing else", so prose, markup, or
    a worked calculation around the number are all violations. The worked
    calculation is the dangerous case: the first integer is an operand.
    """
    if not text or not text.strip():
        return ParseResult(None, EMPTY)
    if is_degenerate(text):
        return ParseResult(None, DEGENERATE)

    stripped = text.strip()

    if re.fullmatch(r"-?\d+", stripped):
        value = _safe_int(stripped)
        # Over-long is UNPARSEABLE, not DEGENERATE: is_degenerate already
        # judged the text above, and a varied out-of-range integer is not a
        # repetition collapse -- labeling it one would inflate the census.
        return ParseResult(value, None if value is not None else UNPARSEABLE)

    # A bare integer wearing markup or punctuation, e.g. "**42**" or '"42".'
    # Only the number is present, so only the "no punctuation" clause broke.
    if re.fullmatch(r"[\s*_`\"'.]*-?\d+[\s*_`\"'.]*", stripped):
        return ParseResult(_safe_int(_INT.search(stripped).group()), MARKUP)

    # A bare integer in answer markup, e.g. "\boxed{280}".
    boxed = _TERMINAL_INT.fullmatch(stripped)
    if boxed:
        return ParseResult(_safe_int(boxed.group(1)), MARKUP)

    # A calculation rather than its result, e.g. "2520/2". Before any
    # integer-picking rule, each of which would score an operand instead.
    arithmetic = _eval_arithmetic(stripped)
    if arithmetic is not None:
        return ParseResult(arithmetic, EXPRESSION)

    ints = _INT.findall(stripped)
    if not ints:
        return ParseResult(None, TRUNCATED if len(stripped) > _LONG_RESPONSE else UNPARSEABLE)

    if len(ints) == 1:
        return ParseResult(_safe_int(ints[0]), _preamble(stripped))

    # Several integers: a concluding "Answer: N" or a terminal integer is the
    # result, the earlier ones are working. FIRST would score the working.
    terminal = _TERMINAL_ANSWER_INT.search(stripped[-_TAIL_WINDOW:])
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

    A QnA subclass this module does not special-case falls back to the
    question's own strict ``condition`` rather than being mis-parsed.
    """
    if isinstance(question, ToF):
        return parse_tof(text)
    if isinstance(question, Numeric):
        return parse_numeric(text)
    try:
        return ParseResult(question.condition(text), None)
    except ValueError:
        return ParseResult(None, UNPARSEABLE)
