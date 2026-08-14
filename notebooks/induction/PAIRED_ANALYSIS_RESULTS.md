# Paired re-analysis of the landed induction study — results, 2026-08-14

Run of `notebooks/induction/paired_analysis.py`, which implements §2.1 and §2.2 of
`MULTIPLICITY_PLAN.md` against the marks already collected. 84 conditions, R = 30 on
20 of 21 lanes (`min3_14b` at 23, compared on its common seeds only). No new data
collection.

Companion to `POWER_ANALYSIS_2026-08-14.md` (prospective sizing). This document is
retrospective: it tests the contrasts, it does not size them.

**Merged narrative, agreed across two sessions.** Provenance is marked per claim rather
than presented as jointly verified, because only some of it was checked twice:

| claim | computed by | independently reproduced? |
|---|---|---|
| paired-vs-unpaired rejection counts, DE measurement | this session | **no** |
| R = 78 sizing run, CONFOUND_AUDIT clearance | `smolbench-d7` | **no** |
| the 21 × 4 non-compliance sweep | both, separately | **yes — matched exactly** |
| regrade dry-run, response-level diagnosis | this session | **no** |

---

## Headline: pairing is the right test and it changes almost nothing

Rejections at FWER 0.05 over the 210 PRIMARY contrasts:

| test | Bonferroni | Holm |
|---|---|---|
| unpaired CMH (what `power_analysis.py` plans) | 121 | 122 |
| paired exact McNemar (what the design supports) | 120 | **123** |

**Exactly one contrast changes status:** `[nemo3 ladder | intens] nemo3_30b vs
nemo3_120b` (0.956 vs 1.000; p_paired 4.9e-4 vs p_unpaired 9.2e-4). Dropping
item-pairs where either arm is invalid gives the same picture (118 paired vs 117
unpaired). Tier 3 returns 40 discoveries under either test.

### Why `MULTIPLICITY_PLAN.md` over-promised

That document predicted up to a **53× power gain** from pairing. The prediction was
sound for the regime it simulated and wrong about the regime this study produced.

The design effect for a matched binary contrast is `DE = 2pq / d`, where `d` is the
observed discordance rate — so pairing pays most when discordance is *low but nonzero*.
The simulation swept ρ ∈ {0, 0.3, …, 0.9} and never modelled `d = 0`. The actual ceiling
pairs have **exactly zero discordant items**: `qwen35_27b`, `qwen35_397b`, `gemma4_31b`
and `ds_v31` all sit at 1.000 vs 1.000 with b/c = 0/0. No test extracts signal from zero
discordance, so there is nothing for pairing to recover.

**The recommendation stands, the justification changes.** Adopt the paired test because
it is the correct test for a matched design, it is free, and it is what the deduction leg
already does — not because it will rescue the near-ties. It will not.

**Consequence for sizing:** `POWER_ANALYSIS_2026-08-14.md` deferred its R = 78 headline
pending this re-analysis. The re-analysis does not move the difference claims, so that
document's framing stands unchanged: R = 30 is adequate for difference claims, and the
only open R question is the equivalence bound (±0.20 at R = 30, ±0.15 at R = 49). The
earlier suggestion that pairing would close the gap on its own is **withdrawn**.

---

## Clustering: measured, and much smaller than the bracket

`MULTIPLICITY_PLAN.md` §2.2 said the sign of the cross-stratum covariance CMH omits was
measurable from these data and had to be measured before anything else was believed.
Measuring `Var(per-seed total arm difference) / Σₖ Varₖ` over the 196 measurable PRIMARY
contrasts:

| median | mean | p10 | p90 | max | frac > 1.0 | frac > 1.5 |
|---|---|---|---|---|---|---|
| 1.124 | 1.279 | 0.869 | 1.881 | 2.969 | 0.602 | 0.235 |

**The sign is settled: mildly-to-moderately anticonservative.** The seed × arm
interaction dominates, as expected, but the effect is ~1.1–1.9×, not the 56× worst case
the simulation bracketed. Worth fixing with replicate-level resampling; not a reason to
distrust the landed results.

---

## The finding that actually matters: the noise arm is a compliance artifact

`intens` vs `noise_intens` separates at Bonferroni for **seven** models — the exact
opposite of every prior study's "separated for no model". That result is mostly not real.

Every mark carries a `compliance` field. Share of the 270 marks with a non-null
compliance value, `intens` → `noise_intens`:

| model | non-compliant | accuracy | dominant failure modes (noise arm) |
|---|---|---|---|
| exaone_32b | 0.0% → **99.6%** | 0.889 → **0.000** | multiple-values 213, prefixed 25, unparseable 16 |
| exaone_33b | 0.0% → **99.6%** | 0.996 → **0.000** | multiple-values 249, unparseable 6, markup 4 |
| min3_8b | 78.9% → **100.0%** | 0.789 → 0.215 | multiple-values 247, degenerate-repetition 6 |
| min3_14b | 56.5% → **100.0%** | 0.502 → 0.039 | multiple-values 176, degenerate-repetition 25 |
| glm_flash | 0.4% → **60.0%** | 0.289 → 0.122 | empty 132, multiple-values 17 |
| glm_air | 0.0% → **30.7%** | 0.970 → 0.607 | empty 48, multiple-values 31 |

An accuracy of 0.000 at 99.6% non-compliance is not a reasoning result — it is the model
coming apart under whitespace padding. This is the failure the noise-arm record describes
as **"UNUSABLE, not acc 0.000"**. (The precise mechanism differs by lane, and it is *not*
the recoverable formatting problem a compliance-aware regrade fixed on chromatic — see
"The regrade is already applied" below.)

**Quarantine those six.** The reportable noise finding is what survives with a clean arm:

| model | non-compliant | accuracy | p_paired | status |
|---|---|---|---|---|
| **glm_47** | 0.0% → 0.4% | 0.959 → 0.789 | 3.2e-10 | **genuine, survives Bonferroni** |
| exaone_236b | 0.0% → 0.0% | 1.000 → 0.978 | 0.031 | genuine, uncorrected only |
| nemo3_4b | 0.0% → 0.0% | 0.633 → 0.719 | 0.011 | noise *better*, uncorrected only |

So the honest headline is **one model with a clean Bonferroni-surviving noise effect
(glm_47), not seven** — and one model where the noise arm scores *higher*.

### Non-compliance is a study-wide, arm-crossing confound

Not only Ministral and not only the noise arm. Every cell at ≥25% non-compliance, from a
full 21 × 4 sweep (computed independently in both sessions, matching exactly):

| model | arm | non-compliant | acc | seeds |
|---|---|---|---|---|
| min3_8b | noise | 100.0% | 0.215 | 30 |
| min3_14b | noise | 100.0% | 0.039 | 23 |
| exaone_32b | noise | 99.6% | 0.000 | 30 |
| exaone_33b | noise | 99.6% | 0.000 | 30 |
| min3_14b | **extens** | 82.6% | 0.092 | 23 |
| min3_8b | **intens** | 78.9% | 0.789 | 30 |
| min3_8b | **zero** | 67.8% | 0.007 | 30 |
| glm_flash | noise | 60.0% | 0.122 | 30 |
| min3_3b | **extens** | 57.0% | 0.407 | 30 |
| exaone_32b | **extens** | 57.0% | 0.141 | 30 |
| min3_14b | **intens** | 56.5% | 0.502 | 23 |
| min3_14b | **zero** | 50.7% | 0.000 | 23 |
| min3_8b | **extens** | 47.0% | 0.222 | 30 |
| min3_3b | noise | 44.8% | 0.637 | 30 |
| glm_air | noise | 30.7% | 0.607 | 30 |
| gemma4_12b | **extens** | 30.4% | 0.541 | 30 |

Two consequences beyond the noise arm:

- **The `zero` arm is contaminated across all three Ministral rungs** (13.7 / 67.8 /
  50.7%). That is the chance-floor baseline the whole four-condition
  "amount-of-positive-information" design leans on.
- **`gemma4_12b` extens at 30.4%** is one of the three homogeneity re-run lanes, so its
  re-collected data carries this too.

This reaches into the sizing document. `POWER_ANALYSIS_2026-08-14.md`'s R = 78 headline is
driven by `[min3 ladder | intens] min3_3b vs min3_14b` (0.44 vs 0.33), with min3 extens
(77) as runner-up — a contrast between lanes at 13.7% and 56.5% intens non-compliance,
where `min3_14b` additionally holds only **23 of 30 seeds**. **R = 78 is contaminated at
source**, which strengthens that document's "do not act on R = 78" banner.

**It is not a serving confound.** `smolbench-d7`'s CONFOUND_AUDIT reading clears every
Ministral lane (min3_3b static tp=1 on mixed g6e sizes, explicitly cleared; min3_8b one
box g6e.12xl tp=4 us-west-2b; min3_14b a full 30-seed re-run on 8× g7.24xlarge tp=4
us-east-2c), and likewise exaone_32b (one box, g6e.12xl tp=4) and exaone_33b. So this is
model/parser behaviour, **not hardware heterogeneity — nobody should buy instances to
chase it.**

### The regrade is already applied — there is nothing to recover

The obvious remedy is `scripts/regrade.py`, which re-parses stored raw responses with the
compliance-aware parser. A dry run over the whole study (`--study induction`, no
`--write`) changes **zero marks in every one of the 84 conditions**: accuracy before ==
accuracy after, `recov = 0` throughout. The landed data is *already* under the
compliance-aware convention; the `compliance` field records violations that grading has
already accounted for. **Regrade-vs-quarantine is not a live fork — only quarantine is.**

Reading the raw responses says why, and the three collapsed lanes are not the same
failure:

- **exaone_32b / exaone_33b noise — total generative collapse.** **Zero** empty
  completions, but the text is unrelated to the task: *"We are going to implement a for
  and use only the = signs there"*, Korean prose about stakeholder relations. Longest
  responses run to **299,517** and **159,156 characters** — generating to the token cap.
  Of 270 marks the correct answer appears anywhere in only **2 and 5** respectively, and
  those are incidental substring matches inside multi-kilobyte rambles. **acc 0.000 is a
  graded zero, but the arm is unusable:** it measures whitespace-padding-induced
  degeneration, not induction. Report it as UNUSABLE, never as accuracy — the same call
  the noise-arm record makes for prior degenerate arms, and consistent with the standing
  rule never to regrade runaway enumerations leniently.
- **glm_flash noise — half the arm is missing.** **132 of 270** completions are empty
  (48.9%). The non-empty ones are fine (`<tool_call>2520` — 2520 is the correct answer for
  the k=9 harmonic, lcm(1..9), merely wrapped in markup). But the parser is not materially
  under-recovering: 33 marks scored correct against 39 that contain their own answer at
  all. **Unusable**, and the empty half is an infrastructure symptom (longest response
  284,206 chars) worth a separate look.
- **glm_air noise — degraded but usable, with an 18% caveat.** **48 of 270** empty
  (17.8%); 164 scored correct against 176 containing their own answer. Kept in, because
  acc 0.607 rests on responses that parse fine — but the caveat is sized to 18% missing,
  not the 6% an earlier draft of this document reported.

### Measurement notes — two traps, both hit before being caught

Reproduce with `notebooks/induction/response_audit.py`, which encodes both.

**Trap 1 — `response` is a YAML block scalar.** A line-oriented regex truncates it at the
first line that looks like a new key. That understated `glm_air` empties (16 vs 48) and
overstated `exaone_33b` answer-hits (24 vs 5). Use a real parser. The files carry
`!!python/object:` tags, so `safe_load` refuses them and `unsafe_load` would construct
arbitrary objects from generated files — against repo convention. The third option is what
the script uses: map unknown tags to plain dicts. Both sessions independently reproduced
all six lanes' counts under this method.

**Trap 2 — the per-harmonic answer is not `lcm(1..k)`.** The queries are *counts* over one
full 2520-position sequence, so harmonic k's answer is `2520 // k` =
(2520, 1260, 840, 630, 504, 420, 360, 315, 280) — and it is identical for every seed, since
only the label assignment varies with the seed. Assuming `lcm` yields
`scored > answer_in_response`, which is arithmetically impossible. The script asserts
`scored <= ans_in_resp` and checks each mark against `EXPECTED_ANSWERS`, so this fails
loudly instead of producing a plausible table. (Verified against `qwen35_397b_intens` at
acc 1.000: 270/270/270, longest response 6 characters.)

**Interpreting the `scored` vs `ans_in_resp` gap.** It only indicates parser
under-recovery when the lane's violation profile is *not* `multiple-values`-dominated. A
response that rambles through a long list of integers contains the correct one by
construction, so `min3_8b` noise (181 vs 58) and `min3_14b` (70 vs 8) are **not** evidence
of recoverable signal — the regrade no-op independently confirms nothing is recoverable
there. Where the profile is empty- or collapse-dominated, the small gaps
(`glm_flash` 39 vs 33, `glm_air` 176 vs 164) genuinely do show the parser recovering what
is present.

> **Note on the companion document.** `POWER_ANALYSIS_2026-08-14.md` as committed at
> `3cac6e75` still carries a banner deferring to a predicted pairing gain that this
> document refutes (§"Headline"). A corrected version is staged in the sibling session and
> may or may not land; until it does, read that banner as superseded here.

**Operational hazard (do not skip).** `results_store.sync_down()` is a one-way S3 → local
mirror that overwrites the local tree, so any `regrade.py --write` is destroyed by the
next sync unless deliberately re-appended to S3 — and the bucket is append-only and
user-directed to stay clean, so **write-back is a user decision, not ours.** Separately,
`regrade.py:28-29` claims a bad `--write` is recoverable via `git checkout` because the
YAMLs are "git-tracked". They are **not**: `.gitignore:235` ignores `notebooks/*/results/`.
That safety net does not exist for this study and the docstring should be corrected.

---

## Recommendations

1. **Adopt the paired test** (exact McNemar / matched-set CMH; Cochran's Q for the ladder
   gate) — correct for the design, and it makes the equivalence claims defensible. Expect
   no change to existing conclusions.
2. **Adopt Holm** over Bonferroni on Tier 2. Free; worth one contrast here.
3. **Resample whole replicates** for p-values rather than trusting the asymptotic χ², given
   the measured DE.
4. **Do not buy replicates on the strength of R = 78.** It is both an unpaired-statistic
   artifact and a min3-compliance artifact.
5. **Quarantine, don't regrade** — the regrade is already applied and recovers nothing.
   Mark `exaone_32b`/`exaone_33b` noise and `glm_flash` noise UNUSABLE (not acc 0.000);
   report `glm_air` noise as degraded-with-caveat; report **glm_47 as the noise finding**.
6. **Hold all Ministral conclusions.** All four arms are contaminated, `min3_14b` is at
   23/30 seeds, and it drives the R = 78 figure. Let the lane drain, then re-examine —
   but do not re-collect on hardware grounds; the audit clears the serving stack.
7. **Flag the `zero`-arm contamination** on all three Ministral rungs before leaning on
   the chance-floor baseline anywhere in the write-up.
8. **Fix `regrade.py:28-29`'s stale safety claim** (results are gitignored, so
   `git checkout` will not undo a `--write`), and treat S3 write-back as user-approved
   only.

## Reproduce

```
uv run --no-project --with numpy --with scipy python notebooks/induction/paired_analysis.py
```

Requires the synced local results tree (`InductionExperiment.harness.sync_down()`).
