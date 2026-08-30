"""Drive a Lean 4 REPL session for one theorem, via `lean_interact`.

This is the Lean-side backend `smolbench.deduction.lean.verify` sits on top of.
It replaces the deprecated LeanDojo v1 ``Dojo`` interaction layer, which cannot
drive Lean >= v4.20 and therefore cannot reach the new corpus (mathlib4 at Lean
v4.34.0-rc2). `lean_interact` wraps `leanprover-community/repl
<https://github.com/leanprover-community/repl>`_, which tracks current Lean.

The whole module exists to answer one question repeatedly: *starting from proof
state ``s``, what does Lean do with tactic ``t``?* Getting there needs four
steps, and each is a separately testable seam here:

1. Find the theorem's source text (`declaration_text`, or a corpus row that
   already carries it).
2. Cut the statement off its proof and rename it (`find_statement_end`,
   `rename_declaration`, `theorem_statement_stub`).
3. Build an environment that can elaborate that statement, and elaborate a
   ``:= by sorry`` stub in it; the REPL reports the stub's ``sorry`` as a proof
   state (`open_session`).
4. Send tactics at that state and read the replies (`ReplSession.step`,
   `classify_step`).

Known limitations, stated plainly
---------------------------------
**The environment is import-only.** `open_session` builds the elaboration
environment with a single ``import <Module>`` of the theorem's own module. That
restores the module's *imports* but NOT its file-level ``open`` / ``variable`` /
``namespace`` scope, nor any ``local notation``. A theorem statement that
depends on such scope will fail to elaborate; that surfaces as a `ReplError`
naming the theorem and quoting Lean's messages, which `verify` reports as
``"exception"`` (or ``"replay_failed"`` when it happens under a prefix replay).
The alternative -- re-elaborating the whole file prefix up to the declaration --
is correct but much more expensive, and the spec chose cost. Environment
construction is deliberately kept a separate step from statement derivation
(`_default_server_factory` / the ``import`` command vs. `theorem_statement_stub`)
so a file-prefix environment can be dropped in later without `verify.py`
changing at all.

**None of this has run against a real Lean toolchain.** The development box has
no ``elan``/``lake`` and no built mathlib4, so every REPL interaction below is
written against `lean_interact`'s documented types and exercised only against
scripted fakes. The pure text-processing parts (`find_statement_end`,
`rename_declaration`, `declaration_text`, `module_name`) *were* measured against
a real mathlib4 checkout at the corpus commit; those measurements are cited at
the rules they justify.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Literal

from lean_interact import Command, LeanREPLConfig, LeanServer, LocalProject, ProofStep
from lean_interact.interface import LeanError

logger = logging.getLogger(__name__)


#: Name every theorem statement is re-declared under before it is sent to the
#: REPL. See `rename_declaration` for why a rename is mandatory rather than
#: cosmetic.
TARGET_NAME: str = "smolbenchTarget"

#: Environment variable naming the mathlib4 checkout to run the REPL against.
#: Read at CALL time by `mathlib_root`, never cached at import, so a test or a
#: late ``os.environ`` assignment takes effect.
MATHLIB_ROOT_ENV: str = "SMOLBENCH_MATHLIB_ROOT"


class ReplError(Exception):
    """A REPL-level (infrastructure) failure: no Lean verdict was obtained.

    Design: this is a direct `Exception` subclass and deliberately NOT a
    `RuntimeError`. `verify.verify_proof_tail` catches `RuntimeError` and maps
    it to verdict ``"replay_failed"``, whose meaning is "the RECORDED
    ground-truth prefix does not replay" -- a statement about the *corpus*. A
    dead REPL, a timeout, or an unelaborable statement says nothing about the
    corpus and must land on ``"exception"`` instead. Making `ReplError` a
    `RuntimeError` would silently reclassify every infrastructure outage as a
    corpus defect.
    """


class StatementError(ReplError):
    """A DETERMINISTIC failure to obtain a proof state for a theorem's statement.

    Raised when the declaration has no statement/proof boundary to cut at, or
    when the resulting stub does not elaborate in the environment built for it.

    Design: this exists purely to split `open_session`'s retry policy in two.
    Starting a Lean server and importing a module are worth retrying -- a cold
    or racing ``lake`` build cache makes both transiently fail, which is what
    the backoff is for. Elaborating the stub is not: the statement, the
    environment, and Lean are all fixed, so attempt 3 fails exactly as attempt 1
    did. Retrying it costs
    ``sum(_REPL_OPEN_BACKOFF_S)`` seconds of sleeping plus three Lean process
    startups per affected theorem, and under this backend's import-only
    environment (see the module docstring) that failure is EXPECTED to be
    common, not rare.

    Still a `ReplError`, so every caller that already handles the general case
    -- notably `verify`, which must report it as ``"exception"`` and never as
    ``"replay_failed"`` -- needs no change.
    """


@dataclass(frozen=True)
class StepOutcome:
    """What Lean did with one tactic, normalised away from `lean_interact` types.

    Field order is part of the contract: callers construct these positionally.
    """

    #: What happened. ``"success"`` (whole proof closed), ``"lean_error"``
    #: (Lean rejected the tactic), ``"incomplete"`` (tactic ran, goals remain),
    #: ``"given_up"`` (a ``sorry`` closed or contaminated the proof), or
    #: ``"exception"`` (the REPL itself failed -- see `classify_step`).
    kind: Literal["success", "lean_error", "incomplete", "given_up", "exception"]
    #: Proof-state id to branch the NEXT tactic from. None when there is no
    #: usable continuation (``"lean_error"``, ``"exception"``).
    proof_state: int | None
    #: Lean's message text (``"lean_error"``) or the REPL's message text
    #: (``"exception"``); None for every other kind. Never empty when set.
    error: str | None
    #: Remaining goals, ``"\\n\\n"``-joined, only for ``"incomplete"``; None
    #: otherwise (including an ``"incomplete"`` with an empty goal list).
    goals_pp: str | None


# ---------------------------------------------------------------------------
# Path / module-name plumbing
# ---------------------------------------------------------------------------


def module_name(file_path: str) -> str:
    """Convert a corpus ``file_path`` into the Lean module name to ``import``.

    Parameters
    ----------
    file_path : str
        Repo-relative path of the declaring source, e.g.
        ``"Mathlib/Algebra/Group/Basic.lean"``. Always ``/``-separated: this is
        a value out of the LeanDojo trace, not a host path.

    Returns
    -------
    str
        The dotted module name, e.g. ``"Mathlib.Algebra.Group.Basic"``.

    Raises
    ------
    ValueError
        `file_path` is empty or does not end in ``.lean``. Naming the offending
        path matters: a bad ``file_path`` otherwise reaches the REPL as an
        ``import`` of a module that does not exist, and Lean's message for that
        does not mention the corpus row that produced it.

    Examples
    --------
    >>> module_name("Mini/A.lean")
    'Mini.A'
    """
    if not file_path or not file_path.endswith(".lean"):
        raise ValueError(f"not a Lean source path (expected a '.lean' suffix): {file_path!r}")
    return file_path[: -len(".lean")].replace("/", ".")


def mathlib_root(root: str | Path | None = None) -> Path:
    """Resolve the mathlib4 checkout the REPL should run inside.

    Resolution order: the `root` argument, else the ``SMOLBENCH_MATHLIB_ROOT``
    environment variable read AT CALL TIME. Nothing is cached and nothing is
    read at import, so the variable can be set after this module is imported.

    Parameters
    ----------
    root : str or Path, optional
        Explicit override. When given, the environment is not consulted.

    Returns
    -------
    Path
        The checkout root, as given. Symlinks are deliberately NOT resolved:
        callers (and tests) compare the result against the literal path they
        supplied, and a Lean project reached through a symlinked path works.

    Raises
    ------
    RuntimeError
        Nothing was configured, the path is missing or is not a directory, or
        the directory has no ``lean-toolchain`` file. Every message is
        actionable, and the checks run in that order: the "not a Lean project"
        diagnosis is only meaningful once the directory is known to exist.
        This is the cheapest configuration gate in the whole backend, and
        `open_session` runs it before starting any Lean process precisely so a
        misconfiguration costs milliseconds rather than a REPL startup.
    """
    # Design: read the environment inside the function, never at module scope.
    # A module-level `os.getenv` would freeze whatever the value was at first
    # import -- which for a long-lived sweep process is "whatever the CLI had
    # not yet configured".
    configured = root if root is not None else os.getenv(MATHLIB_ROOT_ENV)
    if not configured:
        raise RuntimeError(
            f"no mathlib4 checkout configured: set {MATHLIB_ROOT_ENV} to a mathlib4 "
            "checkout that has been built with elan/lake (the directory containing "
            "'lean-toolchain' and 'lakefile.lean'), or pass root= explicitly"
        )

    path = Path(configured)
    if not path.is_dir():
        raise RuntimeError(
            f"{MATHLIB_ROOT_ENV} does not point at an existing directory: {path}"
        )
    if not (path / "lean-toolchain").is_file():
        raise RuntimeError(
            f"{path} does not look like a Lean project: no 'lean-toolchain' file. "
            f"Point {MATHLIB_ROOT_ENV} at a mathlib4 checkout built with elan/lake."
        )
    return path


# ---------------------------------------------------------------------------
# Lean source scanning
# ---------------------------------------------------------------------------

#: Bracket pairs `find_statement_end` counts. Beyond ASCII, Lean uses ``⟨⟩``
#: for anonymous constructors and ``⁅⁆`` for Lie brackets / interval notation,
#: both of which can legitimately wrap a ``:=``.
_OPEN_BRACKETS = "([{⟨⁅"
_CLOSE_BRACKETS = ")]}⟩⁆"

#: Characters that terminate a declaration's identifier token, in addition to
#: whitespace: binder openers and the type ascription colon.
_IDENT_TERMINATORS = ":({[⦃⟨"

#: Declaration keywords `rename_declaration` will rename. ``def`` is
#: deliberately absent: the corpus holds theorems, and a ``def`` has no tactic
#: proof to slice, so accepting one would quietly produce a nonsense stub.
_DECLARATION_KEYWORDS = ("theorem", "lemma")

#: Characters that may continue a Lean identifier. Used for the word-boundary
#: test around a keyword, so ``mytheorem`` / ``theorem_of`` / ``Foo.lemma`` are
#: not mistaken for the keyword itself.
_IDENT_CHARS = re.compile(r"[A-Za-z0-9_'.!?]")


def _iter_code_positions(text: str) -> Iterator[int]:
    """Yield, in order, the index of every character of `text` outside a comment.

    One left-to-right pass. Indices are offsets into the ORIGINAL `text`, which
    is why comments are skipped in-place rather than stripped into a new string:
    every caller needs to slice `text` at the index it gets back.

    Nested block comments (``/- /- -/ -/``) are NOT supported: the first ``-/``
    closes the comment. mathlib4 does not nest them in declaration headers, and
    supporting nesting would need a depth counter whose only effect on this
    corpus is to make the scanner harder to reason about.

    Yields
    ------
    int
        Index into `text` of a character that is not inside a ``--`` line
        comment or a ``/- ... -/`` block comment (doc comments ``/-- ... -/``
        are block comments and are skipped too).
    """
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("/-", i):
            end = text.find("-/", i + 2)
            i = n if end == -1 else end + 2
            continue
        if text.startswith("--", i):
            end = text.find("\n", i)
            i = n if end == -1 else end + 1
            continue
        yield i
        i += 1


def find_statement_end(text: str) -> int | None:
    """Index of the ``:=`` that separates a declaration's statement from its proof.

    The boundary is the first ``:=`` that is simultaneously at bracket depth 0
    and outside any comment. Both exclusions were measured against the real
    mathlib4 checkout at the corpus commit before being specified, and both are
    load-bearing rather than defensive:

    * **Depth.** An ``autoParam`` default puts a ``:=`` inside parentheses --
      ``theorem foo (h : Nat := by simp) : ...``. Splitting on the first ``:=``
      truncates the signature mid-binder and produces a statement that cannot
      elaborate. Real instance: ``Basis.reindexFinsetRange_self``.
    * **Comments.** A doc comment or trailing ``--`` comment above or beside the
      declaration routinely contains ``:=``.

    Over the 300 pinned corpus theorems located in the real checkout, this rule
    found a boundary for 228 of the 229 it was applied to. The single miss,
    ``Filter.bot_pow``, is an equation-style proof (``| 0, h => ...``) that has
    no ``:=`` at all. No heuristic rescues it here on purpose: it carries no
    traced tactics, so it is never verified.

    Parameters
    ----------
    text : str
        Declaration source, starting at or before the declaration keyword.

    Returns
    -------
    int or None
        Index into `text` of the ``:``. ``text[:index]`` is the statement,
        ``text[index:]`` the proof. None when no depth-0, non-comment ``:=``
        exists.
    """
    depth = 0
    for i in _iter_code_positions(text):
        ch = text[i]
        if ch in _OPEN_BRACKETS:
            depth += 1
        elif ch in _CLOSE_BRACKETS:
            # Clamp at 0: a slice that starts mid-expression can open with a
            # closer, and going negative would make a later `:=` look nested.
            depth = max(depth - 1, 0)
        elif depth == 0 and ch == ":" and text.startswith(":=", i):
            return i
    return None


def rename_declaration(text: str, target_name: str = TARGET_NAME) -> str:
    """Rewrite a declaration's identifier to `target_name`, leaving all else intact.

    The statement is re-elaborated in an environment that ALREADY contains the
    original theorem (`open_session` ``import``\\ s its module), so re-declaring
    it under its own name raises Lean's "has already been declared" for the
    *modal* case, not an edge case. Renaming is therefore mandatory.

    The keyword is located with the comment-aware scanner (`_iter_code_positions`)
    rather than a regex. That is not defensiveness: 213 of mathlib4's 106,445
    column-0 ``theorem``/``lemma`` declarations are preceded by a docstring
    containing the words "theorem <word>" or "lemma <word>". A naive regex
    renames the docstring text and leaves the declaration untouched -- a silent
    miss that only shows up later as an "already declared" elaboration error.

    Parameters
    ----------
    text : str
        Declaration source. Leading attributes (``@[simp]``), modifiers
        (``private``/``protected``/``nonrec``) and any preceding docstring are
        returned byte-identical.
    target_name : str, optional
        Replacement identifier. Defaults to `TARGET_NAME`.

    Returns
    -------
    str
        `text` with the declaration's identifier token replaced. The identifier
        token runs from the first non-whitespace character after the keyword to
        the first whitespace or one of ``:({[⦃⟨``.

    Raises
    ------
    ValueError
        No ``theorem``/``lemma`` keyword occurs outside a comment, or one does
        but is not followed by an identifier. The message quotes a truncated
        prefix of `text` so the caller can see what it handed over. ``def`` is
        not accepted; see `_DECLARATION_KEYWORDS`.

    Examples
    --------
    >>> rename_declaration("theorem add_comm (a b : Nat) : a + b = b + a", "tgt")
    'theorem tgt (a b : Nat) : a + b = b + a'
    """
    n = len(text)
    for i in _iter_code_positions(text):
        keyword = next((kw for kw in _DECLARATION_KEYWORDS if text.startswith(kw, i)), None)
        if keyword is None:
            continue
        # Word boundaries on both sides, so `mytheorem`, `theorem_of` and
        # `Foo.lemma` are not mistaken for the keyword.
        if i > 0 and _IDENT_CHARS.match(text[i - 1]):
            continue
        after = i + len(keyword)
        if after < n and _IDENT_CHARS.match(text[after]):
            continue

        # The identifier is the next token: skip the separating whitespace,
        # then run to the first whitespace or binder/ascription opener.
        start = after
        while start < n and text[start].isspace():
            start += 1
        end = start
        while end < n and not text[end].isspace() and text[end] not in _IDENT_TERMINATORS:
            end += 1
        if end == start:
            raise ValueError(
                f"{keyword!r} keyword is not followed by an identifier in: {text[:120]!r}"
            )
        return text[:start] + target_name + text[end:]

    raise ValueError(
        "no 'theorem'/'lemma' declaration keyword outside a comment in: " f"{text[:120]!r}"
    )


#: Keywords that, at column 0, start something OTHER than the declaration being
#: sliced -- i.e. that terminate `declaration_text`'s slice. Broader than
#: `_DECLARATION_KEYWORDS` because a slice must also stop at ``end``,
#: ``namespace``, ``open``, ``section`` and friends, none of which are
#: declarations but all of which are unambiguously outside the current one.
_TOP_LEVEL_KEYWORDS = frozenset(
    {
        "theorem", "lemma", "def", "instance", "abbrev", "structure", "class",
        "inductive", "namespace", "end", "section", "open", "variable",
        "noncomputable", "protected", "private", "nonrec", "universe", "attribute",
        "example", "macro", "syntax", "notation", "deriving", "alias", "set_option",
        "import",
    }
)

#: Keywords that open a DECLARATION, as opposed to a command or a scope marker.
#: A strict subset of `_TOP_LEVEL_KEYWORDS`, and the arming set for
#: `declaration_text`'s stop rule. Deliberately excludes ``set_option``,
#: ``open``, ``namespace``, ``variable`` and friends: those can legitimately
#: appear in a declaration's own header (``set_option maxHeartbeats 400000 in``
#: above a theorem), and arming on one would truncate the slice to the header.
_DECLARATION_OPENERS = frozenset(
    {
        "theorem", "lemma", "def", "instance", "abbrev", "structure", "class",
        "inductive", "example", "macro", "syntax", "notation", "alias",
    }
)

#: Modifiers that may precede the declaration keyword on the SAME line. Stripped
#: before asking whether a line opens a declaration (`_opens_a_declaration`).
_DECLARATION_MODIFIERS = frozenset(
    {"private", "protected", "noncomputable", "nonrec", "partial", "unsafe", "scoped", "local"}
)

_LEADING_ATTRIBUTE = re.compile(r"^@\[[^\]]*\]\s*")
_LEADING_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")


def _starts_top_level(line: str) -> bool:
    """True when `line` begins, at column 0, something outside the current slice."""
    if not line or line[0].isspace():
        return False
    if line.startswith("@[") or line.startswith("/--"):
        return True
    word = _LEADING_WORD.match(line)
    return word is not None and word.group(0) in _TOP_LEVEL_KEYWORDS


def _opens_a_declaration(line: str) -> bool:
    """True when `line` is the declaration's own keyword line (`theorem`/`def`/...).

    Attributes and same-line modifiers are stripped first, so
    ``protected theorem Foo.bar`` and ``@[simp] lemma baz`` both count.
    """
    if not line or line[0].isspace():
        return False
    rest = _LEADING_ATTRIBUTE.sub("", line)
    tokens = rest.split()
    idx = 0
    while idx < len(tokens) and tokens[idx] in _DECLARATION_MODIFIERS:
        idx += 1
    if idx >= len(tokens):
        return False
    word = _LEADING_WORD.match(tokens[idx])
    return word is not None and word.group(0) in _DECLARATION_OPENERS


def _advance_comment_state(line: str, in_comment: bool) -> bool:
    """Return whether a ``/- ... -/`` block is still open at the end of `line`.

    Nested blocks are not tracked (see `_iter_code_positions`); the first ``-/``
    closes. A ``--`` line comment outside a block ends the scan of the line.
    """
    i = 0
    n = len(line)
    while i < n:
        if in_comment:
            if line.startswith("-/", i):
                in_comment = False
                i += 2
                continue
        else:
            if line.startswith("--", i):
                break  # rest of the line is a line comment; block state unchanged
            if line.startswith("/-", i):
                in_comment = True
                i += 2
                continue
        i += 1
    return in_comment


def declaration_text(root: Path, file_path: str, start_line: int, max_lines: int = 400) -> str:
    """Slice one declaration's source out of ``root / file_path``.

    `start_line` is 1-INDEXED. That is the convention
    `smolbench.deduction.lean.premises.slice_full_decl` already uses for the same
    class of LeanDojo trace positions (it converts with an explicit
    ``start_line - 1``), so the two slicers agree.

    `BenchmarkTheorem.start`'s COLUMN is deliberately ignored. The corpus
    docstring documents that field's indexing convention as untested, and a
    declaration's first line may begin with an attribute or a docstring rather
    than the keyword, so the column would point into the wrong token anyway.
    Starting at the LINE and scanning forward is the robust reading.

    The slice ends before the next line that begins, at column 0, something
    outside this declaration (see `_TOP_LEVEL_KEYWORDS`, plus ``@[`` and
    ``/--``). That stop rule only ARMS once the declaration's own keyword line
    has been consumed -- otherwise a declaration whose first line is a docstring
    or an attribute would stop at its own ``theorem`` line and return only the
    header. Lines inside an open ``/- ... -/`` block never stop the slice.

    Parameters
    ----------
    root : Path
        Checkout root; `file_path` is resolved against it.
    file_path : str
        Repo-relative, ``/``-separated source path.
    start_line : int
        1-indexed line the declaration starts on.
    max_lines : int, optional
        Hard cap on the number of lines returned, so a missing stop keyword
        cannot drag a whole file into the REPL. Default 400.

    Returns
    -------
    str
        The declaration's source, ``rstrip()``\\ ped.

    Raises
    ------
    FileNotFoundError
        ``root / file_path`` does not exist. The message names `file_path`, the
        corpus-side value, not just the absolute path.
    ValueError
        `start_line` is below 1 or past the end of the file.
    """
    source = Path(root) / file_path
    if not source.is_file():
        raise FileNotFoundError(f"no such Lean source: {file_path} (looked in {root})")

    lines = source.read_text(encoding="utf-8").splitlines()
    if start_line < 1:
        raise ValueError(f"start_line must be >= 1 (1-indexed), got {start_line}")
    if start_line > len(lines):
        # `> len(lines)` rather than `>=`: start_line == len(lines) is the last
        # line and is legitimate.
        raise ValueError(
            f"start_line {start_line} is past the end of {file_path} ({len(lines)} lines)"
        )

    collected: list[str] = []
    armed = False
    in_comment = False
    for offset, line in enumerate(lines[start_line - 1 : start_line - 1 + max_lines]):
        if armed and not in_comment and offset > 0 and _starts_top_level(line):
            break
        collected.append(line)
        in_comment = _advance_comment_state(line, in_comment)
        if not in_comment and _opens_a_declaration(line):
            # Arm only AFTER appending, so the declaration's own keyword line
            # is always part of the slice -- true both when it is the start line
            # (`theorem foo ...` at start_line) and when a docstring/attribute
            # precedes it.
            armed = True
    return "\n".join(collected).rstrip()


def theorem_statement_stub(bt, root: Path | None = None, target_name: str = TARGET_NAME) -> str:
    """Build the ``:= by sorry`` stub whose ``sorry`` opens `bt`'s proof state.

    The REPL has no "give me the goal of declaration X" request. The standard
    way to obtain a proof state is to elaborate a declaration whose proof is
    ``sorry``: the response then carries a `Sorry` entry with a ``proofState``
    id, and tactics can be branched from it.

    Parameters
    ----------
    bt : BenchmarkTheorem
        Corpus row. `full_name`, `file_path` and `start` are read; a
        ``theorem_statement`` attribute is preferred when present.
    root : Path, optional
        Checkout root, forwarded to `mathlib_root`. Ignored when `bt` carries
        its own statement.
    target_name : str, optional
        Identifier to declare the stub under. Defaults to `TARGET_NAME`.

    Returns
    -------
    str
        ``"<renamed statement>\\n  := by sorry"``.

    Raises
    ------
    StatementError
        The declaration read from disk has no top-level ``:=`` -- a term-mode or
        equation-style (``| 0, h => ...``) proof -- so there is no statement/proof
        boundary and no proof state can be opened. Message names `bt.full_name`.
        A `ReplError` subclass, so existing handlers are unaffected; the narrower
        type marks the failure as deterministic (`open_session` must not retry
        it).
    ValueError
        The statement has no renameable ``theorem``/``lemma`` keyword
        (`rename_declaration`).
    FileNotFoundError
        The declaring source is missing (`declaration_text`).
    """
    # Step 1: source text. LeanDojo-v2 corpora carry `theorem_statement`
    # directly on the row; the LeanDojo v1 `BenchmarkTheorem` in this repo does
    # not, so this branch is a forward-compatible seam rather than dead code.
    carried = getattr(bt, "theorem_statement", None)
    if isinstance(carried, str) and carried.strip():
        text = carried
        from_disk = False
    else:
        # Called through the module-level name (not a local alias / direct
        # import) so tests and future backends can monkeypatch it.
        text = declaration_text(mathlib_root(root), bt.file_path, bt.start[0])
        from_disk = True

    # Step 2: cut the proof off. Which branch produced the text decides how a
    # missing `:=` is read: a CARRIED statement is already statement-only, so
    # "no `:=`" is normal there; a slice read off disk still contains its proof,
    # so "no `:=`" means the proof is term/equation-style and unusable.
    end = find_statement_end(text)
    if end is None:
        if from_disk:
            raise StatementError(
                f"cannot open a proof state for {bt.full_name}: its declaration has no "
                "top-level ':=' (term-mode or equation-style proof), so there is no "
                "statement/proof boundary to cut at"
            )
        statement = text
    else:
        statement = text[:end]

    # Step 3/4: rename (the original is already in the environment) and stub.
    return f"{rename_declaration(statement, target_name).rstrip()}\n  := by sorry"


# ---------------------------------------------------------------------------
# Response classification
# ---------------------------------------------------------------------------


def classify_step(response) -> StepOutcome:
    """Map one `lean_interact` reply onto a `StepOutcome`.

    THE ORDER OF THE BRANCHES IS THE TAXONOMY. Each one is commented with why it
    sits where it does; reordering them changes what the eval measures.

    Parameters
    ----------
    response : ProofStepResponse or LeanError
        Whatever `lean_interact.LeanServer.run` returned for a `ProofStep`.
        Note `run` RETURNS a `LeanError` object rather than raising when the
        REPL's reply is exactly ``{"message": ...}``.

    Returns
    -------
    StepOutcome
        Normalised outcome. ``error`` is never empty for ``"lean_error"`` or
        ``"exception"``.
    """
    # 1. REPL-level failure. `LeanError` is the REPL's own top-level channel:
    #    malformed request, unknown proof state, crashed process. It is
    #    INFRASTRUCTURE -- the analogue of the old backend's Dojo-open failure --
    #    NOT Lean rejecting the candidate tactic. Getting this backwards makes
    #    infra outages masquerade as broken proofs and inflates `lean_error`.
    if isinstance(response, LeanError):
        return StepOutcome("exception", None, f"REPL error: {response.message}", None)

    status = response.proof_status or ""

    # 2. `sorry` before success. `Completed` WITH a sorry is sorry-shaped
    #    cheating (an LLM emitting `sorry`, or a tactic that leaves one behind),
    #    which the old backend reported as `ProofGivenUp`. Checking success
    #    first would score it as a proof.
    if response.sorries or "sorry" in status.lower():
        return StepOutcome("given_up", None, None, None)

    # 3. Lean rejected the tactic. `get_errors()` filters on
    #    `severity == "error"`, so warnings (`unused variable`, deprecation)
    #    never count as a rejection.
    errors = response.get_errors()
    if errors or status.startswith("Error"):
        message = "\n".join(msg.data for msg in errors)
        return StepOutcome(
            "lean_error",
            None,
            # `error` must never be empty for this kind: a blank Lean error in a
            # results row is indistinguishable from a bug in this classifier.
            message or f"Lean reported proof status {status!r} with no error message",
            None,
        )

    # 4. Whole proof closed. Keyed on `proofStatus`, not on `goals == []`:
    #    `proofStatus` is the status of the WHOLE proof and is authoritative,
    #    whereas an empty `goals` list can coexist with unfinished sibling goals.
    if status.startswith("Completed"):
        return StepOutcome("success", response.proof_state, None, None)

    # 5. Otherwise the tactic ran and work remains.
    goals_pp = "\n\n".join(response.goals) if response.goals else None
    return StepOutcome("incomplete", response.proof_state, None, goals_pp)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


@dataclass
class ReplSession:
    """A live REPL process pinned to one theorem, plus a per-request timeout.

    Thin by design: `verify` owns the verdict policy, this owns only the
    transport and the translation of transport failures into `ReplError`.
    """

    #: A `lean_interact.LeanServer`, or any object exposing ``run(request, *,
    #: timeout=...)`` and ``kill()``. Kept structurally typed so tests and a
    #: future pooled/remote backend can substitute one.
    server: object
    #: Seconds allowed per request, passed straight through to `server.run`.
    #: None means no timeout.
    timeout: int | None
    #: The theorem's ``full_name``. Used ONLY to make error messages
    #: attributable; nothing here reads the corpus row.
    theorem: str

    def run(self, request):
        """Send one request, translating transport failures into `ReplError`.

        Design: `lean_interact` raises builtin `TimeoutError` (and kills the
        server) on a slow request, and `BrokenPipeError` when the REPL closes.
        Both are translated rather than propagated because `runner.py` records
        ``f"{type(exc).__name__}: {exc}"`` into the row's ``lean_error`` column:
        a uniform `ReplError` type with a ``timeout:``-shaped message keeps
        timeouts greppable in results WITHOUT introducing a seventh verdict
        string. `runner.py` owns the verdict->glyph map and the sanity-failure
        set, so adding a verdict is a far larger change than it looks.

        Parameters
        ----------
        request : BaseREPLQuery
            A `Command`, `ProofStep`, or any other `lean_interact` request.

        Returns
        -------
        CommandResponse or ProofStepResponse or LeanError
            Whatever the server returned; a `LeanError` is a VALUE here, not a
            raise (see `classify_step`).

        Raises
        ------
        ReplError
            The request timed out (message contains the lowercase word
            ``timeout``) or the REPL closed its pipe.
        """
        try:
            return self.server.run(request, timeout=self.timeout)
        except TimeoutError as exc:
            raise ReplError(f"timeout after {self.timeout}s on {self.theorem}: {exc}") from exc
        except BrokenPipeError as exc:
            raise ReplError(f"REPL closed on {self.theorem}: {exc}") from exc

    def step(self, proof_state: int, tactic: str) -> StepOutcome:
        """Apply `tactic` at `proof_state` and classify the reply.

        Parameters
        ----------
        proof_state : int
            Proof-state id to branch from. Proof states are immutable, so many
            calls may branch from the same id.
        tactic : str
            One tactic. Combinators (``;``, ``<;>``) are part of a single
            tactic and must not be split by the caller.

        Returns
        -------
        StepOutcome
            One of the four LEAN-reported kinds: ``"success"``, ``"lean_error"``,
            ``"incomplete"``, ``"given_up"``.

        Raises
        ------
        ReplError
            The REPL itself failed -- either at transport level (`run`) or by
            replying on its own error channel (`classify_step` kind
            ``"exception"``). REPL-level trouble is always an exception here and
            never a return value, so callers cannot silently record it as a Lean
            verdict.
        """
        outcome = classify_step(self.run(ProofStep(proof_state=proof_state, tactic=tactic)))
        if outcome.kind == "exception":
            raise ReplError(outcome.error or "REPL-level failure with no message")
        return outcome

    def close(self) -> None:
        """Kill the REPL process. Safe to call more than once.

        A failure to kill an already-dead process is logged at DEBUG and
        swallowed: `close` runs in `finally` blocks, and letting a teardown
        failure escape would MASK the real error being propagated. Nothing else
        is swallowed.
        """
        try:
            self.server.kill()
        except Exception as exc:  # noqa: BLE001 - teardown must not mask the real error
            logger.debug("killing the REPL for %s failed: %s", self.theorem, exc)


# ---------------------------------------------------------------------------
# Session opening
# ---------------------------------------------------------------------------

#: Mirrors the retired `_open_dojo_with_retry`. Server startup occasionally
#: fails when several sessions open concurrently: the Lean subprocess races on
#: the build cache. A reopen usually succeeds within seconds, so retry with
#: backoff.
_REPL_OPEN_RETRIES = 3
#: One entry per SLEEP, i.e. ``_REPL_OPEN_RETRIES - 1``: the last attempt raises
#: instead of sleeping.
_REPL_OPEN_BACKOFF_S = (5.0, 15.0)


def _default_server_factory(root: Path) -> LeanServer:
    """Start a `LeanServer` on the mathlib4 checkout at `root`.

    Kept a separate function (rather than inlined into `open_session`) so tests
    can substitute a fake and so a pooled or remote server can be dropped in
    without touching the open/retry logic around it.

    Notes
    -----
    `LeanServer.__init__` asserts its config is set up and STARTS the process,
    so this returns a live server or raises.
    """
    return LeanServer(LeanREPLConfig(project=LocalProject(directory=str(root))))


def _describe(response) -> str:
    """Render a REPL reply's messages verbatim, for an actionable `ReplError`."""
    if isinstance(response, LeanError):
        return response.message
    return "\n".join(f"[{msg.severity}] {msg.data}" for msg in response.messages)


def open_session(
    bt,
    timeout: int = 600,
    root: str | Path | None = None,
    server_factory: Callable[[Path], object] | None = None,
) -> tuple[ReplSession, int]:
    """Start a REPL, elaborate `bt`'s statement as a stub, return its proof state.

    Parameters
    ----------
    bt : BenchmarkTheorem
        The theorem to open.
    timeout : int, optional
        Seconds per REPL request (not for the session as a whole). Default 600.
    root : str or Path, optional
        Checkout root; forwarded to `mathlib_root`.
    server_factory : callable, optional
        Injection seam: takes the resolved root `Path` and returns a STARTED
        server exposing ``run``/``kill``. Defaults to `_default_server_factory`.

    Returns
    -------
    (ReplSession, int)
        The live session and the proof-state id of the stub's ``sorry`` -- the
        state tactic 0 of the proof should be applied to.

    Raises
    ------
    ReplError
        The checkout is misconfigured, the server could not be started, or the
        module could not be imported. The message quotes `mathlib_root`'s /
        Lean's / the REPL's own text verbatim. Never a bare `RuntimeError`:
        `verify.verify_proof_tail` reads that as ``"replay_failed"``, a claim
        about the corpus (see the translation comment in the body).
    StatementError
        The declaration has no statement/proof boundary, or its stub did not
        elaborate. A `ReplError` subclass that is NOT retried.

    Notes
    -----
    Configuration and statement derivation happen BEFORE any Lean process is
    started, so a misconfiguration or an unusable declaration fails in
    milliseconds rather than after a REPL startup -- and, since both are
    deterministic, they are outside the retry loop: retrying them would only
    multiply the wait before the same failure. Inside the loop the same rule
    applies one level down -- server start and ``import`` are retried, stub
    elaboration (`StatementError`) is not. See `StatementError`.
    """
    # Design: `mathlib_root` signals a misconfiguration with a plain builtin
    # `RuntimeError`, which is the right type for a direct caller and is pinned
    # by its own tests. It is the WRONG type once it starts travelling toward
    # `verify.verify_proof_tail`, whose FIRST except clause maps `RuntimeError`
    # to verdict "replay_failed" -- a claim that the RECORDED ground-truth proof
    # does not replay. An operator who forgets to set SMOLBENCH_MATHLIB_ROOT
    # would otherwise see every theorem in the study condemned as a broken
    # ground truth, and `runner.SANITY_FAILURE_VERDICTS` would suppress cell
    # generation for all of them. Translating here -- at the boundary, not in
    # `mathlib_root` -- keeps both contracts right.
    try:
        resolved_root = mathlib_root(root)
    except RuntimeError as exc:
        raise ReplError(str(exc)) from exc

    stub = theorem_statement_stub(bt, resolved_root)
    module = module_name(bt.file_path)
    factory = server_factory or _default_server_factory

    last_exc: Exception | None = None
    for attempt in range(_REPL_OPEN_RETRIES):
        session: ReplSession | None = None
        try:
            session = ReplSession(
                server=factory(resolved_root), timeout=timeout, theorem=bt.full_name
            )
            return session, _open_proof_state(session, bt, module, stub)
        except StatementError:
            # Terminal: same statement, same environment, same answer. Kill the
            # server first -- no orphaned Lean processes -- then propagate
            # without sleeping. See `StatementError` for the cost this avoids.
            if session is not None:
                session.close()
            raise
        except Exception as exc:  # noqa: BLE001 - retried below, or re-raised
            # No orphaned Lean processes: whatever failed, the server this
            # attempt started (if any) dies with the attempt.
            if session is not None:
                session.close()
            last_exc = exc
            if attempt + 1 < _REPL_OPEN_RETRIES:
                time.sleep(_REPL_OPEN_BACKOFF_S[attempt])
    assert last_exc is not None
    raise last_exc


def _open_proof_state(session: ReplSession, bt, module: str, stub: str) -> int:
    """Import `module`, elaborate `stub` in it, and return the ``sorry``'s state id.

    Two REPL round trips: a fresh-environment ``import`` (``env=None`` starts a
    new session in which ``import`` is legal), then the stub in the environment
    that produced.

    Raises
    ------
    ReplError
        The ``import`` round trip failed. Deliberately the BROAD type, i.e.
        retryable: a failed import is routinely a cold or racing ``lake`` build
        cache, which is exactly what `open_session`'s backoff exists for.
    StatementError
        The stub did not elaborate, or elaborated without producing a ``sorry``
        to branch from. Deterministic, so `open_session` does not retry it. This
        is the single most likely failure mode in production -- see the module
        docstring on import-only environments -- so every message carries the
        REPL's own text verbatim: an undiagnosable version of it would degrade a
        whole eval into a wall of ``exception`` rows.
    """
    imported = session.run(Command(cmd=f"import {module}"))
    if isinstance(imported, LeanError) or imported.get_errors():
        raise ReplError(f"could not import {module} for {bt.full_name}: {_describe(imported)}")

    elaborated = session.run(Command(cmd=stub, env=imported.env))
    if isinstance(elaborated, LeanError) or elaborated.get_errors() or not elaborated.sorries:
        raise StatementError(
            f"could not elaborate the statement of {bt.full_name} in module {module}: "
            f"{_describe(elaborated) or 'no sorry in the response'}\n--- stub ---\n{stub}"
        )

    proof_state = elaborated.sorries[0].proof_state
    if proof_state is None:
        raise StatementError(
            f"the stub for {bt.full_name} elaborated to a sorry with no proofState; "
            "no proof state can be branched from it"
        )
    return proof_state
