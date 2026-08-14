# CMH variants for the family-ladder induction design — findings (draft of StructuredOutput)

## 1. Ordered-category / trend CMH

C1. PREMISE DEFECT. With a binary response (C=2), the CMH row-mean-scores statistic
(df=R-1=2) and the general-association statistic (df=(R-1)(C-1)=2x1=2) are the SAME
statistic. SAS PROC FREQ: "For a stratified 2x2 table, the three CMH statistics ...
test the same hypothesis." So the row-mean-scores option is NOT a distinct alternative
to the df=2 gate already coded in gcmh_reject. The only genuinely 1-df ordered option
is the CORRELATION / nonzero-correlation statistic (Mantel 1963) = stratified
Cochran-Armitage, which requires numeric SCORES on the rung axis.
Cites: Landis, Heyman & Koch 1978 Int Stat Rev 46:237-254; Mantel 1963 JASA 58:690-700;
SAS/STAT FREQ CMH doc; vcdExtra::CMHtest (cor df=1, rmeans df=R-1, general df=(R-1)(C-1)).

C2. POWER GAIN (derived, scipy ncx2/chi2). At the lambda giving 80% power at df=1:
  alpha=0.05      lam=7.85  -> df=2 power 0.709 ; n-ratio (lam2/lam1) 1.228
  alpha=0.05/7    lam=12.47 -> df=2 power 0.706 ; n-ratio 1.182
  alpha=0.05/210  lam=20.40 -> df=2 power 0.708 ; n-ratio 1.136
At 90%: 0.835/0.834/0.837 and ratios 1.204/1.166/1.125.
=> ~9pp power at fixed n, or 13-23% fewer replicates. Gain SHRINKS as alpha shrinks
(Bonferroni already pushed to 2.38e-4 => only 13.6%). Theory: Lachin 2011 Stat Med
30(25):3057-3066, doi 10.1002/sim.4330 (power = f(noncentrality)).

C3. WHAT IT MISSES + SCORE CHOICE. lambda_total (df=2) = lambda_linear + lambda_quadratic
(orthogonal). Trend captures only lambda_lin/lambda_total = corr^2(centered scores,
centered true rung means). Computed:
  symmetric inverted-U (p, p+d, p): corr^2 = 0.0 EXACTLY -> trend power = alpha, a
    total miss; the df=2 gate retains full power. Non-monotone ladders are a live risk.
  exaone 32b/33b/236b: rank scores (1,2,3) vs truth linear in log10(params) -> 0.7615
    (24% of lambda thrown away; ~24% more replicates). Symmetric in the other direction too.
  min3 3b/8b/14b -> 0.9757 ; qwen35 27b/122b/397b -> 0.9951.
=> the score choice (rank vs log-params) is a real, pre-registerable decision and it
matters most for exaone.
Cites: Cochran 1954 Biometrics 10:417-451 doi 10.2307/3001616; Armitage 1955 Biometrics
11:375-386 doi 10.2307/3001775.

## 2. Paired / matched binary

C4. The code's `cmh_reject` treats the two arms as INDEPENDENT binomials, but every
model answers the same seeds/harmonics with byte-identical prompts. Correct tests:
 - 2 arms: McNemar (discordant cells only). CMH stratified with each matched SET as its
   own stratum reduces EXACTLY to McNemar; = score test of conditional logistic regression.
 - blocking factor (harmonic) retained: CMH with strata = (harmonic x seed) matched sets,
   or equivalently harmonic-stratified McNemar (sum discordances within harmonic).
 - >2 matched groups (the 3 rungs!): Cochran's Q (Cochran 1950 Biometrika 37:256-266),
   the direct generalization of McNemar to k related binary samples. This is the right
   Tier-1 omnibus, NOT the independent-binomial gcmh df=2.

C5. QUANTIFIED LOSS (exact identity, derived + verified numerically).
For equal marginals p:  DE = n_unpaired/n_paired = 2pq / d
  where d = observed discordance rate and 2pq = discordance expected under independence.
Equivalently DE = 1/(1-phi) to first order (phi = tetrachoric/phi correlation of arms).
  p=0.97: d=0.02 -> DE 2.91 (+191% replicates); d=0.05 -> DE 1.16
  p=0.95: d=0.02 -> DE 4.75; d=0.05 -> DE 1.90; d=0.08 -> 1.19
  p=0.92: d=0.05 -> DE 2.94; d=0.133 -> DE 1.11
  p=0.90: d=0.02 -> DE 9.00; d=0.05 -> 3.60
  unequal, near-ceiling nested (0.98 vs 0.96, d=0.02) -> DE 2.96, phi +0.700
  ceiling ladder pair (0.97 vs 0.93, d=0.05) -> DE 1.95, phi +0.526
  extens collapse (0.94 vs 0.44, d=0.52) -> DE 1.12, phi +0.139
Note DE<1 is possible (d>2pq, anti-correlated arms) — pairing can LOSE.
Published range: independence chi-square on paired data commonly quoted at 20-50% power loss.

C6. CEILING IS WHERE PAIRING PAYS. Because 2pq -> 0 slowly but d can -> 0 fast at ceiling,
the ceiling arms (intens/noise/zero at 0.97-1.00) are exactly where the independent-binomial
CMH is most wasteful (DE 2-6x), while the WIDE-SPREAD extens arm gains least (DE ~1.1).
Anchor from this repo's own divisor study: two gpt-oss arms scored identically but agreed
on only 86.7% of marks (104 flips exactly cancelling) => d=0.133 at p~=0.92 => DE=1.11,
phi=+0.096. So on THAT contrast pairing buys only ~11%; on the low-discordance ceiling
contrasts it buys 2-3x. The gain is a function of measured discordance, not of "pairedness".

## 3. Clustered / overdispersed

C7. STRUCTURAL MISMATCH with the standard fixes. Here cluster = replicate seed, and one
seed contributes EXACTLY ONE unit to EACH of the 9 harmonic strata. So:
 - within a stratum, observations are independent across seeds -> the per-stratum
   hypergeometric variances CMH computes are CORRECT;
 - the error is the OMITTED CROSS-STRATUM COVARIANCE in Var(sum_j T_j) =
   sum_j Var(T_j) + 2 sum_{j<j'} Cov(T_j, T_j'). CMH drops the second term.
Donner-Banerjee / Donald-Donner adjusted MH, Rao-Scott, and Zhang-Boos (1997 Biometrics
53:1185-1198) are all formulated for clusters nested INSIDE a single stratum x arm cell
(multiple correlated units in one 2x2 table). They do not address clusters that span strata.
The nearest exact match in the literature is the CLUSTERED MATCHED-PAIR family
(Obuchowski 1998 Stat Med 17:1495-1507; Durkalski 2003; Yang 2010 Biom J; R pkg clust.bin.pair),
where a cluster contributes several matched pairs — that IS this design with cluster=seed.

C8. QUANTIFIED SIZE DISTORTION (derived). With equicorrelation rho_d among the 9
per-stratum arm-difference contributions, CMH stat ~ (1 + 8*rho_d) * chi2_1.
Actual size at nominal 0.05:  rho_d=.02 -> .069 ; .05 -> .098 (2.0x) ; .10 -> .144 (2.9x)
Actual size at Bonferroni 2.38e-4: rho_d=.02 -> 6.5e-4 (2.7x) ; .05 -> 1.9e-3 (8.0x) ;
   .10 -> 6.2e-3 (26x) ; .20 -> 2.3e-2 (95x).
KEY: the deep Bonferroni tail is FAR more sensitive to variance inflation than alpha=0.05.
A rho_d of only 0.05 — easily produced by one shared sequence realization — turns a
2.4e-4 test into a 1.9e-3 test.

C9. DIRECTION IS NOT UNCONDITIONALLY INFLATION. The classic inflation result assumes
clusters nested within treatment arms. Here every seed serves every model and every arm,
so the seed's shared difficulty largely CANCELS in the arm difference; what survives is
the seed x arm interaction. If rho_d < 0 the naive CMH is CONSERVATIVE (rho_d=-0.05 ->
size .011 at nominal .05). The sign is directly measurable from the existing R=30 data
(correlate per-seed arm differences across harmonics) and is the discriminating question.

C10. WHICH FIX IS STANDARD PRACTICE, given C7's geometry:
 - PERMUTE / BLOCK-BOOTSTRAP WHOLE REPLICATES (cluster-level randomization inference;
   Gail et al. 1996; Braun & Feng 2001 JASA). Admits cross-stratum clusters, needs no
   large-#cluster asymptotics, exact under exchangeability of seeds. RECOMMENDED HERE,
   and consistent with notebooks/lean/power_analysis.py which already block-bootstraps.
 - GEE with seed as cluster id, arm/rung as within-cluster covariate, exchangeable
   working correlation (Liang & Zeger 1986). At 30 clusters the naive sandwich is
   downward-biased: <40 clusters inflates type I error; use Mancl-DeRouen 2001 /
   Fay-Graubard 2001 / Kauermann-Carroll 2001 corrections + t/F reference distribution
   (Li & Redden 2015 Stat Med 34:281-296 doi 10.1002/sim.6344).
 - Design-effect inflation (divide statistic by 1+(m-1)rho) and Rao-Scott are the
   survey-sampling standards but assume the within-stratum geometry — applicable only
   after collapsing harmonics, not for the harmonic-stratified statistic.
