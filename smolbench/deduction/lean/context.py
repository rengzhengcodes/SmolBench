"""Render context rungs along the `stepk`, `hint`, and `noise` chains.

- `stepk:0..2` adds *step-k* information with no answer-conditional content;
  cumulative (`stepk:n` includes `stepk:0..n-1`).
- `hint:0..4` adds *answer-conditional* detail about the premises the *true*
  next tactic uses; cumulative, on a `stepk:2` baseline.
- `noise:N` is `hint:(N-1)` whitespace-padded to `hint:N`'s exact token
  count — the length control for the hint chain.

`stepk:*` and `hint:0` build from a `BenchmarkTheorem` alone; `hint:1+` needs
a premise-body lookup against the premise corpus (see `.premises`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .corpus import BenchmarkTheorem

Chain = Literal["stepk", "hint", "noise"]

# `_MAX_LEVEL` bounds `validate`'s (chain, level) range check, per chain:
#
# - "stepk" caps at 2. `_render_stepk_parts` only defines levels 0 (bare
#   goal), 1 (+ full tactic state), and 2 (+ proof-so-far + theorem
#   identity). There is no level 3+ to render.
# - "hint" caps at 9. `_render_hint_parts` defines levels 0 (premise
#   names), 1 (+ signatures), 2 (+ full bodies with proofs), and 3+ as a
#   transitive premise-dependency closure whose *hop count* is `level -
#   2` (hint:3 = 1-hop, hint:4 = 2-hop, ..., hint:9 = 7-hop -- see
#   `_render_hint_parts`'s `depth = level - 2`). This deliberately extends
#   well past the range `notebooks/deduction/README.md` documents and
#   sweep-tests (hint:0..4). Nothing in the renderer actually breaks past
#   hint:4, since `_HINT2_3_TOKEN_CAP` (50k tokens) already bounds the
#   rendered text no matter how many hops the closure walks. A caller
#   experimenting with deeper hops just hits earlier truncation (more
#   content discovered, none of it rendered) rather than an error. The cap
#   exists to keep `validate` a real bound, rather than removing
#   range-checking outright, without artificially restricting
#   experimentation to the currently used levels.
# - "noise" caps at 9 to mirror "hint". `_render_noise_parts(level)`
#   renders `_render_hint_parts` at both `level - 1` and `level` to find
#   the exact token count a whitespace pad must hit, so it needs the same
#   level range "hint" supports.
_MAX_LEVEL: dict[str, int] = {"stepk": 2, "hint": 9, "noise": 9}


# ---------------------------------------------------------------------------
# Goal-state parsing
# ---------------------------------------------------------------------------


def split_state(state_pp: str) -> tuple[str, str]:
    """Return `(hypotheses, goals)` from a Lean tactic-state pretty-print.

    `goals` starts at the first `⊢` line, with any preceding `case ...`
    headers attached. A state with no `⊢` line yields `(state_pp, "")`.
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
    """One rendered (chain, level) context rung.

    Returned by `render`; `prompt.build_user_prompt` consumes `text`, and every
    result row records `label` as the cell's ``rung``.
    """

    #: Which chain this rung belongs to.
    chain: Chain
    #: The rung's level within `chain`.
    level: int
    #: The fully-assembled prompt-context text for this rung: the
    #: chain-specific parts, blank-line-joined by `render`.
    text: str

    @property
    def label(self) -> str:
        """This rung's canonical ``"<chain>:<level>"`` identifier, e.g. ``"hint:2"``.

        The single ``":"`` is a wire contract: `cli.py`'s ``--rung`` and
        `runner.py`'s sweep-config ``rungs`` split on it to recover
        ``(chain, level)``; `runner.slug_rung` swaps it for ``"-"`` in paths.
        """
        return f"{self.chain}:{self.level}"


# ---------------------------------------------------------------------------
# Per-chain rendering (cumulative within each chain)
# ---------------------------------------------------------------------------


def _render_stepk_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """Cumulative `stepk:0..level`, for `level` in {0,1,2}."""
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
# Noise (whitespace) padding — control arm for hint:3 / hint:4
# ---------------------------------------------------------------------------


def _count_tokens(s: str) -> int:
    """Token count of `s`: `tiktoken` ``cl100k_base``, else ``len(s) // 4``.

    The module's only token counter, and already an approximation of the
    prompted model's tokenizer. Approximate suffices for `_render_hint_parts`'s
    hint:3+ budget and `is_trivial_rung`, but the char-based fallback makes
    `_render_noise_parts`'s exact-token padding unsatisfiable — it raises.
    """
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(s))
    except Exception:  # noqa: BLE001
        return len(s) // 4


class _TokenCounter:
    """Adapt `_count_tokens` to the interface the pad search expects.

    `smolbench.induction._common`'s token-matching search needs `count()` and
    `name`. Ad hoc rather than `smolbench.evals.tokenization.Tokenizer`, a
    duck-typed `Protocol`: this module must not depend on `smolbench.evals`
    (see `_render_noise_parts`'s Notes).
    """

    #: Identifies which counter is in play, in
    #: `token_matched_noise_prompt`'s `ValueError` messages (e.g. "no
    #: whitespace unit costs ~1 token per repetition under tokenizer
    #: ..."). Nothing else consumes this attribute.
    name = "smolbench.deduction.lean.context._count_tokens (tiktoken cl100k_base, or len//4 fallback)"

    def count(self, text: str) -> int:
        """`_count_tokens(text)`, under the name the search helper calls."""
        return _count_tokens(text)


def _render_noise_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """`noise:N` = `hint:(N-1)` whitespace-padded to `hint:N`'s exact token count.

    The length control for the hint chain: both rungs cost identical tokens, so
    only `hint:N`'s marginal *content* differs. The pad is appended to the LAST
    part's text, never as a new list element — `render()` joins parts with
    ``"\\n\\n"``, and a new element would add a separator the token search never
    measured. A baseline already equal to the target (a trivial rung, see
    `is_trivial_rung`) returns unchanged: `render()` still calls this under
    ``skip_trivial: false``, so that case must not raise.

    Raises
    ------
    ValueError
        `level < 1` (the `hint:0`/`stepk:2` baseline has no noise counterpart);
        the `hint:(level - 1)` baseline is LONGER in tokens than the
        `hint:level` target, since whitespace can only grow a rendering and
        under-padding would reintroduce the length confound;
        `choose_whitespace_unit` finds no unit costing ~1 token per repetition,
        which is what `_count_tokens`'s ``len(s) // 4`` fallback causes; or the
        pad misses the target.

    Notes
    -----
    The pad search is `smolbench.induction._common.token_matched_noise_prompt`,
    reused so the two benchmarks' padding cannot drift apart; its import is LAZY
    because that module pulls in `numpy`/`ordered_set`/`smolbench.evals` and
    `runner.py` imports this module at top level. The pad is pure whitespace —
    prose or a header would be content the paired `hint:N` rung lacks. The
    result is re-verified here because the helper can fall back to returning an
    unpadded render with only a warning.
    """
    if level < 1:
        raise ValueError(f"noise:{level} not defined; only noise:1+ supported")

    # Lazy import -- see this function's Notes for why
    # `smolbench.induction._common` must not be pulled in at module top.
    from smolbench.induction._common import choose_whitespace_unit, token_matched_noise_prompt

    base_parts = _render_hint_parts(theorem, k, level - 1)
    base_text = "\n\n".join(base_parts)
    base_tokens = _count_tokens(base_text)

    target_text = "\n\n".join(_render_hint_parts(theorem, k, level))
    target_tokens = _count_tokens(target_text)

    if base_tokens > target_tokens:
        raise ValueError(
            f"noise:{level} baseline (hint:{level - 1}, {base_tokens} tokens) is "
            f"LONGER than its hint:{level} target ({target_tokens} tokens) for "
            f"{theorem.full_name!r} at k={k} -- a whitespace pad can only grow "
            "a rendering, never shrink one, so this rung cannot be built as a "
            "length control"
        )
    if base_tokens == target_tokens:
        # Already exact: nothing to pad. This case is real and common:
        # every rung where hint:level adds nothing over hint:(level - 1)
        # hits it, and `is_trivial_rung` independently reports those as
        # trivial. `render()` still calls this on trivial noise rungs
        # when a sweep sets `skip_trivial: false`, so this must return
        # cleanly, not raise.
        return base_parts

    counter = _TokenCounter()
    padded_text = token_matched_noise_prompt(
        lambda pad: base_text + pad,  # render: pad string -> full rendered text
        "",  # context: empty -- the pad IS the whole variable part being searched
        target_tokens,
        counter,
        unit=choose_whitespace_unit(counter),
    )

    # Belt-and-braces (see Notes): this verifies exactness itself, rather
    # than trusting the helper's own internal verification blindly.
    padded_tokens = _count_tokens(padded_text)
    if padded_tokens != target_tokens:
        raise ValueError(
            f"noise:{level} padding for {theorem.full_name!r} at k={k} did not "
            f"hit the exact target: got {padded_tokens} tokens, wanted "
            f"{target_tokens}"
        )

    pad = padded_text[len(base_text):]
    return base_parts[:-1] + [base_parts[-1] + pad]


def _render_hint_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """`hint:0..level` on a `stepk:2` baseline; `level` 0..9, sweep-tested 0..4."""
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
    """Check that `(chain, level)` names an in-range rung.

    Raises
    ------
    ValueError
        `chain` is not a `_MAX_LEVEL` key, or `level` is outside
        ``[0, _MAX_LEVEL[chain]]``. Narrower per-chain constraints are not
        applied, so ``noise:0`` passes here and `_render_noise_parts`
        rejects it later.
    """
    if chain not in _MAX_LEVEL:
        raise ValueError(f"unknown chain: {chain!r}")
    hi = _MAX_LEVEL[chain]
    if not 0 <= level <= hi:
        raise ValueError(f"{chain} level must be 0..{hi}; got {level}")


def render(theorem: BenchmarkTheorem, k: int, chain: Chain, level: int) -> RenderedContext:
    """Render context at proof step `k` of `theorem` for the given (chain, level).

    Parameters
    ----------
    k : int
        0-indexed step about to be proved, in ``[0, len(traced_tactics))``: the
        context describes the state immediately before
        ``theorem.traced_tactics[k]``, and the model is expected to produce the
        tail starting at that tactic.
    chain, level : Chain, int
        Rung to render; checked by `validate`.

    Returns
    -------
    RenderedContext
        `chain`/`level` echoed back, with `text` = the chain-specific parts
        joined by blank lines.

    Raises
    ------
    ValueError
        `k` out of range; `(chain, level)` rejected by `validate`; or --
        for ``noise`` -- propagated from `_render_noise_parts` (notably
        ``noise:0``, which `validate` allows through).
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


# Canonical default rung universe. hint:N for N≥3 is a (N−2)-hop
# transitive closure. Depths up to 9 are runnable, but hit the 50k token
# cap by depth ~5-6 in mathlib, since the per-premise dependency graph
# fans out fast.
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

    Skipping these cells keeps per-rung pass rates apples-to-apples: every
    counted cell saw a real context expansion. Trivial when:

      - `stepk:1` and the state has no hypotheses (same as stepk:0);
      - `hint:*` and no premises are recorded for the next tactic;
      - `hint:1` and the corpus has no record for any true premise;
      - `hint:2` and no premise's body differs from its signature;
      - `hint:3+` and the closure at that hop depth is empty;
      - `noise:N` and `hint:N` is trivial or adds no tokens over `hint:(N-1)`.

    `stepk:0` and `stepk:2` are never trivial (stepk:2 adds theorem identity
    even at k=0). Only caller is `runner.sweep`, gated by ``skip_trivial``.

    Returns
    -------
    bool
        True if the rung is trivial. False -- not an exception -- for an
        unrecognized `chain` or an out-of-range `k`, so the cell still runs
        instead of being silently dropped.
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
            # stepk:2 adds theorem identity even at k=0, so it is never
            # trivial.
            return False
        return False

    if chain == "hint":
        # Without recorded premises, the entire hint chain collapses:
        # hint:0 would just say "(none recorded)", and 1+ have nothing to
        # elaborate.
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
        # Trivial when the matching hint rung is trivial, or when there
        # is nothing to pad (hint:N's text length ≤ hint:(N-1)'s).
        if level < 1:
            return True
        if is_trivial_rung(theorem, k, "hint", level):
            return True
        base_text = "\n\n".join(_render_hint_parts(theorem, k, level - 1))
        target_text = "\n\n".join(_render_hint_parts(theorem, k, level))
        return _count_tokens(target_text) - _count_tokens(base_text) <= 0
    return False
