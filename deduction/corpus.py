"""LeanDojo corpus loader and Mathlib source readers.

Read-only access layer. All functions take pure inputs and return pure data
(no I/O side effects beyond reading files at well-defined paths).

The "transitive-import resolver" the legacy plan called for is intentionally
absent — DESIGN.md commits to using F's literal direct imports verbatim and
letting Lean's import resolution handle the transitive closure.

Public API
----------
    Premise                   — frozen dataclass for a corpus entry
    load_corpus()             — full_name -> Premise dict from corpus.jsonl
    load_traced_lookup()      — full_name -> list[traced_tactic dict]
    read_source()             — declaration text at corpus [start, end]
    read_source_with_attrs()  — same, expanded backward through @[...]
    strip_docstring()         — remove /-- ... -/ blocks
    parse_imports()           — F's literal import block (lines + end_index)
    extract_prefix_full()     — F lines 1..L-1, leading import block stripped
    extract_prefix_scope_only() — scope-affecting subset of the full prefix
    namespace_stack_at()      — active namespace stack at line L
    local_name()              — strip the deepest namespace prefix from full_name
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = ROOT / "data" / "leandojo_benchmark_4"
MATHLIB_DIR = ROOT / "data" / "mathlib4"


@dataclass(frozen=True, slots=True)
class Premise:
    full_name: str
    file_path: str        # repo-relative, e.g. "Mathlib/Algebra/.../Foo.lean"
    corpus_code: str      # `code` field from corpus.jsonl (signature only for theorems)
    kind: str             # "commanddeclaration", "lemma", "def", ...
    start: Tuple[int, int]  # (line, col) 1-indexed line, 0-indexed col
    end: Tuple[int, int]


# ---------- corpus + splits I/O ----------

def load_corpus(corpus_path: Path = BENCHMARK_DIR / "corpus.jsonl") -> Dict[str, Premise]:
    """full_name -> Premise. Last-write-wins on collisions across files."""
    out: Dict[str, Premise] = {}
    with corpus_path.open() as f:
        for line in f:
            entry = json.loads(line)
            for p in entry["premises"]:
                out[p["full_name"]] = Premise(
                    full_name=p["full_name"],
                    file_path=entry["path"],
                    corpus_code=p["code"],
                    kind=p["kind"],
                    start=tuple(p["start"]),
                    end=tuple(p["end"]),
                )
    return out


def load_traced_lookup(benchmark_dir: Path = BENCHMARK_DIR) -> Dict[str, list]:
    """Union of traced_tactics across every split, keyed by theorem full_name.
    Used as the premise-graph source for BFS expansion in elaborate.py."""
    out: Dict[str, list] = {}
    for schema in ("random", "novel_premises"):
        for split in ("train", "val", "test"):
            path = benchmark_dir / schema / f"{split}.json"
            if not path.exists():
                continue
            for t in json.load(path.open()):
                tactics = t.get("traced_tactics")
                if tactics and t["full_name"] not in out:
                    out[t["full_name"]] = tactics
    return out


# ---------- source reading ----------

_ATTR_LINE_RE = re.compile(r"^\s*@\[")


def read_source(file_path: Path, start: Tuple[int, int], end: Tuple[int, int]) -> str:
    """Read the declaration text at corpus [start, end] from a Mathlib file.
    `start`/`end` are (line, col) 1-indexed line, 0-indexed col, matching the
    LeanDojo corpus convention."""
    lines = file_path.read_text().splitlines()
    sl, _ = start
    el, _ = end
    return "\n".join(lines[sl - 1:el])


def read_source_with_attrs(file_path: Path, start: Tuple[int, int], end: Tuple[int, int]) -> str:
    """Same as read_source but expands `start` upward through any contiguous
    `@[...]` attribute lines. The corpus is inconsistent about whether
    attribute decoration is included in [start, end]; this normalizes it."""
    lines = file_path.read_text().splitlines()
    sl, _ = start
    el, _ = end
    # Walk upward from sl-2 (0-indexed) while preceding lines are @[...]
    i = sl - 2  # index of the line ABOVE the start
    while i >= 0 and _ATTR_LINE_RE.match(lines[i]):
        i -= 1
    actual_start = i + 1 + 1  # back to 1-indexed line of first @[ (or sl)
    return "\n".join(lines[actual_start - 1:el])


def _find_top_level_assign(text: str) -> int:
    """Return the index of the first top-level `:=` (outside `[...]` brackets)
    in `text`, or -1 if not found."""
    depth = 0
    i = 0
    while i < len(text) - 1:
        c = text[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
        elif depth == 0 and c == ":" and text[i + 1] == "=":
            return i
        i += 1
    return -1


def is_tactic_mode_proof(file_path: Path, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
    """True iff the declaration body (the text after the first top-level
    `:=`) starts with `by` — meaning the canonical proof is genuinely
    tactic-mode and LeanDojo's `traced_tactics` reconstructs into a
    complete proof.

    Returns False for term-mode proofs (`:= ⟨...⟩`, `:= rfl`, `:= some_term`),
    and for declarations with no `:=` body (structures, inductives,
    pattern-matching defs). LeanDojo may still record `traced_tactics`
    for inner `by` blocks inside term-mode proofs, but those are proof
    fragments that don't compose into a tactic-mode replay — replays
    would fail with `unknown identifier` or `unsolved goals`.
    """
    text = read_source(file_path, start, end)
    idx = _find_top_level_assign(text)
    if idx < 0:
        return False
    after = text[idx + 2:].lstrip()
    if not after:
        return False
    return after.startswith("by\n") or after.startswith("by ") or after == "by"


def extract_proof_body_source(
    file_path: Path, start: Tuple[int, int], end: Tuple[int, int]
) -> str:
    """Return the literal source text of the proof body — everything after
    `:= by` in the declaration at corpus `[start, end]`. Trailing
    whitespace stripped; leading-tactic indentation preserved verbatim
    so the body can be spliced back into a `theorem ... := by\\n` site
    without re-indentation.

    Returns empty string for non-tactic-mode declarations or when
    parsing fails."""
    text = read_source(file_path, start, end)
    idx = _find_top_level_assign(text)
    if idx < 0:
        return ""
    after = text[idx + 2:].lstrip()
    if after.startswith("by\n"):
        body = after[3:]  # strip "by\n"
    elif after.startswith("by "):
        body = after[3:]  # strip "by "
        # Inline-by case: body lacks indentation. Add 2 spaces if it doesn't
        # already have leading whitespace, so it sits cleanly under our
        # generated `theorem ... := by\n`.
        if body and not body[0].isspace():
            body = "  " + body
    elif after == "by":
        return ""
    else:
        return ""
    return body.rstrip()


# Identifier-like tokens that get extracted from term-mode proof bodies.
# Lean identifiers can include dots, primes, and Greek/subscript Unicode;
# we keep this conservative — module/declaration names accessed in
# typical Mathlib bodies match `[A-Za-z_][\w.']*`.
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9.']*")

# Single-letter / very-common short bound-variable names that almost
# never refer to corpus declarations. If a single-letter name happens
# to also be a corpus entry, that entry will not be picked up by
# `extract_premise_refs_from_text` — we accept the precision loss in
# exchange for far fewer false positives from proof-local binders.
_BOUND_VAR_BLACKLIST = (
    set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    | {
        # Two-letter / common
        "ih", "ne", "le", "lt", "ge", "gt", "eq",
        # Lean keywords / primitives that shouldn't ever resolve to a
        # premise even if they collide with a corpus name
        "by", "fun", "let", "have", "show", "match", "with", "do",
        "if", "then", "else", "rfl", "Iff", "Eq",
    }
)


def extract_premise_refs_from_text(
    text: str, corpus: "Dict[str, Premise]"
) -> List[str]:
    """Extract Mathlib-resident premise full_names from a chunk of Lean
    source (typically a term-mode proof body). Used as a fallback in BFS
    expansion when LeanDojo's `traced_tactics` are empty for a premise
    (because the proof is term-mode and has no recorded tactics).

    Strategy:
      - Regex-extract identifier-like tokens
      - Filter to tokens that are corpus-indexed and live in `Mathlib/...`
      - Drop tokens in `_BOUND_VAR_BLACKLIST`
      - Preserve first-seen order, dedup

    Precision is lower than LeanDojo's annotations (which run after type
    inference and capture dot-notation method calls). For tactic-mode
    proofs with traced_tactics, use the annotations directly. For
    term-mode proofs this is the only option."""
    seen: set = set()
    out: List[str] = []
    for tok in _IDENT_RE.findall(text):
        if tok in _BOUND_VAR_BLACKLIST:
            continue
        if tok in seen:
            continue
        if tok in corpus and corpus[tok].file_path.startswith("Mathlib/"):
            seen.add(tok)
            out.append(tok)
    return out


def split_top_level_tactics(proof_body_source: str) -> List[str]:
    """Split a proof body into its top-level tactics by indentation.

    The first non-blank line's leading-whitespace count is the body's
    "base indent"; each line at exactly that indent starts a new top-
    level tactic, and lines indented further are continuations of the
    current tactic. Blank lines attach to the preceding tactic.

    Each returned tactic has the base indent stripped from every line so
    callers can re-indent uniformly when splicing into a generated
    `theorem ... := by\\n` site.

    Correctly handles:
      - linear sequential proofs (one line per tactic)
      - bullet-focused proofs (`· tac`) — each bullet is its own top-level
      - inner-`by` blocks (`exact f fun h => by tac`) — kept as part of
        the outer tactic, not split out
      - multi-line tactics (`have h : T := by\\n  tac1\\n  tac2`) — kept
        grouped via continuation indentation
      - `<;>` chains on one line — single tactic
    """
    lines = proof_body_source.splitlines()
    if not lines:
        return []
    base_indent: Optional[int] = None
    for line in lines:
        if line.strip():
            base_indent = len(line) - len(line.lstrip())
            break
    if base_indent is None:
        return []

    groups: List[List[str]] = []
    current: List[str] = []
    for line in lines:
        if not line.strip():
            if current:
                current.append(line)
            continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent <= base_indent:
            if current:
                groups.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        groups.append(current)

    out: List[str] = []
    for group in groups:
        dedented: List[str] = []
        for line in group:
            if line.strip():
                # Strip up to base_indent leading spaces (no more — preserves
                # relative indentation of continuation lines).
                idx = 0
                while idx < base_indent and idx < len(line) and line[idx] == " ":
                    idx += 1
                dedented.append(line[idx:])
            else:
                dedented.append(line)
        joined = "\n".join(dedented).rstrip()
        if joined:
            out.append(joined)
    return out


_DOC_BLOCK_RE = re.compile(r"/--[\s\S]*?-/")


def strip_docstring(text: str) -> str:
    """Remove `/-- ... -/` doc-comment blocks. Non-doc `/- ... -/` blocks and
    `--` line comments are preserved."""
    return _DOC_BLOCK_RE.sub("", text)


# ---------- F's import block + prefix extraction ----------

_IMPORT_RE = re.compile(r"^\s*import\s+\S")
_BLANK_RE = re.compile(r"^\s*$")
_LINE_COMMENT_RE = re.compile(r"^\s*--")
_BLOCK_COMMENT_OPEN_RE = re.compile(r"^\s*/-")
_BLOCK_COMMENT_CLOSE_TOKEN = "-/"


def _scan_skipping_comments(lines: List[str], i: int) -> int:
    """Advance i past blank lines, line comments, and well-formed block
    comments. Returns the new index. Conservative: a malformed unterminated
    block comment terminates the scan at the same line."""
    while i < len(lines):
        line = lines[i]
        if _BLANK_RE.match(line) or _LINE_COMMENT_RE.match(line):
            i += 1
            continue
        if _BLOCK_COMMENT_OPEN_RE.match(line):
            # Find matching -/
            if _BLOCK_COMMENT_CLOSE_TOKEN in line[line.index("/-") + 2:]:
                i += 1
                continue
            j = i + 1
            while j < len(lines) and _BLOCK_COMMENT_CLOSE_TOKEN not in lines[j]:
                j += 1
            if j == len(lines):
                return i  # unterminated; bail
            i = j + 1
            continue
        return i
    return i


def parse_imports(file_path: Path) -> Tuple[List[str], int]:
    """Return (import_lines, line_after_imports_1indexed).

    Reads from the top of `file_path`, skipping leading blank/comment lines,
    then collects the contiguous `import ...` block. Stops at the first
    non-import non-blank-non-comment line. Assumes Mathlib convention: imports
    are contiguous at the file head (after copyright)."""
    lines = file_path.read_text().splitlines()
    i = _scan_skipping_comments(lines, 0)
    imports: List[str] = []
    while i < len(lines):
        if _IMPORT_RE.match(lines[i]):
            imports.append(lines[i])
            i += 1
            continue
        # Blank lines or comments interleaved with imports are tolerated
        if _BLANK_RE.match(lines[i]) or _LINE_COMMENT_RE.match(lines[i]):
            i += 1
            continue
        break
    return imports, i + 1  # 1-indexed line number after the import block


def extract_prefix_full(file_path: Path, L: int) -> str:
    """F lines 1..L-1 with the leading import block stripped.

    Imports are emitted separately (as the standalone `imports` field on a
    Target); leaving them in F's prefix would create duplicates in the
    verifier file. The returned text starts at the first non-import,
    non-blank, non-pure-comment line (or the line right after the last
    import, whichever comes first).
    """
    lines = file_path.read_text().splitlines()
    if L <= 1:
        return ""
    _, after_imports = parse_imports(file_path)
    start_idx = after_imports - 1  # 0-indexed line index where prefix begins
    # F lines 1..L-1 in 1-indexed terms = 0..L-2 in 0-indexed slice
    end_idx = L - 1  # exclusive
    if start_idx >= end_idx:
        return ""
    return "\n".join(lines[start_idx:end_idx])


# ---------- scope-only prefix extraction ----------

# Lines that affect Lean's elaboration scope and should be kept.
_SCOPE_HEADS = (
    "namespace ", "namespace\n",
    "section", "noncomputable section",
    "open ", "open\n",
    "variable ", "variable\n",
    "universe ", "universes ",
    "set_option ",
    "end",
    "local notation", "local infix", "local prefix", "local postfix",
    "local syntax", "local macro_rules",
    "scoped notation", "scoped infix", "scoped prefix", "scoped postfix",
)

# Lines that begin a *content* declaration (to be dropped).
_CONTENT_HEADS = (
    "theorem ", "lemma ", "def ", "instance ", "instance:",
    "structure ", "inductive ", "class ", "abbrev ", "example ", "example:",
    "axiom ", "opaque ", "attribute ",
)

_MODIFIER_PREFIXES = (
    "private ", "protected ", "scoped ",
    "unsafe ", "partial ", "mutual ",
    "noncomputable ",
)


def _column0_kind(line: str) -> str:
    """Classify a line that starts at column 0 (no leading whitespace).
    Returns one of: scope, content, attr, doc_open, block_comment_open,
    line_comment, admin, import, empty, unknown."""
    stripped = line.rstrip()
    if not stripped.strip():
        return "empty"
    if stripped.startswith("--"):
        return "line_comment"
    if stripped.startswith("/--"):
        return "doc_open"
    if stripped.startswith("/-"):
        return "block_comment_open"
    if stripped.startswith("@["):
        return "attr"
    if stripped.startswith("#"):
        return "admin"
    if stripped.startswith("import "):
        return "import"

    # Strip modifiers to find the base keyword
    s = stripped
    while True:
        for m in _MODIFIER_PREFIXES:
            if s.startswith(m):
                s = s[len(m):].lstrip()
                break
        else:
            break

    # `noncomputable section` is scope; `noncomputable def ...` was already
    # stripped by the modifier loop above (so s now starts with "def ").
    # But the unstripped "noncomputable section" exits the loop with s
    # starting with "section" — we handle it below.

    if s.startswith("section") and (len(s) == len("section") or not s[len("section")].isalnum()):
        return "scope"
    if s.startswith("end") and (len(s) == len("end") or not s[len("end")].isalnum()):
        return "scope"

    for h in _SCOPE_HEADS:
        if s.startswith(h):
            return "scope"
    for h in _CONTENT_HEADS:
        if s.startswith(h):
            return "content"
    return "unknown"


def extract_prefix_scope_only(file_path: Path, L: int) -> str:
    """Subset of `extract_prefix_full` that keeps only scope-affecting lines.

    Drops:
      - all theorem/lemma/def/instance/structure/inductive/class/abbrev/
        example/axiom/opaque/attribute declarations and their bodies
      - `@[...]` attribute markers and the declaration they modify
      - `/-- ... -/` doc-comment blocks (and the declaration they document)
      - `/- ... -/` non-doc block comments
      - `--` line comments
      - `#align_import`, `#check`, `#eval`, `#print` admin directives
      - `import` lines (already emitted in the imports field)
    Keeps:
      - `namespace`/`section`/`noncomputable section`/`end` directives
      - `open`/`variable`/`universe`/`set_option`
      - `local notation`/`infix`/`prefix`/`postfix`/`syntax`
    """
    full = extract_prefix_full(file_path, L)
    if not full:
        return ""
    lines = full.splitlines()
    out: List[str] = []
    skip_next_block = False  # set when we hit attr or doc — drop the decl that follows
    in_block_comment = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if in_block_comment:
            if _BLOCK_COMMENT_CLOSE_TOKEN in line:
                in_block_comment = False
            i += 1
            continue

        # Continuation lines (indented or blank) belong to the previous block
        if _BLANK_RE.match(line):
            # Emit blank lines only if we're NOT mid-skip
            if not skip_next_block:
                out.append(line)
            i += 1
            continue
        if line and line[0].isspace():
            # Indented continuation of the previous block — emit only if we
            # decided to keep that block. Track via skip_next_block: if it's
            # set, we're skipping, so drop. Otherwise, the previous block
            # was kept (scope), and indented continuation should be kept too.
            if not skip_next_block:
                out.append(line)
            i += 1
            continue

        # Column-0, non-empty: start of a new logical block.
        kind = _column0_kind(line)
        if kind in ("import", "admin", "line_comment"):
            skip_next_block = False
            i += 1
            continue
        if kind == "block_comment_open":
            # Drop the comment; don't drop a following declaration.
            if _BLOCK_COMMENT_CLOSE_TOKEN in line[line.index("/-") + 2:]:
                pass  # closed on same line
            else:
                in_block_comment = True
            skip_next_block = False
            i += 1
            continue
        if kind == "doc_open":
            # Drop the doc and the declaration it documents.
            if _BLOCK_COMMENT_CLOSE_TOKEN in line[line.index("/--") + 3:]:
                pass
            else:
                in_block_comment = True
            skip_next_block = True
            i += 1
            continue
        if kind == "attr":
            # Attr applies to the next declaration; skip the attr and keep the
            # skip flag set to drop the decl too.
            skip_next_block = True
            i += 1
            continue
        if kind == "content":
            skip_next_block = True
            i += 1
            continue
        if kind == "scope":
            out.append(line)
            skip_next_block = False
            i += 1
            continue
        # Unknown: be conservative and emit, unless we're in skip mode
        if not skip_next_block:
            out.append(line)
        i += 1

    # Collapse runs of >2 blank lines to one
    collapsed: List[str] = []
    blank_run = 0
    for ln in out:
        if not ln.strip():
            blank_run += 1
            if blank_run <= 1:
                collapsed.append("")
        else:
            blank_run = 0
            collapsed.append(ln)
    # Trim trailing blanks
    while collapsed and not collapsed[-1].strip():
        collapsed.pop()
    return "\n".join(collapsed)


# ---------- namespace stack + local-name resolution ----------

_NAMESPACE_RE = re.compile(r"^\s*namespace\s+(\S+)")
_SECTION_RE = re.compile(r"^\s*section(?:\s+(\S+))?\s*$")
_END_RE = re.compile(r"^\s*end(?:\s+(\S+))?\s*$")

# Stack entry: (kind, segment). kind ∈ {"ns", "sec"}. Sections don't
# contribute to qualified names but DO consume `end` directives, so we
# track them so an anonymous `end` doesn't accidentally close a namespace.


def _push_namespace(stack: List[Tuple[str, str]], dotted: str) -> None:
    """`namespace A.B` ≡ `namespace A; namespace B`. Push each segment
    so `end B` closes only the inner one."""
    for segment in dotted.split("."):
        stack.append(("ns", segment))


def _pop_end(stack: List[Tuple[str, str]], name: Optional[str]) -> None:
    """`end` (no name) pops the top, regardless of kind. `end A.B` pops
    matching `ns` segments right-to-left."""
    if name is None:
        if stack:
            stack.pop()
        return
    segments = name.split(".")
    for seg in reversed(segments):
        if stack and stack[-1] == ("ns", seg):
            stack.pop()
        elif stack and stack[-1][0] == "sec" and stack[-1][1] == seg:
            stack.pop()
        else:
            return  # mismatch — bail


def namespace_stack_at(file_path: Path, L: int) -> List[str]:
    """Active *namespace* stack at line L (1-indexed). Each entry is one
    namespace segment. Sections are tracked internally so `end` doesn't
    accidentally pop a namespace, but section names are not returned —
    they don't contribute to qualified declaration names."""
    if L <= 1:
        return []
    lines = file_path.read_text().splitlines()
    stack: List[Tuple[str, str]] = []
    in_block_comment = False
    for line in lines[:L - 1]:
        if in_block_comment:
            if _BLOCK_COMMENT_CLOSE_TOKEN in line:
                in_block_comment = False
            continue
        s = line.strip()
        if not s:
            continue
        if s.startswith("/-") and _BLOCK_COMMENT_CLOSE_TOKEN not in s[2:]:
            in_block_comment = True
            continue
        if s.startswith("--"):
            continue
        m = _NAMESPACE_RE.match(line)
        if m:
            _push_namespace(stack, m.group(1))
            continue
        m = _SECTION_RE.match(line)
        if m:
            stack.append(("sec", m.group(1) or ""))
            continue
        m = _END_RE.match(line)
        if m:
            _pop_end(stack, m.group(1))
            continue
    return [seg for (kind, seg) in stack if kind == "ns"]


def local_name(full_name: str, file_path: Path, L: int) -> str:
    """Strip the deepest matching namespace prefix from `full_name`, given
    the active namespace stack at line L."""
    stack = namespace_stack_at(file_path, L)
    for k in range(len(stack), 0, -1):
        prefix = ".".join(stack[:k]) + "."
        if full_name.startswith(prefix):
            return full_name[len(prefix):]
    return full_name
