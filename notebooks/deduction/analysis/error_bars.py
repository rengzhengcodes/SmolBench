"""Block-bootstrap error bars for the deduction leg of the family-ladder study.

Reports each of the 21 checkpoints' pass@1 rate with an interval, plus every
pre-registered contrast's paired difference. B is chosen by MEASUREMENT:
``--mode sweep`` measures Monte-Carlo drift across a grid of B.

The resampling unit is a THEOREM BLOCK, not a cell (a cell is one
``(theorem_id, k, prompt_rung)`` triple): the cells of one theorem share a
ground truth and a proof prefix, so whole blocks are drawn with replacement to
keep that correlation -- the standard cluster/block bootstrap (Davison &
Hinkley 1997, ch. 3; Field & Welsh 2007). Effective n is the block count, so
the intervals come out wider than a naive binomial on cells; both figures are
printed. They are BCa (Efron 1987) accelerated by a jackknife over blocks,
shown beside percentile intervals because BCa is what moves materially for the
near-floor lanes; where its bias correction is undefined (only at a degenerate
0.000) the code falls back to percentile and reports the fallback, not a silent
NaN. The PRIMARY p-value uses the same unit: a block SIGN-FLIP permutation test
on per-theorem differences (null: within a theorem, which of the two models
does better is a coin flip), which collapses onto exact McNemar at one cell per
block. Cell-level McNemar stays as a labelled DESCRIPTIVE column; the gap
between the two is clustering.

Denominator rule, COUNT-AS-FAILURE by default: a cell with no surviving
measurable row in one lane scores 0 there exactly when its key is measurable in
another lane -- the operational test for "the fault travelled with this model's
own output". Dropping such cells instead makes denominators model-dependent
(five lanes carry 711 cells, not 712) and rewards breaking the verifier;
``--no-count-as-failure`` restores that drop rule for sensitivity checks. The
232 cells unmeasurable in EVERY lane stay excluded either way. Contrasts run on
the 21-way paired cell set, so all rest on the same cells; pool size, per-lane
denominators and their maximum disagreement are printed, never quoted as
constants.

Row rules are NOT re-implemented here: ``lane_outcomes`` grades through
``power_analysis.grade_verdicts``, the single implementation of
earliest-surviving-row-per-cell and the unmeasurable-verdict exclusion, shared
with ``load_joint_cells`` and ``hint_vs_noise.load_rungs``. This file adds only
the count-as-failure denominator rule and the recovery rows' second schema.

Run:
    uv run --no-project --with numpy --with scipy python \
        notebooks/deduction/analysis/error_bars.py --rows-dir <dir> --mode sweep
    uv run --no-project --with numpy --with scipy python \
        notebooks/deduction/analysis/error_bars.py --rows-dir <dir> --mode report -B 20000
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))

from power_analysis import (  # noqa: E402
    ALPHA,
    FAMILIES,
    MODELS,
    Q_SECONDARY,
    benjamini_hochberg,
    build_cross_family_contrasts,
    build_within_family_contrasts,
    grade_verdicts,
    load_joint_cells,
    mcnemar_exact_p,
    reject_superseded,
    reject_unverified_verdicts,
)

#: Sign-flip resamples for the PRIMARY block permutation test. The resolution
#: floor 1/(B+1) sits two orders of magnitude below Holm's strictest step
#: (0.05/21 = 2.38e-03). No rejection decision is made at the floor.
B_SIGNFLIP = 1_000_000

#: Fixed RNG seed for the permutation test. The report must be byte-reproducible
#: from the same rows. Nothing here draws from entropy.
SIGNFLIP_SEED = 20260821

#: Resample counts swept by ``--mode sweep``. Each count runs on an INDEPENDENT
#: RNG stream. This way the drift between them measures Monte-Carlo error, not
#: a shared seed's luck.
B_GRID = (1_000, 5_000, 20_000, 50_000, 100_000, 200_000, 500_000)

#: Resamples processed per batch. Bounds peak memory at roughly
#: ``CHUNK * n_theorems * n_models * 4`` bytes regardless of B.
CHUNK = 2_000

#: Drift below this (in accuracy points) is smaller than anything the write-up
#: interprets. Rates are reported to 3 decimals, so half a thousandth on an
#: interval endpoint is invisible.
DRIFT_TOL = 0.0005


def holm(pvals: np.ndarray, alpha: float = ALPHA) -> np.ndarray:
    """Compute Holm (1979) step-down rejections at familywise level `alpha`.

    Valid under ARBITRARY dependence, which this family needs: the 21 ladder
    contrasts share cells and models. The sort is STABLE because several
    contrasts sit exactly on the permutation test's ``1/(B+1)`` resolution
    floor, and those ties must not make the rejection mask depend on the order
    the contrasts were built in.
    """
    m = pvals.size
    order = np.argsort(pvals, kind="stable")
    reject = np.zeros(m, dtype=bool)
    for i, idx in enumerate(order):
        if pvals[idx] <= alpha / (m - i):
            reject[idx] = True
        else:
            break
    return reject


def block_matrix(models: list[str], blocks: dict) -> tuple[np.ndarray, np.ndarray]:
    """Flatten `blocks` (from `build_pool`) into per-theorem arrays.

    Returns ``(succ, size)``: ``(n_theorems, n_models)`` successes with columns
    in `models` order, and the ``(n_theorems,)`` cell count per block. The
    bootstrap resamples both together, so a theorem is always drawn whole.
    """
    thms = sorted(blocks)
    succ = np.zeros((len(thms), len(models)), dtype=np.int32)
    size = np.zeros(len(thms), dtype=np.int32)
    for i, thm in enumerate(thms):
        cells = blocks[thm]
        size[i] = len(cells)
        for j, model in enumerate(models):
            succ[i, j] = sum(cellmap[model] for cellmap in cells.values())
    return succ, size


def _bca_bounds(theta_star: np.ndarray, theta_hat: float, jack: np.ndarray,
                alpha: float) -> tuple[float, float, bool]:
    """Compute the BCa interval endpoints for one statistic.

    `jack` holds the jackknife values, one per theorem block; `alpha` is the
    two-sided level (0.05 for a 95% interval). Returns
    ``(lo, hi, used_percentile_fallback)``; the flag is True when the bias
    correction z0 was undefined and a plain percentile interval was used.
    """
    lo_pct, hi_pct = np.percentile(theta_star, [100 * alpha / 2,
                                                100 * (1 - alpha / 2)])
    prop = float(np.mean(theta_star < theta_hat))
    if prop <= 0.0 or prop >= 1.0:
        return float(lo_pct), float(hi_pct), True  # z0 undefined -> percentile
    z0 = norm.ppf(prop)
    jbar = jack.mean()
    num = float(np.sum((jbar - jack) ** 3))
    den = 6.0 * float(np.sum((jbar - jack) ** 2)) ** 1.5
    a = num / den if den > 0 else 0.0
    out = []
    for z in (norm.ppf(alpha / 2), norm.ppf(1 - alpha / 2)):
        adj = z0 + (z0 + z) / (1 - a * (z0 + z))
        out.append(float(np.percentile(theta_star, 100 * norm.cdf(adj))))
    return out[0], out[1], False


def bootstrap_stats(succ: np.ndarray, size: np.ndarray, B: int, seed: int,
                    alpha: float = 0.05) -> dict:
    """Compute block-bootstrap marginal rates and BCa intervals per model.

    One resample draws ``n_theorems`` theorem indices WITH REPLACEMENT (`succ`
    and `size` come from `block_matrix`) and recomputes every model's rate as
    ``sum(successes) / sum(cells)`` over them -- a ratio estimator, since a
    resample's total cell count varies with the draw. `seed` fixes the
    resamples; `alpha` is the two-sided interval level.

    Returns a dict of ``star_rate`` (the ``(B, n_models)`` resampled rate
    matrix, kept so `diff_ci` can pair two models on the SAME theorem draws),
    ``jack`` (``(n_theorems, n_models)`` jackknife rates), ``theta_hat``
    (full-sample rate per model), ``marginal`` (BCa and percentile intervals
    keyed by model index) and ``alpha``.
    """
    n_thm, n_mod = succ.shape
    rng = np.random.default_rng(seed)

    # The loop runs in chunks, so memory stays flat in B. The intermediate
    # ``succ[idx]`` array has shape (chunk, n_thm, n_models). At B = 500k
    # in one shot, that array would need about 90 GB. This is why the loop
    # exists; it is not premature optimisation. Only the final
    # (B, n_models) rate matrix is kept.
    star_rate = np.empty((B, n_mod), dtype=np.float64)
    done = 0
    while done < B:
        chunk = min(CHUNK, B - done)
        idx = rng.integers(0, n_thm, size=(chunk, n_thm))
        star_rate[done:done + chunk] = (
            succ[idx].sum(axis=1) / size[idx].sum(axis=1)[:, None]
        )
        done += chunk

    # Jackknife over theorem blocks for the BCa acceleration.
    tot_succ, tot_size = succ.sum(axis=0), size.sum()
    jack = (tot_succ - succ) / (tot_size - size)[:, None]  # (n_thm, n_models)

    theta_hat = tot_succ / tot_size
    marg = {}
    for j in range(n_mod):
        lo, hi, fb = _bca_bounds(star_rate[:, j], float(theta_hat[j]),
                                 jack[:, j], alpha)
        p_lo, p_hi = np.percentile(star_rate[:, j],
                                   [100 * alpha / 2, 100 * (1 - alpha / 2)])
        marg[j] = dict(rate=float(theta_hat[j]), lo=lo, hi=hi,
                       pct_lo=float(p_lo), pct_hi=float(p_hi),
                       se=float(star_rate[:, j].std(ddof=1)), fallback=fb)
    return dict(star_rate=star_rate, jack=jack, theta_hat=theta_hat,
                marginal=marg, alpha=alpha)


def diff_ci(bs: dict, ja: int, jb: int) -> dict:
    """Compute the BCa interval for the PAIRED difference rate(b) - rate(a).

    The difference is taken INSIDE each resample, cancelling the two models'
    shared theorem draw; that is the point of pairing, and it makes this
    interval much tighter than the two marginals suggest. `bs` is
    `bootstrap_stats` output; `ja`/`jb` index its ``star_rate`` columns for the
    baseline and the comparison model. Returns ``diff`` (full-sample paired
    difference), ``lo``/``hi`` (BCa), ``se`` and ``fallback``.
    """
    star = bs["star_rate"][:, jb] - bs["star_rate"][:, ja]
    hat = float(bs["theta_hat"][jb] - bs["theta_hat"][ja])
    jack = bs["jack"][:, jb] - bs["jack"][:, ja]
    lo, hi, fb = _bca_bounds(star, hat, jack, bs["alpha"])
    return dict(diff=hat, lo=lo, hi=hi, se=float(star.std(ddof=1)), fallback=fb)


def paired_mcnemar(models: list[str], blocks: dict, a: str, b: str) -> tuple:
    """Compute discordant counts and the exact McNemar p over all paired cells.

    Treats each cell as independent, so it is a DESCRIPTIVE column beside the
    PRIMARY block sign-flip test, never used for inference. `blocks` is as built
    by `build_pool`. Returns ``(nb, nc, p)``: cells where `a` succeeds and `b`
    fails, cells where `b` succeeds and `a` fails, and the exact two-sided
    McNemar p-value.
    """
    ia, ib = models.index(a), models.index(b)
    nb = nc = 0
    for cells in blocks.values():
        for cellmap in cells.values():
            va, vb = cellmap[models[ia]], cellmap[models[ib]]
            if va and not vb:
                nb += 1
            elif vb and not va:
                nc += 1
    return nb, nc, mcnemar_exact_p(nb, nc)


def block_signflip_p(succ: np.ndarray, models: list[str], contrasts: list,
                     B: int = B_SIGNFLIP, seed: int = SIGNFLIP_SEED,
                     chunk: int = 2_000) -> np.ndarray:
    """Compute block sign-flip permutation p-values, one per contrast.

    For contrast ``(label, a, b)`` in `contrasts`, let
    ``D_t = successes_b(t) - successes_a(t)`` be the per-THEOREM difference.
    The null is: within a theorem, which of the two models does better is a
    coin flip. Block signs are then exchangeable, so

        p = ( #{ |sum_t eps_t D_t| >= |sum_t D_t| } + 1 ) / (B + 1)

    with eps uniform on ``{-1, +1}^n_theorems``. The ``+1``/``+1`` is the
    standard Monte-Carlo correction keeping the test exact-valid at finite B.
    With one cell per theorem every D_t is 0 or +-1 and the sign-flip
    distribution IS the binomial McNemar conditions on, so this degenerates to
    cell-level exact McNemar. All contrasts are permuted with the SAME eps
    draws, which costs nothing and keeps the family's dependence structure
    intact. `succ` is `block_matrix`'s array with columns in `models` order;
    `chunk` bounds peak memory. Returns one p-value per contrast, in
    `contrasts` order.
    """
    n_thm = succ.shape[0]
    jmap = {m: j for j, m in enumerate(models)}
    diff = np.empty((n_thm, len(contrasts)), dtype=np.float64)
    for ci, (_label, a, b) in enumerate(contrasts):
        diff[:, ci] = succ[:, jmap[b]] - succ[:, jmap[a]]
    observed = np.abs(diff.sum(axis=0))
    rng = np.random.default_rng(seed)
    count = np.zeros(len(contrasts))
    done = 0
    while done < B:
        take = min(chunk, B - done)
        eps = rng.integers(0, 2, size=(take, n_thm)).astype(np.float64) * 2 - 1
        # The comparison uses >= with a tolerance. The observed assignment
        # itself must always count, and these are integer sums carried in
        # float.
        count += (np.abs(eps @ diff) >= observed - 1e-9).sum(axis=0)
        done += take
    return (count + 1) / (B + 1)


def lane_outcomes(rows_dir: Path, model: str, recovery_dir: Path | None = None,
                  ) -> tuple[dict, set]:
    """Grade one lane's cells and collect its no-survivor cells.

    Reads ``<rows_dir>/<model>/verified_rows.jsonl`` and, when `recovery_dir`
    is given, appends ``<recovery_dir>/<model>/recovered_rows.jsonl`` (DojoInit
    recovery) AFTER it -- those rows share the primary schema but carry their
    verdict in ``recovered_verdict``, and only fill holes, never overriding a
    measured cell. Each source is screened by `reject_unverified_verdicts` on
    its OWN verdict field before any row reaches `grade_verdicts`; otherwise a
    generation-time ``"unverified"`` sentinel would grade as a real failure and
    bias this lane's rate invisibly.

    Returns ``(graded, no_survivor)``: ``(theorem_id, k, prompt_rung) -> 0/1``
    under ``power_analysis.grade_verdicts`` (the shared rule where the EARLIEST
    surviving row wins and an unmeasurable verdict is not a measurement), plus
    the cell keys that rule could not grade at all. The latter are returned
    unresolved rather than scored, because only a cross-lane comparison tells a
    model-dependent fault from an unrunnable cell; `build_pool` decides.
    """
    rows: dict = {}
    sources = [(rows_dir / model / "verified_rows.jsonl", "verdict")]
    if recovery_dir is not None:
        sources.append(
            (recovery_dir / model / "recovered_rows.jsonl", "recovered_verdict")
        )
    reject_superseded(path for path, _field in sources)
    for path, field in sources:
        parsed = [json.loads(line) for line in path.read_text().splitlines() if line]
        # Refused HERE, on this source's own field, before any row is
        # graded. See reject_unverified_verdicts for why the field check
        # must run per-source, not always on "verdict".
        reject_unverified_verdicts(parsed, field, path)
        for row in parsed:
            if row.get("kind") != "cell" or row.get("replicate_idx", 0) != 0:
                continue
            key = (row["theorem_id"], row["k"], row["rung"])
            rows.setdefault(key, []).append(row.get(field))
    graded, no_survivor = {}, set()
    for key, verdicts in rows.items():
        grade = grade_verdicts(verdicts)
        if grade is None:
            no_survivor.add(key)
        else:
            graded[key] = grade
    return graded, no_survivor


def build_pool(rows_dir: Path, recovery_dir: Path | None = None,
               count_as_failure: bool = True) -> tuple:
    """Build the paired 21-way pool under an explicit denominator rule.

    `rows_dir` and `recovery_dir` pass through to `lane_outcomes`;
    `count_as_failure` (default True) scores a model-dependent no-survivor cell
    as 0 instead of dropping it (see the module docstring).

    Returns ``(models, blocks, prompt_rungs, meta)``: sorted model names;
    blocks as ``{theorem_id: {(k, prompt_rung): {model: 0 or 1}}}``; the sorted
    distinct prompt rungs present; and `meta`, recording what the denominator
    rule actually did (cells added, per lane, and each lane's own-denominator
    rate) so the report can PRINT the rule's cost instead of asserting it is
    negligible.
    """
    graded, nosurv = {}, {}
    for model in MODELS:
        graded[model], nosurv[model] = lane_outcomes(rows_dir, model, recovery_dir)

    # A no-survivor cell is MODEL-DEPENDENT only when some other lane
    # graded it. The fault then travelled with this model's own output,
    # not with the theorem.
    measurable_somewhere = set().union(*(set(g) for g in graded.values()))
    added: dict[str, set] = {m: set() for m in MODELS}
    if count_as_failure:
        for model in MODELS:
            added[model] = nosurv[model] & measurable_somewhere
            for key in added[model]:
                graded[model][key] = 0

    paired = sorted(set.intersection(*(set(g) for g in graded.values())))
    blocks: dict = {}
    for thm, k, rung in paired:
        blocks.setdefault(thm, {})[(k, rung)] = {
            m: graded[m][(thm, k, rung)] for m in MODELS
        }
    prompt_rungs = sorted({ck[1] for cmap in blocks.values() for ck in cmap})

    # What the denominator rule COST, measured rather than asserted. Every
    # added cell scores 0. A lane's successes stay unchanged, so the whole
    # effect is a larger denominator. The report quotes this cost pooled
    # over the lane, and again over the one prompt rung that absorbed the
    # cell. The rung figure is where the cost bites hardest: a rung is
    # about 1/4 of a lane.
    cost = []
    for model in MODELS:
        for thm, k, rung in sorted(added[model]):
            n_rung = sum(1 for key in graded[model] if key[2] == rung)
            hit_rung = sum(v for key, v in graded[model].items() if key[2] == rung)
            n_lane = len(graded[model])
            hit_lane = sum(graded[model].values())
            cost.append(dict(
                model=model, rung=rung, k=k, theorem=thm,
                pooled_drop=hit_lane / (n_lane - 1), pooled_caf=hit_lane / n_lane,
                rung_drop=hit_rung / (n_rung - 1), rung_caf=hit_rung / n_rung,
                n_lane=n_lane, n_rung=n_rung,
            ))
    meta = dict(
        count_as_failure=count_as_failure,
        recovery=recovery_dir is not None,
        added={m: sorted(v) for m, v in added.items() if v},
        rule_cost=cost,
        n_unresolved={m: len(nosurv[m] - measurable_somewhere) for m in MODELS},
        own_denominator={m: len(graded[m]) for m in MODELS},
        own_rate={m: sum(graded[m].values()) / len(graded[m]) for m in MODELS},
    )
    return sorted(MODELS), blocks, prompt_rungs, meta


def load(rows_dir: Path) -> tuple:
    """Build a back-compatible drop-rule pool (no count-as-failure, no recovery).

    Returns ``(models, blocks, prompt_rungs)`` from
    ``power_analysis.load_joint_cells`` over
    ``<rows_dir>/<model>/verified_rows.jsonl``; raises ``SystemExit`` if any
    model's row file is missing.
    """
    files = [rows_dir / m / "verified_rows.jsonl" for m in MODELS]
    missing = [f for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"missing row files: {[str(f) for f in missing]}")
    return load_joint_cells(files, models=tuple(MODELS))


def mode_sweep(succ: np.ndarray, size: np.ndarray, models: list[str]) -> None:
    """Measure Monte-Carlo drift across B, so B is chosen rather than asserted.

    Runs `bootstrap_stats` at each B in `B_GRID`, on an INDEPENDENT RNG stream
    per B, and prints the interval-endpoint drift against the next larger B.
    `succ`/`size` come from `block_matrix`; `models` matches `succ`'s column
    order.
    """
    print(f"Resample-count sweep -- {succ.shape[0]} theorem blocks, "
          f"{int(size.sum())} cells, {len(models)} models")
    print("Each B runs on an INDEPENDENT RNG stream; drift = max |endpoint "
          "change| vs the\nnext larger B, over all 21 marginal BCa intervals.\n")
    print(f"{'B':>8s} {'max drift (pts)':>16s} {'median drift':>14s} "
          f"{'worst lane':>28s}")
    print("-" * 72)
    prev = None
    for k, B in enumerate(B_GRID):
        bs = bootstrap_stats(succ, size, B, seed=1000 + k)
        cur = np.array([[bs["marginal"][j]["lo"], bs["marginal"][j]["hi"]]
                        for j in range(len(models))])
        if prev is not None:
            d = np.abs(cur - prev)
            worst = models[int(np.argmax(d.max(axis=1)))]
            print(f"{B:8d} {d.max():16.5f} {np.median(d):14.5f} {worst:>28s}")
        else:
            print(f"{B:8d} {'(baseline)':>16s} {'':>14s} {'':>28s}")
        prev = cur
    print(f"\nTolerance: {DRIFT_TOL} pts (rates are reported to 3 decimals, so "
          f"drift below\nhalf a thousandth cannot change a printed figure).")


def mode_report(succ, size, models, blocks, per_lane, B, out_json,
                meta=None, sensitivity=None) -> None:
    """Print the full report and optionally write a JSON summary.

    Prints marginal pass@1 rates with BCa intervals; then every PRIMARY
    (within-family) and SECONDARY (cross-family) contrast with its paired
    difference, block sign-flip p-value, cell-level McNemar p-value and Holm/BH
    rejection; then the design effect versus a naive binomial; then, when
    `sensitivity` is given, the same PRIMARY test under the other denominator
    rules. `succ`/`size` come from `block_matrix` and `models` matches their
    column order; `blocks` (from `build_pool`) feeds the McNemar column.

    `per_lane` maps model name to that lane's rate over its OWN measurable
    denominator (``build_pool``'s ``meta["own_rate"]``), and `meta` is that same
    denominator-rule metadata -- when given, the report prints what the rule
    did. `out_json` is where to write the results dict as JSON, if given.
    `sensitivity` rows are ``(label, n_cells, n_blocks, n_rejected, max_gap)``
    per alternate denominator pool; a row with ``n_cells == 0`` is a plain
    message, printed after the table instead of as a table row.
    """
    bs = bootstrap_stats(succ, size, B, seed=20260816)
    n_thm = succ.shape[0]
    n_cells = int(size.sum())
    meta = meta or {}

    print("=" * 92)
    print("DEDUCTION LEG -- pass@1 with block-bootstrap 95% CIs")
    print("=" * 92)
    print(f"Resampling unit: THEOREM BLOCK. n = {n_thm} blocks "
          f"({n_cells} cells, {n_cells / n_thm:.1f} cells per block).")
    print(f"B = {B:,} resamples, BCa intervals (percentile shown for contrast).")
    print(f"The effective sample size is {n_thm} THEOREMS, not {n_cells} cells "
          f"-- see the module docstring.")
    if meta:
        rule = ("COUNT-AS-FAILURE (default)"
                if meta["count_as_failure"] else "DROP unmeasurable (legacy)")
        n_added = sum(len(v) for v in meta["added"].values())
        print(f"Denominator rule: {rule}.", end=" ")
        if meta["count_as_failure"]:
            print(f"{n_added} model-dependent no-survivor cell(s) scored 0, in "
                  f"{len(meta['added'])} lane(s).")
            print(f"  {'lane':28s} {'rung':9s} {'k':>3s}  "
                  f"{'pooled pt':>10s} {'rung pt':>8s}  theorem")
            for c in sorted(meta["rule_cost"],
                            key=lambda c: c["rung_caf"] - c["rung_drop"]):
                print(f"  {c['model']:28s} {c['rung']:9s} {c['k']:3d}  "
                      f"{100 * (c['pooled_caf'] - c['pooled_drop']):+10.3f} "
                      f"{100 * (c['rung_caf'] - c['rung_drop']):+8.3f}  "
                      f"{c['theorem']}")
            if meta["rule_cost"]:
                worst_p = min(c["pooled_caf"] - c["pooled_drop"]
                              for c in meta["rule_cost"])
                worst_r = min(c["rung_caf"] - c["rung_drop"]
                              for c in meta["rule_cost"])
                print(f"  Cost of the rule: at most {100 * worst_p:.3f} "
                      f"accuracy points pooled over a lane and\n  "
                      f"{100 * worst_r:.3f} over a single prompt rung. Successes "
                      f"are unchanged; only the\n  denominator moves, and it "
                      f"moves to the SAME value in all 21 lanes.")
        else:
            print("no-survivor cells dropped, so per-lane denominators "
                  "diverge.")
        if meta["recovery"]:
            print("  DojoInit recovery rows POOLED IN -- a SENSITIVITY "
                  "configuration. The headline\n  figures are Mathlib-only.")
    print()

    print(f"{'model':30s} {'pass@1':>7s} {'95% BCa':>17s} {'width':>7s} "
          f"{'percentile':>17s} {'own-lane':>9s}")
    print("-" * 92)
    order = [m for fam in FAMILIES.values() for m in fam]
    for m in order:
        j = models.index(m)
        r = bs["marginal"][j]
        flag = " *pct" if r["fallback"] else ""
        print(f"{m:30s} {r['rate']:7.3f} [{r['lo']:.3f}, {r['hi']:.3f}] "
              f"{r['hi'] - r['lo']:7.3f} [{r['pct_lo']:.3f}, {r['pct_hi']:.3f}] "
              f"{per_lane.get(m, float('nan')):9.3f}{flag}")
    if meta:
        gaps = {m: abs(per_lane[m] - bs["marginal"][models.index(m)]["rate"])
                for m in order if m in per_lane}
        worst = max(gaps, key=gaps.get)
        denoms = sorted({meta["own_denominator"][m] for m in order})
        print(f"\nown-lane = each lane's rate over its OWN measurable "
              f"denominator ("
              f"{'/'.join(str(d) for d in denoms)} cells).\n  Max |own-lane - "
              f"paired| = {gaps[worst]:.4f} ({worst}); at the 3 decimals "
              f"printed that reads as\n  {gaps[worst]:.3f}.")

    naive = np.sqrt(bs["theta_hat"] * (1 - bs["theta_hat"]) / n_cells) * 1.96 * 2
    boot_w = np.array([bs["marginal"][j]["hi"] - bs["marginal"][j]["lo"]
                       for j in range(len(models))])
    print(f"\nDesign effect: block-bootstrap intervals are "
          f"{np.median(boot_w / naive):.2f}x (median) the width a naive binomial "
          f"on {n_cells}\n  independent cells would give -- range "
          f"{np.min(boot_w / naive):.2f}x to {np.max(boot_w / naive):.2f}x. "
          f"Treating cells as independent\n  would overstate precision by that "
          f"factor.")

    results = {"n_theorem_blocks": n_thm, "n_cells": n_cells, "B": B,
               "marginals": {m: bs["marginal"][models.index(m)] for m in models},
               "contrasts": {}}

    for tier, contrasts, corrected in (
        ("PRIMARY -- within-family ladder", build_within_family_contrasts(), True),
        ("SECONDARY -- cross-family, size-matched", build_cross_family_contrasts(), False),
    ):
        p_block = block_signflip_p(succ, models, contrasts)
        rows = []
        for i, (label, a, b) in enumerate(contrasts):
            ci = diff_ci(bs, models.index(a), models.index(b))
            nb, nc, p_cell = paired_mcnemar(models, blocks, a, b)
            rows.append((label, a, b, ci, nb, nc, float(p_block[i]), p_cell))
        pv = np.array([r[6] for r in rows])          # PRIMARY inference
        pv_cell = np.array([r[7] for r in rows])     # descriptive
        # PRIMARY gets Holm (FWER, arbitrary dependence); SECONDARY gets the
        # pre-registered Benjamini-Hochberg FDR at q = 0.05, because it is an
        # exploratory tier. Running BH here rather than in a throwaway script
        # is the point: every number in the report must come out of this file.
        rej = holm(pv) if corrected else benjamini_hochberg(pv, Q_SECONDARY)
        rej_cell = holm(pv_cell) if corrected else benjamini_hochberg(pv_cell,
                                                                     Q_SECONDARY)

        proc = "Holm" if corrected else "BH"
        print(f"\n{'=' * 92}\n{tier}: {len(rows)} contrasts\n{'=' * 92}")
        print(f"PRIMARY p = BLOCK SIGN-FLIP permutation over the {n_thm} theorem "
              f"blocks,\n  B = {B_SIGNFLIP:,} draws, fixed seed "
              f"{SIGNFLIP_SEED} (resolution floor {1 / (B_SIGNFLIP + 1):.1e}). "
              f"Cell-level\n  exact McNemar is shown beside it as a DESCRIPTIVE "
              f"figure -- it assumes the "
              f"{n_cells}\n  cells are independent, which is the assumption "
              f"every interval on this page rejects.")
        if corrected:
            print("Holm-Bonferroni at FWER 0.05 over these 21 (arbitrary "
                  "dependence).\n")
        else:
            print(f"Benjamini-Hochberg FDR at q = {Q_SECONDARY} over these "
                  f"{len(rows)} (pre-registered:\nexploratory tier, so FDR "
                  f"rather than FWER).\n")
        print(f"{'contrast':46s} {'diff':>7s} {'95% BCa':>17s} {'b/c':>10s} "
              f"{'p_block':>9s} {'p_cell':>9s} {proc:>5s}")
        print("-" * 110)
        for (label, a, b, ci, nb, nc, p, p_cell), ok in zip(rows, rej):
            mark = " yes " if ok else "  .  "
            crosses = "" if (ci["lo"] > 0 or ci["hi"] < 0) else "  (CI spans 0)"
            short = label if len(label) <= 46 else label[:43] + "..."
            print(f"{short:46s} {ci['diff']:+7.3f} [{ci['lo']:+.3f}, "
                  f"{ci['hi']:+.3f}] {nb:4d}/{nc:<5d} {p:9.2e} {p_cell:9.2e} "
                  f"{mark}{crosses}")
            results["contrasts"][label] = dict(
                model_a=a, model_b=b, **ci, b=nb, c=nc, p=p, p_cell=p_cell,
                holm=bool(ok))

        agree = sum(1 for (_, _, _, ci, _, _, _, _), ok in zip(rows, rej)
                    if ok == (ci["lo"] > 0 or ci["hi"] < 0))
        print(f"\n{proc} rejects {int(rej.sum())} of {len(rows)}; "
              f"uncorrected p<{ALPHA} would be {int((pv < ALPHA).sum())}; "
              f"CIs excluding 0: "
              f"{sum(1 for r in rows if r[3]['lo'] > 0 or r[3]['hi'] < 0)}.")
        print(f"  On the SAME cells, cell-level McNemar + {proc} would reject "
              f"{int(rej_cell.sum())}. The\n  difference is entirely "
              f"clustering: cells inside a theorem share a ground truth and\n"
              f"  a proof prefix, so treating them as independent overstates the "
              f"evidence.")
        lost = [rows[i][0] for i in range(len(rows)) if rej_cell[i] and not rej[i]]
        for label in lost:
            print(f"    only under the cell-level test: {label}")
        print(f"  {proc} and the uncorrected CI agree on {agree}/{len(rows)}. "
              f"They are DIFFERENT questions: the CI is\n  uncorrected and "
              f"two-sided per contrast; {proc} controls error over the whole "
              f"tier.")

        if corrected:
            print("\nPer-family ladder verdict (a family 'scales cleanly' only "
                  "if all three\nrung-pairs are positive AND significant):")
            for family, ladder in FAMILIES.items():
                idx = [i for i, r in enumerate(rows)
                       if r[1] in ladder and r[2] in ladder]
                n_sig = sum(1 for i in idx if rej[i])
                n_pos = sum(1 for i in idx if rows[i][3]["diff"] > 0)
                clean = "CLEAN" if (n_sig == 3 and n_pos == 3) else "no"
                print(f"  {family:12s} {n_sig}/3 significant, {n_pos}/3 "
                      f"positive  -> {clean}")

    if sensitivity:
        print(f"\n{'=' * 92}\nSENSITIVITY -- the same PRIMARY test under other "
              f"denominator rules\n{'=' * 92}")
        print("Each row re-pools the cells and re-runs the block sign-flip test "
              "from scratch.\nRe-pooling the DojoInit recovery rows is a "
              "sensitivity only: the headline figures\nare Mathlib-only.\n")
        print(f"{'pool':46s} {'cells':>7s} {'blocks':>7s} {'Holm':>6s} "
              f"{'max own-vs-paired':>18s}")
        print("-" * 90)
        for label, n_c, n_b, n_rej, gap in sensitivity:
            if n_c == 0:
                continue
            print(f"{label:46s} {n_c:7d} {n_b:7d} {n_rej:5d}/21 {gap:18.4f}")
        print("\nmax own-vs-paired = largest gap between a lane's rate over its "
              "own denominator and\n  its rate on the 21-way paired pool. It is "
              "exactly 0 under count-as-failure,\n  because that rule gives "
              "every lane the same denominator as the pool.")
        for label, n_c, _n_b, _n_rej, _gap in sensitivity:
            if n_c == 0:
                print(f"\n{label}")

    if out_json:
        Path(out_json).write_text(json.dumps(results, indent=2, default=float))
        print(f"\nwrote {out_json}")


def main(argv=None) -> int:
    """Parse arguments, build the pool, and run the requested mode.

    Returns the process exit code (0 on success); raises ``SystemExit`` if any
    model's ``verified_rows.jsonl`` is missing.
    """
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows-dir", type=Path, required=True,
                    help="directory of <model>/verified_rows.jsonl")
    ap.add_argument("--mode", choices=("sweep", "report"), default="report")
    ap.add_argument("-B", type=int, default=20_000)
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--recovery-dir", type=Path, default=None,
                    help="directory of <model>/recovered_rows.jsonl (DojoInit "
                         "recovery). Pooled into the SENSITIVITY rows, never "
                         "into the headline pool.")
    ap.add_argument("--no-count-as-failure", dest="count_as_failure",
                    action="store_false",
                    help="revert to the legacy rule that DROPS model-dependent "
                         "no-survivor cells (five lanes then carry 711 cells)")
    ap.set_defaults(count_as_failure=True)
    args = ap.parse_args(argv)

    missing = [args.rows_dir / m / "verified_rows.jsonl" for m in MODELS]
    missing = [f for f in missing if not f.exists()]
    if missing:
        raise SystemExit(f"missing row files: {[str(f) for f in missing]}")

    models, blocks, rungs, meta = build_pool(
        args.rows_dir, count_as_failure=args.count_as_failure)
    succ, size = block_matrix(models, blocks)
    per_lane = dict(meta["own_rate"])

    if args.mode == "sweep":
        mode_sweep(succ, size, models)
        return 0

    # Sensitivity pools: the same PRIMARY test under the other denominator
    # rules. This lets the reader attribute a change to the rule, rather
    # than guess. The script computes this here; it does not assert it.
    sensitivity = []
    for caf in (True, False):
        for rec in ([None] + ([args.recovery_dir] if args.recovery_dir else [])):
            if caf == args.count_as_failure and rec is None:
                continue
            _m, _b, _r, _meta = build_pool(args.rows_dir, recovery_dir=rec,
                                           count_as_failure=caf)
            _succ, _size = block_matrix(_m, _b)
            p = block_signflip_p(_succ, _m, build_within_family_contrasts())
            paired = _succ.sum(axis=0) / _size.sum()
            gap = max(abs(paired[_m.index(mm)] - _meta["own_rate"][mm])
                      for mm in MODELS)
            label = ("count-as-failure" if caf else "drop no-survivor")
            label += " + DojoInit recovery" if rec else " (Mathlib only)"
            sensitivity.append((label, int(_size.sum()), _succ.shape[0],
                                int(holm(p).sum()), gap))
    if args.recovery_dir is None:
        sensitivity.append((
            "Post-recovery pools are NOT shown: pass --recovery-dir "
            "<dir-of-<model>/recovered_rows.jsonl>\n(e.g. "
            "notebooks/deduction/results/dojoinit_recovery_2026-08-18) to add "
            "them.", 0, 0, 0, 0.0))

    mode_report(succ, size, models, blocks, per_lane, args.B, args.out_json,
                meta=meta, sensitivity=sensitivity)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
