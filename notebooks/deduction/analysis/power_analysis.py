"""Power analysis for the Lean-4 deduction family-ladder study: 21 checkpoints, 7 vendor families x 3 rungs.

The study overloads "rung"; this file separates model ``ladder_pos`` from context ``prompt_rung``.
PRIMARY has 21 within-family Bonferroni contrasts; exploratory SECONDARY has 63 size-matched BH contrasts.
Both use a theorem block-bootstrap and Beta-mixture pass@N advisory: theorems, not replicates, are this benchmark's power lever.
Read ``verified_rows.jsonl``, never generation-time ``all_rows.jsonl``; its ``"unverified"`` placeholders can silently mimic universal failure.
"""

from __future__ import annotations

# Cap BLAS/OpenMP before numpy: its default pool exceeds shared-container RLIMIT_NPROC
# beside Dojo verifiers ("pthread_create failed"); one thread suffices.
import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import functools
import hashlib
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import binom

# _power_common.py is two levels up; anchor to __file__ for cwd independence.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Required for the bare sibling import: spec_from_file_location does not add this directory
# to sys.path, so rows_source would otherwise resolve only by accident.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ``uv run --no-project`` has no installed smolbench, so resolve study_config from source.
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
    _banner,
    reject_superseded,
    resolve_rows_dir,
    spool_prefix,
)

# Roster comes from the committed config; spec keys match JSONL ``model`` values.
# Family order must be SMALL -> MID -> LARGE: contrast builders pair by ladder position,
# so reordering silently re-pairs all 63 secondary contrasts.
FAMILIES: dict[str, tuple[str, ...]] = {
    family: tuple(rungs) for family, rungs in _study_families().items()
}
MODELS = tuple(_study_roster_keys())  # 21, the FAMILIES tuples concatenated

# Guard at import so constant consumers fail too; use raise because python -O strips
# asserts. A short family IndexErrors at contrast position 2; a long one fails the count.
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
SIMS = 4000  # Monte-Carlo simulations per grid point; matches the archived default.
#: Equivalence half-width: a 90% paired-gap CI inside it certifies a near-tie.
EQUIV_BAND = 0.10
#: Beta concentration (a + b) for the pass@N solvable-cell probability mixture.
BETA_CONC = 5.0

N_THEOREMS_GRID = (30, 60, 100, 150, 200, 300)
N_REPLICATES_GRID = (1, 2, 3, 4, 8)

# PRIMARY: 21 within-family contrasts (7 x C(3,2)); Bonferroni over the family.
N_PRIMARY = 21
ALPHA_PRIMARY = ALPHA / N_PRIMARY

# SECONDARY: 63 size-matched contrasts (3 x C(7,2)); BH FDR q=0.05. Sizing uses
# Q_SECONDARY/N_SECONDARY, the conservative rank-1 upper bound; decisions use actual BH.
N_SECONDARY = 63
Q_SECONDARY = 0.05
ALPHA_SECONDARY = Q_SECONDARY / N_SECONDARY

RESULTS_DIR = results_dir(__file__, up=1)

_Contrast = tuple[str, str, str]  # (label, model_a, model_b)


def _seed_of(name: str) -> int:
    """Derive a deterministic 32-bit seed from a model name.

    Use SHA-256, never salted builtin ``hash``, so RNG streams, power, and CIs reproduce.

    Parameters
    ----------
    name : str
        Model name.

    Returns
    -------
    int
        Deterministic seed.
    """
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "little")


# Hand-roll closed-form pass_at_n and BH; use declared scipy.stats.binom for McNemar.
def pass_at_n(p: np.ndarray | float, n: int) -> np.ndarray | float:
    """Return ``1 - (1 - p)**n`` for `n` independent replicates.

    Parameters
    ----------
    p : np.ndarray | float
        Per-replicate success probability.
    n : int
        Replicate count.

    Returns
    -------
    np.ndarray | float
        Probability of at least one success.
    """
    return 1.0 - (1.0 - np.asarray(p, dtype=float)) ** n


@functools.lru_cache(maxsize=None)
def mcnemar_exact_p(b: int, c: int) -> float:
    """Return McNemar's exact two-sided p-value for discordant counts.

    Parameters
    ----------
    b : int
        A-success/B-failure count.
    c : int
        B-success/A-failure count.

    Returns
    -------
    float
        Two-sided p-value; 1.0 when ``b + c == 0``.
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2.0 * binom.cdf(k, n, 0.5))


def benjamini_hochberg(pvalues: np.ndarray, q: float) -> np.ndarray:
    """Apply the Benjamini-Hochberg step-up FDR procedure at `q`.

    Sizing can use ``q/m`` as a conservative upper bound because only the smallest
    p-value faces it; the exploratory SECONDARY tier therefore uses BH, not Bonferroni.

    Parameters
    ----------
    pvalues : np.ndarray
        P-values in input order.
    q : float
        False-discovery-rate level.

    Returns
    -------
    np.ndarray
        Rejection mask in input order.
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


def _warn_unverified(reasons: list[str]) -> None:
    """Print a hard-to-miss stderr banner that loaded rows are unverified.

    Parameters
    ----------
    reasons : list[str]
        Banner lines.
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


#: Cells with only these verdicts are excluded, not scored 0. Must equal
#: `smolbench.deduction.lean.runner.NEVER_MEASURED_VERDICTS`; restate it because that
#: provider/corpus module cannot load under ``uv run --no-project``, and drift would make
#: this loader and `lean_verify_rows.py` disagree on what was measured.
UNMEASURABLE_VERDICTS: frozenset = frozenset({"exception", "replay_failed"})


def reject_unverified_verdicts(rows: Iterable[dict[str, Any]], field: str, source: str | Path) -> None:
    """Refuse rows with the ungraded ``"unverified"`` sentinel.

    It is not unmeasurable, so grading it as failure would yield a plausible, wrong report.
    `field` differs because `error_bars.lane_outcomes` reads ``"verdict"`` on primary
    rows and ``"recovered_verdict"`` on recovery rows, which lack ``"verdict"``.

    Parameters
    ----------
    rows : Iterable[dict[str, Any]]
        Parsed rows from one source.
    field : str
        Verdict field.
    source : str | Path
        Source file.

    Raises
    ------
    SystemExit
        For an unverified cell row.
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
    """Grade one cell's chronological verdicts.

    Earliest surviving attempt wins: a retry is an independent draw, so later-wins reports
    pass@N as pass@1. Unmeasurable verdicts neither score 0 nor claim the cell.
    This file and ``hint_vs_noise.load_rungs`` leave None absent; `error_bars.build_pool`
    may score it 0 when another lane graded it.

    Parameters
    ----------
    verdicts : Iterable[str | None]
        Verdicts in file order.

    Returns
    -------
    int | None
        1, 0, or None when no attempt survives.
    """
    for verdict in verdicts:
        if verdict in UNMEASURABLE_VERDICTS:
            continue
        return 1 if verdict == "success" else 0
    return None


def load_joint_cells(
    row_files: list[Path], models: tuple[str, ...] | None = None,
) -> tuple[list[str], dict, list[str]]:
    """Load paired per-cell outcomes from run files.

    This R=1 study drops, never aggregates, ``replicate_idx > 0`` rows; that grid sizes a
    future need. Warn for dropped rows and ``all_rows.jsonl``/``"unverified"`` input.

    Parameters
    ----------
    row_files : list[Path]
        Row files.
    models : tuple[str, ...] | None, optional
        Pairing set; cells require every member.

    Returns
    -------
    tuple[list[str], dict, list[str]]
        Sorted models, fully graded blocks, and prompt rungs.
    """
    reject_superseded(row_files)
    cell_rows: list[dict] = []
    warn_reasons: list[str] = []
    unverified_count = 0
    # Keep counts per file so the warning identifies R>1 sources.
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

    # theorem_id -> (k, prompt_rung) -> model -> outcome (1 success / 0 fail).
    # `grade_verdicts`, shared with error_bars.lane_outcomes and hint_vs_noise.load_rungs,
    # keeps the earliest attempt: later retries are independent draws, so last-wins is pass@N.
    # ``exception`` is not failure (e.g. deepseek-v3.1: 415 cells, 44% infra faults).
    # ``replay_failed`` is not behaviour: 232 cells (151 DojoInit + 81 prefix) across all
    # 21 models failed setup before candidates. Scoring it 0 deflates rates by 232/944 =
    # 24.6% (gemma-4-e2b 0.110 -> 0.083); McNemar's concordant zeros cancel, but rates are
    # wrong. The measurable denominator is 944 - 232 = 712 per lane. ``incomplete`` stays
    # measured (model-specific 68/30/50 cells, 8 shared); ``no_answer`` is a real completed
    # miss. Leave unmeasurable cells absent so paired blocks drop unmeasured cells.
    raw: dict[str, dict[tuple, dict[str, int]]] = {}
    for row in cell_rows:
        model = row["model"]
        if model not in wanted_set:
            continue
        # None neither scores nor claims the cell.
        grade = grade_verdicts([row.get("verdict")])
        if grade is None:
            continue  # never measured -- see above
        cell_key = (row["k"], row["rung"])  # row["rung"] is this file's prompt_rung
        by_model = raw.setdefault(row["theorem_id"], {}).setdefault(cell_key, {})
        if model in by_model:
            continue  # an earlier attempt already answered this cell
        by_model[model] = grade

    # Keep cells graded for the full requested model set.
    blocks: dict[str, dict[tuple, dict[str, int]]] = {}
    n_wanted = len(wanted_set)
    for thm, cmap in raw.items():
        kept = {ck: mv for ck, mv in cmap.items() if len(mv) == n_wanted}
        if kept:
            blocks[thm] = kept

    prompt_rungs = sorted({ck[1] for cmap in blocks.values() for ck in cmap})
    return wanted, blocks, prompt_rungs


def marginal_rates(models: list[str], blocks: dict) -> dict[str, float]:
    """Return each model's paired-cell pass@1 pilot rate.

    Parameters
    ----------
    models : list[str]
        Models.
    blocks : dict
        Paired cells.

    Returns
    -------
    dict[str, float]
        Rates, or NaN for empty blocks.
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
    """Return the fraction of paired cells solved by either contrast model.

    Do not use all 21 models: their union trends to 1.0 regardless of the pair.

    Parameters
    ----------
    models : list[str]
        Contrast models.
    blocks : dict
        Paired cells.

    Returns
    -------
    float
        Fraction, or NaN for empty blocks.
    """
    solved = tot = 0
    for cmap in blocks.values():
        for mv in cmap.values():
            tot += 1
            solved += 1 if any(mv[m] for m in models) else 0
    return solved / tot if tot else float("nan")


def pooled_discordant_counts(blocks: dict, model_a: str, model_b: str) -> tuple:
    """Return pooled McNemar discordant counts for a model pair.

    Pool across theorems and prompt rungs as a conservative single-stratum CMH collapse.

    Parameters
    ----------
    blocks : dict
        Paired cells.
    model_a : str
        First model.
    model_b : str
        Second model.

    Returns
    -------
    tuple
        A-success/B-failure and the reverse.
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


def build_within_family_contrasts() -> list:
    """Build 21 PRIMARY within-family ladder contrasts (7 x C(3,2))."""
    contrasts: list[_Contrast] = []
    for family, ladder in FAMILIES.items():
        for pos_a, pos_b in combinations(range(3), 2):
            model_a, model_b = ladder[pos_a], ladder[pos_b]
            label = f"[{family} ladder] {model_a} vs {model_b}"
            contrasts.append((label, model_a, model_b))
    return contrasts


_LADDER_POS_NAMES = ("small", "mid", "large")


def build_cross_family_contrasts() -> list:
    """Build 63 SECONDARY size-matched contrasts (3 x C(7,2)).

    Labels say ``SECONDARY`` so exploratory results cannot be mistaken for PRIMARY.
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


_WITHIN_FAMILY_CONTRASTS = build_within_family_contrasts()
_CROSS_FAMILY_CONTRASTS = build_cross_family_contrasts()
if len(_WITHIN_FAMILY_CONTRASTS) != N_PRIMARY:
    raise ValueError(
        f"N_PRIMARY={N_PRIMARY} but the within-family builder returns "
        f"{len(_WITHIN_FAMILY_CONTRASTS)} contrasts; ALPHA_PRIMARY is frozen"
    )
if len(_CROSS_FAMILY_CONTRASTS) != N_SECONDARY:
    raise ValueError(
        f"N_SECONDARY={N_SECONDARY} but the cross-family builder returns "
        f"{len(_CROSS_FAMILY_CONTRASTS)} contrasts; ALPHA_SECONDARY is frozen"
    )


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
    """Bootstrap McNemar power and a paired rate-gap CI for one pair.

    Resample whole theorem blocks to preserve their within-theorem dependence.

    Parameters
    ----------
    blocks : dict
        Paired cells.
    model_a : str
        First model.
    model_b : str
        Second model.
    n_theorems : int
        Theorem blocks per simulation.
    alpha : float
        Significance threshold.
    sims : int
        Simulation count.
    rng : np.random.Generator
        Seeded generator for byte-identical runs.

    Returns
    -------
    tuple
        Rejection fraction and 5th/95th gap CI.
    """
    thm_ids = list(blocks.keys())
    # Flatten first so simulations accumulate integers rather than walk dictionaries.
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
    """Project pairwise McNemar power at `n_replicates` with a Beta mixture.

    Replicates resample the same theorem difficulty, so they saturate; theorems are the lever.
    Both models share theorem solvability; their solvable-cell means are rate / frac_solvable.

    Parameters
    ----------
    rate_a : float
        First pass@1 rate.
    rate_b : float
        Second pass@1 rate.
    frac_solvable : float
        Pairwise solvable fraction; must be ``> 0``.
    n_theorems : int
        Theorem blocks per simulation.
    n_replicates : int
        Replicates per cell.
    n_prompt_rungs : int
        Prompt rungs per theorem.
    alpha : float
        Significance threshold.
    sims : int
        Simulation count.
    beta_conc : float
        Mixture concentration.
    rng : np.random.Generator
        Random generator.

    Returns
    -------
    float
        Rejection fraction, or NaN for implied means outside ``(0, 1]``.
    """
    ma = rate_a / frac_solvable
    mb = rate_b / frac_solvable
    if not (0 < ma <= 1 and 0 < mb <= 1):
        return float("nan")  # The solvable fraction cannot host this rate.
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
    """Return the smallest `grid` value reaching `target`, else ``None``.

    NaN at every point is uncalibratable; no replicate count can fix it.

    Parameters
    ----------
    rate_a : float
        First pass@1 rate.
    rate_b : float
        Second pass@1 rate.
    frac_solvable : float
        Pairwise solvable fraction.
    n_theorems : int
        Theorem blocks per simulation.
    n_prompt_rungs : int
        Prompt rungs per theorem.
    alpha : float
        Significance threshold.
    sims : int
        Simulation count.
    beta_conc : float
        Mixture concentration.
    rng : np.random.Generator
        Random generator.
    grid : tuple, optional
        Replicate counts.
    target : float, optional
        Required rejection fraction.

    Returns
    -------
    int | None
        First sufficient value, or ``None``.
    """
    for n_rep in sorted(grid):
        power = passn_power(
            rate_a, rate_b, frac_solvable, n_theorems, n_rep, n_prompt_rungs,
            alpha=alpha, sims=sims, beta_conc=beta_conc, rng=rng,
        )
        if not np.isnan(power) and power >= target:
            return n_rep
    return None


@dataclass(frozen=True)
class ContrastSizing:
    """Observed pair statistics and sizing.

    ``near_tie`` requires the gap and its CI inside ``+/- EQUIV_BAND`` to certify
    equivalence; ``needed_replicates`` is the first projected ``POWER_TARGETS[0]`` point.
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
    """Compute observed and projected sizing for one contrast.

    Seed independent bootstrap and replicate generators from the model pair for
    byte-identical reruns.

    Parameters
    ----------
    blocks : dict
        Paired cells.
    label : str
        Contrast label.
    model_a : str
        First model.
    model_b : str
        Second model.
    rates : dict
        Observed pass@1 rates.
    prompt_rungs : list
        Rungs; only their count is used.
    alpha : float
        Significance threshold.
    sims : int
        Simulations per grid point.

    Returns
    -------
    ContrastSizing | None
        None when a pre-registered contrast lacks model data and must be skipped.
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
        ci_lo, ci_hi = lo, hi  # Keep the largest-grid CI.
    r_theorems = {
        target: next((n for n, pw in zip(N_THEOREMS_GRID, curve) if pw >= target), None)
        for target in POWER_TARGETS
    }
    near_tie = abs(gap) < EQUIV_BAND and ci_hi <= EQUIV_BAND and ci_lo >= -EQUIV_BAND

    # Calibrate frac_solvable to this pair only.
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
    """Format a DIFFERENCE, NEAR-TIE, or UNRESOLVED verdict."""
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
    """Compute and print one contrast tier's observed and sizing report.

    Announce skipped members of the full 21- or 63-contrast pre-registered list.

    Parameters
    ----------
    tier_label : str
        Display label.
    contrasts : list
        Pre-registered contrasts.
    blocks : dict
        Paired cells.
    rates : dict
        Observed pass@1 rates.
    prompt_rungs : list
        Paired prompt rungs.
    secondary : bool
        SECONDARY uses sizing alpha and BH q; PRIMARY uses Bonferroni alpha.
    sims : int
        Simulations per grid point.
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments; `argv` defaults to ``sys.argv[1:]``."""
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        help="local results root containing runs/scaling_*/verified_rows.jsonl "
             "(default: %(default)s)",
    )
    p.add_argument(
        "--s3",
        nargs="?",
        const="",
        default=None,
        metavar="PREFIX",
        help="download rows from S3; PREFIX defaults to the study spool prefix",
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
    """Load run files, pair cells, and print the report.

    Parameters
    ----------
    argv : list[str] | None, optional
        Command-line arguments.

    Returns
    -------
    int
        0 for a report; 1 when files or fully paired cells are absent.
    """
    args = parse_args(argv)
    models_filter = (
        tuple(m.strip() for m in args.models.split(",")) if args.models else None
    )

    local = args.s3 is None
    rows_dir = resolve_rows_dir(
        rows_dir=args.results_dir / "runs" if local else None,
        s3_prefix=None if args.s3 is None else (args.s3 or spool_prefix()),
        candidates=("verified_rows.jsonl", "all_rows.jsonl"),
    )
    prefix = "scaling_*" if local else "*"
    row_files = sorted(rows_dir.glob(f"{prefix}/verified_rows.jsonl"))
    verified_dirs = {path.parent for path in row_files}
    row_files.extend(sorted(
        path for path in rows_dir.glob(f"{prefix}/all_rows.jsonl")
        if path.parent not in verified_dirs
    ))

    if not row_files:
        print(
            "No deduction row files found. Use --s3 [PREFIX] or point "
            "--results-dir at a local tree containing "
            "runs/scaling_*/verified_rows.jsonl.",
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
