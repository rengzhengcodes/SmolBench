"""Premise lookup over LeanDojo Benchmark 4 `corpus.jsonl`.

`corpus.jsonl` has one record per Lean source file in the traced repo:
    {path, imports: [paths], premises: [{full_name, code, start, end, kind}]}

Three layers of premise data:

- `signature(p)` — the prefix of `code` before the first top-level `:=`.
- `body(p)` — the corpus's `code` field (signature-only for theorems, includes
  `:= body` for `def`s).
- `body_with_proof(p)` — slices the source file from the premise's `start` to
  the next top-level declaration. Captures the proof body for theorems too.

`transitive_files(seeds, depth)` does a BFS over file-level imports for
`hint:3`/`hint:4` rungs. `premises_in_files(paths)` yields the premises
declared in those files for token-budget-bounded inclusion.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .corpus import DATA_ROOT


@dataclass(frozen=True)
class Premise:
    full_name: str
    code: str
    start: tuple[int, int]
    end: tuple[int, int]
    kind: str
    file_path: str   # the source file this premise is declared in


@lru_cache(maxsize=1)
def _index() -> dict[str, Premise]:
    """Load corpus.jsonl into a full_name -> Premise dict (~5s, cached)."""
    path = DATA_ROOT / "corpus.jsonl"
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
    return _index().get(full_name)


def signature(p: Premise) -> str:
    """Premise signature: code prefix before the first top-level `:=`.

    "Top-level" means outside any `[]`, `()`, or `{}` brackets — Lean attribute
    syntax like `@[to_additive (attr := simp) "..."]` puts a `:=` inside the
    attribute, and a naive split would chop the declaration in half.

    Many mathlib theorems have no `:=` at all in `code` (the corpus slice ends
    at the type signature), in which case this returns the full `code`.
    Trailing whitespace stripped.
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
    """Premise source as captured in `corpus.jsonl` (signature-only for theorems)."""
    return p.code


def index_size() -> int:
    """Total number of unique premises indexed."""
    return len(_index())


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
    """Resolve a corpus file_path to an absolute path on disk, or None if missing.

    `file_path` may be either:
      - `Mathlib/...` — lives directly under the traced mathlib4 root.
      - `.lake/packages/.../*.lean` — lives under `<traced_root>/.lake/packages`.
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

    `start_line` and `end_line` are 1-indexed (matching the corpus). Reads from
    `start_line` until either:
      - the next line at column 0 matching a top-level keyword (theorem/def/...)
      - `max_lines` lines have been consumed
      - end of file
    Returns the slice with trailing whitespace stripped, or `""` on miss.
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
    """Slice from the source file: full declaration including any proof body.

    Falls back to `body(p)` (the corpus `code` field) if the source file isn't
    accessible.
    """
    sliced = slice_full_decl(p.file_path, p.start[0], p.end[0])
    return sliced or p.code


# ---------------------------------------------------------------------------
# File-level transitive closure (hint:3 / hint:4)
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _file_records() -> dict[str, dict]:
    """Map `file_path -> {imports: [...], premises: [...]}`. Loaded once (~5s)."""
    out: dict[str, dict] = {}
    with (DATA_ROOT / "corpus.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            out[r["path"]] = {"imports": r["imports"], "premises": r["premises"]}
    return out


def transitive_files(seed_files: set[str], depth: int) -> list[str]:
    """BFS over file imports starting from `seed_files`.

    Returns a list of file paths discovered at hops 1..depth (excluding seeds),
    in BFS order so token-truncation keeps the closest dependencies.
    """
    if depth <= 0:
        return []
    records = _file_records()
    visited: set[str] = set(seed_files)
    frontier = list(seed_files)
    out: list[str] = []
    for _ in range(depth):
        next_frontier: list[str] = []
        for f in frontier:
            rec = records.get(f)
            if not rec:
                continue
            for imp in rec["imports"]:
                if imp not in visited:
                    visited.add(imp)
                    next_frontier.append(imp)
                    out.append(imp)
        frontier = next_frontier
    return out


def premises_in_files(file_paths: list[str]) -> list[Premise]:
    """Yield Premise records for every premise declared in the given files."""
    records = _file_records()
    out: list[Premise] = []
    for fp in file_paths:
        rec = records.get(fp)
        if not rec:
            continue
        for p in rec["premises"]:
            out.append(Premise(
                full_name=p["full_name"],
                code=p["code"],
                start=tuple(p["start"]),  # type: ignore[arg-type]
                end=tuple(p["end"]),      # type: ignore[arg-type]
                kind=p["kind"],
                file_path=fp,
            ))
    return out


# ---------------------------------------------------------------------------
# Per-premise dependency graph (proper transitive closure for hint:3 / hint:4)
# ---------------------------------------------------------------------------


# Lean 4 identifier: starts with a letter / underscore / Greek; can contain
# alphanumeric, underscore, prime, dot (for namespacing), and a few unicode
# letters that mathlib uses heavily. We deliberately stay ASCII-leaning here
# since name lookups are against the corpus index (which uses ASCII full_names).
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_'.]*")

# Lean keywords + tactic vocabulary + ubiquitous short identifiers that would
# pollute the dep graph if treated as premise references. Not exhaustive; just
# the high-traffic ones.
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
    """Map each premise's last-dot segment → list of full_names sharing it.

    Lean 4 / mathlib uses heavy namespacing; references in proof bodies are
    sometimes fully qualified (`Set.subset_def`) and sometimes just the short
    name (after `open Set`). The short-name index lets us catch the latter.
    """
    out: dict[str, list[str]] = {}
    for full in _index().keys():
        short = full.rsplit(".", 1)[-1]
        out.setdefault(short, []).append(full)
    return out


@lru_cache(maxsize=4096)
def referenced_premises(full_name: str) -> tuple[Premise, ...]:
    """Premises referenced (by name) in `full_name`'s body.

    Tokenizes the premise's body (proof + signature), looks up each
    identifier-like token in the premise index by exact full-name match
    or by short-name match (when unambiguous). Filters Lean keywords,
    common tactics, and very-common short identifiers.

    Returns a tuple (so it's hashable and lru-cacheable). Empty tuple if the
    premise isn't found or has no recognisable refs.
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
    """BFS over per-premise references to depth `depth`.

    Yields premises reachable from `seeds` within `depth` hops in BFS order
    (closest first). Excludes the seeds themselves. Capped at `max_premises`
    to keep prompts bounded; truncation drops the deepest discoveries first.
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
