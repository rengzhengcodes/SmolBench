"""Drive a Lean 4 REPL session for one theorem via `lean_interact`.

Sessions restore imports, not file-level `open`/`variable`/`namespace` scope, so dependent
statements fail as ``"exception"``; restoring a file prefix costs more than that coverage.
Text processing was measured against mathlib4 at the corpus commit; REPL calls use fakes.
`verify` uses `module_name`, `declaration_text`, `rename_declaration`, and
`theorem_statement_stub`; `ReplSession.step` uses `classify_step`.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Literal, Protocol, Sequence

from lean_interact import Command, LeanREPLConfig, LeanServer, LocalProject, ProofStep
from lean_interact.interface import LeanError

from smolbench.deduction.lean.corpus import BenchmarkTheorem

logger = logging.getLogger(__name__)


#: REPL declaration name; the original already exists in its imported module.
TARGET_NAME: str = "smolbenchTarget"

#: Mathlib4 checkout, read at call time so late environment changes take effect.
MATHLIB_ROOT_ENV: str = "SMOLBENCH_MATHLIB_ROOT"


class ReplError(Exception):
    """REPL infrastructure failure, not a Lean verdict.

    This is not `RuntimeError`, which `verify.verify_proof_tail` maps to corpus claim
    ``"replay_failed"``; REPL failures must remain ``"exception"``.
    """


class ReplTimeout(ReplError):
    """A request exceeded the per-request timeout.

    `lean_interact` kills the server on timeout, so the session is dead
    afterwards. `verify.try_tail` records this as the model verdict
    ``"timeout"`` (the candidate tactic did not terminate) and reopens the
    checkpoint for later candidates.
    """


class ReplClosed(ReplError):
    """The REPL process is gone (killed, crashed, or pipe broken).

    Infrastructure, not a verdict: the caller records ``"exception"`` and
    `verify.Checkpoint` reopens the session before the next candidate.
    """


class StatementError(ReplError):
    """Deterministic failure to obtain a statement proof state.

    `open_session` retries transient server/import failures but never stub elaboration: attempt
    3 repeats attempt 1 under the same import-only environment. It remains ``"exception"``.
    """


@dataclass(frozen=True)
class StepOutcome:
    """Normalized result of one tactic.

    Field order is contractual because callers construct instances positionally.
    """

    #: Whole proof, Lean rejection, remaining goals, `sorry`, or REPL failure.
    kind: Literal["success", "lean_error", "incomplete", "given_up", "exception"]
    #: Next proof-state id; None after rejection or REPL failure.
    proof_state: int | None
    #: Lean or REPL message; never empty when set.
    error: str | None
    #: ``"\\n\\n"``-joined remaining goals, only for ``"incomplete"``.
    goals_pp: str | None


def module_name(file_path: str) -> str:
    """Convert a corpus ``file_path`` into the Lean module name to ``import``.

    Parameters
    ----------
    file_path : str
        Repo-relative, ``/``-separated path (e.g. ``Mathlib/Algebra/Group/Basic.lean``).

    Returns
    -------
    str
        Lean module name.

    Raises
    ------
    ValueError
        Empty or non-``.lean`` path, named before an untraceable REPL import error.
    """
    if not file_path or not file_path.endswith(".lean"):
        raise ValueError(
            f"not a Lean source path (expected a '.lean' suffix): {file_path!r}"
        )
    return file_path[: -len(".lean")].replace("/", ".")


def mathlib_root(root: str | Path | None = None) -> Path:
    """Resolve the mathlib4 checkout the REPL should run inside.

    Read ``SMOLBENCH_MATHLIB_ROOT`` at call time so late configuration works; preserve symlinks
    because callers compare literal paths and Lean works through them. Validate before REPL startup.

    Parameters
    ----------
    root : str | Path | None, optional
        Checkout path overriding the environment.

    Returns
    -------
    Path
        Configured mathlib4 checkout.

    Raises
    ------
    RuntimeError
        Missing configuration, invalid directory, or missing ``lean-toolchain``, in that order.
    """
    # Avoid freezing a long-lived process's environment at import time.
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


#: Lean brackets, including ``⟨⟩`` and ``⁅⁆``, can wrap a ``:=``.
_OPEN_BRACKETS = "([{⟨⁅"
_CLOSE_BRACKETS = ")]}⟩⁆"

#: Identifier terminators besides whitespace.
_IDENT_TERMINATORS = ":({[⦃⟨"

#: Renameable declarations; ``def`` has no tactic proof to slice.
_DECLARATION_KEYWORDS = ("theorem", "lemma")

#: Identifier continuations prevent partial keyword matches.
_IDENT_CHARS = re.compile(r"[A-Za-z0-9_'.!?]")


def _iter_code_positions(text: str) -> Iterator[int]:
    """Yield, in order, the index of every character of `text` outside a comment.

    Indices address the original text because callers slice it. The first ``-/`` closes because
    mathlib4 declaration headers do not nest block comments.

    Parameters
    ----------
    text : str

    Yields
    ------
    int
        Non-comment character index.
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

    Use the first depth-0, non-comment ``:=``: `autoParam` (e.g. `Basis.reindexFinsetRange_self`)
    and comments contain ``:=`` too.
    Across 300 pinned theorems it found 228 of 229 applicable boundaries; ``Filter.bot_pow``
    is equation-style, has no traced tactics, and is never verified.

    Parameters
    ----------
    text : str

    Returns
    -------
    int | None
        Depth-0 non-comment boundary, if present.
    """
    depth = 0
    first: int | None = None
    for i in _iter_code_positions(text):
        ch = text[i]
        if ch in _OPEN_BRACKETS:
            depth += 1
        elif ch in _CLOSE_BRACKETS:
            # A mid-expression slice can start with a closer; negative depth hides later ``:=``.
            depth = max(depth - 1, 0)
        elif depth == 0 and ch == ":" and text.startswith(":=", i):
            # A statement-level `letI x : T := v` / `haveI` carries its own depth-0 `:=`
            # before the proof's; the proof boundary is the one followed by `by`.
            if _BY_AFTER_ASSIGN_RE.match(text, i + 2):
                return i
            if first is None:
                first = i
    return first


#: Whitespace (possibly a newline) then the `by` keyword.
_BY_AFTER_ASSIGN_RE = re.compile(r"\s*by(?![\w'?!])")


def rename_declaration(text: str, target_name: str = TARGET_NAME) -> str:
    """Rewrite a declaration's identifier to `target_name`, leaving all else intact.

    Rename because `open_session` imports the original. Use `_iter_code_positions`, not regex:
    213 of 106,445 mathlib4 declarations have a preceding docstring matching a declaration;
    regex would silently rename it. Preserve leading text byte-identically; reject ``def``.

    Parameters
    ----------
    text : str
    target_name : str, optional

    Returns
    -------
    str
        Source with a rewritten identifier.

    Raises
    ------
    ValueError
        Missing renameable declaration or identifier; quotes a source prefix.
    """
    start, end = _declaration_identifier_span(text)
    return text[:start] + target_name + text[end:]


def _declaration_identifier_span(text: str) -> tuple[int, int]:
    """``(start, end)`` of the identifier following the first code-level ``theorem``/``lemma``.

    Raises
    ------
    ValueError
        Missing declaration keyword or identifier; quotes a source prefix.
    """
    n = len(text)
    for i in _iter_code_positions(text):
        keyword = next(
            (kw for kw in _DECLARATION_KEYWORDS if text.startswith(kw, i)), None
        )
        if keyword is None:
            continue
        # Avoid partial keyword matches such as `mytheorem`.
        if i > 0 and _IDENT_CHARS.match(text[i - 1]):
            continue
        after = i + len(keyword)
        if after < n and _IDENT_CHARS.match(text[after]):
            continue

        start = after
        while start < n and text[start].isspace():
            start += 1
        end = start
        while (
            end < n and not text[end].isspace() and text[end] not in _IDENT_TERMINATORS
        ):
            end += 1
        if end == start:
            raise ValueError(
                f"{keyword!r} keyword is not followed by an identifier in: {text[:120]!r}"
            )
        return start, end

    raise ValueError(
        "no 'theorem'/'lemma' declaration keyword outside a comment in: "
        f"{text[:120]!r}"
    )


#: Column-0 keywords that end a declaration slice, including scope markers.
_TOP_LEVEL_KEYWORDS = frozenset(
    {
        "theorem",
        "lemma",
        "def",
        "instance",
        "abbrev",
        "structure",
        "class",
        "inductive",
        "namespace",
        "end",
        "section",
        "open",
        "variable",
        "noncomputable",
        "protected",
        "private",
        "nonrec",
        "universe",
        "attribute",
        "example",
        "macro",
        "syntax",
        "notation",
        "deriving",
        "alias",
        "set_option",
        "import",
    }
)

#: Declaration openers; ``set_option maxHeartbeats 400000 in`` can begin a header, so scope
#: commands must not arm the stop rule.
_DECLARATION_OPENERS = frozenset(
    {
        "theorem",
        "lemma",
        "def",
        "instance",
        "abbrev",
        "structure",
        "class",
        "inductive",
        "example",
        "macro",
        "syntax",
        "notation",
        "alias",
    }
)

#: Same-line declaration modifiers.
_DECLARATION_MODIFIERS = frozenset(
    {
        "private",
        "protected",
        "noncomputable",
        "nonrec",
        "partial",
        "unsafe",
        "scoped",
        "local",
    }
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

    Strip attributes and same-line modifiers first, so ``protected theorem Foo.bar`` and
    ``@[simp] lemma baz`` count.

    Parameters
    ----------
    line : str

    Returns
    -------
    bool
        Whether the line opens a declaration.
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

    The first ``-/`` closes because nested blocks are not tracked; ``--`` ends its line.

    Parameters
    ----------
    line : str
    in_comment : bool

    Returns
    -------
    bool
        Block-comment state after the line.
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


def declaration_text(
    root: Path, file_path: str, start_line: int, max_lines: int = 400
) -> str:
    """Slice one declaration's source out of ``root / file_path``.

    `start_line` is 1-indexed to match `premises.slice_full_decl`; ignore `BenchmarkTheorem.start`'s
    untested column, which can point into a docstring or attribute, and scan forward from the line. Stop only
    at the next column-0 top-level line (including ``@[`` and ``/--``)
    after the declaration opener, so leading attributes/docstrings remain in the slice; block
    comments never stop it.

    Parameters
    ----------
    root : Path
        Mathlib4 checkout root.
    file_path : str
    start_line : int
        1-indexed slice start.
    max_lines : int, optional
        Maximum 400 lines so a missing stop keyword cannot consume a file.

    Returns
    -------
    str
        Declaration source.

    Raises
    ------
    FileNotFoundError
        Missing source, named by corpus path.
    ValueError
        `start_line` below 1 or past EOF.
    """
    source = Path(root) / file_path
    if not source.is_file():
        raise FileNotFoundError(f"no such Lean source: {file_path} (looked in {root})")

    lines = source.read_text(encoding="utf-8").splitlines()
    if start_line < 1:
        raise ValueError(f"start_line must be >= 1 (1-indexed), got {start_line}")
    if start_line > len(lines):
        # `start_line == len(lines)` is the legitimate final line.
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
            # Arm after appending so the opener remains in the slice.
            armed = True
    return "\n".join(collected).rstrip()


#: Column-0 commands that shape the environment a later declaration in the
#: same file elaborates in. Importing the module supplies its *declarations*
#: but none of this scope: mathlib theorems live inside ``namespace``/``section``
#: blocks with ``variable`` binders and ``open`` namespaces, and (module system,
#: 2026) under ``public section``. Elaborating a statement bare fails on the
#: first unqualified name, so `scope_prefix` replays these commands first.
_SCOPE_KEYWORDS = frozenset(
    {
        "namespace",
        "section",
        "end",
        "open",
        "variable",
        "universe",
        "set_option",
        "include",
        "omit",
        "suppress_compilation",
        "unseal",
    }
)

#: ``local`` commands are not exported by the module, so they must be replayed
#: (``local notation``, ``local instance``, ``local macro``...). ``scoped`` ones
#: ARE exported and reactivate on ``open``, so replaying them would duplicate.
_LOCAL_KEYWORD = "local"
_ATTRIBUTE_LOCAL_PREFIX = re.compile(r"^attribute\s*\[\s*local\b")
#: Module-system export markers; meaningless outside a ``module`` file.
_SCOPE_MODIFIER_RE = re.compile(r"^(?:@\[[^\]]*\]\s*|public\s+|meta\s+)+")


def _split_top_level_commands(lines: list[str]) -> list[str]:
    """Group `lines` into column-0-started commands, ignoring block comments.

    A new command begins at every line whose first character is non-blank
    while no ``/- ... -/`` block is open; anything before the first such line
    is dropped.
    """
    commands: list[str] = []
    current: list[str] = []
    in_comment = False
    for line in lines:
        if not in_comment and line and not line[0].isspace():
            if current:
                commands.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
        in_comment = _advance_comment_state(line, in_comment)
    if current:
        commands.append("\n".join(current))
    return commands


def _code_only(text: str) -> str:
    """`text` with every comment removed (see `_iter_code_positions`)."""
    return "".join(text[i] for i in _iter_code_positions(text))


def _scope_command(command: str) -> str | None:
    """Return the replayable form of a top-level `command`, or None to drop it.

    Strip leading attributes and ``public``/``meta`` so ``@[expose] public
    section`` replays as ``section`` (its ``end`` is kept as-is). Drop the
    ``... in`` form (``open Foo in``, ``variable (p) in``, ``set_option ... in``):
    it binds to the declaration that follows, which is not replayed, and would
    otherwise be a parse error.
    """
    stripped = _SCOPE_MODIFIER_RE.sub("", command.lstrip())
    word = _LEADING_WORD.match(stripped)
    if word is None:
        return None
    keyword = word.group(0)
    keep = (
        keyword in _SCOPE_KEYWORDS
        or (keyword == "noncomputable" and stripped.split()[1:2] == ["section"])
        or keyword == _LOCAL_KEYWORD
        or _ATTRIBUTE_LOCAL_PREFIX.match(stripped) is not None
    )
    if not keep:
        return None
    code = _code_only(stripped).rstrip()
    if code == "in" or code.endswith((" in", "\tin", "\nin")):
        return None
    return stripped.rstrip()


def scope_commands(root: Path, file_path: str, start_line: int) -> list[str]:
    """Replayable scope commands preceding line `start_line` of ``root / file_path``.

    Import the module first (that supplies every declaration, including the ones
    the ``variable`` binders mention), then run these, then the renamed stub: the
    stub then elaborates in the namespace, sections, variables, opens and options
    of its original position. Declarations, docstrings and the ``module``/``import``
    header are dropped.

    Parameters
    ----------
    root : Path
        Mathlib4 checkout root.
    file_path : str
    start_line : int
        1-indexed first line of the declaration slice (see `declaration_text`).

    Returns
    -------
    list[str]
        Commands in file order; empty when nothing precedes the declaration.
    """
    source = Path(root) / file_path
    if not source.is_file():
        raise FileNotFoundError(f"no such Lean source: {file_path} (looked in {root})")
    lines = source.read_text(encoding="utf-8").splitlines()[: max(start_line - 1, 0)]
    return [c for c in map(_scope_command, _split_top_level_commands(lines)) if c]


def scope_prefix(root: Path, file_path: str, start_line: int) -> str:
    """`scope_commands` joined by newlines, ready to precede a stub in one REPL command."""
    return "\n".join(scope_commands(root, file_path, start_line))


def _ends_with_in(command: str) -> bool:
    """True for the ``<command> in`` form that binds to the next declaration."""
    code = _code_only(command).rstrip()
    return code == "in" or code.endswith((" in", "\tin", "\nin"))


def declaration_in_commands(root: Path, file_path: str, start_line: int) -> list[str]:
    """The ``... in`` commands that bind to the declaration starting at `start_line`.

    Mathlib puts ``set_option backward.isDefEq.respectTransparency false in``,
    ``include hZ in`` and ``open Foo in`` on the lines above a theorem, and
    LeanDojo's ``start`` points at the docstring or keyword below them. They are
    part of the declaration command (`_scope_command` drops them from the scope
    replay) and change what its tactics do, so they must precede the stub.

    Parameters
    ----------
    root : Path
    file_path : str
    start_line : int
        1-indexed first line of the declaration slice.

    Returns
    -------
    list[str]
        Trailing run of ``in`` commands, in file order; empty when there is none.
    """
    source = Path(root) / file_path
    if not source.is_file():
        raise FileNotFoundError(f"no such Lean source: {file_path} (looked in {root})")
    lines = source.read_text(encoding="utf-8").splitlines()[: max(start_line - 1, 0)]
    commands = _split_top_level_commands(lines)
    trailing: list[str] = []
    for command in reversed(commands):
        if not _ends_with_in(command):
            break
        trailing.append(_SCOPE_MODIFIER_RE.sub("", command.lstrip()).rstrip())
    return trailing[::-1]


#: Tokens that end the namespace list of an ``open`` command.
_OPEN_LIST_TERMINATORS = frozenset({"(", "hiding", "renaming", "in"})


def scoped_syntax_namespaces(commands: Sequence[str]) -> list[str]:
    """Namespaces whose scoped syntax is active after `commands`, in activation order.

    Track ``section``/``namespace``/``end`` so an ``open`` inside a closed block
    is forgotten, as Lean forgets it; ``namespace A.B`` activates ``A`` and ``A.B``.
    Only the namespace identifiers are taken from ``open`` (``hiding``, ``renaming``
    and explicit ``(a b)`` lists are irrelevant to notation).

    Parameters
    ----------
    commands : Sequence[str]
        Output of `scope_commands`.

    Returns
    -------
    list[str]
        Deduplicated namespace identifiers.
    """
    stack: list[list[str]] = [[]]
    for command in commands:
        tokens = _code_only(command).replace("(", " ( ").split()
        if not tokens:
            continue
        head = tokens[0]
        if head == "open" and tokens[-1] == "in":
            # `open Foo in` bound to the declaration (see `declaration_in_commands`):
            # its notation is needed for the tactics too.
            tokens = tokens[:-1]
        if head in ("section", "namespace") or (
            head == "noncomputable" and tokens[1:2] == ["section"]
        ):
            stack.append([])
            if head == "namespace" and len(tokens) > 1:
                parts = tokens[1].split(".")
                stack[-1].extend(".".join(parts[: i + 1]) for i in range(len(parts)))
        elif head == "end":
            if len(stack) > 1:
                stack.pop()
        elif head == "open":
            names = tokens[1:]
            if names[:1] == ["scoped"]:
                names = names[1:]
            for tok in names:
                if tok in _OPEN_LIST_TERMINATORS:
                    break
                stack[-1].append(tok)
    seen: dict[str, None] = {}
    for frame in stack:
        for name in frame:
            seen.setdefault(name, None)
    return list(seen)


def tactic_open_prefix(namespaces: Sequence[str]) -> str:
    """``open scoped A B in`` line for `ReplSession.tactic_prefix`; empty for no namespaces."""
    return f"open scoped {' '.join(namespaces)} in\n" if namespaces else ""


#: ``public theorem`` / ``public lemma``: the export modifier at the start of a code line.
_PUBLIC_MODIFIER_RE = re.compile(r"(?m)^(\s*)public\s+(?=(?:\w+\s+)*(?:theorem|lemma)\b)")

#: ``where`` at depth 0 before ``:=`` means a structure-instance proof whose
#: fields carry their own ``:=``; there is no single proof state to open.
_WHERE_RE = re.compile(r"(?<![\w.'])where(?![\w'])")


def strip_leading_attributes(text: str) -> str:
    """Remove every ``@[...]`` group before the declaration keyword.

    The stub is renamed, so name-deriving attributes (``@[to_additive]``,
    ``@[simps]``) would fail or spawn extra declarations, and ``@[simp]`` on a
    ``sorry``-proved lemma is pointless. Docstrings are left in place.
    """
    while True:
        first = next(
            (i for i in _iter_code_positions(text) if not text[i].isspace()), None
        )
        if first is None or not text.startswith("@[", first):
            return text
        depth = 0
        end = None
        for i in _iter_code_positions(text[first:]):
            ch = text[first + i]
            if ch in _OPEN_BRACKETS:
                depth += 1
            elif ch in _CLOSE_BRACKETS:
                depth -= 1
                if depth == 0:
                    end = first + i + 1
                    break
        if end is None:
            return text
        text = text[:first] + text[end:].lstrip()


def theorem_statement_stub(
    bt: BenchmarkTheorem,
    root: Path | None = None,
    target_name: str = TARGET_NAME,
) -> str:
    """Build the ``:= by sorry`` stub whose ``sorry`` opens `bt`'s proof state.

    Elaborate ``sorry`` because the REPL has no goal-by-declaration request; its response carries
    the `Sorry` ``proofState`` tactics branch from.

    Parameters
    ----------
    bt : BenchmarkTheorem
    root : Path | None, optional
        Mathlib4 checkout root.
    target_name : str, optional

    Returns
    -------
    str
        Statement ending in ``:= by sorry``.

    Raises
    ------
    StatementError
        Missing top-level ``:=``; `open_session` must not retry this deterministic failure.
    ValueError
        No renameable declaration.
    FileNotFoundError
        Missing source.
    """
    # Module-level lookup lets tests and future backends monkeypatch it.
    text = declaration_text(mathlib_root(root), bt.file_path, bt.start[0])

    # No ``:=`` means a term/equation-style proof with no state boundary.
    end = find_statement_end(text)
    if end is None:
        raise StatementError(
            f"cannot open a proof state for {bt.full_name}: its declaration has no "
            "top-level ':=' (term-mode or equation-style proof), so there is no "
            "statement/proof boundary to cut at"
        )

    # `public` (module system) is meaningless in the REPL's non-module environment.
    statement = _PUBLIC_MODIFIER_RE.sub("", strip_leading_attributes(text[:end]))
    if _WHERE_RE.search(_code_only(statement)):
        raise StatementError(
            f"cannot open a proof state for {bt.full_name}: its proof is a `where` "
            "structure instance, so the first ':=' belongs to a field, not the statement"
        )
    # Keep the declared name's dotted prefix: `theorem IsSuccPrelimit.sSup_lt_iff` opens
    # namespace `IsSuccPrelimit` for its own body, and traced tactics rely on that.
    start, stop = _declaration_identifier_span(statement)
    prefix = statement[start:stop].rpartition(".")[0]
    target = f"{prefix}.{target_name}" if prefix else target_name
    return f"{rename_declaration(statement, target).rstrip()}\n  := by sorry"


#: Message-channel prefix the REPL uses for an exception thrown by a tactic.
_TACTIC_EXCEPTION_PREFIX = "Lean error:"


def classify_step(response: Any) -> StepOutcome:
    """Map one `lean_interact` reply onto a `StepOutcome`.

    Branch order defines the evaluation taxonomy. `LeanServer.run` returns `LeanError` rather
    than raising for ``{"message": ...}``; errors are never empty for failure outcomes.

    Parameters
    ----------
    response : Any

    Returns
    -------
    StepOutcome
        Normalized tactic outcome.
    """
    if isinstance(response, LeanError):
        # The community REPL reports an exception thrown BY a tactic (`rw` found no
        # occurrence, `simp` made no progress, an unknown identifier, `abortTactic`)
        # on its message channel as "Lean error:\n<text>" instead of as a
        # `ProofStepResponse` error message. That is a rejected tactic, scored like
        # any `lean_error`; anything else on the channel (unknown proof state, bad
        # request) is infrastructure and stays `exception`.
        message = response.message.strip()
        if message.startswith(_TACTIC_EXCEPTION_PREFIX):
            detail = message[len(_TACTIC_EXCEPTION_PREFIX) :].strip()
            return StepOutcome("lean_error", None, detail or message, None)
        return StepOutcome("exception", None, f"REPL error: {response.message}", None)

    status = response.proof_status or ""

    # Check errors before `sorry`: a term that fails to elaborate is filled with a
    # synthetic `sorry`, so an error-first check keeps that a `lean_error`.
    # Warnings never reject a tactic: `get_errors()` selects severity ``"error"``.
    errors = response.get_errors()
    if errors or status.startswith("Error"):
        message = "\n".join(msg.data for msg in errors)
        return StepOutcome(
            "lean_error",
            None,
            # Blank results-row errors are indistinguishable from classifier bugs.
            message or f"Lean reported proof status {status!r} with no error message",
            None,
        )

    # Check `sorry` before completion or a contaminated proof scores as success.
    if response.sorries or "sorry" in status.lower():
        return StepOutcome("given_up", None, None, None)

    # `proofStatus`, not empty goals, is authoritative; sibling goals can remain.
    if status.startswith("Completed"):
        return StepOutcome("success", response.proof_state, None, None)

    goals_pp = "\n\n".join(response.goals) if response.goals else None
    return StepOutcome("incomplete", response.proof_state, None, goals_pp)


class _ReplServer(Protocol):
    """Structural server API: run requests, kill the process."""

    def run(self, request: Any, timeout: Any = None) -> Any:
        """Send `request`, returning the server reply."""

    def kill(self) -> None:
        """Terminate the REPL process."""


@dataclass
class ReplSession:
    """Live REPL process for one theorem with a request timeout.

    `verify` owns verdict policy; this translates transport failures to `ReplError`.
    """

    #: Server-like object; structural typing permits fake, pooled, or remote backends.
    server: _ReplServer
    #: Per-request seconds; None disables the timeout.
    timeout: int | None
    #: Theorem name, used only to attribute error messages.
    theorem: str
    #: Prepended to every tactic, e.g. ``"open scoped TensorProduct in\\n"``: the REPL
    #: parses a ``ProofStep`` without the scoped notation the file's ``open``/``namespace``
    #: commands activated (``⊗[R]``, ``≫``), so the stub's scope is re-opened per tactic.
    #: Name resolution itself is unaffected: the proof state keeps the file's open
    #: declarations. Cleared after one ``unknown namespace`` failure (see `step`).
    tactic_prefix: str = ""

    def run(self, request: Any) -> Any:
        """Send one request, translating transport failures into `ReplError`.

        Translate timeout (which kills the server) and closed-pipe failures so `runner.py` records
        greppable ``timeout:`` errors without a seventh verdict; return `LeanError` values.

        Parameters
        ----------
        request : Any
            Lean server request.

        Returns
        -------
        Any
            Server reply.
        """
        try:
            return self.server.run(request, timeout=self.timeout)
        except TimeoutError as exc:
            raise ReplTimeout(
                f"timeout after {self.timeout}s on {self.theorem}: {exc}"
            ) from exc
        except (BrokenPipeError, ChildProcessError, ConnectionAbortedError) as exc:
            # `lean_interact` raises ChildProcessError on a dead server and
            # ConnectionAbortedError on a broken pipe; both mean the process is gone.
            raise ReplClosed(f"REPL closed on {self.theorem}: {exc}") from exc

    def step(self, proof_state: int, tactic: str) -> StepOutcome:
        """Apply `tactic` at `proof_state` and classify the reply.

        Proof states are immutable, so calls may branch from one id; callers must not split
        combinators (``;``, ``<;>``).

        Parameters
        ----------
        proof_state : int
            Proof-state id.
        tactic : str
            Lean tactic.

        Returns
        -------
        StepOutcome
            Classified tactic result.

        Raises
        ------
        ReplError
            Transport or REPL-channel failure, never silently recorded as a Lean verdict.
        """
        outcome = classify_step(
            self.run(ProofStep(proof_state=proof_state, tactic=self.tactic_prefix + tactic))
        )
        if (
            self.tactic_prefix
            and outcome.kind in ("exception", "lean_error")
            and "unknown namespace" in (outcome.error or "")
        ):
            # A prefix namespace that does not resolve here would fail every step; the bare
            # tactic is the pre-prefix behaviour.
            self.tactic_prefix = ""
            outcome = classify_step(self.run(ProofStep(proof_state=proof_state, tactic=tactic)))
        if outcome.kind == "exception":
            raise ReplError(outcome.error or "REPL-level failure with no message")
        return outcome

    def close(self) -> None:
        """Kill the REPL process. Safe to call more than once.

        Swallow only kill failures because `finally` teardown must not mask the real error.
        """
        try:
            self.server.kill()
        except Exception as exc:  # noqa: BLE001 - teardown must not mask the real error
            logger.debug("killing the REPL for %s failed: %s", self.theorem, exc)


#: Retry concurrent-start build-cache races; reopening usually succeeds within seconds.
_REPL_OPEN_RETRIES = 3
#: One entry per SLEEP, i.e. ``_REPL_OPEN_RETRIES - 1``; the final attempt raises
#: instead of sleeping.
_REPL_OPEN_BACKOFF_S = (5.0, 15.0)


def _default_server_factory(root: Path) -> LeanServer:
    """Start a `LeanServer` on the mathlib4 checkout at `root`.

    Keep this seam so fake, pooled, and remote servers can replace it without changing retry
    logic. `LeanServer.__init__` validates config and starts the process, so this returns a live
    server or raises.

    Parameters
    ----------
    root : Path
        Mathlib4 checkout.

    Returns
    -------
    LeanServer
        Started server.
    """
    return LeanServer(
        LeanREPLConfig(
            project=LocalProject(directory=str(root)),
            repl_git=os.environ.get(REPL_GIT_ENV, DEFAULT_REPL_GIT),
            repl_rev=repl_rev_for(root),
        )
    )


#: Overrides the REPL revision derived from the project's ``lean-toolchain``.
REPL_REV_ENV: str = "SMOLBENCH_REPL_REV"
#: Overrides the REPL repository. lean-interact's default is its own fork,
#: whose newest tag stopped at Lean v4.33.0-rc1 (checked 2026-09-22); the
#: community REPL tags a release per Lean version, so `repl_rev_for` always
#: resolves against it. Verified on Mathlib at Lean v4.34.0-rc2: Command,
#: sorry -> proof state, ProofStep -> Completed.
REPL_GIT_ENV: str = "SMOLBENCH_REPL_GIT"
DEFAULT_REPL_GIT: str = "https://github.com/leanprover-community/repl"


def repl_rev_for(root: Path) -> str:
    """REPL git revision for the project at ``root``.

    lean-interact 0.11 defaults to REPL ``v4.21.0-rc3`` and, when no
    ``<rev>_lean-toolchain-<lean>`` tag exists for the project's Lean, falls
    back to that revision and then refuses the mismatch (seen with Mathlib at
    Lean v4.34.0-rc2). leanprover-community/repl tags a release per Lean
    version, so the project's own toolchain version is the revision to use.
    ``SMOLBENCH_REPL_REV`` overrides it.

    Parameters
    ----------
    root : Path
        Project checkout containing ``lean-toolchain``
        (``leanprover/lean4:v4.34.0-rc2``).

    Returns
    -------
    str
        e.g. ``"v4.34.0-rc2"``.
    """
    override = os.environ.get(REPL_REV_ENV)
    if override:
        return override
    toolchain = (root / "lean-toolchain").read_text().strip()
    return toolchain.rsplit(":", 1)[-1]


def _describe(response: Any) -> str:
    """Render a REPL reply's messages verbatim, for an actionable `ReplError`."""
    if isinstance(response, LeanError):
        return response.message
    return "\n".join(f"[{msg.severity}] {msg.data}" for msg in response.messages)


def open_session(
    bt: BenchmarkTheorem,
    timeout: int = 600,
    root: str | Path | None = None,
    server_factory: Callable[[Path], _ReplServer] | None = None,
) -> tuple[ReplSession, int]:
    """Start a REPL, elaborate `bt`'s statement as a stub, return its proof state.

    Resolve configuration and derive the statement before startup so deterministic failures cost
    milliseconds. Retry server startup and ``import``, never `StatementError` elaboration.

    Parameters
    ----------
    bt : BenchmarkTheorem
    timeout : int, optional
    root : str | Path | None, optional
        Mathlib4 checkout root.
    server_factory : Callable[[Path], _ReplServer] | None, optional
        Started server factory, defaulting to `_default_server_factory`.

    Returns
    -------
    tuple[ReplSession, int]
        Live session and stub proof-state id, where tactic 0 applies.

    Raises
    ------
    ReplError
        Misconfiguration, failed server start, or failed import; never bare `RuntimeError`.
    StatementError
        Missing statement boundary or failed stub elaboration; not retried.
    """
    # Translate here: `verify.verify_proof_tail` maps `RuntimeError` to the false corpus claim
    # ``"replay_failed"``, while direct `mathlib_root` callers need its native error.
    try:
        resolved_root = mathlib_root(root)
    except RuntimeError as exc:
        raise ReplError(str(exc)) from exc

    stub = theorem_statement_stub(bt, resolved_root)
    # Scoped first (the file's namespace/section/variable/open context), bare
    # second: the bare form still covers self-contained statements when the
    # prefix itself fails to elaborate (e.g. a ``variable`` naming a private def).
    commands = scope_commands(resolved_root, bt.file_path, bt.start[0])
    bound = declaration_in_commands(resolved_root, bt.file_path, bt.start[0])
    # The `... in` commands are part of the declaration, so both variants carry them.
    stub = "\n".join([*bound, stub])
    prefix = "\n".join(commands)
    stubs = [f"{prefix}\n\n{stub}", stub] if prefix else [stub]
    tactic_prefix = tactic_open_prefix(scoped_syntax_namespaces([*commands, *bound]))
    module = module_name(bt.file_path)
    factory = server_factory or _default_server_factory

    last_exc: Exception | None = None
    for attempt in range(_REPL_OPEN_RETRIES):
        session: ReplSession | None = None
        try:
            session = ReplSession(
                server=factory(resolved_root),
                timeout=timeout,
                theorem=bt.full_name,
                tactic_prefix=tactic_prefix,
            )
            return session, _open_proof_state(session, bt, module, stubs)
        except StatementError:
            # Deterministic; kill first so this terminal path leaves no Lean process.
            if session is not None:
                session.close()
            raise
        except Exception as exc:  # noqa: BLE001 - retried below, or re-raised
            # Each failed attempt must leave no Lean process.
            if session is not None:
                session.close()
            last_exc = exc
            if attempt + 1 < _REPL_OPEN_RETRIES:
                time.sleep(_REPL_OPEN_BACKOFF_S[attempt])
    assert last_exc is not None
    raise last_exc


def _open_proof_state(
    session: ReplSession,
    bt: BenchmarkTheorem,
    module: str,
    stubs: Sequence[str],
) -> int:
    """Import `module`, elaborate the first of `stubs` that works, return its ``sorry`` state.

    Import in a fresh environment (``env=None``), then elaborate each stub in its result
    until one yields a ``sorry`` without errors. The proof state is the LAST sorry's:
    a replayed ``local instance`` or ``variable`` prefix may contain sorries of its own,
    and the theorem stub always comes last.

    Parameters
    ----------
    session : ReplSession
    bt : BenchmarkTheorem
    module : str
    stubs : Sequence[str]
        Candidate commands, most complete first (see `open_session`).

    Returns
    -------
    int
        Elaborated stub ``sorry`` state id.

    Raises
    ------
    ReplError
        Failed import, including a cold/racing ``lake`` build cache.
    StatementError
        No stub elaborated; carries the FIRST (most complete) attempt's REPL text.
    """
    imported = session.run(Command(cmd=f"import {module}"))
    if isinstance(imported, LeanError) or imported.get_errors():
        raise ReplError(
            f"could not import {module} for {bt.full_name}: {_describe(imported)}"
        )

    first_failure: str | None = None
    elaborated = None
    for stub in stubs:
        elaborated = session.run(Command(cmd=stub, env=imported.env))
        failed = (
            isinstance(elaborated, LeanError)
            or elaborated.get_errors()
            or not elaborated.sorries
        )
        if not failed:
            break
        if first_failure is None:
            first_failure = (
                f"could not elaborate the statement of {bt.full_name} in module {module}: "
                f"{_describe(elaborated) or 'no sorry in the response'}\n--- stub ---\n{stub}"
            )
    else:
        assert first_failure is not None
        raise StatementError(first_failure)

    proof_state = elaborated.sorries[-1].proof_state
    if proof_state is None:
        raise StatementError(
            f"the stub for {bt.full_name} elaborated to a sorry with no proofState; "
            "no proof state can be branched from it"
        )
    return proof_state
