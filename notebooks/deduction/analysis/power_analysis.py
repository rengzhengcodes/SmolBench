"""Power analysis for the Lean-4 deduction family-ladder scaling study (21 checkpoints,
7 vendor families x 3 rungs).

The study overloads "rung"; this file does not: ``ladder_pos`` is a model's position in
its family 3-tuple (0..2), ``prompt_rung`` is a prompt's context rung. PRIMARY = 21
within-family ladder contrasts (Bonferroni); SECONDARY = 63 cross-family size-matched
contrasts (Benjamini-Hochberg, exploratory), both sized by a block-bootstrap n_theorems
curve plus a Beta-mixture pass@N advisory -- theorems, not replicates, are this
benchmark's power lever.

Reads ``verified_rows.jsonl``, never the generation-time ``all_rows.jsonl``: the latter's
verdicts are all the ``"unverified"`` placeholder, so every rate would read at or near
0.000, indistinguishable from a genuine "every model failed everything" result -- hence
`load_joint_cells` prints a loud stderr banner instead of falling back silently.

`S3_BUCKET` is read from ``smolbench/evals/study_config.toml``, never spelled out in
prose, so this can't drift from the bucket a run actually reads.

    .venv/bin/python notebooks/deduction/analysis/power_analysis.py --s3
"""

from __future__ import annotations

# Cap BLAS/OpenMP threads before numpy is imported: on the shared eval container,
# numpy's default OpenBLAS pool trips RLIMIT_NPROC beside a lean sweep's Dojo verifiers
# ("pthread_create failed"). One thread suffices here.
import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import functools
import hashlib
import json
import sys
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import binom

# notebooks/ (where _power_common.py lives) is two levels up; anchored to __file__ so
# this is cwd-independent.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# THIS directory, for the bare-name sibling import of `rows_source` below. Required:
# tests load this file via ``importlib.util.spec_from_file_location``, which does not put
# this dir on sys.path the way running it as a script would, so without this the sibling
# import would resolve only by accident. `error_bars.py`/`hint_vs_noise.py` carry the same.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Repo root: the documented run mode is ``uv run --no-project`` (no smolbench
# installed), so `study_config` below must resolve from this source tree.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from _power_common import (
    ALPHA,
    POWER_TARGETS,
    SEED,
    fmt_r,
    results_dir,
)

from smolbench.evals.study_config import families as _study_families
from smolbench.evals.study_config import roster_keys as _study_roster_keys

from rows_source import (  # noqa: E402
    S3_BUCKET,
    _banner,
    download_scaling_rows,
    reject_superseded,
    spool_prefix,
)

# --------------------------------------------------------------------------- #
# Roster: 7 vendor families x 3 rungs = 21 models, from the committed study config
# rather than hand-typed here. Spec keys are kept as-is (unlike the induction sibling),
# since they're already what every JSONL row's "model" field uses.
#
# ORDER IS LOAD-BEARING: each family's tuple must read SMALL -> MID -> LARGE, because
# `build_cross_family_contrasts` pairs families BY LADDER POSITION and
# `build_within_family_contrasts` names its pairs by it. The config's
# ``[roster.families]`` order already is that order; reordering a family's rungs there
# silently re-pairs all 63 secondary contrasts here.
# --------------------------------------------------------------------------- #
FAMILIES: dict[str, tuple[str, ...]] = {
    family: tuple(rungs) for family, rungs in _study_families().items()
}
MODELS = tuple(_study_roster_keys())  # 21, the FAMILIES tuples concatenated

# Module scope, not just inside main(), so importing this module for its constants gets
# the guard too. `raise`, not `assert`: `python -O` strips asserts, and this must fire at
# import time. MODELS is the FAMILIES tuples concatenated, so length/uniqueness are the
# only drift possible; these two checks don't by themselves pin "3 rungs per family" --
# a short family instead IndexErrors at position 2 on the first contrast build, and a
# long one still fails the count below -- so that shape is left implicit rather than
# checked a third time.
if len(MODELS) != 21:
    raise ValueError(
        f"expected 21 models (7 families x 3 rungs) from study_config, got "
        f"{len(MODELS)} across {len(FAMILIES)} families"
    )
if len(set(MODELS)) != len(MODELS):
    raise ValueError(
        f"study_config's roster repeats model spec-key(s) "
        f"{sorted(k for k in set(MODELS) if MODELS.count(k) > 1)}; "
        "each checkpoint must appear on exactly one family ladder"
    )

# --------------------------------------------------------------------------- #
# Design constants.
# --------------------------------------------------------------------------- #
SIMS = 4000  # Monte-Carlo sims per grid point (matches the archived script's default)
#: Equivalence half-width for near-ties (pass@1 rate points). A pair whose bootstrap
#: 90% CI (5th/95th percentile) for the paired rate gap falls inside +/- this is
#: certified "indistinguishable at this resolution", not left unresolved.
EQUIV_BAND = 0.10
#: Beta concentration (a + b) for the pass@N solvable-cell probability mixture.
BETA_CONC = 5.0

N_THEOREMS_GRID = (30, 60, 100, 150, 200, 300)
N_REPLICATES_GRID = (1, 2, 3, 4, 8)

# PRIMARY tier: 21 within-family ladder contrasts (7 families x C(3,2)=3
# size-pairs). Bonferroni over the full family.
N_PRIMARY = 21
ALPHA_PRIMARY = ALPHA / N_PRIMARY

# SECONDARY tier: 63 cross-family, size-matched contrasts (3 ladder positions x
# C(7,2)=21 family-pairs). Benjamini-Hochberg FDR at q=0.05. Sizing uses
# Q_SECONDARY/N_SECONDARY, BH's conservative rank-1 threshold, as an upper bound on the
# real per-contrast alpha (see `benjamini_hochberg`'s docstring); the OBSERVED decision
# uses the actual procedure -- see `_print_tier_report`.
N_SECONDARY = 63
Q_SECONDARY = 0.05
ALPHA_SECONDARY = Q_SECONDARY / N_SECONDARY

RESULTS_DIR = results_dir(__file__, up=1)

_Contrast = tuple[str, str, str]  # (label, model_a, model_b)


def _seed_of(name: str) -> int:
    """Derive a deterministic 32-bit seed from a model name.

    SHA-256, never builtin ``hash``: the latter is salted per process
    (``PYTHONHASHSEED``), which would make every per-pair RNG stream -- and so every
    reported power value and CI -- irreproducible across runs.

    Parameters
    ----------
    name : str
        Model name.

    Returns
    -------
    int
        deterministic 32-bit seed
    """
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "little")


# --------------------------------------------------------------------------- #
# Core statistics. `pass_at_n` and `benjamini_hochberg` stay hand-rolled (a few lines of
# closed-form arithmetic); `mcnemar_exact_p` uses `scipy.stats.binom` directly, since this
# file's ``uv run --no-project --with numpy --with scipy`` environment already declares it.
# --------------------------------------------------------------------------- #
def pass_at_n(p: np.ndarray | float, n: int) -> np.ndarray | float:
    """Probability at least one of `n` conditionally-independent replicates succeeds:
    ``1 - (1 - p)**n``, for `p` in ``[0, 1]`` and `n >= 1`.

    Parameters
    ----------
    p : np.ndarray | float
        Per-replicate success probability.
    n : int
        Number of conditionally-independent replicates.

    Returns
    -------
    np.ndarray | float
        probability that at least one replicate succeeds
    """
    return 1.0 - (1.0 - np.asarray(p, dtype=float)) ** n


@functools.lru_cache(maxsize=None)
def mcnemar_exact_p(b: int, c: int) -> float:
    """McNemar's exact two-sided binomial p-value for discordant counts.

    Under H0, ``b`` is ``Binomial(b + c, 0.5)``, so
    ``p = min(1, 2 * P(X <= min(b, c)))`` via ``scipy.stats.binom.cdf``.

    Parameters
    ----------
    b : int
        Counts where A succeeds and B fails.
    c : int
        Counts where B succeeds and A fails.

    Returns
    -------
    float
        1.0 when ``b + c == 0``; otherwise the two-sided p-value
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2.0 * binom.cdf(k, n, 0.5))


def benjamini_hochberg(pvalues: np.ndarray, q: float) -> np.ndarray:
    """Benjamini-Hochberg (1995) step-up FDR procedure at level `q`.

    Rejects ranks ``1..i`` for the largest rank ``i`` whose sorted p-value satisfies
    ``p_(i) <= i * q / m``. The per-rank bar grows with rank, so only the smallest
    p-value ever faces ``q / m`` -- why sizing can use that as a conservative upper
    bound, and why the exploratory SECONDARY tier uses BH rather than Bonferroni.

    Parameters
    ----------
    pvalues : np.ndarray
        P-values in input order.
    q : float
        False-discovery-rate level.

    Returns
    -------
    np.ndarray
        boolean mask in `pvalues`' input order, not sorted order
    """
    pvalues = np.asarray(pvalues, dtype=float)
    if pvalues.ndim != 1:
        raise ValueError(f"pvalues must be 1-D, got shape {pvalues.shape}")
    if not (0.0 < q <= 1.0):
        raise ValueError(f"q must be in (0, 1], got {q}")
    m = pvalues.size
    reject = np.zeros(m, dtype=bool)
    if m == 0:
        return reject
    order = np.argsort(pvalues, kind="stable")
    sorted_p = pvalues[order]
    thresholds = (np.arange(1, m + 1) / m) * q
    passed = np.nonzero(sorted_p <= thresholds)[0]
    if passed.size == 0:
        return reject
    cutoff_rank = int(passed.max())  # 0-indexed; largest i (1-indexed) satisfying p_(i) <= i*q/m
    reject[order[: cutoff_rank + 1]] = True
    return reject


# --------------------------------------------------------------------------- #
# Loading: pair per-cell joint outcomes across every model in the requested
# set, from one or more JSONL row files.
# --------------------------------------------------------------------------- #
def _warn_unverified(reasons: list[str]) -> None:
    """Print a hard-to-miss stderr banner that loaded rows are unverified.

    Called by `load_joint_cells` for an ``all_rows.jsonl`` input or an
    ``"unverified"`` cell row.

    Parameters
    ----------
    reasons : list[str]
        Each `reasons` entry becomes one banner line, verbatim.
    """
    lines = [f"!!  {reason}" for reason in reasons] + [
        "!!",
        '!!  Every "success" verdict in the affected rows is a GENERATION-TIME',
        '!!  PLACEHOLDER (verdict == "unverified"), never a real Lean-checked',
        "!!  proof -- generation runs on a venv without lean_dojo and cannot",
        "!!  verify anything itself. EVERY success rate this script prints will",
        "!!  therefore read at or near 0.000 -- indistinguishable from a genuine",
        "!!  'every model failed everything' finding unless you know to expect",
        "!!  this.",
        "!!",
        "!!  Run scripts/deduction/lean_verify_rows.py (the deferred verification pass",
        '!!  that replays candidates against real Lean and writes the sibling',
        "!!  verified_rows.jsonl) before trusting ANY number below.",
    ]
    print(_banner("WARNING: UNVERIFIED LEAN VERDICTS IN LOADED ROWS", lines),
          file=sys.stderr)


#: Verdicts meaning "this cell was never measured for ANY model" (reasoning and
#: measurements in load_joint_cells): cells carrying only these are excluded from
#: the paired blocks rather than scored 0.
#: Must equal `smolbench.deduction.lean.runner.NEVER_MEASURED_VERDICTS`, restated
#: rather than imported because that module pulls the provider and corpus stacks
#: this ``uv run --no-project`` script cannot load; drift makes this loader and
#: `lean_verify_rows.py` disagree about what "measured" means for the same rows.
UNMEASURABLE_VERDICTS: frozenset = frozenset({"exception", "replay_failed"})


def reject_unverified_verdicts(rows: Iterable[dict[str, Any]], field: str, source: str | Path) -> None:
    """Refuse rows that still carry the ungraded ``"unverified"`` sentinel.

    A warning isn't enough: the sentinel is deliberately not in `UNMEASURABLE_VERDICTS`,
    so `grade_verdicts` would otherwise score it as a real failure, making the report
    come out complete, plausible, and wrong.

    `rows` is already-parsed, from ONE source file. `field` is explicit because callers
    differ (`error_bars.lane_outcomes` checks ``"verdict"`` on primary rows and
    ``"recovered_verdict"`` on its recovery sibling, which has no ``"verdict"``).

    Parameters
    ----------
    rows : Iterable[dict[str, Any]]
        Already-parsed rows from one source file.
    field : str
        Verdict field to inspect.
    source : str | Path
        Source file represented by the rows.

    Raises
    ------
    SystemExit
        if any row has ``kind == "cell"`` and ``row[field] == "unverified"``.
    """
    count = sum(
        1 for row in rows
        if row.get("kind") == "cell" and row.get(field) == "unverified"
    )
    if count == 0:
        return
    raise SystemExit(
        _banner(
            "REFUSING UNVERIFIED ROW(S)",
            [f"!!  {count} cell row(s) in {source} still carry the",
             f'!!  generation-time placeholder "unverified" in their '
             f"{field!r} field.",
             "!!",
             "!!  This field is filled in LATER, by a deferred verification",
             "!!  pass that replays each candidate against real Lean -- a row",
             "!!  still reading \"unverified\" here means that pass silently",
             "!!  never reached it, not that the candidate failed. Loading it",
             "!!  anyway scores a NEVER-MEASURED cell as a real outcome,",
             "!!  biasing every rate and paired statistic that includes it",
             "!!  downward, and doing so invisibly: the report comes out",
             "!!  complete and plausible, not obviously wrong.",
             "!!",
             "!!  Run the verification pass to completion for this file",
             "!!  before loading it for analysis."]
        )
    )


def grade_verdicts(verdicts: Iterable[str | None]) -> int | None:
    """Grade ONE cell from its rows' verdicts in file order (chronological).

    Earliest surviving attempt wins, since a later retry is an independent draw and
    taking it would report pass@N as pass@1; an `UNMEASURABLE_VERDICTS` verdict is not
    a measurement, so it neither scores 0 nor claims the cell.

    Callers resolve None differently: this file and ``hint_vs_noise.load_rungs`` leave
    the cell absent, ``error_bars.build_pool`` may score it 0 when another lane graded
    it.

    Parameters
    ----------
    verdicts : Iterable[str | None]
        Cell verdicts in file order.

    Returns
    -------
    int | None
        1 (success), 0 (failure), or None (no surviving attempt)
    """
    for verdict in verdicts:
        if verdict in UNMEASURABLE_VERDICTS:
            continue
        return 1 if verdict == "success" else 0
    return None


def load_joint_cells(
    row_files: list[Path], models: tuple[str, ...] | None = None,
) -> tuple[list[str], dict, list[str]]:
    """Load and pair per-cell joint outcomes across one or more run files.

    Reads only ``kind == "cell"``, ``replicate_idx == 0`` rows: this study collects
    R=1, so a ``replicate_idx > 0`` row is dropped, not aggregated, even once a run
    starts writing real replicates (`N_REPLICATES_GRID` only sizes a FUTURE need).
    Prints one stderr warning per call naming the dropped-row count and file(s).

    Prints the `_warn_unverified` banner if any input is named ``all_rows.jsonl`` or
    any loaded cell is still ``"unverified"``.

    Parameters
    ----------
    row_files : list[Path]
        Row files to load and pair.
    models : tuple[str, ...] | None, optional
        Restrict pairing to this set (default: every model present); a cell is
        kept only if graded for EVERY member.

    Returns
    -------
    tuple[list[str], dict, list[str]]
        Sorted paired spec-keys; ``{theorem_id: {(k, prompt_rung): {model: 1 or
        0}}}`` restricted to fully-graded cells; sorted distinct ``rung`` values
        present.
    """
    reject_superseded(row_files)
    cell_rows: list[dict] = []
    warn_reasons: list[str] = []
    unverified_count = 0
    # Kept PER FILE, not just a grand total, so the warning can name exactly which
    # file(s) carried R>1 rows.
    dropped_replicates: dict[Path, int] = {}
    for path in row_files:
        if path.name == "all_rows.jsonl":
            warn_reasons.append(
                f"{path} is named all_rows.jsonl -- the UNVERIFIED "
                f"generation-time log, not verified_rows.jsonl."
            )
        for line in path.read_text().splitlines():
            if not line:
                continue
            row = json.loads(line)
            if row.get("kind") != "cell":
                continue
            if row.get("replicate_idx", 0) != 0:
                dropped_replicates[path] = dropped_replicates.get(path, 0) + 1
                continue
            if row.get("verdict") == "unverified":
                unverified_count += 1
            cell_rows.append(row)
    if unverified_count:
        warn_reasons.append(
            f'{unverified_count} loaded cell row(s) carry verdict == "unverified".'
        )
    if dropped_replicates:
        total_dropped = sum(dropped_replicates.values())
        detail = "; ".join(
            f"{path}: {n}" for path, n in dropped_replicates.items()
        )
        print(
            f"WARNING: load_joint_cells dropped {total_dropped} row(s) with "
            f"replicate_idx > 0 (this study collects R=1; rows past "
            f"replicate_idx == 0 are DISCARDED, not aggregated) -- {detail}",
            file=sys.stderr,
        )
    if warn_reasons:
        _warn_unverified(warn_reasons)

    present_models = sorted({row["model"] for row in cell_rows})
    wanted = sorted(models) if models is not None else present_models
    wanted_set = set(wanted)

    # theorem_id -> (k, prompt_rung) -> model -> outcome (1 success / 0 fail)
    #
    # Two row rules, implemented once in `grade_verdicts` (shared by
    # error_bars.lane_outcomes and hint_vs_noise.load_rungs):
    #
    #  * EARLIEST SURVIVING ATTEMPT WINS. A cell can own several rows in file
    #    (chronological) order; last-wins would take a RESAMPLED retry (generation
    #    isn't deterministic across server processes) and report pass@N as pass@1.
    #
    #  * UNMEASURABLE verdicts don't score 0. Two kinds mean the model was never
    #    tested:
    #      "exception" -- generation produced no answer (infra fault, e.g.
    #          deepseek-v3.1: 415 cells, 44% of its lane), not a model failure.
    #      "replay_failed" -- verification couldn't be set up (missing traced-cache
    #          AST, or the ground-truth k-tactic prefix wouldn't replay), before the
    #          candidate is even considered. Not model behaviour: a byte-identical
    #          232-cell set (151 DojoInit + 81 prefix) across all 21 models.
    #    Scoring replay_failed as 0 would deflate every marginal rate by up to
    #    232/944 = 24.6% (e.g. gemma-4-e2b 0.110 -> 0.083); paired McNemar survives
    #    it (concordant zeros cancel) but every rate would be wrong. Measurable
    #    denominator is 944 - 232 = 712 per lane.
    #
    #    "incomplete" stays OUT of this set (cell sets differ per model: 68/30/50,
    #    8 shared -- real behaviour). "no_answer" also stays out: it means the
    #    request completed and the model produced nothing extractable (often
    #    truncated inside <think>), a real miss on this study's axis, unlike
    #    exception/replay_failed where the attempt never completed.
    #
    #    Unmeasurable cells are left ABSENT, so the paired filter below drops them
    #    from every model's block -- what "not measured" means in a paired design.
    raw: dict[str, dict[tuple, dict[str, int]]] = {}
    for row in cell_rows:
        model = row["model"]
        if model not in wanted_set:
            continue
        # `grade_verdicts` returns None for a non-measurement, so that row neither
        # scores nor claims the cell -- the rules above, unrolled one row at a time.
        grade = grade_verdicts([row.get("verdict")])
        if grade is None:
            continue  # never measured -- see above
        cell_key = (row["k"], row["rung"])  # row["rung"] is this file's prompt_rung
        by_model = raw.setdefault(row["theorem_id"], {}).setdefault(cell_key, {})
        if model in by_model:
            continue  # an earlier attempt already answered this cell
        by_model[model] = grade

    # Paired filter: keep only cells graded for the FULL requested model set.
    blocks: dict[str, dict[tuple, dict[str, int]]] = {}
    n_wanted = len(wanted_set)
    for thm, cmap in raw.items():
        kept = {ck: mv for ck, mv in cmap.items() if len(mv) == n_wanted}
        if kept:
            blocks[thm] = kept

    prompt_rungs = sorted({ck[1] for cmap in blocks.values() for ck in cmap})
    return wanted, blocks, prompt_rungs


def marginal_rates(models: list[str], blocks: dict) -> dict[str, float]:
    """Each model's pass@1 rate over all paired `blocks` cells (the pilot point
    estimate); ``float("nan")`` for every model if `blocks` is empty.

    Parameters
    ----------
    models : list[str]
        Models to score.
    blocks : dict
        Paired theorem cells.

    Returns
    -------
    dict[str, float]
        pass@1 rate for each model
    """
    succ = {m: 0 for m in models}
    tot = 0
    for cmap in blocks.values():
        for mv in cmap.values():
            tot += 1
            for m in models:
                succ[m] += mv[m]
    return {m: (succ[m] / tot if tot else float("nan")) for m in models}


def union_solvable_fraction(models: list[str], blocks: dict) -> float:
    """Fraction of paired cells solved by at least one of `models` (NaN if empty).

    Feeds `passn_power`'s "solvable at all" anchor. Called with just a contrast's two
    models, never the whole roster: across 21 models "did any solve it" trends to 1.0
    regardless of the pair.

    Parameters
    ----------
    models : list[str]
        Models in the contrast.
    blocks : dict
        Paired theorem cells.

    Returns
    -------
    float
        fraction of paired cells solved by at least one model
    """
    solved = tot = 0
    for cmap in blocks.values():
        for mv in cmap.values():
            tot += 1
            solved += 1 if any(mv[m] for m in models) else 0
    return solved / tot if tot else float("nan")


def pooled_discordant_counts(blocks: dict, model_a: str, model_b: str) -> tuple:
    """Pooled McNemar discordant counts for one model pair.

    Pooled over every paired theorem and prompt rung, unstratified -- the conservative
    single-stratum collapse of the rung-stratified CMH test.

    Parameters
    ----------
    blocks : dict
        Paired theorem cells.
    model_a : str
        First model in the pair.
    model_b : str
        Second model in the pair.

    Returns
    -------
    tuple
        (b, c): `model_a` succeeds and `model_b` fails, and the reverse
    """
    disc_b = disc_c = 0
    for cmap in blocks.values():
        for mv in cmap.values():
            oa, ob = mv[model_a], mv[model_b]
            if oa == 1 and ob == 0:
                disc_b += 1
            elif oa == 0 and ob == 1:
                disc_c += 1
    return disc_b, disc_c


# --------------------------------------------------------------------------- #
# Contrast families.
# --------------------------------------------------------------------------- #
def build_within_family_contrasts() -> list:
    """Build the 21 PRIMARY within-family ladder contrasts (7 families x C(3,2)).

    Returns (label, model_a, model_b) tuples grouped by family in `FAMILIES` order;
    within a family, pairs follow ``combinations(range(3), 2)`` -- (0,1), (0,2), (1,2).
    """
    contrasts: list[_Contrast] = []
    for family, ladder in FAMILIES.items():
        for pos_a, pos_b in combinations(range(3), 2):
            model_a, model_b = ladder[pos_a], ladder[pos_b]
            label = f"[{family} ladder] {model_a} vs {model_b}"
            contrasts.append((label, model_a, model_b))
    return contrasts


_LADDER_POS_NAMES = ("small", "mid", "large")


def build_cross_family_contrasts() -> list:
    """Build the 63 SECONDARY cross-family, size-matched contrasts (3 ladder positions
    x C(7,2) = 21 family pairs); every label carries "SECONDARY" so this tier can't be
    mistaken for a primary result.

    Returns (label, model_a, model_b) tuples grouped by ladder position, then by
    `FAMILIES` order.
    """
    contrasts: list[_Contrast] = []
    for ladder_pos in range(3):
        pos_name = _LADDER_POS_NAMES[ladder_pos]
        for fam_a, fam_b in combinations(FAMILIES, 2):
            model_a = FAMILIES[fam_a][ladder_pos]
            model_b = FAMILIES[fam_b][ladder_pos]
            label = f"[SECONDARY | {pos_name}] {model_a} vs {model_b}"
            contrasts.append((label, model_a, model_b))
    return contrasts


if len(build_within_family_contrasts()) != N_PRIMARY:
    raise ValueError(
        f"N_PRIMARY={N_PRIMARY} but the within-family builder returns "
        f"{len(build_within_family_contrasts())} contrasts; ALPHA_PRIMARY is frozen"
    )
if len(build_cross_family_contrasts()) != N_SECONDARY:
    raise ValueError(
        f"N_SECONDARY={N_SECONDARY} but the cross-family builder returns "
        f"{len(build_cross_family_contrasts())} contrasts; ALPHA_SECONDARY is frozen"
    )


# --------------------------------------------------------------------------- #
# n_theorems sizing: block bootstrap of the observed joint cells (pass@1).
# --------------------------------------------------------------------------- #
def bootstrap_power(
    blocks: dict,
    model_a: str,
    model_b: str,
    n_theorems: int,
    *,
    alpha: float,
    sims: int,
    rng: np.random.Generator,
) -> tuple:
    """Bootstrap McNemar power and the paired rate-gap CI for one model pair.

    Resamples `n_theorems` whole theorem blocks with replacement from `blocks`, pools
    their cells, and computes McNemar's exact p over `sims` simulations.

    Parameters
    ----------
    blocks : dict
        Paired theorem cells.
    model_a : str
        First model in the pair.
    model_b : str
        Second model in the pair.
    n_theorems : int
        Theorem blocks sampled per simulation.
    alpha : float
        McNemar significance threshold.
    sims : int
        Number of bootstrap simulations.
    rng : np.random.Generator
        Freshly seeded by the caller (see `_seed_of`) so runs are byte-identical.

    Returns
    -------
    tuple
        (power, gap_lo, gap_hi): rejection fraction at `alpha`, and the
        5th/95th-percentile bootstrap CI of ``rate_a - rate_b`` (for the near-tie
        verdict)
    """
    thm_ids = list(blocks.keys())
    # Pre-flatten each theorem's per-cell (a, b) outcomes so the inner sim loop
    # is pure integer accumulation, not dict walking.
    per_thm = {
        t: np.array([(cmap[ck][model_a], cmap[ck][model_b]) for ck in cmap], dtype=np.int8)
        for t, cmap in blocks.items()
    }
    idx = np.arange(len(thm_ids))
    rejects = 0
    gaps = np.empty(sims)
    for s in range(sims):
        pick = rng.choice(idx, size=n_theorems, replace=True)
        stacked = np.concatenate([per_thm[thm_ids[i]] for i in pick])
        oa, ob = stacked[:, 0], stacked[:, 1]
        disc_b = int(np.sum((oa == 1) & (ob == 0)))
        disc_c = int(np.sum((oa == 0) & (ob == 1)))
        if mcnemar_exact_p(disc_b, disc_c) < alpha:
            rejects += 1
        gaps[s] = oa.mean() - ob.mean()
    return rejects / sims, float(np.quantile(gaps, 0.05)), float(np.quantile(gaps, 0.95))


# --------------------------------------------------------------------------- #
# n_replicates advisory: Beta-mixture pass@N (projects unobserved replicates).
# --------------------------------------------------------------------------- #
def passn_power(
    rate_a: float,
    rate_b: float,
    frac_solvable: float,
    n_theorems: int,
    n_replicates: int,
    n_prompt_rungs: int,
    *,
    alpha: float,
    sims: int,
    beta_conc: float,
    rng: np.random.Generator,
) -> float:
    """Project McNemar power for a pair at `n_replicates`, via the Beta mixture.

    Each theorem is solvable with probability `frac_solvable` (the SAME theorems for
    both models); each solvable cell draws a per-replicate success probability from
    ``Beta(m * beta_conc, (1 - m) * beta_conc)``, ``m = rate / frac_solvable`` being the
    model's calibrated solvable-cell mean. `pass_at_n` converts cells to pass@N;
    McNemar's p is computed per simulation on an `n_theorems` x `n_prompt_rungs` grid.

    Adding replicates re-samples the SAME theorem's difficulty, so this saturates:
    theorems, not replicates, are the lever.

    Parameters
    ----------
    rate_a : float
        First model's pass@1 rate.
    rate_b : float
        Second model's pass@1 rate.
    frac_solvable : float
        From `union_solvable_fraction` on just this pair; must be ``> 0``.
    n_theorems : int
        Number of theorem blocks per simulation.
    n_replicates : int
        Replicates per cell.
    n_prompt_rungs : int
        Prompt rungs per theorem.
    alpha : float
        McNemar significance threshold.
    sims : int
        Number of simulations.
    beta_conc : float
        Beta-mixture concentration.
    rng : np.random.Generator
        Random-number generator.

    Returns
    -------
    float
        rejection fraction at `alpha`, or ``nan`` if either model's implied
        solvable-cell mean falls outside ``(0, 1]``
    """
    ma = rate_a / frac_solvable
    mb = rate_b / frac_solvable
    if not (0 < ma <= 1 and 0 < mb <= 1):
        return float("nan")  # solvable fraction too small/large to host this rate
    rejects = 0
    shape = (n_theorems, n_prompt_rungs)
    for _ in range(sims):
        solvable = rng.random(n_theorems) < frac_solvable
        solv_cell = np.repeat(solvable[:, None], n_prompt_rungs, axis=1)
        pa = np.where(solv_cell, rng.beta(ma * beta_conc, (1 - ma) * beta_conc, shape), 0.0)
        pb = np.where(solv_cell, rng.beta(mb * beta_conc, (1 - mb) * beta_conc, shape), 0.0)
        sa = pass_at_n(pa, n_replicates)
        sb = pass_at_n(pb, n_replicates)
        oa = rng.random(shape) < sa
        ob = rng.random(shape) < sb
        disc_b = int(np.sum(oa & ~ob))
        disc_c = int(np.sum(~oa & ob))
        if mcnemar_exact_p(disc_b, disc_c) < alpha:
            rejects += 1
    return rejects / sims


def needed_replicates(
    rate_a: float,
    rate_b: float,
    frac_solvable: float,
    n_theorems: int,
    n_prompt_rungs: int,
    *,
    alpha: float,
    sims: int,
    beta_conc: float,
    rng: np.random.Generator,
    grid: tuple = N_REPLICATES_GRID,
    target: float = POWER_TARGETS[0],
) -> int | None:
    """Smallest `grid` value whose `passn_power` reaches `target`, else ``None``.

    Scans `grid` ascending, stopping at the first sufficient point. ``None`` also
    covers the uncalibratable case where `passn_power` is NaN at every grid point,
    which no number of replicates can fix.

    Parameters
    ----------
    rate_a : float
        First model's pass@1 rate.
    rate_b : float
        Second model's pass@1 rate.
    frac_solvable : float
        Fraction of cells solvable by either model.
    n_theorems : int
        Number of theorem blocks per simulation.
    n_prompt_rungs : int
        Prompt rungs per theorem.
    alpha : float
        McNemar significance threshold.
    sims : int
        Number of simulations.
    beta_conc : float
        Beta-mixture concentration.
    rng : np.random.Generator
        Random-number generator.
    grid : tuple, optional
        Replicate counts to scan.
    target : float, optional
        Required rejection fraction.

    Returns
    -------
    int | None
        first sufficient `grid` value, or ``None``
    """
    for n_rep in sorted(grid):
        power = passn_power(
            rate_a, rate_b, frac_solvable, n_theorems, n_rep, n_prompt_rungs,
            alpha=alpha, sims=sims, beta_conc=beta_conc, rng=rng,
        )
        if not np.isnan(power) and power >= target:
            return n_rep
    return None


# --------------------------------------------------------------------------- #
# Per-contrast sizing result + computation.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ContrastSizing:
    """One model-pair contrast's observed statistics and sizing result.

    n_paired_theorems: ``len(blocks)``, identical across every contrast from the same
        `blocks`.
    observed_gap: ``rates[model_a] - rates[model_b]`` on the current R=1 pilot.
    observed_p: McNemar exact two-sided p, pooled over all paired cells and prompt
        rungs; observed, not a projection.
    theorem_curve, r_theorems: block-bootstrap power at each `N_THEOREMS_GRID` point,
        and the smallest grid point reaching each `POWER_TARGETS` level (None if none).
    ci_lo, ci_hi: bootstrap 5th/95th-percentile CI of the paired rate gap at the
        LARGEST `N_THEOREMS_GRID` point.
    near_tie: True only if `observed_gap` and ``[ci_lo, ci_hi]`` both fall inside
        ``+/- EQUIV_BAND`` -- a certified equivalence, not an unresolved test.
    needed_replicates: smallest `N_REPLICATES_GRID` point the Beta-mixture projects to
        reach ``POWER_TARGETS[0]`` at the current `n_paired_theorems`.
    """

    label: str
    model_a: str
    model_b: str
    n_paired_theorems: int
    observed_gap: float
    observed_p: float
    theorem_curve: tuple
    r_theorems: dict
    ci_lo: float
    ci_hi: float
    near_tie: bool
    needed_replicates: int | None


def compute_contrast_sizing(
    blocks: dict,
    label: str,
    model_a: str,
    model_b: str,
    rates: dict,
    prompt_rungs: list,
    *,
    alpha: float,
    sims: int,
) -> ContrastSizing | None:
    """Compute one contrast's observed statistics plus its sizing projections.

    Reseeds two independent generators per contrast (bootstrap curve, replicate
    projection), both derived from ``(model_a, model_b)`` via `_seed_of`, so re-running
    produces byte-identical output.

    Parameters
    ----------
    blocks : dict
        Paired theorem cells.
    label : str
        Contrast label.
    model_a : str
        First model in the contrast.
    model_b : str
        Second model in the contrast.
    rates : dict
        Observed pass@1 rates by model.
    prompt_rungs : list
        Used only for its length (the Beta-mixture's per-theorem cell count).
    alpha : float
        Significance threshold for sizing simulations.
    sims : int
        Number of simulations per grid point.

    Returns
    -------
    ContrastSizing | None
        None if either model is absent from `rates`, so a pre-registered contrast the
        current data doesn't cover is skipped, not raised on
    """
    if model_a not in rates or model_b not in rates:
        return None

    n_theorems = len(blocks)
    disc_b, disc_c = pooled_discordant_counts(blocks, model_a, model_b)
    observed_p = mcnemar_exact_p(disc_b, disc_c)
    gap = rates[model_a] - rates[model_b]

    rng_thm = np.random.default_rng([SEED, _seed_of(model_a), _seed_of(model_b)])
    curve: list[float] = []
    ci_lo = ci_hi = 0.0
    for n in N_THEOREMS_GRID:
        power, lo, hi = bootstrap_power(
            blocks, model_a, model_b, n, alpha=alpha, sims=sims, rng=rng_thm
        )
        curve.append(power)
        ci_lo, ci_hi = lo, hi  # keep the LARGEST grid point's CI (last iteration)
    r_theorems = {
        target: next((n for n, pw in zip(N_THEOREMS_GRID, curve) if pw >= target), None)
        for target in POWER_TARGETS
    }
    near_tie = abs(gap) < EQUIV_BAND and ci_hi <= EQUIV_BAND and ci_lo >= -EQUIV_BAND

    # frac_solvable is calibrated to THIS PAIR ONLY (see union_solvable_fraction).
    frac_solv = union_solvable_fraction([model_a, model_b], blocks)
    needed: int | None = None
    if frac_solv > 0:
        rng_rep = np.random.default_rng([SEED, 7, _seed_of(model_a), _seed_of(model_b)])
        needed = needed_replicates(
            rates[model_a], rates[model_b], frac_solv, n_theorems, len(prompt_rungs),
            alpha=alpha, sims=sims, beta_conc=BETA_CONC, rng=rng_rep,
            target=POWER_TARGETS[0],
        )

    return ContrastSizing(
        label=label,
        model_a=model_a,
        model_b=model_b,
        n_paired_theorems=n_theorems,
        observed_gap=gap,
        observed_p=observed_p,
        theorem_curve=tuple(curve),
        r_theorems=r_theorems,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        near_tie=near_tie,
        needed_replicates=needed,
    )


def _verdict_text(sizing: ContrastSizing) -> str:
    """Format a one-line DIFFERENCE/NEAR-TIE/UNRESOLVED verdict for a sizing result."""
    r80 = sizing.r_theorems[POWER_TARGETS[0]]
    if r80 is not None:
        return f"DIFFERENCE -- >= {POWER_TARGETS[0]:.0%} power at n_theorems={r80}"
    if sizing.near_tie:
        return (
            f"NEAR-TIE -- equivalent within [{sizing.ci_lo:+.2f},{sizing.ci_hi:+.2f}] "
            f"(band +/-{EQUIV_BAND:.2f}) at n_theorems={N_THEOREMS_GRID[-1]}"
        )
    return (
        f"UNRESOLVED at n_theorems<={N_THEOREMS_GRID[-1]} "
        f"(neither a difference nor a certified near-tie)"
    )


def _print_tier_report(
    tier_label: str,
    contrasts: list,
    blocks: dict,
    rates: dict,
    prompt_rungs: list,
    *,
    secondary: bool,
    sims: int,
) -> None:
    """Compute and print one contrast tier's observed + sizing report.

    `contrasts`: the tier's full pre-registered list (21 or 63); contrasts whose
    models are absent from the loaded data are skipped with a summary line, not
    silently.

    Parameters
    ----------
    tier_label : str
        Label displayed for the contrast tier.
    contrasts : list
        Full pre-registered list of contrasts.
    blocks : dict
        Paired theorem cells.
    rates : dict
        Observed pass@1 rates by model.
    prompt_rungs : list
        Prompt rungs represented in the paired cells.
    secondary : bool
        True = SECONDARY cross-family tier (sized at `ALPHA_SECONDARY`, decided by
        `benjamini_hochberg` at `Q_SECONDARY`); False = PRIMARY, at the fixed
        `ALPHA_PRIMARY` Bonferroni threshold.
    sims : int
        Number of simulations per grid point.
    """
    alpha_sizing = ALPHA_SECONDARY if secondary else ALPHA_PRIMARY
    sizings: list[ContrastSizing] = []
    skipped: list[str] = []
    for label, model_a, model_b in contrasts:
        sizing = compute_contrast_sizing(
            blocks, label, model_a, model_b, rates, prompt_rungs,
            alpha=alpha_sizing, sims=sims,
        )
        if sizing is None:
            skipped.append(label)
        else:
            sizings.append(sizing)

    tag = "SECONDARY -- " if secondary else "PRIMARY -- "
    print(f"\n{'=' * 78}")
    print(
        f"=== {tag}{tier_label} ({len(contrasts)} pre-registered, "
        f"{len(sizings)} with paired data, {len(skipped)} skipped) ==="
    )
    print("=" * 78)
    if secondary:
        print(
            f"SECONDARY TIER: exploratory, NOT a pre-registered primary result. "
            f"Corrected with Benjamini-Hochberg FDR control (q={Q_SECONDARY}) over "
            f"the observed p-values below; sizing simulations use the conservative "
            f"rank-1 threshold alpha={ALPHA_SECONDARY:.6f} "
            f"(={Q_SECONDARY}/{N_SECONDARY}, an upper bound -- see "
            f"benjamini_hochberg's docstring)."
        )
    else:
        print(
            f"PRIMARY TIER: Bonferroni-corrected, alpha={ALPHA_PRIMARY:.6f} "
            f"(={ALPHA}/{N_PRIMARY})."
        )
    if skipped:
        shown = ", ".join(skipped[:5])
        more = f", ... (+{len(skipped) - 5} more)" if len(skipped) > 5 else ""
        print(
            f"  {len(skipped)} contrast(s) skipped -- model(s) not in the "
            f"currently loaded/paired set: {shown}{more}"
        )
    if not sizings:
        print("  no contrasts with paired data in this tier.")
        return

    print(
        "\n  CAVEAT: prior work on this benchmark found n_theorems, NOT replicates, "
        "to be the effective lever for statistical power --\n"
        "  adding replicates re-samples the SAME theorem's difficulty and saturates "
        "(see passn_power's docstring), while adding theorems\n"
        "  adds independent blocks. The 'needed R' projection below is reported "
        "because it was asked for; read it against this finding,\n"
        "  not as an endorsement that more replicates is the efficient lever.\n"
    )

    pvals = np.array([s.observed_p for s in sizings])
    reject_mask = benjamini_hochberg(pvals, Q_SECONDARY) if secondary else pvals < ALPHA_PRIMARY

    for sizing, rejected in zip(sizings, reject_mask):
        print(f"  {sizing.label}")
        print(
            f"      observed: {sizing.model_a}={rates[sizing.model_a]:.3f} vs "
            f"{sizing.model_b}={rates[sizing.model_b]:.3f}  "
            f"(gap {sizing.observed_gap:+.3f}, n={sizing.n_paired_theorems} paired theorems)"
        )
        sig_word = "REJECT null (significant)" if rejected else "not significant"
        corr_name = "BH-adjusted" if secondary else "Bonferroni"
        print(f"      McNemar exact p = {sizing.observed_p:.4f}  [{corr_name}] -> {sig_word}")
        print(f"      n_theorems power curve (block bootstrap, {sims} sims):")
        grid_row = "        " + "  ".join(f"{n:>5d}" for n in N_THEOREMS_GRID)
        power_row = "        " + "  ".join(f"{p:5.2f}" for p in sizing.theorem_curve)
        print(grid_row)
        print(power_row)
        r80 = fmt_r(sizing.r_theorems[POWER_TARGETS[0]], N_THEOREMS_GRID[-1])
        r90 = fmt_r(sizing.r_theorems[POWER_TARGETS[1]], N_THEOREMS_GRID[-1])
        print(f"        R({POWER_TARGETS[0]:.0%}) = {r80}   R({POWER_TARGETS[1]:.0%}) = {r90}")
        needed_str = fmt_r(sizing.needed_replicates, N_REPLICATES_GRID[-1])
        print(
            f"      replicate (pass@N) projection at n_theorems="
            f"{sizing.n_paired_theorems} (Beta mixture, {sims} sims): "
            f"needed R = {needed_str}  (target {POWER_TARGETS[0]:.0%})"
        )
        print(f"      verdict: {_verdict_text(sizing)}")
        print()

    n_sig = int(np.sum(reject_mask))
    n_near_tie = sum(1 for s in sizings if s.near_tie)
    print(
        f"  Summary: {n_sig}/{len(sizings)} contrasts significant on the current "
        f"R=1 pilot; {n_near_tie} certified near-ties (band +/-{EQUIV_BAND:.2f})."
    )


# --------------------------------------------------------------------------- #
# CLI + report.
# --------------------------------------------------------------------------- #
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse this script's command-line arguments (`argv` defaults to ``sys.argv[1:]``)."""
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--s3",
        action="store_true",
        help=(
            f"Download this study's run files from s3://{S3_BUCKET}/<spool-prefix> "
            "into a temp dir and analyze those (preferring verified_rows.jsonl, "
            "falling back to all_rows.jsonl per run -- see the module docstring's "
            "warning about \"unverified\" verdicts). Overrides --results-dir. "
            "<spool-prefix> is set by "
            "--spool-prefix, below."
        ),
    )
    p.add_argument(
        "--spool-prefix",
        default=None,
        help=(
            "S3 key prefix the deduction lanes spooled under (default: "
            "LEAN_SPOOL_PREFIX, or deduction_postcutoff/runs if unset). "
            "Resolved after argument parsing, not here. Ignored unless --s3 "
            "is passed."
        ),
    )
    p.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        help=(
            "Local results directory to read "
            "<results-dir>/runs/scaling_*/verified_rows.jsonl from "
            "(default: %(default)s). Ignored if --s3 is passed."
        ),
    )
    p.add_argument(
        "--models",
        type=str,
        default=None,
        help=(
            "Comma-separated model spec-keys to restrict the paired cell set to "
            "(default: all 21 -- see MODELS). A cell is kept only if graded for "
            "EVERY listed model."
        ),
    )
    p.add_argument(
        "--sims",
        type=int,
        default=SIMS,
        help="Monte-Carlo simulations per grid point (default: %(default)s).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Load the requested run files (S3 or local), pair joint cells, print the report.

    Parameters
    ----------
    argv : list[str] | None, optional
        Command-line arguments.

    Returns
    -------
    int
        0 on a normal report, 1 if no row files or no fully-paired cells for the
        requested model set were found
    """
    args = parse_args(argv)
    models_filter = (
        tuple(m.strip() for m in args.models.split(",")) if args.models else None
    )

    if args.s3:
        # Resolved HERE, after parse_args: not a module constant and not an
        # argparse default, so a late LEAN_SPOOL_PREFIX takes effect.
        deduction_prefix = (args.spool_prefix or spool_prefix()) + "/"
        tmp_dir = Path(tempfile.mkdtemp(prefix="smolbench_deduction_power_"))
        print(
            f"Downloading run files from s3://{S3_BUCKET}/{deduction_prefix} into "
            f"{tmp_dir} ...",
            file=sys.stderr,
        )
        # `download_scaling_rows`, not `rows_source.resolve_rows_dir`: this script
        # needs the row-file LIST (it reports how many runs loaded) and must return 1
        # on an empty archive rather than raise. Both candidates are passed to keep
        # this script's documented all_rows.jsonl fallback -- the candidate name is
        # also the landed basename, so `load_joint_cells`'s unverified-input banner
        # still fires on it. `load_joint_cells` keys every model off the row's own
        # ``model`` field and never reads a directory name, so this same downloader
        # also serves `error_bars.py`/`hint_vs_noise.py`.
        row_files = download_scaling_rows(
            tmp_dir,
            prefix=deduction_prefix,
            candidates=("verified_rows.jsonl", "all_rows.jsonl"),
        )
        if not row_files:
            print(
                f"No run files found under s3://{S3_BUCKET}/{deduction_prefix} -- "
                f"nothing to analyze.",
                file=sys.stderr,
            )
            return 1
    else:
        row_files = sorted(args.results_dir.glob("runs/scaling_*/verified_rows.jsonl"))
        if not row_files:
            print(
                f"No verified_rows.jsonl files found under "
                f"{args.results_dir}/runs/scaling_*/ -- nothing to analyze. Pass "
                f"--s3 to download and analyze the live S3-backed runs, or "
                f"--results-dir to point at a different local results tree.",
                file=sys.stderr,
            )
            return 1

    models, blocks, prompt_rungs = load_joint_cells(row_files, models=models_filter)
    if not blocks:
        print(
            "No fully-paired cells for the requested model set -- nothing to "
            "analyze.",
            file=sys.stderr,
        )
        return 1

    rates = marginal_rates(models, blocks)
    n_thm = len(blocks)
    n_cells = sum(len(c) for c in blocks.values())

    print(
        f"Lean deduction family-ladder replicate-sizing power analysis "
        f"(seed={SEED}, sims/point={args.sims})"
    )
    print(
        f"Loaded {len(row_files)} run file(s); {len(models)} model(s) paired, "
        f"{n_thm} paired theorems, {n_cells} paired cells, "
        f"{len(prompt_rungs)} prompt rungs ({', '.join(prompt_rungs) or 'none'})."
    )
    print(
        f"Design: PRIMARY within-family tier {N_PRIMARY} contrasts (Bonferroni, "
        f"alpha={ALPHA_PRIMARY:.6f}); SECONDARY cross-family tier {N_SECONDARY} "
        f"contrasts (Benjamini-Hochberg, q={Q_SECONDARY}). Equivalence band "
        f"+/-{EQUIV_BAND:.2f}."
    )
    print("\nPer-model observed pass@1 rate (pilot point estimate), sorted descending:")
    for m in sorted(models, key=lambda m: -rates[m]):
        print(f"    {m:32s} {rates[m]:.3f}")

    _print_tier_report(
        "within-family ladder contrasts",
        build_within_family_contrasts(),
        blocks,
        rates,
        prompt_rungs,
        secondary=False,
        sims=args.sims,
    )
    _print_tier_report(
        "cross-family size-matched contrasts",
        build_cross_family_contrasts(),
        blocks,
        rates,
        prompt_rungs,
        secondary=True,
        sims=args.sims,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
