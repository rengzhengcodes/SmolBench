"""Find mathlib4 declarations introduced after a cutoff date.

Names are excluded on ambiguity because this name-only scan cannot elaborate Lean.
Both trees must be non-empty because an empty side reverses that conservative rule.
PR dates, including misses, are cached so reruns need no GitHub requests and remain byte-identical.
``fetch_pr_created_at`` is the module's only network call.
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

#: Stable under file-path loading, where ``__name__`` varies.
LOGGER: logging.Logger = logging.getLogger("postcutoff_names")

#: Column-0 declaration keywords; ``alias`` has separate scanning and ``example`` has no name.
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

#: Prefix modifiers; ``irreducible_def`` must not appear or its name becomes a modifier tail.
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

#: Name-token terminators; closers are absent because a name never starts inside a binder.
_NAME_STOP_CHARS: frozenset[str] = frozenset(":({[⦃⟨<>")

#: ``_root_.Foo`` bypasses the ambient namespace.
_ROOT_PREFIX: str = "_root_."

#: Any ``deprecated`` attribute marks the declaration.
_DEPRECATED_RE: re.Pattern[str] = re.compile(r"\bdeprecated\b")

#: ASCII digits only: ``int()`` accepts non-ASCII digits, which would yield a bogus PR number.
_PR_NUMBER_RE: re.Pattern[str] = re.compile(r"\(#([0-9]+)\)\s*$")

_WHITESPACE_RUN_RE: re.Pattern[str] = re.compile(r"\s+")

#: Four prefix strips exceed real sources' two and bound pathological loops.
_MAX_PREFIX_STRIPS: int = 4

DEFAULT_REPO_URL: str = "https://github.com/leanprover-community/mathlib4"

#: Value of the artifact's ``method`` field.
METHOD: str = "name-set-difference+pr-opened-after-T"

#: Subdirectory of a mathlib4 checkout that holds the library itself.
_SUBDIR: str = "Mathlib"

#: mathlib commit-subject PR numbers only identify this repository.
_PR_API_URL: str = (
    "https://api.github.com/repos/leanprover-community/mathlib4/pulls/{number}"
)

_API_HEADERS: dict[str, str] = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "smolbench-postcutoff",
}

#: Three retries after the initial request, with ``_HTTP_RETRY_SLEEPS`` delays.
_HTTP_RETRIES: int = 3
_HTTP_RETRY_SLEEPS: tuple[float, ...] = (2.0, 4.0, 8.0)

#: Bounds a stalled socket across hundreds of PRs.
_HTTP_TIMEOUT: float = 30.0

#: Generous for cold clones but bounds hangs from lazy blob fetches over dead transports.
_GIT_TIMEOUT: float = 1800.0

#: Lines of git stderr quoted in a :class:`RuntimeError`.
_STDERR_TAIL_LINES: int = 5

#: Matches porcelain headers, not tab-prefixed content or word-keyed headers.
_BLAME_HEADER_RE: re.Pattern[str] = re.compile(
    r"^([0-9a-f]{40}) (?P<orig>[0-9]+) (?P<final>[0-9]+)(?: [0-9]+)?$"
)


class RateLimitError(RuntimeError):
    """GitHub rate-limit response; messages never expose token material."""


@dataclasses.dataclass(frozen=True)
class Decl:
    """A scanned Lean declaration.

    ``statement`` uses the move oracle's normalization so comparisons agree.
    ``alias_targets`` holds alias candidates and is empty otherwise.
    """

    full_name: str
    file_path: str
    line: int
    kind: str
    statement: str
    deprecated: bool
    alias_targets: tuple[str, ...]


def normalise_line(line: str) -> str:
    """Collapse whitespace and strip ends.

    No comment stripping or case folding, so the move heuristic compares like with like.

    Parameters
    ----------
    line : str

    Returns
    -------
    str
        normalised source line.
    """
    return _WHITESPACE_RUN_RE.sub(" ", line).strip()


def _strip_comments(line: str, depth: int) -> tuple[str, int]:
    """Remove comments while carrying nested block-comment depth.

    Mid-line closers lose column-0 status to avoid false declarations.

    Parameters
    ----------
    line : str
    depth : int

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
    """Consume attribute text while tracking bracket balance.

    Parameters
    ----------
    text : str
    balance : int

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
    """Peel leading modifiers from column-0 text.

    A modifier must be a whitespace-delimited word so similarly named declarations survive.
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
    """Read a declaration name after its keyword.

    Empty unnamed declarations must be skipped; universe binders leave a dot for ``_qualify``.

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
    """Apply an ambient namespace prefix.

    Handle ``_root_.`` before stripping a universe-binder dot.

    Parameters
    ----------
    token : str
    prefix : str

    Returns
    -------
    str
        Empty when no name remains; callers must skip it.
    """
    if token.startswith(_ROOT_PREFIX):
        return token[len(_ROOT_PREFIX) :].rstrip(".")
    token = token.rstrip(".")
    if not token:
        return ""
    return f"{prefix}.{token}" if prefix else token


def _alias_targets(text: str, prefix: str) -> tuple[str, ...]:
    """Resolve candidate full names for an ``alias`` target.

    Emit bare and qualified forms because scanning cannot resolve Lean names.
    A multi-line alias with ``:=`` on a later line returns ``()``, so deprecation
    excludes its own name but not its target.

    Parameters
    ----------
    text : str
        alias text following its left-hand side.
    prefix : str

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
    return tuple(dict.fromkeys(candidates))


def _alias_names(text: str) -> tuple[list[str], str]:
    """Split an ``alias`` left-hand side from its remainder.

    Unterminated ``⟨`` produces no names, so the declaration is skipped.

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
    """Scan top-level declarations from one ``.lean`` file without I/O.

    Only column-0 declarations after modifiers or ``open ... in`` are recognized
    to avoid nested terms, even if indented top-level declarations are missed.
    Private declarations are excluded because mangled names cannot match across trees.
    A pending attribute survives skipped declarations; over-marking deprecated is conservative.
    ``namespace``/``section``/``end`` share one unmatched scope stack, so an
    unbalanced file silently drifts, giving later names wrong prefixes and therefore
    wrong post-cutoff verdicts.

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
        deprecated = pending_attr is not None and bool(
            _DEPRECATED_RE.search(pending_attr)
        )
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
    """List ``.lean`` files in deterministic order.

    Shared scans use the same files and order.

    Parameters
    ----------
    root : pathlib.Path
        root of the Lean tree.
    subdir : str

    Returns
    -------
    list[pathlib.Path]
        Empty when absent; ``main`` rejects empty scan sides.
    """
    base = root / subdir if subdir else root
    # Exclude matching directories because callers read every returned path.
    return sorted(path for path in base.rglob("*.lean") if path.is_file())


def _scan_tree_state(
    root: pathlib.Path,
    subdir: str,
) -> tuple[dict[str, Decl], set[str], set[str]]:
    """Collect a Lean tree's declarations, lines, and paths in one pass.

    Parameters
    ----------
    root : pathlib.Path
        Root of the Lean tree.
    subdir : str

    Returns
    -------
    tuple[dict[str, Decl], set[str], set[str]]
        Declarations, normalized lines, and root-relative paths.
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
    """Index declarations from every ``.lean`` file.

    Replacement decoding preserves a repository scan; sorted first occurrence keeps duplicate handling deterministic.

    Parameters
    ----------
    root : pathlib.Path
        root of the Lean tree.
    subdir : str, optional

    Returns
    -------
    dict[str, Decl]
        declarations indexed by full name.
    """
    return _scan_tree_state(root, subdir)[0]


def deprecation_excluded_names(decls: Iterable[Decl]) -> set[str]:
    """Collect names accounted for by deprecations or renames.

    Use the whole new tree because an old deprecated alias can target a diff name.

    Parameters
    ----------
    decls : Iterable[Decl]
        Declarations from the new commit.

    Returns
    -------
    set[str]
        Deprecated names and alias targets; both resolutions are dropped without elaboration.
    """
    excluded: set[str] = set()
    for decl in decls:
        if not decl.deprecated:
            continue
        excluded.add(decl.full_name)
        if decl.kind == "alias":
            # A deprecated alias target is renamed old mathematics, not a new declaration.
            excluded.update(decl.alias_targets)
    return excluded


def parse_pr_number(commit_message: str) -> int | None:
    """Extract a mathlib PR number from the first commit-message line.

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
    """Keep declarations genuinely new between scanned trees.

    Drop deprecated aliases from the whole new tree and moved statements in new files; requiring a new file avoids dropping coincidental duplicates.

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
        Name-sorted declarations and funnel counts.
    """
    diff = {name: decl for name, decl in new_decls.items() if name not in old_decls}

    excluded = deprecation_excluded_names(new_decls.values())
    after_deprecated = {
        name: decl for name, decl in diff.items() if name not in excluded
    }

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


def _run_git(
    args: list[str], cwd: pathlib.Path | None = None
) -> subprocess.CompletedProcess:
    """Run a git command.

    Used for exit-status probes and branches; callers otherwise use ``run_git``'s stdout-or-raise contract.

    Parameters
    ----------
    args : list[str]
    cwd : pathlib.Path | None, optional
        working directory for the command.

    Returns
    -------
    subprocess.CompletedProcess
        completed git process.
    """
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT,
        check=False,
    )


def run_git(
    args: list[str], cwd: pathlib.Path | None = None, check: bool = True
) -> str:
    """Run git and return standard output.

    ``check=False`` means no answer; timeouts remain infrastructure failures. Tokens never reach git arguments.

    Parameters
    ----------
    args : list[str]
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
        tail = " | ".join(
            (proc.stderr or "").strip().splitlines()[-_STDERR_TAIL_LINES:]
        )
        raise RuntimeError(
            f"git {' '.join(args)} failed (exit {proc.returncode}): {tail}"
        )
    return proc.stdout


def _commit_present(clone: pathlib.Path, commit: str) -> bool:
    """Report whether ``commit`` resolves to a commit object inside ``clone``."""
    return (
        _run_git(
            ["-C", str(clone), "cat-file", "-e", f"{commit}^{{commit}}"]
        ).returncode
        == 0
    )


def _ensure_commits_present(clone: pathlib.Path, commits: Iterable[str]) -> None:
    """Fetch commits absent from a clone.

    Recheck after fetch because shallow or partial remotes may refuse fetch-by-sha.

    Parameters
    ----------
    clone : pathlib.Path
        Local clone to inspect and fetch into.
    commits : Iterable[str]
        Commit identifiers to ensure are present.

    Raises
    ------
    RuntimeError
        A commit remains missing after fetch, preventing an empty or wrong diff.
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
    """Return or create a usable clone under ``workdir``.

    Reuse valid clones; blobless history supports blame without ~2 GB of blobs, with one plain-clone fallback for servers rejecting filters.

    Parameters
    ----------
    workdir : pathlib.Path
        directory that holds the local clone.
    repo_url : str, optional
    commits : Iterable[str], optional
        Commit identifiers to ensure are present.

    Returns
    -------
    pathlib.Path
        usable local clone path.
    """
    clone = workdir / "mathlib4"
    preexisting = clone.exists()
    if (
        preexisting
        and run_git(["-C", str(clone), "rev-parse", "--git-dir"], check=False).strip()
    ):
        LOGGER.info("reusing existing clone at %s", clone)
    else:
        workdir.mkdir(parents=True, exist_ok=True)
        filtered = _run_git(
            ["clone", "--filter=blob:none", "--no-checkout", repo_url, str(clone)]
        )
        if filtered.returncode != 0:
            LOGGER.warning(
                "blobless clone failed (exit %d); retrying without --filter",
                filtered.returncode,
            )
            # Never remove a pre-existing operator directory.
            if not preexisting and clone.exists():
                shutil.rmtree(clone)
            run_git(["clone", "--no-checkout", repo_url, str(clone)])
        LOGGER.info("cloned %s into %s", repo_url, clone)
    if commits:
        _ensure_commits_present(clone, commits)
    return clone


def ensure_worktree(
    clone: pathlib.Path, path: pathlib.Path, commit: str
) -> pathlib.Path:
    """Return a worktree checked out at ``commit``.

    Separate worktrees keep old scanning and new blame readable together without races.

    Parameters
    ----------
    clone : pathlib.Path
        local clone that owns the worktree.
    path : pathlib.Path
    commit : str

    Returns
    -------
    pathlib.Path
        worktree checked out at the commit.
    """
    if not path.exists():
        run_git(
            ["-C", str(clone), "worktree", "add", "--detach", "-f", str(path), commit]
        )
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
    """Bulk-fetch objects a blobless clone needs for blame.

    11,548 objects took ~35 s and reduced per-file blame from 4.6 s to 0.24 s. This and ``apply_pr_filter`` alone catch failures because prefetch is only optimization.

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
        Requested object count; zero must not fetch an empty list, which fetches the remote.
    """
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be >= 1, got {chunk_size}")
    requested = 0
    try:
        listing = run_git(
            [
                "-C",
                str(clone),
                "rev-list",
                "--objects",
                "--missing=print",
                f"{old}..{new}",
                "--",
                subdir,
            ]
        )
        # ``--missing=print`` marks absent objects with ``?``.
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
                    "-C",
                    str(clone),
                    "fetch",
                    "--no-tags",
                    "--no-write-fetch-head",
                    "--filter=blob:none",
                    "origin",
                    *chunk,
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


def blame_lines(
    worktree: pathlib.Path, old: str, new: str, file_path: str
) -> dict[int, str]:
    """Attribute file lines to their introducing commits.

    Range blame maps older lines to ``old``, whose date fails the cutoff. Failures yield unresolved drops; timeouts remain infrastructure failures.

    Parameters
    ----------
    worktree : pathlib.Path
        checked-out new tree to blame.
    old : str
    new : str
    file_path : str
        file path relative to the worktree.

    Returns
    -------
    dict[int, str]
        mapping from line numbers to introducing commits.
    """
    out = run_git(
        [
            "-C",
            str(worktree),
            "blame",
            "--line-porcelain",
            f"{old}..{new}",
            "--",
            file_path,
        ],
        check=False,
    )
    blames: dict[int, str] = {}
    for line in out.splitlines():
        match = _BLAME_HEADER_RE.match(line)
        if match:
            blames[int(match.group("final"))] = match.group(1)
    return blames


def _iso_utc(raw: str) -> str:
    """Normalize a git timestamp to UTC.

    GitHub dates are UTC; textual local-time comparison misdates near midnight.

    Parameters
    ----------
    raw : str

    Returns
    -------
    str
        timestamp normalised to UTC.
    """
    moment = datetime.datetime.fromisoformat(raw.strip())
    return moment.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def commit_metadata(clone: pathlib.Path, shas: Iterable[str]) -> dict[str, dict]:
    """Read each commit's date, subject, and PR number.

    A NUL-delimited batch avoids hundreds of processes; validate groups of three because messages contain arbitrary text.

    Parameters
    ----------
    clone : pathlib.Path
    shas : Iterable[str]

    Returns
    -------
    dict[str, dict]
        metadata indexed by commit identifier.
    """
    unique = sorted({sha for sha in shas if sha})
    if not unique:
        return {}
    out = run_git(
        [
            "-C",
            str(clone),
            "log",
            "--no-walk",
            "-z",
            "--format=%H%x00%aI%x00%B",
            *unique,
        ]
    )
    fields = out.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
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
    """Distinguish rate limits from other 403/429 responses.

    GitHub uses 403 for authorization failures too, which must not abort a run.

    Parameters
    ----------
    headers : object
    body : str

    Returns
    -------
    bool
        whether the response indicates rate limiting.
    """
    remaining = (
        headers.get("X-RateLimit-Remaining") if hasattr(headers, "get") else None
    )
    return remaining == "0" or "rate limit" in body.lower()


def fetch_pr_created_at(pr_number: int, token: str | None) -> str | None:
    """Fetch a mathlib pull request's creation time.

    Tokens stay only in Authorization headers, never logs, exceptions, or artifacts. Never retry 404 or rate limits because each is definitive or forbidden.

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
                # Never expose token material.
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
    """Attribute kept declarations to introducing commits.

    Blame by file to share its cost; low concurrency avoids GitHub throttling. Sorted input/output preserves determinism; unresolved lines are dropped, never guessed.

    Parameters
    ----------
    kept : dict[str, Decl]
        declarations retained by the scanner filters.
    worktree : pathlib.Path
        checked-out new tree to blame.
    clone : pathlib.Path
        local clone containing commit history.
    old : str
    new : str
    jobs : int, optional

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
            # Input-order ``map`` prevents completion order leaking into output.
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

    metadata = commit_metadata(
        clone, [entry["introduced_commit"] for entry in provenance.values()]
    )
    for entry in provenance.values():
        meta = metadata.get(entry["introduced_commit"], {})
        entry["author_date"] = meta.get("author_date")
        entry["pr_number"] = meta.get("pr_number")

    if unresolved:
        LOGGER.warning(
            "%d declaration(s) had no blamed line in %s..%s and were dropped",
            unresolved,
            old,
            new,
        )
    return provenance


def apply_pr_filter(
    provenance: dict[str, dict],
    target_date: str,
    token: str | None,
    cache: dict,
    counters: Counter[str],
) -> dict[str, dict]:
    """Keep declarations with post-cutoff date evidence.

    Prefer PR opening, the earliest public date, then commit date if no PR evidence. Cache misses prevent repeat lookup. On rate limit, drop remaining unresolved PRs while retaining cached and completed work.
    This pipeline never emits schema-supported ``reason == "new-name"`` because it demands date evidence.

    Parameters
    ----------
    provenance : dict[str, dict]
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

        # Commit date is fallback when PR evidence is unavailable.
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
            # Both cases lack evidence that the declaration is new.
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
    """Assemble a JSON artifact.

    Exclude wall clock, host, duration, and version so identical commits produce identical artifacts.

    Parameters
    ----------
    old : str
    new : str
    target_date : str
        cutoff date in ISO format.
    counts : dict
        funnel counts from declaration selection.
    selected : dict[str, dict]
    kept : dict[str, Decl]

    Returns
    -------
    dict
        JSON-serializable artifact.
    """
    assert selected.keys() <= kept.keys(), "selected declarations must be retained"
    decls: dict[str, dict] = {}
    for name in sorted(selected):
        entry = selected[name]
        decls[name] = {
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
    parser.add_argument(
        "--old", required=True, help="commit-ish of the OLD (pre-cutoff) tree"
    )
    parser.add_argument("--new", required=True, help="commit-ish of the NEW tree")
    parser.add_argument(
        "--target-date",
        required=True,
        help="cutoff date YYYY-MM-DD; a declaration is kept when its evidence "
        "date is on or after it",
    )
    parser.add_argument(
        "--out", required=True, help="path of the JSON artifact to write"
    )
    parser.add_argument(
        "--workdir",
        required=True,
        help="scratch dir for the clone, worktrees and PR cache",
    )
    parser.add_argument(
        "--repo-url",
        default=DEFAULT_REPO_URL,
        help="remote to clone (default: %(default)s)",
    )
    parser.add_argument(
        "--github-token",
        default=None,
        help="GitHub token; falls back to $GITHUB_ACCESS_TOKEN. Never logged or stored",
    )
    parser.add_argument(
        "--jobs", type=int, default=8, help="parallel blame jobs (default: %(default)s)"
    )
    parser.add_argument(
        "--no-prefetch",
        action="store_true",
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
    """Run the pipeline and write the artifact.

    Always write cached dates so interrupted runs resume; configure logging here to keep imports side-effect-free.

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

    clone = ensure_clone(workdir, args.repo_url, commits=(args.old, args.new))
    if not args.no_prefetch:
        prefetch_range_objects(clone, args.old, args.new, subdir=_SUBDIR)
    wt_old = ensure_worktree(clone, workdir / "wt_old", args.old)
    wt_new = ensure_worktree(clone, workdir / "wt_new", args.new)

    new_decls = scan_tree(wt_new, _SUBDIR)
    old_decls, old_lines, old_files = _scan_tree_state(wt_old, _SUBDIR)
    # Empty sides make the diff meaningless; an empty old tree makes every name look new.
    if not new_decls:
        raise SystemExit(
            f"the new tree at {wt_new} yielded zero declarations -- refusing to diff"
        )
    if not old_decls:
        raise SystemExit(
            f"the old tree at {wt_old} yielded zero declarations -- refusing to diff"
        )

    kept, counts = select_postcutoff_names(new_decls, old_decls, old_lines, old_files)
    provenance = resolve_provenance(
        kept, wt_new, clone, args.old, args.new, jobs=args.jobs
    )

    cache: dict = {}
    if cache_path.is_file():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        LOGGER.info("loaded %d cached PR date(s) from %s", len(cache), cache_path)
    counters: Counter[str] = Counter()
    try:
        selected = apply_pr_filter(provenance, args.target_date, token, cache, counters)
    finally:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    artifact = build_artifact(
        args.old, args.new, args.target_date, counts, selected, kept
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as sink:
        json.dump(artifact, sink, indent=2, sort_keys=True)
        sink.write("\n")

    reasons = {"pr-opened-after-T": 0, "commit-date": 0}
    for entry in selected.values():
        reasons[entry["reason"]] = reasons.get(entry["reason"], 0) + 1
    unresolved = counts["n_after_move"] - len(provenance)

    # Print so callers can parse output independently of logging configuration.
    print(
        f"postcutoff: old_commit={args.old} new_commit={args.new} target_date={args.target_date}"
    )
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
