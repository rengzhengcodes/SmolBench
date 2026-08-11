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

# `_MAX_LEVEL` bounds `validate`'s (chain, level) range check, per chain:
#
# - "stepk" caps at 2 because `_render_stepk_parts` only defines levels 0
#   (bare goal), 1 (+ full tactic state), and 2 (+ proof-so-far + theorem
#   identity) -- there is no level 3+ to render.
# - "hint" caps at 9. `_render_hint_parts` defines levels 0 (premise names),
#   1 (+ signatures), 2 (+ full bodies with proofs), and 3+ as a transitive
#   premise-dependency closure whose *hop count* is `level - 2` (hint:3 =
#   1-hop, hint:4 = 2-hop, ..., hint:9 = 7-hop -- see `_render_hint_parts`'s
#   `depth = level - 2`). This deliberately extends well past the
#   `notebooks/deduction/README.md`-documented, sweep-tested range (hint:0..4):
#   nothing in the renderer actually breaks past hint:4, since
#   `_HINT2_3_TOKEN_CAP` (50k tokens) already bounds the rendered text no
#   matter how many hops the closure walks -- so a caller experimenting
#   with deeper hops just hits earlier truncation (more content discovered,
#   none of it rendered) rather than an error. The cap exists to keep
#   `validate` a real bound rather than removing range-checking outright,
#   without artificially restricting experimentation to the currently-used
#   levels.
# - "noise" caps at 9 to mirror "hint": `_render_noise_parts(level)` renders
#   `_render_hint_parts` at both `level - 1` and `level` to find the exact
#   token count a whitespace pad must hit, so it needs the same level range
#   `hint` supports.
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
    """The rendered text for one (chain, level) context rung, plus its label.

    Returned by `render`; the text is consumed by prompt assembly
    (``smolbench.deduction.lean.prompt.build_user_prompt``), and `label` is recorded
    as the cell's ``rung`` in every result row (see
    ``smolbench.deduction.lean.runner.run_cell``).
    """

    #: Which chain this rung belongs to.
    chain: Chain
    #: The rung's level within `chain`.
    level: int
    #: The fully-assembled prompt-context text for this rung (the
    #: chain-specific parts, blank-line-joined by `render`).
    text: str

    @property
    def label(self) -> str:
        """This rung's canonical ``"<chain>:<level>"`` identifier, e.g. ``"hint:2"``.

        Returns
        -------
        str
            ``f"{self.chain}:{self.level}"``. This exact format is the wire
            contract every other module in this package parses rungs with:
            `cli.py`'s ``--rung`` flag is split on ``":"``
            (``chain_str, _, level_str = args.rung.partition(":")``),
            `runner.py` does the same (``rung.split(":", 1)``) when
            reconstructing ``(chain, level)`` from a sweep config's
            ``rungs`` list, and ``runner.slug_rung`` replaces the ``":"``
            with ``"-"`` for filesystem-safe output paths.
        """
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
# Noise (whitespace) padding — control arm for hint:3 / hint:4
# ---------------------------------------------------------------------------


def _count_tokens(s: str) -> int:
    """Token count of `s` under this module's harness tokenizer.

    Parameters
    ----------
    s : str
        Text to measure.

    Returns
    -------
    int
        The `tiktoken` ``cl100k_base`` encoding length of `s` when
        `tiktoken` is importable and encoding succeeds; otherwise
        ``len(s) // 4`` (a rough ~4-characters-per-token estimate for
        English prose).

    Notes
    -----
    The char-based fallback is intentionally rough, and callers differ in
    how much that roughness matters. `_render_hint_parts`'s hint:3+
    truncation loop and `is_trivial_rung`'s noise-triviality check only need
    a consistent-enough estimate to size a budget or decide whether a rung
    added content -- an approximation is fine there. `_render_noise_parts`'s
    exact-token-match padding is different: it needs `_count_tokens` to be
    the harness's single source of truth for "how many tokens is this text",
    since `token_matched_noise_prompt` verifies its pad against exactly this
    function (via `_TokenCounter`) and nothing else -- there is no second,
    more-precise counter it falls back to. `cl100k_base` is not necessarily
    the tokenizer of whichever model is actually being prompted, so even the
    `tiktoken` path is already an approximation of that model's real token
    count; the char-based fallback only widens that approximation for the
    rare case where `tiktoken` is unavailable or errors, rather than raising
    and aborting context rendering entirely. See `_TokenCounter` for how
    this function is exposed as an exact-match target where it counts.
    """
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(s))
    except Exception:  # noqa: BLE001
        return len(s) // 4


class _TokenCounter:
    """Adapts `_count_tokens` to the small `Tokenizer`-like interface
    `smolbench.induction._common`'s token-matching search expects: a
    `count(str) -> int` method plus a `name` attribute (used only in that
    module's own error messages -- see `choose_whitespace_unit` /
    `token_matched_noise_prompt`). This is a deliberately minimal, ad hoc
    adapter rather than an import of `smolbench.evals.tokenization.Tokenizer`
    -- the interface is duck-typed (`typing.Protocol` there), so no import is
    needed to satisfy it, and this module must not acquire a dependency on
    `smolbench.evals` (see `_render_noise_parts`'s Notes for why the whole
    `smolbench.induction._common` import stays lazy).
    """

    #: Identifies which counter is in play in `token_matched_noise_prompt`'s
    #: `ValueError` messages (e.g. "no whitespace unit costs ~1 token per
    #: repetition under tokenizer ...") -- not consumed anywhere else.
    name = "smolbench.deduction.lean.context._count_tokens (tiktoken cl100k_base, or len//4 fallback)"

    def count(self, text: str) -> int:
        """`_count_tokens(text)`, spelled as the `Tokenizer.count` the search helper expects."""
        return _count_tokens(text)


def _render_noise_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """`noise:N` = `hint:(N-1)` baseline + whitespace padded to `hint:N`'s exact token count.

    `noise:N` isolates the marginal *content* `hint:N` adds over
    `hint:(N-1)`: it renders the SAME `hint:(N-1)` baseline text, then pads
    it with whitespace until its token count exactly equals `hint:N`'s.
    Comparing a model's `hint:N` vs `noise:N` performance then isolates the
    effect of that content, because prompt length is no longer a confound --
    both rungs are the exact same number of tokens, and the padding carries
    no information a model could use.

    Parameters
    ----------
    theorem : BenchmarkTheorem
        Theorem being evaluated.
    k : int
        0-indexed proof step; forwarded to `_render_hint_parts`.
    level : int
        Noise level `N`; must be `>= 1` (see Raises). The baseline padded is
        `hint:(level - 1)`; the target token count matched is `hint:level`'s.

    Returns
    -------
    list of str
        `_render_hint_parts(theorem, k, level - 1)`'s parts, unchanged
        except that the LAST part has a whitespace pad appended to its end
        (never a new list element -- see Notes for why). When the baseline
        is already exactly as long as the target (the rung is trivial --
        see `is_trivial_rung`), the parts are returned completely unchanged,
        pad or no pad.

    Raises
    ------
    ValueError
        If `level < 1` (no noise counterpart is defined for the
        `hint:0`/`stepk:2` baseline -- there is nothing to pad against). If
        the `hint:(level - 1)` baseline is somehow LONGER, in tokens, than
        the `hint:level` target it is supposed to be padded to match --
        appending whitespace can only grow a rendering, never shrink one, so
        this contract is unsatisfiable; in practice this should never fire,
        since `hint:level`'s content is a strict superset of
        `hint:(level - 1)`'s, but it is guarded rather than silently
        under-padding and reintroducing the length confound. If
        `choose_whitespace_unit` cannot find a whitespace unit that costs
        ~1 token per repetition under `_count_tokens` (notably: whenever
        `tiktoken` is unavailable and `_count_tokens` has fallen back to its
        ``len(s) // 4`` estimate, since an *exact* token match cannot be
        built against an approximate counter -- see `_count_tokens`'s
        Notes). If the padding search itself cannot land on the exact target
        token count (`token_matched_noise_prompt`'s own `ValueError`), or if
        this function's own post-hoc verification of the result disagrees
        with the target (belt-and-braces -- see Notes).

    Notes
    -----
    Design: reuses `smolbench.induction._common.token_matched_noise_prompt`
    (the periodic/chromatic induction benchmarks' own exact-token-count
    whitespace-pad search) rather than reimplementing it. Both problems are
    identical -- "grow this text with content-free padding until it hits an
    exact token count under a given tokenizer" -- and a second, independently
    written bisection search would only be a second place for that logic to
    subtly drift from the first. The import is LAZY (inside this function,
    not at module top): `smolbench.induction._common` pulls in `numpy`,
    `ordered_set`, and `smolbench.evals`, none of which any other caller of
    this (`context`) module needs, and `context` is imported at module level
    by `runner.py` -- an eager import here would make every `runner`/`cli`
    invocation pay that cost even when no noise rung is ever rendered.

    The pad is appended to `base_parts[-1]` (the last existing part) rather
    than appended as a new part in the returned list. This is load-bearing:
    `render()` joins whatever parts this function returns with `"\\n\\n"`, so
    a new trailing part would silently insert an extra `"\\n\\n"` separator
    that the token search below never measured or accounted for, making the
    "exact token count" guarantee off by the separator's own token cost.
    Appending directly to the final part's text is what makes the final
    rendered string exactly `base_text + pad` -- precisely what
    `token_matched_noise_prompt` measured and verified.

    The pad is pure whitespace, not placeholder prose (the prior
    implementation this replaces generated a fixed paragraph, repeated):
    prose is itself informational content the paired `hint:N` rung does not
    have, and a markdown section header announcing the padding's own
    presence is unmatched content in its own right. Whitespace carries
    nothing a model could read as signal, and the
    match is exact (not approximate) rather than merely "close" -- both
    properties this experiment's noise arm requires to be a clean length
    control (see `smolbench.induction._common`'s module docstring for the
    same argument made about the induction benchmarks' own noise arm, where
    an earlier *character*-matched pad was found to silently overshoot its
    token-count target by 1.6x).

    This function never trusts `token_matched_noise_prompt`'s return value
    blindly, even though that function already verifies its own result
    internally: it has one documented escape hatch (returning the *unpadded*
    render, with a logged warning, when the unpadded text is already at or
    past the target -- see that function's docstring) that this function's
    own `base_tokens > target_tokens` / `base_tokens == target_tokens`
    pre-checks make unreachable in practice. "Should be unreachable" is not
    the same guarantee as "is checked", so the result's token count is
    re-verified here regardless before being returned.
    """
    if level < 1:
        raise ValueError(f"noise:{level} not defined; only noise:1+ supported")

    # Lazy import -- see this function's Notes for why `smolbench.induction._common`
    # must not be pulled in at module top.
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
        # Already exact: nothing to pad. Real and common -- every rung where
        # hint:level adds nothing over hint:(level - 1), which
        # `is_trivial_rung` independently reports as trivial. `render()` is
        # still called on trivial noise rungs when a sweep sets
        # `skip_trivial: false`, so this must return cleanly, not raise.
        return base_parts

    counter = _TokenCounter()
    padded_text = token_matched_noise_prompt(
        lambda pad: base_text + pad,  # render: pad string -> full rendered text
        "",  # context: empty -- the pad IS the whole variable part being searched
        target_tokens,
        counter,
        unit=choose_whitespace_unit(counter),
    )

    # Belt-and-braces (see Notes): verify exactness ourselves rather than
    # trusting the helper's own internal verification blindly.
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
    """Validate that `(chain, level)` names an in-range rung.

    Parameters
    ----------
    chain : Chain
        Chain name to validate.
    level : int
        Level to validate against `chain`'s bound in `_MAX_LEVEL`.

    Raises
    ------
    ValueError
        If `chain` is not one of `_MAX_LEVEL`'s keys (``"stepk"``,
        ``"hint"``, ``"noise"``), or if `level` is outside
        ``[0, _MAX_LEVEL[chain]]``. Does not check chain-specific
        constraints narrower than `_MAX_LEVEL` (e.g. `chain == "noise"`
        with `level == 0` passes here but is rejected later, by
        `_render_noise_parts`; see `render`'s ``Raises`` section).
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
    theorem : BenchmarkTheorem
        Theorem being proved.
    k : int
        The 0-indexed step we are about to prove -- the rendered context
        describes the state immediately before ``theorem.traced_tactics[k]``,
        and the LLM is expected to produce a tail starting at that tactic.
        Must satisfy ``0 <= k < len(theorem.traced_tactics)``.
    chain : Chain
        Which context chain to render (``"stepk"``, ``"hint"``, or
        ``"noise"``).
    level : int
        Level within `chain`; checked against `_MAX_LEVEL` via `validate`.

    Returns
    -------
    RenderedContext
        `chain`/`level` echoed back, plus `RenderedContext.text`: the
        chain-specific parts (from `_render_stepk_parts`,
        `_render_hint_parts`, or `_render_noise_parts`) joined with blank
        lines.

    Raises
    ------
    ValueError
        If `k` is outside ``[0, len(theorem.traced_tactics))``; if
        `(chain, level)` fails `validate` (unknown `chain`, or `level`
        outside `_MAX_LEVEL`'s bound); or if `chain == "noise"`, propagated
        from `_render_noise_parts`, whose own ``Raises`` section documents
        the noise-specific cases in full -- notably `level < 1` (``validate``
        alone does not reject ``noise:0``, since there is no noise
        counterpart for the `hint:0`/`stepk:2` baseline it would pad; see
        ``figures.NOISE_RUNGS_ALIGNED``'s docstring for the same gap
        described from the figure-plotting side), the `hint:(level - 1)`
        baseline somehow being LONGER, in tokens, than the `hint:level`
        target it must be padded to match, and the exact-token-match search
        itself failing (no whitespace unit found, or the search unable to
        land on the target).
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
      - `hint:3`+ when the per-premise dependency closure
        (``premises.premise_dep_closure``) at the requested hop depth is
        empty.
      - `noise:N` when the matching `hint:N` rung is itself trivial, or when
        `hint:N`'s rendering adds no tokens beyond `hint:(N-1)`'s (nothing
        to pad).

    Skipping these saves LLM tokens and makes per-rung pass rates a clean
    apples-to-apples comparison: every counted cell saw a real context
    expansion vs the previous rung.

    Parameters
    ----------
    theorem : BenchmarkTheorem
        Theorem being evaluated.
    k : int
        0-indexed proof step under consideration.
    chain : Chain
        Chain the rung belongs to.
    level : int
        Level within `chain`.

    Returns
    -------
    bool
        True if `(chain, level)` is trivial at this `(theorem, k)`, per the
        chain-specific rules above. False for any `chain` this function
        does not recognize, and for `k` outside
        ``[0, len(theorem.traced_tactics))`` -- a defensive default rather
        than a raised error, since the only caller (`smolbench.deduction.lean.runner.
        sweep`, gated by ``skip_trivial``) always invokes this with a `k`
        it has already validated for other purposes; "never trivial" is
        the safe default in case that assumption is ever violated, since it
        means a cell still runs rather than being silently dropped.
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
