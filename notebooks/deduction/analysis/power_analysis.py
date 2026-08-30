"""Power analysis for the Lean-4 deduction FAMILY-LADDER SCALING study: 21
checkpoints, 7 vendor families x 3 parameter rungs; sibling of
``notebooks/induction/analysis/power_analysis.py``.

TERMINOLOGY -- this study overloads "rung", this file never does:
``ladder_pos`` is a model's position in its family 3-tuple (0..2),
``prompt_rung`` is a PROMPT's context rung (the ``"rung"`` field on every JSONL
row, ``stepk:1`` .. ``hint:3``). The Beta-mixture replicate projection needs
each theorem's cell count to equal the number of distinct prompt rungs.

Unit of observation = one ``(theorem_id, k, prompt_rung)`` cell, scored 1 only
for ``verdict == "success"``; all models run the SAME cells, so pairs go
through McNemar's exact test pooled over prompt rungs (the conservative
single-stratum collapse of the CMH test). PRIMARY = 21 within-family ladder
contrasts, Bonferroni ``ALPHA / 21``; SECONDARY = 63 cross-family size-matched
contrasts, exploratory, Benjamini-Hochberg at q=0.05. Sizing = block-bootstrap
n_theorems power curve plus a Beta-mixture pass@N advisory, printed with the
caveat that theorems, not replicates, are this benchmark's power lever.

DATA SOURCE -- LOUD WARNING: read ``verified_rows.jsonl`` (written by
``scripts/deduction/lean_verify_rows.py``), NEVER the generation-time
``all_rows.jsonl``, whose verdicts are all the ``"unverified"`` placeholder:
every success rate then reads at or near 0.000, indistinguishable from a
genuine "every model failed everything" result, so `load_joint_cells` prints a
loud stderr banner instead of falling back silently. Sources are ``--s3``
(``s3://smolbench-results-414266451290/deduction/runs/scaling_*/``) or
``--results-dir`` (default: sibling ``results/``, glob
``runs/scaling_*/verified_rows.jsonl``). Plain ``uv run`` resyncs the extras
away:

    uv run --no-project --with numpy --with scipy \
        python notebooks/deduction/analysis/power_analysis.py --s3
"""

from __future__ import annotations

# Cap the BLAS/OpenMP thread pools BEFORE numpy is imported. This script
# often runs on the shared eval container while a lean sweep's Dojo
# verifiers are resident, and numpy's default 16-thread OpenBLAS pool trips
# RLIMIT_NPROC there ("pthread_create failed: Resource temporarily
# unavailable"). One thread is enough for a few-thousand-sim Monte Carlo.
import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import json
import math
import sys
import tempfile
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import numpy as np

# notebooks/ (where _power_common.py lives) is this file's parent directory.
# This anchors the import to __file__, so it works regardless of the
# caller's cwd (repo convention -- see _power_common.py itself).
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _power_common import (
    ALPHA,
    POWER_TARGETS,
    SEED,
    fmt_r,
    results_dir,
)

# --------------------------------------------------------------------------- #
# Roster: 7 vendor families x 3 parameter-count rungs (ladder positions) =
# 21 models. The study spec gives this roster verbatim.
# Keys are the EC2 spec keys this study's runs use as ``model`` (==
# ``display_name``) on every JSONL row -- see the module docstring's "Data
# source" section -- NOT the short analysis tags the induction sibling
# study uses.
#
# Each family's 3-tuple is ordered SMALL -> MID -> LARGE. That order is
# load-bearing for build_cross_family_contrasts's size-matched pairing
# below. Never reorder it silently.
# --------------------------------------------------------------------------- #
FAMILIES: dict[str, tuple[str, str, str]] = {
    "qwen35": ("qwen3.5-27b", "qwen3.5-122b-a10b", "qwen3.5-397b-a17b"),
    "nemotron3": ("nemotron-3-nano-4b", "nemotron-3-nano-30b-a3b", "nemotron-3-super-120b-a12b"),
    "gemma4": ("gemma-4-e2b", "gemma-4-12b", "gemma-4-31b"),
    "glm": ("glm-4.7-flash", "glm-4.5-air", "glm-4.7"),
    "ministral3": ("ministral-3-3b", "ministral-3-8b", "ministral-3-14b"),
    "exaone": ("exaone-4.0-32b", "exaone-4.5-33b", "k-exaone-236b-a23b"),
    "deepseek": ("deepseek-v4-flash", "deepseek-v3.1", "deepseek-v4-pro"),
}
MODELS = tuple(m for rungs in FAMILIES.values() for m in rungs)  # 21

# This drift guard runs at MODULE scope, not just inside main(), so
# importing this module for its constants elsewhere also gets it for free.
# This mirrors notebooks/induction/analysis/power_analysis.py's analogous
# module-scope assert. MODELS is DEFINED as a comprehension over FAMILIES
# (never hand-duplicated), so a length/uniqueness check is the only drift
# this design can suffer. Unlike the induction sibling, there is no
# separate hand-maintained flat tuple that could disagree with FAMILIES
# about membership or order.
assert len(MODELS) == 21, f"expected 21 models (7 families x 3 rungs), got {len(MODELS)}"
assert len(set(MODELS)) == 21, "MODELS contains a duplicate model spec-key"

# --------------------------------------------------------------------------- #
# Design constants.
# --------------------------------------------------------------------------- #
SIMS = 4000  # Monte-Carlo sims per grid point (matches the archived script's default)
#: Equivalence half-width for near-ties (pass@1 rate points). A pair whose
#: bootstrap 90% CI (5th/95th percentile) for the paired rate gap falls
#: inside +/- this is certified "indistinguishable at this resolution"
#: rather than left as an unresolved difference test.
EQUIV_BAND = 0.10
#: Beta concentration (a + b) for the pass@N solvable-cell probability
#: mixture.
BETA_CONC = 5.0

N_THEOREMS_GRID = (30, 60, 100, 150, 200, 300)
N_REPLICATES_GRID = (1, 2, 3, 4, 8)

# PRIMARY tier: 21 within-family ladder contrasts (7 families x C(3,2)=3
# size-pairs). Bonferroni over the full family.
N_PRIMARY = 21
ALPHA_PRIMARY = ALPHA / N_PRIMARY

# SECONDARY tier: 63 cross-family, size-matched contrasts (3 ladder
# positions x C(7,2)=21 family-pairs). Benjamini-Hochberg FDR at q=0.05.
# Sizing simulations use the conservative rank-1 BH threshold
# ALPHA_SECONDARY = Q_SECONDARY / N_SECONDARY as an UPPER BOUND on the
# per-test alpha BH will actually apply at analysis time. This mirrors
# notebooks/induction/analysis/power_analysis.py's ALPHA_SECONDARY exactly (see that
# file's module docstring for the full "why an upper bound" argument). The
# OBSERVED-data significance decision reported per contrast uses the real
# `benjamini_hochberg` procedure below, not this constant -- see
# `_print_tier_report`.
N_SECONDARY = 63
Q_SECONDARY = 0.05
ALPHA_SECONDARY = Q_SECONDARY / N_SECONDARY

# S3 layout (see module docstring's "Data source" section).
S3_BUCKET = "smolbench-results-414266451290"
S3_REGION = "us-west-2"
S3_PREFIX = "deduction/runs/"

RESULTS_DIR = results_dir(__file__, up=1)

_Contrast = tuple[str, str, str]  # (label, model_a, model_b)


def _seed_of(name: str) -> int:
    """Derive a deterministic 32-bit seed from a model name.

    Uses a stable SHA-256 digest, never builtin ``hash``: the latter is salted per
    process (``PYTHONHASHSEED``), which would make every per-pair RNG stream -- and
    so every reported power value and CI -- irreproducible across runs, and this repo
    requires seeded, reproducible evals.
    """
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "little")


# --------------------------------------------------------------------------- #
# Core statistics. Inlined rather than imported: this file must stay
# self-contained under ``uv run --no-project``.
# --------------------------------------------------------------------------- #
def pass_at_n(p: np.ndarray | float, n: int) -> np.ndarray | float:
    """Probability that at least one of `n` conditionally-independent replicates
    succeeds: ``1 - (1 - p)**n``. `p` in ``[0, 1]``, `n >= 1`; at ``n == 1`` this is
    `p`, the per-replicate regime this study's R=1 pilot measures directly.
    """
    return 1.0 - (1.0 - np.asarray(p, dtype=float)) ** n


def _log_binom_cdf_half(n: int, k: int) -> float:
    """Log of the Binomial(`n`, 0.5) CDF at `k` (``0 <= k <= n``), via ``lgamma``
    plus log-sum-exp: stays finite for the discordant totals of several thousand that
    would underflow a naive ``0.5**n``.
    """
    ln_half = math.log(0.5)
    ln_nfac = math.lgamma(n + 1)
    log_terms = [
        ln_nfac - math.lgamma(i + 1) - math.lgamma(n - i + 1) + n * ln_half
        for i in range(k + 1)
    ]
    max_lt = max(log_terms)
    return max_lt + math.log(sum(math.exp(lt - max_lt) for lt in log_terms))


def mcnemar_exact_p(b: int, c: int) -> float:
    """McNemar's exact two-sided binomial p-value for discordant counts.

    `b` (A succeeds, B fails) and `c` (the reverse) are both ``>= 0``. Under H0 the
    ``b`` cells are ``Binomial(b + c, 0.5)``, so ``p = min(1, 2 * P(X <= min(b, c)))``;
    with no discordant pairs there is no evidence either way and this returns 1.0.
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2.0 * math.exp(_log_binom_cdf_half(n, k)))


def benjamini_hochberg(pvalues: np.ndarray, q: float) -> np.ndarray:
    """Benjamini-Hochberg (1995) step-up procedure for FDR control at level `q`.

    Rejects ranks ``1..i`` for the LARGEST rank ``i`` whose sorted p-value satisfies
    ``p_(i) <= i * q / m`` (nothing if no rank qualifies). Deliberately NOT a flat
    ``q / m`` threshold: the per-rank bar grows with rank, so only the smallest
    p-value ever faces ``q / m``, and that is the mechanism by which BH beats
    Bonferroni at the same nominal level. Used for the exploratory SECONDARY
    cross-family tier, where Bonferroni FWER control over 63 tests that gate no
    decision would be needlessly conservative.

    `pvalues` must be 1-D and need not be sorted -- the returned boolean mask is
    aligned to its input order; `q` must lie in ``(0, 1]``. Either violation raises
    ``ValueError``.
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

    `load_joint_cells` calls this for an ``all_rows.jsonl`` input file or a cell row
    still carrying the ``"unverified"`` placeholder; each `reasons` entry is appended
    verbatim as one banner line. A silent fallback would yield a whole report of
    near-zero success rates that reads exactly like a genuine "every model failed
    everything" finding.
    """
    bar = "!" * 78
    lines = [bar, "!!  WARNING: UNVERIFIED LEAN VERDICTS IN LOADED ROWS", bar]
    for reason in reasons:
        lines.append(f"!!  {reason}")
    lines += [
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
        bar,
    ]
    print("\n".join(lines), file=sys.stderr)


#: Verdicts that mean "this cell was never measured for ANY model" -- see
#: the reasoning in load_joint_cells. This file excludes cells carrying
#: only these verdicts from the paired blocks, rather than scoring them 0.
UNMEASURABLE_VERDICTS: frozenset = frozenset({"exception", "replay_failed"})


#: Filename marker for a RETIRED row artifact. ``run_study.py`` renames a
#: superseded ``all_rows.jsonl`` to ``all_rows_SUPERSEDED-<stamp>.jsonl``
#: rather than deleting it (this preserves the audit trail on purpose), and
#: the S3 analysis snapshot copies those files along with everything else.
#: So a byte-identical copy of the retired MIXED-HARDWARE all_rows artifact
#: sits one directory away from live data. Any glob wide enough to pick it
#: up would pool two hardware regimes into one lane, with nothing but line
#: order to tell them apart -- exactly the confound the archiving exists to
#: remove.
SUPERSEDED_MARKER = "SUPERSEDED"
#: The snapshot writes three retirement markers for the same audit-trail
#: class (scripts/results/snapshot_analysis_data.py: ``*_SUPERSEDED-*``,
#: ``*_STALE-*``, ``*_BROKEN-*``). STALE/BROKEN are anchored ``_MARKER-`` to
#: avoid matching ordinary words in basenames; SUPERSEDED stays bare (the
#: historical form).
RETIRED_MARKERS = (SUPERSEDED_MARKER, "_STALE-", "_BROKEN-")


def reject_superseded(paths) -> None:
    """Refuse retired row artifacts, loudly and by name.

    Raises ``SystemExit`` naming every path whose BASENAME contains any
    `RETIRED_MARKERS` entry (a directory legitimately named after an audit is not a
    target). A warning would not do: these files parse perfectly and their rows are
    well-formed, so ingesting one yields a complete, plausible, WRONG report rather
    than a crash.
    """
    bad = [str(p) for p in paths
           if any(m in Path(p).name for m in RETIRED_MARKERS)]
    if not bad:
        return
    bar = "!" * 78
    raise SystemExit(
        "\n".join(
            [bar, "!!  REFUSING SUPERSEDED ROW FILE(S)", bar]
            + [f"!!  {b}" for b in bad]
            + [
                "!!",
                "!!  A *_SUPERSEDED-* file is a RETIRED artifact kept as an audit",
                "!!  trail (see run_study.py --force-rerun). Its rows were collected",
                "!!  on hardware that has since been superseded; pooling them with",
                "!!  current rows re-creates the mixed-hardware confound the archive",
                "!!  was made to remove. Point the loader at verified_rows.jsonl.",
                bar,
            ]
        )
    )


def reject_unverified_verdicts(rows, field, source) -> None:
    """Refuse rows that still carry the ungraded ``"unverified"`` sentinel.

    Raises ``SystemExit``, naming the count and `source`, if any row has
    ``kind == "cell"`` and ``row[field] == "unverified"``. A warning would not do:
    such a cell grades exactly like a real measurement (`grade_verdicts` has no
    special case, and the sentinel is deliberately NOT in `UNMEASURABLE_VERDICTS`,
    which would turn this loud condition into a silent drop), so it scores as a
    failure and the report comes out complete, plausible, and wrong.

    `rows` are already-parsed rows from ONE source file -- this does no I/O -- and
    must be checked BEFORE they reach `grade_verdicts`. `field` is explicit rather
    than hardcoded because callers differ: `error_bars.lane_outcomes` checks
    ``"verdict"`` on primary rows and ``"recovered_verdict"`` on its recovery sibling,
    whose rows have no ``"verdict"`` key at all.
    """
    count = sum(
        1 for row in rows
        if row.get("kind") == "cell" and row.get(field) == "unverified"
    )
    if count == 0:
        return
    bar = "!" * 78
    raise SystemExit(
        "\n".join(
            [bar, "!!  REFUSING UNVERIFIED ROW(S)", bar,
             f"!!  {count} cell row(s) in {source} still carry the",
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
             "!!  before loading it for analysis.",
             bar]
        )
    )


def grade_verdicts(verdicts) -> int | None:
    """Grade ONE cell from its rows' verdicts in file order (== chronological).

    Two rules, both of which earlier code got wrong (the measurements that settled
    them are recorded in `load_joint_cells`):

      * EARLIEST SURVIVING ATTEMPT WINS -- a later retry is an independent draw, and
        taking it would report pass@N as pass@1.
      * An `UNMEASURABLE_VERDICTS` verdict is not a measurement: it neither scores 0
        nor claims the cell, so the next row still gets its chance.

    Returns 1 (success), 0 (a real failure), or ``None`` for "no surviving attempt".
    Callers resolve ``None`` differently on purpose -- this function and
    ``hint_vs_noise.load_rungs`` leave the cell ABSENT, while
    ``error_bars.build_pool`` may score it 0 when another lane graded the same cell.
    `load_joint_cells` passes a single row's verdict in a one-element list while
    streaming, where ``None`` means "not a measurement, keep looking".
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

    Unions `row_files` (e.g. the 21 checkpoints' individual ``verified_rows.jsonl``),
    reading only ``kind == "cell"``, ``replicate_idx == 0`` rows -- a filter, not an
    assumption: this study collects R=1, but the code stays correct if a later run
    adds replicates. Each cell is graded through `grade_verdicts`. `models`, if given,
    restricts pairing to exactly that set (a cell is kept only if graded for EVERY
    member), which lets a partial or single-family run be analyzed without every
    contrast reporting "no data".

    Returns ``(models, blocks, prompt_rungs)``: the sorted spec-keys actually paired;
    ``{theorem_id: {(k, prompt_rung): {model: 1 or 0}}}`` restricted to cells graded
    for every paired model and theorems with at least one such cell, where one whole
    theorem block is `bootstrap_power`'s resample unit; and the sorted distinct
    ``rung`` values present (prompt rungs, NOT ladder positions).

    Raises ``SystemExit`` via `reject_superseded` before any row is read, and prints
    the `_warn_unverified` stderr banner if any input basename is ``all_rows.jsonl``
    or any loaded cell row's verdict is still ``"unverified"`` -- regardless of
    whether those rows survive into `blocks`, since a row dropped for another reason
    is still evidence the input is unverified.
    """
    reject_superseded(row_files)
    cell_rows: list[dict] = []
    warn_reasons: list[str] = []
    unverified_count = 0
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
                continue
            if row.get("verdict") == "unverified":
                unverified_count += 1
            cell_rows.append(row)
    if unverified_count:
        warn_reasons.append(
            f'{unverified_count} loaded cell row(s) carry verdict == "unverified".'
        )
    if warn_reasons:
        _warn_unverified(warn_reasons)

    present_models = sorted({row["model"] for row in cell_rows})
    wanted = sorted(models) if models is not None else present_models
    wanted_set = set(wanted)

    # theorem_id -> (k, prompt_rung) -> model -> outcome (1 success / 0 fail)
    #
    # EARLIEST SURVIVING ATTEMPT WINS. A cell can own several rows. Rows are
    # appended, so file order is chronological. The first row whose verdict
    # is not "exception" is the first time this cell was actually measured.
    #
    # This file applies two rules. Both directions were wrong before:
    #
    #  * Plain assignment per row is LAST-wins. Some cells hold more than
    #    one surviving attempt, and generation is not deterministic across
    #    server processes, so each retry is a fresh draw. Last-wins takes
    #    the RESAMPLED attempt, which reports pass@N as pass@1.
    #
    #  This file implements both rules ONCE, in `grade_verdicts`. Every
    #  loader in this study reads rows through it (error_bars.lane_outcomes,
    #  hint_vs_noise.load_rungs). The reasoning and its measurements stay
    #  here.
    #
    #  * UNMEASURABLE verdicts must not score 0. Two kinds exist, and both
    #    mean the model was never actually tested:
    #
    #      "exception" -- the generation attempt never produced an answer
    #          (spot interruption, idle watchdog, unreachable endpoint).
    #          This is an infrastructure fault, not a model failure.
    #          deepseek-v3.1 carries 415 such cells, 44% of its lane.
    #          Scoring them would read as 415 failures it never had.
    #
    #      "replay_failed" -- VERIFICATION could not be set up. LeanDojo
    #          could not open a session for the theorem (missing
    #          *.ast.json in the traced cache), or the GROUND-TRUTH prefix
    #          of k tactics would not replay. Both happen before the
    #          candidate is considered. Proof this is not model behaviour:
    #          the replay_failed cell set is BYTE-IDENTICAL across lanes --
    #          exactly 232 cells, 100% overlap, in every one of 21 models
    #          (151 DojoInit + 81 prefix). A model-dependent failure cannot
    #          do that.
    #
    #    Scoring replay_failed as 0 would deflate EVERY model's marginal
    #    rate, by up to 232/944 = 24.6% (measured: gemma-4-e2b 0.110 ->
    #    0.083, glm-4.7-flash 0.146 -> 0.110). Paired McNemar survives it,
    #    because concordant zeros cancel. But every reported rate would be
    #    wrong.
    #
    #    The measurable denominator is therefore 944 - 232 = 712 per lane --
    #    exactly the row count on which Lean actually ran.
    #
    #    "incomplete" is NOT in this set. Its cell sets differ per model
    #    (68 / 30 / 50 across three lanes, 8 shared), so it is real
    #    behaviour.
    #
    #    This file leaves unmeasurable cells ABSENT, so the paired filter
    #    below drops them from every model's block. That is what "not
    #    measured" means in a paired design.
    raw: dict[str, dict[tuple, dict[str, int]]] = {}
    for row in cell_rows:
        model = row["model"]
        if model not in wanted_set:
            continue
        # `grade_verdicts` is the ONE implementation of the two rules above;
        # applied to the row in hand it returns None for a verdict that is not
        # a measurement, so that row neither scores nor claims the cell and the
        # next one still gets its chance -- earliest-surviving-wins, unrolled.
        grade = grade_verdicts([row.get("verdict")])
        if grade is None:
            continue  # never measured -- see above
        cell_key = (row["k"], row["rung"])  # row["rung"] is this file's prompt_rung
        by_model = raw.setdefault(row["theorem_id"], {}).setdefault(cell_key, {})
        if model in by_model:
            continue  # an earlier attempt already answered this cell
        by_model[model] = grade

    # Keep only cells graded for the FULL requested model set (paired), and
    # only theorems with at least one such cell.
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
    estimate): ``{model: successes / total_paired_cells}``, or ``float("nan")`` for
    every model if `blocks` is empty.
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
    """Fraction of paired cells solved by AT LEAST ONE of `models`; NaN if `blocks`
    is empty.

    This is the Beta-mixture advisory's (`passn_power`) "solvable at all" anchor.
    `compute_contrast_sizing` calls it with exactly the contrast's two models, never
    the whole roster: across 21 models "did ANY solve it" trends to 1.0 regardless of
    how the compared pair performs.
    """
    solved = tot = 0
    for cmap in blocks.values():
        for mv in cmap.values():
            tot += 1
            solved += 1 if any(mv[m] for m in models) else 0
    return solved / tot if tot else float("nan")


def pooled_discordant_counts(blocks: dict, model_a: str, model_b: str) -> tuple:
    """Pooled McNemar discordant counts ``(b, c)`` for one model pair.

    `b` = `model_a` succeeds and `model_b` fails, `c` = the reverse, pooled over every
    paired theorem and prompt rung in `blocks` with no stratification -- the
    conservative single-stratum collapse of the rung-stratified CMH test. Both models
    are assumed present in every cell's model-map, true by construction for a pair in
    `load_joint_cells`'s returned `models`.
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

    Returns ``(label, model_a, model_b)`` triples grouped by family in `FAMILIES`
    order; within a family, ladder-position pairs follow ``combinations(range(3), 2)``
    -- (0,1), (0,2), (1,2). Labels: ``f"[{family} ladder] {model_a} vs {model_b}"``.
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
    """Build the 63 SECONDARY cross-family, size-matched contrasts
    (3 ladder positions x C(7,2) = 21 family pairs).

    Returns ``(label, model_a, model_b)`` triples grouped by ladder position 0, 1, 2;
    within a position, family pairs follow `FAMILIES` definition order. Every label
    carries the literal "SECONDARY" tag (``f"[SECONDARY | {small/mid/large}] ..."``)
    so this tier's output can never be mistaken for a primary result.
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
    their cells, and computes McNemar's exact p over `sims` simulations at `alpha`
    (this tier's `ALPHA_PRIMARY` or `ALPHA_SECONDARY`). `rng` must be a freshly-seeded
    generator (see `_seed_of`) so repeated runs are byte-identical.

    Returns ``(power, gap_lo, gap_hi)``: the rejection fraction at `alpha`, then the
    5th/95th-percentile bootstrap CI of ``rate_a - rate_b``, used for the near-tie /
    equivalence verdict. `mcnemar_exact_p` is cached on ``(b + c, min(b, c))``, which
    takes few distinct values across `sims`; a pure speedup, results are unchanged.
    """
    thm_ids = list(blocks.keys())
    # Pre-flatten each theorem's per-cell (a, b) outcomes to plain arrays so
    # the inner sim loop is pure integer accumulation, not dict walking.
    per_thm = {
        t: np.array([(cmap[ck][model_a], cmap[ck][model_b]) for ck in cmap], dtype=np.int8)
        for t, cmap in blocks.items()
    }
    idx = np.arange(len(thm_ids))
    rejects = 0
    gaps = np.empty(sims)
    cache: dict[tuple, float] = {}
    for s in range(sims):
        pick = rng.choice(idx, size=n_theorems, replace=True)
        stacked = np.concatenate([per_thm[thm_ids[i]] for i in pick])
        oa, ob = stacked[:, 0], stacked[:, 1]
        disc_b = int(np.sum((oa == 1) & (ob == 0)))
        disc_c = int(np.sum((oa == 0) & (ob == 1)))
        key = (disc_b + disc_c, min(disc_b, disc_c))
        p = cache.get(key)
        if p is None:
            p = mcnemar_exact_p(disc_b, disc_c)
            cache[key] = p
        if p < alpha:
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

    Each theorem is solvable with probability `frac_solvable` (shared -- the SAME
    theorems); each solvable cell draws a per-replicate success probability from
    ``Beta(m * beta_conc, (1 - m) * beta_conc)`` with the model's calibrated
    solvable-cell mean ``m = rate / frac_solvable``, i.e. shared coarse difficulty
    plus idiosyncratic per-model skill. `pass_at_n` converts cells to pass@N and
    McNemar's p is computed per simulation, at `alpha`, over `sims` simulations on an
    `n_theorems` x `n_prompt_rungs` grid (prompt rungs, NOT ladder positions).

    `rate_a` / `rate_b` are observed marginal pass@1 rates from `marginal_rates`;
    `frac_solvable` comes from `union_solvable_fraction` called with just this pair
    and must be ``> 0``; `beta_conc` is the mixture concentration ``a + b``; `rng` is
    freshly seeded by the caller. Returns the rejection fraction in ``[0, 1]``, or
    ``float("nan")`` if either model's implied solvable-cell mean falls outside
    ``(0, 1]`` -- the observed rate cannot be calibrated against this `frac_solvable`.

    Adding replicates re-samples the SAME theorem's difficulty, so this projection
    saturates: theorems, not replicates, are the power lever.
    """
    ma = rate_a / frac_solvable
    mb = rate_b / frac_solvable
    if not (0 < ma <= 1 and 0 < mb <= 1):
        return float("nan")  # solvable fraction too small/large to host this rate
    rejects = 0
    shape = (n_theorems, n_prompt_rungs)
    cache: dict[tuple, float] = {}
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
        key = (disc_b + disc_c, min(disc_b, disc_c))
        p = cache.get(key)
        if p is None:
            p = mcnemar_exact_p(disc_b, disc_c)
            cache[key] = p
        if p < alpha:
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

    Scans `grid` ascending and stops at the first sufficient point (the same
    early-stop discipline as the induction sibling's ``replicates_needed``). ``None``
    also covers the uncalibratable case where `passn_power` is NaN at every grid
    point, which no number of replicates can fix.
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

    `compute_contrast_sizing` produces one per contrast whose two models are both
    present in the loaded/paired data; contrasts naming an absent model never get one.

    Attributes
    ----------
    n_paired_theorems : int
        ``len(blocks)``; identical across every contrast from the same `blocks`.
    observed_gap : float
        ``rates[model_a] - rates[model_b]`` on the current R=1 pilot.
    observed_p : float
        McNemar exact two-sided p, POOLED over all paired cells and prompt rungs --
        an observed statistic, not a projection.
    theorem_curve, r_theorems
        Block-bootstrap power at each `N_THEOREMS_GRID` point (same order), and the
        smallest grid point reaching each `POWER_TARGETS` level (``None`` if none
        does).
    ci_lo, ci_hi : float
        Bootstrap 5th/95th-percentile CI of the paired rate gap at the LARGEST
        `N_THEOREMS_GRID` point.
    near_tie : bool
        True only if `observed_gap` AND ``[ci_lo, ci_hi]`` both fall inside
        ``+/- EQUIV_BAND`` -- a certified equivalence, not merely an unresolved
        difference test.
    needed_replicates : int or None
        Smallest `N_REPLICATES_GRID` point the Beta-mixture projects to reach
        ``POWER_TARGETS[0]`` at the CURRENT `n_paired_theorems`.
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

    `prompt_rungs` is used only for its length (the Beta-mixture's per-theorem cell
    count); `alpha` is the per-test threshold for every McNemar test inside
    `bootstrap_power` / `passn_power` (this tier's `ALPHA_PRIMARY` or
    `ALPHA_SECONDARY`); `sims` is simulations per grid point.

    Returns ``None`` if either model is absent from `rates`, so callers can print a
    clean "skipped, no data" line for a pre-registered contrast the current data does
    not cover instead of raising. Reseeds two independent generators per contrast
    (bootstrap curve, replicate projection), both derived from ``(model_a, model_b)``
    via `_seed_of`, so re-running produces byte-identical output.
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

    # frac_solvable is calibrated to THIS PAIR ONLY (see
    # union_solvable_fraction's docstring) -- not the whole loaded roster.
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

    `contrasts` is the tier's full pre-registered list (21 or 63 entries); contrasts
    whose models are absent from the loaded data are skipped with a summary line
    rather than silently. The n_theorems-vs-replicates caveat is printed once per
    tier, into the report itself and not only as a code comment.

    With ``secondary=True`` this is the SECONDARY cross-family tier: every header and
    summary line is labelled SECONDARY, sizing uses `ALPHA_SECONDARY`, and observed
    significance is decided by `benjamini_hochberg` at `Q_SECONDARY`. Otherwise it is
    the PRIMARY tier, sized and decided at the fixed `ALPHA_PRIMARY` Bonferroni
    threshold.
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
# S3 loading.
# --------------------------------------------------------------------------- #
def _download_s3_rows(tmp_dir: Path) -> list:
    """Download this study's ``scaling_*`` run row files from S3 into `tmp_dir`.

    Lists ``s3://S3_BUCKET/S3_PREFIX`` with ``Delimiter="/"``, keeps run prefixes
    named ``scaling_*``, and per run downloads ``verified_rows.jsonl`` or, failing
    that, ``all_rows.jsonl`` (which makes `load_joint_cells` fire `_warn_unverified`),
    into one subdirectory per run under the caller-supplied `tmp_dir`. Returns one
    path per downloaded run, silently omitting runs with neither object present; any
    ``ClientError`` other than a 404/NoSuchKey propagates. ``boto3``/``botocore`` are
    imported LAZILY so the local ``--results-dir`` path and every pure function stay
    usable without boto3 installed.
    """
    import boto3  # lazy: keep the local-analysis path boto3-free
    from botocore.exceptions import ClientError

    client = boto3.client("s3", region_name=S3_REGION)
    resp = client.list_objects_v2(Bucket=S3_BUCKET, Prefix=S3_PREFIX, Delimiter="/")
    run_prefixes = sorted(
        cp["Prefix"]
        for cp in resp.get("CommonPrefixes", [])
        if Path(cp["Prefix"].rstrip("/")).name.startswith("scaling_")
    )

    row_files: list[Path] = []
    for prefix in run_prefixes:
        run_name = Path(prefix.rstrip("/")).name
        local_dir = tmp_dir / run_name
        local_dir.mkdir(parents=True, exist_ok=True)
        for candidate in ("verified_rows.jsonl", "all_rows.jsonl"):
            key = f"{prefix}{candidate}"
            local_path = local_dir / candidate
            try:
                client.download_file(S3_BUCKET, key, str(local_path))
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code", "")
                if code not in ("404", "NoSuchKey"):
                    raise
                continue
            row_files.append(local_path)
            break  # prefer verified_rows.jsonl; only try all_rows.jsonl if it 404s
    return row_files


# --------------------------------------------------------------------------- #
# CLI + report.
# --------------------------------------------------------------------------- #
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse this script's command-line arguments.

    `argv` defaults to ``sys.argv[1:]``; tests pass an explicit list.
    """
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--s3",
        action="store_true",
        help=(
            f"Download this study's run files from s3://{S3_BUCKET}/{S3_PREFIX} "
            "into a temp dir and analyze those (preferring verified_rows.jsonl, "
            "falling back to all_rows.jsonl per run -- see the module docstring's "
            "LOUD WARNING). Overrides --results-dir."
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

    Prints a data summary, then the PRIMARY (21 within-family) and SECONDARY (63
    cross-family) tiers, each contrast carrying observed significance, a
    block-bootstrap n_theorems power curve, and a Beta-mixture replicate projection.
    Returns 0 on a normal report, 1 if no row files or no fully-paired cells were
    found for the requested model set.
    """
    # Drift guards. These re-assert here as a second line of defense
    # (module scope already checks MODELS itself -- see the top of this
    # file). A future edit that changes the contrast-family sizes, without
    # updating N_PRIMARY/N_SECONDARY (and so ALPHA_PRIMARY/ALPHA_SECONDARY),
    # would silently invalidate every correction in this script's report.
    assert len(MODELS) == 21 and len(set(MODELS)) == 21
    assert len(build_within_family_contrasts()) == N_PRIMARY == 21
    assert len(build_cross_family_contrasts()) == N_SECONDARY == 63

    args = parse_args(argv)
    models_filter = (
        tuple(m.strip() for m in args.models.split(",")) if args.models else None
    )

    if args.s3:
        tmp_dir = Path(tempfile.mkdtemp(prefix="smolbench_deduction_power_"))
        print(
            f"Downloading run files from s3://{S3_BUCKET}/{S3_PREFIX} into "
            f"{tmp_dir} ...",
            file=sys.stderr,
        )
        row_files = _download_s3_rows(tmp_dir)
        if not row_files:
            print(
                f"No run files found under s3://{S3_BUCKET}/{S3_PREFIX} -- "
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
