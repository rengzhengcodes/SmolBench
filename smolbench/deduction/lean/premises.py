"""Look up traced Lean premises and their source text.

`body_with_proof` slices source through the next declaration so theorem proofs
survive the signature-only corpus record.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .corpus import data_root, metadata


@dataclass(frozen=True)
class Premise:
    """A declaration in the traced repository."""

    #: Fully-qualified declaration name.
    full_name: str
    #: Corpus source text.
    code: str
    #: 1-indexed start ``(line, column)``.
    start: tuple[int, int]
    #: End ``(line, column)``.
    end: tuple[int, int]
    #: Corpus declaration kind.
    kind: str
    #: Corpus-relative source path.
    file_path: str


@lru_cache(maxsize=1)
def _index() -> dict[str, Premise]:
    """Load the ~5s cached ``corpus.jsonl`` index."""
    path = data_root() / "corpus.jsonl"
    idx: dict[str, Premise] = {}
    with path.open() as f:
        for line in f:
            rec = json.loads(line)
            for p in rec["premises"]:
                fn = p["full_name"]
                # Keep the first collision.
                if fn in idx:
                    continue
                idx[fn] = Premise(
                    full_name=fn,
                    code=p["code"],
                    start=tuple(p["start"]),  # type: ignore[arg-type]
                    end=tuple(p["end"]),      # type: ignore[arg-type]
                    kind=p["kind"],
                    file_path=rec["path"],
                )
    return idx


def lookup(full_name: str) -> Premise | None:
    """Look up a premise by full name.

    Absence renders as a placeholder rather than an error.

    Parameters
    ----------
    full_name : str
        Premise name.

    Returns
    -------
    Premise | None
        Matching premise, if present.
    """
    return _index().get(full_name)


def signature(p: Premise) -> str:
    """Return source through the first top-level ``:=``.

    Ignore bracketed ``:=`` so attributes do not truncate declarations.

    Parameters
    ----------
    p : Premise
        Premise to parse.

    Returns
    -------
    str
        Rstripped signature.
    """
    s = p.code
    depth = 0
    i = 0
    while i < len(s):
        c = s[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif depth == 0 and c == ":" and i + 1 < len(s) and s[i + 1] == "=":
            return s[:i].rstrip()
        i += 1
    return s.rstrip()


_TOP_LEVEL_RE = re.compile(
    r"^(?:@\[|"
    r"theorem\s|lemma\s|def\s|instance\s|structure\s|inductive\s|"
    r"axiom\s|example\s|class\s|abbrev\s|"
    r"noncomputable\s|private\s|protected\s|partial\s|mutual\s|"
    r"section\s|namespace\s|end\s|end$|"
    r"variable\s|variables\s|"
    r"open\s|import\s|"
    r"syntax\s|macro\s|elab\s|"
    r"deriving\s|attribute\s|set_option\s|"
    r"#)"
)


@lru_cache(maxsize=1)
def _traced_root() -> Path | None:
    """Return the cached repository matching the corpus commit.

    Match the commit to avoid silently slicing another trace; missing source is
    optional, so return ``None`` while other failures surface; only
    `FileNotFoundError` and `KeyError` are caught. Call
    `corpus.reset_caches` after changing ``SMOLBENCH_LEAN_DATA`` mid-process.
    The matching directory is
    ``~/.cache/lean_dojo/leanprover-community-mathlib4-{commit}/mathlib4``.
    """
    try:
        commit = metadata()["from_repo"]["commit"]
    except (FileNotFoundError, KeyError):
        return None
    cache = Path.home() / ".cache" / "lean_dojo"
    candidate = cache / f"leanprover-community-mathlib4-{commit}" / "mathlib4"
    return candidate if candidate.is_dir() else None


def _resolve_source(file_path: str) -> Path | None:
    """Resolve a corpus path in the traced repository.

    Parameters
    ----------
    file_path : str
        Corpus-relative path.

    Returns
    -------
    Path | None
        Source path, if present.
    """
    root = _traced_root()
    if root is None:
        return None
    candidate = root / file_path
    return candidate if candidate.exists() else None


@lru_cache(maxsize=8192)
def slice_full_decl(file_path: str, start_line: int, end_line: int, max_lines: int = 200) -> str:
    """Slice a declaration and proof from source.

    Stop at the next top-level declaration, ``max_lines``, or EOF.

    Parameters
    ----------
    file_path : str
        Corpus-relative path.
    start_line : int
        1-indexed start line.
    end_line : int
        1-indexed end line.
    max_lines : int, optional
        Maximum slice length.

    Returns
    -------
    str
        Rstripped slice, if source exists.
    """
    src = _resolve_source(file_path)
    if src is None:
        return ""
    lines = src.read_text().splitlines()
    s = max(0, start_line - 1)
    if s >= len(lines):
        return ""
    search_from = max(s + 1, end_line)
    cap = min(s + max_lines, len(lines))
    for i in range(search_from, cap):
        if _TOP_LEVEL_RE.match(lines[i]):
            return "\n".join(lines[s:i]).rstrip()
    return "\n".join(lines[s:cap]).rstrip()


def body_with_proof(p: Premise) -> str:
    """Return a full declaration or its corpus fallback.

    Parameters
    ----------
    p : Premise
        Premise to retrieve.

    Returns
    -------
    str
        Declaration text.
    """
    sliced = slice_full_decl(p.file_path, p.start[0], p.end[0])
    return sliced or p.code


def has_full_source(p: Premise) -> bool:
    """Whether a traced-source slice is available.

    A corpus ``code`` field can include a proof, so text alone cannot identify
    a slice; `context._render_hint_parts` needs this distinction. Keep
    `body_with_proof` returning usable text for its callers; the second slice
    call is cheap because `slice_full_decl` is cached.

    Parameters
    ----------
    p : Premise
        Premise to check.

    Returns
    -------
    bool
        Whether traced source was sliced.
    """
    return bool(slice_full_decl(p.file_path, p.start[0], p.end[0]))


# ASCII identifiers match corpus full names.
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_'.]*")

#: Excluded Lean tokens; frozen because every identifier checks membership.
_LEAN_NOISE: frozenset[str] = frozenset({
    "theorem", "lemma", "def", "instance", "structure", "inductive",
    "axiom", "example", "class", "abbrev", "fun", "let", "in", "do",
    "if", "then", "else", "match", "with", "by", "have", "show", "this",
    "true", "True", "false", "False", "Type", "Prop", "Sort", "Set",
    "namespace", "open", "import", "section", "end", "variable", "variables",
    "where", "macro", "syntax", "elab", "deriving", "attribute", "set_option",
    "noncomputable", "private", "protected", "partial", "mutual",
    "rw", "rewrite", "simp", "exact", "apply", "intro", "intros", "rintro",
    "cases", "rcases", "obtain", "use", "constructor", "refine", "refine'",
    "split", "and", "or", "not", "iff", "exists", "forall", "all_goals",
    "any_goals", "tauto", "ring", "field_simp", "linarith", "nlinarith",
    "omega", "decide", "rfl", "trivial", "assumption", "id", "le", "lt",
    "ge", "gt", "eq", "ne", "of", "to", "from", "h1", "h2", "h3",
})


@lru_cache(maxsize=1)
def _short_name_index() -> dict[str, list[str]]:
    """Index full names by final segment for bare-name references."""
    out: dict[str, list[str]] = {}
    for full in _index().keys():
        short = full.rsplit(".", 1)[-1]
        out.setdefault(short, []).append(full)
    return out


@lru_cache(maxsize=4096)
def referenced_premises(full_name: str) -> tuple[Premise, ...]:
    """Find references in a premise body.

    Prefer exact full names; bare names resolve only when unambiguous. Tuples
    keep cached results hashable.

    Parameters
    ----------
    full_name : str
        Premise name.

    Returns
    -------
    tuple[Premise, ...]
        Referenced premises.
    """
    p = lookup(full_name)
    if p is None:
        return ()
    text = body_with_proof(p)
    if not text:
        text = p.code  # fallback: corpus signature

    idx = _index()
    short_idx = _short_name_index()

    seen: set[str] = {full_name}
    out: list[Premise] = []
    for tok in _IDENT_RE.findall(text):
        if tok in _LEAN_NOISE or len(tok) <= 1:
            continue
        if tok in idx and tok not in seen:
            seen.add(tok)
            out.append(idx[tok])
            continue
        if "." not in tok:
            cands = short_idx.get(tok)
            if cands and len(cands) == 1 and cands[0] not in seen:
                seen.add(cands[0])
                out.append(idx[cands[0]])
    return tuple(out)


def premise_dep_closure(
    seeds: list[Premise], depth: int, max_premises: int = 500,
) -> list[Premise]:
    """Return a breadth-first premise closure.

    Excludes seeds; order is hop-major and first-discovered, so the cap drops
    the deepest, least-relevant references.

    Parameters
    ----------
    seeds : list[Premise]
        Starting premises, excluded from results.
    depth : int
        Maximum hop depth.
    max_premises : int, optional
        Result cap.

    Returns
    -------
    list[Premise]
        Breadth-first closure.
    """
    if depth <= 0 or not seeds:
        return []
    visited: set[str] = {p.full_name for p in seeds}
    frontier: list[Premise] = list(seeds)
    out: list[Premise] = []
    for _ in range(depth):
        next_frontier: list[Premise] = []
        for p in frontier:
            for ref in referenced_premises(p.full_name):
                if ref.full_name not in visited:
                    visited.add(ref.full_name)
                    next_frontier.append(ref)
                    out.append(ref)
                    if len(out) >= max_premises:
                        return out
        if not next_frontier:
            break
        frontier = next_frontier
    return out
