"""Find mathlib4 declarations that provably appeared after a cutoff date.

This script answers one question: which Lean declaration names exist in the
mathlib4 repository at a NEW commit, did not exist at an OLD commit, and can be
shown by dated evidence to have entered the repository after a target date, so
that a theorem-proving eval can be pointed at material a model cannot have
memorised. It writes the surviving names, with per-declaration provenance, as a
JSON artifact.

The pipeline has four stages, and each one only ever removes names:

1. **Scan** both commits' worktrees with a namespace-aware ``.lean`` scanner
   (:func:`scan_lean_text`, :func:`scan_tree`).
2. **Select** the names present at the new commit and absent at the old one,
   minus deprecation artefacts and moved statements
   (:func:`select_postcutoff_names`).
3. **Attribute** each survivor to the commit that introduced its line, via
   ``git blame`` bounded to ``old..new`` (:func:`resolve_provenance`).
4. **Date** that commit: preferably by the creation date of the mathlib PR named
   in its subject, fetched from the GitHub API, else by the commit's own author
   date (:func:`apply_pr_filter`).

Importing this module performs no I/O and no network access. Every network call
in the whole script goes through :func:`fetch_pr_created_at` and nowhere else.

Correctness direction (the rule every other rule bends to)
----------------------------------------------------------
This is a NAME-ONLY heuristic. It never elaborates Lean, so it can never be
exactly right. The direction of the error is therefore fixed and CONSERVATIVE:
**when it is unsure whether a name is new, it treats the name as NOT new and
excludes it.** Every ambiguity below is resolved in the direction that excludes
more names. A name this module reports as post-cutoff may still, rarely, be
old; but the design goal is that the reported set is a subset of the truly-new
set as often as the heuristics allow, and a caller may treat "excluded" as
cheap and "wrongly included" as expensive.

Known approximations (all deliberate, all under-approximating)
--------------------------------------------------------------
* Only declarations whose keyword starts at column 0 are seen, so
  ``have``/``let``/``where``-fields and any indented or nested declaration is
  invisible.
* ``--`` inside a string literal is treated as the start of a line comment.
* A line whose leading text is closed block-comment (``/- .. -/ theorem foo``)
  loses its column-0 status and declares nothing.
* ``namespace``/``section``/``end`` share one scope stack and ``end`` is never
  matched by name; an unbalanced file silently drifts.
* ``private`` declarations are dropped entirely (Lean mangles their real full
  names), and unnamed declarations (``instance : Foo Bar where``) are dropped.
* ``alias`` right-hand sides are not resolved by elaboration: BOTH the bare
  token and the namespace-qualified token are emitted as candidate targets, so
  that a deprecated alias excludes both.
* The move heuristic compares whole normalised source lines, so a declaration
  whose statement line was reflowed counts as new.

Empty-tree hazard
-----------------
:func:`scan_tree` and :func:`collect_normalised_lines` return empty results for
an absent or empty tree instead of raising; they are pure functions over a
directory and have no opinion about what a caller meant. An EMPTY old tree
inverts this module's whole conservative direction, because then every name in
the new tree looks new. :func:`main` therefore refuses to continue, with
``SystemExit``, when either scanned tree yields zero declarations. A library
caller that materialises its own trees must make the same check.

Reproducibility
---------------
The artifact carries no wall clock, hostname, duration or version field, so two
runs over the same commits produce a byte-identical file. PR creation dates are
cached in ``<workdir>/cache/prs.json`` (including negative results), so a repeat
run makes no GitHub requests at all.

Usage::

    .venv/bin/python scripts/deduction/postcutoff_names.py \\
        --old 69c8a067c87c2bb6ba583f03fbf46090564be370 \\
        --new 2ca39e62989124794bd8405bb2e60805f63d37bc \\
        --target-date 2026-07-31 \\
        --workdir /scratch/postcutoff --out postcutoff_names.json

The GitHub token is read from ``--github-token`` or ``GITHUB_ACCESS_TOKEN``. It
is optional (the unauthenticated API allows 60 requests/hour, which a cold run
over a few hundred PRs will exhaust), and it is never logged, printed or written
to the artifact.
"""

import argparse
import concurrent.futures
import dataclasses
import datetime
import json
import logging
import os
import pathlib
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Iterable

#: Fixed logger name: the script is normally loaded by file path, under which
#: ``__name__`` varies, and a stable name keeps log capture predictable.
LOGGER: logging.Logger = logging.getLogger("postcutoff_names")

#: Declaration keywords recognised at column 0. ``example`` is deliberately
#: absent (it declares no name) and ``alias`` is absent because it is scanned
#: by a separate rule with its own syntax, though it does appear as a
#: ``Decl.kind``.
DECL_KEYWORDS: frozenset[str] = frozenset(
    {
        "theorem",
        "lemma",
        "def",
        "abbrev",
        "structure",
        "inductive",
        "class",
        "instance",
    }
)

#: Declaration modifiers skipped before the declaration keyword. Only true
#: modifiers belong here: a word that is itself a declaration keyword in
#: disguise (``irreducible_def``) must NOT be listed, or its own name token
#: would be read as a modifier's tail.
MODIFIERS: frozenset[str] = frozenset(
    {
        "private",
        "protected",
        "nonrec",
        "noncomputable",
        "scoped",
        "local",
        "partial",
        "unsafe",
    }
)

#: Characters that terminate a declaration's name token. Binder openers and
#: ``:`` (which also covers ``:=``) end the name; closers are absent on
#: purpose, since a name token never starts inside a binder.
_NAME_STOP_CHARS: frozenset[str] = frozenset(":({[⦃⟨<>")

#: ``_root_.Foo`` escapes the ambient namespace; the marker is stripped and no
#: prefix is applied.
_ROOT_PREFIX: str = "_root_."

#: Whole-word ``deprecated`` anywhere in an attribute block marks the
#: declaration, covering ``@[deprecated]``, ``@[deprecated (since := "...")]``
#: and ``@[simp, deprecated foo]``.
_DEPRECATED_RE: re.Pattern[str] = re.compile(r"\bdeprecated\b")

#: mathlib's merge queue appends ``(#NNNNN)`` to the first line of the commit
#: subject. ``[0-9]`` rather than ``\d`` so that non-ASCII digits (which
#: ``int()`` would happily accept) cannot produce a bogus PR number.
_PR_NUMBER_RE: re.Pattern[str] = re.compile(r"\(#([0-9]+)\)\s*$")

_WHITESPACE_RUN_RE: re.Pattern[str] = re.compile(r"\s+")

#: Bound on how many ``@[...]`` / ``open ... in`` prefixes are peeled off one
#: line before giving up. Real sources use at most two; the bound exists only
#: so that a pathological line cannot loop.
_MAX_PREFIX_STRIPS: int = 4

#: Repository scanned, cloned and asked about by default.
DEFAULT_REPO_URL: str = "https://github.com/leanprover-community/mathlib4"

#: Value of the artifact's ``method`` field: a name-set difference, then a date
#: test on the PR that introduced each surviving name.
METHOD: str = "name-set-difference+pr-opened-after-T"

#: Subdirectory of a mathlib4 checkout that holds the library itself.
_SUBDIR: str = "Mathlib"

#: GitHub REST endpoint for one pull request. Hardcoded to the mathlib4
#: repository: ``--repo-url`` selects what to clone, but the PR numbers in
#: mathlib commit subjects only mean anything against this repository.
_PR_API_URL: str = "https://api.github.com/repos/leanprover-community/mathlib4/pulls/{number}"

_API_HEADERS: dict[str, str] = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "smolbench-postcutoff",
}

#: One initial attempt plus this many retries, sleeping ``_HTTP_RETRY_SLEEPS``
#: seconds before each retry.
_HTTP_RETRIES: int = 3
_HTTP_RETRY_SLEEPS: tuple[float, ...] = (2.0, 4.0, 8.0)

#: Per-request ceiling. Unbounded ``urlopen`` calls in a loop over hundreds of
#: PRs turn one stalled socket into a hung run.
_HTTP_TIMEOUT: float = 30.0

#: Ceiling on any single git invocation. Generous, because a cold mathlib4
#: clone legitimately takes minutes; it exists to break a hang (a blobless
#: clone lazily fetching over a dead transport), not to budget a command.
_GIT_TIMEOUT: float = 1800.0

#: Lines of git stderr quoted in a :class:`RuntimeError`.
_STDERR_TAIL_LINES: int = 5

#: ``git blame --line-porcelain`` emits one of these headers before every line:
#: ``<sha> <original-line> <final-line> [<lines-in-group>]``. Content lines are
#: tab-prefixed and key/value headers start with a word, so neither can match.
_BLAME_HEADER_RE: re.Pattern[str] = re.compile(
    r"^([0-9a-f]{40}) (?P<orig>[0-9]+) (?P<final>[0-9]+)(?: [0-9]+)?$"
)


class RateLimitError(RuntimeError):
    """Raised when the GitHub API refuses a request for rate-limit reasons.

    Carries no token material: the message names the PR number and the status
    code only.
    """


@dataclasses.dataclass(frozen=True)
class Decl:
    """One Lean declaration found by the scanner.

    Attributes
    ----------
    full_name : str
        Namespace-qualified name, e.g. ``"Foo.Bar.baz"``. Never empty.
    file_path : str
        Path of the containing file relative to the scanned tree root, POSIX
        style, e.g. ``"Mathlib/Order/Basic.lean"``.
    line : int
        1-based line number of the line carrying the declaration keyword. For a
        multi-line attribute block this is the line the keyword itself is on.
    kind : str
        A member of :data:`DECL_KEYWORDS`, or ``"alias"``.
    statement : str
        The declaration's source line passed through :func:`normalise_line`.
        This is the RAW line, including any ``@[simp] `` or ``open ... in ``
        prefix and any trailing comment, because it is compared against the
        equally raw lines of :func:`collect_normalised_lines`.
    deprecated : bool
        True when an ``@[deprecated ...]`` attribute is attached.
    alias_targets : tuple of str
        For ``kind == "alias"``, the conservatively resolved candidate full
        names of the right-hand side; ``()`` for every other kind.
    """

    full_name: str
    file_path: str
    line: int
    kind: str
    statement: str
    deprecated: bool
    alias_targets: tuple[str, ...]


def normalise_line(line: str) -> str:
    """Collapse whitespace runs in a source line and strip the ends.

    No other transformation is applied: no case folding and, in particular, no
    comment stripping. The same function produces :attr:`Decl.statement` and
    the entries of :func:`collect_normalised_lines`, so that the move heuristic
    of :func:`select_postcutoff_names` compares like with like.

    Parameters
    ----------
    line : str
        A raw source line, with or without a trailing newline.

    Returns
    -------
    str
        The line with every whitespace run replaced by a single space and
        leading/trailing whitespace removed. Possibly the empty string.

    Examples
    --------
    >>> normalise_line("  theorem   foo :\\tTrue := trivial  ")
    'theorem foo : True := trivial'
    """
    return _WHITESPACE_RUN_RE.sub(" ", line).strip()


def _strip_comments(line: str, depth: int) -> tuple[str, int]:
    """Remove Lean comments from one line, carrying block-comment depth.

    Lean 4 block comments nest, so the depth is a counter rather than a flag,
    and doc comments ``/-- ... -/`` are just block comments for this purpose.

    Parameters
    ----------
    line : str
        The raw line.
    depth : int
        Block-comment nesting depth in force at the start of the line; 0 when
        the line starts in ordinary code.

    Returns
    -------
    tuple of (str, int)
        The code-only text of the line and the depth in force at the start of
        the next line.

    Notes
    -----
    Text emitted while at depth 0 keeps its original column, so a leading run
    of code preserves column-0 detection. Text emitted AFTER a block comment
    closes mid-line does not: the comment's characters are dropped rather than
    blanked, so ``/- x -/ theorem foo`` yields code that no longer starts at
    column 0 and therefore declares nothing. That is the conservative
    direction, and mathlib does not write declarations that way.
    """
    out: list[str] = []
    i = 0
    n = len(line)
    while i < n:
        pair = line[i : i + 2]
        if depth > 0:
            # Inside a block comment nothing is emitted; only the nesting
            # markers matter, and `--` is inert here.
            if pair == "/-":
                depth += 1
                i += 2
            elif pair == "-/":
                depth -= 1
                i += 2
            else:
                i += 1
        elif pair == "/-":
            depth += 1
            i += 2
        elif pair == "--":
            # Rest of the line is a line comment. Known approximation: this
            # also fires for `--` inside a string literal.
            break
        else:
            out.append(line[i])
            i += 1
    return "".join(out), depth


def _consume_attribute(text: str, balance: int) -> tuple[str, int, str]:
    """Consume attribute-block characters from ``text``.

    Parameters
    ----------
    text : str
        Text starting inside, or at the ``@`` of, an attribute block.
    balance : int
        Square-bracket balance already open; 0 when ``text`` starts at ``@[``.

    Returns
    -------
    tuple of (str, int, str)
        The consumed attribute text, the bracket balance still open (0 when the
        block closed on this line), and the remainder of the line after the
        closing bracket (empty while the block is still open).
    """
    for i, ch in enumerate(text):
        if ch == "[":
            balance += 1
        elif ch == "]":
            balance -= 1
            if balance == 0:
                return text[: i + 1], 0, text[i + 1 :]
    return text, balance, ""


def _strip_modifiers(text: str) -> tuple[list[str], str]:
    """Peel a leading run of :data:`MODIFIERS` off column-0 text.

    Parameters
    ----------
    text : str
        Column-0 text, already free of comments and of any ``@[...]`` or
        ``open ... in`` prefix.

    Returns
    -------
    tuple of (list of str, str)
        The modifiers found, in source order, and the remaining text with its
        leading whitespace removed.

    Notes
    -----
    A modifier only counts when it is a whole word FOLLOWED by whitespace, so
    a declaration named exactly like a modifier is not mistaken for one. The
    same peeling feeds both the declaration branch and the scope-keyword
    branch of the scanner, because ``noncomputable section`` is ubiquitous in
    mathlib and a missed ``section`` push would desynchronise the scope stack.
    """
    modifiers: list[str] = []
    rest = text
    while True:
        parts = rest.split(None, 1)
        if len(parts) == 2 and parts[0] in MODIFIERS:
            modifiers.append(parts[0])
            rest = parts[1]
        else:
            return modifiers, rest.lstrip()


def _name_token(text: str) -> str:
    """Read a declaration's name token off the text following its keyword.

    Parameters
    ----------
    text : str
        Text immediately after the declaration keyword and its whitespace.

    Returns
    -------
    str
        The name token, which runs up to the first whitespace character or
        member of :data:`_NAME_STOP_CHARS`. The empty string means the
        declaration is unnamed (``instance : Foo Bar where``,
        ``instance [Group G] : Foo G``) and must be skipped. A universe binder
        leaves a trailing dot on the token (``def foo.{u}`` gives ``foo.``),
        which :func:`_qualify` strips.
    """
    for i, ch in enumerate(text):
        if ch.isspace() or ch in _NAME_STOP_CHARS:
            return text[:i]
    return text


def _qualify(token: str, prefix: str) -> str:
    """Apply the ambient namespace prefix to a declared name token.

    Parameters
    ----------
    token : str
        The declared name token, possibly dotted, possibly ``_root_.``-escaped.
    prefix : str
        Dot-joined ambient namespace, or ``""`` at the top level.

    Returns
    -------
    str
        The full name, or ``""`` when the token carries no name at all (an
        empty token, a bare ``_root_.``, or a token that is only dots), which
        the caller must skip.

    Notes
    -----
    Trailing dots are stripped before qualification. They come from a universe
    binder, whose ``{`` ends the name token one character too late
    (``def foo.{u}`` reads as ``foo.``); the declared name is ``foo``. The
    ``_root_.`` escape is honoured first, so that its own dot is not mistaken
    for a universe binder's.
    """
    if token.startswith(_ROOT_PREFIX):
        # `_root_.` is an explicit escape: no prefix, marker removed.
        return token[len(_ROOT_PREFIX) :].rstrip(".")
    token = token.rstrip(".")
    if not token:
        return ""
    return f"{prefix}.{token}" if prefix else token


def _alias_targets(text: str, prefix: str) -> tuple[str, ...]:
    """Resolve an ``alias``'s right-hand side into candidate full names.

    Parameters
    ----------
    text : str
        The text following the alias's left-hand side, expected to contain
        ``:=`` and then a single dotted token.
    prefix : str
        Dot-joined ambient namespace, or ``""``.

    Returns
    -------
    tuple of str
        The bare token first and, when a namespace is in force, the
        namespace-qualified form second; deduplicated, order preserved. Empty
        when the line carries no ``:=`` or no token after it.

    Notes
    -----
    Deciding which of the two candidates Lean would actually pick needs
    elaboration (it depends on what is ``open`` and on which of them exists).
    Emitting both, so that a deprecated alias later excludes both, is the
    conservative direction: over-exclusion is the acceptable error.

    A multi-line alias whose ``:=`` is on a later line under-resolves to ``()``
    here, which means a deprecated multi-line alias excludes its own name but
    not its target.
    """
    marker = text.find(":=")
    if marker == -1:
        return ()
    rhs = text[marker + 2 :].split(None, 1)
    if not rhs:
        return ()
    token = rhs[0]
    if token.startswith(_ROOT_PREFIX):
        token = token[len(_ROOT_PREFIX) :]
    if not token:
        return ()
    candidates = [token]
    if prefix:
        candidates.append(f"{prefix}.{token}")
    # dict.fromkeys deduplicates while preserving first-seen order.
    return tuple(dict.fromkeys(candidates))


def _alias_names(text: str) -> tuple[list[str], str]:
    """Split an ``alias``'s left-hand side from the rest of the line.

    Parameters
    ----------
    text : str
        The text following the ``alias`` keyword.

    Returns
    -------
    tuple of (list of str, str)
        The declared name tokens (``_`` placeholders NOT yet removed) and the
        remainder of the line, which holds the ``:=`` and the target.

    Notes
    -----
    Handles both ``alias X := Y`` and the iff-splitting forms
    ``alias ⟨X, Y⟩ := Z`` and ``alias ⟨_, X⟩ := Z``. An unterminated ``⟨``
    yields no names, which skips the declaration.
    """
    if text.startswith("⟨"):
        close = text.find("⟩")
        if close == -1:
            return [], ""
        return [part.strip() for part in text[1:close].split(",")], text[close + 1 :]
    token = _name_token(text)
    return [token], text[len(token) :]


def scan_lean_text(text: str, file_path: str) -> list[Decl]:
    """Scan one ``.lean`` file's text for top-level declarations.

    Parameters
    ----------
    text : str
        The full text of the file.
    file_path : str
        Path recorded on every returned :class:`Decl`; the caller decides what
        it is relative to (:func:`scan_tree` makes it POSIX-relative to the
        tree root).

    Returns
    -------
    list of Decl
        The declarations found, in source order. May contain duplicate
        ``full_name`` values only if the file itself does.

    Notes
    -----
    The scanner is line-oriented and stateful across lines: it tracks
    block-comment nesting depth, a scope stack, and a pending attribute block.
    It performs no I/O.

    Recognised forms, in the order the scanner tries them on a column-0 line:
    a balanced ``@[...]`` attribute prefix, an ``open ... in`` prefix, a run of
    :data:`MODIFIERS`, then one of ``namespace`` / ``section`` / ``end`` /
    ``alias`` / a member of :data:`DECL_KEYWORDS`.

    Known approximations
    --------------------
    1. **Column 0 only.** A declaration keyword is recognised only at column 0
       (after optional modifiers and an optional ``open ... in`` prefix).
       mathlib puts top-level declarations at column 0, and requiring it is
       what keeps ``have``/``let``/``where``-fields and nested terms inside
       proofs from being read as declarations. Deliberate
       under-approximation: an indented top-level declaration is missed.
    2. **Comments.** Block comments ``/- ... -/`` (including doc comments
       ``/-- ... -/``) are skipped, may span many lines and DO nest, so the
       depth is counted. Line comments ``--`` hide the rest of their line, so
       a line whose first non-space content is ``--`` declares nothing.
       Deliberate approximation: ``--`` inside a string literal is treated as
       a comment. See :func:`_strip_comments` for the column-0 consequence of
       a block comment that closes mid-line.
    3. **Scopes.** ``namespace X`` (X may be dotted) pushes a NAMED scope;
       ``section`` / ``section Name`` pushes an ANONYMOUS one; ``end`` and
       ``end X`` pop the innermost scope whatever it is, and are ignored when
       the stack is empty. Names are never matched on ``end``: mathlib is
       well-formed, and matching would only add failure modes. The namespace
       prefix is the dot-join of the NAMED scopes in order. Deliberate
       approximation: ``namespace`` inside ``section`` and vice versa share
       this single stack, so an unbalanced file silently drifts and every
       later name in it is wrong.
    4. **Name token.** After the keyword, the name runs up to the first
       whitespace or one of ``:({[⦃⟨<>`` (``:`` also covering ``:=``). An
       empty token means the declaration is unnamed, and the whole
       declaration is skipped; ``example`` is skipped for free by not being a
       keyword. A token carrying universe parameters (``def foo.{u}``) reads
       as ``foo.``, because ``{`` ends the token one character late; the
       trailing dot is stripped, giving ``foo``. A token left empty by that
       strip skips the declaration.
    5. **``open ... in``.** ``open Foo Bar in`` alone on a line is ignored, and
       ``open Foo in theorem bar ...`` has everything up to and including the
       first ``" in "`` stripped, with the remainder re-parsed as if at column
       0. No other ``... in`` prefix is handled -- notably not
       ``variable ... in``.
    6. **``private``.** Private declarations produce no :class:`Decl` at all,
       because Lean mangles their real full names and a mangled name could
       never match across two trees.
    7. **``protected``.** Keeps the namespace prefix: ``protected`` changes
       only how a name may be opened, not the name itself.
    8. **``_root_.``.** A name token starting with ``_root_.`` has the marker
       stripped and receives NO namespace prefix. Otherwise a dotted token is
       appended to the prefix as-is (``theorem Foo.bar`` inside
       ``namespace N`` gives ``N.Foo.bar``).
    9. **Attributes.** A column-0 line starting with ``@[`` opens an attribute
       block that may span lines until its brackets balance; the text attaches
       to the NEXT declaration found, and is cleared once attached or when a
       blank line or a ``namespace``/``section``/``end`` line intervenes. A
       declaration on the same line as the closing bracket is parsed as if at
       column 0. :attr:`Decl.deprecated` is true when the attached text
       contains whole-word ``deprecated``. Deliberate approximation: an
       attribute is NOT cleared by a skipped (private or unnamed)
       declaration, so it may attach to a later one -- which over-marks
       ``deprecated``, and over-marking excludes more.
    10. **``alias``.** ``alias X := Y``, ``alias ⟨X, Y⟩ := Z`` and
        ``alias ⟨_, X⟩ := Z`` at column 0 produce one ``kind="alias"``
        :class:`Decl` per declared name, skipping the ``_`` placeholder. Left
        names get the rule-8 treatment; the right-hand side is resolved
        conservatively into both candidate forms (see :func:`_alias_targets`).

    Examples
    --------
    >>> decls = scan_lean_text("namespace Foo\\ntheorem bar : True := trivial\\n", "F.lean")
    >>> [(d.full_name, d.kind, d.line) for d in decls]
    [('Foo.bar', 'theorem', 2)]
    """
    decls: list[Decl] = []
    scopes: list[str | None] = []
    comment_depth = 0
    pending_attr: str | None = None
    attr_balance = 0

    for index, raw_line in enumerate(text.splitlines()):
        lineno = index + 1
        code, comment_depth = _strip_comments(raw_line, comment_depth)

        # Phase 1: obtain the column-0 code text of this line, or skip it.
        if attr_balance > 0:
            # Still inside a multi-line attribute block opened on an earlier line.
            consumed, attr_balance, remainder = _consume_attribute(code, attr_balance)
            pending_attr = f"{pending_attr or ''} {consumed}"
            if attr_balance > 0:
                continue
            candidate = remainder.strip()
        else:
            if not raw_line.strip():
                # A truly blank line detaches a pending attribute. Blankness is
                # judged on the RAW line, so a comment-only line does not
                # detach it -- keeping the attribute over-marks `deprecated`,
                # which excludes more.
                pending_attr = None
                continue
            if not code.strip() or code[:1].isspace():
                continue
            candidate = code.strip()

        # Phase 2: peel any `@[...]` and `open ... in` prefixes, in either
        # order, re-treating what is left as column-0 text each time.
        for _ in range(_MAX_PREFIX_STRIPS):
            if candidate.startswith("@["):
                consumed, attr_balance, remainder = _consume_attribute(candidate, 0)
                pending_attr = f"{pending_attr or ''} {consumed}"
                candidate = "" if attr_balance > 0 else remainder.strip()
                continue
            if candidate.startswith("open "):
                trimmed = candidate.rstrip()
                if trimmed.endswith(" in"):
                    # Layout (a): the declaration is on the next line.
                    candidate = ""
                    break
                marker = trimmed.find(" in ")
                if marker == -1:
                    # A plain `open Foo`: affects resolution, not names.
                    candidate = ""
                    break
                candidate = trimmed[marker + 4 :].strip()
                continue
            break
        if not candidate:
            continue

        # Phase 3: classify the column-0 text. Modifiers are peeled first so
        # that `noncomputable section` still pushes a scope; a missed push
        # would let the matching `end` pop a real namespace and silently
        # unqualify every later name in the file.
        modifiers, rest = _strip_modifiers(candidate)
        parts = rest.split(None, 1)
        head = parts[0] if parts else ""
        tail = parts[1] if len(parts) == 2 else ""

        if head == "namespace":
            # `namespace Foo.Bar` pushes the dotted name as one named scope.
            name = tail.split()[0] if tail.split() else ""
            scopes.append(name or None)
            pending_attr = None
            continue
        if head == "section":
            scopes.append(None)
            pending_attr = None
            continue
        if head == "end":
            if scopes:
                scopes.pop()
            pending_attr = None
            continue

        if head != "alias" and head not in DECL_KEYWORDS:
            continue
        if "private" in modifiers:
            # Rule 6: no Decl at all, and the pending attribute survives.
            continue

        prefix = ".".join(scope for scope in scopes if scope)
        deprecated = pending_attr is not None and bool(_DEPRECATED_RE.search(pending_attr))
        statement = normalise_line(raw_line)

        if head == "alias":
            names, remainder = _alias_names(tail)
            targets = _alias_targets(remainder, prefix)
            emitted = False
            for name in names:
                if not name or name == "_":
                    continue
                full_name = _qualify(name, prefix)
                if not full_name:
                    continue
                decls.append(
                    Decl(
                        full_name=full_name,
                        file_path=file_path,
                        line=lineno,
                        kind="alias",
                        statement=statement,
                        deprecated=deprecated,
                        alias_targets=targets,
                    )
                )
                emitted = True
            if emitted:
                pending_attr = None
            continue

        full_name = _qualify(_name_token(tail), prefix)
        if not full_name:
            # Unnamed declaration (rule 4): skipped entirely.
            continue
        decls.append(
            Decl(
                full_name=full_name,
                file_path=file_path,
                line=lineno,
                kind=head,
                statement=statement,
                deprecated=deprecated,
                alias_targets=(),
            )
        )
        pending_attr = None

    return decls


def _iter_lean_files(root: pathlib.Path, subdir: str) -> list[pathlib.Path]:
    """List the ``.lean`` files of a tree in a deterministic order.

    Parameters
    ----------
    root : pathlib.Path
        Tree root (a checkout of the repository).
    subdir : str
        Subdirectory of ``root`` to walk; ``""`` walks ``root`` itself.

    Returns
    -------
    list of pathlib.Path
        Every ``*.lean`` file under ``root / subdir``, recursively, sorted.
        Empty when that directory does not exist -- see the module docstring's
        empty-tree hazard.

    Notes
    -----
    Shared by :func:`scan_tree` and :func:`collect_normalised_lines` so that
    both see exactly the same files in exactly the same order.
    """
    base = root / subdir if subdir else root
    # `rglob` also yields directories, and a directory named `*.lean` would
    # make the callers' `read_text` raise; filter it here, as the sibling
    # scripts in this directory do.
    return sorted(path for path in base.rglob("*.lean") if path.is_file())


def scan_tree(root: pathlib.Path, subdir: str = "Mathlib") -> dict[str, Decl]:
    """Scan every ``.lean`` file of a tree and index the declarations by name.

    Parameters
    ----------
    root : pathlib.Path
        Tree root; recorded ``file_path`` values are relative to this.
    subdir : str, default "Mathlib"
        Subdirectory of ``root`` to walk, so that a repository's own build and
        test directories are excluded.

    Returns
    -------
    dict of str to Decl
        Maps ``full_name`` to its declaration. Empty when the directory is
        absent or holds no ``.lean`` files.

    Notes
    -----
    Files are read with ``encoding="utf-8", errors="replace"``: a decoding
    error must degrade one line, never abort a whole-repository scan.

    On a duplicate full name the FIRST occurrence in sorted-file, source order
    wins. mathlib does not define the same full name twice, so this tie-break
    exists only to make the result independent of filesystem iteration order.
    """
    out: dict[str, Decl] = {}
    for path in _iter_lean_files(root, subdir):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()
        for decl in scan_lean_text(text, rel):
            # First wins; see Notes.
            if decl.full_name not in out:
                out[decl.full_name] = decl
    return out


def collect_normalised_lines(root: pathlib.Path, subdir: str = "Mathlib") -> set[str]:
    """Collect every non-empty normalised source line of a tree.

    Parameters
    ----------
    root : pathlib.Path
        Tree root.
    subdir : str, default "Mathlib"
        Subdirectory of ``root`` to walk.

    Returns
    -------
    set of str
        ``normalise_line`` of every line of every ``*.lean`` file under
        ``root / subdir``, excluding lines that normalise to ``""``.

    Notes
    -----
    This is the "did this exact text already exist at the old commit" oracle
    for the move heuristic of :func:`select_postcutoff_names`. It deliberately
    contains ALL lines rather than just declaration lines: the broader set
    matches more statements and therefore excludes more names, which is the
    conservative direction.

    Memory: mathlib is roughly 1.5 million lines, so the returned set holds on
    the order of a million short strings (a few hundred MB). That is accepted
    because the script runs once, offline, on a developer machine, and because
    the alternative -- re-reading the old tree per candidate -- is orders of
    magnitude slower. Files are read with ``errors="replace"`` for the same
    reason as :func:`scan_tree`.
    """
    lines: set[str] = set()
    for path in _iter_lean_files(root, subdir):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            normalised = normalise_line(line)
            if normalised:
                lines.add(normalised)
    return lines


def deprecation_excluded_names(decls: Iterable[Decl]) -> set[str]:
    """Collect the names that a deprecation or rename accounts for.

    Parameters
    ----------
    decls : iterable of Decl
        The declarations of the NEW commit (all of them, not just the diff:
        a deprecated alias outside the diff can still name a target inside it).

    Returns
    -------
    set of str
        Every deprecated declaration's ``full_name``, of any kind, plus every
        ``alias_targets`` entry of every DEPRECATED alias. Names that are not
        in the caller's diff are returned too; the caller subtracts.

    Notes
    -----
    Non-deprecated aliases contribute nothing here: they are ordinary
    declarations as far as this function is concerned.
    """
    excluded: set[str] = set()
    for decl in decls:
        if not decl.deprecated:
            continue
        excluded.add(decl.full_name)
        if decl.kind == "alias":
            # The standard mathlib rename is "new decl `Bar.baz` +
            # `@[deprecated] alias Foo.foo := Bar.baz`". The target of a
            # deprecated alias is therefore the renamed OLD theorem wearing a
            # new name, not new mathematics, so it must go too. Both candidate
            # resolutions are dropped, since we cannot tell which one Lean
            # meant (see `_alias_targets`).
            excluded.update(decl.alias_targets)
    return excluded


def parse_pr_number(commit_message: str) -> int | None:
    """Extract the mathlib PR number from a commit message.

    mathlib's merge queue puts the PR number in a trailing ``(#NNNNN)`` on the
    FIRST line of the message.

    Parameters
    ----------
    commit_message : str
        The full commit message.

    Returns
    -------
    int or None
        The PR number when the first line ends in ``(#NNNNN)``, allowing
        trailing whitespace; ``None`` otherwise. A ``(#123)`` in the middle of
        the first line, one on a later line, and a non-numeric body such as
        ``(#abc)`` all yield ``None``.

    Examples
    --------
    >>> parse_pr_number("feat: add Foo.bar (#12345)\\n\\nBody (#999)\\n")
    12345
    >>> parse_pr_number("chore: no pr number") is None
    True
    """
    first_line = commit_message.splitlines()[:1]
    if not first_line:
        return None
    match = _PR_NUMBER_RE.search(first_line[0])
    return int(match.group(1)) if match else None


def select_postcutoff_names(
    new_decls: dict[str, Decl],
    old_decls: dict[str, Decl],
    old_lines: set[str],
    old_files: set[str],
) -> tuple[dict[str, Decl], dict[str, int]]:
    """Reduce two scanned trees to the declarations that are genuinely new.

    Parameters
    ----------
    new_decls : dict of str to Decl
        Declarations of the NEW commit, as returned by :func:`scan_tree`.
    old_decls : dict of str to Decl
        Declarations of the OLD commit.
    old_lines : set of str
        Normalised source lines of the OLD commit, from
        :func:`collect_normalised_lines`.
    old_files : set of str
        POSIX-relative paths that existed at the OLD commit.

    Returns
    -------
    tuple of (dict of str to Decl, dict of str to int)
        The kept declarations, ordered by sorted full name, and the funnel
        counts, whose keys are exactly and in this order ``n_old_decls``,
        ``n_new_decls``, ``n_name_diff``, ``n_after_deprecated``,
        ``n_after_move``. ``n_after_move`` equals ``len(kept)``.

    Notes
    -----
    Pure: no I/O, no mutation of the arguments. The three filters run in this
    order.

    1. Name-set difference: keep the names absent from ``old_decls``.
    2. Deprecation: drop everything in
       ``deprecation_excluded_names(new_decls.values())``. Note that the whole
       new tree, not the diff, feeds that call, so a deprecated alias whose own
       name is old still excludes its target.
    3. Move heuristic: drop a declaration when BOTH its file is new
       (``file_path not in old_files``) AND its statement text already existed
       somewhere in the old tree (``statement in old_lines``). That is the
       signature of a declaration moved or renamed into a new file rather than
       written for the first time. Requiring a NEW file keeps a genuinely new
       declaration that happens to duplicate a line of its own unchanged file
       from being dropped, while still catching the file-split case, which is
       how mathlib actually moves material.
    """
    diff = {name: decl for name, decl in new_decls.items() if name not in old_decls}

    excluded = deprecation_excluded_names(new_decls.values())
    after_deprecated = {name: decl for name, decl in diff.items() if name not in excluded}

    after_move = {
        name: decl
        for name, decl in after_deprecated.items()
        if not (decl.file_path not in old_files and decl.statement in old_lines)
    }

    kept = {name: after_move[name] for name in sorted(after_move)}
    counts = {
        "n_old_decls": len(old_decls),
        "n_new_decls": len(new_decls),
        "n_name_diff": len(diff),
        "n_after_deprecated": len(after_deprecated),
        "n_after_move": len(kept),
    }
    return kept, counts


# ---------------------------------------------------------------------------
# Git plumbing
# ---------------------------------------------------------------------------


def _run_git(args: list[str], cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    """Run one git command and return the completed process.

    Parameters
    ----------
    args : list of str
        Arguments after ``git``.
    cwd : pathlib.Path or None, optional
        Working directory for the child process.

    Returns
    -------
    subprocess.CompletedProcess
        With ``text=True`` streams captured.

    Raises
    ------
    subprocess.TimeoutExpired
        After :data:`_GIT_TIMEOUT` seconds.

    Notes
    -----
    Private because callers normally want :func:`run_git`'s stdout-or-raise
    contract. The two exceptions are presence probes (``git cat-file -e``
    prints nothing, so only its exit code carries the answer) and the
    best-effort steps that must branch on an exit code rather than catch an
    exception.
    """
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=_GIT_TIMEOUT
    )


def run_git(args: list[str], cwd: pathlib.Path | None = None, check: bool = True) -> str:
    """Run one git command and return its standard output.

    Parameters
    ----------
    args : list of str
        Arguments after ``git``, e.g. ``["-C", str(clone), "rev-parse", "HEAD"]``.
    cwd : pathlib.Path or None, optional
        Working directory for the child process.
    check : bool, default True
        Raise on a non-zero exit status. With ``check=False`` a failing command
        yields the empty string, which the callers treat as "no answer".

    Returns
    -------
    str
        The command's standard output, undecorated.

    Raises
    ------
    RuntimeError
        When ``check`` is true and git exits non-zero. The message names the
        command, the exit code and the last :data:`_STDERR_TAIL_LINES` lines of
        stderr.
    subprocess.TimeoutExpired
        After :data:`_GIT_TIMEOUT` seconds, regardless of ``check``: a hung
        transport is an infrastructure failure, not an unresolved declaration,
        so it must not be mistaken for one.

    Notes
    -----
    The GitHub token is never passed to git (git talks to the anonymous HTTPS
    remote), so no argument list handled here can leak it.
    """
    proc = _run_git(args, cwd=cwd)
    if check and proc.returncode != 0:
        tail = " | ".join((proc.stderr or "").strip().splitlines()[-_STDERR_TAIL_LINES:])
        raise RuntimeError(f"git {' '.join(args)} failed (exit {proc.returncode}): {tail}")
    return proc.stdout


def _commit_present(clone: pathlib.Path, commit: str) -> bool:
    """Report whether ``commit`` resolves to a commit object inside ``clone``."""
    return _run_git(["-C", str(clone), "cat-file", "-e", f"{commit}^{{commit}}"]).returncode == 0


def _ensure_commits_present(clone: pathlib.Path, commits: Iterable[str]) -> None:
    """Fetch any of ``commits`` the clone does not already have.

    Parameters
    ----------
    clone : pathlib.Path
        The clone directory.
    commits : iterable of str
        Commit-ish arguments that later steps must be able to resolve.

    Raises
    ------
    RuntimeError
        When a commit is still missing after the fetch. A missing endpoint
        would silently turn into an empty or wrong diff, so it must stop the
        run rather than degrade it.

    Notes
    -----
    The fetch itself is judged by its exit code rather than by an exception,
    because a shallow or partial remote may legitimately refuse a
    fetch-by-sha; only the re-check decides.
    """
    for commit in commits:
        if _commit_present(clone, commit):
            continue
        LOGGER.info("commit %s not present locally; fetching it from origin", commit)
        _run_git(["-C", str(clone), "fetch", "--no-tags", "origin", commit])
        if not _commit_present(clone, commit):
            raise RuntimeError(
                f"commit {commit} is not present in {clone} and could not be fetched from origin"
            )


def ensure_clone(
    workdir: pathlib.Path,
    repo_url: str = DEFAULT_REPO_URL,
    *,
    commits: Iterable[str] = (),
) -> pathlib.Path:
    """Return a usable clone of the repository under ``workdir``, creating it if needed.

    Parameters
    ----------
    workdir : pathlib.Path
        Scratch directory; the clone is ``workdir / "mathlib4"``.
    repo_url : str, default :data:`DEFAULT_REPO_URL`
        Remote to clone from.
    commits : iterable of str, optional, keyword-only
        Commit-ishes that must resolve locally afterwards; each missing one is
        fetched from origin. Empty by default, which checks nothing.

    Returns
    -------
    pathlib.Path
        The clone directory.

    Raises
    ------
    RuntimeError
        When both clone attempts fail, or when a requested commit is still
        missing after its fetch.

    Notes
    -----
    An existing directory whose ``git rev-parse --git-dir`` succeeds is REUSED
    untouched. Cloning mathlib4 costs minutes, and the whole script is meant to
    be re-runnable (and to be pointed at a pre-warmed clone), so re-cloning
    would be the wrong default.

    The clone is ``--filter=blob:none --no-checkout``: history and trees are
    needed for ``blame``, but the ~2 GB of file blobs are not, and the
    worktrees fetch the few they need lazily. Some servers and transports
    reject an object filter, so a failed filtered clone is logged and retried
    once as a plain clone; the run is then slower but correct.
    """
    clone = workdir / "mathlib4"
    preexisting = clone.exists()
    if preexisting and run_git(["-C", str(clone), "rev-parse", "--git-dir"], check=False).strip():
        LOGGER.info("reusing existing clone at %s", clone)
    else:
        workdir.mkdir(parents=True, exist_ok=True)
        filtered = _run_git(["clone", "--filter=blob:none", "--no-checkout", repo_url, str(clone)])
        if filtered.returncode != 0:
            LOGGER.warning(
                "blobless clone failed (exit %d); retrying without --filter",
                filtered.returncode,
            )
            # Only remove what this call created: a directory that was already
            # there before the attempt is the operator's, not ours.
            if not preexisting and clone.exists():
                shutil.rmtree(clone)
            run_git(["clone", "--no-checkout", repo_url, str(clone)])
        LOGGER.info("cloned %s into %s", repo_url, clone)
    if commits:
        _ensure_commits_present(clone, commits)
    return clone


def ensure_worktree(clone: pathlib.Path, path: pathlib.Path, commit: str) -> pathlib.Path:
    """Return a worktree of ``clone`` checked out at ``commit``.

    Parameters
    ----------
    clone : pathlib.Path
        The clone directory.
    path : pathlib.Path
        Where the worktree lives; created when absent, reused when present.
    commit : str
        Commit-ish to check out, detached.

    Returns
    -------
    pathlib.Path
        ``path``, checked out at ``commit``.

    Raises
    ------
    RuntimeError
        When git refuses to add the worktree or to check the commit out.

    Notes
    -----
    Worktrees rather than repeated ``git checkout`` calls in one tree: the old
    and the new commit must both be readable at the same time (the scanner and
    the move oracle read the old tree while blame reads the new one), and
    swapping a single checkout back and forth would be both slower and racy.

    An existing worktree already at ``commit`` is left completely alone, which
    is what makes a re-run cheap. The comparison is textual, so passing an
    abbreviated sha forces a redundant (harmless) checkout.
    """
    if not path.exists():
        run_git(["-C", str(clone), "worktree", "add", "--detach", "-f", str(path), commit])
        return path
    head = run_git(["-C", str(path), "rev-parse", "HEAD"], check=False).strip()
    if head == commit:
        LOGGER.info("reusing worktree %s already at %s", path, commit)
        return path
    run_git(["-C", str(path), "checkout", "--detach", "-f", commit])
    return path


def prefetch_range_objects(
    clone: pathlib.Path,
    old: str,
    new: str,
    subdir: str = "Mathlib",
    chunk_size: int = 2000,
) -> int:
    """Bulk-fetch the objects a blobless clone will need for blame.

    Parameters
    ----------
    clone : pathlib.Path
        The clone directory.
    old, new : str
        Endpoints of the revision range whose objects are wanted.
    subdir : str, default "Mathlib"
        Path filter, so that only the library's objects are fetched.
    chunk_size : int, default 2000
        Object ids per ``git fetch`` invocation, bounding the command line.

    Returns
    -------
    int
        How many object ids were requested. Zero when nothing was missing or
        when the attempt failed.

    Raises
    ------
    ValueError
        When ``chunk_size`` is below 1.

    Notes
    -----
    This is an OPTIMISATION and never a correctness requirement: without it,
    ``git blame`` fetches each missing blob on demand over its own connection.
    Measured on real mathlib: 11548 missing objects, about 35 s to prefetch,
    turning a 4.6 s per-file blame into 0.24 s.

    Because it is pure performance, and only performance, this is the one place
    in the module that catches and swallows a failure: any git or OS error is
    logged as a warning and the run continues with lazy fetching. Nothing else
    here may do that.

    An empty missing-object list returns early rather than calling ``git
    fetch`` with no object arguments, which would fetch the entire remote.
    """
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")
    requested = 0
    try:
        listing = run_git(
            [
                "-C", str(clone), "rev-list", "--objects", "--missing=print",
                f"{old}..{new}", "--", subdir,
            ]
        )
        # `--missing=print` marks each absent object with a leading `?`; every
        # other line is an object the clone already has.
        oids: list[str] = []
        seen: set[str] = set()
        for line in listing.splitlines():
            if not line.startswith("?"):
                continue
            fields = line[1:].split(maxsplit=1)
            if fields and fields[0] not in seen:
                seen.add(fields[0])
                oids.append(fields[0])
        if not oids:
            LOGGER.info("prefetch: no objects missing in %s..%s", old, new)
            return 0
        for start in range(0, len(oids), chunk_size):
            chunk = oids[start : start + chunk_size]
            run_git(
                [
                    "-C", str(clone), "fetch", "--no-tags", "--no-write-fetch-head",
                    "--filter=blob:none", "origin", *chunk,
                ]
            )
            requested += len(chunk)
        LOGGER.info("prefetched %d missing object(s) for %s..%s", requested, old, new)
    except (RuntimeError, OSError) as exc:
        LOGGER.warning(
            "object prefetch stopped after %d oid(s); blame will fetch lazily instead: %s",
            requested,
            exc,
        )
    return requested


def blame_lines(worktree: pathlib.Path, old: str, new: str, file_path: str) -> dict[int, str]:
    """Attribute each line of one file to the commit that introduced it.

    Parameters
    ----------
    worktree : pathlib.Path
        A worktree checked out at ``new``.
    old, new : str
        Endpoints of the revision range blame is bounded to.
    file_path : str
        Path of the file relative to the worktree root, POSIX style.

    Returns
    -------
    dict of int to str
        Maps 1-based final line number to the sha that introduced it. Empty
        when git fails or the file has no lines.

    Notes
    -----
    Bounding blame to ``old..new`` is what makes this affordable AND correct
    for our purpose: only commits in the range are considered, so every line
    older than ``old`` comes back attributed to the boundary commit ``old``
    itself, whose author date is by construction at or before the old commit's
    and is therefore rejected by the date filter. Blaming the whole history
    instead would walk decades of mathlib for no extra information.

    A git failure yields ``{}`` rather than an exception, so the affected
    declarations are simply dropped as unresolved -- the conservative
    direction. A ``subprocess.TimeoutExpired`` still propagates: a hung git is
    an infrastructure fault and must not be silently reported as "no such
    line".
    """
    out = run_git(
        ["-C", str(worktree), "blame", "--line-porcelain", f"{old}..{new}", "--", file_path],
        check=False,
    )
    blames: dict[int, str] = {}
    for line in out.splitlines():
        match = _BLAME_HEADER_RE.match(line)
        if match:
            blames[int(match.group("final"))] = match.group(1)
    return blames


def _iso_utc(raw: str) -> str:
    """Normalise a git ``%aI`` timestamp to ``YYYY-MM-DDTHH:MM:SSZ`` in UTC.

    Parameters
    ----------
    raw : str
        Strict ISO-8601 timestamp with an offset, as ``git log --format=%aI``
        emits it.

    Returns
    -------
    str
        The same instant in UTC, ``Z``-suffixed.

    Raises
    ------
    ValueError
        When ``raw`` is not ISO-8601.

    Notes
    -----
    Author dates are compared against GitHub's ``created_at``, which is always
    UTC with a ``Z``. Comparing a ``+02:00`` local timestamp against it as text
    would misdate every commit near midnight.
    """
    moment = datetime.datetime.fromisoformat(raw.strip())
    return moment.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def commit_metadata(clone: pathlib.Path, shas: Iterable[str]) -> dict[str, dict]:
    """Read the date, subject and PR number of each of ``shas``.

    Parameters
    ----------
    clone : pathlib.Path
        A clone that contains every sha.
    shas : iterable of str
        Commit shas; duplicates and empty strings are ignored.

    Returns
    -------
    dict of str to dict
        ``{sha: {"author_date": str, "subject": str, "pr_number": int or None}}``
        with ``author_date`` normalised by :func:`_iso_utc` and ``pr_number``
        taken from the full message by :func:`parse_pr_number`.

    Raises
    ------
    RuntimeError
        When git fails (typically an unknown revision), or when its output does
        not split into whole records.

    Notes
    -----
    One batched ``git log --no-walk -z --format=%H%x00%aI%x00%B`` call rather
    than one call per sha: a run resolves hundreds of commits, and process
    startup would dominate. The format is unambiguous because ``-z`` ends each
    record with a NUL and the format contributes exactly two more, so the
    stream splits into groups of three regardless of what a commit message
    contains. The record count is validated instead of assumed.
    """
    unique = sorted({sha for sha in shas if sha})
    if not unique:
        return {}
    out = run_git(["-C", str(clone), "log", "--no-walk", "-z", "--format=%H%x00%aI%x00%B", *unique])
    fields = out.split("\0")
    if fields and fields[-1] == "":
        fields.pop()  # trailing record separator
    if len(fields) % 3 != 0:
        raise RuntimeError(
            f"git log returned {len(fields)} field(s) for {len(unique)} commit(s), "
            "which is not a whole number of records"
        )
    metadata: dict[str, dict] = {}
    for start in range(0, len(fields), 3):
        sha, raw_date, message = fields[start : start + 3]
        lines = message.splitlines()
        metadata[sha] = {
            "author_date": _iso_utc(raw_date),
            "subject": lines[0] if lines else "",
            "pr_number": parse_pr_number(message),
        }
    return metadata


# ---------------------------------------------------------------------------
# GitHub PR provenance
# ---------------------------------------------------------------------------


def _is_rate_limited(headers: object, body: str) -> bool:
    """Decide whether a 403/429 response is a rate limit rather than a refusal.

    Parameters
    ----------
    headers : object
        The response headers, anything with a ``get``; ``None`` is tolerated.
    body : str
        The decoded response body.

    Returns
    -------
    bool
        True when the remaining-requests header is exhausted or the body says
        "rate limit". GitHub uses 403 for both rate limiting and plain
        authorisation failures, so the two must be told apart before a whole
        run is abandoned.
    """
    remaining = headers.get("X-RateLimit-Remaining") if hasattr(headers, "get") else None
    return remaining == "0" or "rate limit" in body.lower()


def fetch_pr_created_at(pr_number: int, token: str | None) -> str | None:
    """Ask the GitHub API when a mathlib pull request was opened.

    Parameters
    ----------
    pr_number : int
        Pull request number.
    token : str or None
        GitHub token. Optional; without one the API allows 60 requests/hour.

    Returns
    -------
    str or None
        The PR's ``created_at`` (``YYYY-MM-DDTHH:MM:SSZ``), or ``None`` when
        the PR does not exist (HTTP 404) or carries no creation date.

    Raises
    ------
    RateLimitError
        On an HTTP 403 or 429 that is identifiably a rate limit. The caller is
        expected to stop making requests rather than retry.
    RuntimeError
        When the request still fails after :data:`_HTTP_RETRIES` retries.

    Notes
    -----
    This is the ONLY function in the module that touches the network. Every
    other function is offline, so a caller that stubs this one out makes the
    whole script offline.

    The token is written into an ``Authorization`` header and nowhere else: it
    is never logged, never interpolated into an exception message, never
    written to the artifact, and never passed to a subprocess.

    Retry policy: one attempt, then up to :data:`_HTTP_RETRIES` retries with
    2/4/8 s sleeps. A 404 is a definitive answer and is never retried; a rate
    limit is never retried either, because retrying is exactly what the limit
    forbids.
    """
    url = _PR_API_URL.format(number=pr_number)
    headers = dict(_API_HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    last_error = "no attempt made"
    for attempt in range(_HTTP_RETRIES + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
            created_at = payload.get("created_at")
            return created_at if isinstance(created_at, str) else None
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 404:
                return None
            if exc.code in (403, 429) and _is_rate_limited(exc.headers, body):
                # Message names the status and the PR only -- never the token.
                raise RateLimitError(
                    f"GitHub rate limit reached on PR #{pr_number} (HTTP {exc.code})"
                ) from exc
            last_error = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = f"{type(exc).__name__}: {getattr(exc, 'reason', exc)}"
        if attempt < _HTTP_RETRIES:
            time.sleep(_HTTP_RETRY_SLEEPS[attempt])
    raise RuntimeError(
        f"GitHub request for PR #{pr_number} failed after {_HTTP_RETRIES + 1} attempt(s): "
        f"{last_error}"
    )


def resolve_provenance(
    kept: dict[str, Decl],
    worktree: pathlib.Path,
    clone: pathlib.Path,
    old: str,
    new: str,
    jobs: int = 8,
) -> dict[str, dict]:
    """Attribute every kept declaration to the commit that introduced it.

    Parameters
    ----------
    kept : dict of str to Decl
        Survivors of :func:`select_postcutoff_names`.
    worktree : pathlib.Path
        Worktree checked out at ``new``, where blame runs.
    clone : pathlib.Path
        Clone holding the commit metadata.
    old, new : str
        Endpoints of the blame range.
    jobs : int, default 8
        Blame threads. Blame is dominated by git subprocesses and, on a
        blobless clone, by their lazy blob fetches, so threads help; the
        default is kept low because more concurrent fetches against GitHub
        invite abuse throttling.

    Returns
    -------
    dict of str to dict
        ``{full_name: {"file_path", "introduced_commit", "author_date",
        "pr_number"}}``, ordered by sorted full name. Declarations whose line
        could not be blamed are omitted, and their number is logged; they are
        never guessed at.

    Notes
    -----
    One blame per FILE, not per declaration: several declarations usually share
    a file, and blame's cost is per file.

    Deterministic: files are blamed in sorted order, results are collected in
    input order rather than completion order, and the output is built by sorted
    name, so thread scheduling cannot change the result.
    """
    by_file: dict[str, list[str]] = {}
    for name in sorted(kept):
        by_file.setdefault(kept[name].file_path, []).append(name)
    paths = sorted(by_file)

    def _blame(path: str) -> dict[int, str]:
        return blame_lines(worktree, old, new, path)

    blames: dict[str, dict[int, str]] = {}
    if paths:
        workers = max(1, min(jobs, len(paths)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            # `map` yields in INPUT order, so completion order cannot leak in.
            blames = dict(zip(paths, pool.map(_blame, paths)))

    provenance: dict[str, dict] = {}
    unresolved = 0
    for name in sorted(kept):
        decl = kept[name]
        sha = blames.get(decl.file_path, {}).get(decl.line)
        if sha is None:
            unresolved += 1
            continue
        provenance[name] = {
            "file_path": decl.file_path,
            "introduced_commit": sha,
            "author_date": None,
            "pr_number": None,
        }

    metadata = commit_metadata(clone, [entry["introduced_commit"] for entry in provenance.values()])
    for entry in provenance.values():
        meta = metadata.get(entry["introduced_commit"], {})
        entry["author_date"] = meta.get("author_date")
        entry["pr_number"] = meta.get("pr_number")

    if unresolved:
        LOGGER.warning(
            "%d declaration(s) had no blamed line in %s..%s and were dropped", unresolved, old, new
        )
    return provenance


def _bump(counters: dict, key: str) -> None:
    """Increment ``counters[key]``, tolerating a key that is not there yet."""
    counters[key] = counters.get(key, 0) + 1


def apply_pr_filter(
    provenance: dict[str, dict],
    target_date: str,
    token: str | None,
    cache: dict,
    counters: dict,
) -> dict[str, dict]:
    """Keep only the declarations with dated evidence of being post-cutoff.

    Parameters
    ----------
    provenance : dict of str to dict
        Output of :func:`resolve_provenance`.
    target_date : str
        Cutoff, ``YYYY-MM-DD``. A declaration is kept when its evidence date is
        on or after it.
    token : str or None
        GitHub token, forwarded to :func:`fetch_pr_created_at`.
    cache : dict
        ``{str(pr_number): created_at or None}``, read AND written in place so
        that the caller can persist it; a negative result is cached too, so a
        re-run never re-asks about a deleted PR.
    counters : dict
        Mutated in place. Integer keys ``kept_pr``, ``kept_commit_date``,
        ``dropped_pr_before_target``, ``dropped_no_date``, ``rate_limited``,
        ``api_calls``.

    Returns
    -------
    dict of str to dict
        The kept entries only, ordered by sorted full name, each
        ``{"file_path", "introduced_commit", "pr_number", "pr_created_at",
        "reason"}``.

    Notes
    -----
    Evidence order: the PR's creation date first, because a mathlib PR is
    opened before it is merged and is therefore the earliest defensible moment
    the text could have been public; the commit's own author date only when no
    PR number was found or the PR no longer exists.

    ``counters["dropped_no_date"]`` covers BOTH failure modes of the
    commit-date branch -- no author date at all, and an author date before the
    target -- because both mean the same thing here: no evidence that the
    declaration is new. PR-branch rejections are counted separately in
    ``dropped_pr_before_target``.

    ``api_calls`` counts attempts, including one that turns out to be rate
    limited.

    On :class:`RateLimitError` the filter stops calling the API, logs how much
    was resolved, and drops every remaining PR-numbered entry into
    ``rate_limited`` -- dropping is the conservative direction, and raising
    would throw away the work already done. Cached PR dates are still used
    afterwards, since reading the cache is not a request. This deliberate
    catch, and :func:`prefetch_range_objects`'s, are the only two in the
    module.

    The artifact schema also allows ``reason == "new-name"``, for a
    declaration kept on name-newness alone. This pipeline always demands date
    evidence, so it never emits that value; it exists for a caller that
    relaxes the rule, and inventing a use for it here would weaken the
    conservative direction.
    """
    selected: dict[str, dict] = {}
    rate_limited = False
    for name in sorted(provenance):
        entry = provenance[name]
        pr_number = entry.get("pr_number")
        created_at = None

        if pr_number is not None:
            key = str(pr_number)
            if key in cache:
                created_at = cache[key]
            elif rate_limited:
                _bump(counters, "rate_limited")
                continue
            else:
                _bump(counters, "api_calls")
                try:
                    created_at = fetch_pr_created_at(pr_number, token)
                except RateLimitError as exc:
                    rate_limited = True
                    LOGGER.warning(
                        "%s: %d name(s) already kept, remaining PR lookups are dropped unresolved",
                        exc,
                        len(selected),
                    )
                    _bump(counters, "rate_limited")
                    continue
                cache[key] = created_at

        if created_at is not None:
            if created_at[:10] >= target_date:
                _bump(counters, "kept_pr")
                selected[name] = {
                    "file_path": entry["file_path"],
                    "introduced_commit": entry["introduced_commit"],
                    "pr_number": pr_number,
                    "pr_created_at": created_at,
                    "reason": "pr-opened-after-T",
                }
            else:
                _bump(counters, "dropped_pr_before_target")
            continue

        # No usable PR evidence: fall back to the introducing commit's own date.
        author_date = entry.get("author_date")
        if author_date is not None and author_date[:10] >= target_date:
            _bump(counters, "kept_commit_date")
            selected[name] = {
                "file_path": entry["file_path"],
                "introduced_commit": entry["introduced_commit"],
                "pr_number": None,
                "pr_created_at": None,
                "reason": "commit-date",
            }
        else:
            _bump(counters, "dropped_no_date")
    return selected


# ---------------------------------------------------------------------------
# Artifact and CLI
# ---------------------------------------------------------------------------


def build_artifact(
    old: str,
    new: str,
    target_date: str,
    counts: dict,
    selected: dict[str, dict],
    kept: dict[str, Decl],
) -> dict:
    """Assemble the JSON artifact.

    Parameters
    ----------
    old, new : str
        The two commits compared.
    target_date : str
        The cutoff the run was made against.
    counts : dict
        Funnel counts from :func:`select_postcutoff_names`; only
        ``n_new_decls`` and ``n_old_decls`` reach the artifact.
    selected : dict of str to dict
        Output of :func:`apply_pr_filter`.
    kept : dict of str to Decl
        The scanner's own records for the selected names, used as the
        authoritative source of each declaration's file path.

    Returns
    -------
    dict
        The artifact, with ``decls`` ordered by sorted full name.

    Notes
    -----
    The artifact carries no wall clock, hostname, duration or tool version, so
    two runs over the same commits are byte-identical and a re-run can be
    diffed against its predecessor to prove nothing moved.
    """
    decls: dict[str, dict] = {}
    for name in sorted(selected):
        entry = selected[name]
        decl = kept.get(name)
        decls[name] = {
            # `kept` is the scanner's own record; `selected`'s copy is derived
            # from it, so prefer the original and fall back only if absent.
            "file_path": decl.file_path if decl is not None else entry["file_path"],
            "introduced_commit": entry["introduced_commit"],
            "pr_number": entry["pr_number"],
            "pr_created_at": entry["pr_created_at"],
            "reason": entry["reason"],
        }
    return {
        "new_commit": new,
        "old_commit": old,
        "target_date": target_date,
        "method": METHOD,
        "n_new_decls": counts.get("n_new_decls", 0),
        "n_old_decls": counts.get("n_old_decls", 0),
        "n_postcutoff": len(selected),
        "decls": decls,
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Define and parse the command line.

    Parameters
    ----------
    argv : list of str or None
        Argument vector; ``None`` reads ``sys.argv``.

    Returns
    -------
    argparse.Namespace
        The parsed arguments.

    Raises
    ------
    SystemExit
        On an argparse error, an unparseable ``--target-date``, or a ``--jobs``
        below 1. Validation failures are reported as clean exits rather than
        tracebacks.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--old", required=True, help="commit-ish of the OLD (pre-cutoff) tree")
    parser.add_argument("--new", required=True, help="commit-ish of the NEW tree")
    parser.add_argument(
        "--target-date", required=True,
        help="cutoff date YYYY-MM-DD; a declaration is kept when its evidence "
        "date is on or after it",
    )
    parser.add_argument("--out", required=True, help="path of the JSON artifact to write")
    parser.add_argument("--workdir", required=True, help="scratch dir for the clone, worktrees and PR cache")
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL, help="remote to clone (default: %(default)s)")
    parser.add_argument(
        "--github-token", default=None,
        help="GitHub token; falls back to $GITHUB_ACCESS_TOKEN. Never logged or stored",
    )
    parser.add_argument("--jobs", type=int, default=8, help="parallel blame jobs (default: %(default)s)")
    parser.add_argument(
        "--no-prefetch", action="store_true",
        help="skip the bulk object prefetch (slower blame, same result)",
    )
    args = parser.parse_args(argv)

    try:
        datetime.date.fromisoformat(args.target_date)
    except ValueError as exc:
        raise SystemExit(f"--target-date must be YYYY-MM-DD: {exc}") from exc
    if args.jobs < 1:
        raise SystemExit(f"--jobs must be >= 1, got {args.jobs}")
    return args


def main(argv: list[str] | None = None) -> int:
    """Run the whole pipeline and write the artifact.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector; ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        0 on success.

    Raises
    ------
    SystemExit
        On a validation failure, including the hard refusal to diff when either
        scanned tree is empty.
    RuntimeError
        On a git failure that is not recoverable, or a GitHub failure that is
        neither a 404 nor a rate limit.

    Notes
    -----
    The PR cache is written in a ``finally``, so a run stopped by a rate limit
    or an exception still leaves every date it paid for on disk and the next
    run resumes from there.

    Logging is configured here rather than at import, so that importing this
    module stays free of side effects.
    """
    args = _parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    workdir = pathlib.Path(args.workdir)
    out_path = pathlib.Path(args.out)
    cache_path = workdir / "cache" / "prs.json"
    token = args.github_token or os.environ.get("GITHUB_ACCESS_TOKEN")

    # Stage 1: materialise both commits.
    clone = ensure_clone(workdir, args.repo_url, commits=(args.old, args.new))
    if not args.no_prefetch:
        prefetch_range_objects(clone, args.old, args.new, subdir=_SUBDIR)
    wt_old = ensure_worktree(clone, workdir / "wt_old", args.old)
    wt_new = ensure_worktree(clone, workdir / "wt_new", args.new)

    # Stage 2: scan both trees.
    new_decls = scan_tree(wt_new, _SUBDIR)
    old_decls = scan_tree(wt_old, _SUBDIR)
    # The empty-tree hazard of the module docstring: an empty side would make
    # the diff meaningless (an empty OLD tree declares every name new), so it
    # is refused rather than handled.
    if not new_decls:
        raise SystemExit(f"the new tree at {wt_new} yielded zero declarations -- refusing to diff")
    if not old_decls:
        raise SystemExit(f"the old tree at {wt_old} yielded zero declarations -- refusing to diff")
    old_lines = collect_normalised_lines(wt_old, _SUBDIR)
    old_files = {path.relative_to(wt_old).as_posix() for path in _iter_lean_files(wt_old, _SUBDIR)}

    # Stage 3: select, attribute, date.
    kept, counts = select_postcutoff_names(new_decls, old_decls, old_lines, old_files)
    provenance = resolve_provenance(kept, wt_new, clone, args.old, args.new, jobs=args.jobs)

    cache: dict = {}
    if cache_path.is_file():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        LOGGER.info("loaded %d cached PR date(s) from %s", len(cache), cache_path)
    counters: dict = {}
    try:
        selected = apply_pr_filter(provenance, args.target_date, token, cache, counters)
    finally:
        # Written even on failure: the dates already paid for must survive.
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Stage 4: write the artifact.
    artifact = build_artifact(args.old, args.new, args.target_date, counts, selected, kept)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as sink:
        json.dump(artifact, sink, indent=2, sort_keys=True)
        sink.write("\n")

    reasons = {"pr-opened-after-T": 0, "commit-date": 0}
    for entry in selected.values():
        reasons[entry["reason"]] = reasons.get(entry["reason"], 0) + 1
    unresolved = counts["n_after_move"] - len(provenance)

    # The summary is printed, not logged: it is the script's result, and a
    # caller may parse it without depending on logging configuration.
    print(f"postcutoff: old_commit={args.old} new_commit={args.new} target_date={args.target_date}")
    print(f"postcutoff: n_old_decls={counts['n_old_decls']}")
    print(f"postcutoff: n_new_decls={counts['n_new_decls']}")
    print(f"postcutoff: n_name_diff={counts['n_name_diff']}")
    print(f"postcutoff: n_after_deprecated={counts['n_after_deprecated']}")
    print(f"postcutoff: n_after_move={counts['n_after_move']}")
    print(f"postcutoff: n_with_provenance={len(provenance)}")
    print(f"postcutoff: n_postcutoff={len(selected)}")
    print(
        f"postcutoff: reasons pr-opened-after-T={reasons['pr-opened-after-T']} "
        f"commit-date={reasons['commit-date']}"
    )
    print(
        f"postcutoff: dropped pr_before_target={counters.get('dropped_pr_before_target', 0)} "
        f"no_date={counters.get('dropped_no_date', 0)} "
        f"rate_limited={counters.get('rate_limited', 0)} "
        f"unresolved={unresolved}"
    )
    print(f"postcutoff: github_api_calls={counters.get('api_calls', 0)}")
    print(f"postcutoff: wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
