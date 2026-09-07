"""Render context rungs along the `stepk`, `hint`, and `noise` chains.

`stepk:0..2` is cumulative step-k info with no answer-conditional content. `hint:0..4` is
cumulative answer-conditional detail about the premises the true next tactic uses, on a
`stepk:2` baseline. `noise:N` is `hint:(N-1)` whitespace-padded to `hint:N`'s exact token
count in the full PROMPT, not the bare context: the instruction suffix's own token cost
depends on what precedes it (BPE merges across that boundary), so a context-only match can
still ship a prompt one token short of its `hint:N` twin.

`hint:1+` needs a premise-body lookup against the premise corpus (see `.premises`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .corpus import BenchmarkTheorem

Chain = Literal["stepk", "hint", "noise"]

# Per-chain bound for `validate`'s (chain, level) range check.
# - stepk caps at 2: `_render_stepk_parts` only defines 0/1/2.
# - hint caps at 9: 0-2 are explicit; 3+ walks a transitive premise-dependency closure
#   (hint:3 = 1-hop ... hint:9 = 7-hop), deeper than the hint:0..4 range README/sweep-tests
#   use, but a real bound since `_HINT2_3_TOKEN_CAP` truncates however far it walks.
# - noise mirrors hint since `_render_noise_parts(level)` renders hint at level-1 and level.
_MAX_LEVEL: dict[str, int] = {"stepk": 2, "hint": 9, "noise": 9}


# ---------------------------------------------------------------------------
# Goal-state parsing
# ---------------------------------------------------------------------------


def split_state(state_pp: str) -> tuple[str, str]:
    """Return `(hypotheses, goals)` from a Lean tactic-state pretty-print.

    `goals` starts at the first `⊢` line, with any preceding `case ...`
    headers attached. A state with no `⊢` line yields `(state_pp, "")`.

    Parameters
    ----------
    state_pp : str
        Lean tactic-state pretty-print.

    Returns
    -------
    tuple[str, str]
        ``(hypotheses, goals)`` split of the state.
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
    """`stepk:0` helper: drop hypotheses, keep every goal's `case ...`/`⊢` lines.

    A tactic state can carry multiple goals at once (after a branching tactic), each with
    its own optional `case ...` header, hypothesis lines, and a `⊢ ...` line. `split_state`
    only locates the first `⊢`, which is right for its own callers but wrong here: used
    naively it would pass every later goal's hypotheses straight through unfiltered. This
    instead walks every line and drops hypothesis lines across all goals.

    A wrapped `⊢ ...` continuation line is indented, while hypotheses and `case ...` headers
    start at column 0 -- that indentation is the only signal for telling a continuation apart
    from the next goal's hypotheses, so it is what this function keys on.

    Parameters
    ----------
    state_pp : str
        Lean tactic-state pretty-print.

    Returns
    -------
    str
        `state_pp` completely unchanged if it has no `⊢` line at all.
    """
    lines = state_pp.splitlines()
    if not any(line.lstrip().startswith("⊢") for line in lines):
        return state_pp

    kept: list[str] = []
    in_goal = False  # True while consuming a just-kept `⊢` line's wrapped continuation.
    for line in lines:
        stripped = line.lstrip()
        if in_goal and stripped and line != stripped:
            # Indented and non-blank: a continuation of the previous `⊢` line.
            kept.append(line)
            continue
        in_goal = False
        if stripped.startswith("case ") or stripped.startswith("⊢"):
            kept.append(line)
            in_goal = stripped.startswith("⊢")
            continue
        if not stripped:
            # Blank separator between goals: keep at most one, never leading, so dropped
            # hypotheses don't leave a run of blanks or a leading empty line.
            if kept and kept[-1] != "":
                kept.append("")
            continue
        # Anything else is a hypothesis line: drop it.
    return "\n".join(kept).rstrip()


# ---------------------------------------------------------------------------
# Rendered context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RenderedContext:
    """One rendered (chain, level) context rung.

    Returned by `render`; `prompt.build_user_prompt` consumes `text`, and every
    result row records `label` as the cell's ``rung``.
    """

    chain: Chain
    level: int
    #: The chain-specific parts, blank-line-joined by `render`.
    text: str

    @property
    def label(self) -> str:
        """Canonical ``"<chain>:<level>"`` id, e.g. ``"hint:2"``.

        The single ``":"`` is a wire contract: `cli.py` and `runner.py` split on it to
        recover (chain, level); `runner.slug_rung` swaps it for ``"-"`` in paths.
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

    For BUDGET-style measurements only, where an approximate count is an acceptable price
    for never raising because `tiktoken` is missing. The `noise` chain needs an EXACT length
    control instead, so it uses `TiktokenTokenizer` directly rather than this fallback.
    `_render_hint_parts`'s hint:3+ budget re-implements this same policy inline as a local
    ``tok()`` (not a call here); change both together.

    Parameters
    ----------
    s : str
        Text to count.

    Returns
    -------
    int
        Token count.
    """
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(s))
    except Exception:  # noqa: BLE001
        return len(s) // 4


def _as_full_prompt(level: int, text: str) -> str:
    """Wrap noise-chain context `text` as the full prompt the model receives.

    `_render_noise_parts` and `is_trivial_rung`'s ``noise`` branch must measure and pad
    against identical text, so this is the one place that builds `RenderedContext` and calls
    `prompt.build_user_prompt` -- keeping both callers in lockstep.

    Imports `prompt` lazily: it imports `RenderedContext` from this module at module scope,
    so an eager import here would be a cycle (`runner.py` imports `context` at top level).

    Parameters
    ----------
    level : int
        Noise rung level.
    text : str
        Context text to wrap.

    Returns
    -------
    str
        Full user prompt.
    """
    from . import prompt as _prompt
    return _prompt.build_user_prompt(RenderedContext(chain="noise", level=level, text=text))


def _render_noise_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """`noise:N` = `hint:(N-1)` whitespace-padded to `hint:N`'s exact PROMPT token count.

    Matched on `prompt.build_user_prompt`'s output, not the bare context: the instruction
    suffix's own token cost depends on what precedes it (BPE merges across that boundary),
    so a context-only match can land on the right context count while still shipping a
    prompt one token short of its `hint:N` twin -- reintroducing the exact length confound
    this rung exists to remove.

    The pad is appended to the last part's text rather than as a new list element, since
    `render()` joins parts with ``"\\n\\n"`` and a new element would add an unmeasured
    separator. A baseline already equal to the target returns unchanged rather than raising,
    since `render()` still calls this on trivial rungs under ``skip_trivial: false``.

    Reuses `smolbench.evals.tokenization.token_matched_noise_prompt` (shared with the
    induction benchmark's padding, so the two cannot drift apart) and re-derives + re-renders
    the pad from its output to confirm the reconstruction is byte-exact, rather than trusting
    the helper's own internal check. Imports that module lazily: it pulls in
    `requests`/`joblib`/`numpy`/`psutil` via `openai_compat`, needed only by this rung.

    Parameters
    ----------
    theorem : BenchmarkTheorem
        The theorem containing the tactic step.
    k : int
        Index of the tactic step.
    level : int
        Noise rung level.

    Returns
    -------
    list[str]
        Rendered context parts.

    Raises
    ------
    ImportError
        If `tiktoken` is missing (`TiktokenTokenizer` does not degrade the way `_count_tokens`
        does -- an exact control cannot tolerate the approximation).
    """
    if level < 1:
        raise ValueError(f"noise:{level} not defined; only noise:1+ supported")

    # Lazy: only this rung needs tokenization's requests/joblib/numpy/psutil pull-in.
    from smolbench.evals.tokenization import (
        TiktokenTokenizer,
        choose_whitespace_unit,
        token_matched_noise_prompt,
    )

    base_parts = _render_hint_parts(theorem, k, level - 1)
    base_text = "\n\n".join(base_parts)
    base_prompt = _as_full_prompt(level, base_text)

    target_text = "\n\n".join(_render_hint_parts(theorem, k, level))
    target_prompt = _as_full_prompt(level, target_text)

    # Reused for both counts below -- no need to reload the encoding per measurement.
    tokenizer = TiktokenTokenizer()
    base_tokens = tokenizer.count(base_prompt)
    target_tokens = tokenizer.count(target_prompt)

    if base_tokens > target_tokens:
        raise ValueError(
            f"noise:{level} baseline (hint:{level - 1}, {base_tokens} PROMPT "
            f"tokens) is LONGER than its hint:{level} target ({target_tokens} "
            f"PROMPT tokens) for {theorem.full_name!r} at k={k} -- a "
            "whitespace pad can only grow a rendering, never shrink one, so "
            "this rung cannot be built as a length control"
        )
    if base_tokens == target_tokens:
        # Already exact: common when hint:level adds nothing new; render() still calls this
        # under skip_trivial:false, so this must return, not raise.
        return base_parts

    padded_prompt = token_matched_noise_prompt(
        # Padded against the full prompt, not bare context (see docstring).
        lambda pad: _as_full_prompt(level, base_text + pad),
        "",  # empty: the pad is the only variable part being searched
        target_tokens,
        tokenizer,
        unit=choose_whitespace_unit(tokenizer),
    )

    # Re-verify rather than trust the helper's own check.
    padded_tokens = tokenizer.count(padded_prompt)
    if padded_tokens != target_tokens:
        raise ValueError(
            f"noise:{level} padding for {theorem.full_name!r} at k={k} did not "
            f"hit the exact target: got {padded_tokens} PROMPT tokens, wanted "
            f"{target_tokens}"
        )

    # suffix_len is derived from base_prompt, never hardcoded from prompt.py's suffix --
    # copying that literal would be exactly the drift this closes.
    suffix_len = len(base_prompt) - len(base_text)
    pad = padded_prompt[len(base_text): len(padded_prompt) - suffix_len]

    # A future PREFIX in build_user_prompt would make the suffix_len slice
    # mis-locate the pad silently; only re-rendering catches that.
    reconstructed = _as_full_prompt(level, base_text + pad)
    if reconstructed != padded_prompt:
        raise ValueError(
            f"noise:{level} pad recovery for {theorem.full_name!r} at k={k} "
            "did not reconstruct the padded prompt: slicing the instruction "
            "suffix off the helper's returned prompt produced a pad that, "
            "re-rendered, does not reproduce that prompt byte-for-byte"
        )

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
        # `body_with_proof` falls back to the corpus's signature-only `Premise.code`
        # whenever there's no traced-repo slice (any box without `_traced_root()`), so the
        # heading must say which one actually rendered; a mixed block gets per-entry marks
        # too, so it isn't misread as uniformly real or uniformly fallback.
        from .premises import lookup, body_with_proof, has_full_source
        resolved = [(n, lookup(n)) for n in names]
        full_source: dict[str, bool] = {
            n: has_full_source(p) for n, p in resolved if p is not None
        }
        any_full_source = any(full_source.values())
        bodies: list[str] = []
        for n, p in resolved:
            if p is None:
                bodies.append(f"### `{n}`\n_(not found in premise corpus)_")
                continue
            header = f"### `{n}` ({p.kind}) at `{p.file_path}`"
            if any_full_source and not full_source[n]:
                # Mixed block: the section heading alone would call this "full source" too.
                header += "  _(no traced source for this premise; signature shown)_"
            bodies.append(f"{header}\n```lean\n{body_with_proof(p)}\n```")
        if bodies:
            heading = (
                "## Premise full source (with proof)"
                if any_full_source
                # Every body below is a fallback; "full source" would misdescribe them.
                else "## Premise signature (corpus record; traced source unavailable)"
            )
            parts.append(f"{heading}\n" + "\n\n".join(bodies))

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

    Only checks `_MAX_LEVEL`'s range, not narrower per-chain rules -- e.g. ``noise:0``
    passes here and `_render_noise_parts` rejects it later.

    Parameters
    ----------
    chain : Chain
        Rung chain to validate.
    level : int
        Rung level to validate.
    """
    if chain not in _MAX_LEVEL:
        raise ValueError(f"unknown chain: {chain!r}")
    hi = _MAX_LEVEL[chain]
    if not 0 <= level <= hi:
        raise ValueError(f"{chain} level must be 0..{hi}; got {level}")


def render(theorem: BenchmarkTheorem, k: int, chain: Chain, level: int) -> RenderedContext:
    """Render context at proof step `k` of `theorem` for the given (chain, level).

    `k` is the 0-indexed step about to be proved: context describes the state immediately
    before `theorem.traced_tactics[k]`, and the model is expected to produce the tail
    starting there. `(chain, level)` is checked by `validate`.

    Parameters
    ----------
    theorem : BenchmarkTheorem
        The theorem containing the tactic step.
    k : int
        Index of the tactic step.
    chain : Chain
        Context chain to render.
    level : int
        Rung level to render.

    Returns
    -------
    RenderedContext
        Rendered context for the requested rung.

    Raises
    ------
    ValueError
        If `k` is outside the theorem's traced tactics, or `chain`/`level` is invalid.
    ImportError
        ``noise`` can still raise this from `_render_noise_parts` even after
        validation passes (e.g. ``noise:0``, which `validate` allows through).
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


# Canonical default rung universe. Depths up to hint:9 run (see `_MAX_LEVEL`),
# but mathlib's dependency fan-out hits the 50k token cap by depth ~5-6.
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

    Skipping these cells keeps per-rung pass rates apples-to-apples: every counted cell saw
    a real context expansion. Only caller is `runner.sweep`, gated by ``skip_trivial``.

    Parameters
    ----------
    theorem : BenchmarkTheorem
        The theorem containing the tactic step.
    k : int
        Index of the tactic step.
    chain : Chain
        Rung chain to inspect.
    level : int
        Rung level to inspect.

    Returns
    -------
    bool
        False, not an exception, for an unrecognized `chain` or out-of-range `k`, so the cell
        still runs rather than being silently dropped.

    Raises
    ------
    ImportError
        For ``noise`` when `tiktoken` is missing, rather than guessing True/False:
        `_render_noise_parts` cannot build that rung either without it, and a wrong guess here
        could tell `runner.sweep` a rung is safe to render when it would raise.
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
            # stepk:2 adds theorem identity even at k=0.
            return False
        return False

    if chain == "hint":
        # Collapses the whole chain: hint:0 says "(none recorded)", 1+ have nothing to add.
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
        if level < 1:
            return True
        if is_trivial_rung(theorem, k, "hint", level):
            return True
        # Must measure the same quantity as `_render_noise_parts` -- full PROMPT tokens, not
        # `_count_tokens`'s context-text count -- or a rung called trivial here could still
        # render non-trivially there, or vice versa (silently unpadded).
        from smolbench.evals.tokenization import TiktokenTokenizer
        tokenizer = TiktokenTokenizer()
        base_text = "\n\n".join(_render_hint_parts(theorem, k, level - 1))
        target_text = "\n\n".join(_render_hint_parts(theorem, k, level))
        base_tokens = tokenizer.count(_as_full_prompt(level, base_text))
        target_tokens = tokenizer.count(_as_full_prompt(level, target_text))
        return target_tokens - base_tokens <= 0
    return False
