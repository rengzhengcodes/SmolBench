"""Run the power analysis for the Lean-4 deduction FAMILY-LADDER SCALING study.

This sizes the 21-checkpoint scaling design: 7 vendor families x 3
parameter-count rungs each (see ``FAMILIES`` / ``MODELS`` below). It is the
deduction-side sibling of
``notebooks/induction/analysis/power_analysis.py``.

Two meanings of "rung" -- READ THIS FIRST
-------------------------------------------------------------------------
This study overloads the word "rung". This file does not. There are two
entirely different ladders in play:

  1. A model's LADDER POSITION within its vendor family -- small, mid, or
     large parameter count (index 0, 1, 2 into a ``FAMILIES[family]``
     3-tuple). This file always spells this ``ladder_pos`` (an int 0..2), or
     refers to a family's ``ladder`` (the 3-tuple itself). It is NEVER
     called "rung" anywhere in this file.
  2. A PROMPT's context rung -- how much of the ground-truth proof the
     model gets before it must complete the tail (``stepk:1`` gives the
     least context, ``hint:3`` the most; the data defines the exact label
     set, not this file). This is the ``"rung"`` field on every JSONL row
     the runner writes. This file always spells this ``prompt_rung`` (a
     str), or ``prompt_rungs`` (the sorted list of distinct values present
     in a loaded dataset).

Keeping these apart matters because both dimensions appear in the SAME
report: within-family contrasts vary ladder position while pooling over
prompt rungs. The Beta-mixture replicate projection needs a per-theorem
CELL COUNT that is exactly the number of distinct prompt rungs. Conflating
the two would silently swap one for the other in that projection.

Statistical design (unchanged from the archived script's shape)
-------------------------------------------------------------------------
- **Unit of observation = one ``(theorem_id, k, prompt_rung)`` cell.**
  Every model in the loaded/paired set is evaluated on the SAME cells
  (identical theorem sample, identical prompt-rung ladder). So every model
  pair is a PAIRED comparison, and the natural test is McNemar's exact test
  on the discordant cells (cells where exactly one model of the pair
  succeeds). This mirrors the induction study's "replicate, don't change
  the task" principle in the deduction setting: sizing adds cells (more
  theorems, more replicates), and never makes a theorem easier.
- **McNemar pooled over prompt rungs (used here for sizing) is the
  single-stratum collapse** of the rung-stratified Cochran-Mantel-Haenszel
  test that would run at analysis time. Pooling can only dilute a
  consistent per-rung effect, so it is the conservative choice for a power
  analysis (see ``pooled_discordant_counts``).
- **Cell outcome = pass@N.** A model "passes" a cell if ANY of its ``N``
  REPLICATES verifies: ``P(pass@N) = 1 - (1 - p)**N`` for per-replicate
  success probability ``p`` (``pass_at_n`` below). ``N == 1`` is the
  per-replicate regime this study's R=1 pilot measures directly.

Where the numbers come from
-------------------------------------------------------------------------
This script reads a REAL run's per-cell joint outcomes (JSONL rows written
by ``smolbench.deduction.lean.runner``; see ``load_joint_cells``). Two
estimators use that data. Both are reported side by side for EVERY
contrast (see "Headline deliverable" below):

1. **n_theorems sizing = block bootstrap of the observed joint cells**
   (``bootstrap_power``). This resamples whole THEOREM blocks with
   replacement (a theorem block carries every prompt rung's cell for it,
   so it preserves within-theorem cross-rung correlation) up to a
   candidate ``n_theorems``. It recomputes the pair's pooled McNemar p each
   simulation and reports the rejection rate. It uses the effect sizes
   actually observed in the pilot, with no parametric effect assumption,
   and is the PRIMARY sizing estimator.
2. **n_replicates advisory = a Beta-mixture projection**
   (``passn_power`` / ``needed_replicates``). A single R=1 draw per cell
   cannot reveal that cell's per-replicate probability. So this projects
   the effect of ADDING replicates with a theorem-level solvable-fraction
   plus Beta-ability mixture, calibrated so each model's marginal pass@1
   matches the pilot and the pair's solvable fraction matches the pilot's
   empirical union-solvable rate for that pair. It answers "do more
   replicates buy separation, or just lift both models together?".

Headline deliverable: replicate sizing, and why it comes with a caveat
-------------------------------------------------------------------------
For EVERY contrast, this script reports two numbers side by side: (i) how
many ADDITIONAL replicates the Beta-mixture projection says it would need
for 80% power at the CURRENT theorem count, and (ii) the n_theorems
block-bootstrap power CURVE, over ``N_THEOREMS_GRID``. It prints both
together (see ``_print_tier_report``), with a CAVEAT printed in the report
output itself, not only here: prior sizing work on this benchmark found
``n_theorems``, not replicates, to be the effective statistical lever.
More replicates re-sample the SAME theorem's difficulty, so the
Beta-mixture projection saturates. More theorems add genuinely
independent blocks.

Contrast tiers
-------------------------------------------------------------------------
This study pre-registers two contrast families. It sizes and corrects
them differently on purpose:

- **PRIMARY -- within-family ladder contrasts** (``build_within_family_
  contrasts``, 21 = 7 families x C(3, 2) size-pairs). Does accuracy change
  along ONE family's own small -> mid -> large ladder? This is the study's
  actual pre-registered scaling question. So this file Bonferroni-corrects
  it at full force: ``ALPHA_PRIMARY = ALPHA / 21``.
- **SECONDARY -- cross-family, size-matched contrasts** (``build_cross_
  family_contrasts``, 63 = 3 ladder positions x C(7, 2) family-pairs). Are
  two DIFFERENT families roughly comparable at the SAME size class? This
  was never the study's primary question. It is an exploratory, coarser
  check, so it gets the gentler Benjamini-Hochberg FDR correction
  (``q = 0.05``) rather than Bonferroni. It uses a real BH procedure
  (``benjamini_hochberg``; see its docstring for why FDR control, not
  FWER, is the right tool here, and why this differs from a fixed ``q/m``
  constant). Every report line and header for this tier carries an
  explicit SECONDARY label, so a reader can never mistake it for a
  primary result.

Data source: local tree or S3, and the LOUD unverified-verdict warning
-------------------------------------------------------------------------
Row files are JSONL (one JSON object per line) written by
``smolbench.deduction.lean.runner``. Cell rows have ``kind == "cell"`` and
carry (among other fields) ``theorem_id``, ``k``, ``rung`` (this file's
``prompt_rung``), ``model`` (the config's ``display_name``, which this
study sets to the EC2 spec key -- e.g. ``"glm-4.7"``), ``replicate_idx``,
and ``verdict``. A cell counts as a success only if ``verdict ==
"success"``. Every other verdict (``lean_error``, ``incomplete``,
``given_up``, ``exception``, ``replay_failed``, and the placeholder
``"unverified"``) is a failure.

Generation (``smolbench.deduction.lean.runner``, main ``.venv``) writes
``all_rows.jsonl`` with every cell's ``verdict`` set to the placeholder
``"unverified"``. It never talks to real Lean (``lean_dojo`` cannot live
on that venv; see ``smolbench/deduction/lean/verify.py``). A separate
deferred verification pass, ``scripts/deduction/lean_verify_rows.py`` (``.venv-lean``,
where ``lean_dojo`` IS installed), replays every candidate proof against
real Lean and writes the sibling ``verified_rows.jsonl`` with the real
verdicts. This script is meant to read ONLY ``verified_rows.jsonl``.
If this script reads ``all_rows.jsonl``, or finds even one cell row
whose verdict is still ``"unverified"``, every "success rate" it
computes will silently read at or near 0.000. That reading is
indistinguishable from a genuine "every model failed everything"
finding. So ``load_joint_cells`` prints a
hard-to-miss multi-line warning to stderr the moment it detects either
condition (see ``_warn_unverified``). A silent fallback would make this
correctness trap invisible.

There are two ways to point this script at data:
  * ``--s3`` downloads this study's run files itself (``verified_rows.jsonl``,
    falling back to ``all_rows.jsonl`` -- which triggers the warning above --
    per run) from ``s3://smolbench-results-414266451290/deduction/runs/``
    into a temp directory, so an analysis host needs no manual staging.
  * ``--results-dir PATH`` (default: this file's sibling ``results/``)
    reads an already-staged local tree,
    ``<results-dir>/runs/scaling_*/verified_rows.jsonl``.

Shared scaffolding
-------------------------------------------------------------------------
This file imports ``ALPHA``, ``POWER_TARGETS``, ``SEED``, ``fmt_r``, and
``results_dir`` from ``notebooks/_power_common.py`` (the same shared
module ``notebooks/induction/analysis/power_analysis.py`` uses).

Run this script in an ephemeral env via ``--no-project`` so plain ``uv
run`` does not resync and strip the notebook/dev extras (numpy/scipy
only):

    uv run --no-project --with numpy --with scipy \\
        python notebooks/deduction/analysis/power_analysis.py --s3

    # or against an already-staged local results tree:
    python notebooks/deduction/analysis/power_analysis.py \\
        --results-dir notebooks/deduction/results

    # restrict to a subset of models (e.g. one family) and fewer sims for
    # a quick smoke:
    python notebooks/deduction/analysis/power_analysis.py --results-dir DIR \\
        --models qwen3.5-27b,qwen3.5-122b-a10b,qwen3.5-397b-a17b --sims 200
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

    Python's builtin ``hash`` is salted per process (``PYTHONHASHSEED``).
    That would make the per-pair RNG streams below -- and so every
    reported power value and CI -- irreproducible across runs. This repo
    requires seeded, reproducible evals (never drop a seed to dodge a
    problem). So this function derives the stream seed from a stable
    digest instead.
    """
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "little")


# --------------------------------------------------------------------------- #
# Core statistics. Inlined rather than imported: this file must stay
# self-contained under ``uv run --no-project``.
# --------------------------------------------------------------------------- #
def pass_at_n(p: np.ndarray | float, n: int) -> np.ndarray | float:
    """Compute the probability that at least one of ``n`` replicates succeeds.

    Replicates are conditionally independent, each with per-replicate
    success probability ``p``: ``1 - (1 - p)**n``. At ``n == 1`` this
    equals ``p`` exactly -- the grid's N=1 point reduces to the
    per-replicate regime, this study's current R=1 pilot.

    Parameters
    ----------
    p : ndarray or float
        Per-replicate success probability (or an array of them), each in
        ``[0, 1]``.
    n : int
        Number of conditionally-independent replicates, ``>= 1``.

    Returns
    -------
    ndarray or float
        Same shape as ``p``.
    """
    return 1.0 - (1.0 - np.asarray(p, dtype=float)) ** n


def _log_binom_cdf_half(n: int, k: int) -> float:
    """Compute the log of the Binomial(n, 0.5) CDF at k.

    This computes ``log(sum_{i=0}^{k} C(n, i) * 0.5**n)`` in log space, via
    ``lgamma`` plus log-sum-exp. This stays stable for the large discordant
    totals (``n`` up to several thousand at the upper end of
    ``N_THEOREMS_GRID``) that would overflow a naive ``0.5**n`` in float.
    ``k`` must lie in ``[0, n]``.
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
    """Compute McNemar's exact two-sided binomial p-value for discordant counts.

    Under H0, the ``b`` "A-only-passes" cells follow ``Binomial(b + c,
    0.5)``. The two-sided p-value is ``min(1, 2 * P(X <= min(b, c)))``. With
    no discordant pairs (``b + c == 0``) there is no evidence either way,
    and p = 1.

    Parameters
    ----------
    b, c : int
        Discordant cell counts: ``b`` = model A succeeds, B fails;
        ``c`` = the reverse. Both ``>= 0``.

    Returns
    -------
    float
        The two-sided exact p-value, in ``[0, 1]``.
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2.0 * math.exp(_log_binom_cdf_half(n, k)))


def benjamini_hochberg(pvalues: np.ndarray, q: float) -> np.ndarray:
    """Run the Benjamini-Hochberg (1995) step-up procedure for FDR control.

    This controls the FALSE DISCOVERY RATE (FDR) -- the expected
    proportion of false positives AMONG the hypotheses this procedure
    rejects -- at level ``q``. This is a fundamentally different, and
    weaker, guarantee than the family-wise error rate (FWER) that a
    Bonferroni correction controls (the probability of ANY false positive
    across the whole family). FDR control tolerates a bounded FRACTION of
    false rejections among the rejections actually made, in exchange for
    substantially more power on large test families, where FWER control
    becomes very conservative. That distinction is exactly why this
    script's SECONDARY (cross-family) contrast tier -- an exploratory,
    size-matched check that was never this study's pre-registered primary
    question -- is corrected with BH here rather than Bonferroni. A flat
    ``ALPHA / N_SECONDARY`` would needlessly punish a family of tests that
    gates no downstream decision, while BH still gives an honest,
    principled multiple-testing correction. See the module docstring's
    "Contrast tiers" section.

    Algorithm: sort the ``m`` p-values ascending, ``p_(1) <= ... <=
    p_(m)``. Find the LARGEST rank ``i`` such that ``p_(i) <= i * q / m``.
    Reject the null for that hypothesis and every hypothesis with a
    strictly smaller p-value (ranks ``1..i``). If no rank satisfies the
    inequality, reject nothing.

    Parameters
    ----------
    pvalues : ndarray
        1-D array of p-values, one per hypothesis test. Need not be
        pre-sorted; the returned mask is aligned to this array's input
        order.
    q : float
        Target FDR level (e.g. ``0.05``). Must lie in ``(0, 1]``.

    Returns
    -------
    ndarray of bool
        Same shape as ``pvalues``; ``True`` where the null is rejected.

    Raises
    ------
    ValueError
        If ``pvalues`` is not 1-D, or ``q`` is not in ``(0, 1]``.

    Notes
    -----
    This is deliberately NOT a fixed ``q / m`` threshold applied uniformly
    to every p-value (a Bonferroni-style approximation, which this
    function's brief explicitly forbids). The per-rank threshold
    ``i * q / m`` GROWS with rank, so larger p-values face a laxer bar
    than a flat ``q / m`` would apply. Only the single smallest p-value
    is ever compared against the strict ``q / m``. Every other rank's
    threshold is less strict, which is the mechanism by which BH achieves
    more power than Bonferroni at the same nominal level.

    Examples
    --------
    >>> import numpy as np
    >>> ps = np.array([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205])
    >>> benjamini_hochberg(ps, 0.05)
    array([ True,  True,  True, False, False, False, False, False])
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

    `load_joint_cells` calls this the moment it detects either an
    ``all_rows.jsonl``-named input file, or a cell row whose ``verdict`` is
    still the generation-time placeholder ``"unverified"`` (see the module
    docstring's "Data source" section). A silent fallback here would
    produce a whole report of near-zero success rates that reads exactly
    like a genuine "every model failed everything" finding. This banner
    exists specifically so that never happens unnoticed.

    Parameters
    ----------
    reasons : list of str
        One line per distinct trigger (e.g. a specific file's name, or a
        count of unverified cell rows), appended verbatim into the banner.
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

    Raises ``SystemExit`` if ANY of `paths` has `SUPERSEDED_MARKER` in its
    file name, and names every offender. A warning would not do here: these
    files parse perfectly and their rows are well-formed, so ingesting one
    produces a complete, plausible, WRONG report, not a crash.

    This matches the marker on the basename only. A directory legitimately
    named after an audit (``.../superseded_audit/verified_rows.jsonl``) is
    not the thing this guard targets. The marker stays upper-case, exactly
    as ``run_study.py`` writes it.
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
    """Refuse re-verified rows that still carry the ungraded sentinel.

    Raises ``SystemExit`` if any row has ``kind == "cell"`` and `field`
    equal to the generation-time placeholder ``"unverified"``, and names
    the offending count and `source`. A warning would not do here, for the
    same reason as `reject_superseded`: a cell whose `field` is still the
    placeholder loads and grades exactly like a real measurement.
    `grade_verdicts` has no special case for it, and it is deliberately NOT
    a member of `UNMEASURABLE_VERDICTS` (adding it there would convert this
    loud condition into a SILENT DROP, which is worse than the bug this
    guard exists to catch). Left unchecked, the sentinel scores as a
    failure, and the resulting report is complete, plausible, and wrong.

    Parameters
    ----------
    rows : Iterable[dict]
        Already-parsed rows from ONE source file. This function does no I/O
        of its own -- a caller reading from a local path, an S3 download, or
        an in-memory test fixture uses it identically -- and it must run
        BEFORE those rows reach `grade_verdicts`.
    field : str
        The verdict field to check. Different callers read different
        fields for the same concept: `error_bars.lane_outcomes` checks
        ``"verdict"`` on its primary rows and ``"recovered_verdict"`` on
        its recovery sibling (whose rows do not even have a ``"verdict"``
        key), and `hint_vs_noise.load_rungs` checks ``"verdict"``. This
        function takes the field as an explicit argument, rather than
        hardcoding ``"verdict"``, so one helper can serve every caller
        without any of them silently checking the wrong key.
    source : Path or str
        Where `rows` came from, embedded verbatim in the raised message so a
        reader is told exactly which file to go re-verify.

    Raises
    ------
    SystemExit
        One or more rows have ``row["kind"] == "cell"`` and
        ``row[field] == "unverified"``.
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
    """Apply THE row rule of this study, in one place.

    This grades ONE cell from the verdicts of its rows IN FILE ORDER (rows
    are appended, so file order is chronological). It applies two rules.
    Both directions were wrong before -- see `load_joint_cells` for the
    measurements that settled them:

      * EARLIEST SURVIVING ATTEMPT WINS. A later retry is an independent
        draw. Taking it would report pass@N as pass@1.
      * An UNMEASURABLE verdict is not a measurement. It neither scores 0
        nor claims the cell, so the next row still gets its chance.

    Returns 1 (success), 0 (a real failure), or ``None`` when no row is a
    measurement at all -- "no surviving attempt". Callers resolve that
    case differently on purpose: `load_joint_cells` and
    ``hint_vs_noise.load_rungs`` leave the cell ABSENT (the drop rule),
    while ``error_bars.build_pool`` may score it 0 when another lane graded
    the same cell (count-as-failure). That policy choice stays with the
    caller. Only the rule for reading rows lives here.

    `load_joint_cells` accepts a single row's verdict in a one-element list
    while it streams rows: ``None`` there means "this row is not a
    measurement, keep looking" -- the same rule unrolled.
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

    Parameters
    ----------
    row_files : list of Path
        JSONL row files to UNION (e.g. the 21 checkpoints' individual
        ``verified_rows.jsonl``). Each line is one JSON object; ``kind ==
        "cell"`` rows are the gradeable marks, everything else (e.g.
        ``kind == "sanity"``) is skipped.
    models : tuple of str, optional
        Restrict pairing to exactly this model set. This function keeps a
        cell only if it is graded for EVERY model in this set (or, if
        ``models`` is ``None``, for every model actually present anywhere
        in the union of ``row_files``). Use a smaller set than the full
        roster to analyze a partial or single-family run, without every
        contrast reporting "no data".

    Returns
    -------
    (models, blocks, prompt_rungs)
        ``models`` -- sorted list of the model spec-keys actually used for
        pairing (== ``sorted(models)`` if given, else every model spec-key
        present in the loaded cell rows).
        ``blocks`` -- ``{theorem_id: {(k, prompt_rung): {model: 1 or 0}}}``,
        restricted to cells graded for EVERY model in ``models`` (the
        paired set) and to theorems with at least one such cell. ``1`` ==
        ``verdict == "success"``; ``0`` == any other verdict. A resample
        unit for `bootstrap_power` is one whole theorem block.
        ``prompt_rungs`` -- the sorted distinct ``rung`` values present in
        ``blocks`` (this file's "prompt rung"; see the module docstring's
        terminology note -- NOT a model's ladder position).

    Notes
    -----
    This function reads only ``replicate_idx == 0``. This study collects
    R=1, so this selects the (only) replicate collected today. It also
    stays correct without modification if a later run adds more replicates
    per cell -- it is a filter, not an assumption that no other replicate
    exists.

    This function refuses (``SystemExit``, via `reject_superseded`) any
    input file whose name carries the ``SUPERSEDED`` marker, before reading
    a single row.

    It prints a LOUD warning to stderr (`_warn_unverified`) if any input
    file's basename is ``"all_rows.jsonl"`` (the unverified generation-time
    log), or if any loaded cell row's ``verdict`` is still the placeholder
    ``"unverified"`` -- see that function's docstring and the module
    docstring's "Data source" section. This check runs regardless of
    whether the offending rows end up in the final paired ``blocks``: a row
    filtered out downstream for some other reason is still evidence the
    input data is unverified.
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
    """Compute each model's pass@1 rate over all paired cells.

    This is the pilot point estimate.

    Parameters
    ----------
    models : list of str
        Models to compute a rate for (typically `load_joint_cells`'s
        returned ``models``).
    blocks : dict
        As returned by `load_joint_cells`.

    Returns
    -------
    dict of str -> float
        ``{model: successes / total_paired_cells}``. ``float("nan")`` for
        every model if ``blocks`` is empty (no paired cells at all).
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
    """Compute the fraction of paired cells solved by AT LEAST ONE of `models`.

    The Beta-mixture pass@N advisory (`passn_power`) needs a per-pair
    theorem/cell "solvable at all" fraction. The empirically honest anchor
    is "did either of the two models being compared get it", which is
    ``>=`` the best single model's rate by construction.
    `compute_contrast_sizing` calls this per CONTRAST, with exactly the
    pair's two models, not the whole loaded roster. So the calibration
    reflects that specific pair's difficulty, not a union across all 21
    models. A union across all 21 models would be a much less meaningful
    anchor at this roster size: with 21 models, "did ANY of them solve it"
    trends toward 1.0 regardless of how the two compared models actually
    perform.

    Parameters
    ----------
    models : list of str
        The model(s) whose union-solved fraction to compute.
    blocks : dict
        As returned by `load_joint_cells`.

    Returns
    -------
    float
        In ``[0, 1]``; ``float("nan")`` if ``blocks`` is empty.
    """
    solved = tot = 0
    for cmap in blocks.values():
        for mv in cmap.values():
            tot += 1
            solved += 1 if any(mv[m] for m in models) else 0
    return solved / tot if tot else float("nan")


def pooled_discordant_counts(blocks: dict, model_a: str, model_b: str) -> tuple:
    """Compute pooled McNemar discordant counts ``(b, c)`` for one model pair.

    ``b`` counts cells where `model_a` succeeds and `model_b` fails.
    ``c`` counts the reverse. This pools over EVERY paired theorem and
    EVERY prompt rung in `blocks`, with no per-rung stratification.
    McNemar pooled over prompt rungs is the single-stratum collapse of the
    rung-stratified CMH test that would run at analysis time. This is the
    conservative choice for a power/sizing script (see the module
    docstring).

    Parameters
    ----------
    blocks : dict
        As returned by `load_joint_cells`; every cell's model-map is
        assumed to contain both `model_a` and `model_b` (true by
        construction for any pair both present in `load_joint_cells`'s
        ``models`` return value).
    model_a, model_b : str
        The two model spec-keys to compare.

    Returns
    -------
    (int, int)
        ``(b, c)`` discordant counts, both ``>= 0``.
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
    """Build the 21 PRIMARY within-family ladder contrasts.

    For each of the 7 `FAMILIES`, this builds every
    ``itertools.combinations(range(3), 2)`` pair of ladder positions
    (small-vs-mid, small-vs-large, mid-vs-large): 7 families x 3 size-pairs
    = 21 contrasts.

    Returns
    -------
    list of (str, str, str)
        ``(label, model_a, model_b)`` triples. Order: grouped by family, in
        `FAMILIES` order. Within each family, ladder-position pairs follow
        ``itertools.combinations(range(3), 2)`` order (i.e. (0,1), (0,2),
        (1,2)). Labels: ``f"[{family} ladder] {model_a} vs {model_b}"``.
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
    """Build the 63 SECONDARY cross-family, size-matched contrasts.

    For each ladder position ``pos in range(3)`` (small/mid/large), and
    each of ``itertools.combinations(FAMILIES, 2)`` = C(7, 2) = 21 family
    pairs, this compares ``FAMILIES[fam_a][pos]`` vs
    ``FAMILIES[fam_b][pos]``: 3 ladder positions x 21 family-pairs = 63
    contrasts. This mirrors
    ``notebooks/induction/analysis/power_analysis.py::build_secondary_contrasts``'s
    structure (grouped by size class, then by family pair).

    Returns
    -------
    list of (str, str, str)
        ``(label, model_a, model_b)`` triples, same shape as
        `build_within_family_contrasts`'s return value. Order: grouped by
        ladder position ``pos = 0, 1, 2``. Within each position, family
        pairs follow `FAMILIES`' dict-iteration (definition) order, via
        ``itertools.combinations(FAMILIES, 2)``. Labels:
        ``f"[SECONDARY | {small/mid/large}] {model_a} vs {model_b}"`` --
        this always carries the literal "SECONDARY" tag, so a reader can
        never mistake this tier's output for a primary result (see the
        module docstring).
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
    """Bootstrap McNemar power and the paired rate-gap CI for one pair.

    This resamples ``n_theorems`` whole theorem blocks with replacement
    from the loaded pool, pools their cells, and computes McNemar's exact
    p for `model_a` vs `model_b` each simulation. It returns ``(power,
    gap_lo, gap_hi)``: power is the rejection fraction at `alpha`, and
    ``[gap_lo, gap_hi]`` is the 5th/95th-percentile bootstrap CI of the
    paired success-rate difference ``rate_a - rate_b`` (used for the
    near-tie / equivalence verdict).

    Parameters
    ----------
    blocks : dict
        As returned by `load_joint_cells`.
    model_a, model_b : str
        The two model spec-keys to compare.
    n_theorems : int
        Candidate theorem-block count to resample up to.
    alpha : float
        Significance threshold for each simulated McNemar test (this
        tier's ``ALPHA_PRIMARY`` or ``ALPHA_SECONDARY``).
    sims : int
        Number of bootstrap resamples.
    rng : numpy.random.Generator
        Source of randomness. Callers pass a freshly-seeded generator
        (see `_seed_of`), so repeated runs are byte-identical.

    Returns
    -------
    (float, float, float)
        ``(power, gap_lo, gap_hi)``.

    Notes
    -----
    Design: this caches `mcnemar_exact_p` on the discrete key
    ``(b + c, min(b, c))``. The discordant-pair total takes only a small
    number of distinct values across `sims` resamples, so this is far
    cheaper than one fresh `math.lgamma` sweep per simulation.
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
    """Project McNemar power for a pair at `n_replicates`, via the mixture.

    Each theorem is solvable with probability `frac_solvable` (shared by
    both models -- the SAME theorems). Each solvable cell draws an
    independent per-replicate success probability from ``Beta(m *
    beta_conc, (1 - m) * beta_conc)``, with the model's calibrated
    solvable-cell mean ``m = rate / frac_solvable`` -- shared coarse
    difficulty plus idiosyncratic per-model skill. `pass_at_n` converts
    cells to pass@N. This draws both models' cell outcomes and computes
    McNemar's p. It returns the rejection fraction over `sims`
    simulations.

    Parameters
    ----------
    rate_a, rate_b : float
        Each model's observed marginal pass@1 rate (from `marginal_rates`).
    frac_solvable : float
        Fraction of theorems solvable by at least one of the pair (from
        `union_solvable_fraction`, called with just this pair -- see that
        function's docstring). Must be ``> 0`` for calibration to be
        possible. Callers must not call this with ``frac_solvable == 0``.
    n_theorems, n_prompt_rungs : int
        Grid shape: `n_theorems` theorems, each with `n_prompt_rungs` cells
        (this file's prompt-rung count -- see module docstring's
        terminology note; NOT a model's ladder position).
    n_replicates : int
        Candidate replicate count ``N`` for the pass@N conversion.
    alpha : float
        Significance threshold for each simulated McNemar test.
    sims : int
        Number of Monte-Carlo simulations.
    beta_conc : float
        Beta concentration (``a + b``) for the solvable-cell mixture.
    rng : numpy.random.Generator
        Source of randomness. Callers pass a freshly-seeded generator.

    Returns
    -------
    float
        Rejection fraction in ``[0, 1]``, or ``float("nan")`` if the
        implied solvable-cell mean for either model is outside ``(0, 1]``
        (the observed rate cannot be calibrated against this
        `frac_solvable` -- e.g. `frac_solvable` too small for the observed
        marginal rate to fit inside a probability).

    Notes
    -----
    Design: this caches `mcnemar_exact_p` on ``(b + c, min(b, c))`` per
    simulation, the same technique as `bootstrap_power` (see its Notes).
    This is a pure performance optimization. The projected power is
    identical to the un-cached computation.
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
    """Find the smallest ``n_replicates`` in `grid` reaching `target` power.

    This scans `grid` in ascending order via `passn_power`, and stops at
    the first grid point that reaches `target`. This mirrors
    ``notebooks/induction/analysis/power_analysis.py``'s ``replicates_needed``
    early-stop discipline: it is cheaper than always computing the full
    grid, and the natural reading of "how many replicates would be needed"
    is the smallest sufficient count.

    Parameters
    ----------
    rate_a, rate_b, frac_solvable, n_theorems, n_prompt_rungs, alpha, sims,
    beta_conc, rng
        Passed through to `passn_power` unchanged. See its docstring.
    grid : tuple of int, default N_REPLICATES_GRID
        Candidate replicate counts to scan, ascending.
    target : float, default POWER_TARGETS[0]
        Power threshold to reach.

    Returns
    -------
    int or None
        The smallest `grid` value reaching `target` power, or `None` if no
        grid value does (including the case where `passn_power` returns
        NaN at every grid point -- an uncalibratable pair at this
        `frac_solvable`, which no amount of replicates can fix).
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
    """Record one model-pair contrast's observed statistics and replicate sizing.

    `compute_contrast_sizing` produces one of these for every contrast
    whose two models are both present in the currently loaded/paired data.
    A contrast naming an absent model is skipped upstream (see
    `_print_tier_report`), and never gets one of these.

    Attributes
    ----------
    label : str
        The contrast's report label, from `build_within_family_contrasts`
        or `build_cross_family_contrasts`.
    model_a, model_b : str
        The two model spec-keys being compared.
    n_paired_theorems : int
        Number of theorem blocks with at least one cell graded for every
        model in the loaded/paired set (``== len(blocks)``; identical
        across every contrast computed from the same `blocks`).
    observed_gap : float
        ``rates[model_a] - rates[model_b]``, the pilot's pass@1 rate gap.
    observed_p : float
        Pooled (all paired cells, all prompt rungs) McNemar exact
        two-sided p-value for `model_a` vs `model_b` on the CURRENTLY
        collected R=1 data -- an observed statistic, not a projection.
    theorem_curve : tuple of float
        Block-bootstrap McNemar power at each point of `N_THEOREMS_GRID`,
        same order.
    r_theorems : dict of float -> (int or None)
        Smallest `N_THEOREMS_GRID` point reaching each of `POWER_TARGETS`,
        or `None` if no grid point reaches it.
    ci_lo, ci_hi : float
        5th/95th-percentile bootstrap CI of the paired rate gap at the
        LARGEST `N_THEOREMS_GRID` point.
    near_tie : bool
        True if `observed_gap` and ``[ci_lo, ci_hi]`` both fall inside
        ``+/- EQUIV_BAND`` -- a certified equivalence, not merely an
        unresolved difference test.
    needed_replicates : int or None
        Smallest `N_REPLICATES_GRID` point projected (via the Beta-mixture
        pass@N model) to reach `POWER_TARGETS[0]` power at the CURRENT
        `n_paired_theorems`, or `None` if no grid point reaches it.
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
    """Compute one contrast's full observed statistics + replicate sizing.

    Parameters
    ----------
    blocks : dict
        As returned by `load_joint_cells`.
    label : str
        This contrast's report label.
    model_a, model_b : str
        The two model spec-keys to compare.
    rates : dict of str -> float
        Per-model pass@1 rate, from `marginal_rates`.
    prompt_rungs : list of str
        Distinct prompt-rung values present in `blocks`. Used only for its
        length (`n_prompt_rungs`, the Beta-mixture's per-theorem cell
        count).
    alpha : float
        Per-test significance threshold for every McNemar test inside
        `bootstrap_power` / `passn_power` (this tier's `ALPHA_PRIMARY` or
        `ALPHA_SECONDARY`).
    sims : int
        Monte-Carlo simulations per grid point.

    Returns
    -------
    ContrastSizing or None
        `None` if either `model_a` or `model_b` is not in `rates` (not
        part of the currently loaded/paired model set). This lets callers
        report a clean "skipped, no data" line for pre-registered
        contrasts the current data does not cover -- e.g. a partial run
        analyzed via `--models` -- instead of raising.

    Notes
    -----
    This reseeds two independent `np.random.default_rng` streams per
    contrast: one for the n_theorems bootstrap curve, one for the
    replicate projection. Both derive from `(model_a, model_b)` via
    `_seed_of` -- the SEED-threading idiom ported verbatim from the
    archived script, so re-running this script produces byte-identical
    output.
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
    """Compute and print one contrast tier's full observed + sizing report.

    This iterates every contrast in `contrasts`. It skips any whose
    model(s) are absent from the currently loaded/paired data, with a
    summary line, not silently. It computes `ContrastSizing` for the rest.
    It applies this tier's multiple-comparisons correction to the OBSERVED
    p-values: a fixed Bonferroni threshold (`ALPHA_PRIMARY`) for the
    within-family tier, or the real `benjamini_hochberg` procedure
    (`Q_SECONDARY`) for the cross-family tier. It prints one block per
    contrast, plus a tier summary line.

    It prints the n_theorems-vs-replicates CAVEAT (see the module
    docstring's "Headline deliverable" section) once per tier, immediately
    before the per-contrast blocks. This appears in the printed output
    itself, not only as a code comment, per this script's brief.

    Parameters
    ----------
    tier_label : str
        Human-readable tier name for the section header.
    contrasts : list of (str, str, str)
        This tier's full pre-registered contrast list (21 or 63 entries),
        as returned by `build_within_family_contrasts` or
        `build_cross_family_contrasts`.
    blocks, rates, prompt_rungs
        As returned by `load_joint_cells` / `marginal_rates`.
    secondary : bool
        If True, this is the SECONDARY (cross-family) tier: every header
        and summary line is explicitly labelled SECONDARY, sizing uses
        `ALPHA_SECONDARY`, and observed significance is decided by
        `benjamini_hochberg` at `Q_SECONDARY`. If False, this is the
        PRIMARY (within-family) tier: sizing and observed significance
        both use the fixed `ALPHA_PRIMARY` Bonferroni threshold.
    sims : int
        Monte-Carlo simulations per grid point, threaded through to every
        `compute_contrast_sizing` call.
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
    """Download this study's per-run row files from S3 into `tmp_dir`.

    This lists ``s3://S3_BUCKET/S3_PREFIX`` with ``Delimiter="/"`` to
    enumerate run prefixes, and keeps the ones named ``scaling_*`` (this
    study's run naming convention -- see the module docstring). For each
    run, it downloads ``verified_rows.jsonl`` if present. If not present,
    it falls back to ``all_rows.jsonl``, which triggers `_warn_unverified`
    once `load_joint_cells` loads the fallback file.

    Parameters
    ----------
    tmp_dir : Path
        Destination directory, created by the caller via
        ``tempfile.mkdtemp()``. This function creates one subdirectory per
        run under it, named after the run prefix.

    Returns
    -------
    list of Path
        One path per successfully-downloaded run: its
        ``verified_rows.jsonl``, or, failing that, ``all_rows.jsonl``.
        This silently omits runs with neither object present (nothing to
        download).

    Notes
    -----
    This imports ``boto3``/``botocore`` LAZILY, so every other code path
    in this script (local ``--results-dir`` analysis, every
    unit-testable pure function) stays usable in an environment without
    boto3 installed.
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

    Parameters
    ----------
    argv : list of str, optional
        Argument vector to parse. ``None`` uses ``sys.argv[1:]`` (the
        normal CLI entrypoint). Tests pass an explicit list here to
        exercise this function without touching real argv.

    Returns
    -------
    argparse.Namespace
        With attributes ``s3`` (bool), ``results_dir`` (Path), ``models``
        (str or None), ``sims`` (int).
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
    """Run the deduction family-ladder replicate-sizing power analysis.

    This function loads the requested run files (S3 or local), pairs
    per-cell joint outcomes across the requested model set, and prints the
    full report: a data summary, the PRIMARY (within-family) tier's 21
    contrasts, and the SECONDARY (cross-family) tier's 63 contrasts. Each
    contrast reports observed significance, a block-bootstrap n_theorems
    power curve, and a Beta-mixture replicate-sizing projection. See the
    module docstring for the full design.

    Parameters
    ----------
    argv : list of str, optional
        Passed through to `parse_args`.

    Returns
    -------
    int
        Process exit code: 0 on a normal report, 1 if no row files or no
        fully-paired cells were found for the requested model set.
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
