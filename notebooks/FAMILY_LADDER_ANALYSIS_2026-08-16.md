# Family-ladder scaling study — final analysis, both legs

**2026-08-16.** 21 checkpoints (7 vendor families × 3 parameter rungs), evaluated on
periodic **induction** (R=30 replicates × 9 harmonics × 4 information arms) and Lean-4
**deduction** (pass@1 over `(theorem, k, prompt_rung)` cells). Collection and
verification finished 2026-08-16; this document is the analysis.

Two method directives were set for this pass and both are honoured below:
**Holm–Bonferroni** for the induction multiplicity correction, and **error bars
established by measurement** for deduction.

Artifacts: `notebooks/induction/significance_report.py`,
`notebooks/induction/extens_vs_noise.py`, `notebooks/deduction/error_bars.py`,
`notebooks/deduction/ERROR_BARS_REPORT.txt`.

---

## 0. Data provenance, gated on content

The published snapshot is `s3://smolbench-results-414266451290/analysis/2026-08-16/`
(55,006 objects / 4.61 GB). Two checks ran before any number below was computed,
because both legs had a rule that a row/object count would have certified wrongly.

**Induction — the local tree is current, gated under the ruling in force.** The gate had
to flip with the selection rule: a tree that matched the *newest* version, as an earlier
pass certified, is wrong for the 140 multi-attempt cells once earliest-wins applies.
Size discriminates them — the `gemma-4-12b` seed=8 `extens` pair is 922,083 vs 1,319,921
bytes — so a full-tree size match is a real content gate rather than an object count:

| check | result |
|---|---|
| snapshot objects | 2,660 |
| distinct cells (= 21 × 4 × 30) | 2,520 |
| cells with more than one attempt | 140 |
| **local matches EARLIEST, by size** | **2,520** |
| missing locally | 0 |
| not earliest (stale) | 0 |
| lanes below R=30 | none |

2,660 = 2,520 + 140 duplicates. The re-gate was run after the snapshot refresh that
closed `ministral-3-14b`; the refresh was additive-only (28 objects added, 55,002
untouched), so nothing previously certified changed content.

*Limit of the size gate:* it discriminates here because all 140 earliest/newest pairs are
size-distinct, minimum delta 827 bytes — but that is a property of this data, not a
guarantee. A same-size pair would pass a size gate while differing in content. The
durable form is a checksum comparison (an independent `sync_down` md5 pass reported 0
downloaded / 2,520 skipped, agreeing cell-for-cell with the result above).

**Selection rule — EARLIEST logged attempt, both legs (user ruling, 2026-08-16).** Per
(model, seed, arm) on induction the object with the minimum run timestamp wins; per cell
on deduction the earliest *surviving* row wins. 140 of the 2,520 induction cells own more
than one logged attempt (`gemma-4-12b` 56, `deepseek-v4-flash` 48, `ministral-3-14b` 36);
the other 18 lanes are single-attempt and bit-identical under any rule.

The rule's effect was measured rather than assumed, holding the seed set fixed so the
selection is the only variable (`notebooks/induction/compare_selection_rules.py`):
**124 rejections under earliest against 122 under newest, with 2 of 210 contrasts
flipping** — both borderline, both crossing *into* significance. That direction is a
property of those two lanes, not of the rule; earliest-wins is neither statistically
conservative nor liberal, it exists to stop retry-until-success inflating a pass@1
numerator. **The five clean lanes carrying the extens-vs-noise finding own no
multi-attempt cell, so their p-values are byte-identical under both rules and the ruling
cannot reach the headline.** Both predicted flips then confirmed at R=30:
`[gemma4 ladder | intens] gemma4_e2b vs gemma4_12b` held at p=1.22e-04, and
`[min3 ladder | extens] min3_8b vs min3_14b` strengthened from 6.36e-04 to 5.85e-06.

**Deduction — the loader reproduces the collection side exactly.** `load_joint_cells`
already implements *earliest surviving row per cell* (last-wins takes a resampled retry
and inflates `ministral-3-3b` by 5.9 points) and the exclusion of unmeasurable verdicts
(`exception`, `replay_failed`). Loading each lane singly reproduces all six independently
computed rates:

| lane | reproduced | expected |
|---|---|---|
| deepseek-v3.1 | 0.441 | 0.441 |
| gemma-4-31b | 0.351 | 0.351 |
| qwen3.5-27b | 0.298 | 0.298 |
| exaone-4.5-33b | 0.160 | 0.160 |
| nemotron-3-nano-4b | 0.096 | 0.096 |
| ministral-3-3b | 0.066 | 0.066 |

All 21 lanes land at 712 measurable cells (944 − 232), except five at 711 —
`nemotron-3-nano-4b`, `glm-4.7`, `ministral-3-3b`, `ministral-3-14b`, `exaone-4.0-32b`.
That gap was checked rather than waved through, since the stated invariant is 712: each
of those five holds **exactly one cell whose only rows are `exception`**, a different
cell in each lane. **This fully accounts for the paired total** — five distinct cells
dropped from the 21-way intersection gives 712 − 5 = **707**.

These five are worth naming precisely, because they are *not* the same kind of thing as
the other unmeasurable cells and the exclusion rule was written for those. They are
**Lean verifier faults on model-specific candidates** — in three of the five,
`DojoTacticTimeoutError` after ~600 s of elaboration (e.g. `glm-4.7` on
`Submodule.iSup_toAddSubmonoid`, 9,413 completion tokens, an ordinary one-line
`exact AddSubmonoid.add_mem …`); in the other two (`nemotron-3-nano-4b`,
`ministral-3-14b`), `DojoCrashError: Unexpected EOF` on cap-length generations
[split corrected 2026-08-18 from the primary rows — the earlier "all five are
timeouts" read the two crash cells' stripped error strings as timeouts]. So unlike a spot-kill `exception` (never
reached the model) or `replay_failed` (provably model-independent — the identical 232
cells in all 21 lanes), these are **model-dependent**: five different cells in five
different lanes, where every other model's candidate on the same cell verified fine. The
model proposed a tactic that would not elaborate in budget.

**Scoring them 0 and dropping them are both defensible, and it does not matter
numerically** — one cell in 712 is 0.14 points, an order of magnitude below the narrowest
interval in this document. They are dropped here, as a consequence of the intersection.
Flagged so that a reader who counts cells and finds 711 in five lanes knows it is an
elaboration timeout rather than a hole in the data.

| lane | theorem | k | rung |
|---|---|---|---|
| nemotron-3-nano-4b | `Polynomial.natSepDegree_eq_natDegree_iff` | 1 | stepk:1 |
| glm-4.7 | `Submodule.iSup_toAddSubmonoid` | 15 | stepk:1 |
| ministral-3-3b | `IntermediateField.card_algHom_adjoin_integral` | 0 | hint:2 |
| ministral-3-14b | `CategoryTheory.GradedObject.ιMapObjOrZero_mapMap` | 2 | noise:3 |
| exaone-4.0-32b | `IntermediateField.card_algHom_adjoin_integral` | 0 | noise:3 |

**Pairing scope.** `load_joint_cells` keeps a cell only if it is graded for *every*
model requested, so loading all 21 at once yields the **21-way intersection**. That
intersection is **707 cells over 216 theorems — 99.3% of a lane's 712**, because
`deepseek-v3.1`'s 415 exception cells were repaired before the snapshot. Global pairing
therefore costs essentially nothing and is used for every contrast, so all contrasts
rest on the same cells. Per-lane marginals over each lane's own 712 are reported
alongside; the two differ by at most 0.002.

---

## 1. Induction — Holm–Bonferroni

**Family: 210 pre-registered PRIMARY contrasts** (84 ladder + 126 info-arm), FWER
α = 0.05, paired exact McNemar on item-matched marks. Pairing is the correct test here:
every model answers the same seeds with byte-identical prompts, and all four arms at a
given seed reuse the same queries and answers.

Every contrast runs at **n = 270 matched items** (30 seeds × 9 harmonics). All 21 lanes
closed at R=30 on 2026-08-16; the earlier unequal-R caveat for `ministral-3-14b` is
retired, not merely narrowed.

| test | procedure | rejected | uncorrected p<0.05 |
|---|---|---|---|
| paired | **Holm** | **125** | 148 |
| paired | Hochberg | 125 | 148 |
| unpaired (CMH) | Holm | 124 | 146 |

**Holm and Hochberg reject the identical set**, not merely the same count. The two share
critical values α/(m−i+1) and differ only in stepping direction, so they can diverge only
when a p-value fails its threshold and a *larger* one later passes its looser threshold.
Holm stops at rank 126 and nothing beyond it passes — there is a 2× gap at the boundary
(4.88e-04 → 9.77e-04) and the curves never re-cross. **Use Holm**: it is valid under
arbitrary dependence, while Hochberg's Simes/MTP2 assumption is unverified for 210
statistics sharing models, seeds and harmonics — and here it buys zero extra rejections.
This is a property of this dataset's bimodal p-value distribution, not a general identity.

Of the 125 rejections, **48 are scientific findings**; the rest are `zero`-arm positive
controls (significant by construction — a chance-floor baseline against arms at
0.60–1.00) and quarantined-lane contrasts.

**Not significant: 57 of 105 non-control contrasts — and 48 of those are ceiling pairs**
(both arms ≥ 0.95), many with *zero* discordant items. These are ties by construction,
not underpowered: no replicate count separates two arms that never disagree on a single
item.

### 1.1 The information-vs-length contrast (`extens` vs `noise_intens`)

Both arms are token-matched — `noise_intens` is the compact rule padded with whitespace
to exactly the extensional listing's token count under the model's own tokenizer — so
this contrast holds prompt **length** fixed and varies only whether the tokens carry
information.

Under the primary m=210 correction, **10 of 21 are significant. Five of those are
quarantined or contaminated, so the finding rests on 5 clean lanes — and all 5 point the
same way:**

| model | extens | noise | direction | p |
|---|---|---|---|---|
| nemo3_4b | 0.396 | 0.719 | noise higher | 1.74e-11 |
| nemo3_30b | 0.711 | 0.937 | noise higher | 9.63e-11 |
| nemo3_120b | 0.841 | 0.996 | noise higher | 5.12e-12 |
| gemma4_e2b | 0.115 | 0.981 | noise higher | 1.29e-67 |
| exaone_236b | 0.641 | 0.978 | noise higher | 6.58e-23 |

**Length is not the explanation.** At a byte-matched prompt length, models do
*substantially better* when the padding is meaningless whitespace than when it is a full
enumeration. Enumerated evidence is harder to induce from than a stated rule; the
extensional arm's difficulty is label density, not prompt length. Direction among clean
significant results: **5 noise-higher, 0 extens-higher.**

**The counter-example, stated rather than buried.** "5 noise-higher, 0 extens-higher" is
true *conditional on significance*, and that conditioning is doing work. The
sixth-ranked clean lane runs the other way:

| model | extens | noise | direction | p |
|---|---|---|---|---|
| glm_47 | 0.889 | 0.789 | **extens higher** | 2.44e-03 |

`glm_47` is **not** quarantined and **not** ≥25% non-compliant — it is a clean lane whose
extensional arm beats its noise arm, and it fails only the m=210 family threshold
(2.44e-03 vs the ~5.9e-04 Holm threshold at the boundary rank — 0.05/(210−126+1); the oft-quoted 2.4e-04 is the Bonferroni floor, which binds only for the family's smallest p). Re-correcting at m=21 would admit it, along
with `glm_air` (which *is* quarantined). So the directional claim is: among lanes that
clear the pre-registered threshold the effect is unanimous, but the strongest lane just
below the line points the other way. This study's own record — the `gpt-oss`
opposite-ends crossover that the pilot mistook for a general result — is a warning
against reading unanimity off a significance-filtered set.

Re-sizing a family to a subset chosen after seeing the data is not a valid primary
analysis, so m=21 is reported as sensitivity only.

---

## 2. Deduction — block-bootstrap error bars

### 2.1 Why the resampling unit is a theorem

A cell is one `(theorem_id, k, prompt_rung)` triple, and each theorem contributes ~3.3
cells sharing a ground truth and a proof prefix. Those cells are not independent: a
theorem the model cannot do fails at every rung. Resampling **cells** would treat
correlated observations as fresh information and understate every interval, so whole
**theorem blocks** are resampled with replacement.

**The effective sample size is 216 theorem blocks, not 707 cells.** Measured
consequence: the block-bootstrap intervals are **1.38× (median) the width** a naive
binomial on 707 independent cells would give, range 1.16–1.45×. Treating cells as
independent would overstate precision by that factor.

Intervals are **BCa** (bias-corrected and accelerated, jackknife over blocks), which
matters for the near-floor lanes where the resample distribution is right-skewed. No
lane needed the percentile fallback.

### 2.2 Choosing B by measurement

Monte-Carlo drift across independent RNG streams, max over all 21 marginal interval
endpoints:

| B | max drift (pts) | median drift |
|---|---|---|
| 5,000 | 0.00619 | 0.00153 |
| 20,000 | 0.00404 | 0.00075 |
| 50,000 | 0.00121 | 0.00029 |
| 100,000 | 0.00067 | 0.00018 |
| 200,000 | 0.00072 | 0.00021 |
| **500,000** | **0.00038** | 0.00009 |

Tolerance is 0.0005 points — rates are reported to 3 decimals, so drift below half a
thousandth cannot change a printed figure. **B = 500,000** is the first grid point under
it, and is what every number below uses. The full sweep costs 12 seconds.

### 2.3 pass@1 with 95% CIs

| model | pass@1 | 95% BCa | width |
|---|---|---|---|
| qwen3.5-27b | 0.298 | [0.253, 0.347] | 0.094 |
| qwen3.5-122b-a10b | 0.348 | [0.298, 0.400] | 0.101 |
| qwen3.5-397b-a17b | 0.393 | [0.342, 0.445] | 0.103 |
| nemotron-3-nano-4b | 0.096 | [0.073, 0.125] | 0.052 |
| nemotron-3-nano-30b-a3b | 0.041 | [0.027, 0.061] | 0.034 |
| nemotron-3-super-120b-a12b | 0.164 | [0.131, 0.202] | 0.072 |
| gemma-4-e2b | 0.110 | [0.082, 0.147] | 0.065 |
| gemma-4-12b | 0.184 | [0.146, 0.227] | 0.082 |
| gemma-4-31b | 0.352 | [0.303, 0.403] | 0.100 |
| glm-4.7-flash | 0.147 | [0.117, 0.181] | 0.064 |
| glm-4.5-air | 0.216 | [0.175, 0.263] | 0.088 |
| glm-4.7 | 0.362 | [0.315, 0.410] | 0.096 |
| ministral-3-3b | 0.066 | [0.045, 0.095] | 0.051 |
| ministral-3-8b | 0.074 | [0.054, 0.099] | 0.045 |
| ministral-3-14b | 0.103 | [0.075, 0.138] | 0.062 |
| exaone-4.0-32b | 0.182 | [0.146, 0.225] | 0.079 |
| exaone-4.5-33b | 0.161 | [0.131, 0.196] | 0.065 |
| k-exaone-236b-a23b | 0.105 | [0.079, 0.135] | 0.056 |
| deepseek-v4-flash | 0.349 | [0.302, 0.398] | 0.096 |
| deepseek-v3.1 | 0.440 | [0.389, 0.490] | 0.101 |
| deepseek-v4-pro | 0.406 | [0.358, 0.454] | 0.096 |

Marginal intervals are wide (±0.05 at mid-range) because 216 blocks is the real n.
**Contrast intervals are much tighter** — median width 0.072, max 0.093 — because the
difference is taken *inside* each resample, so a draw of hard theorems lowers both models
together and cancels. This is the payoff of the paired design, and it is why 17 of 21
ladder contrasts separate despite overlapping marginal bars. **Overlapping marginal CIs
in the table above do not imply a null contrast**; read the contrast intervals.

### 2.4 Ladder contrasts — 17 of 21 significant under Holm

Scaling holds cleanly in **3 of 7 families** — qwen3.5, gemma-4 and GLM, where every
rung-pair is positive and Holm-significant. The other four each break monotonicity in a
different way.

**DeepSeek rises then stops:** `deepseek-v4-flash` → `deepseek-v3.1` is +0.091 (Holm) and
→ `deepseek-v4-pro` is +0.057 (Holm), but the top rung-pair `deepseek-v3.1` vs
`deepseek-v4-pro` is **−0.034 [−0.072, +0.004]**, negative and not significant. Two of
its three rung-pairs separate, not three.

**EXAONE inverts — bigger is monotonically worse:**

| contrast | diff | 95% BCa | Holm |
|---|---|---|---|
| exaone-4.0-32b vs exaone-4.5-33b | −0.021 | [−0.055, +0.013] | . |
| exaone-4.0-32b vs k-exaone-236b-a23b | **−0.078** | [−0.114, −0.044] | yes |
| exaone-4.5-33b vs k-exaone-236b-a23b | **−0.057** | [−0.086, −0.029] | yes |

**Nemotron-3 is non-monotone (V-shaped)** — the mid rung is significantly *worse* than
the small rung, then the large rung recovers past both:

| contrast | diff | 95% BCa | Holm |
|---|---|---|---|
| nano-4b vs nano-30b-a3b | **−0.055** | [−0.084, −0.029] | yes |
| nano-4b vs super-120b-a12b | **+0.068** | [+0.037, +0.101] | yes |
| nano-30b-a3b vs super-120b-a12b | **+0.123** | [+0.093, +0.158] | yes |

**Ministral-3 is flat**: 0.066 → 0.074 → 0.103, only the 3b-vs-14b endpoint contrast
(+0.037) survives Holm; adjacent rungs do not separate.

Holm rejections by family: qwen3.5 3, gemma-4 3, GLM 3, Nemotron-3 3, DeepSeek 2,
EXAONE 2, Ministral-3 1 = **17 of 21**. Note that Nemotron-3's three include a
*negative* rung, so "all three separate" is not the same as "scales cleanly."

Both results survived the hardware audit, which matters because they are the two a reader
would most reasonably suspect of being a serving artifact: all three EXAONE rungs are
single-configuration lanes, and `nemotron-3-nano-4b` was fully re-run on one
`g6e.4xlarge` in a single process — the only internally bit-reproducible lane in the
study — precisely so its number could not be blamed on mixed hardware.

A tempting reading is that *active* rather than total parameters drive this — both
inverted top rungs are low-active MoEs (`k-exaone-236b-a23b` 23B active vs a 32B dense
sibling; `nano-30b-a3b` 3B active vs a 4B dense sibling, and the Nemotron ladder's scores
order exactly as 3B < 4B < 12B active). **But qwen3.5 contradicts it**: its 10B-active
122b beats its 27B-dense sibling. Stated as a hypothesis the data is consistent with in
two families and inconsistent with in a third — not a conclusion.

**Holm vs the raw CI agree on 20 of 21.** The one disagreement (ministral-3-8b vs
ministral-3-14b, +0.030 [+0.003, +0.060]) is exactly what multiplicity control is for:
an interval that just excludes zero, in a family of 21.

### 2.5 Secondary tier — cross-family, size-matched

63 contrasts, pre-registered at Benjamini–Hochberg q = 0.05 (exploratory, so FDR rather
than FWER). **BH rejects 56 of 63**, identical to both the uncorrected p<0.05 count and
the count of CIs excluding zero — the cross-family effects are large enough that the
correction is not binding at this tier. BH runs inside `error_bars.py --mode report`, so
this figure regenerates with the rest.

For contrast, at the PRIMARY tier Holm *is* binding: 17 rejections against 18
uncorrected. The single contrast it removes (ministral-3-8b vs ministral-3-14b, +0.030
[+0.003, +0.060]) is exactly what multiplicity control is for.

---

## 3. Caveats that belong in any write-up of these numbers

1. **`ministral-3-14b`: the re-collection REMOVED a survivorship bias — it did not add an
   inhomogeneity.** All 21 lanes closed at R=30 and every contrast runs at n=270, so the
   unequal-R caveat is retired. Seeds 19 and 24–29 originally failed on a silent
   non-streaming socket that dropped **cap-length** response bodies, and were recovered
   with `EC2_STREAM_COMPLETIONS=1` — same hardware pin, same sampling parameters,
   different transport, cross-transport equality verified live.

   The tempting framing is "7 of 30 seeds differ, priced as noise." **That framing is
   wrong, and the empty-response profile shows why** (verified independently here):

   | arm | pre-fix 23 seeds | re-collected 7 | delta |
   |---|---|---|---|
   | `intens` | 11.1% empty | 61.9% | **+50.8 pt** |
   | `extens` | 36.2% | 79.4% | **+43.1 pt** |
   | `zero` | 14.0% | 50.8% | **+36.8 pt** |
   | `noise_intens` | 0.5% | 0.0% | −0.5 pt |

   The lift is confined to exactly the arms whose draws run to the token cap; the noise
   arm, which does not, is **identical across the two groups**.

   **The mechanism is EXCLUSION, not survivorship**, and the landing timestamps settle it.
   Seeds 0–8 landed 08-11/12; seeds 9–18 and 20–23 landed 07:17–10:46Z on 08-14; the
   delivery fault began ~13:48Z. **Zero of the 23 old seeds landed after fault onset** —
   that cohort was never filtered by the fault, it simply ran first. What makes the 7
   missing seeds special is intrinsic: server counters from inside the fault window show
   the boxes serving exactly seeds 19/24–29, on the *old* builds, at `length:stop ≈ 28:13`
   (~68% cap-length), matching the 62–79% those seeds show today on the new build. Their
   cap-out propensity predates the rebuild and is *why* they could not finish inside the
   fault window.

   So the correct statement is **missing-not-at-random**: an R=23 lane omitting them is
   biased toward answered cells, and R=30 removes that bias. The valence is unchanged —
   the re-collection is a correction, not an inhomogeneity — but it is exclusion bias, not
   survival of a filter.

   *Correcting an overclaim made in an earlier draft of this document:* the flat noise arm
   does **not** make this "the only reading consistent with the data." It excludes
   arm-uniform mechanisms, but a length-mediated per-process or build shift would also
   spare the noise arm. What excludes the build/regime reading is the fault-window counters
   above, plus the observation that the two pre-fix cohorts sit within a few points of each
   other (`intens` 13.6% vs 9.5% empty) *across two hardware families and two builds* — era
   drift does not produce shifts of this size here. **Cite the counters as the pin, not the
   noise row.** Residual limit: the marks carry no `finish_reason`, so this rests on
   server-side counters rather than per-mark evidence.

   > This lane's contrasts moved most on closing:
   > `[min3 ladder | extens] min3_8b vs min3_14b` went 6.36e-04 → 5.85e-06 across the
   > rule change and the seed completion together. Its `extens` arm is 84% non-compliant,
   > so those contrasts are flagged `[!]` regardless.

2. **SCOPE: the deduction leg measures Mathlib only, not Lean's standard library.**
   The unusable theorems are not a random subset. Of the 300 theorems, the 45 that
   LeanDojo could never open are **100% `.lake/packages/std/`**, and all **218**
   measurable theorems are **100% `Mathlib/`** — complete separation, verified directly
   from `file_path` on the collected rows:

   | theorem set | count | source |
   |---|---|---|
   | measurable | 218 | Mathlib 218 / std 0 |
   | unmeasurable | 82 | Mathlib 37 (prefix-replay) / std 45 (DojoInit) |

   So every deduction number in this document is a statement about **next-tactic
   prediction on Mathlib**. It is a scope restriction and nothing more should be read
   into it: no model ever attempted those 45 under a verifiable setup, so there is no
   success rate on them to compare and none is recoverable from the collected data.
   **[Superseded 2026-08-18: 34 of the 45 WERE recovered post-hoc** — the candidates
   were always in the collected rows; only their *verification* had failed (an
   incomplete LeanDojo cache), so verification-only compute recovered them. The other
   11 close their goal before step k and join the prefix class. See caveat 12 and
   `DOJOINIT_RECOVERY_2026-08-18.md`.]
   Proof length happens to match (3.04 vs 3.05 tactics, p=1.00), but that does **not**
   license "and they are no harder."

3. **24.6% of the deduction cells (27.3% of theorems: 82 of 300) are unusable for everyone.** The same **232
   cells** fail in every one of the 21 lanes — 151 where LeanDojo could not open the
   theorem (missing `*.ast.json`) and 81 where the *ground-truth* prefix would not
   replay. 100% overlap across models proves this is not model behaviour. They are
   excluded, never scored 0; scoring them 0 would deflate every marginal rate by up to
   24.6%. Uniform across models, so **no bias — but real lost power**: the measurable
   denominator is 712 cells / 218 theorem blocks per lane (707 cells / 216 blocks in
   the 21-way paired analysis; two lanes are 217 because their exception-only cell
   consumes a whole theorem), not 944. **[Post-recovery accounting, 2026-08-18: the
   232 shrink to 111 — 151 DojoInit cells → 0 — see caveat 12.]**

4. **Induction hardware attribution is MOSTLY inferred — and the split has a date.**
   Per-object `server_config` stamping landed at **02:06:44Z on 2026-08-14** (`040d2e83`).
   Objects written before it carry `date` / `marks` / `model` and nothing else; objects
   written after carry a full `server_config` block with instance type, instance id and
   GPU. Verified on the analyzed tree: `ministral-3-14b` seeds 0–8 have no block, seeds
   9–29 do.

   | analyzed objects | hardware provenance |
   |---|---|
   | ~2,436 of 2,520 | **fleet-log-inferred** from run timestamps |
   | `ministral-3-14b` seeds 9–29 (84 objects) | **object-carried** |

   Among the 140 duplicates: no `gemma-4-12b` or `deepseek-v4-flash` attempt carries the
   block in *either* version — both lanes' newest attempts finished 01:48Z and 01:55Z,
   missing stamping by 18 and 11 minutes — while `ministral-3-14b` seeds 0–8 carry it only
   in the *unanalyzed* newest attempt. So for every duplicated cell the analyzed object is
   unstamped, and the mixed-instance-type claims below are inferences, near-certain but
   inferences.

   > **How both sides of this got it wrong, since the lesson generalises.** An earlier
   > draft of this document asserted that *no* induction object carries hardware fields,
   > generalising from one duplicated cell; the collection side asserted that only the
   > newest attempts do. Each sample falsified the other's generalisation, and neither was
   > right. The sampled cell (`gemma-4-12b` seed 8) happened to straddle nothing — both its
   > versions predate stamping by minutes. **Date the commit that introduced the field
   > before generalising from any sample of objects written around it.**

   Related: the count of vLLM builds serving the study is a count of *recorded* builds — at
   least one re-collection's boxes logged no version string, so the true number is a lower
   bound, not a total. (The 2026-08-16 determinism probe recorded its build —
   `0.27.2rc1.dev122+g8efa13b70`, the sixth known — which is the practice the rest of the
   study should have followed.)

5. **The decontamination re-runs are in the log but invisible to this analysis.** Under
   earliest-wins, the three multi-attempt lanes (`gemma-4-12b`, `deepseek-v4-flash`,
   `ministral-3-14b`) are analysed on their **pre-re-collection** attempts. Those
   re-collections were run specifically to remove hardware mixing, so the analysed data
   for those lanes is the mixed-instance-type version and the compute spent on
   decontaminating them does not appear in any number here. This is a direct consequence
   of the selection ruling, priced as noise rather than bias on the strength of the
   cross-process determinism measurement in the next item. Stated explicitly because a
   reader who knows the re-runs happened will look for them, and should find this
   paragraph rather than conclude they were forgotten.

6. **Per-process nondeterminism is a study-wide noise term.** vLLM output here is
   reproducible *within* one server process **for some model×config pairs** —
   `nemotron-3-nano-4b` 8/8 byte-identical, but `ministral-3-3b` 0/8 even back-to-back
   on one box under the stock config — and **bimodal across processes**: 8/8 in one of
   six archived pairings, 0/8 in four (do not treat 0/8 as "the" cross-process rate;
   `DETERMINISM_PLAN_2026-08-16.md` §0/§7.4). Nearly every lane
   spans several boxes — `ministral-3-14b` ×48, `gemma-4-12b` ×21, `glm-4.7-flash` ×4.
   Because every lane runs on its own hardware by design, this does **not** correlate
   with the model axis: it is noise, not bias, and re-runs cannot remove it. Do not
   chase it.

   The 8/8 within-process figure is **genuine kernel determinism, not prefix-cache
   replay** — the obvious alternative explanation, since pass 2 could simply be replaying
   pass 1 from cache. Tested directly: the stock configuration logged 3,904 prefix-cache
   hits, and a caching-off configuration logged 0 queries and 0 hits *and still scored
   8/8*. The noise floor stands without a caveat.

7. **`nemotron-3-nano-4b`'s deduction leg is the only internally bit-reproducible lane**
   (fully re-run on one box). Its induction leg is still mixed (`g6e.4xlarge` +
   `g6e.8xlarge`). `ministral-3-3b` is mixed on both legs by decision.

   > **Correction — `ministral-3-3b` is not an irreproducible model.** An earlier version
   > of this document reported its same-box baseline as 0/8 and concluded that
   > contamination there was "undetectable *and* unfixable by re-running," implying a
   > property of the model. A direct test refutes that: **stock 0/8, determinism
   > configuration 8/8** (`--no-enable-prefix-caching --max-num-seqs 1 --enforce-eager
   > --seed 0`). The 0/8 was the *serving configuration*, not the model. The stock 0/8
   > also occurred at strictly sequential client concurrency, so the cause is the config
   > itself — CUDA graphs, scheduling, cache path — and not batching.
   >
   > What does **not** change: the lanes were collected under the stock configuration, so
   > the within-lane nondeterminism in the *collected data* is real as collected. Only the
   > model-property claim was wrong. Correct phrasing going forward:
   > *nondeterministic under the study's serving configuration; fully deterministic under
   > caching-off / `max-num-seqs 1` / eager / fixed seed.*
   >
   > Scope limit on all of this: cross-configuration agreement is **0/8 on both models**,
   > same box and same seed. Determinism holds within one process × one configuration —
   > it does not survive a config change, so re-collecting a lane under the determinism
   > config would make it internally reproducible while making it incomparable to the
   > other twenty.

8. **`deepseek-v3.1`'s 415 repaired cells came from a different box than its original
   529**, unavoidably (see 6). This is why its lane nonetheless reaches a full 712
   measurable cells.

9. **Six `noise_intens` lanes are quarantined for output-contract collapse**, not low
   accuracy: `exaone_32b`/`exaone_33b` at acc 0.000 with total generative collapse,
   `glm_flash` 48.9% empty, `min3_8b`/`min3_14b` 100% non-compliant, `glm_air` 17.8%
   empty. Contrasts involving them measure whitespace-padding-induced degeneration, not
   induction, and are reported separately from the findings. 16 of 84 cells (including the six quarantined noise arms — so 10 genuinely further) are
   ≥25% non-compliant; findings touching them are flagged `[!]` in the report, because
   the mechanism may be format collapse rather than task difficulty.

10. **`glm_flash` has 132/270 empty completions** on a 110-token prompt against an 86,751
   token budget — an infrastructure symptom, not truncation, and it has not been
   investigated.

11. **[2026-08-18] The deduction leg's cross-process noise term is now MEASURED on one
   lane, not qualitative.** For `nemotron-3-nano-4b` — the study's *most stable* lane
   (caveat 7), so plausibly a lower bound elsewhere — the per-cell score flip
   probability across serving processes is **9.5%** (95% CI [5.8%, 14.4%], n = 200
   paired cells; the ±2.1-point figure is the 1-SE width of that rate estimate at
   n = 200, likely too narrow since sampled cells share theorems). On a full 712-cell
   lane this implies roughly **±1.2 points of process-swap SD on pass@1**. Verifier
   drift was 200/200 exact, so every flip is generation, not grading; and 178/200
   (89%) of the re-generations differ in text while only 9.5% flip score — byte
   agreement is the wrong metric for what this study measures. Noise, not bias:
   process identity is assigned by spot capacity and does not correlate with the
   model axis. Two scope cautions: the rerun landed on a g6e.2xlarge in us-west-2
   (the lane's own g6e.4xlarge fleet was dry; both boxes carry exactly one L40S,
   enforced by pin), and it pinned image+checkpoint where the study's own build is
   unrecoverable — so 9.5% upper-bounds the pure process term. Full design and data:
   `DETERMINISM_PLAN_2026-08-16.md` §6.

12. **[2026-08-18] The 151 DojoInit std cells per lane were recovered — as a SCOPE
   EXTENSION, not a headline change.** Every number in this document stands on the
   Mathlib-only 712/711 denominators, unchanged. The recovery (root cause: an incomplete
   LeanDojo cache on the grading box; 30/30 exact control-cell gate; strictly additive —
   study S3 objects untouched) adds 121 measurable cells per lane under a separate
   `dojoinit_recovery_2026-08-18/` prefix, moving the PER-LANE extended denominators
   to 833/832 (218→252 blocks per lane; 217→251 in `glm-4.7` and `nemotron-3-nano-4b`)
   and this document's own 21-way PAIRED pools from 707 cells / 216 blocks to
   **828 cells / 250 blocks**. Any analysis that pools the extension must say so and
   carry its caveats: `DOJOINIT_RECOVERY_2026-08-18.md`.

13. **[2026-08-18] The stock-config epoch closed after this study.** The serving defaults
   are now the hinge-certified determinism bundle plus digest/revision pins
   (`DETERMINISM_PLAN_2026-08-16.md` §4 ADOPTED). Cross-config agreement is 0/8, so any
   future run under the new defaults is config-incomparable with every number here.

---

## 4. Reproducing

```bash
# induction — Holm over the 210-contrast primary family
uv run --no-project --with numpy --with scipy python notebooks/induction/significance_report.py
uv run --no-project --with numpy --with scipy python notebooks/induction/extens_vs_noise.py

# deduction — pick B by measurement, then report
uv run --no-project --with numpy --with scipy python notebooks/deduction/error_bars.py \
    --rows-dir <dir-of-verified_rows> --mode sweep
uv run --no-project --with numpy --with scipy python notebooks/deduction/error_bars.py \
    --rows-dir <dir-of-verified_rows> --mode report -B 500000
```

`<dir-of-verified_rows>` is a directory of `<model>/verified_rows.jsonl`, fetched from
`s3://smolbench-results-414266451290/analysis/2026-08-16/deduction/`. Use
`verified_rows.jsonl`, never `all_rows.jsonl` — the latter is pre-verification
candidates, and the loader prints a loud banner if it sees one.
