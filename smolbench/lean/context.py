"""Render context rungs along the `stepk` and `hint` chains.

Two chains:
- `stepk:0..2` — progressively more *step-k* information, no answer-conditional
  content. Cumulative: stepk:n includes stepk:0..n-1.
- `hint:0..4` — progressively more *answer-conditional* detail about the
  premises used in the *true* next tactic. Cumulative within the chain, and
  every hint rung includes `stepk:2` as its baseline.

`stepk:0..2` and `hint:0` are implemented from a BenchmarkTheorem alone.
`hint:1..4` need premise-body lookup against `corpus.jsonl` and are stubbed for
Phase 3.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .corpus import BenchmarkTheorem

Chain = Literal["stepk", "hint", "noise"]

# hint:N for N >= 3 is (N-2)-hop transitive premise closure. 50k token cap
# means deeper levels just hit truncation rather than producing more content.
# Cap chains generously so callers can experiment with depth.
_MAX_LEVEL: dict[str, int] = {"stepk": 2, "hint": 9, "noise": 9}


# ---------------------------------------------------------------------------
# Goal-state parsing
# ---------------------------------------------------------------------------


def split_state(state_pp: str) -> tuple[str, str]:
    """Return `(hypotheses, goals)` from a Lean tactic-state pretty-print.

    A state pp typically looks like:
        F : Type u_1
        ...
        hs : s ⊆ range ↑m
        ⊢ s / t ⊆ range ↑m
    `goals` is the substring starting at the first line beginning with `⊢ `.
    Multi-goal states (`case ... ⊢ ...` blocks) keep their `case ...` headers
    attached to the goal block.
    """
    lines = state_pp.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("⊢"):
            goal_start = i
            while goal_start > 0 and lines[goal_start - 1].lstrip().startswith("case "):
                goal_start -= 1
            return "\n".join(lines[:goal_start]).rstrip(), "\n".join(lines[goal_start:]).rstrip()
    return state_pp.rstrip(), ""


def extract_goal_only(state_pp: str) -> str:
    """`stepk:0` helper: drop hypotheses, keep only the goal block."""
    _, goals = split_state(state_pp)
    return goals or state_pp


# ---------------------------------------------------------------------------
# Rendered context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RenderedContext:
    chain: Chain
    level: int
    text: str

    @property
    def label(self) -> str:
        return f"{self.chain}:{self.level}"


# ---------------------------------------------------------------------------
# Per-chain rendering (cumulative within each chain)
# ---------------------------------------------------------------------------


def _render_stepk_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """Cumulative `stepk:0..level`. `level` in {0,1,2}."""
    tt = theorem.traced_tactics[k]
    parts: list[str] = [
        f"## Current goal\n```\n{extract_goal_only(tt.state_before)}\n```"
    ]
    if level >= 1:
        parts.append(f"## Full tactic state\n```\n{tt.state_before}\n```")
    if level >= 2:
        prior = theorem.traced_tactics[:k]
        if prior:
            tactics_block = "\n".join(t.tactic for t in prior)
            label = f"{k} tactic{'s' if k != 1 else ''}"
            parts.append(f"## Proof so far ({label})\n```lean\n{tactics_block}\n```")
        else:
            parts.append(
                "## Proof so far\n_(no tactics applied yet — this is the start of the proof)_"
            )
        parts.append(
            f"## Theorem\n`{theorem.full_name}` in `{theorem.file_path}`"
        )
    return parts


_HINT2_3_TOKEN_CAP = 50_000  # token budget for transitive closure rendering


# ---------------------------------------------------------------------------
# Noise (lorem-ipsum) padding — control arm for hint:3 / hint:4
# ---------------------------------------------------------------------------


_LOREM_PARAGRAPH = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim "
    "veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
    "commodo consequat. Duis aute irure dolor in reprehenderit in voluptate "
    "velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint "
    "occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
    "mollit anim id est laborum.\n\n"
)


def _generate_lorem(target_tokens: int) -> str:
    """Generate a lorem-ipsum string of approximately `target_tokens` tokens.

    Uses tiktoken cl100k_base for budgeting (close enough to the actual model
    tokenizer for an isolation test). Returns clean prose; pure whitespace
    would tokenize differently and not match hint:N token counts.
    """
    if target_tokens <= 0:
        return ""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tokens_per_para = len(enc.encode(_LOREM_PARAGRAPH))
        n_paras = max(1, (target_tokens // tokens_per_para) + 1)
        text = _LOREM_PARAGRAPH * n_paras
        # Trim to exact target by re-encoding/decoding.
        toks = enc.encode(text)
        if len(toks) > target_tokens:
            toks = toks[:target_tokens]
        return enc.decode(toks)
    except Exception:  # noqa: BLE001
        # Fallback: rough char-based estimate (~4 chars/token for English).
        target_chars = target_tokens * 4
        n_paras = max(1, target_chars // len(_LOREM_PARAGRAPH) + 1)
        return (_LOREM_PARAGRAPH * n_paras)[:target_chars]


def _count_tokens(s: str) -> int:
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(s))
    except Exception:  # noqa: BLE001
        return len(s) // 4


def _render_noise_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """`noise:N` = `hint:(N-1)` baseline + lorem padding sized to match `hint:N`.

    Each comparison `hint:N` vs `noise:N` isolates the marginal *content*
    added at step N (e.g. for noise:2: lorem-padded hint:1 = signatures plus
    filler vs hint:2 = signatures plus real premise bodies, both at the same
    token count).
    """
    if level < 1:
        raise ValueError(f"noise:{level} not defined; only noise:1+ supported")

    base_parts = _render_hint_parts(theorem, k, level - 1)
    base_text = "\n\n".join(base_parts)
    base_tokens = _count_tokens(base_text)

    target_text = "\n\n".join(_render_hint_parts(theorem, k, level))
    target_tokens = _count_tokens(target_text)

    delta = target_tokens - base_tokens
    if delta <= 0:
        return base_parts  # nothing to pad; rung is trivial

    filler = _generate_lorem(delta)
    base_parts.append(
        f"## Filler (hint:{level-1} → hint:{level} token-match, ≈{delta} tokens, "
        "no informational content)\n" + filler
    )
    return base_parts


def _render_hint_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """`hint:0..level` with `stepk:2` baseline. `level` in {0..4}."""
    parts = _render_stepk_parts(theorem, k, 2)

    tt = theorem.traced_tactics[k]
    names = [p["full_name"] for p in tt.premises]

    # hint:0 — bare premise names
    if names:
        block = "\n".join(f"- `{n}`" for n in names)
        parts.append(f"## Premises used in the next tactic\n{block}")
    else:
        parts.append("## Premises used in the next tactic\n_(none recorded)_")

    if level >= 1:
        from .premises import lookup, signature
        sigs: list[str] = []
        for n in names:
            p = lookup(n)
            if p is None:
                sigs.append(f"### `{n}`\n_(not found in premise corpus)_")
            else:
                sigs.append(
                    f"### `{n}` ({p.kind})\n```lean\n{signature(p)}\n```"
                )
        if sigs:
            parts.append("## Premise signatures\n" + "\n\n".join(sigs))

    if level >= 2:
        from .premises import lookup, body_with_proof
        bodies: list[str] = []
        for n in names:
            p = lookup(n)
            if p is None:
                bodies.append(f"### `{n}`\n_(not found in premise corpus)_")
            else:
                bodies.append(
                    f"### `{n}` ({p.kind}) at `{p.file_path}`\n```lean\n{body_with_proof(p)}\n```"
                )
        if bodies:
            parts.append("## Premise full source (with proof)\n" + "\n\n".join(bodies))

    if level >= 3:
        from .premises import body_with_proof, lookup, premise_dep_closure
        depth = level - 2  # hint:3 = 1-hop, hint:4 = 2-hop, hint:5 = 3-hop, ...
        seeds: list = []
        for n in names:
            p = lookup(n)
            if p is not None:
                seeds.append(p)
        if seeds:
            transitive_premises = premise_dep_closure(seeds, depth)
            try:
                import tiktoken
                enc = tiktoken.get_encoding("cl100k_base")

                def tok(s: str) -> int:
                    return len(enc.encode(s))
            except Exception:  # noqa: BLE001
                def tok(s: str) -> int:
                    return len(s) // 4

            chunks: list[str] = []
            used = 0
            n_kept = 0
            for p in transitive_premises:
                # Same content shape as hint:2 — full source incl. proof body.
                snippet = (
                    f"### `{p.full_name}` ({p.kind}) at `{p.file_path}`\n"
                    f"```lean\n{body_with_proof(p)}\n```"
                )
                cost = tok(snippet)
                if used + cost > _HINT2_3_TOKEN_CAP:
                    break
                chunks.append(snippet)
                used += cost
                n_kept += 1
            if chunks:
                parts.append(
                    f"## Transitive premise context ({depth}-hop, "
                    f"{n_kept}/{len(transitive_premises)} premises, ≈{used} tokens)\n"
                    + "\n\n".join(chunks)
                )
    return parts


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------


def validate(chain: Chain, level: int) -> None:
    if chain not in _MAX_LEVEL:
        raise ValueError(f"unknown chain: {chain!r}")
    hi = _MAX_LEVEL[chain]
    if not 0 <= level <= hi:
        raise ValueError(f"{chain} level must be 0..{hi}; got {level}")


def render(theorem: BenchmarkTheorem, k: int, chain: Chain, level: int) -> RenderedContext:
    """Render context at proof step `k` of `theorem` for the given (chain, level).

    `k` is the 0-indexed step we are about to prove (the LLM should produce the
    tail starting at tactic[k]). Requires `0 <= k < len(traced_tactics)`.
    """
    if not 0 <= k < len(theorem.traced_tactics):
        raise ValueError(f"k={k} out of range [0, {len(theorem.traced_tactics)})")
    validate(chain, level)

    if chain == "stepk":
        parts = _render_stepk_parts(theorem, k, level)
    elif chain == "hint":
        parts = _render_hint_parts(theorem, k, level)
    elif chain == "noise":
        parts = _render_noise_parts(theorem, k, level)
    else:
        raise ValueError(f"unknown chain {chain!r}")
    return RenderedContext(chain=chain, level=level, text="\n\n".join(parts))


# Canonical default rung universe. hint:N for N≥3 = (N−2)-hop transitive
# closure; depths up to 9 are runnable but will hit the 50k token cap by
# depth ~5-6 in mathlib (per-premise dep graph fans out fast).
IMPLEMENTED_RUNGS: tuple[tuple[Chain, int], ...] = (
    ("stepk", 0), ("stepk", 1), ("stepk", 2),
    ("hint", 0), ("hint", 1), ("hint", 2), ("hint", 3),
    ("noise", 1), ("noise", 2), ("noise", 3),
)


# ---------------------------------------------------------------------------
# Trivial-rung detection (skip cells where a rung adds no new information)
# ---------------------------------------------------------------------------


def is_trivial_rung(theorem: BenchmarkTheorem, k: int, chain: Chain, level: int) -> bool:
    """True iff this rung adds no informational content beyond the previous rung.

    Used to skip cells whose rung-up is a no-op:
      - `stepk:1` when the tactic state has no hypotheses (= same as stepk:0).
      - `stepk:2` when k=0 (no prior tactics; only adds theorem identity).
      - `hint:0` when no premises are recorded for the next tactic.
      - `hint:1` when the corpus has no record for any of the true premises.
      - `hint:2` when no premise's body differs from its signature.
      - `hint:3`/`hint:4` when seed files have no imports at the requested depth.

    Skipping these saves LLM tokens and makes per-rung pass rates a clean
    apples-to-apples comparison: every counted cell saw a real context
    expansion vs the previous rung.
    """
    if not 0 <= k < len(theorem.traced_tactics):
        return False
    tt = theorem.traced_tactics[k]

    if chain == "stepk":
        if level == 0:
            return False
        if level == 1:
            hyps, _ = split_state(tt.state_before)
            return not hyps.strip()
        if level == 2:
            # stepk:2 adds theorem identity even at k=0; never trivial.
            return False
        return False

    if chain == "hint":
        # Without recorded premises, the entire hint chain collapses (hint:0
        # would just say "(none recorded)" and 1+ have nothing to elaborate).
        if not tt.premises:
            return True
        if level == 0:
            return False
        from .premises import body_with_proof, lookup, signature
        premises = [lookup(p["full_name"]) for p in tt.premises]
        if level == 1:
            return all(p is None for p in premises)
        if level == 2:
            for p in premises:
                if p is not None and signature(p) != body_with_proof(p):
                    return False
            return True
        if level >= 3:
            from .premises import premise_dep_closure
            seeds = [p for p in premises if p is not None]
            return not premise_dep_closure(seeds, level - 2)
        return False
    if chain == "noise":
        # Trivial when the matching hint rung is trivial OR when there's
        # nothing to pad (hint:N's text length ≤ hint:(N-1)'s).
        if level < 1:
            return True
        if is_trivial_rung(theorem, k, "hint", level):
            return True
        base_text = "\n\n".join(_render_hint_parts(theorem, k, level - 1))
        target_text = "\n\n".join(_render_hint_parts(theorem, k, level))
        return _count_tokens(target_text) - _count_tokens(base_text) <= 0
    return False

# Full rung universe per the README.
ALL_RUNGS: tuple[tuple[Chain, int], ...] = (
    ("stepk", 0), ("stepk", 1), ("stepk", 2),
    ("hint", 0), ("hint", 1), ("hint", 2), ("hint", 3), ("hint", 4),
)
