"""Power analysis for the Lean-4 deduction MODEL-COMPARISON study.

The deduction "result we want to measure" is a RANKING of models by
next-tactic success rate -- e.g. on the all-MoE pilot, ``qwen3.5 (29.9%) >
gpt-oss (24.7%) >> nemotron-3 (6.5%)``. This script sizes how many
theorems and rollouts (``n_theorems``, ``n_rollouts``) are needed to be
CONFIDENT in that ranking for a given trio of models: every genuinely
different model pair separated at >=80% power under a Bonferroni-corrected
alpha, and any near-tie certified equivalent within a stated band rather
than left ambiguous.

It is the deduction counterpart of ``notebooks/periodic/power_analysis.py``
(the induction study's sizer) and shares the McNemar machinery of
``scripts/lean_gate_power.py`` (the CoT-recipe gate's sizer). It differs from
both in WHAT it contrasts: periodic sizes archetype-vs-archetype accuracy on
counting quizzes; the gate sizes ARM-vs-ARM (bare-tactic vs CoT SFT) of ONE
model; this sizes MODEL-vs-MODEL success across a trio.

Statistical design (deliberately the same shape as the gate's, so the two are
directly comparable)
---------------------------------------------------------------------------
- **Unit of observation = one ``(theorem_id, k, rung)`` cell.** The three
  models are evaluated on the SAME cells (identical theorem sample, identical
  rung ladder, model-independent trivial-skips), so every model pair is a
  PAIRED comparison and the natural test is McNemar's exact test on the
  discordant cells (cells where exactly one model of the pair succeeds). This
  is the induction study's "replicate, don't change the task" principle in the
  deduction setting: we add cells (more theorems, more rollouts), never make a
  theorem easier.
- **Stratify by rung.** Difficulty varies systematically with the rung (the
  amount of proof context handed to the model: ``stepk:1`` gives least,
  ``hint:3`` most), exactly as difficulty varies with the harmonic ``k`` in the
  periodic study. The analysis-time test is therefore the rung-stratified
  Cochran-Mantel-Haenszel test; McNemar pooled over rungs (used here for
  sizing) is its single-stratum collapse and is the conservative choice for
  power (pooling can only dilute a consistent per-stratum effect).
- **Cell outcome = pass@N.** A model "passes" a cell if ANY of its ``N``
  rollouts verifies: ``P(pass@N) = 1 - (1 - p)**N`` for per-rollout success
  probability ``p`` (``pass_at_n`` from the gate script). ``N == 1`` is the
  per-rollout regime the R=1 pilot measures directly.
- **Two model pairs, two questions.** For each of the three pairs in a trio we
  ask: is the pair a genuine DIFFERENCE (size ``n`` to detect it at >=80%
  power) or a near-TIE (certify equivalence within ``+/- EQUIV_BAND`` via the
  bootstrap CI of the paired rate gap)? The periodic study made the same
  split -- 15 clearly-separated contrasts sized as difference tests, 3
  near-ties certified by TOST equivalence.

Where the numbers come from
---------------------------
Unlike the gate sizer (which sweeps ASSUMED effects, having no pilot), this
script reads a REAL pilot run's per-cell joint outcomes -- for the MoE trio,
``results/runs/lean_moe_pilot`` (R=1, 30-theorem seeded sample of
``novel_premises/val``); for the archetype trio,
``results/runs/lean_arch_pilot`` once it has run. Two estimators use that data:

1. **n_theorems sizing = block bootstrap of the observed joint cells.**
   Resample whole THEOREMS with replacement (a theorem block carries all its
   rungs, preserving within-theorem cross-rung correlation) up to the target
   ``n_theorems``, recompute each pair's McNemar p, and report the rejection
   rate. This uses the effect sizes we actually observe -- no parametric
   effect assumption -- and is the primary sizing. Its one caveat, stated in
   the output, is that the pilot has only ~22 gradeable theorems, so the
   bootstrap population is those 22 (a larger pilot would tighten the tail).
2. **n_rollouts (pass@N) advisory = the gate's Beta-mixture.** A single R=1
   draw per cell cannot reveal that cell's per-rollout probability, so the
   effect of ADDING rollouts is projected with the gate script's theorem-level
   solvable-fraction + Beta-ability mixture, calibrated so each model's
   marginal pass@1 matches the pilot and the solvable fraction matches the
   pilot's empirical union-solvable rate. It answers "do more rollouts buy
   separation, or just lift every model together?".

Run (ephemeral env via --no-project so plain ``uv run`` does not resync and
strip the notebook/dev extras; numpy/scipy only):
    uv run --no-project --with numpy --with scipy \
        python notebooks/lean/power_analysis.py

    # a specific pilot / trio, or both:
    python notebooks/lean/power_analysis.py --run lean_moe_pilot
    python notebooks/lean/power_analysis.py --run lean_arch_pilot
"""

from __future__ import annotations

# Cap the BLAS/OpenMP thread pools BEFORE numpy is imported: this script is
# routinely run on the shared eval container WHILE a lean sweep's Dojo
# verifiers are resident, and numpy's default 16-thread OpenBLAS pool trips
# RLIMIT_NPROC there ("pthread_create failed: Resource temporarily
# unavailable"). One thread is plenty for a 2000-sim Monte Carlo.
import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np


def _seed_of(name: str) -> int:
    """Deterministic 32-bit seed from a model name.

    Python's builtin ``hash`` is salted per process (``PYTHONHASHSEED``), which
    would make the per-pair RNG streams -- and thus the reported powers --
    irreproducible across runs. This repo requires seeded, reproducible evals,
    so derive the stream seed from a stable digest instead.
    """
    return int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "little")

# Reuse the gate sizer's exact, unit-tested McNemar + pass@N math rather than
# re-deriving it (repo convention: __file__-anchored, cwd-independent import).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
from lean_gate_power import mcnemar_exact_p, pass_at_n  # noqa: E402

# --------------------------------------------------------------------------- #
# Design constants
# --------------------------------------------------------------------------- #
SEED = 1776
ALPHA = 0.05
POWER_TARGET = 0.80
SIMS = 4000
#: Equivalence half-width for near-ties (pass@1 rate points). A pair whose
#: bootstrap 90% CI for the paired rate gap falls inside +/- this is certified
#: "indistinguishable at this resolution" rather than sized as a difference --
#: the same treatment the periodic study gives its near-tie contrasts.
EQUIV_BAND = 0.10

N_THEOREMS_GRID = (30, 60, 100, 150, 200, 300)
N_ROLLOUTS_GRID = (1, 2, 3, 4, 8)
#: n_theorems at which the pass@N advisory is evaluated (the val pool is 1104,
#: so 150 -- the gate/dense-micro working size -- is comfortable).
ADVISORY_N_THEOREMS = 150
#: Beta concentration for the pass@N mixture (matches lean_gate_power default).
BETA_CONC = 5.0

RESULTS_RUNS = _REPO_ROOT / "notebooks" / "lean" / "results" / "runs"

#: Trio rosters by pilot run-name, in a FIXED display order (weakest last is
#: not assumed; order is just for stable printing). Values are the ``model``
#: display strings the runner writes into all_rows.jsonl.
TRIOS = {
    "lean_moe": [
        "gpt-oss-120b-base",
        "nemotron-3-super-120b-a12b-base",
        "qwen3.5-397b-a17b-base",
    ],
    "lean_arch": [
        "llama-31-405b-base",
        "nemotron-ultra-253b-base",
        "llama4-maverick-base",
    ],
}


# --------------------------------------------------------------------------- #
# Pilot loading
# --------------------------------------------------------------------------- #
def load_joint_cells(run_dir: Path) -> tuple[list[str], dict, list[str]]:
    """Load a pilot run's per-cell joint outcomes, paired across its models.

    Parameters
    ----------
    run_dir : Path
        A sweep run directory containing ``all_rows.jsonl`` (append-only,
        one JSON object per line; ``kind == "cell"`` rows are the gradeable
        marks, ``kind == "sanity"`` rows are skipped here).

    Returns
    -------
    (models, blocks, rungs)
        ``models`` -- the model display names present, sorted.
        ``blocks`` -- ``{theorem_id: {(k, rung): {model: 1|0}}}`` restricted to
        cells present for EVERY model (the paired set). 1 == ``verdict ==
        "success"``, 0 == any other verdict (lean_error / incomplete /
        exception). A resample unit is a whole theorem block.
        ``rungs`` -- the sorted distinct rungs, for reporting.

    Notes
    -----
    Only ``rollout_idx == 0`` is read: the pilots are R=1, so this is the
    per-rollout (pass@1) outcome. Cells missing for some model of the trio
    (should not happen -- trivial-skips are model-independent) are dropped
    from the paired set so every retained cell contributes to every pair.
    """
    rows = [json.loads(line) for line in (run_dir / "all_rows.jsonl").read_text().splitlines() if line]
    cells = [r for r in rows if r.get("kind") == "cell" and r.get("rollout_idx", 0) == 0]
    models = sorted({r["model"] for r in cells})
    rungs = sorted({r["rung"] for r in cells})

    # theorem_id -> (k, rung) -> model -> outcome
    raw: dict[str, dict[tuple, dict[str, int]]] = {}
    for r in cells:
        cell_key = (r["k"], r["rung"])
        raw.setdefault(r["theorem_id"], {}).setdefault(cell_key, {})[r["model"]] = (
            1 if r.get("verdict") == "success" else 0
        )

    # Keep only cells graded for the full model set (paired), and only
    # theorems with at least one such cell.
    blocks: dict[str, dict[tuple, dict[str, int]]] = {}
    n_models = len(models)
    for thm, cmap in raw.items():
        kept = {ck: mv for ck, mv in cmap.items() if len(mv) == n_models}
        if kept:
            blocks[thm] = kept
    return models, blocks, rungs


def marginal_rates(models, blocks) -> dict[str, float]:
    """Per-model pass@1 rate over all paired cells (the pilot point estimate)."""
    succ = {m: 0 for m in models}
    tot = 0
    for cmap in blocks.values():
        for mv in cmap.values():
            tot += 1
            for m in models:
                succ[m] += mv[m]
    return {m: (succ[m] / tot if tot else float("nan")) for m in models}


def union_solvable_fraction(models, blocks) -> float:
    """Fraction of paired cells solved by AT LEAST ONE model.

    The Beta-mixture pass@N advisory needs a theorem/cell solvable fraction;
    the empirically honest anchor is "did any model in the trio get it",
    which is >= the best single model's rate by construction.
    """
    solved = tot = 0
    for cmap in blocks.values():
        for mv in cmap.values():
            tot += 1
            solved += 1 if any(mv[m] for m in models) else 0
    return solved / tot if tot else float("nan")


# --------------------------------------------------------------------------- #
# n_theorems sizing: block bootstrap of the observed joint cells (pass@1)
# --------------------------------------------------------------------------- #
def bootstrap_power(
    blocks: dict,
    a: str,
    b: str,
    n_theorems: int,
    *,
    alpha: float,
    sims: int,
    rng: np.random.Generator,
) -> tuple[float, float, float]:
    """Bootstrap McNemar power and the paired rate-gap CI for one model pair.

    Resamples ``n_theorems`` whole theorem blocks with replacement from the
    pilot pool, pools their cells, and computes McNemar's exact p for
    ``a`` vs ``b`` each sim. Returns ``(power, gap_lo, gap_hi)`` where power is
    the rejection fraction at ``alpha`` and ``[gap_lo, gap_hi]`` is the 90%
    bootstrap CI of the paired success-rate difference ``rate_a - rate_b``
    (used for the equivalence verdict).
    """
    thm_ids = list(blocks.keys())
    # Pre-flatten each theorem's per-cell (a, b) outcomes to plain arrays so the
    # inner sim loop is pure integer accumulation, not dict walking.
    per_thm = {
        t: np.array([(cmap[ck][a], cmap[ck][b]) for ck in cmap], dtype=np.int8)
        for t, cmap in blocks.items()
    }
    idx = np.arange(len(thm_ids))
    rejects = 0
    gaps = np.empty(sims)
    for s in range(sims):
        pick = rng.choice(idx, size=n_theorems, replace=True)
        stacked = np.concatenate([per_thm[thm_ids[i]] for i in pick])
        oa, ob = stacked[:, 0], stacked[:, 1]
        b_disc = int(np.sum((oa == 1) & (ob == 0)))
        c_disc = int(np.sum((oa == 0) & (ob == 1)))
        if mcnemar_exact_p(b_disc, c_disc) < alpha:
            rejects += 1
        gaps[s] = oa.mean() - ob.mean()
    return rejects / sims, float(np.quantile(gaps, 0.05)), float(np.quantile(gaps, 0.95))


# --------------------------------------------------------------------------- #
# n_rollouts advisory: Beta-mixture pass@N (projects unobserved rollouts)
# --------------------------------------------------------------------------- #
def passn_power(
    rate_a: float,
    rate_b: float,
    frac_solvable: float,
    n_theorems: int,
    n_rollouts: int,
    n_rungs: int,
    *,
    alpha: float,
    sims: int,
    beta_conc: float,
    rng: np.random.Generator,
) -> float:
    """Projected McNemar power for a pair at ``n_rollouts`` via the mixture.

    Theorem solvable w.p. ``frac_solvable`` (shared by both models -- same
    theorems); each solvable cell draws an independent per-rollout probability
    from a Beta with the model's calibrated solvable-cell mean
    (``rate / frac_solvable``), giving shared coarse difficulty plus
    idiosyncratic per-model skill. Cells convert to pass@N, both models' cell
    outcomes are drawn, and McNemar's p is computed. Returns rejection fraction.
    """
    ma = rate_a / frac_solvable
    mb = rate_b / frac_solvable
    if not (0 < ma <= 1 and 0 < mb <= 1):
        return float("nan")  # solvable fraction too small to host this rate
    rejects = 0
    shape = (n_theorems, n_rungs)
    for _ in range(sims):
        solvable = rng.random(n_theorems) < frac_solvable
        solv_cell = np.repeat(solvable[:, None], n_rungs, axis=1)
        pa = np.where(solv_cell, rng.beta(ma * beta_conc, (1 - ma) * beta_conc, shape), 0.0)
        pb = np.where(solv_cell, rng.beta(mb * beta_conc, (1 - mb) * beta_conc, shape), 0.0)
        sa = pass_at_n(pa, n_rollouts)
        sb = pass_at_n(pb, n_rollouts)
        oa = rng.random(shape) < sa
        ob = rng.random(shape) < sb
        b_disc = int(np.sum(oa & ~ob))
        c_disc = int(np.sum(~oa & ob))
        if mcnemar_exact_p(b_disc, c_disc) < alpha:
            rejects += 1
    return rejects / sims


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def analyze_run(run_name: str) -> None:
    run_dir = RESULTS_RUNS / run_name
    if not (run_dir / "all_rows.jsonl").exists():
        print(f"\n=== {run_name}: no all_rows.jsonl yet (pilot not run) — skipping ===")
        return
    models, blocks, rungs = load_joint_cells(run_dir)
    n_thm = len(blocks)
    n_cells = sum(len(c) for c in blocks.values())
    n_rungs = len(rungs)
    rates = marginal_rates(models, blocks)
    frac_solv = union_solvable_fraction(models, blocks)
    pairs = list(combinations(models, 2))
    n_tests = len(pairs)
    alpha_bonf = ALPHA / n_tests

    print(f"\n{'=' * 78}\n=== {run_name}  ({n_thm} paired theorems, {n_cells} cells, "
          f"{n_rungs} rungs, R=1 pilot) ===\n{'=' * 78}")
    print(f"union-solvable fraction (any model): {frac_solv:.3f}")
    print("per-model pass@1 rate (pilot point estimate):")
    for m in sorted(models, key=lambda m: -rates[m]):
        print(f"    {m:32} {rates[m]:.3f}")
    print(f"\nBonferroni alpha = {ALPHA}/{n_tests} pairs = {alpha_bonf:.4f}; "
          f"power target {POWER_TARGET:.0%}; equivalence band +/-{EQUIV_BAND:.2f}")

    # ---- n_theorems sizing (bootstrap, pass@1) ----------------------------- #
    print(f"\n[1] n_theorems to resolve each pair at pass@1 "
          f"(block bootstrap, {SIMS} sims):")
    header = "    pair" + " " * 44 + "gap   " + "".join(f"{n:>7}" for n in N_THEOREMS_GRID)
    print(header)
    recommend_nthm = {}
    equiv_pairs = []
    for a, b in pairs:
        rng = np.random.default_rng([SEED, _seed_of(a), _seed_of(b)])
        powers, cis = [], []
        for n in N_THEOREMS_GRID:
            pw, lo, hi = bootstrap_power(blocks, a, b, n, alpha=alpha_bonf, sims=SIMS, rng=rng)
            powers.append(pw)
            cis.append((lo, hi))
        gap = rates[a] - rates[b]
        label = f"{a.replace('-base','')} vs {b.replace('-base','')}"
        cells_row = "".join(f"{pw:7.2f}" for pw in powers)
        print(f"    {label:46} {gap:+.3f} {cells_row}")
        # smallest grid n reaching the power target
        hit = next((n for n, pw in zip(N_THEOREMS_GRID, powers) if pw >= POWER_TARGET), None)
        recommend_nthm[(a, b)] = hit
        # equivalence: 90% CI of the gap at the largest grid n inside the band
        lo_big, hi_big = cis[-1]
        if abs(gap) < EQUIV_BAND and hi_big <= EQUIV_BAND and lo_big >= -EQUIV_BAND:
            equiv_pairs.append((a, b, lo_big, hi_big))

    print("\n    per-pair verdict:")
    for a, b in pairs:
        label = f"{a.replace('-base','')} vs {b.replace('-base','')}"
        hit = recommend_nthm[(a, b)]
        if hit is not None:
            print(f"      {label:46} DIFFERENCE — >=80% power at n_theorems={hit}")
        elif any(p[:2] == (a, b) for p in equiv_pairs):
            lo, hi = next((lo, hi) for x, y, lo, hi in equiv_pairs if (x, y) == (a, b))
            print(f"      {label:46} NEAR-TIE — equivalent within [{lo:+.2f},{hi:+.2f}] "
                  f"(band +/-{EQUIV_BAND}) at n_theorems={N_THEOREMS_GRID[-1]}")
        else:
            print(f"      {label:46} UNRESOLVED at n<= {N_THEOREMS_GRID[-1]} "
                  f"(neither >=80% power nor equivalence)")

    # ---- n_rollouts advisory (pass@N mixture) ------------------------------ #
    print(f"\n[2] pass@N advisory at n_theorems={ADVISORY_N_THEOREMS} "
          f"(Beta mixture, {SIMS} sims) — does adding rollouts buy separation?")
    print("    pair" + " " * 44 + "".join(f"  N={n}" for n in N_ROLLOUTS_GRID))
    for a, b in pairs:
        rng = np.random.default_rng([SEED, 7, _seed_of(a), _seed_of(b)])
        row = []
        for nr in N_ROLLOUTS_GRID:
            pw = passn_power(rates[a], rates[b], frac_solv, ADVISORY_N_THEOREMS, nr,
                             n_rungs, alpha=alpha_bonf, sims=SIMS, beta_conc=BETA_CONC, rng=rng)
            row.append(pw)
        label = f"{a.replace('-base','')} vs {b.replace('-base','')}"
        print(f"    {label:46}" + "".join(f"{pw:6.2f}" for pw in row))

    # ---- recommendation ---------------------------------------------------- #
    resolvable = [n for n in recommend_nthm.values() if n is not None]
    rec_nthm = max(resolvable) if resolvable else None
    print("\n    RECOMMENDATION:")
    if rec_nthm is not None:
        print(f"      n_theorems = {rec_nthm} resolves every DIFFERENCE pair at >=80% power "
              f"(pass@1, N=1 rollout).")
    else:
        print(f"      no difference pair reaches 80% power within n<= {N_THEOREMS_GRID[-1]} "
              f"— all pairs are near-ties at this effect size.")
    if equiv_pairs:
        names = ", ".join(f"{a.replace('-base','')}~{b.replace('-base','')}" for a, b, _, _ in equiv_pairs)
        print(f"      near-tie pair(s) [{names}] certified equivalent within +/-{EQUIV_BAND} "
              f"at n_theorems={N_THEOREMS_GRID[-1]} — add rollouts only if [2] shows they separate.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", action="append",
                   help="run-name under results/runs/ (repeatable). "
                        "Default: both lean_moe and lean_arch (the full n=300 runs).")
    args = p.parse_args(argv)
    runs = args.run or list(TRIOS.keys())
    print(f"Lean deduction model-comparison power analysis (seed {SEED}, {SIMS} sims/point)")
    for run_name in runs:
        analyze_run(run_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
