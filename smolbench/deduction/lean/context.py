"""Render ``stepk``, ``hint``, and ``noise`` context rungs.

``noise:N`` matches ``hint:N`` full-prompt tokens, not context tokens, because
BPE merges at the instruction boundary can otherwise make it one token short.
``stepk`` is non-answer-conditional; ``hint`` adds answer-conditional premise
detail on a ``stepk:2`` baseline. ``hint:1+`` needs premise-corpus lookups.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .corpus import BenchmarkTheorem

Chain = Literal[
    "stepk", "hint", "noise", "sig", "proof", "signoise", "proofnoise", "hoponly"
]

# ``stepk`` has levels 0..2. ``hint``/``noise`` (flagged ladder) and
# ``sig``/``proof`` (unflagged library block, level = hops beyond the MPI
# lemmas) go to 9; the closure is uncapped, so the roster bounds the depth.
# ``signoise:N`` pads ``sig:0`` to ``sig:N``; ``proofnoise:N`` pads ``sig:N``
# to ``proof:N``. ``hoponly:N`` is ``sig:N`` with the MPI lemmas themselves
# removed: the N-hop closure alone, signatures, so the value of the MPI can be
# separated from the value of its neighbourhood.
_MAX_LEVEL: dict[str, int] = {
    "stepk": 2,
    "hint": 9,
    "noise": 9,
    "sig": 9,
    "proof": 9,
    "signoise": 9,
    "proofnoise": 9,
    "hoponly": 9,
}


def split_state(state_pp: str) -> tuple[str, str]:
    """Return `(hypotheses, goals)` from a Lean tactic-state pretty-print.

    Keep preceding ``case`` headers; no ``⊢`` yields ``(state_pp, "")``.

    Parameters
    ----------
    state_pp : str

    Returns
    -------
    tuple[str, str]
        Hypotheses and goals.
    """
    lines = state_pp.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("⊢"):
            goal_start = i
            while goal_start > 0 and lines[goal_start - 1].lstrip().startswith("case "):
                goal_start -= 1
            return (
                "\n".join(lines[:goal_start]).rstrip(),
                "\n".join(lines[goal_start:]).rstrip(),
            )
    return state_pp.rstrip(), ""


def extract_goal_only(state_pp: str) -> str:
    """`stepk:0` helper: drop hypotheses, keep every goal's `case ...`/`⊢` lines.

    Scan every goal because ``split_state`` would retain later hypotheses. Indented
    nonblank lines are goal continuations; that is the only distinguishing signal.

    Parameters
    ----------
    state_pp : str

    Returns
    -------
    str
        Unchanged input if it has no goal.
    """
    lines = state_pp.splitlines()
    if not any(line.lstrip().startswith("⊢") for line in lines):
        return state_pp

    kept: list[str] = []
    in_goal = False
    for line in lines:
        stripped = line.lstrip()
        if in_goal and stripped and line != stripped:
            kept.append(line)
            continue
        in_goal = False
        if stripped.startswith("case ") or stripped.startswith("⊢"):
            kept.append(line)
            in_goal = stripped.startswith("⊢")
            continue
        if not stripped:
            # Keep one separator so removed hypotheses leave no blank run.
            if kept and kept[-1] != "":
                kept.append("")
            continue
    return "\n".join(kept).rstrip()


@dataclass(frozen=True)
class RenderedContext:
    """One rendered (chain, level) context rung.

    ``prompt.build_user_prompt`` consumes ``text``; rows record ``label``.
    """

    chain: Chain
    level: int
    #: Context text.
    text: str

    @property
    def label(self) -> str:
        """Canonical ``"<chain>:<level>"`` id, e.g. ``"hint:2"``.

        ``cli.py`` and ``runner.py`` split the single ``":"``; ``slug_rung`` swaps it for ``"-"``.
        """
        return f"{self.chain}:{self.level}"


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
        parts.append(f"## Theorem\n`{theorem.full_name}` in `{theorem.file_path}`")
    return parts


def _count_tokens(s: str) -> int:
    """Token count of `s`: `tiktoken` ``cl100k_base``, else ``len(s) // 4``.

    Approximation keeps budget measurements usable without ``tiktoken``; noise
    uses exact ``TiktokenTokenizer`` because an exact control cannot approximate.

    Parameters
    ----------
    s : str

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

    Shared construction keeps padding and triviality measurements identical. Import
    ``prompt`` lazily to avoid its ``RenderedContext`` cycle; ``runner.py`` imports
    this module at top level.

    Parameters
    ----------
    level : int
    text : str

    Returns
    -------
    str
        User prompt.
    """
    from . import (
        prompt as _prompt,  # RenderedContext cycle; pylint: disable=cyclic-import
    )

    return _prompt.build_user_prompt(
        RenderedContext(chain="noise", level=level, text=text)
    )


def _render_noise_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """`noise:N` = `hint:(N-1)` whitespace-padded to `hint:N`'s exact PROMPT token count.

    Match full prompts because BPE at the instruction boundary can defeat a
    context-only match. Append padding to the final part so ``render`` adds no
    unmeasured separator. Return equal baselines because ``skip_trivial: false``
    still renders them. ``token_matched_noise_prompt`` is shared with induction
    padding so controls cannot drift; re-render its output to verify byte-exact
    recovery. Import it lazily because only noise needs its
    ``openai_compat`` ``requests``/``joblib``/``numpy``/``psutil`` dependencies.

    Parameters
    ----------
    theorem : BenchmarkTheorem
    k : int
    level : int

    Returns
    -------
    list[str]
        Context parts.

    Raises
    ------
    ImportError
        Missing ``tiktoken``; exact controls cannot approximate.
    """
    if level < 1:
        raise ValueError(f"noise:{level} not defined; only noise:1+ supported")
    return _pad_to_target(
        theorem,
        k,
        level,
        _render_hint_parts(theorem, k, level - 1),
        _render_hint_parts(theorem, k, level),
        f"noise:{level}",
        f"hint:{level - 1}",
        f"hint:{level}",
    )


def _pad_to_target(  # pylint: disable=too-many-arguments
    theorem: BenchmarkTheorem,
    k: int,
    level: int,
    base_parts: list[str],
    target_parts: list[str],
    rung: str,
    base_rung: str,
    target_rung: str,
) -> list[str]:
    """Whitespace-pad ``base_parts`` to ``target_parts``' exact PROMPT token count.

    Shared by every length control (``noise``, ``signoise``, ``proofnoise``)
    so they cannot drift. Import the tokenizer lazily because only controls
    need its ``requests``/``joblib``/``numpy``/``psutil`` dependencies.

    Parameters
    ----------
    theorem : BenchmarkTheorem
    k : int
    level : int
    base_parts : list[str]
    target_parts : list[str]
    rung, base_rung, target_rung : str
        Names for error messages.

    Returns
    -------
    list[str]

    Raises
    ------
    ValueError
        Base longer than target, or padding that does not hit the target.
    """
    from smolbench.evals.tokenization import (
        TiktokenTokenizer,
        choose_whitespace_unit,
        token_matched_noise_prompt,
    )

    base_text = "\n\n".join(base_parts)
    base_prompt = _as_full_prompt(level, base_text)
    target_text = "\n\n".join(target_parts)
    target_prompt = _as_full_prompt(level, target_text)

    tokenizer = TiktokenTokenizer()
    base_tokens = tokenizer.count(base_prompt)
    target_tokens = tokenizer.count(target_prompt)

    if base_tokens > target_tokens:
        raise ValueError(
            f"{rung} baseline ({base_rung}, {base_tokens} PROMPT "
            f"tokens) is LONGER than its {target_rung} target ({target_tokens} "
            f"PROMPT tokens) for {theorem.full_name!r} at k={k} -- a "
            "whitespace pad can only grow a rendering, never shrink one, so "
            "this rung cannot be built as a length control"
        )
    if base_tokens == target_tokens:
        # ``skip_trivial: false`` still renders equal baselines, so return.
        return base_parts

    padded_prompt = token_matched_noise_prompt(
        lambda pad: _as_full_prompt(level, base_text + pad),
        "",  # empty: the pad is the only variable part being searched
        target_tokens,
        tokenizer,
        unit=choose_whitespace_unit(tokenizer),
    )

    # Re-verify the study's exact length control.
    padded_tokens = tokenizer.count(padded_prompt)
    if padded_tokens != target_tokens:
        raise ValueError(
            f"{rung} padding for {theorem.full_name!r} at k={k} did not "
            f"hit the exact target: got {padded_tokens} PROMPT tokens, wanted "
            f"{target_tokens}"
        )

    # Derive the suffix length to avoid drift from prompt.py.
    suffix_len = len(base_prompt) - len(base_text)
    pad = padded_prompt[len(base_text) : len(padded_prompt) - suffix_len]

    # Re-rendering detects a future prompt prefix that would mis-locate padding.
    reconstructed = _as_full_prompt(level, base_text + pad)
    if reconstructed != padded_prompt:
        raise ValueError(
            f"{rung} pad recovery for {theorem.full_name!r} at k={k} "
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

    if names:
        block = "\n".join(f"- `{n}`" for n in names)
        parts.append(f"## Premises used in the next tactic\n{block}")
    else:
        parts.append("## Premises used in the next tactic\n_(none recorded)_")

    if level >= 1:
        from .premises import lookup, signature  # pylint: disable=cyclic-import

        sigs: list[str] = []
        for n in names:
            p = lookup(n)
            if p is None:
                sigs.append(f"### `{n}`\n_(not found in premise corpus)_")
            else:
                sigs.append(f"### `{n}` ({p.kind})\n```lean\n{signature(p)}\n```")
        if sigs:
            parts.append("## Premise signatures\n" + "\n\n".join(sigs))

    if level >= 2:
        # ``body_with_proof`` falls back without ``_traced_root()``; label it so
        # source availability is not misrepresented.
        from .premises import (  # pylint: disable=cyclic-import
            body_with_proof,
            has_full_source,
            lookup,
        )

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
                header += "  _(no traced source for this premise; signature shown)_"
            bodies.append(f"{header}\n```lean\n{body_with_proof(p)}\n```")
        if bodies:
            heading = (
                "## Premise full source (with proof)"
                if any_full_source
                else "## Premise signature (corpus record; traced source unavailable)"
            )
            parts.append(f"{heading}\n" + "\n\n".join(bodies))

    if level >= 3:
        from .premises import (  # pylint: disable=cyclic-import
            body_with_proof,
            lookup,
            premise_dep_closure,
        )

        depth = level - 2  # hint:3 = 1-hop, hint:4 = 2-hop, hint:5 = 3-hop, ...
        seeds: list = []
        for n in names:
            p = lookup(n)
            if p is not None:
                seeds.append(p)
        if seeds:
            # Unbounded on purpose: the closure is the manipulation, so no
            # token or premise cap may silently make two levels identical.
            # Context-window limits belong to the model roster, not the rung.
            transitive_premises = premise_dep_closure(seeds, depth)
            chunks = [
                f"### `{p.full_name}` ({p.kind}) at `{p.file_path}`\n"
                f"```lean\n{body_with_proof(p)}\n```"
                for p in transitive_premises
            ]
            if chunks:
                # Bare heading: hop depth, premise count, and token estimate
                # would tell the model how large the manipulation is.
                parts.append(
                    "## Transitive premise context\n" + "\n\n".join(chunks)
                )
    return parts


def _library_premises(
    theorem: BenchmarkTheorem, k: int, depth: int, exclude_seeds: bool = False
) -> list:
    """MPI lemmas of step ``k`` plus their ``depth``-hop closure, in library order.

    Parameters
    ----------
    theorem : BenchmarkTheorem
    k : int
    depth : int
    exclude_seeds : bool, optional
        Drop the MPI lemmas and keep only the closure (``hoponly``).

    Returns
    -------
    list[Premise]
        Empty when no MPI lemma is in the corpus.
    """
    from .premises import (  # pylint: disable=cyclic-import
        library_order,
        lookup,
        premise_dep_closure,
    )

    seeds: list = []
    seen: set[str] = set()
    for rec in theorem.traced_tactics[k].premises:  # a trace may cite a lemma twice
        p = lookup(rec["full_name"])
        if p is not None and p.full_name not in seen:
            seen.add(p.full_name)
            seeds.append(p)
    if not seeds:
        return []
    closure = premise_dep_closure(seeds, depth)
    if exclude_seeds:
        seed_names = {p.full_name for p in seeds}
        return library_order([p for p in closure if p.full_name not in seed_names])
    return library_order(seeds + closure)


def _render_library_parts(
    theorem: BenchmarkTheorem,
    k: int,
    depth: int,
    form: str,
    exclude_seeds: bool = False,
) -> list[str]:
    """``sig:depth`` / ``proof:depth``: `stepk:2` plus one unflagged library block.

    The block lists the MPI lemmas and their closure together, in import
    order, with nothing marking which entries the next tactic uses. ``form``
    ``sig`` renders each declaration's signature; ``proof`` renders its full
    source with proof. A step whose MPI is empty renders no block.

    Parameters
    ----------
    theorem : BenchmarkTheorem
    k : int
    depth : int
    form : str
        ``"sig"`` or ``"proof"``.
    exclude_seeds : bool, optional
        ``hoponly``: the closure without the MPI lemmas.

    Returns
    -------
    list[str]
    """
    from .premises import body_with_proof, signature  # pylint: disable=cyclic-import

    render_one = signature if form == "sig" else body_with_proof
    parts = _render_stepk_parts(theorem, k, 2)
    # No kind in the header: corpus records say ``commanddeclaration`` or
    # ``lemma`` while checked (generated) ones say ``theorem``, a tell.
    entries = [
        f"### `{p.full_name}` at `{p.file_path}`\n```lean\n{render_one(p)}\n```"
        for p in _library_premises(theorem, k, depth, exclude_seeds)
    ]
    if entries:
        parts.append("## Library context\n" + "\n\n".join(entries))
    return parts


def _render_hoponly_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """``hoponly:N`` = ``sig:N`` minus the MPI lemmas: the N-hop closure alone.

    Level 0 would be an empty block, so it is rejected.
    """
    if level < 1:
        raise ValueError(f"hoponly:{level} not defined; only hoponly:1+ supported")
    return _render_library_parts(theorem, k, level, "sig", exclude_seeds=True)


def _render_signoise_parts(theorem: BenchmarkTheorem, k: int, level: int) -> list[str]:
    """``signoise:N`` = ``sig:0`` padded to ``sig:N``: the hops as blank length."""
    if level < 1:
        raise ValueError(f"signoise:{level} not defined; only signoise:1+ supported")
    return _pad_to_target(
        theorem,
        k,
        level,
        _render_library_parts(theorem, k, 0, "sig"),
        _render_library_parts(theorem, k, level, "sig"),
        f"signoise:{level}",
        "sig:0",
        f"sig:{level}",
    )


def _render_proofnoise_parts(
    theorem: BenchmarkTheorem, k: int, level: int
) -> list[str]:
    """``proofnoise:N`` = ``sig:N`` padded to ``proof:N``: the proof bodies as blank length."""
    return _pad_to_target(
        theorem,
        k,
        level,
        _render_library_parts(theorem, k, level, "sig"),
        _render_library_parts(theorem, k, level, "proof"),
        f"proofnoise:{level}",
        f"sig:{level}",
        f"proof:{level}",
    )


def validate(chain: Chain, level: int) -> None:
    """Check that `(chain, level)` names an in-range rung.

    Check only ``_MAX_LEVEL``; ``_render_noise_parts`` later rejects ``noise:0``.

    Parameters
    ----------
    chain : Chain
    level : int
    """
    if chain not in _MAX_LEVEL:
        raise ValueError(f"unknown chain: {chain!r}")
    hi = _MAX_LEVEL[chain]
    if not 0 <= level <= hi:
        raise ValueError(f"{chain} level must be 0..{hi}; got {level}")


def render(
    theorem: BenchmarkTheorem, k: int, chain: Chain, level: int
) -> RenderedContext:
    """Render context at proof step `k` of `theorem` for the given (chain, level).

    ``k`` is the 0-indexed step to prove; context describes the preceding state.

    Parameters
    ----------
    theorem : BenchmarkTheorem
    k : int
    chain : Chain
    level : int

    Returns
    -------
    RenderedContext
        Requested context.

    Raises
    ------
    ValueError
        Out-of-range step or rung.
    ImportError
        Missing noise dependency or ``noise:0`` after range validation.
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
    elif chain in ("sig", "proof"):
        parts = _render_library_parts(theorem, k, level, chain)
    elif chain == "signoise":
        parts = _render_signoise_parts(theorem, k, level)
    elif chain == "proofnoise":
        parts = _render_proofnoise_parts(theorem, k, level)
    elif chain == "hoponly":
        parts = _render_hoponly_parts(theorem, k, level)
    else:
        raise ValueError(f"unknown chain {chain!r}")
    return RenderedContext(chain=chain, level=level, text="\n\n".join(parts))


# Default rungs stop at hint:3; validation permits hint:9. The closure is
# uncapped, so deep levels can exceed a model's context window; the roster,
# not the renderer, decides which levels a model can take.
IMPLEMENTED_RUNGS: tuple[tuple[Chain, int], ...] = (
    ("stepk", 0),
    ("stepk", 1),
    ("stepk", 2),
    ("hint", 0),
    ("hint", 1),
    ("hint", 2),
    ("hint", 3),
    ("noise", 1),
    ("noise", 2),
    ("noise", 3),
    ("sig", 0),
    ("sig", 1),
    ("sig", 2),
    ("proof", 0),
    ("proof", 1),
    ("proof", 2),
    ("signoise", 1),
    ("signoise", 2),
    ("proofnoise", 0),
    ("proofnoise", 1),
    ("proofnoise", 2),
)


def is_trivial_rung(  # the per-rung early exits are the spec; pylint: disable=too-many-return-statements
    theorem: BenchmarkTheorem, k: int, chain: Chain, level: int
) -> bool:
    """True iff this rung adds no informational content beyond the previous rung.

    Skip trivial cells so counted cells all add context; called by
    ``runner.sweep`` under ``skip_trivial``.

    Parameters
    ----------
    theorem : BenchmarkTheorem
    k : int
    chain : Chain
    level : int

    Returns
    -------
    bool
        False for unknown chains or bad steps so cells are not silently dropped.

    Raises
    ------
    ImportError
        Missing ``tiktoken`` for noise; guessing could mark an unrenderable rung safe.
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
            # ``stepk:2`` adds theorem identity even at k=0.
            return False
        return False

    if chain == "hint":
        # No premises makes every hint rung add nothing.
        if not tt.premises:
            return True
        if level == 0:
            return False
        from .premises import (  # pylint: disable=cyclic-import
            body_with_proof,
            lookup,
            signature,
        )

        premises = [lookup(p["full_name"]) for p in tt.premises]
        if level == 1:
            return all(p is None for p in premises)
        if level == 2:
            for p in premises:
                if p is not None and signature(p) != body_with_proof(p):
                    return False
            return True
        if level >= 3:
            from .premises import premise_dep_closure  # pylint: disable=cyclic-import

            seeds = [p for p in premises if p is not None]
            return not premise_dep_closure(seeds, level - 2)
        return False
    if chain == "noise":
        if level < 1:
            return True
        # Must use full-prompt tokens like noise rendering; this also subsumes the
        # structural hint test, or padding diverges silently.
        from smolbench.evals.tokenization import TiktokenTokenizer

        tokenizer = TiktokenTokenizer()
        base_parts = _render_hint_parts(theorem, k, level - 1)
        target_parts = _render_hint_parts(theorem, k, level)
        base_text = "\n\n".join(base_parts)
        target_text = "\n\n".join(target_parts)
        base_tokens = tokenizer.count(_as_full_prompt(level, base_text))
        target_tokens = tokenizer.count(_as_full_prompt(level, target_text))
        return target_tokens - base_tokens <= 0

    if chain in ("sig", "proof"):
        # Trivial when the block is empty, or adds nothing over the rung
        # below it: sig:N over sig:N-1 (no new closure entries), proof:N over
        # sig:N (every body equals its signature).
        if not _library_premises(theorem, k, level):
            return True
        if chain == "sig":
            return level > 0 and len(_library_premises(theorem, k, level)) == len(
                _library_premises(theorem, k, level - 1)
            )
        return _render_library_parts(theorem, k, level, "proof") == _render_library_parts(
            theorem, k, level, "sig"
        )
    if chain in ("signoise", "proofnoise"):
        if chain == "signoise" and level < 1:
            return True
        from smolbench.evals.tokenization import TiktokenTokenizer

        tokenizer = TiktokenTokenizer()
        if chain == "signoise":
            base = _render_library_parts(theorem, k, 0, "sig")
            target = _render_library_parts(theorem, k, level, "sig")
        else:
            base = _render_library_parts(theorem, k, level, "sig")
            target = _render_library_parts(theorem, k, level, "proof")
        base_tokens = tokenizer.count(_as_full_prompt(level, "\n\n".join(base)))
        target_tokens = tokenizer.count(_as_full_prompt(level, "\n\n".join(target)))
        return target_tokens - base_tokens <= 0
    if chain == "hoponly":
        # Trivial when the closure minus the MPI is empty, or gains nothing
        # over the level below.
        if level < 1 or not _library_premises(theorem, k, level, exclude_seeds=True):
            return True
        return level > 1 and len(_library_premises(theorem, k, level, True)) == len(
            _library_premises(theorem, k, level - 1, True)
        )
    return False
