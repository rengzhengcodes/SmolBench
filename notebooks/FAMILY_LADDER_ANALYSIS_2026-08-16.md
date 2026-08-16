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

**Induction — the local tree is current.** Three lanes hold two files per cell
(`gemma-4-12b` 176 objects, `deepseek-v4-flash` 168, `ministral-3-14b` 128, against a
120 baseline); the extras are deliberate decontamination re-collections, and the
correct rule is **newest run-timestamp per cell** — the opposite of the deduction rule
in the next paragraph. Every cell's newest snapshot version was compared against the
local file **by size**, and the `gemma-4-12b` seed=8 `extens` pair (922,083 vs
1,319,921 bytes) confirms size discriminates the versions that matter:

| check | result |
|---|---|
| snapshot cells (newest per cell) | 2,492 |
| local matches newest, by size | **2,492** |
| missing locally | 0 |
| stale locally | 0 |

2,492 = 21 × 4 × 30 − 28, the 28 being `ministral-3-14b`'s seven abandoned seeds.
A byte-level `md5` on the `gemma-4-12b` seed=8 pair confirms the local file is the
**newer** version. The committed Holm numbers therefore rest on current data.

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

All 21 lanes land at 712 measurable cells (944 − 232), except five at 711.

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

| test | procedure | rejected | uncorrected p<0.05 |
|---|---|---|---|
| paired | **Holm** | **123** | 144 |
| paired | Hochberg | 123 | 144 |
| unpaired (CMH) | Holm | 122 | 143 |

**Holm and Hochberg reject the identical set**, not merely the same count. The two share
critical values α/(m−i+1) and differ only in stepping direction, so they can diverge only
when a p-value fails its threshold and a *larger* one later passes its looser threshold.
Holm stops at rank 124 and nothing beyond it passes — there is a 2× gap at the boundary
(4.88e-04 → 9.77e-04) and the curves never re-cross. **Use Holm**: it is valid under
arbitrary dependence, while Hochberg's Simes/MTP2 assumption is unverified for 210
statistics sharing models, seeds and harmonics — and here it buys zero extra rejections.
This is a property of this dataset's bimodal p-value distribution, not a general identity.

Of the 123 rejections, **46 are scientific findings**; the rest are 57 `zero`-arm
positive controls (significant by construction — a chance-floor baseline against arms at
0.60–1.00) and 20 quarantined-lane contrasts.

**Not significant: 59 of 105 non-control contrasts — and 48 of those are ceiling pairs**
(both arms ≥ 0.95), many with *zero* discordant items. These are ties by construction,
not underpowered: no replicate count separates two arms that never disagree on a single
item.

### 1.1 The information-vs-length contrast (`extens` vs `noise_intens`)

Both arms are token-matched — `noise_intens` is the compact rule padded with whitespace
to exactly the extensional listing's token count under the model's own tokenizer — so
this contrast holds prompt **length** fixed and varies only whether the tokens carry
information.

Under the primary m=210 correction, **10 of 21 are significant. Six of those are
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

Re-correcting at m=21 would add 2 more (glm_air, glm_47) — but both are
quarantined/borderline, and re-sizing a family to a subset chosen after seeing the data
is not a valid primary analysis. It is reported as sensitivity only.

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

Scaling holds cleanly in **4 of 7 families** (qwen3.5, gemma-4, GLM, DeepSeek): every
rung-pair positive and Holm-significant. The other three are the finding.

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
correction is not binding at this tier.

---

## 3. Caveats that belong in any write-up of these numbers

1. **`ministral-3-14b` induction ships at R=23, not R=30.** Seeds 19 and 24–29 were
   abandoned: cap-length responses were undeliverable to the collecting host, a fault
   that survived reverting every client change. All other 20 lanes are R=30. `aligned()`
   intersects seeds, so contrasts touching this lane run at **n=207** rather than 270 —
   validly paired, but model-level tables mix denominators. Contrast n is reported as a
   range (207–270) rather than a single figure.

2. **24.6% of the deduction theorem set is unusable for everyone.** The same **232
   cells** fail in every one of the 21 lanes — 151 where LeanDojo could not open the
   theorem (missing `*.ast.json`) and 81 where the *ground-truth* prefix would not
   replay. 100% overlap across models proves this is not model behaviour. They are
   excluded, never scored 0; scoring them 0 would deflate every marginal rate by up to
   24.6%. Uniform across models, so **no bias — but real lost power**: the measurable
   denominator is 712 cells / 216 theorem blocks, not 944.

3. **Per-process nondeterminism is a study-wide noise term.** vLLM output here is
   reproducible *within* one server process (8/8 byte-identical) and **not across
   processes** (0/8, at identical instance type, GPU, tp and image). Nearly every lane
   spans several boxes — `ministral-3-14b` ×48, `gemma-4-12b` ×21, `glm-4.7-flash` ×4.
   Because every lane runs on its own hardware by design, this does **not** correlate
   with the model axis: it is noise, not bias, and re-runs cannot remove it. Do not
   chase it.

4. **`nemotron-3-nano-4b`'s deduction leg is the only internally bit-reproducible lane**
   (fully re-run on one box). Its induction leg is still mixed (`g6e.4xlarge` +
   `g6e.8xlarge`). `ministral-3-3b` is mixed on both legs by decision — its same-box
   baseline is 0/8, so contamination there is undetectable *and* unfixable by re-running.

5. **`deepseek-v3.1`'s 415 repaired cells came from a different box than its original
   529**, unavoidably (see 3). This is why its lane nonetheless reaches a full 712
   measurable cells.

6. **Six `noise_intens` lanes are quarantined for output-contract collapse**, not low
   accuracy: `exaone_32b`/`exaone_33b` at acc 0.000 with total generative collapse,
   `glm_flash` 48.9% empty, `min3_8b`/`min3_14b` 100% non-compliant, `glm_air` 17.8%
   empty. Contrasts involving them measure whitespace-padding-induced degeneration, not
   induction, and are reported separately from the findings. A further 16 of 84 cells are
   ≥25% non-compliant; findings touching them are flagged `[!]` in the report, because
   the mechanism may be format collapse rather than task difficulty.

7. **`glm_flash` has 132/270 empty completions** on a 110-token prompt against an 86,751
   token budget — an infrastructure symptom, not truncation, and it has not been
   investigated.

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
