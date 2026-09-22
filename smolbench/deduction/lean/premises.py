"""Look up traced Lean premises, their source text, and their derivation edges.

`body_with_proof` slices source through the next declaration so theorem proofs
survive the signature-only corpus record.

`referenced_premises` gives the derivation edges the `hint:3+` rungs expand.
It prefers the LeanDojo trace (the premises each tactic of a theorem's proof
actually used, the same data the MPI is built from) and falls back to
namespace-aware name resolution over the declaration source for premises
without a trace (definitions, instances, term-mode proofs).
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
    """A declaration in the traced repository.

    ``full_name`` is the join key from lighter ``corpus.TracedTactic.premises``
    records to `lookup`, which `context.py` uses to resolve them.
    """

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
                    end=tuple(p["end"]),  # type: ignore[arg-type]
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
def slice_full_decl(
    file_path: str, start_line: int, end_line: int, max_lines: int = 200
) -> str:
    """Slice a declaration and proof from source.

    Stop at the next top-level declaration, ``max_lines``, or EOF.

    Parameters
    ----------
    file_path : str
    start_line : int
        1-indexed start line.
    end_line : int
        1-indexed end line.
    max_lines : int, optional

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

    Returns
    -------
    bool
        Whether traced source was sliced.
    """
    return bool(slice_full_decl(p.file_path, p.start[0], p.end[0]))


# ---------------------------------------------------------------------------
# Trace-based derivation index
# ---------------------------------------------------------------------------


def derivation_index_path() -> Path:
    """Sidecar next to the active corpus: ``<data_root>/derivation_index.json``.

    Per corpus because a post-cutoff corpus has its own splits and traces.
    """
    return data_root() / "derivation_index.json"


def build_derivation_index(kind: str = "random") -> dict[str, list[str]]:
    """``full_name -> premises used by its traced proof``, over every split present.

    Reads the raw split JSON (train.json can be hundreds of MB) without going
    through `corpus.load_split`'s cache so the objects can be freed. Premises
    are in first-use order, deduplicated, self-references dropped. A traced
    theorem whose proof named no corpus premise maps to an empty list; that is
    exact for named usage and blind only to what ``simp``/``omega``/typeclass
    search find on their own.

    Parameters
    ----------
    kind : str, optional

    Returns
    -------
    dict[str, list[str]]
    """
    out: dict[str, list[str]] = {}
    for split in ("train", "val", "test"):
        path = data_root() / kind / f"{split}.json"
        if not path.exists():
            continue
        raw = json.loads(path.read_text())
        for rec in raw:
            tts = rec.get("traced_tactics") or []
            if not tts:
                continue
            seen: set[str] = {rec["full_name"]}
            names: list[str] = []
            for tt in tts:
                annotated = tt.get("annotated_tactic") or []
                for p in annotated[1] if len(annotated) > 1 else []:
                    n = p["full_name"]
                    if n not in seen:
                        seen.add(n)
                        names.append(n)
            out[rec["full_name"]] = names
        del raw
    return out


def write_derivation_index() -> Path:
    """Build the index from the active corpus and write the sidecar.

    ``python -m smolbench.deduction.lean.cli build-derivation-index``; run it
    once per corpus so sweeps do not re-read the split JSON on every start.

    Returns
    -------
    Path
        The written sidecar.
    """
    path = derivation_index_path()
    path.write_text(json.dumps(build_derivation_index()))
    _derivation_index.cache_clear()
    return path


@lru_cache(maxsize=1)
def _derivation_index() -> dict[str, list[str]]:
    """Load `derivation_index_path`, or build it in memory when absent.

    Never writes: the active corpus may be a read-only fixture. Cached; call
    `corpus.reset_caches` after repointing ``SMOLBENCH_LEAN_DATA``.
    """
    path = derivation_index_path()
    if path.exists():
        return json.loads(path.read_text())
    return build_derivation_index()


def dep_source(full_name: str) -> str:
    """Which edge source `referenced_premises` uses: ``trace`` | ``text`` | ``none``.

    Parameters
    ----------
    full_name : str

    Returns
    -------
    str
    """
    if full_name in _derivation_index():
        return "trace"
    return "text" if lookup(full_name) is not None else "none"


# ---------------------------------------------------------------------------
# Text fallback: namespace-aware name resolution over the declaration source
# ---------------------------------------------------------------------------


# ASCII identifiers match corpus full names. A trailing ``.`` (a sentence end
# inside a docstring) is stripped by the caller.
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_'.]*")

_NAMESPACE_RE = re.compile(r"^namespace\s+([\w.']+)")
_SECTION_RE = re.compile(r"^section\b")
_END_RE = re.compile(r"^end\b")
_OPEN_RE = re.compile(r"^open\s+(?!scoped\b)(.+)$")


@lru_cache(maxsize=512)
def _source_lines(file_path: str) -> tuple[str, ...] | None:
    """Lines of a corpus source file, or None if it is not on disk."""
    src = _resolve_source(file_path)
    if src is None:
        return None
    return tuple(src.read_text(encoding="utf-8").splitlines())


@lru_cache(maxsize=8192)
def _file_context(file_path: str, line: int) -> tuple[str, tuple[str, ...]]:
    """``(current namespace, opened namespaces)`` in effect at 1-indexed ``line``.

    Tracks ``namespace``/``section``/``end`` nesting and ``open`` commands
    above the line. ``open A in`` and ``open A (x y)`` / ``hiding`` /
    ``renaming`` forms are read as opening ``A``; ``open scoped`` is ignored
    (notation only).

    Parameters
    ----------
    file_path : str
    line : int

    Returns
    -------
    tuple[str, tuple[str, ...]]
    """
    lines = _source_lines(file_path) or ()
    stack: list[str | None] = []  # namespace name, or None for a section
    opens: list[str] = []
    for raw in lines[: max(0, line - 1)]:
        s = raw.strip()
        if m := _NAMESPACE_RE.match(s):
            stack.append(m.group(1))
        elif _SECTION_RE.match(s):
            stack.append(None)
        elif _END_RE.match(s):
            if stack:
                stack.pop()
        elif m := _OPEN_RE.match(s):
            body = re.split(r"\b(?:hiding|renaming|in)\b|\(", m.group(1))[0]
            opens.extend(tok for tok in body.split() if re.fullmatch(r"[\w.']+", tok))
    ns = ".".join(n for n in stack if n)
    return ns, tuple(opens)


def _resolve_name(
    tok: str, ns: str, opens: tuple[str, ...], idx: dict, short_idx: dict
) -> str | None:
    """Resolve an identifier the way Lean would, given the file context.

    Order: exact full name; ``_root_.`` prefix; qualified under the current
    namespace, its ancestors, or an opened namespace (also opened namespaces
    relative to the current one); a bare short name that is globally unique;
    for ``x.foo`` dot notation on a local, the suffix under the same context.
    Returns None when nothing or more than one candidate matches.

    Parameters
    ----------
    tok : str
    ns : str
    opens : tuple[str, ...]
    idx : dict
    short_idx : dict

    Returns
    -------
    str | None
    """
    if tok.startswith("_root_."):
        tok = tok[len("_root_.") :]
    if tok in idx:
        return tok

    parts = ns.split(".") if ns else []
    prefixes = [".".join(parts[:i]) for i in range(len(parts), 0, -1)]
    scopes = set(prefixes) | set(opens) | {f"{p}.{o}" for p in prefixes for o in opens}
    hits = {f"{s}.{tok}" for s in scopes if f"{s}.{tok}" in idx}
    if len(hits) == 1:
        return hits.pop()
    if hits:
        return None  # ambiguous even with context

    if "." not in tok:
        cands = short_idx.get(tok)
        return cands[0] if cands and len(cands) == 1 else None

    # `h.trans`-style dot notation on a local: resolve the suffix under the
    # file context only (never by global uniqueness -- too many collisions).
    suffix = tok.rpartition(".")[2]
    hits = {f"{s}.{suffix}" for s in scopes if f"{s}.{suffix}" in idx}
    return hits.pop() if len(hits) == 1 else None

#: Excluded Lean tokens; frozen because every identifier checks membership.
_LEAN_NOISE: frozenset[str] = frozenset(
    {
        "theorem",
        "lemma",
        "def",
        "instance",
        "structure",
        "inductive",
        "axiom",
        "example",
        "class",
        "abbrev",
        "fun",
        "let",
        "in",
        "do",
        "if",
        "then",
        "else",
        "match",
        "with",
        "by",
        "have",
        "show",
        "this",
        "true",
        "True",
        "false",
        "False",
        "Type",
        "Prop",
        "Sort",
        "Set",
        "namespace",
        "open",
        "import",
        "section",
        "end",
        "variable",
        "variables",
        "where",
        "macro",
        "syntax",
        "elab",
        "deriving",
        "attribute",
        "set_option",
        "noncomputable",
        "private",
        "protected",
        "partial",
        "mutual",
        "rw",
        "rewrite",
        "simp",
        "exact",
        "apply",
        "intro",
        "intros",
        "rintro",
        "cases",
        "rcases",
        "obtain",
        "use",
        "constructor",
        "refine",
        "refine'",
        "split",
        "and",
        "or",
        "not",
        "iff",
        "exists",
        "forall",
        "all_goals",
        "any_goals",
        "tauto",
        "ring",
        "field_simp",
        "linarith",
        "nlinarith",
        "omega",
        "decide",
        "rfl",
        "trivial",
        "assumption",
        "id",
        "le",
        "lt",
        "ge",
        "gt",
        "eq",
        "ne",
        "of",
        "to",
        "from",
        "h1",
        "h2",
        "h3",
    }
)


@lru_cache(maxsize=1)
def _short_name_index() -> dict[str, list[str]]:
    """Index full names by final segment for bare-name references."""
    out: dict[str, list[str]] = {}
    for full in _index():
        short = full.rsplit(".", 1)[-1]
        out.setdefault(short, []).append(full)
    return out


@lru_cache(maxsize=4096)
def referenced_premises(full_name: str) -> tuple[Premise, ...]:
    """Derivation edges of ``full_name``: the premises its proof uses.

    1. If the benchmark traced ``full_name``'s proof, return the premises its
       tactics used, in first-use order (exact for named usage).
    2. Otherwise (definitions, instances, term-mode proofs) tokenize the
       declaration source and resolve each identifier with the file's
       ``namespace``/``open`` context (`_resolve_name`). This is a reference
       closure over the whole declaration, statement included.

    Tuples keep cached results hashable.

    Parameters
    ----------
    full_name : str

    Returns
    -------
    tuple[Premise, ...]
        Referenced premises; empty if nothing resolves.
    """
    traced = _derivation_index().get(full_name)
    if traced is not None:
        out: list[Premise] = []
        seen: set[str] = {full_name}
        for n in traced:
            p = lookup(n)
            if p is not None and n not in seen:
                seen.add(n)
                out.append(p)
        return tuple(out)

    p = lookup(full_name)
    if p is None:
        return ()
    text = body_with_proof(p)
    if not text:
        text = p.code  # fallback: corpus signature

    idx = _index()
    short_idx = _short_name_index()
    ns, opens = _file_context(p.file_path, p.start[0])

    seen = {full_name}
    out = []
    for tok in _IDENT_RE.findall(text):
        tok = tok.rstrip(".")
        if tok in _LEAN_NOISE or len(tok) <= 1:
            continue
        resolved = _resolve_name(tok, ns, opens, idx, short_idx)
        if resolved is not None and resolved not in seen:
            seen.add(resolved)
            out.append(idx[resolved])
    return tuple(out)


def premise_dep_closure(
    seeds: list[Premise],
    depth: int,
    max_premises: int = 500,
) -> list[Premise]:
    """Return a breadth-first premise closure.

    Excludes seeds; order is hop-major and first-discovered, so the cap drops
    the deepest, least-relevant references.

    Parameters
    ----------
    seeds : list[Premise]
        Starting premises, excluded from results.
    depth : int
    max_premises : int, optional

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
