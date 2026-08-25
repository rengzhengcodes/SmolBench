"""Premise lookup over LeanDojo Benchmark 4 `corpus.jsonl`.

`corpus.jsonl` has one record per Lean source file in the traced repo:
    {path, imports: [paths], premises: [{full_name, code, start, end, kind}]}

This module exposes three layers of premise data:

- `signature(p)` — the prefix of `code` before the first top-level `:=`.
- `body(p)` — the corpus's `code` field (signature-only for theorems,
  includes `:= body` for `def`s).
- `body_with_proof(p)` — slices the source file from the premise's `start`
  to the next top-level declaration. This captures the proof body for
  theorems too.
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

    Built from one entry of a `corpus.jsonl` record's ``premises`` list
    (see `_index`). This is distinct from
    ``smolbench.deduction.lean.corpus.TracedTactic.premises`` -- the
    lighter, per-reference dicts recorded inline in a proof step.
    ``full_name`` is the join key between the two: `context.py`'s
    hint-chain rendering looks each `TracedTactic.premises` entry up in
    this class's index via `lookup`.
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
    """Look up a premise by its fully-qualified name.

    Parameters
    ----------
    full_name : str
        Fully-qualified Lean declaration name (e.g. ``Nat.add_comm``).

    Returns
    -------
    Premise or None
        The indexed `Premise`, or None if `full_name` is not present in
        the corpus index (e.g. declared outside the traced repo, or
        dropped as a duplicate by `_index`'s collision handling). Every
        caller in this module and in `context.py` treats a None result as
        "premise unavailable" rather than an error condition. For
        example, ``context._render_hint_parts`` renders a "(not found in
        premise corpus)" placeholder instead of raising.
    """
    return _index().get(full_name)


def signature(p: Premise) -> str:
    """Get the premise signature: the code prefix before the first top-level `:=`.

    Parameters
    ----------
    p : Premise
        Premise to extract the signature from.

    Returns
    -------
    str
        `p.code` up to (excluding) the first top-level `:=`, with
        trailing whitespace stripped. "Top-level" means outside any `[]`,
        `()`, or `{}` brackets. Lean attribute syntax like
        `@[to_additive (attr := simp) "..."]` puts a `:=` inside the
        attribute, so a naive split would chop the declaration in half.
        Many mathlib theorems have no `:=` at all in `code` (the corpus
        slice ends at the type signature); this returns the full `code`
        for those.
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
    """Get the premise source as captured in `corpus.jsonl`.

    Parameters
    ----------
    p : Premise
        Premise to read.

    Returns
    -------
    str
        `p.code`: signature-only for theorems, signature plus ``:= body``
        for defs.
    """
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
    """Resolve a corpus file_path to an absolute path on disk.

    Parameters
    ----------
    file_path : str
        Either `Mathlib/...` (lives directly under the traced mathlib4
        root) or `.lake/packages/.../*.lean` (lives under
        `<traced_root>/.lake/packages`).

    Returns
    -------
    Path or None
        The resolved absolute path, or None if it does not exist on disk.
    """
    root = _traced_root()
    if file_path.startswith(".lake/"):
        candidate = root / file_path
    else:
        candidate = root / file_path
    return candidate if candidate.exists() else None


@lru_cache(maxsize=8192)
def slice_full_decl(file_path: str, start_line: int, end_line: int, max_lines: int = 200) -> str:
    """Slice the full declaration (statement + proof body) from a source file.

    Parameters
    ----------
    file_path : str
        Corpus-relative path to the source file (see `_resolve_source`).
    start_line : int
        1-indexed line where the declaration starts (matches the corpus).
    end_line : int
        1-indexed line where the declaration's recorded span ends.
    max_lines : int, default 200
        Maximum number of lines to read from `start_line`.

    Returns
    -------
    str
        The slice, with trailing whitespace stripped, or `""` if the
        source file is not found. This function reads from `start_line`
        and stops at the first of: the next line at column 0 matching a
        top-level keyword (theorem/def/...), `max_lines` lines consumed,
        or end of file.
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
    """Slice the full declaration, including any proof body, from the source file.

    Parameters
    ----------
    p : Premise
        Premise to slice.

    Returns
    -------
    str
        The sliced declaration, via `slice_full_decl`. Falls back to
        `body(p)` (the corpus `code` field) if the source file is not
        accessible.
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

    Returns
    -------
    dict of str to list of str
        Short name -> `full_name`s that share it. Lean 4 / mathlib uses
        heavy namespacing. References in proof bodies are sometimes fully
        qualified (`Set.subset_def`) and sometimes just the short name
        (after `open Set`). This index lets `referenced_premises` match
        the short-name form.
    """
    out: dict[str, list[str]] = {}
    for full in _index().keys():
        short = full.rsplit(".", 1)[-1]
        out.setdefault(short, []).append(full)
    return out


@lru_cache(maxsize=4096)
def referenced_premises(full_name: str) -> tuple[Premise, ...]:
    """Find premises referenced by name in `full_name`'s body.

    Parameters
    ----------
    full_name : str
        Fully-qualified name of the premise whose body to scan.

    Returns
    -------
    tuple of Premise
        Premises referenced in the body (proof plus signature) of
        `full_name`. This function tokenizes the body, then looks up
        each identifier-like token in the premise index, by exact
        full-name match or by short-name match (only when unambiguous).
        It filters out Lean keywords, common tactics, and very common
        short identifiers (see `_LEAN_NOISE`). The result is a tuple, so
        it stays hashable and lru-cacheable. Returns an empty tuple if
        `full_name` is not found, or has no recognizable references.
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
    """Run a BFS over per-premise references, to depth `depth`.

    This finds premises reachable from `seeds` within `depth` hops, in
    BFS order (closest first). It excludes the seeds themselves, and caps
    the result at `max_premises` to keep prompts bounded; truncation
    drops the deepest discoveries first.

    Parameters
    ----------
    seeds : list of Premise
        Starting premises. Typically the true premises used in a tactic,
        already resolved via `lookup`. The BFS walks outward from each
        seed's per-premise reference graph (`referenced_premises`).
    depth : int
        Number of BFS hops to expand. `depth <= 0`, or an empty `seeds`,
        short-circuits to an empty list, without calling
        `referenced_premises` at all.
    max_premises : int, default 500
        Hard cap on the number of premises returned. The BFS returns as
        soon as `len(out) >= max_premises` is reached -- mid-hop, and
        even mid-frontier-item if needed. It does not finish the
        remaining references of the premise it is currently expanding,
        or the rest of that hop's frontier.

    Returns
    -------
    list of Premise
        Premises reachable from `seeds`, in BFS order: every hop-``n``
        premise precedes every hop-``(n+1)`` premise. Within a hop, order
        follows frontier-iteration order, then per-premise reference
        order. Excludes `seeds` themselves, and any premise already
        discovered at a shallower hop. A `visited` set dedupes across
        hops, so a premise referenced by multiple frontier premises
        appears once, at its first-discovered hop.

    Notes
    -----
    Discovery order is strictly hop-major, so truncating the output at
    `max_premises` always drops the deepest (least-relevant) tail of that
    order first. A hop-1 premise already appended to `out` is never
    displaced by, or dropped in favor of, a hop-2 discovery.

    Each hop's cost is bounded by `referenced_premises`'s own
    ``lru_cache(maxsize=4096)``. Repeated calls that share seeds across
    different (theorem, k) cells reuse prior tokenization/lookup work,
    instead of repeating it.
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
