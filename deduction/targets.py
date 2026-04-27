"""Target dataclass + builder.

A `Target` carries everything `prompt.py` and `lean_file.py` need to assemble
the LLM view and the Lean verification view for a single Mathlib theorem.
Pure data: builders here don't touch the network or the verifier.

The replay-passing pool (which `runner.py` actually iterates over) is built
in `filter.py` by submitting each candidate's canonical proof through the
local Kimina server and keeping only those that verify cleanly.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, Tuple

from deduction.corpus import (
    MATHLIB_DIR,
    Premise,
    extract_prefix_full,
    extract_prefix_scope_only,
    local_name,
    parse_imports,
)


@dataclass(frozen=True, slots=True)
class Target:
    full_name: str
    local_name: str
    sig_text: str                         # binders + return type, no `theorem` keyword, no `:=`
    tactics: Tuple[str, ...]              # canonical proof, one entry per traced_tactic
    premise_refs_per_tactic: Tuple[Tuple[str, ...], ...]  # full_names referenced in each tactic
    file_path: str                        # repo-relative
    start_line: int                       # L, 1-indexed
    imports: Tuple[str, ...]              # F's literal `import ...` lines verbatim
    f_prefix_full: str                    # F lines 1..L-1 with leading imports stripped
    f_prefix_scope_only: str              # scope-affecting subset of f_prefix_full


# ---------- signature extraction ----------

_ATTR_PREFIX_RE = re.compile(r"^\s*@\[[^\]]*\]\s*")
_MODIFIER_PREFIX_RE = re.compile(
    r"^(?:\s*(?:noncomputable|private|protected|scoped|unsafe|partial|mutual)\s+)+"
)
_DECL_HEAD_KEYWORDS = ("theorem", "lemma", "def", "instance", "abbrev", "axiom", "opaque")


def _strip_attrs_and_modifiers(s: str) -> str:
    while True:
        m = _ATTR_PREFIX_RE.match(s)
        if not m:
            break
        s = s[m.end():]
    s = _MODIFIER_PREFIX_RE.sub("", s)
    return s


def _split_at_top_level_assign(code: str) -> str:
    """Return prefix of `code` up to the first top-level `:=`, where
    'top-level' means outside `[...]` brackets. If no `:=` is found, return
    the whole string."""
    depth = 0
    i = 0
    while i < len(code) - 1:
        c = code[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
        elif depth == 0 and c == ":" and code[i + 1] == "=":
            return code[:i]
        i += 1
    return code


def extract_signature(corpus_code: str, local_decl_name: str) -> str:
    """Extract binders + return type from a corpus `code` field.

    Strips, in order: leading `@[...]` attribute blocks, leading
    declaration modifiers, the `theorem|lemma|def|... <local>` head, and any
    trailing `:= <body>`. The result is the bare signature (binders +
    `:` + return type).
    """
    s = _strip_attrs_and_modifiers(corpus_code)
    pattern = (
        r"^\s*(?:" + "|".join(_DECL_HEAD_KEYWORDS) + r")\s+"
        + re.escape(local_decl_name)
    )
    m = re.match(pattern, s)
    if m:
        s = s[m.end():].lstrip()
    s = _split_at_top_level_assign(s)
    return s.rstrip()


# ---------- candidate enumeration + Target build ----------

def candidate_full_names(
    corpus: Dict[str, Premise],
    traced_lookup: Dict[str, list],
) -> Iterator[str]:
    """Yield full_names eligible as evaluation targets.

    Eligibility: (1) indexed in corpus, (2) has traced_tactics in some split,
    (3) lives in a `Mathlib/...` source file (so we can read its prefix and
    declaration body from the local clone). The replay-passing filter is
    applied separately by `filter.py`.
    """
    for name, p in corpus.items():
        if name not in traced_lookup:
            continue
        if not p.file_path.startswith("Mathlib/"):
            continue
        yield name


def build_target(
    full_name: str,
    corpus: Dict[str, Premise],
    traced_lookup: Dict[str, list],
    mathlib_dir: Path = MATHLIB_DIR,
) -> Target:
    """Construct a Target from corpus + traced_lookup. Reads F's source from
    `mathlib_dir / file_path`. No network I/O."""
    p = corpus[full_name]
    f_path = mathlib_dir / p.file_path
    L = p.start[0]

    ln = local_name(full_name, f_path, L)
    sig = extract_signature(p.corpus_code, ln)

    traced = traced_lookup.get(full_name, [])
    tactics = tuple(t["tactic"] for t in traced)
    premise_refs_per_tactic = tuple(
        tuple(
            ref["full_name"]
            for ref in t.get("annotated_tactic", [None, []])[1]
            if ref.get("full_name")
        )
        for t in traced
    )

    imports, _ = parse_imports(f_path)
    f_prefix_full = extract_prefix_full(f_path, L)
    f_prefix_scope_only = extract_prefix_scope_only(f_path, L)

    return Target(
        full_name=full_name,
        local_name=ln,
        sig_text=sig,
        tactics=tactics,
        premise_refs_per_tactic=premise_refs_per_tactic,
        file_path=p.file_path,
        start_line=L,
        imports=tuple(imports),
        f_prefix_full=f_prefix_full,
        f_prefix_scope_only=f_prefix_scope_only,
    )
