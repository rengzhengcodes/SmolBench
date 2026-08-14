"""Monte Carlo study of TEST and CORRECTION choice for the periodic-induction
family-ladder scaling study (21 models x 4 info arms, R=30 replicates x 9 harmonics).

Self-contained. Run with:
  uv run --no-project --with numpy --with scipy python multiplicity_sim.py

Every statistic below is simulated; nothing is analytic-approximated for reporting.
The pairwise test is byte-for-byte the repo's continuity-corrected 2x2xK CMH
(notebooks/induction/power_analysis.py::cmh_reject) and the 2-df general-association
statistic mirrors that file's gcmh_reject.
"""

from __future__ import annotations

import json
import time

import numpy as np
from scipy.stats import binom, chi2

# ----------------------------------------------------------------------------- design
R_DEFAULT = 30          # replicates (seeds 0..29)
K_HARM = 9              # harmonics k = 1..9  -> CMH strata for pairwise tests
N_PRIMARY = 210
ALPHA = 0.05
ALPHA_BONF = ALPHA / N_PRIMARY          # 2.381e-4
OUT = {}
SCRATCH = "/tmp/claude-1001/-workspace-SmolBench/54dbdffb-0485-4ced-9231-fa52049df286/scratchpad"


def dump(tag: str) -> None:
    with open(f"{SCRATCH}/multiplicity_sim_results.json", "w") as fh:
        json.dump(OUT, fh, indent=2, default=float)
    print(f"[checkpoint written after {tag}]", flush=True)


# ------------------------------------------------------------------------- statistics
def cmh_stat(succ_a: np.ndarray, succ_b: np.ndarray, n: int) -> np.ndarray:
    """Repo's continuity-corrected 2x2xK CMH statistic (chi2, df=1)."""
    big_n = 2 * n
    m1 = succ_a + succ_b
    m0 = big_n - m1
    expect = m1 * n / big_n
    var = (n * n * m1 * m0) / (big_n * big_n * (big_n - 1))
    num = np.abs((succ_a - expect).sum(axis=-1)) - 0.5
    num = np.clip(num, 0.0, None) ** 2
    denom = var.sum(axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(denom > 0, num / denom, 0.0)


def cmh_p(succ_a: np.ndarray, succ_b: np.ndarray, n: int) -> np.ndarray:
    return chi2.sf(cmh_stat(succ_a, succ_b, n), df=1)


def gcmh_stat(succ: np.ndarray, n: int) -> np.ndarray:
    """Generalized CMH 'general association', 3 rungs -> df=2. succ: (..., 3, K)."""
    n_rungs = succ.shape[-2]
    total_n = float(n_rungs * n)
    total_succ = succ.sum(axis=-2)                       # (..., K)
    resid = succ - (total_succ / n_rungs)[..., None, :]
    t_vec = resid[..., :2, :].sum(axis=-1)               # (..., 2)
    p = n / total_n
    common = total_succ * (total_n - total_succ) / (total_n - 1.0)
    shape = np.full((2, 2), -p * p)
    np.fill_diagonal(shape, p * (1.0 - p))
    w = common.sum(axis=-1)
    sigma = w[..., None, None] * shape
    sigma_inv = np.linalg.pinv(sigma)
    return np.einsum("...d,...de,...e->...", t_vec, sigma_inv, t_vec)


def trend_stat(succ: np.ndarray, n: int, scores=(1.0, 2.0, 3.0)) -> np.ndarray:
    """1-df CMH correlation (linear trend) statistic. succ: (..., 3, K)."""
    x = np.asarray(scores)
    n_rungs = succ.shape[-2]
    total_n = float(n_rungs * n)
    m = succ.sum(axis=-2)                                 # (..., K) successes
    t = (succ * x[:, None]).sum(axis=(-2, -1))            # observed
    sum_nx = n * x.sum()
    sum_nx2 = n * (x ** 2).sum()
    e_j = sum_nx * m / total_n
    v_j = (m * (total_n - m) / (total_n ** 2 * (total_n - 1.0))) * (
        total_n * sum_nx2 - sum_nx ** 2
    )
    e = e_j.sum(axis=-1)
    v = v_j.sum(axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(v > 0, (t - e) ** 2 / v, 0.0)


def mcnemar_exact_p(b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Two-sided exact conditional (binomial) McNemar p-value."""
    nd = b + c
    lo = np.minimum(b, c)
    p = 2.0 * binom.cdf(lo, np.maximum(nd, 1), 0.5)
    p = np.clip(p, 0.0, 1.0)
    return np.where(nd == 0, 1.0, p)


def paired_marks(p_a: float, p_b: float, rho: float, n_sims: int, reps: int,
                 rng: np.random.Generator):
    """Latent-bivariate-normal (tetrachoric rho) matched marks. -> (S, reps, K) bools."""
    z1 = rng.standard_normal((n_sims, reps, K_HARM), dtype=np.float32)
    z2 = rng.standard_normal((n_sims, reps, K_HARM), dtype=np.float32)
    zb = rho * z1 + np.sqrt(max(1.0 - rho * rho, 0.0)) * z2
    from scipy.stats import norm
    return z1 < norm.ppf(p_a), zb < norm.ppf(p_b)


# =============================================================== PART 1: ceiling headroom
def part1(rng: np.random.Generator, n_sims: int = 20000, step: float = 0.0025):
    print("\n=== PART 1: minimum detectable difference (80% power) ===", flush=True)
    rows = []
    for p_a in (0.99, 0.97, 0.95, 0.90, 0.70, 0.50):
        found = {}
        d = step
        while d <= min(p_a, 0.60) + 1e-9 and len(found) < 2:
            p_b = p_a - d
            sa = rng.binomial(R_DEFAULT, p_a, (n_sims, K_HARM))
            sb = rng.binomial(R_DEFAULT, p_b, (n_sims, K_HARM))
            st = cmh_stat(sa, sb, R_DEFAULT)
            for a_lab, a in (("bonf", ALPHA_BONF), ("naive", ALPHA)):
                if a_lab not in found:
                    pw = (st > chi2.isf(a, df=1)).mean()
                    if pw >= 0.80:
                        found[a_lab] = (round(d, 4), float(pw))
            d += step
        row = dict(p_a=p_a,
                   mdd_bonf=found.get("bonf", (None, None))[0],
                   pow_bonf=found.get("bonf", (None, None))[1],
                   mdd_naive=found.get("naive", (None, None))[0],
                   pow_naive=found.get("naive", (None, None))[1])
        row["ratio"] = (row["mdd_bonf"] / row["mdd_naive"]
                        if row["mdd_bonf"] and row["mdd_naive"] else None)
        rows.append(row)
        print(f"  p_A={p_a:.2f}  MDD(alpha=2.38e-4)={row['mdd_bonf']}  "
              f"MDD(alpha=0.05)={row['mdd_naive']}  ratio={row['ratio']}", flush=True)
    OUT["part1"] = dict(n_sims=n_sims, grid_step=step, rows=rows)


# ======================================================= PART 3: clustering / Type I error
def part3(rng: np.random.Generator, n_sims: int = 200000, chunk: int = 20000):
    print("\n=== PART 3: within-replicate clustering -> actual Type I error ===", flush=True)
    from scipy.stats import norm
    crit05 = chi2.isf(ALPHA, df=1)
    critb = chi2.isf(ALPHA_BONF, df=1)
    rows = []
    for p in (0.90, 0.70):
        for icc in (0.0, 0.1, 0.2, 0.4):
            for variant in ("independent", "shared"):
                if p == 0.70 and variant == "shared":
                    continue
                thr = norm.ppf(p)
                r05 = rb = 0
                done = 0
                phis = []
                while done < n_sims:
                    s = min(chunk, n_sims - done)
                    u_a = rng.standard_normal((s, R_DEFAULT, 1), dtype=np.float32)
                    u_b = (u_a if variant == "shared"
                           else rng.standard_normal((s, R_DEFAULT, 1), dtype=np.float32))
                    ea = rng.standard_normal((s, R_DEFAULT, K_HARM), dtype=np.float32)
                    eb = rng.standard_normal((s, R_DEFAULT, K_HARM), dtype=np.float32)
                    w1, w2 = np.sqrt(icc), np.sqrt(1.0 - icc)
                    ma = (w1 * u_a + w2 * ea) < thr
                    mb = (w1 * u_b + w2 * eb) < thr
                    if len(phis) < 3:            # empirical binary within-replicate corr
                        x = ma.astype(np.float64)
                        mu = x.mean()
                        cx = x - mu
                        # mean over k<k' of E[cx_k cx_k'] / var
                        ssum = cx.sum(axis=2)
                        cross = (ssum ** 2 - (cx ** 2).sum(axis=2)).mean() / (
                            K_HARM * (K_HARM - 1))
                        phis.append(cross / (mu * (1 - mu)))
                    sa = ma.sum(axis=1)
                    sb = mb.sum(axis=1)
                    st = cmh_stat(sa, sb, R_DEFAULT)
                    r05 += int((st > crit05).sum())
                    rb += int((st > critb).sum())
                    done += s
                row = dict(p=p, icc=icc, variant=variant,
                           phi_binary=float(np.mean(phis)),
                           t1_alpha05=r05 / n_sims, t1_alpha_bonf=rb / n_sims,
                           infl05=(r05 / n_sims) / ALPHA,
                           inflb=(rb / n_sims) / ALPHA_BONF, n_sims=n_sims)
                rows.append(row)
                print(f"  p={p} icc={icc} {variant:11s} phi_bin={row['phi_binary']:.3f} "
                      f"T1@0.05={row['t1_alpha05']:.4f} ({row['infl05']:.2f}x)  "
                      f"T1@2.38e-4={row['t1_alpha_bonf']:.6f} ({row['inflb']:.2f}x)",
                      flush=True)
    OUT["part3"] = dict(rows=rows)


# ============================================================ PART 5: trend vs pairwise
def part5(rng: np.random.Generator, n_sims: int = 20000):
    print("\n=== PART 5: 1-df trend vs 2-df omnibus vs 3 pairwise ===", flush=True)
    alpha_fam_trend = ALPHA / 28          # 28 one-df trend tests
    alpha_pair = ALPHA_BONF               # pairwise inside the 210 family
    rows = []
    for label, rates in (("monotone 0.60/0.75/0.88", (0.60, 0.75, 0.88)),
                         ("non-monotone 0.60/0.88/0.75", (0.60, 0.88, 0.75)),
                         ("monotone-small 0.60/0.66/0.72", (0.60, 0.66, 0.72)),
                         ("non-monotone-small 0.60/0.72/0.66", (0.60, 0.72, 0.66)),
                         ("monotone-ceiling 0.99/0.96/0.93", (0.99, 0.96, 0.93)),
                         ("non-monotone-ceiling 0.99/0.93/0.96", (0.99, 0.93, 0.96))):
        succ = np.stack([rng.binomial(R_DEFAULT, r, (n_sims, K_HARM)) for r in rates],
                        axis=1)
        tr = trend_stat(succ, R_DEFAULT)
        gc = gcmh_stat(succ, R_DEFAULT)
        pair_stats = [cmh_stat(succ[:, i, :], succ[:, j, :], R_DEFAULT)
                      for i, j in ((0, 1), (1, 2), (0, 2))]
        res = dict(label=label, rates=rates)
        # study-wide alphas (pre-registered)
        res["trend_studywide"] = float((tr > chi2.isf(alpha_fam_trend, 1)).mean())
        res["gcmh_studywide"] = float((gc > chi2.isf(ALPHA / 7, 2)).mean())
        res["pairwise_any_studywide"] = float(
            np.any([s > chi2.isf(alpha_pair, 1) for s in pair_stats], axis=0).mean())
        # local, uncorrected-family alphas (test choice isolated from correction)
        res["trend_local05"] = float((tr > chi2.isf(ALPHA, 1)).mean())
        res["gcmh_local05"] = float((gc > chi2.isf(ALPHA, 2)).mean())
        res["pairwise_any_local"] = float(
            np.any([s > chi2.isf(ALPHA / 3, 1) for s in pair_stats], axis=0).mean())
        rows.append(res)
        print(f"  {label}", flush=True)
        print(f"    study-wide: trend={res['trend_studywide']:.4f} "
              f"gcmh(2df)={res['gcmh_studywide']:.4f} "
              f"any-pairwise={res['pairwise_any_studywide']:.4f}", flush=True)
        print(f"    local a=.05: trend={res['trend_local05']:.4f} "
              f"gcmh={res['gcmh_local05']:.4f} any-pairwise={res['pairwise_any_local']:.4f}",
              flush=True)
    OUT["part5"] = dict(rows=rows, n_sims=n_sims,
                        alpha_trend_studywide=alpha_fam_trend,
                        alpha_pairwise=ALPHA_BONF, alpha_gcmh=ALPHA / 7)


# ================================================================== PART 2: pairing gain
def _paired_powers(p_a, delta, rho, reps, n_sims, rng):
    """Return (power_unpaired_CMH, power_exact_McNemar) on the SAME simulated marks."""
    p_b = p_a - delta
    ma, mb = paired_marks(p_a, p_b, rho, n_sims, reps, rng)
    sa = ma.sum(axis=1)
    sb = mb.sum(axis=1)
    unp = (cmh_stat(sa, sb, reps) > chi2.isf(ALPHA_BONF, 1)).mean()
    b = (ma & ~mb).sum(axis=(1, 2))
    c = (~ma & mb).sum(axis=(1, 2))
    pv = mcnemar_exact_p(b, c)
    # realized BINARY (phi) correlation between the two arms' marks, and agreement
    xa, xb = ma.astype(np.float64), mb.astype(np.float64)
    va, vb = xa.mean() * (1 - xa.mean()), xb.mean() * (1 - xb.mean())
    phi = ((xa * xb).mean() - xa.mean() * xb.mean()) / np.sqrt(max(va * vb, 1e-12))
    agree = float((ma == mb).mean())
    return float(unp), float((pv < ALPHA_BONF).mean()), float(phi), agree


def part2(rng, n_sims=20000, search_sims=8000, cap=900):
    print("\n=== PART 2: pairing gain (matched items) ===", flush=True)
    rows = []
    grid_r = [30, 35, 40, 45, 50, 60, 70, 85, 100, 120, 145, 175, 210, 250, 300, 360,
              430, 520, 620, 750, 900]
    for p_a in (0.95, 0.70):
        for delta in (0.05, 0.10):
            for rho in (0.0, 0.3, 0.5, 0.7, 0.9):
                if p_a == 0.70 and rho not in (0.5, 0.7):
                    continue
                unp, pair, phi, agree = _paired_powers(p_a, delta, rho, R_DEFAULT,
                                                       n_sims, rng)
                # equivalent R: smallest R at which the UNPAIRED test matches the
                # paired test's R=30 power (paired data throughout).
                eq_r = None
                if pair > unp + 0.005:
                    for rr in grid_r:
                        u2 = _paired_powers(p_a, delta, rho, rr, search_sims, rng)[0]
                        if u2 >= pair:
                            eq_r = rr
                            break
                else:
                    eq_r = 30
                rows.append(dict(p_a=p_a, delta=delta, rho=rho, power_unpaired=unp,
                                 power_paired=pair, eq_R=eq_r, cap=cap,
                                 phi_binary=phi, agreement=agree,
                                 eq_ratio=(None if eq_r is None else eq_r / 30.0)))
                print(f"  p_A={p_a} d={delta} rho={rho}: phi_bin={phi:.3f} "
                      f"agree={agree:.3f} unpaired={unp:.4f} "
                      f"paired={pair:.4f} eqR={eq_r}", flush=True)
    # null calibration of both tests under matched data (rho=0.5)
    nulls = {}
    for rho in (0.0, 0.5, 0.9):
        u, p = _paired_powers(0.90, 0.0, rho, R_DEFAULT, 60000, rng)[:2]
        nulls[rho] = dict(unpaired_t1=u, mcnemar_t1=p)
        print(f"  NULL rho={rho}: unpaired T1={u:.6f} mcnemar T1={p:.6f}", flush=True)
    OUT["part2"] = dict(rows=rows, n_sims=n_sims, nulls=nulls,
                        alpha=ALPHA_BONF, grid_r=grid_r)


# ============================================================== PART 4: correction cost
def build_rate_matrix():
    """21 models (7 families x 3 rungs) x 4 infos. Stylized per the brief:
    a spread of true effects near ceiling and mid-range, the rest exact nulls."""
    rates = np.zeros((7, 3, 4))
    flat = [0.99, 0.97, 0.95, 0.92, 0.85, 0.75, 0.62]
    for f in range(7):
        rates[f, :, :] = flat[f]
    # F0: near-ceiling WHOLE-MODEL ladder (all 4 arms shift together)
    #     -> 4 infos x 3 rung-pairs = 12 true ladder contrasts, 0 true info contrasts
    for i in range(4):
        rates[0, :, i] = [0.99, 0.96, 0.925]
    # F1: upper-mid ladder on extens only -> 3 ladder + 6 info = 9 true
    rates[1, :, 1] = [0.97, 0.91, 0.83]
    # F2: mid-range ladder on extens only -> 3 ladder + 6 info = 9 true
    rates[2, :, 1] = [0.95, 0.86, 0.74]
    # total = 12 + 9 + 9 = 30 true effects, 180 exact nulls (per the brief)
    return rates


def apply_corrections(pv: np.ndarray, is_null: np.ndarray, m: int):
    """pv: (S, m). Returns dict of procedure -> (rej bool (S,m))."""
    out = {}
    order = np.argsort(pv, axis=1)
    sortedp = np.take_along_axis(pv, order, axis=1)
    ranks = np.arange(1, m + 1)
    # Bonferroni
    out["Bonferroni"] = pv < ALPHA / m
    # Holm (step-down)
    thr = ALPHA / (m - ranks + 1)
    viol = sortedp > thr
    first = np.where(viol.any(axis=1), viol.argmax(axis=1), m)
    keep = np.arange(m)[None, :] < first[:, None]
    rej_sorted = keep
    rej = np.zeros_like(pv, dtype=bool)
    np.put_along_axis(rej, order, rej_sorted, axis=1)
    out["Holm"] = rej
    # Hochberg (step-up, alpha/(m-i+1))
    ok = sortedp <= thr
    idx = np.where(ok.any(axis=1), m - 1 - ok[:, ::-1].argmax(axis=1), -1)
    keep = np.arange(m)[None, :] <= idx[:, None]
    rej = np.zeros_like(pv, dtype=bool)
    np.put_along_axis(rej, order, keep, axis=1)
    out["Hochberg"] = rej
    # BH
    bh_thr = ALPHA * ranks / m
    ok = sortedp <= bh_thr
    idx = np.where(ok.any(axis=1), m - 1 - ok[:, ::-1].argmax(axis=1), -1)
    keep = np.arange(m)[None, :] <= idx[:, None]
    rej = np.zeros_like(pv, dtype=bool)
    np.put_along_axis(rej, order, keep, axis=1)
    out["BH(q=0.05)"] = rej
    return out


def part4(rng, n_sims=4000):
    print("\n=== PART 4: correction cost ===", flush=True)
    rates = build_rate_matrix()
    lad_idx, info_idx, ladder_of_pair = [], [], []
    for f in range(7):
        for i in range(4):
            for a, b in ((0, 1), (1, 2), (0, 2)):
                lad_idx.append((f, a, i, f, b, i))
                ladder_of_pair.append(f * 4 + i)
    for f in range(7):
        for r in range(3):
            for a, b in ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)):
                info_idx.append((f, r, a, f, r, b))
    contrasts = lad_idx + info_idx
    m_full = len(contrasts)
    assert m_full == 210, m_full
    # truth
    true_diff = np.array([abs(rates[c[0], c[1], c[2]] - rates[c[3], c[4], c[5]])
                          for c in contrasts])
    is_null = true_diff == 0.0
    n_true = int((~is_null).sum())
    # trend-family truth: ladder non-flat (all 28 ladders)
    ladder_rates = np.array([[rates[f, r, i] for r in range(3)]
                             for f in range(7) for i in range(4)])
    ladder_nonflat = ~np.all(ladder_rates == ladder_rates[:, :1], axis=1)
    print(f"  config: {n_true} true effects / {int(is_null.sum())} true nulls; "
          f"non-flat ladders = {int(ladder_nonflat.sum())}/28", flush=True)
    print(f"  true-effect deltas: {np.sort(true_diff[~is_null])}", flush=True)

    # simulate
    succ = np.empty((n_sims, 7, 3, 4, K_HARM), dtype=np.int32)
    for f in range(7):
        for r in range(3):
            for i in range(4):
                succ[:, f, r, i, :] = rng.binomial(R_DEFAULT, rates[f, r, i],
                                                   (n_sims, K_HARM))
    pv = np.empty((n_sims, m_full))
    for t, c in enumerate(contrasts):
        pv[:, t] = cmh_p(succ[:, c[0], c[1], c[2], :], succ[:, c[3], c[4], c[5], :],
                         R_DEFAULT)
    # reduced family: 28 trend tests + 126 info contrasts
    trend_p = np.empty((n_sims, 28))
    t = 0
    for f in range(7):
        for i in range(4):
            trend_p[:, t] = chi2.sf(trend_stat(succ[:, f, :, i, :], R_DEFAULT), df=1)
            t += 1
    pv_red = np.concatenate([trend_p, pv[:, 84:]], axis=1)
    null_red = np.concatenate([~ladder_nonflat, is_null[84:]])
    m_red = pv_red.shape[1]
    assert m_red == 154

    def summarize(name, rejmap, nullmask, ladder_flag_fn):
        res = {}
        for proc, rej in rejmap.items():
            v = (rej & nullmask).sum(axis=1)
            s = (rej & ~nullmask).sum(axis=1)
            tot = rej.sum(axis=1)
            res[proc] = dict(
                true_rej=float(s.mean()), false_rej=float(v.mean()),
                fwer=float((v > 0).mean()),
                fdr=float(np.where(tot > 0, v / np.maximum(tot, 1), 0.0).mean()),
                ladders_flagged=float(ladder_flag_fn(rej).mean()),
                power_per_true=float(s.mean() / max((~nullmask).sum(), 1)))
            print(f"  [{name}] {proc:12s} trueRej={res[proc]['true_rej']:.2f} "
                  f"FWER={res[proc]['fwer']:.4f} FDR={res[proc]['fdr']:.4f} "
                  f"ladders={res[proc]['ladders_flagged']:.2f}", flush=True)
        return res

    lad_pair_ladder = np.array(ladder_of_pair)

    def flag_full(rej):
        out = np.zeros(rej.shape[0])
        nf = np.where(ladder_nonflat)[0]
        got = np.zeros((rej.shape[0], 28), dtype=bool)
        for t_ in range(84):
            got[:, lad_pair_ladder[t_]] |= rej[:, t_]
        return got[:, nf].sum(axis=1)

    def flag_red(rej):
        nf = np.where(ladder_nonflat)[0]
        return rej[:, :28][:, nf].sum(axis=1)

    full = summarize("m=210", apply_corrections(pv, is_null, m_full), is_null, flag_full)
    red2 = summarize("m=154", apply_corrections(pv_red, null_red, m_red), null_red,
                     flag_red)
    # DECOMPOSITION: hold the family size at 210 (alpha unchanged) but swap the TEST
    # (3 pairwise -> 1 trend per ladder). Difference vs the m=154 arm isolates the
    # correction's contribution from the test's.
    fixed_alpha = summarize(
        "test-swap only (alpha=0.05/210)",
        {"Bonferroni@210": pv_red < ALPHA / N_PRIMARY}, null_red, flag_red)
    OUT["part4"] = dict(n_sims=n_sims, n_true=n_true, n_null=int(is_null.sum()),
                        n_true_reduced=int((~null_red).sum()),
                        nonflat_ladders=int(ladder_nonflat.sum()),
                        true_deltas=sorted(set(np.round(true_diff[~is_null], 4).tolist())),
                        full=full, reduced=red2, test_swap_fixed_alpha=fixed_alpha,
                        rates=rates.tolist())


def main():
    t0 = time.time()
    part1(np.random.default_rng(1)); dump("part1")
    part3(np.random.default_rng(3)); dump("part3")
    part5(np.random.default_rng(5)); dump("part5")
    part2(np.random.default_rng(2)); dump("part2")
    part4(np.random.default_rng(4)); dump("part4")
    print(f"\nTOTAL {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
