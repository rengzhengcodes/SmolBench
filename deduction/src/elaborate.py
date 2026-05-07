"""Knob B: BFS premise expansion.

Given a `Target` and visible-tactic count K, produce the per-tactic blocks of
rendered premise declarations that populate the `# Relevant premises` section
of the LLM view.

Per DESIGN.md:
  - `P_0` = direct premises referenced in `t_1..t_K` (from
    `target.premise_refs_per_tactic[:K]`).
  - `P_b` = `P_{b-1}` plus premises referenced in declarations of `P_{b-1}`,
    discovered via `traced_lookup`.
  - Mathlib-only filter: premises in `Init`/`Batteries`/etc. dropped.
  - Premises with no corpus entry: dropped + counted (typically `def`s,
    instance projections, alias-introduced names).
  - Per-tactic block, ordered reverse-BFS (deepest first; siblings in
    first-seen order).
  - Cross-block dedup: a premise that appeared in an earlier tactic's block
    is skipped in later blocks. If a block becomes empty after dedup, no
    header or marker is emitted.
  - Each declaration rendered with `@[...]` attribute lines included
    (backward expansion) and `/-- ... -/` doc comments stripped.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .corpus import (
    MATHLIB_DIR,
    Premise,
    extract_premise_refs_from_text,
    read_source_with_attrs,
    strip_docstring,
)
from .targets import Target


@dataclass
class Elaboration:
    blocks: List[List[str]] = field(default_factory=list)
    skipped_no_corpus: List[str] = field(default_factory=list)
    skipped_non_mathlib: List[str] = field(default_factory=list)


def _render_premise(p: Premise) -> str:
    """Read p's source text with attribute backward-expansion and strip
    docstrings. Returns the cleaned declaration body."""
    src = read_source_with_attrs(MATHLIB_DIR / p.file_path, p.start, p.end)
    return strip_docstring(src).strip()


def expand_premises(
    target: Target,
    K: int,
    B: int,
    corpus: Dict[str, Premise],
    traced_lookup: Dict[str, list],
) -> Elaboration:
    """Return per-tactic premise blocks for the LLM view at coordinate (K, B).

    `K` is the visible-tactic count (the first K tactics of the canonical
    proof). `B` is the BFS depth. B=0 returns an empty `blocks` list; B=1
    returns one block per tactic with that tactic's direct premises; B>=2
    walks the premise graph through `traced_lookup`."""
    if not (0 <= K <= len(target.tactics)):
        raise ValueError(f"K={K} out of range [0, {len(target.tactics)}]")
    if B < 0:
        raise ValueError(f"B={B} must be >= 0")

    result = Elaboration()
    if B == 0 or K == 0:
        # No premises shown
        result.blocks = [[] for _ in range(K)]
        return result

    seen_global: set[str] = set()  # cross-block dedup

    for i in range(K):
        # Layered BFS for this tactic: layers[d-1] = premises at depth d.
        # We collect all layers, then emit reversed (deepest first).
        layers: List[List[str]] = []
        seen_in_walk: set[str] = set()
        frontier = list(target.premise_refs_per_tactic[i])

        for depth in range(1, B + 1):
            this_layer: List[str] = []
            for name in frontier:
                if name in seen_in_walk:
                    continue
                seen_in_walk.add(name)
                if name not in corpus:
                    if name not in result.skipped_no_corpus:
                        result.skipped_no_corpus.append(name)
                    continue
                if not corpus[name].file_path.startswith("Mathlib/"):
                    if name not in result.skipped_non_mathlib:
                        result.skipped_non_mathlib.append(name)
                    continue
                this_layer.append(name)
            layers.append(this_layer)

            if depth == B:
                break

            # Build next frontier from this layer's children (premises
            # referenced inside each premise's own canonical proof).
            #
            # First try LeanDojo's annotated premise refs (precise, post-
            # type-inference). If a premise has no traced_tactics (term-mode
            # body, e.g., `:= rfl` or `:= some_lemma.trans other`), fall
            # back to regex-extracting Mathlib-resident identifier tokens
            # from its source body.
            next_frontier: List[str] = []
            for name in this_layer:
                children: List[str] = []
                for ct in traced_lookup.get(name, []):
                    for ref in ct.get("annotated_tactic", [None, []])[1]:
                        cn = ref.get("full_name") if isinstance(ref, dict) else None
                        if cn:
                            children.append(cn)
                if not children:
                    # Term-mode fallback: parse the premise's source body
                    p = corpus[name]
                    text = read_source_with_attrs(MATHLIB_DIR / p.file_path, p.start, p.end)
                    text = strip_docstring(text)
                    children = extract_premise_refs_from_text(text, corpus)
                for cn in children:
                    if cn not in seen_in_walk:
                        next_frontier.append(cn)
            frontier = next_frontier
            if not frontier:
                break

        # Emit reverse-BFS (deepest first), with cross-block dedup.
        block: List[str] = []
        for layer in reversed(layers):
            for name in layer:
                if name in seen_global:
                    continue
                seen_global.add(name)
                rendered = _render_premise(corpus[name])
                if rendered:
                    block.append(rendered)
        result.blocks.append(block)

    return result
