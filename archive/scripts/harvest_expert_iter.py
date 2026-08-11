"""Harvest CoT-augmented SFT rows from an expert-iteration sweep pass.

Companion to ``scripts/build_lean_synth_sft.py``: instead of an external
synthetic corpus, the *candidate rows* here are the model's own verified
rollouts from a ``scripts/lean_ec2_sweep.py --phase expert-iter`` run (a
pass@N sample, temperature 1.0, over ``novel_premises/train`` theorems --
see that phase's docstring for why ``source: with_proof`` is required
there). This is "expert iteration" in the STaR / RL-with-verifier sense: the
model's own *verified* successes become new supervised targets, closing the
loop between the eval's Lean-verified pass/fail signal and the next SFT
round -- and because the wire format is the base ``stepk:1`` shape the eval
scores, a harvested row trains under exactly the context distribution the
eval will re-test it on.

Pipeline, per ``(theorem_id, k)`` cell (all sourced from one run's
``all_rows.jsonl`` -- see ``smolbench.deduction.lean.runner``'s module
docstring for that file's schema):

1. **Difficulty gate** (BFS-Prover style): drop a cell whose success rate
   over its attempted rollouts is ``>= --easy-at`` -- a cell the model
   solves almost every time teaches the LoRA nothing it doesn't already do.
   Also drop a cell with fewer than ``--min-successes`` successful rollouts
   (not enough evidence to trust, and nothing to harvest from a cell with
   zero of them).
2. **Dedup + cap**: among the surviving rollouts' verified ``candidate_proof``
   texts, collapse whitespace-only duplicates and keep up to
   ``--max-per-theorem`` distinct proofs (a seeded sample when there are
   more -- see `select_candidates`), so one easy-to-restate cell can't
   dominate the harvested set.
3. **Rationale + target assembly**: each kept rollout's target is built via
   `wrap_assistant`, per the trainer's CoT-target coordination constants --
   ``think`` style wraps the model's own chain-of-thought (recovered from
   ``reasoning_content`` or, failing that, a ``<think>...</think>`` prefix
   in ``raw_response``) around the verified tail; ``fenced`` style puts the
   rationale before a fenced ```` ```lean ```` block. A rollout with NO
   recoverable rationale (a non-reasoning model, or an unterminated
   ``<think>`` block) contributes a BARE target -- see `wrap_assistant`. A
   recoverable rationale that itself contains forbidden markup (a fenced
   code block, or a literal ``<think>``/``</think>`` tag -- which would
   break the wrapping template's round-trip through
   `smolbench.deduction.lean.prompt.extract_tactic_block`, e.g. an embedded
   ``</think>`` closing the block early and stranding the verified tail
   outside it) is likewise degraded to a BARE target, counted separately
   under ``rationale_markup_dropped`` -- see `_rationale_has_forbidden_markup`.
4. **Re-render + decontaminate**: the user/system turns are rebuilt from
   scratch via `smolbench.deduction.lean.context.render` /
   `smolbench.deduction.lean.prompt` (never trusted from the sweep's
   recorded prompt file), then every row is checked against
   `smolbench.deduction.lean.decontam.HoldoutIndex` using facets derived
   from the VERIFIED ``candidate_proof`` -- never from the rationale, which
   is unverified free text a reasoning model could echo eval content into.
   `scripts.build_lean_synth_sft._facets_from_rendered` is reused (not
   reimplemented) for this so the derivation cannot drift between the two
   builders -- see its docstring. The row's own state is ALSO passed as
   `HoldoutIndex.check`'s ``statement=`` argument (mirroring
   `scripts.build_lean_synth_sft._parse_real`), which -- unlike the plain
   ``states=`` sweep -- additionally reaches the K2 exact+near-duplicate
   family, catching a harvested state that closely paraphrases (rather than
   byte-matches) an eval theorem's initial goal.

Runs on the main 3.14 venv (no ``lean_dojo`` -- this only reads a sweep's
already-verified JSONL output, it verifies nothing itself):

    .venv/bin/python scripts/harvest_expert_iter.py \\
        --run-dir notebooks/lean/results/runs/lean_expert_iter \\
        --style think --out notebooks/lean/data/sft/expert_iter_r1_think.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.build_lean_synth_sft import _facets_from_rendered  # noqa: E402
from smolbench.deduction.lean import context, corpus, decontam, prompt, sft  # noqa: E402

#: Assistant-target wrapping templates -- MUST match the coordination
#: constants byte-for-byte (every other package that consumes a harvested
#: row, or trains against one, assumes this exact shape). Keyed by
#: ``--style``; see `wrap_assistant` for the empty-rationale exception.
_STYLE_TEMPLATES: dict[str, str] = {
    "think": "<think>\n{rationale}\n</think>\n\n{tail}",
    "fenced": "{rationale}\n\n```lean\n{tail}\n```",
}


# ---------------------------------------------------------------------------
# all_rows.jsonl ingestion
# ---------------------------------------------------------------------------


def load_cell_rows(run_dir: Path) -> list[dict]:
    """Read ``<run_dir>/all_rows.jsonl``, keeping only ``kind == "cell"`` rows.

    Parameters
    ----------
    run_dir : Path
        A sweep's output directory (see
        ``smolbench.deduction.lean.runner``'s module docstring, "Output
        layout"). Typically the ``expert-iter`` phase's run_dir.

    Returns
    -------
    list of dict
        Every ``kind == "cell"`` row, in file order, at ANY verdict (not
        just ``success``) -- the difficulty gate in `select_candidates`
        needs the full attempted-rollout count as its denominator, so
        filtering to successes here would silently break it. Malformed
        (non-JSON) lines are skipped rather than raising, matching
        ``runner._existing_keys``'s tolerance of a truncated resume file.

    Raises
    ------
    FileNotFoundError
        If ``all_rows.jsonl`` does not exist under `run_dir` -- the sweep
        has not been run (or `run_dir` is wrong).
    """
    path = run_dir / "all_rows.jsonl"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found -- run the expert-iteration sweep first: "
            "scripts/lean_ec2_sweep.py --phase expert-iter"
        )
    rows: list[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("kind") == "cell":
                rows.append(rec)
    return rows


def group_by_theorem_k(rows: Iterable[dict]) -> dict[tuple[str, int], list[dict]]:
    """Group cell rows by their ``(theorem_id, k)`` cell key.

    Parameters
    ----------
    rows : iterable of dict
        Cell rows, e.g. from `load_cell_rows`.

    Returns
    -------
    dict[(str, int), list[dict]]
        Every row bucketed under its ``(row["theorem_id"], int(row["k"]))``
        key, preserving each bucket's relative row order. A row missing
        either key raises `KeyError` (a malformed sweep row, not a
        condition this function should paper over).
    """
    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["theorem_id"], int(r["k"]))].append(r)
    return dict(groups)


# ---------------------------------------------------------------------------
# Difficulty gate + dedup/cap (candidate SELECTION -- no rendering yet)
# ---------------------------------------------------------------------------


def normalize_proof(proof: str) -> str:
    """Dedup key for a candidate proof: every line stripped, then rejoined.

    Parameters
    ----------
    proof : str
        A verified ``candidate_proof`` (raw tactic lines).

    Returns
    -------
    str
        ``proof`` with each line's leading/trailing whitespace stripped,
        rejoined with ``\\n``. Deliberately does NOT collapse blank lines or
        strip the whole result -- this is a literal per-line normalization
        (two rollouts differing only in incidental indentation collide;
        two rollouts differing in an actual blank line between tactics do
        not), matching the module's coordination-constant spec exactly
        rather than a more aggressive general-purpose normalizer.
    """
    return "\n".join(line.strip() for line in proof.splitlines())


def select_candidates(
    groups: dict[tuple[str, int], list[dict]],
    *,
    easy_at: float,
    min_successes: int,
    max_per_theorem: int,
    seed: int,
) -> tuple[dict[tuple[str, int], list[dict]], dict]:
    """Apply the difficulty gate, then dedup + cap each surviving cell's rollouts.

    Parameters
    ----------
    groups : dict[(str, int), list[dict]]
        Cell rows grouped by ``(theorem_id, k)``, e.g. from
        `group_by_theorem_k`. Each row's ``verdict`` is inspected; other
        keys are untouched.
    easy_at : float
        Drop a cell whose ``successes / len(rows)`` (successes over ALL
        attempted rollouts, any verdict) is ``>= easy_at`` -- the
        BFS-Prover-style "too easy, no signal" gate. ``rows`` (not just
        non-exception rows) is the denominator: an API exception still
        consumed a rollout slot and should count against the cell's
        apparent difficulty the same way a genuine ``lean_error`` would.
    min_successes : int
        Drop a cell with fewer than this many ``verdict == "success"``
        rows -- both a "don't harvest from zero evidence" floor and a way
        for a caller to demand corroborating successes before trusting a
        cell (default 1: at least one).
    max_per_theorem : int
        Cap on distinct (post-dedup) proofs kept per surviving cell. Excess
        candidates are a SEEDED sample without replacement (`rng.sample`),
        not a truncation, so no single cell's rollout ORDER biases which
        proofs get kept.
    seed : int
        Seeds the `random.Random` used for the excess-candidate sample.

    Returns
    -------
    (kept, stats) : (dict[(str, int), list[dict]], dict)
        `kept` -- surviving cells mapped to their kept representative rows
        (one row per distinct proof; the row with the LOWEST
        ``rollout_idx`` among rows sharing a normalized proof is kept, so
        its ``raw_response``/``reasoning_content`` becomes the rationale
        source -- see `build_rows`). `stats` -- counters: ``groups_total``,
        ``groups_insufficient_successes``, ``groups_easy_filtered``,
        ``groups_kept``, ``candidates_considered`` (successes in kept
        cells before dedup), ``candidates_deduped`` (after dedup, before
        the cap), ``candidates_sampled`` (after the cap -- the final count
        `kept` actually holds).

    Notes
    -----
    Iterates `groups` in SORTED key order (not dict/file order) before
    drawing from `rng`, so the seeded sample is reproducible given
    ``(groups content, seed)`` regardless of ``all_rows.jsonl``'s write
    order -- which varies run to run under `runner.sweep`'s
    `ThreadPoolExecutor` theorem-worker pool (see that module's docstring).
    """
    rng = random.Random(seed)
    kept: dict[tuple[str, int], list[dict]] = {}
    stats = {
        "groups_total": 0,
        "groups_insufficient_successes": 0,
        "groups_easy_filtered": 0,
        "groups_kept": 0,
        "candidates_considered": 0,
        "candidates_deduped": 0,
        "candidates_sampled": 0,
    }
    for key in sorted(groups):
        rows = groups[key]
        stats["groups_total"] += 1
        total = len(rows)
        successes = [r for r in rows if r.get("verdict") == "success"]
        n_success = len(successes)

        if n_success < min_successes:
            stats["groups_insufficient_successes"] += 1
            continue
        if total and (n_success / total) >= easy_at:
            stats["groups_easy_filtered"] += 1
            continue
        stats["candidates_considered"] += n_success

        # Dedup by normalized proof text; the earliest rollout_idx among
        # duplicates is the canonical row (arbitrary but deterministic --
        # see the Returns section on why this row's fields matter later).
        by_norm: dict[str, dict] = {}
        for r in sorted(successes, key=lambda r: r.get("rollout_idx", 0)):
            proof = r.get("candidate_proof") or ""
            norm = normalize_proof(proof)
            if not norm:
                continue
            by_norm.setdefault(norm, r)
        distinct = list(by_norm.values())
        stats["candidates_deduped"] += len(distinct)

        if len(distinct) > max_per_theorem:
            distinct = rng.sample(distinct, max_per_theorem)
        stats["candidates_sampled"] += len(distinct)

        if distinct:
            kept[key] = distinct
            stats["groups_kept"] += 1
    return kept, stats


# ---------------------------------------------------------------------------
# Rationale extraction + style wrapping
# ---------------------------------------------------------------------------


def derive_rationale(row: dict) -> str:
    """Recover a rollout's chain-of-thought text, if any.

    Parameters
    ----------
    row : dict
        A cell row (see `smolbench.deduction.lean.runner`'s row schema).
        Reads ``reasoning_content`` and ``raw_response``.

    Returns
    -------
    str
        ``row["reasoning_content"]``, stripped, if it is truthy (a
        reasoning-capable provider that reports its CoT out-of-band --
        e.g. via an OpenAI-compatible ``reasoning_content`` field). Else,
        if ``row["raw_response"]`` contains a literal ``"</think>"``, the
        text before it with a leading ``"<think>"`` stripped. Else ``""``
        -- in particular, an UNTERMINATED ``<think>`` block (the model was
        cut off mid-reasoning, e.g. by ``max_tokens``) yields an empty
        rationale rather than guessing where it would have closed; see
        `wrap_assistant` for what an empty rationale does to the target.
    """
    reasoning_content = row.get("reasoning_content")
    if reasoning_content:
        return reasoning_content.strip()
    raw = row.get("raw_response") or ""
    if "</think>" not in raw:
        return ""
    before = raw.split("</think>", 1)[0]
    if before.startswith("<think>"):
        before = before[len("<think>") :]
    return before.strip()


#: Markup that would break `wrap_assistant`'s wrapping-template round-trip
#: through `smolbench.deduction.lean.prompt.extract_tactic_block` if it
#: appeared INSIDE a rationale rather than around it -- the exact same
#: forbidden-markup set `scripts.annotate_lean_cot._qc_gate` gates on for its
#: own (differently-sourced) rationales. Kept as a tuple, not re-derived from
#: `_STYLE_TEMPLATES`, since the hazard is style-independent: an embedded
#: ``</think>`` breaks the "think" template's round-trip and an embedded
#: fence breaks the "fenced" template's, but either token breaks EITHER
#: template well enough (a stray ``<think>``/``</think>`` inside a "fenced"
#: rationale would still confuse a downstream ``<think>`` scan) that gating
#: on the union, regardless of `style`, is simpler and strictly safer than a
#: per-style allowlist.
_FORBIDDEN_RATIONALE_MARKUP: tuple[str, ...] = ("```", "<think>", "</think>")


def _rationale_has_forbidden_markup(rationale: str) -> bool:
    """True if `rationale` contains markup that would corrupt the CoT wrap.

    A harvested rollout's chain-of-thought (`derive_rationale`'s output) is
    UNVERIFIED free text -- unlike the verified ``candidate_proof`` tail --
    so nothing stops a reasoning model from echoing one of these tokens
    inside its own reasoning (quoting Lean code in triple-backticks), or a
    reasoning-parser artifact leaking a literal ``</think>`` into
    ``reasoning_content``. `wrap_assistant`'s think-style template
    (``"<think>\\n{r}\\n</think>\\n\\n{tail}"``) does no escaping: an
    embedded ``</think>`` closes the block early and stitches the verified
    tail in OUTSIDE it, silently producing malformed supervision rather than
    an error.

    Parameters
    ----------
    rationale : str
        A candidate rationale, e.g. from `derive_rationale`. Safe to call on
        an already-empty string (returns False -- nothing to gate).

    Returns
    -------
    bool
        True if any of `_FORBIDDEN_RATIONALE_MARKUP` appears anywhere in
        `rationale`.
    """
    return any(token in rationale for token in _FORBIDDEN_RATIONALE_MARKUP)


def wrap_assistant(style: str, rationale: str, tail: str) -> tuple[str, bool]:
    """Wrap a verified tactic tail in the CoT-target template for `style`.

    Parameters
    ----------
    style : {"think", "fenced"}
        Which `_STYLE_TEMPLATES` entry to use.
    rationale : str
        The rollout's chain-of-thought text, e.g. from `derive_rationale`.
        May be empty.
    tail : str
        The verified ``candidate_proof`` tactic lines.

    Returns
    -------
    (assistant, used_bare) : (str, bool)
        When `rationale` is non-empty: ``_STYLE_TEMPLATES[style]`` filled
        in with `rationale` and `tail`, and ``used_bare=False``. When
        `rationale` IS empty: `tail` UNCHANGED (no ``<think>`` block, no
        ```` ```lean ```` fence) and ``used_bare=True`` -- wrapping an
        empty rationale would emit a template with nothing inside it
        (``"<think>\\n\\n</think>\\n\\n{tail}"``, or a fenced block preceded
        by a blank line), which teaches the LoRA to always open a
        content-free CoT block rather than teaching it that CoT is
        optional. A bare (rationale-less) row is exactly what the
        ``bare8k-r128`` arm's rows already look like, so this degrades
        gracefully to that shape instead of emitting a malformed one.

    Raises
    ------
    KeyError
        If `style` is not a key of `_STYLE_TEMPLATES`.
    """
    if not rationale:
        return tail, True
    return _STYLE_TEMPLATES[style].format(rationale=rationale, tail=tail), False


# ---------------------------------------------------------------------------
# Re-render + decontaminate -> trainer-shaped rows
# ---------------------------------------------------------------------------


def build_rows(
    kept: dict[tuple[str, int], list[dict]],
    *,
    style: str,
    run_name: str,
    theorem_by_name: dict[str, corpus.BenchmarkTheorem],
    holdout_names: set[str],
    index: decontam.HoldoutIndex,
) -> tuple[list[dict], dict]:
    """Re-render kept candidates and emit decontaminated trainer-shaped rows.

    Parameters
    ----------
    kept : dict[(str, int), list[dict]]
        Surviving ``(theorem_id, k)`` cells and their kept rows, from
        `select_candidates`.
    style : {"think", "fenced"}
        Forwarded to `wrap_assistant`.
    run_name : str
        Recorded verbatim under each row's ``meta.source_run`` -- the
        harvested run's short identifier (see `main`'s ``args.run_dir.name``
        derivation), not a full path, so a manifest/meta diff across two
        harvests of the same run staged at different absolute paths still
        reads as "same source".
    theorem_by_name : dict[str, BenchmarkTheorem]
        Lookup table (``full_name -> BenchmarkTheorem``) built from
        ``corpus.load_split("novel_premises", "train")`` -- see `main`.
    holdout_names : set of str
        `smolbench.deduction.lean.sft.eval_holdout_names`'s result -- every
        ``theorem_id`` in this set is skipped before any rendering (K1,
        redundant with `index`'s own name check, kept as defense in depth
        -- see the ``eval_holdout_name_hits`` assertion in `main`).
    index : HoldoutIndex
        Content-level decontamination index (K2/K3/K4), built once by the
        caller (`decontam.HoldoutIndex.build()`).

    Returns
    -------
    (rows, stats) : (list[dict], dict)
        `rows` -- trainer-shaped dicts: ``{"system", "user", "assistant",
        "meta": {"full_name", "k", "n_tail", "source_run", "rollout_idx"}}``
        (matches `smolbench.deduction.lean.sft.SFTExample.to_json`'s shape).
        `stats` -- counters: ``theorem_not_found`` (a kept cell's
        ``theorem_id`` is absent from `theorem_by_name` -- skipped, not
        raised, so one stale/mismatched run doesn't abort the whole
        harvest), ``eval_holdout_name_hits`` (see above), ``dropped``
        (per-`decontam.Hit.key` counts, first-hit-wins per row, mirroring
        ``scripts.build_lean_synth_sft.BuildStats.record_hits``),
        ``empty_rationale_count`` (rows `wrap_assistant` returned
        ``used_bare=True`` for -- this INCLUDES every
        ``rationale_markup_dropped`` row, since a markup-gated rationale is
        forced empty before `wrap_assistant` ever sees it),
        ``rationale_markup_dropped`` (rows whose recovered rationale was
        non-empty but contained forbidden markup -- see
        `_rationale_has_forbidden_markup` -- and was therefore discarded in
        favor of a bare target), ``emitted`` (``len(rows)``).

    Notes
    -----
    ``n_tail`` is ``len(theorem.traced_tactics) - k`` -- the GROUND-TRUTH
    tail length at step `k`, matching `sft.SFTExample.n_tail`'s definition
    exactly for consistency with the rest of the codebase's ``meta`` shape.
    This is deliberately NOT the harvested row's own ``candidate_proof``
    tactic count (which can legitimately differ from the ground truth --
    Lean often admits multiple correct tactic sequences of different
    lengths for the same goal); `n_tail` here is a proof-length indicator
    of the CELL, not of the specific model-produced proof.
    """
    rows_out: list[dict] = []
    stats = {
        "theorem_not_found": 0,
        "eval_holdout_name_hits": 0,
        "empty_rationale_count": 0,
        "rationale_markup_dropped": 0,
        "dropped": {},
        "emitted": 0,
    }
    for key in sorted(kept):
        theorem_id, k = key
        if theorem_id in holdout_names:
            # Defense in depth -- see `main`'s post-hoc assertion. An
            # expert-iter sweep only ever runs on novel_premises/train
            # (disjoint from DEFAULT_EVAL_SPECS by construction), so this
            # branch should never actually execute.
            stats["eval_holdout_name_hits"] += 1
            continue
        theorem = theorem_by_name.get(theorem_id)
        if theorem is None:
            stats["theorem_not_found"] += 1
            continue

        # Re-render from scratch (never trust the sweep's saved prompt
        # file) -- prompt-format parity with the eval is the whole point.
        rendered = context.render(theorem, k, "stepk", 1)
        user = prompt.build_user_prompt(rendered)
        n_tail = len(theorem.traced_tactics) - k

        for row in kept[key]:
            proof = row.get("candidate_proof") or ""
            rationale = derive_rationale(row)
            # Rationale sanitization: a non-empty rationale containing
            # forbidden markup would corrupt wrap_assistant's template (see
            # _rationale_has_forbidden_markup's docstring) -- force it empty
            # (degrading to a bare target, same as "no rationale recovered")
            # rather than emit malformed supervision, and count it under its
            # OWN counter (in addition to empty_rationale_count below) so a
            # manifest reader can tell "no CoT available" apart from "CoT
            # available but unsafe to wrap" -- mirroring
            # scripts.annotate_lean_cot.py's forbidden-markup QC gate.
            if rationale and _rationale_has_forbidden_markup(rationale):
                stats["rationale_markup_dropped"] += 1
                rationale = ""
            assistant, used_bare = wrap_assistant(style, rationale, proof)
            if used_bare:
                stats["empty_rationale_count"] += 1

            # Facets derived from the VERIFIED proof, never the rationale
            # (unverified free text). Reusing _facets_from_rendered (rather
            # than re-deriving states/tactics/pairs by hand here) means
            # this builder and build_lean_synth_sft's zero-leak gate can
            # never silently disagree about what a row's facets are.
            states, tactics, pairs = _facets_from_rendered(user, proof)
            # Also pass the row's own state as `statement=` (mirrors
            # scripts.build_lean_synth_sft._parse_real) -- unlike the plain
            # `states=` sweep (K3 exact-state matching only), this reaches
            # the K2 exact+near-duplicate (MinHash/LSH) family too, catching
            # a harvested state that closely paraphrases (rather than
            # byte-matches) an eval theorem's initial goal.
            hits = index.check(
                name=theorem_id,
                statement=states[0] if states else None,
                states=states,
                tactics=tactics,
                pairs=pairs,
            )
            if hits:
                stats["dropped"][hits[0].key] = stats["dropped"].get(hits[0].key, 0) + 1
                continue

            rows_out.append(
                {
                    "system": prompt.SYSTEM,
                    "user": user,
                    "assistant": assistant,
                    "meta": {
                        "full_name": theorem_id,
                        "k": k,
                        "n_tail": n_tail,
                        "source_run": run_name,
                        "rollout_idx": row.get("rollout_idx"),
                    },
                }
            )
            stats["emitted"] += 1
    return rows_out, stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-dir", type=Path, required=True,
                   help="expert-iter sweep run dir (containing all_rows.jsonl)")
    p.add_argument("--style", choices=sorted(_STYLE_TEMPLATES), default="think",
                   help="CoT-target wrapping style; see the coordination constants")
    p.add_argument("--out", type=Path, required=True, help="output JSONL path")
    p.add_argument("--easy-at", type=float, default=0.75,
                   help="drop a (theorem, k) cell whose success rate >= this "
                        "(BFS-Prover style: too easy, no signal)")
    p.add_argument("--min-successes", type=int, default=1,
                   help="drop a cell with fewer than this many successful rollouts")
    p.add_argument("--max-per-theorem", type=int, default=2,
                   help="cap on distinct kept proofs per (theorem, k) cell "
                        "(seeded sample when more are available)")
    p.add_argument("--seed", type=int, default=1776)
    return p


def build(args: argparse.Namespace) -> tuple[Path, dict]:
    """Run the harvest end to end; write the output JSONL + manifest.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI args from `build_parser()`.

    Returns
    -------
    (manifest_path, manifest) : (Path, dict)
        Where the manifest was written (``args.out`` with a
        ``.manifest.json`` suffix, mirroring
        ``scripts.build_lean_synth_sft.build``'s convention) and its
        contents.

    Raises
    ------
    FileNotFoundError
        Propagated from `load_cell_rows` if `args.run_dir` has no
        ``all_rows.jsonl``.
    AssertionError
        If any harvested row's ``theorem_id`` was found in the eval
        holdout name set -- see `build_rows`' ``eval_holdout_name_hits``
        docstring. This should be unreachable for a correctly-sourced
        expert-iter run; firing indicates upstream contamination (a sweep
        run against val/test, or a corrupted ``theorem_id``), not a
        normal drop, so it is a hard failure rather than a counted stat.
    """
    rows = load_cell_rows(args.run_dir)
    groups = group_by_theorem_k(rows)
    kept, select_stats = select_candidates(
        groups,
        easy_at=args.easy_at,
        min_successes=args.min_successes,
        max_per_theorem=args.max_per_theorem,
        seed=args.seed,
    )

    # Lookup table for re-rendering: load_split (not iter_with_proof) so a
    # theorem with NO traced tactics can still be looked up (defensively --
    # every kept cell came from a sweep that only emits cells for theorems
    # with tactics, so this is a superset, never a gap).
    theorem_by_name = {t.full_name: t for t in corpus.load_split("novel_premises", "train")}
    holdout_names = sft.eval_holdout_names(sft.DEFAULT_EVAL_SPECS)
    index = decontam.HoldoutIndex.build()

    run_name = args.run_dir.name
    rows_out, build_stats = build_rows(
        kept,
        style=args.style,
        run_name=run_name,
        theorem_by_name=theorem_by_name,
        holdout_names=holdout_names,
        index=index,
    )

    assert build_stats["eval_holdout_name_hits"] == 0, (
        f"{build_stats['eval_holdout_name_hits']} harvested row(s) had a theorem_id inside "
        "the eval holdout -- an expert-iter sweep must only run on novel_premises/train "
        f"theorems (run_dir={args.run_dir}); this indicates upstream contamination, not a "
        "normal drop -- see build_rows' docstring"
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for r in rows_out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    manifest = {
        "config": {
            "run_dir": str(args.run_dir),
            "style": args.style,
            "easy_at": args.easy_at,
            "min_successes": args.min_successes,
            "max_per_theorem": args.max_per_theorem,
            "seed": args.seed,
        },
        "stats": {
            "total_cell_rows": len(rows),
            **select_stats,
            "theorem_not_found": build_stats["theorem_not_found"],
            "eval_holdout_name_hits": build_stats["eval_holdout_name_hits"],
            "empty_rationale_count": build_stats["empty_rationale_count"],
            "rationale_markup_dropped": build_stats["rationale_markup_dropped"],
            "dropped": dict(sorted(build_stats["dropped"].items())),
            "dropped_total": sum(build_stats["dropped"].values()),
            "emitted": build_stats["emitted"],
        },
        "decontamination": {
            "holdout_size": len(holdout_names),
            "index": index.stats(),
        },
        "output_jsonl": args.out.name,
    }
    manifest_path = args.out.with_name(args.out.stem + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest_path, manifest


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest_path, manifest = build(args)
    s = manifest["stats"]
    print(
        f"[{args.run_dir.name}] {s['groups_total']} cells -> "
        f"{s['groups_insufficient_successes']} too-few-successes, "
        f"{s['groups_easy_filtered']} easy-filtered, {s['groups_kept']} kept; "
        f"{s['candidates_deduped']} distinct proofs -> {s['candidates_sampled']} sampled -> "
        f"{s['dropped_total']} decontam-dropped {s['dropped']}, "
        f"{s['emitted']} emitted ({s['empty_rationale_count']} bare/no-rationale, "
        f"incl. {s['rationale_markup_dropped']} via the markup gate)\n"
        f"-> {args.out}\nmanifest -> {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
