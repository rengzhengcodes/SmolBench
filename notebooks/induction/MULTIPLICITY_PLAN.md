# Multiplicity & error-rate plan — periodic induction, 21-model family ladder

**Status:** recommendation, 2026-08-14. **Partly superseded the same day — read
`PAIRED_ANALYSIS_RESULTS.md` alongside it.**

> **Correction (2026-08-14, after running the re-analysis this document specified).**
> §2.1 predicted up to a **53× power gain** from switching to a paired test. Run against
> the landed data, pairing changes **1 of 210 contrasts**. The simulation swept
> discordance rates that were low but nonzero, where `DE = 2pq/d` blows up; the study's
> actual ceiling pairs have *exactly zero* discordant items (1.000 vs 1.000, b/c = 0/0),
> and no test recovers signal from zero discordance. **The recommendation stands — adopt
> the paired test because it is correct for a matched design and free — but the power
> argument for it does not.** §2.2's clustering worry survives in a much milder form: the
> measured design effect is ~1.12 median / 1.88 p90, not the 56× the bracket allowed.
> Read every power figure in §1–§3 as conditional on the simulated regime, not as a
> property of this dataset.
**Scope:** `notebooks/induction/` (the 7-family × 3-rung × 4-info-arm scaling study, R = 30,
seeds 0–29, 9 harmonics per replicate). Sizing lives in `power_analysis.py`; **no
analysis script exists yet**, so this document is written as the specification that
script should implement.

**Evidence and its provenance** (three sources — do not attribute all numbers to one):

- `notebooks/induction/multiplicity_sim.py` — the Monte Carlo. Source for §1's
  correction-cost figures, §2.1's pairing table, §2.2's Type I error table, §3's
  minimum-detectable-difference table, and §4's trend/omnibus/pairwise power table. The
  headline pairing rows were re-derived with an independent implementation and matched to
  within MC error.
- `notebooks/induction/MULTIPLICITY_CMH_VARIANTS.md` — derivations behind the Cochran's Q
  recommendation, the cluster-geometry argument in §2.2, the `DE = 2pq/d` closed form and
  its table in §2.1, and the score-capture figures in §4 (76% exaone / 98% min3 / 99.5%
  qwen35).
- The adversarial verification pass (three verifiers over the literature claims). Source
  for §1's de-pooling comparison (0.856 vs 0.697 etc.) and the `w_j` weight-collapse
  figures, both computed ad hoc against the repo's own `gcmh_reject`. These two were not
  independently reproduced.

Refuted claims are recorded in "What we rejected" so they don't get re-proposed.

---

## Bottom line

**The pre-registered three-tier correction scheme is sound and does not need to be
rebuilt.** Bonferroni over the 210-test PRIMARY family controls FWER validly whether or
not the Tier-1 gate fires, and the Tier-1/Tier-2/Tier-3 split matches standard
confirmatory/exploratory practice.

But the correction is not where this analysis is losing. Two upstream problems dominate
it, and both change how much power Bonferroni is actually costing:

1. **The planned test is unpaired; the design is paired.** `cmh_reject` draws two
   independent binomials, yet every model answers the *same* seeds with byte-identical
   prompts. Switching to a matched test is worth up to a **53× power gain** — roughly
   50 times more than switching Bonferroni → Holm.
2. **The stratified CMH does not hold its nominal level under this design's clustering.**
   Each seed contributes one unit to all 9 harmonic strata, and CMH sums those strata's
   variances as if independent. Depending on the sign of the seed × arm interaction the
   test is either conservative or badly anticonservative — up to **56× the nominal
   α = 2.38e-4**. Correcting a threshold on a statistic that doesn't hold its size is
   precision theater.

Fix the statistic first, then the correction. Recommended changes, in priority order:

| # | Change | Effort | Payoff |
|---|--------|--------|--------|
| 1 | Paired (McNemar / matched-set CMH) pairwise test | moderate | up to 53× power; 2–3× fewer replicates |
| 2 | Replicate-level block bootstrap / permutation for p-values | moderate | fixes the level; the only fix whose geometry matches |
| 3 | Bonferroni → **Holm** on Tier 2 (and Tier 1) | trivial | free, but worth ~0.5% here |
| 4 | Report TOST equivalence for every ceiling contrast | small | stops "no separation" being misread as "no difference" |
| 5 | Add a 1-df CMH trend statistic as a **secondary** ladder readout | moderate | +8 pts on monotone ladders; **do not** replace the df=2 gate |

---

## 1. What multiplicity correction is actually needed

### Keep FWER on Tiers 1–2, keep BH on Tier 3

This is already what the code does and it is defensible. Tier 2 is the confirmatory
family; Tier 3 is explicitly secondary/exploratory. Bender & Lange (2001) and the FDA
multiple-endpoints guidance both support tiering the error criterion by confirmatory
intent, *provided the tiers were fixed before unblinding* — which the lock satisfies.

**One honest caveat.** The design currently spends three separate full budgets: 0.05
across the 7 gates, 0.05 across the 210 Tier-2 tests, and q = 0.05 at Tier 3. Gatekeeping
and α-recycling frameworks *allocate or propagate one* study-level α; they do not license
three independent 0.05 budgets. Nothing is invalid — each family controls its own error
rate — but the write-up must not imply a single 5% study-wide guarantee. State the budget
explicitly: Tier 1 and Tier 2 are separate FWER families at 0.05 each, Tier 3 is a
separate exploratory FDR budget, and the gate is a **reporting** gate, not a claim.

### Bonferroni → Holm: adopt it, but expect nothing

Holm (1979) controls FWER under **arbitrary** dependence — the same guarantee as
Bonferroni, no extra assumption — and is uniformly more powerful: its first threshold is
exactly α/m and every later one is strictly looser, so it can never reject less. Given
the 210 CMH statistics share models, seeds and harmonics in an unmodelled way,
"valid under arbitrary dependence" is the property that matters.

It is free, so take it. But simulate before promising anything: over 210 contrasts with
30 true effects, Holm returns **12.56** true rejections against Bonferroni's **12.49**.
The reason is that this study's effects are bimodal — huge (any arm vs the chance-floor
`zero` arm) or ceiling-vs-ceiling ties — so almost nothing sits near the threshold where
step-down procedures earn their keep.

**This comparison is conditional on the unpaired test and must be re-run once the paired
statistic is in place.** Every figure in this section was simulated under `cmh_reject`.
Pairing moves contrasts that were structurally unable to reject into the near-threshold
band — precisely where step-down procedures earn their keep — so the bimodality argument
that makes Holm worth ~0.5% here may not survive the switch. The same caveat applies to
the BH comparison below.

### Do not use Hochberg, Hommel, or Šidák

- **Hochberg / Hommel** need Simes-type positive dependence (MTP2, Sarkar 1998). That is
  unverified and not obviously true for this contrast structure. In simulation Hochberg
  returns **12.56** — identical to Holm — so the assumption risk buys exactly zero.
- **Šidák** gives 2.44e-4 vs Bonferroni's 2.38e-4: **2.6% looser**, for an independence
  assumption that is false here.

### BH on Tier 2: a real gain, but it changes the guarantee

BH at q = 0.05 over the 210 finds **18.17** true effects vs Bonferroni's 12.49 (+5.7) and
flags 5.26 of 6 true ladders vs 3.78 — at realized FWER **0.312**. That is the honest
trade: a third of runs would contain at least one false claim. Keep FWER as the Tier-2
headline; if the extra discoveries are wanted, report BH-adjusted q-values as a
**pre-registered secondary column**, never as the primary claim.

### Rejected: resampling-based maxT over the whole family

Westfall–Young step-down maxT is the textbook way to exploit correlation instead of
assuming the worst case, and it was the most promising candidate going in. It does not
work here, for a design reason: a joint maxT needs **one** resampling scheme valid for
every hypothesis in the family, and Tier 2 is heterogeneous — the 84 ladder contrasts
exchange *model* labels within a family, the 126 info contrasts exchange *info* labels
within a model, and no single group does both (permuting a model label changes whose info
arms you hold). That is a subset-pivotality failure. The Meinshausen–Maathuis–Bühlmann
optimality result also assumes **sparse** signal; this family is dense in its info half
(63 of 126 contrasts involve the chance-floor `zero` arm and are near-certain rejections).

Per-contrast replicate-level resampling stays fully applicable — see §2.2. It is the
joint 210-test adjustment that fails.

### Rejected: eigenvalue "effective number of tests" (M_eff)

Cheverud / Li–Ji / Nyholt / Galwey estimate an effective test count from the correlation
matrix of the *tested family*. Here the multiplicity is over **210 contrasts**; the 9
harmonics are strata *inside* each single CMH statistic and are already absorbed by
stratification. An M_eff over a 9×9 harmonic matrix corrects a dimension that is not being
multiply tested. The right object would be the ~210×210 contrast-statistic correlation
matrix, which the study does not have and would have to bootstrap — at which point
per-contrast resampling is the more direct route.

### Rejected: dropping Bonferroni under the k=3 protected-LSD result

This was the highest-leverage idea and it is *nearly* right, which makes it dangerous.

The classical result is real and it is **combinatorial, not distributional**: for three
groups, {H₁₂, H₁₃, H₂₃, H₁₂₃} is closed under intersection, so the number of true
hypotheses is 0, 1 or 4 — never 2 or 3. Closed testing (Marcus–Peritz–Gabriel 1976) then
permits testing the intersection at α and, if rejected, each pair at α with no further
adjustment. Crucially, **Goeman & Solari (2021, *The American Statistician*, §10)
explicitly extends this to categorical settings** (chi-square on 2×3 tables,
Kruskal–Wallis, log-rank), so the gate and the pairwise tests need not be the same family
of statistic. Every ladder in this study has exactly 3 rungs.

**It still does not apply to the gate as coded.** `gcmh_reject` pools harmonic × info into
K = 36 strata, so its null is the intersection of all **twelve** ladder hypotheses in a
family (3 rung-pairs × 4 infos) — not the three hypotheses of one (family, info) triple.
The k = 3 collapse holds *within* a triple. Invoking it under the current 36-stratum gate
would be a genuine FWER violation.

Re-scoping to 28 per-(family, info) gates at K = 9 would restore the argument and yield
α/28 = 1.79e-3 for the ladder half (7.5× looser). We do **not** recommend it:

- Run on the repo's own `gcmh_reject` (R = 30, 20k sims, ceiling arms at 0.99, effect on
  `extens` only), de-pooling helps the statistic at matched α (0.856 vs 0.697) but, once
  it pays the 28-way Bonferroni, **loses at small effects** (0.233 vs 0.256; 0.051 vs
  0.078) and wins only at the largest.
- It dissolves the locked pre-registered Tier-2 family.
- **Negative finding worth recording:** no published source establishes the transfer for
  this specific pairing — a generalized-CMH df=2 gate over stratified 2×2×K CMH pairwise
  tests. Searches for protected chi-square, protected CMH, and multiple comparisons for
  stratified 2×2 tables found nothing on point. If this is ever pre-registered it must be
  cited as a *derivation* from closed testing, not as precedent.

Two further guards: the k = 3 result must **never** leak onto the 126 within-model info
contrasts — those are k = 4 (6 hypotheses among 4 arms), where configurations like
{intens = noise_intens, extens = zero} leave two true nulls and protected LSD provably
fails (Hayter 1986). And Shaffer's (1986) logical-constraint improvement, while valid
here, buys nothing: for k = 3 it improves only step 2, and for k = 4 only steps 2–3 —
whereas this study's limiting contrasts (ceiling-vs-ceiling `intens` vs `noise_intens`)
land at steps 5–6, where Shaffer is identical to Holm.

### No correction across tiers, or across the induction/deduction studies

Tiers are pre-registered, disjoint, and reported as separate claim classes; the family
requiring joint control is the set of hypotheses feeding one confirmatory decision. The
sibling deduction study defines its own self-contained family and is reported separately.
Note this is an absence-of-evidence position — no source was found *stating* the norm —
so present it as a design choice, not a cited rule.

---

## 2. The two upstream problems that matter more

### 2.1 The design is paired and the test is not

Confirmed in code: `smolbench/induction/periodic.py` line 116 — *"the intensional and
extensional prompts are identical across models, only `noise_intens` varies"* — and
`get_periodic_zero_info_numeric_quiz` (line 490) reuses **the same queries and answers**,
emptying only the context. So at a given seed, all four info arms and all 21 models face
byte-identical items. **All 210 primary contrasts are matched on item**, as are the 63
Tier-3 contrasts.

`cmh_reject` nevertheless draws `succ_a` and `succ_b` as independent binomials. What that
costs, at α = 2.38e-4, R = 30, p_A = 0.95 (Monte Carlo; ρ = latent tetrachoric
correlation, φ = realized binary correlation):

| ρ (φ) | δ | unpaired CMH | exact McNemar | R needed to match paired R=30 |
|---|---|---|---|---|
| 0.0 (0.00) | 0.05 | 0.0433 | 0.0501 | 35 (1.17× — discreteness floor, not a gain) |
| 0.5 (0.22) | 0.05 | 0.0243 | 0.0762 | 45 (1.50×) |
| **0.9 (0.58)** | **0.05** | **0.0051** | **0.2723** | **85 (2.83×)** |
| 0.9 (0.51) | 0.10 | 0.5421 | 0.9866 | 60 (2.00×) |
| 0.7 (0.48), p_A=0.70 | 0.10 | 0.0327 | 0.3235 | 60 (2.00×) |

The design effect has a closed form: `DE = 2pq / d`, where `d` is the observed discordance
rate and `2pq` is discordance expected under independence. **Ceiling is exactly where
pairing pays**, because `d → 0` faster than `2pq` does: at p = 0.97 with d = 0.02,
DE = 2.91; at p = 0.95 with d = 0.02, DE = 4.75. The wide-spread `extens` arm gains least
(the extens-collapse contrast 0.94 vs 0.44 gives DE ≈ 1.12).

This has a direct bearing on a standing result. The divisor study recorded gpt-oss's two
arms scoring *identically* while agreeing on only 86.7% of marks — 104 flips exactly
cancelling. Under an unpaired test those 104 flips are invisible; under McNemar they are
the entire signal. **"intens vs noise separated for no model" may be an artifact of the
test, not a finding.** Re-analysing the stored marks pairwise is the single highest-value
action available, and it needs no new data collection.

**Specification.** Pairwise contrasts use exact McNemar on item-matched marks, or
equivalently CMH with each matched set (seed × harmonic) as its own stratum — the two
coincide. For the 3-rung ladder omnibus, the matched analogue of the df=2 gCMH is
**Cochran's Q** (Cochran 1950), the direct generalization of McNemar to k related binary
samples. Caveat for the `noise_intens` arm: prompts differ per model by construction
(token-matched padding), so it is matched on *item and answer* but not on rendered prompt
— note it, don't exclude it.

### 2.2 The stratified CMH does not hold its level

Each replicate's 9 questions share one sequence realization, and each seed contributes
**exactly one unit to each of the 9 harmonic strata**. So:

- *within* a stratum, observations are independent across seeds → CMH's per-stratum
  hypergeometric variances are **correct**;
- the error is the **omitted cross-stratum covariance**: Var(ΣT_j) = ΣVar(T_j) +
  2Σ_{j<j'}Cov(T_j,T_j'), and `cmh_reject` drops the second term.

This geometry matters, because it rules out the standard fixes. Donner–Banerjee,
Rao–Scott, and design-effect inflation are all formulated for clusters nested *inside* a
single stratum × arm cell; they do not address clusters that **span** strata. The nearest
literature match is the clustered matched-pair family (Obuchowski 1998; Durkalski 2003).

**The direction is not unconditionally inflation** — this is the part that needs measuring
rather than assuming. Every seed serves every model and every arm, so a seed's shared
difficulty largely *cancels* in the arm difference; what survives is the seed × arm
interaction. Simulation brackets both cases (actual Type I error, p = 0.90):

| ICC | nominal 0.05, arm-specific | nominal 2.38e-4, arm-specific | shared effect (0.05) |
|---|---|---|---|
| 0.0 | 0.0351 (0.70×) | 1.05e-4 (0.44×) | — (conservative by construction) |
| 0.1 | 0.0644 (1.29×) | 5.90e-4 (2.5×) | 0.0321 |
| 0.2 | 0.0987 (1.97×) | 2.36e-3 (9.9×) | 0.0281 |
| 0.4 | 0.1796 (3.6×) | 1.34e-2 (**56×**) | 0.0204 |
| 0.4, p=0.70 | 0.2353 (4.71×) | 2.91e-2 (**122×**) | — |

**The deep Bonferroni tail is far more sensitive to variance inflation than α = 0.05 is.**
A modest cross-stratum correlation of 0.05 — easily produced by one shared sequence
realization — turns a 2.4e-4 test into a 1.9e-3 test. Any argument about whether α/210 is
too strict is moot until the statistic's actual size is known.

**Specification.** (a) *Measure the sign first* — correlate per-seed arm differences across
harmonics in the existing R = 30 data. This is a few lines and it decides everything.
(b) Compute p-values by **resampling whole replicates** (block bootstrap or sign-flip
permutation of the per-replicate paired difference), not from the asymptotic χ². The
resampling unit must be the whole seed, since only between-cluster arrangement is
exchangeable. This is exactly what the sibling deduction leg already does —
`notebooks/deduction/power_analysis.py` block-bootstraps whole theorem blocks — so the
induction leg is the outlier, not the innovator. GEE with seed as cluster id is the
alternative, but at 30 clusters the naive sandwich is downward-biased and would need a
Mancl–DeRouen / Fay–Graubard correction; resampling is cleaner.

---

## 3. Ceiling effects: what α = 2.38e-4 structurally forbids

Minimum detectable difference at 80% power, n = 270 marks/arm:

| p_A | α = 2.38e-4 | α = 0.05 | penalty |
|---|---|---|---|
| 0.99 | **0.0875** | 0.0450 | 1.94× |
| 0.97 | 0.1100 | 0.0600 | 1.83× |
| 0.95 | 0.1250 | 0.0700 | 1.79× |
| 0.90 | 0.1500 | 0.0875 | 1.71× |
| 0.70 | 0.1950 | 0.1200 | 1.63× |

On the saturated `intens` / `noise_intens` / `zero` arms (0.97–1.00 in the predecessor),
Tier 2 **cannot resolve any gap under ~9 points**. Non-rejection there carries almost no
information about equality.

Two consequences. First, the TOST equivalence arm already in `power_analysis.py` is not a
nicety — it is the only way a ceiling contrast can say anything, and it must be reported
for every ceiling contrast, not just those flagged near-tie. Second, **fix the
data-dependent family size**: `alpha_eq = ALPHA / len(near_ties)` sizes the equivalence
family from the *observed* pilot. That is acceptable in a sizing script; carried into
inference it invalidates the correction, because the family size would then depend on the
data. Pre-register the equivalence family as a fixed list.

---

## 4. The ladder trend test: secondary, not a replacement

Two premise corrections first. With a **binary** response, the CMH row-mean-scores and
general-association statistics are the *same* statistic (both df = 2) — so the only
genuinely 1-df ordered option is the **correlation statistic** (Mantel 1963 = stratified
Cochran–Armitage), which needs numeric scores on the rung axis. And it is **not** a df
swap in `gcmh_reject`: that function builds a 2-vector of rung residuals with
Σ = (Σⱼwⱼ)·C₀ from multivariate-hypergeometric moments; the correlation statistic is a
scalar score-weighted contrast with its own variance. New derivation, new code path.

Power (local α = 0.05; 1-df trend / 2-df omnibus / any-of-3 Bonferroni pairwise):

| ladder | trend | omnibus | pairwise |
|---|---|---|---|
| monotone 0.60/0.66/0.72 | **0.8435** | 0.7591 | 0.7062 |
| non-monotone 0.60/0.72/0.66 | **0.3188** | 0.7558 | 0.7056 |
| monotone near-ceiling 0.99/0.96/0.93 | 0.9684 | 0.9384 | 0.8928 |
| non-monotone 0.99/0.93/0.96 | 0.4002 | 0.9389 | 0.8939 |

Trend wins 8–14 points on monotone ladders and **loses 44** on non-monotone ones. That
risk is live, not hypothetical: the predecessor produced Nemotron-3's `extens` collapse to
0.448 while siblings sat at 0.94–0.98. Two roster rungs are also not cleanly ordered —
exaone-4.0-32b / 4.5-33b are 3% apart across two model generations, and ds_flash / ds_v31 /
ds_pro mixes V3.1 with V4 — so the score vector (rank vs log-parameters) is itself a
pre-registrable decision. Computed: rank scores capture only 76% of the available
non-centrality for exaone, against 98% for min3 and 99.5% for qwen35.

**Recommendation: report the trend statistic as a pre-registered secondary readout
alongside the df=2 gate; do not replace it.** For the record, family-size reduction is the
*small* half of this lever anyway — replacing 84 pairwise ladder contrasts with 28 trend
tests flags 4.34 of 6 true ladders vs 3.78, and holding the family at m = 210 while
swapping only the test already gets 4.20. The test change contributes ~3× what the α
change does.

---

## What we rejected, and why (so it isn't re-proposed)

| Proposal | Verdict |
|---|---|
| Drop Bonferroni on ladders via k=3 protected LSD | Valid result, licensed for categorical data — but the K=36 gate's null is the wrong node. Re-scoping loses at small effects. |
| Re-split α over 49 primary units (4.29× looser) | Correct arithmetic for the 84 ladder contrasts only; for the k=4 info half it is *stricter* (1.70e-4 vs 2.38e-4). Also dissolves the locked family. |
| Shaffer instead of Holm | Valid; improves only steps 2–3, while this study's limiting contrasts land at steps 5–6 where Shaffer ≡ Holm. |
| Westfall–Young maxT over Tier 2 | No common exchangeability group across ladder and info contrasts; signal is dense, not sparse. |
| Eigenvalue M_eff from the harmonic correlation matrix | Wrong matrix — harmonics are strata, not family members. |
| Yekutieli hierarchical tree-FDR | Would *downgrade* Tier 2 from strong FWER to a depth-dependent FDR bound. |
| Hochberg / Hommel | Unverified MTP2 assumption; returns exactly Holm's result here. |
| Replace the df=2 gate with a df=1 trend gate | Blind to non-monotone ladders, which this roster produces. |

## Key references

- Holm (1979), *Scand. J. Statist.* 6:65–70 — step-down, arbitrary dependence.
- Marcus, Peritz & Gabriel (1976), *Biometrika* 63:655–660 — closed testing.
- Goeman & Solari (2021/22), *The American Statistician*, DOI 10.1080/00031305.2021.2002188,
  §6 and §10 — three-group closure; explicit extension beyond ANOVA to categorical tests.
- Hayter (1986), *JASA* 81:1000–1004 — LSD protection fails at k ≥ 4.
- Shaffer (1986), *JASA* 81:826–831 — logical-constraint step-down.
- Sarkar (1998), *Ann. Statist.* 26:494–504 — MTP2 ⇒ Simes (Hochberg/Hommel's condition).
- Benjamini & Yekutieli (2001), *Ann. Statist.* 29:1165–1188 — BH under PRDS; BY fallback.
- Benjamini & Bogomolov (2014), *JRSS-B* 76:297–318 — selective inference over families.
- Westfall & Young (1993), *Resampling-Based Multiple Testing* — maxT/minP, subset pivotality.
- Cochran (1950), *Biometrika* 37:256–266 — Q, matched k-sample binary.
- Mantel (1963), *JASA* 58:690–700 — CMH correlation (trend) statistic.
- Obuchowski (1998), *Stat. Med.* 17:1495–1507 — clustered matched pairs.
- Bender & Lange (2001), *J. Clin. Epidemiol.* 54:343–349 — when adjustment is required.

*Two source-level corrections found during verification, noted so they aren't propagated:*
*the 1994 Psychological Bulletin paper is Levin, Serlin & **Seaman** (not Webne-Behrman);*
*Berkeley Stat TR 633 is Ge, Dudoit & **Speed** (not van der Laan).*
