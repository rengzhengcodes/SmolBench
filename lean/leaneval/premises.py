"""Premise lookup over LeanDojo Benchmark 4 `corpus.jsonl`.

`corpus.jsonl` has one record per Lean source file in the traced repo:
    {path, imports: [paths], premises: [{full_name, code, start, end, kind}]}

Two layers of premise data:

- `signature(p)` — the prefix of `code` before the first top-level `:=`.
- `body_with_proof(p)` — slices the source file from the premise's `start` to
  the next top-level declaration. Captures the proof body for theorems too
  (the corpus `code` field is signature-only for theorems).

`premise_dep_closure(seeds, depth)` BFS-expands per-premise derivation edges
for the `hint:3+` rungs. Edges come from `referenced_premises`, which
prefers the LeanDojo trace (the premises each tactic of a theorem's proof
actually used, the same data the MPI is built from) and falls back to
namespace-aware name matching over the declaration source for premises
without a trace (definitions, instances, term-mode proofs).
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


@lru_cache(maxsize=512)
def _source_lines(file_path: str) -> tuple[str, ...] | None:
    """Lines of a corpus source file, or None if it is not on disk."""
    src = _resolve_source(file_path)
    if src is None:
        return None
    return tuple(src.read_text().splitlines())


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
    lines = _source_lines(file_path)
    if lines is None:
        return ""
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

    Falls back to the corpus `code` field if the source file isn't accessible.
    """
    sliced = slice_full_decl(p.file_path, p.start[0], p.end[0])
    return sliced or p.code


# ---------------------------------------------------------------------------
# Trace-based derivation index
# ---------------------------------------------------------------------------


DERIVATION_INDEX_PATH = DATA_ROOT.parent / "derivation_index.json"


def build_derivation_index(kind: str = "random") -> dict[str, list[str]]:
    """`full_name -> premises used by its traced proof`, over every split.

    Reads the raw benchmark JSON (train.json is 357 MB) without going through
    `load_split`'s cache so the objects can be freed afterwards. Premises are
    in first-use order, deduplicated, self-references dropped. A traced
    theorem whose proof named no corpus premise maps to an empty list.
    """
    out: dict[str, list[str]] = {}
    for split in ("train", "val", "test"):
        raw = json.loads((DATA_ROOT / kind / f"{split}.json").read_text())
        for rec in raw:
            tts = rec.get("traced_tactics") or []
            if not tts:
                continue
            seen: set[str] = {rec["full_name"]}
            names: list[str] = []
            for tt in tts:
                annotated = tt.get("annotated_tactic") or []
                for p in (annotated[1] if len(annotated) > 1 else []):
                    n = p["full_name"]
                    if n not in seen:
                        seen.add(n)
                        names.append(n)
            out[rec["full_name"]] = names
        del raw
    return out


@lru_cache(maxsize=1)
def _derivation_index() -> dict[str, list[str]]:
    """Load `data/derivation_index.json`, building it on first use (~1 min)."""
    if DERIVATION_INDEX_PATH.exists():
        return json.loads(DERIVATION_INDEX_PATH.read_text())
    idx = build_derivation_index()
    DERIVATION_INDEX_PATH.write_text(json.dumps(idx))
    return idx


def dep_source(full_name: str) -> str:
    """Which edge source `referenced_premises` uses: trace | text | none."""
    if full_name in _derivation_index():
        return "trace"
    return "text" if lookup(full_name) is not None else "none"


# ---------------------------------------------------------------------------
# Text fallback: namespace-aware name resolution over the declaration source
# ---------------------------------------------------------------------------


# Lean 4 identifier: starts with a letter / underscore / Greek; can contain
# alphanumeric, underscore, prime, dot (for namespacing), and a few unicode
# letters that mathlib uses heavily. We deliberately stay ASCII-leaning here
# since name lookups are against the corpus index (which uses ASCII full_names).
# A trailing `.` (sentence end in a docstring) is stripped by the caller.
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_'.]*")

_NAMESPACE_RE = re.compile(r"^namespace\s+([\w.']+)")
_SECTION_RE = re.compile(r"^section\b")
_END_RE = re.compile(r"^end\b")
_OPEN_RE = re.compile(r"^open\s+(?!scoped\b)(.+)$")


@lru_cache(maxsize=8192)
def _file_context(file_path: str, line: int) -> tuple[str, tuple[str, ...]]:
    """`(current namespace, opened namespaces)` in effect at 1-indexed `line`.

    Tracks `namespace`/`section`/`end` nesting and `open` commands above the
    line. `open A in` and `open A (x y)` / `hiding` / `renaming` forms are
    read as opening `A`; `open scoped` is ignored (notation only).
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


def _resolve_name(tok: str, ns: str, opens: tuple[str, ...], idx: dict, short_idx: dict) -> str | None:
    """Resolve an identifier the way Lean would, given the file context.

    Order: exact full name; `_root_.` prefix; qualified under the current
    namespace, its ancestors, or an opened namespace (also opened namespaces
    relative to the current one); a bare short name that is globally unique;
    for `x.foo` dot notation on a local, the suffix under the same context.
    Returns None when nothing or more than one candidate matches.
    """
    if tok.startswith("_root_."):
        tok = tok[len("_root_."):]
    if tok in idx:
        return tok

    prefixes = []
    parts = ns.split(".") if ns else []
    for i in range(len(parts), 0, -1):
        prefixes.append(".".join(parts[:i]))
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
    # file context only (never by global uniqueness — too many collisions).
    suffix = tok.rpartition(".")[2]
    hits = {f"{s}.{suffix}" for s in scopes if f"{s}.{suffix}" in idx}
    return hits.pop() if len(hits) == 1 else None

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
    """Derivation edges of `full_name`: the premises its proof uses.

    1. If the LeanDojo benchmark traced `full_name`'s proof, return the
       premises its tactics used (in first-use order). This is exact for
       named usage. It does not include lemmas `simp`/`omega`/`aesop` find
       on their own, and instances resolved by typeclass search.
    2. Otherwise (definitions, instances, term-mode proofs) tokenize the
       declaration source and resolve each identifier with the file's
       `namespace`/`open` context (`_resolve_name`). This is a reference
       closure over the whole declaration, statement included.

    Returns a tuple (hashable, lru-cacheable). Empty if nothing resolves.
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
    seeds: list[Premise], depth: int,
) -> list[Premise]:
    """BFS over derivation edges (`referenced_premises`) to depth `depth`.

    Yields premises reachable from `seeds` within `depth` hops in BFS order
    (closest first). Excludes the seeds themselves. Uncapped: a cap would
    let two levels render identically and empty their comparison.
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
        if not next_frontier:
            break
        frontier = next_frontier
    return out
