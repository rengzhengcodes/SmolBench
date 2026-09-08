"""Find mathlib4 declarations that provably appeared after a cutoff date.

Writes the surviving names, with per-declaration provenance, as a JSON
artifact, for pointing a theorem-proving eval at material a model cannot have
memorised.

Name-only heuristic: it never elaborates Lean, so every ambiguity is resolved
toward EXCLUDING a name rather than risking a false post-cutoff claim. An
empty scanned tree would invert that direction (everything in the other tree
would look new), so :func:`main` refuses to run when either side is empty.

PR creation dates are cached in ``<workdir>/cache/prs.json`` (negative results
included), so a re-run over the same commits makes no GitHub requests and
produces a byte-identical artifact. :func:`fetch_pr_created_at` is the only
network call in the module.
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
from collections import Counter
from collections.abc import Iterable

#: Fixed name: the script loads by file path, under which ``__name__`` varies,
#: and a stable name keeps log capture predictable.
LOGGER: logging.Logger = logging.getLogger("postcutoff_names")

#: Declaration keywords recognised at column 0. ``example`` is absent (declares
#: no name); ``alias`` is absent because it has its own scanning rule, though
#: it still appears as a ``Decl.kind``.
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

#: Declaration modifiers skipped before the declaration keyword. A word that is
#: itself a declaration keyword in disguise (``irreducible_def``) must NOT be
#: listed, or its own name token would be read as a modifier's tail.
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

#: Characters that terminate a declaration's name token. Closers are absent on
#: purpose: a name token never starts inside a binder.
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
#: line before giving up. Real sources use at most two; this only guards
#: against a pathological line looping forever.
_MAX_PREFIX_STRIPS: int = 4

DEFAULT_REPO_URL: str = "https://github.com/leanprover-community/mathlib4"

#: Value of the artifact's ``method`` field.
METHOD: str = "name-set-difference+pr-opened-after-T"

#: Subdirectory of a mathlib4 checkout that holds the library itself.
_SUBDIR: str = "Mathlib"

#: GitHub REST endpoint for one pull request. Hardcoded to mathlib4 regardless
#: of ``--repo-url``: the PR numbers in mathlib commit subjects only mean
#: anything against this repository.
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

#: Ceiling on any single git invocation. Generous because a cold mathlib4
#: clone legitimately takes minutes; exists to break a hang (a blobless clone
#: lazily fetching over a dead transport), not to budget a command.
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

    The message names only the PR number and status code -- never token material.
    """


@dataclasses.dataclass(frozen=True)
class Decl:
    """One Lean declaration found by the scanner.

    ``statement`` is the raw source line normalised by :func:`normalise_line`
    (any ``@[simp] ``/``open ... in `` prefix and trailing comment included),
    so it compares like with like against :func:`collect_normalised_lines`'s
    move-heuristic oracle. ``alias_targets`` holds the alias's resolved
    candidate targets for ``kind == "alias"`` and is empty otherwise.
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

    No comment stripping or case folding. Feeds both :attr:`Decl.statement` and
    :func:`collect_normalised_lines`, so the move heuristic in
    :func:`select_postcutoff_names` compares like with like.

    Parameters
    ----------
    line : str
        source line to normalise.

    Returns
    -------
    str
        normalised source line.
    """
    return _WHITESPACE_RUN_RE.sub(" ", line).strip()


def _strip_comments(line: str, depth: int) -> tuple[str, int]:
    """Remove Lean comments from one line, carrying block-comment depth.

    Block comments nest (hence a depth counter, not a flag); doc comments
    ``/-- ... -/`` are just block comments here. Text after a block comment
    closes mid-line loses column-0 status by design: ``/- x -/ theorem foo``
    then declares nothing. That's the conservative direction, and mathlib
    doesn't write declarations that way regardless.

    Parameters
    ----------
    line : str
        source line to process.
    depth : int
        current nested block-comment depth.

    Returns
    -------
    tuple[str, int]
        uncommented text and remaining block-comment depth.
    """
    out: list[str] = []
    i = 0
    n = len(line)
    while i < n:
        pair = line[i : i + 2]
        if depth > 0:
            # `--` is inert inside a block comment; only the nesting markers matter here.
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
            # Known approximation: also fires for `--` inside a string literal.
            break
        else:
            out.append(line[i])
            i += 1
    return "".join(out), depth


def _consume_attribute(text: str, balance: int) -> tuple[str, int, str]:
    """Consume attribute-block characters from ``text``, tracking bracket balance.

    Parameters
    ----------
    text : str
        attribute-block text to consume.
    balance : int
        current open-bracket balance.

    Returns
    -------
    tuple[str, int, str]
        the consumed text, the balance still open (0 once the block closes), and the
        remainder after the closing bracket (empty while still open).
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

    A modifier counts only as a whole word followed by whitespace, so a
    declaration named like a modifier isn't consumed. Feeds both the
    declaration and scope-keyword branches of the scanner, since
    ``noncomputable section`` must still push a scope.

    Parameters
    ----------
    text : str
        column-0 declaration or scope text.

    Returns
    -------
    tuple[list[str], str]
        modifiers and remaining text.
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
    """Read a declaration's name token off the text after its keyword.

    Runs to the first whitespace or member of :data:`_NAME_STOP_CHARS`. Empty
    means the declaration is unnamed (``instance : Foo Bar where``) and must be
    skipped. A universe binder leaves a trailing dot (``def foo.{u}`` gives
    ``foo.``), which :func:`_qualify` strips.

    Parameters
    ----------
    text : str
        text following a declaration keyword.

    Returns
    -------
    str
        declaration name token.
    """
    for i, ch in enumerate(text):
        if ch.isspace() or ch in _NAME_STOP_CHARS:
            return text[:i]
    return text


def _qualify(token: str, prefix: str) -> str:
    """Apply the ambient namespace prefix to a declared name token.

    ``_root_.`` is
    honoured before the trailing-dot strip, so its dot is never mistaken for a
    universe binder's (``def foo.{u}`` reads as ``foo.``).

    Parameters
    ----------
    token : str
        declared name token.
    prefix : str
        ambient namespace prefix.

    Returns
    -------
    str
        ``""`` when the token carries no name at all (empty, a bare ``_root_.``, or all
        dots), which the caller must skip.
    """
    if token.startswith(_ROOT_PREFIX):
        return token[len(_ROOT_PREFIX) :].rstrip(".")
    token = token.rstrip(".")
    if not token:
        return ""
    return f"{prefix}.{token}" if prefix else token


def _alias_targets(text: str, prefix: str) -> tuple[str, ...]:
    """Resolve an ``alias``'s right-hand side into candidate full names.

    Emits both the bare token and, when a namespace is in force, its qualified
    form, since only elaboration (not this scanner) can tell which one Lean
    would resolve. A multi-line alias whose ``:=`` is on a later line resolves
    to ``()`` here, so a deprecated multi-line alias excludes its own name but
    not its target.

    Parameters
    ----------
    text : str
        alias text following its left-hand side.
    prefix : str
        ambient namespace prefix.

    Returns
    -------
    tuple[str, ...]
        candidate full names for the alias target.
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

    Handles plain ``alias X := Y`` and the iff-splitting forms
    ``alias ⟨X, Y⟩ := Z`` / ``alias ⟨_, X⟩ := Z``. An unterminated ``⟨`` yields
    no names, skipping the declaration.

    Parameters
    ----------
    text : str
        alias text following the keyword.

    Returns
    -------
    tuple[list[str], str]
        alias names and remaining text.
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

    Line-oriented and stateful across lines (comment depth, a namespace/section
    scope stack, a pending ``@[...]`` attribute block); performs no I/O.
    Declarations are recognised only at column 0, after optional modifiers and
    an optional ``open ... in`` prefix -- this is what keeps
    ``have``/``let``/``where``-fields and nested proof terms from being read as
    declarations, at the cost of missing an indented top-level one.
    ``namespace``/``section``/``end`` share one scope stack with no name
    matching on ``end``, so an unbalanced file silently drifts. A pending
    attribute is not cleared by a skipped (private or unnamed) declaration, so
    it may attach to a later one; over-marking ``deprecated`` is the safe
    direction. ``private`` declarations produce no :class:`Decl` at all, since
    Lean mangles their real full names and a mangled name could never match
    across two trees.

    Parameters
    ----------
    text : str
        contents of a Lean source file.
    file_path : str
        path recorded on emitted declarations.

    Returns
    -------
    list[Decl]
        top-level declarations found in the source text.
    """
    decls: list[Decl] = []
    scopes: list[str | None] = []
    comment_depth = 0
    pending_attr: str | None = None
    attr_balance = 0

    for index, raw_line in enumerate(text.splitlines()):
        lineno = index + 1
        code, comment_depth = _strip_comments(raw_line, comment_depth)

        if attr_balance > 0:
            consumed, attr_balance, remainder = _consume_attribute(code, attr_balance)
            pending_attr = f"{pending_attr or ''} {consumed}"
            if attr_balance > 0:
                continue
            candidate = remainder.strip()
        else:
            if not raw_line.strip():
                # Blank is judged on the raw line, so a comment-only line does
                # not detach a pending attribute.
                pending_attr = None
                continue
            if not code.strip() or code[:1].isspace():
                continue
            candidate = code.strip()

        # Peel any `@[...]` / `open ... in` prefixes, in either order,
        # re-treating what's left as column-0 text each pass.
        for _ in range(_MAX_PREFIX_STRIPS):
            if candidate.startswith("@["):
                consumed, attr_balance, remainder = _consume_attribute(candidate, 0)
                pending_attr = f"{pending_attr or ''} {consumed}"
                candidate = "" if attr_balance > 0 else remainder.strip()
                continue
            if candidate.startswith("open "):
                trimmed = candidate.rstrip()
                if trimmed.endswith(" in"):
                    # Declaration is on the next line.
                    candidate = ""
                    break
                marker = trimmed.find(" in ")
                if marker == -1:
                    # Plain `open Foo`: affects resolution, not names.
                    candidate = ""
                    break
                candidate = trimmed[marker + 4 :].strip()
                continue
            break
        if not candidate:
            continue

        # Modifiers peeled first so `noncomputable section` still pushes a scope.
        modifiers, rest = _strip_modifiers(candidate)
        parts = rest.split(None, 1)
        head = parts[0] if parts else ""
        tail = parts[1] if len(parts) == 2 else ""

        if head == "namespace":
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
            # No Decl at all: Lean mangles the real name. The pending attribute survives.
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
            # Unnamed declaration (e.g. `instance : Foo Bar where`): skipped entirely.
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
    """List the ``.lean`` files of a tree in a deterministic (sorted) order.

    Shared by :func:`scan_tree` and :func:`collect_normalised_lines` so both
    see exactly the same files in the same order.

    Parameters
    ----------
    root : pathlib.Path
        root of the Lean tree.
    subdir : str
        subdirectory to scan.

    Returns
    -------
    list[pathlib.Path]
        ``[]`` when the directory is absent -- an empty side inverts the module's
        conservative direction; see :func:`main`.
    """
    base = root / subdir if subdir else root
    # A directory named `*.lean` would make callers' `read_text` raise; filter it here.
    return sorted(path for path in base.rglob("*.lean") if path.is_file())


def _scan_tree_state(
    root: pathlib.Path, subdir: str,
) -> tuple[dict[str, Decl], set[str], set[str]]:
    """Read a Lean tree once and collect declarations, lines, and paths.

    Combining these products avoids three full walks of the old mathlib tree.

    Parameters
    ----------
    root : pathlib.Path
        Root of the Lean tree.
    subdir : str
        Subdirectory containing Lean files.

    Returns
    -------
    tuple[dict[str, Decl], set[str], set[str]]
        Declarations, normalized non-empty lines, and root-relative file paths.
    """
    decls: dict[str, Decl] = {}
    lines: set[str] = set()
    files: set[str] = set()
    for path in _iter_lean_files(root, subdir):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()
        files.add(rel)
        for decl in scan_lean_text(text, rel):
            decls.setdefault(decl.full_name, decl)
        lines.update(filter(None, (normalise_line(line) for line in text.splitlines())))
    return decls, lines, files


def scan_tree(root: pathlib.Path, subdir: str = "Mathlib") -> dict[str, Decl]:
    """Scan every ``.lean`` file of a tree and index declarations by full name.

    Files are read with ``errors="replace"``: a decoding error should degrade
    one line, not abort a whole-repository scan. On a duplicate full name the
    first occurrence (sorted-file, source order) wins, which only matters for
    making the result independent of filesystem iteration order -- mathlib
    itself never defines the same name twice.

    Parameters
    ----------
    root : pathlib.Path
        root of the Lean tree.
    subdir : str, optional
        subdirectory containing Lean files.

    Returns
    -------
    dict[str, Decl]
        declarations indexed by full name.
    """
    return _scan_tree_state(root, subdir)[0]


def collect_normalised_lines(root: pathlib.Path, subdir: str = "Mathlib") -> set[str]:
    """Collect every non-empty normalised source line of a tree.

    This is the "did this exact text already exist at the old commit" oracle
    for :func:`select_postcutoff_names`'s move heuristic. Includes ALL lines,
    not just declaration lines, since a broader set matches more statements
    and excludes more names -- the conservative direction.

    Mathlib is roughly 1.5 million lines, so the returned set holds on the
    order of a million short strings (a few hundred MB); accepted because the
    alternative (re-reading the old tree per candidate) is orders of magnitude
    slower and the script runs once, offline.

    Parameters
    ----------
    root : pathlib.Path
        root of the Lean tree.
    subdir : str, optional
        subdirectory containing Lean files.

    Returns
    -------
    set[str]
        non-empty normalised source lines.
    """
    return _scan_tree_state(root, subdir)[1]


def deprecation_excluded_names(decls: Iterable[Decl]) -> set[str]:
    """Collect the names a deprecation or rename accounts for.

    Pass the NEW commit's whole declaration set, not just the diff: a
    deprecated alias outside the diff can still name a target inside it.

    Parameters
    ----------
    decls : Iterable[Decl]
        Declarations from the new commit.

    Returns
    -------
    set[str]
        Every deprecated declaration's name plus every ``alias_targets`` entry of a
        deprecated alias -- both candidate resolutions are dropped, since which one
        Lean means needs elaboration.
    """
    excluded: set[str] = set()
    for decl in decls:
        if not decl.deprecated:
            continue
        excluded.add(decl.full_name)
        if decl.kind == "alias":
            # mathlib's rename pattern is "new decl `Bar.baz` + `@[deprecated]
            # alias Foo.foo := Bar.baz`": a deprecated alias's target is the
            # renamed OLD theorem wearing a new name, not new mathematics.
            excluded.update(decl.alias_targets)
    return excluded


def parse_pr_number(commit_message: str) -> int | None:
    """Extract the mathlib PR number from a commit message.

    mathlib's merge queue appends ``(#NNNNN)`` to the first line only; a match
    elsewhere in the message, or a non-numeric body, yields ``None``.

    Parameters
    ----------
    commit_message : str
        git commit message to inspect.

    Returns
    -------
    int | None
        PR number from the first line, if present.
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

    Pure; runs three filters in order: (1) name-set difference against
    ``old_decls``; (2) drop anything :func:`deprecation_excluded_names` names,
    fed the WHOLE new tree so a deprecated alias whose own name is old can
    still exclude its target; (3) drop a declaration when its file is new AND
    its statement text already existed somewhere in the old tree -- the
    signature of material moved into a new file, which is how mathlib actually
    relocates declarations. Requiring a new file (not just a matching line)
    keeps a genuinely new declaration from being dropped for coincidentally
    duplicating a line in its own unchanged file.

    Parameters
    ----------
    new_decls : dict[str, Decl]
        declarations from the new tree.
    old_decls : dict[str, Decl]
        declarations from the old tree.
    old_lines : set[str]
        normalised source lines from the old tree.
    old_files : set[str]
        Lean file paths from the old tree.

    Returns
    -------
    tuple[dict[str, Decl], dict[str, int]]
        the kept declarations (sorted by name) and the funnel counts ``n_old_decls``,
        ``n_new_decls``, ``n_name_diff``, ``n_after_deprecated``, ``n_after_move``.
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

    Private: callers normally want :func:`run_git`'s stdout-or-raise contract.
    The exceptions are presence probes (``git cat-file -e`` only has an exit
    code to check) and steps that must branch on the exit code themselves.

    Parameters
    ----------
    args : list[str]
        git command arguments.
    cwd : pathlib.Path | None, optional
        working directory for the command.

    Returns
    -------
    subprocess.CompletedProcess
        completed git process.
    """
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=_GIT_TIMEOUT
    )


def run_git(args: list[str], cwd: pathlib.Path | None = None, check: bool = True) -> str:
    """Run one git command and return its standard output.

    With ``check=False`` a failing command returns ``""``, which callers treat
    as "no answer". A hung transport raises `subprocess.TimeoutExpired` after
    :data:`_GIT_TIMEOUT` seconds regardless of ``check``: it's an
    infrastructure failure, not an unresolved declaration. The GitHub token is
    never passed to git, so no argument list here can leak it.

    Parameters
    ----------
    args : list[str]
        git command arguments.
    cwd : pathlib.Path | None, optional
        working directory for the command.
    check : bool, optional
        whether a nonzero exit status raises an error.

    Returns
    -------
    str
        standard output from the command.
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

    The fetch itself is judged by exit code, not exception, since a shallow or
    partial remote may legitimately refuse a fetch-by-sha; only the re-check decides.

    Parameters
    ----------
    clone : pathlib.Path
        Local clone to inspect and fetch into.
    commits : Iterable[str]
        Commit identifiers to ensure are present.

    Raises
    ------
    RuntimeError
        If a commit is still missing after the fetch, rather than let a missing
        endpoint silently turn into an empty or wrong diff.
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

    An existing clone (``git rev-parse --git-dir`` succeeds) is reused
    untouched -- cloning mathlib4 costs minutes and the script is meant to be
    re-run against a pre-warmed clone. The clone is ``--filter=blob:none
    --no-checkout``: history and trees are needed for blame, not the ~2 GB of
    file blobs, which worktrees fetch lazily as needed. Some servers reject an
    object filter, so a failed filtered clone falls back to one plain-clone
    attempt.

    Parameters
    ----------
    workdir : pathlib.Path
        directory that holds the local clone.
    repo_url : str, optional
        remote repository URL.
    commits : Iterable[str], optional
        Commit identifiers to ensure are present.

    Returns
    -------
    pathlib.Path
        usable local clone path.
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
            # Remove only what this call created; a pre-existing directory is
            # the operator's, not ours.
            if not preexisting and clone.exists():
                shutil.rmtree(clone)
            run_git(["clone", "--no-checkout", repo_url, str(clone)])
        LOGGER.info("cloned %s into %s", repo_url, clone)
    if commits:
        _ensure_commits_present(clone, commits)
    return clone


def ensure_worktree(clone: pathlib.Path, path: pathlib.Path, commit: str) -> pathlib.Path:
    """Return a worktree of ``clone`` checked out at ``commit``.

    Worktrees rather than repeated checkouts in one tree, since the old and
    new commits must be readable at the same time (the scanner reads old while
    blame reads new); swapping one checkout back and forth would be slower and
    racy. A worktree already at ``commit`` is left alone, which is what makes a
    re-run cheap.

    Parameters
    ----------
    clone : pathlib.Path
        local clone that owns the worktree.
    path : pathlib.Path
        desired worktree path.
    commit : str
        commit to check out.

    Returns
    -------
    pathlib.Path
        worktree checked out at the commit.
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

    Pure optimisation: without it, ``git blame`` fetches each missing blob
    lazily over its own connection. Measured on real mathlib: 11548 missing
    objects, ~35 s to prefetch, turning a 4.6 s per-file blame into 0.24 s.
    This is the one place besides :func:`apply_pr_filter` that catches and
    swallows a failure (logged as a warning; the run continues with lazy
    fetching), since it is pure performance and nothing else here may degrade
    silently.

    Parameters
    ----------
    clone : pathlib.Path
        blobless clone to fetch into.
    old : str
        older commit in the range.
    new : str
        newer commit in the range.
    subdir : str, optional
        subdirectory whose objects are needed.
    chunk_size : int, optional
        maximum object identifiers per fetch.

    Returns
    -------
    int
        0 without calling ``git fetch`` when nothing is missing, since an empty object list
        would otherwise fetch the entire remote.
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
        # `--missing=print` marks each absent object with a leading `?`.
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

    Bounding blame to ``old..new`` is what makes this both affordable and
    correct: only commits in the range are considered, so every older line
    comes back attributed to the boundary commit ``old`` itself, whose author
    date is at or before the old commit's and therefore rejected by the date
    filter. A git failure returns ``{}`` rather than raising, so the affected
    declarations are simply dropped as unresolved; a `TimeoutExpired` still
    propagates, since a hung git is an infrastructure fault, not "no such line".

    Parameters
    ----------
    worktree : pathlib.Path
        checked-out new tree to blame.
    old : str
        older commit boundary.
    new : str
        newer commit boundary.
    file_path : str
        file path relative to the worktree.

    Returns
    -------
    dict[int, str]
        mapping from line numbers to introducing commits.
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

    Author dates are compared against GitHub's ``created_at``, which is always
    UTC with a ``Z``; comparing a ``+02:00`` local timestamp as text would
    misdate commits near midnight.

    Parameters
    ----------
    raw : str
        git author timestamp.

    Returns
    -------
    str
        timestamp normalised to UTC.
    """
    moment = datetime.datetime.fromisoformat(raw.strip())
    return moment.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def commit_metadata(clone: pathlib.Path, shas: Iterable[str]) -> dict[str, dict]:
    """Read the date, subject and PR number of each of ``shas``.

    One batched ``git log --no-walk -z --format=%H%x00%aI%x00%B`` call rather
    than one per sha, since a run resolves hundreds of commits and process
    startup would dominate. ``-z`` plus the two ``%x00`` separators make the
    stream split into groups of three regardless of message contents; the
    record count is validated rather than assumed.

    Parameters
    ----------
    clone : pathlib.Path
        local clone to query.
    shas : Iterable[str]
        commit identifiers to inspect.

    Returns
    -------
    dict[str, dict]
        metadata indexed by commit identifier.
    """
    unique = sorted({sha for sha in shas if sha})
    if not unique:
        return {}
    out = run_git(["-C", str(clone), "log", "--no-walk", "-z", "--format=%H%x00%aI%x00%B", *unique])
    fields = out.split("\0")
    if fields and fields[-1] == "":
        fields.pop()  # trailing separator
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

    GitHub uses 403 for both rate limiting and plain authorisation failures,
    so the two must be told apart before a whole run is abandoned.

    Parameters
    ----------
    headers : object
        HTTP response headers.
    body : str
        HTTP response body.

    Returns
    -------
    bool
        whether the response indicates rate limiting.
    """
    remaining = headers.get("X-RateLimit-Remaining") if hasattr(headers, "get") else None
    return remaining == "0" or "rate limit" in body.lower()


def fetch_pr_created_at(pr_number: int, token: str | None) -> str | None:
    """Ask the GitHub API when a mathlib pull request was opened.

    The only function in the module that touches the network, so a caller that
    stubs it out makes the whole script offline. The token goes into the
    ``Authorization`` header only -- never logged, never in an exception
    message, never written to the artifact. A 404 is a definitive answer and
    is never retried; a rate limit is never retried either, since retrying is
    exactly what it forbids.

    Parameters
    ----------
    pr_number : int
        pull request number to query.
    token : str | None
        GitHub token for the Authorization header.

    Returns
    -------
    str | None
        pull request creation timestamp, if available.
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

    Blames one FILE at a time, not one declaration at a time, since several
    declarations usually share a file and blame's cost is per file. ``jobs``
    defaults low because more concurrent blob fetches against GitHub invite
    abuse throttling. Deterministic despite threading: files are blamed in
    sorted order, results are collected in input (not completion) order, and
    the output is built by sorted name. Declarations with no blamed line are
    omitted and counted, never guessed at.

    Parameters
    ----------
    kept : dict[str, Decl]
        declarations retained by the scanner filters.
    worktree : pathlib.Path
        checked-out new tree to blame.
    clone : pathlib.Path
        local clone containing commit history.
    old : str
        older commit boundary.
    new : str
        newer commit boundary.
    jobs : int, optional
        maximum concurrent blame jobs.

    Returns
    -------
    dict[str, dict]
        provenance records indexed by declaration name.
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


def apply_pr_filter(
    provenance: dict[str, dict],
    target_date: str,
    token: str | None,
    cache: dict,
    counters: Counter[str],
) -> dict[str, dict]:
    """Keep only the declarations with dated evidence of being post-cutoff.

    Prefers the PR's creation date (a mathlib PR is opened before it merges,
    so that's the earliest defensible moment the text could have been public)
    over the introducing commit's own author date, used only when no PR number
    was found or the PR no longer exists. ``cache`` is read and written in
    place, including negative results, so a re-run never re-asks about a
    deleted PR. On :class:`RateLimitError`, stops calling the API and drops
    every remaining PR-numbered entry unresolved rather than raising, so work
    already done is not thrown away; cached dates are still used since reading
    the cache is not a request.

    The artifact schema also allows ``reason == "new-name"``, for a
    declaration kept on name-newness alone. This pipeline always demands date
    evidence, so it never emits that value -- it exists for a caller that
    relaxes the rule.

    Parameters
    ----------
    provenance : dict[str, dict]
        provenance records to filter.
    target_date : str
        cutoff date in ISO format.
    token : str | None
        GitHub token for pull request lookups.
    cache : dict
        pull request creation dates, updated in place.
    counters : Counter[str]
        pipeline counters, updated in place.

    Returns
    -------
    dict[str, dict]
        declarations with post-cutoff date evidence.
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
                counters["rate_limited"] += 1
                continue
            else:
                counters["api_calls"] += 1
                try:
                    created_at = fetch_pr_created_at(pr_number, token)
                except RateLimitError as exc:
                    rate_limited = True
                    LOGGER.warning(
                        "%s: %d name(s) already kept, remaining PR lookups are dropped unresolved",
                        exc,
                        len(selected),
                    )
                    counters["rate_limited"] += 1
                    continue
                cache[key] = created_at

        if created_at is not None:
            if created_at[:10] >= target_date:
                counters["kept_pr"] += 1
                selected[name] = {
                    "file_path": entry["file_path"],
                    "introduced_commit": entry["introduced_commit"],
                    "pr_number": pr_number,
                    "pr_created_at": created_at,
                    "reason": "pr-opened-after-T",
                }
            else:
                counters["dropped_pr_before_target"] += 1
            continue

        # No usable PR evidence: fall back to the introducing commit's own date.
        author_date = entry.get("author_date")
        if author_date is not None and author_date[:10] >= target_date:
            counters["kept_commit_date"] += 1
            selected[name] = {
                "file_path": entry["file_path"],
                "introduced_commit": entry["introduced_commit"],
                "pr_number": None,
                "pr_created_at": None,
                "reason": "commit-date",
            }
        else:
            # One counter for both commit-date failures: no author date and an
            # author date before the target both mean no evidence the declaration is new.
            counters["dropped_no_date"] += 1
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

    No wall clock, hostname, duration or tool version is included, so two runs
    over the same commits are byte-identical and a re-run can be diffed
    against its predecessor to prove nothing moved.

    Parameters
    ----------
    old : str
        older commit identifier.
    new : str
        newer commit identifier.
    target_date : str
        cutoff date in ISO format.
    counts : dict
        funnel counts from declaration selection.
    selected : dict[str, dict]
        selected provenance records.
    kept : dict[str, Decl]
        retained declaration records.

    Returns
    -------
    dict
        JSON-serializable artifact.
    """
    decls: dict[str, dict] = {}
    for name in sorted(selected):
        entry = selected[name]
        decls[name] = {
            # ``kept`` is the authoritative declaration record; every selected
            # name is guaranteed to be present there.
            "file_path": kept[name].file_path,
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
    """Define and parse the command line."""
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

    The PR cache is written in a ``finally``, so a run stopped by a rate limit
    or an exception still keeps every date already paid for, and the next run
    resumes from there. Logging is configured here, not at import, so
    importing this module stays free of side effects.

    Parameters
    ----------
    argv : list[str] | None, optional
        command-line arguments excluding the program name.

    Returns
    -------
    int
        process exit status.
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
    old_decls, old_lines, old_files = _scan_tree_state(wt_old, _SUBDIR)
    # An empty side would make the diff meaningless (empty OLD tree => every
    # name looks new); refuse rather than handle it.
    if not new_decls:
        raise SystemExit(f"the new tree at {wt_new} yielded zero declarations -- refusing to diff")
    if not old_decls:
        raise SystemExit(f"the old tree at {wt_old} yielded zero declarations -- refusing to diff")

    # Stage 3: select, attribute, date.
    kept, counts = select_postcutoff_names(new_decls, old_decls, old_lines, old_files)
    provenance = resolve_provenance(kept, wt_new, clone, args.old, args.new, jobs=args.jobs)

    cache: dict = {}
    if cache_path.is_file():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        LOGGER.info("loaded %d cached PR date(s) from %s", len(cache), cache_path)
    counters: Counter[str] = Counter()
    try:
        selected = apply_pr_filter(provenance, args.target_date, token, cache, counters)
    finally:
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

    # Printed, not logged, so a caller can parse the result without depending
    # on logging config.
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
