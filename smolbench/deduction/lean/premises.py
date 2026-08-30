"""Premise lookup over LeanDojo Benchmark 4 `corpus.jsonl`.

`corpus.jsonl` has one record per Lean source file in the traced repo:
    {path, imports: [paths], premises: [{full_name, code, start, end, kind}]}

Three layers of premise text: `signature(p)` (the prefix of `code` before
the first top-level `:=`), `body(p)` (the corpus's `code` field:
signature-only for theorems, `:= body` included for `def`s), and
`body_with_proof(p)` (slices the source file from the premise's `start` to
the next top-level declaration, so theorem proof bodies are captured too).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .corpus import data_root


@dataclass(frozen=True)
class Premise:
    """One premise (theorem/def/instance/etc.) declared in the traced repo.

    Built from one entry of a `corpus.jsonl` record's ``premises`` list.
    ``full_name`` is the join key to the lighter per-reference dicts in
    ``corpus.TracedTactic.premises``, which `context.py`'s hint-chain rendering
    resolves via `lookup`.
    """

    #: Fully-qualified Lean declaration name (e.g. ``Nat.add_comm``), unique
    #: within the index (see `_index`'s collision-handling note).
    full_name: str
    #: Source text as captured by the corpus: signature-only for theorems
    #: (proof omitted), signature plus ``:= body`` for defs. See
    #: `signature` / `body` / `body_with_proof` for the three ways this is
    #: presented to callers.
    code: str
    #: ``(line, column)`` of the declaration's start in `file_path`.
    #: `slice_full_decl` consumes `start[0]` (the line) as 1-indexed -- see
    #: that function's explicit ``start_line - 1`` conversion before
    #: list-indexing the source file's lines. This is the one place in
    #: this codebase where the corpus's line-indexing convention is
    #: actually exercised, and is therefore provably 1-indexed.
    start: tuple[int, int]
    #: ``(line, column)`` of the declaration's end in `file_path`. See
    #: `start`.
    end: tuple[int, int]
    #: Corpus-reported declaration kind (e.g. ``"theorem"``, ``"def"``,
    #: ``"instance"``). This is surfaced alongside the premise's
    #: signature/body in rendered hint-chain prompts (see
    #: ``context._render_hint_parts``).
    kind: str
    #: Path (relative to the traced repo root) of the source file this
    #: premise is declared in. Provenance: taken from the *file record*'s
    #: ``path`` field in ``corpus.jsonl`` (the file the premise was found
    #: under, while iterating that record's ``premises`` list). Not taken
    #: from any field on the premise's own JSON dict, so every `Premise`
    #: built from the same file record shares this value. `_resolve_source`
    #: consumes this to locate the cached mathlib4 source file, for
    #: `body_with_proof`'s full-declaration slicing.
    file_path: str


@lru_cache(maxsize=1)
def _index() -> dict[str, Premise]:
    """Load corpus.jsonl into a full_name -> Premise dict (~5s, cached)."""
    path = data_root() / "corpus.jsonl"
    idx: dict[str, Premise] = {}
    with path.open() as f:
        for line in f:
            rec = json.loads(line)
            for p in rec["premises"]:
                fn = p["full_name"]
                # On collisions keep the first occurrence; mathlib4 has very
                # few duplicate full_names.
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
    """Look up a premise by fully-qualified name; None when absent.

    Absent means declared outside the traced repo, or dropped as a duplicate by
    `_index`'s collision handling. Every caller here and in `context.py` treats
    None as "premise unavailable" rather than an error --
    ``context._render_hint_parts`` renders a placeholder instead of raising.
    """
    return _index().get(full_name)


def signature(p: Premise) -> str:
    """The premise signature: `p.code` up to the first top-level `:=`, rstripped.

    "Top-level" means outside any ``[]``, ``()`` or ``{}``: Lean attribute syntax
    like ``@[to_additive (attr := simp) "..."]`` puts a ``:=`` inside the
    attribute, so a naive split would chop the declaration in half. Many mathlib
    theorems have no ``:=`` in `code` at all; those return the full `code`.
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


def body(p: Premise) -> str:
    """`p.code`: signature-only for theorems, signature plus ``:= body`` for defs."""
    return p.code


# ---------------------------------------------------------------------------
# Source-file slicing — captures real proof bodies (theorems too)
# ---------------------------------------------------------------------------


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
def _traced_root() -> Path:
    """Locate the cached, traced mathlib4 repo on disk."""
    cache = Path.home() / ".cache" / "lean_dojo"
    for d in sorted(cache.glob("leanprover-community-mathlib4-*/mathlib4")):
        return d
    raise FileNotFoundError(
        "no cached mathlib4 traced repo found under ~/.cache/lean_dojo/"
    )


def _resolve_source(file_path: str) -> Path | None:
    """Resolve a corpus `file_path` against the traced repo root; None if absent."""
    root = _traced_root()
    if file_path.startswith(".lake/"):
        candidate = root / file_path
    else:
        candidate = root / file_path
    return candidate if candidate.exists() else None


@lru_cache(maxsize=8192)
def slice_full_decl(file_path: str, start_line: int, end_line: int, max_lines: int = 200) -> str:
    """Slice the full declaration (statement + proof body) from a source file.

    Reads `file_path` (corpus-relative, via `_resolve_source`) from 1-indexed
    `start_line` and stops at the first of: the next column-0 line matching a
    top-level keyword (theorem/def/...), searched from 1-indexed `end_line`
    onward; `max_lines` lines consumed; or end of file. Returns the slice
    rstripped, or ``""`` if the source file is not found.
    """
    src = _resolve_source(file_path)
    if src is None:
        return ""
    lines = src.read_text().splitlines()
    s = max(0, start_line - 1)
    if s >= len(lines):
        return ""
    # Search forward starting one line *after* end_line for the next top-level decl.
    search_from = max(s + 1, end_line)
    cap = min(s + max_lines, len(lines))
    for i in range(search_from, cap):
        if _TOP_LEVEL_RE.match(lines[i]):
            return "\n".join(lines[s:i]).rstrip()
    return "\n".join(lines[s:cap]).rstrip()


def body_with_proof(p: Premise) -> str:
    """The full declaration including any proof body, via `slice_full_decl`.

    Falls back to `body(p)` when the source file is not accessible.
    """
    sliced = slice_full_decl(p.file_path, p.start[0], p.end[0])
    return sliced or p.code


# ---------------------------------------------------------------------------
# Per-premise dependency graph (proper transitive closure for hint:3 / hint:4)
# ---------------------------------------------------------------------------


# Lean 4 identifier: starts with a letter, underscore, or Greek letter; can
# contain alphanumeric characters, underscore, prime, and dot (for
# namespacing). This pattern deliberately stays ASCII-leaning, since name
# lookups go against the corpus index, which uses ASCII full_names.
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_'.]*")

# Lean keywords, tactic vocabulary, and ubiquitous short identifiers that
# would pollute the dep graph if treated as premise references. This list
# is not exhaustive; it covers only the high-traffic ones.
_LEAN_NOISE = frozenset({
    "theorem", "lemma", "def", "instance", "structure", "inductive",
    "axiom", "example", "class", "abbrev", "fun", "let", "in", "do",
    "if", "then", "else", "match", "with", "by", "have", "show", "this",
    "true", "True", "false", "False", "Type", "Prop", "Sort", "Set",
    "namespace", "open", "import", "section", "end", "variable", "variables",
    "where", "macro", "syntax", "elab", "deriving", "attribute", "set_option",
    "noncomputable", "private", "protected", "partial", "mutual",
    # core tactics
    "rw", "rewrite", "simp", "exact", "apply", "intro", "intros", "rintro",
    "cases", "rcases", "obtain", "use", "constructor", "refine", "refine'",
    "split", "and", "or", "not", "iff", "exists", "forall", "all_goals",
    "any_goals", "tauto", "ring", "field_simp", "linarith", "nlinarith",
    "omega", "decide", "rfl", "trivial", "trivial!", "assumption",
    # very common short ids that would explode the graph
    "id", "le", "lt", "ge", "gt", "eq", "ne", "of", "to", "from",
    "n", "m", "k", "x", "y", "z", "a", "b", "c", "d", "e", "f", "g",
    "h", "h1", "h2", "h3", "p", "q", "r", "s", "t", "u", "v", "w",
})


@lru_cache(maxsize=1)
def _short_name_index() -> dict[str, list[str]]:
    """Map each premise's last-dot segment to the list of full_names sharing it.

    Proof bodies reference premises both fully qualified (``Set.subset_def``)
    and by bare short name (after ``open Set``); this index matches the latter.
    """
    out: dict[str, list[str]] = {}
    for full in _index().keys():
        short = full.rsplit(".", 1)[-1]
        out.setdefault(short, []).append(full)
    return out


@lru_cache(maxsize=4096)
def referenced_premises(full_name: str) -> tuple[Premise, ...]:
    """Find premises referenced by name in `full_name`'s body (proof plus signature).

    Resolves each identifier-like token against the premise index by exact
    full-name match, or by short-name match when unambiguous, filtering out Lean
    keywords, common tactics and very common short identifiers (`_LEAN_NOISE`).
    Returns a tuple so the result stays hashable and lru-cacheable; empty if
    `full_name` is not found or has no recognizable references.
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
        # Exact full-name match (e.g. `Set.subset_def`).
        if tok in idx and tok not in seen:
            seen.add(tok)
            out.append(idx[tok])
            continue
        # Short-name match — only when unambiguous (one full_name candidate).
        if "." not in tok:
            cands = short_idx.get(tok)
            if cands and len(cands) == 1 and cands[0] not in seen:
                seen.add(cands[0])
                out.append(idx[cands[0]])
    return tuple(out)


def premise_dep_closure(
    seeds: list[Premise], depth: int, max_premises: int = 500,
) -> list[Premise]:
    """Run a BFS over per-premise references from `seeds`, to depth `depth`.

    Parameters
    ----------
    seeds : list[Premise]
        BFS roots (typically a tactic's true premises, resolved via `lookup`),
        excluded from the result. Empty `seeds`, or ``depth <= 0``,
        short-circuits to ``[]`` without calling `referenced_premises` at all.
    max_premises : int
        Result cap that keeps prompts bounded, checked mid-frontier: the BFS
        returns the instant it is reached, without finishing the premise being
        expanded or the rest of that hop's frontier.

    Returns
    -------
    list[Premise]
        Premises reachable from `seeds` in strictly hop-major BFS order (within
        a hop: frontier order, then per-premise reference order), deduped at
        their first-discovered hop -- so the `max_premises` cut always drops the
        deepest, least-relevant tail.
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
