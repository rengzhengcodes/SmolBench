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

> **CORRECTION BANNER — 2026-08-21.** This document was re-verified adversarially in two
> independent rounds, every number recomputed from raw marks and rows. The data, the
> pipeline and the pass@1 tables hold. **Both significance analyses used tests that ignore
> the design's own clustering, and correcting them moves two headlines:**
> induction Holm(210) is **119, not 125** (the seed, not the item, is the replicate — §1);
> deduction ladder Holm is **14 of 21, not 17**, and families scaling cleanly is
> **2 of 7, not 3** (the theorem block, not the cell, is the unit — §2.4). A third
> headline is **reframed rather than corrected**: the extens-vs-noise result is
> **two mechanisms**, an encoding effect where the length control survives and an
> output-collapse effect in the 6 of 21 models whose output contract whitespace padding
> destroys — the latter is now a first-class finding of this study and no contrast is
> excluded from the findings (§1.1, caveat 9). Corrections are stamped in place with the
> original text left visible; where a stamp and the surrounding prose disagree, **the stamp
> is the authority.**

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
flipping** — both borderline, both crossing *into* significance. [Depth stamp 2026-08-21:
this comparison reproduces exactly, but it was run on the *pre-closure* tree, with
`ministral-3-14b` at R=27 and 124 of its eventual 140 duplicate objects present. On the
final earliest-wins tree at R=30 the count is **125** under the item-level test tabulated
in §1 and **119** under the seed-level cluster test that §1 now carries as primary. The
124-vs-125 gap is collection depth, not the selection rule.] That direction is a property
of those two lanes, not of the rule; earliest-wins is neither statistically
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

[Corrected 2026-08-21: four of the five are pure verifier faults, but `ministral-3-3b`'s
cell (`IntermediateField.card_algHom_adjoin_integral`, k=0, `hint:2`) holds **two**
exception rows, and the *earliest* — the one earliest-wins selects — is infrastructure,
not a verifier fault: `RuntimeError: EC2 spot instance i-08d0a095f2920b4b2 is
terminated`, `verify_ms=0`, `completion_tokens=0`. Its second row is the 600 s
`DojoTacticTimeoutError`. The 3-timeout / 2-crash split names the right fault kinds for
the cells, but "unlike a spot-kill `exception`" is false of that one lane.]

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

[Corrected 2026-08-21: "0.14 points" is denominator *granularity* (1/712), not the
measured size of the drop-vs-score-0 choice. Measured: the pooled pass@1 change is
rate/(n+1), i.e. **−0.009 to −0.051 pt** across the five lanes (−0.025 `exaone-4.0-32b`,
−0.014 `ministral-3-14b`, −0.051 `glm-4.7`, −0.013 `nemotron-3-nano-4b`, −0.009
`ministral-3-3b`); the largest per-rung
change is **−0.142 pt** (`exaone-4.0-32b` `noise:3`, 37/161 → 37/162). 0.14 pt is a valid
upper bound only at rung granularity. The conclusion — that the choice cannot move
anything in this document — is unaffected and now measured rather than asserted.
**Rule adopted 2026-08-21:** `DEDUCTION_COVERAGE_DIAGNOSIS` §7 item 10 already declared
count-as-failure non-negotiable while this document dropped the cells, a contradiction of
record; the contradiction is resolved in favour of **count-as-failure as the uniform
convention going forward** (it also restores a 712-cell / 218-block 21-way intersection).
Every figure in §2 below is on the **drop** rule and the 707/216 pool, as collected, and
the two conventions differ by at most the amounts just measured — so nothing here needs
recomputing under the new convention.
**[Amended later on 2026-08-21: `error_bars.py` HAS since been re-run with
count-as-failure as its default, and `notebooks/deduction/ERROR_BARS_REPORT.txt` in this
same commit is on the 712-cell / 218-block pool. §2's tables below remain the published
707/216 drop-rule figures; against the regenerated report the marginal pass@1 rates and
BCa endpoints move only in the third decimal and the primary rejection count is unchanged
at 14 of 21 (same set). `power_analysis.load_joint_cells` still implements the drop rule —
`error_bars.py` augments on top of it and asserts cell-for-cell agreement with it.]**]

**Pairing scope.** `load_joint_cells` keeps a cell only if it is graded for *every*
model requested, so loading all 21 at once yields the **21-way intersection**. That
intersection is **707 cells over 216 theorems — 99.3% of a lane's 712**, because
`deepseek-v3.1`'s 415 exception cells were repaired before the snapshot. Global pairing
therefore costs essentially nothing and is used for every contrast, so all contrasts
rest on the same cells. Per-lane marginals over each lane's own 712 are reported
alongside; the two differ by at most 0.003 [corrected 2026-08-21 from "0.002", which is
true of the printed 3-decimal figures but not of the exact values: the max gap is 0.0025
(`deepseek-v4-flash` 0.34936 paired vs 0.3469 own-denominator), next 0.0024
(`qwen3.5-122b-a10b`)].

---

## 1. Induction — Holm–Bonferroni

**Family: 210 pre-registered PRIMARY contrasts** (84 ladder + 126 info-arm), FWER
α = 0.05, paired exact McNemar on item-matched marks. Pairing is the correct test here:
every model answers the same seeds with byte-identical prompts, and all four arms at a
given seed reuse the same queries and answers.

[Provenance stamp 2026-08-21: the *family* was pre-registered pre-data —
`power_analysis.py:188` `N_PRIMARY = 210`, committed `90ded367` on 2026-08-11 — but the
*procedure* was not. The pre-registered per-test α is Bonferroni 0.05/210; Holm is first
recommended in `MULTIPLICITY_PLAN.md` (`270f7600`, 2026-08-14 18:49), by which time R=30
had landed on 20 of 21 lanes. The liberalisation added exactly two rejections, both
`nemo3_30b vs nemo3_120b` (intens p=4.883e-04, extens p=3.658e-04). FWER validity is
unaffected, and — see the clustering correction below — those same two contrasts are
among the six the corrected test removes, so **no headline in this document rests on
them**. They are not inert, though: `[nemo3 ladder | intens]` 30b–120b is the rank-125
boundary contrast that the Holm≡Hochberg paragraph below and §0's paired-vs-unpaired
design-effect story both lean on.]

Every contrast runs at **n = 270 matched items** (30 seeds × 9 harmonics). All 21 lanes
closed at R=30 on 2026-08-16; the earlier unequal-R caveat for `ministral-3-14b` is
retired, not merely narrowed.

**What a "replicate" is, stated precisely [clarified 2026-08-21].** The 9 harmonic answers
are *identical across all 30 seeds and all 21 lanes* (2520/k); a seed re-randomises the
label vocabulary only. So the design is **30 vocabulary redraws of one fixed 9-item
problem**, not 270 independent items — which is exactly why the seed, not the item, is the
resampling unit below. The repo said so in its own design documents
(`MULTIPLICITY_PLAN.md:286`; `MULTIPLICITY_CMH_VARIANTS.md:103-105`, "RECOMMENDED HERE")
and the published family was never recomputed that way.

| test | procedure | rejected | uncorrected p<0.05 |
|---|---|---|---|
| paired | **Holm** | **125** | 148 |
| paired | Hochberg | 125 | 148 |
| unpaired (CMH) | Holm | 124 | 146 |

> **[Corrected 2026-08-21 — the primary count is 119, not 125.]** The table above is
> item-level exact McNemar, which treats 30 seeds × 9 correlated harmonics as 270
> independent items. Re-running the *identical* Holm procedure on exact seed-level cluster
> sign-flip p-values (2³⁰ enumerated; a 200k cluster bootstrap and a paired *t* agree on
> every ruling) gives **Holm(210) = 119 — 6 lost, 0 gained**; Bonferroni(210) goes 123 →
> 116. **All six losses are ladder contrasts** (`[nemo3 | intens]` and `[nemo3 | extens]`
> 30b–120b, `[gemma4 | intens]` e2b–12b and e2b–31b, `[glm | noise_intens]` air–4.7,
> `[min3 | intens]` 3b–14b), so the family-scaling counts move (ladder 36 → 30) while
> **every within-model information contrast survives unchanged (89 of 126)**. The 125
> figure is retained above as the superseded item-level result, because it is the number
> the study published and the one the report files printed.

**Holm and Hochberg reject the identical set**, not merely the same count. The two share
critical values α/(m−i+1) and differ only in stepping direction, so they can diverge only
when a p-value fails its threshold and a *larger* one later passes its looser threshold.
Holm stops at rank 126 and nothing beyond it passes — there is a 2× gap at the boundary
(4.88e-04 → 9.77e-04) and the curves never re-cross. **Use Holm**: it is valid under
arbitrary dependence, while Hochberg's Simes/MTP2 assumption is unverified for 210
statistics sharing models, seeds and harmonics — and here it buys zero extra rejections.
This is a property of this dataset's bimodal p-value distribution, not a general identity.

[Scoped and corrected 2026-08-21: this paragraph is an **item-level** fact — the boundary
contrasts and their p-values move with the test. The Holm ≡ Hochberg identity itself
survives: it was re-established at m=210 item-level (125 ≡ 125), under the corrected
seed-level cluster test (**119 ≡ 119, same set**), and at the m=21 sensitivity level under
cluster p (10 ≡ 10). Only the boundary moves — under the primary test Holm stops at rank
120, with rank 119 at p=4.578e-04 against its 5.435e-04 threshold and rank 120 at
p=9.369e-04. And the "2× gap" is not a robustness cliff: rank 125 (`[nemo3 ladder |
intens]` 30b–120b, b/c = 0/12) and rank 126 (`[ds ladder | intens]` ds_flash–ds_v31,
b/c = 0/11) are fully-discordant McNemar cases, so their p-values are the adjacent atoms
2⁻¹¹ = 4.88e-04 and 2⁻¹⁰ = 9.77e-04 of the test's discrete support. The factor of two is
arithmetically forced by one fewer discordant pair; neighbouring gaps are 1.33× on both
sides. The Holm ≡ Hochberg conclusion itself reproduces.]

Of the 125 rejections, **48 are scientific findings**; the rest are `zero`-arm positive
controls (significant by construction — a chance-floor baseline against arms at
0.60–1.00) and quarantined-lane contrasts.

> **[Category retired 2026-08-21.]** As published, the 125 partitioned into 48 findings +
> 57 `zero`-arm controls + 20 contrasts on the six collapse lanes, over a family split
> 105 findings-eligible / 78 `zero`-controls / 27 collapse-lane. Per the 2026-08-21 ruling
> the "quarantined" bucket is **retired**: output collapse under whitespace padding is a
> first-class result of this study (§1.1, caveat 9), not a disqualification, and no
> contrast is fenced off from the findings. The family now splits into exactly two
> buckets — **126 findings** (every contrast between two informative arms) and **84
> `zero`-arm controls** (63 arm-vs-floor + 21 `zero`-vs-`zero` ladder contrasts, null by
> construction) — which is what the regenerated report prints. Under the corrected primary
> those two buckets account for the 119 exactly: **59 of 126 findings** (30 of 63 ladder,
> 29 of 63 within-model info) plus **60 of the 63 arm-vs-floor controls**. The 48/57/20
> accounting is kept above as the item-level figure the study published.
>
> Reported plainly, because it is part of the collapse result rather than an embarrassment
> to hide: **3 of the 63 arm-vs-floor positive controls fail** — `exaone_32b` and
> `exaone_33b` `noise_intens` (accuracy 0.000, p=1.00 against their own `zero` arms) and
> `min3_14b` `noise_intens` (0.026, p=1.56e-02). All three are collapse lanes; **no lane
> with a well-formed noise arm fails its control.** A positive control that a collapsed
> arm cannot pass is the control working, not failing. (The remaining 21 members of the
> `zero`-involving bucket are `zero`-vs-`zero` ladder contrasts, null by construction.)

**Not significant: 57 of 105 non-control contrasts — and 48 of those are ceiling pairs**
(both arms ≥ 0.95), many with *zero* discordant items. These are ties by construction,
not underpowered: no replicate count separates two arms that never disagree on a single
item. [Corrected 2026-08-21: the 57 and the 48 are exact, but "ties by construction" holds
for **7 of the 48**, which have zero discordant items. The other 41 carry 1–21 discordant
items out of 270 — ceiling-compressed rather than strictly inseparable. Note also that the
105 denominator is post-quarantine; with that category retired the findings-eligible count
is 126, the extra 21 being the collapse-lane contrasts now reported in §1.1.]

### 1.1 The information-vs-length contrast (`extens` vs `noise_intens`)

Both arms are token-matched — `noise_intens` is the compact rule padded with whitespace
to exactly the extensional listing's token count under the model's own tokenizer — so
this contrast holds prompt **length** fixed and varies only whether the tokens carry
information.

[Corrected 2026-08-21: the last clause is wrong twice over. (i) *Both* arms are fully
informative — `noise_intens` carries the complete rule, plus tabs — so the contrast varies
the **encoding** (enumerated vs intensional) at matched token length, not the presence of
information; `extens_vs_noise.py`'s own docstring states it correctly. (ii) Pad-inertness
is an assumption this section never tested. The `intens`-vs-`noise_intens` contrast — the
pad's *own* effect — is Holm(210)-significant in **7 of 21 lanes**, from −0.996
(`exaone_33b`) to −0.167 (`glm_flash`), and in `nemo3_4b` the pad *improves* accuracy by
+0.085. It has to be conditioned lane by lane, and it is, below.]

**[Rewritten 2026-08-21 — this is a two-mechanism result.]** The section below previously
reported one filtered direction. It now reports both mechanisms the data contains, and no
contrast is excluded or fenced off from the findings.

**Raw direction across all 21 lanes: 14 noise-higher, 7 extens-higher.** That table comes
first, before any filter:

| direction | lanes |
|---|---|
| **noise higher (14)** | `qwen35_27b` `qwen35_122b` `qwen35_397b` `nemo3_4b` `nemo3_30b` `nemo3_120b` `gemma4_e2b` `gemma4_12b` `gemma4_31b` `min3_3b` `exaone_236b` `ds_flash` `ds_v31` `ds_pro` |
| **extens higher (7)** | `glm_flash` `glm_air` `glm_47` `min3_8b` `min3_14b` `exaone_32b` `exaone_33b` |

Six of the seven extens-higher lanes are exactly the six whose `noise_intens` arm
**collapsed** under the pad (`exaone_32b`/`exaone_33b` 99.6% non-compliant,
`min3_8b`/`min3_14b` 100%, `glm_flash` 60.0%, `glm_air` 30.7% — in `min3_8b`'s case on
an arm already broken unpadded; see mechanism 2). That alignment is not a coincidence
and not a selection artifact — a noise arm that cannot emit a parseable integer scores
~0, which forces extens > noise arithmetically. The seventh, `glm_47`, is discussed at
the end.

Under the primary m=210 correction, **10 of 21 are significant** — and the Holm(210)
rejection set for these 21 contrasts is **identical under item-level and seed-level
cluster p** (same 10 lanes), so the §1 clustering correction moves magnitudes and the
sensitivity analysis here, not this set. The 10 split **7 noise-higher / 3 extens-higher**;
the last column is what separates the mechanisms:

| lane | extens | noise | direction | p (item) | p (cluster) | noise-arm state |
|---|---|---|---|---|---|---|
| nemo3_4b | 0.396 | 0.719 | noise higher | 1.74e-11 | 1.79e-07 | well-formed (0.0% n.c.) |
| nemo3_30b | 0.711 | 0.937 | noise higher | 9.63e-11 | 8.34e-07 | well-formed (0.0%) |
| nemo3_120b | 0.841 | 0.996 | noise higher | 5.12e-12 | 2.38e-07 | well-formed (0.0%) |
| gemma4_e2b | 0.115 | 0.981 | noise higher | 1.29e-67 | 1.86e-09 † | well-formed (0.0%) |
| exaone_236b | 0.641 | 0.978 | noise higher | 6.58e-23 | 3.73e-09 | well-formed (0.0%) |
| gemma4_12b | 0.548 | 0.993 | noise higher | 4.63e-35 | 1.86e-09 † | well-formed (0.4%); `extens` 28.5% n.c. |
| min3_3b | 0.407 | 0.637 | noise higher | 8.92e-07 | 4.14e-04 | 44.8% n.c.; `extens` 57.0% |
| glm_flash | 0.393 | 0.122 | **extens higher** | 4.80e-14 | 1.19e-07 | **collapsed, 60.0%** |
| exaone_32b | 0.141 | 0.000 | **extens higher** | 7.28e-12 | 1.91e-06 | **collapsed, 99.6%** |
| exaone_33b | 0.741 | 0.000 | **extens higher** | 1.25e-60 | 1.86e-09 † | **collapsed, 99.6%** |

† at the sign-flip attainable minimum 2/2³⁰ = 1.86e-09. Bonferroni floor 0.05/210 =
2.38e-04. "n.c." = share of marks the compliance parser rejects.

**Mechanism 1 — encoding, on the lanes whose length control is well-formed.** Thirteen
of the 21 lanes have **both** arms well-formed (<25% non-compliance on each); 5 of those
13 are Holm-significant and the direction among them is **noise-higher without exception
— 5 noise-higher, 0 extens-higher**: at a matched token count a model does substantially
better reading the compact rule padded with whitespace than reading the full
enumeration. The five lanes with a clean pad — `nemo3_4b`/`30b`/`120b`, `gemma4_e2b`,
`exaone_236b`, spanning **three families** — carry gaps of 0.155 to 0.866 and survive
the exact seed-level sign-flip at worst p = 8.3e-07, 285× below the Bonferroni floor.
This is the study's information/label-density finding and it is robust to every
correction on this pass.

*Length is not the explanation, and here is the check that shows it.* At a
**token**-matched prompt length [corrected 2026-08-21 from "byte-matched": byte lengths
differ by tokenizer. `extens` is exactly 61,096 chars in all 21 lanes; the noise arm
runs **0.560×** that for the gemma-4 family, 1.034× for `exaone_33b`/`exaone_236b`,
1.058× for nemo3 and min3, 1.111× for qwen3.5. So for `gemma4_e2b` the *winning* prompt
is 44% **shorter** in bytes and that lane cannot discriminate byte length from encoding;
the other four clean lanes have a strictly longer noise prompt in bytes and still score
higher, which is the version of the argument that carries weight]. The pad's own effect,
measured per lane rather than assumed: **inert** in `nemo3_30b` (−0.019), `nemo3_120b`
(−0.004) and `gemma4_e2b` (+0.033), mildly **conservative** in `exaone_236b` (−0.022),
and **pro-claim** in `nemo3_4b` (+0.085, cluster p=4.1e-02) — so `nemo3_4b`'s 0.322 gap
is an **upper bound**, and its pad-free anchor should be quoted beside it: `intens`
0.633 → `extens` 0.396, −0.237, cluster sign-flip p=1.39e-05. The pad-free anchors stay
significant in all five lanes (worst cluster p 1.39e-05), which is what makes the
inference stand without relying on the pad at all. Because the pad *helps* `nemo3_4b`,
the qualitative direction is if anything reinforced there: added length improves that
lane, so its extensional deficit cannot be a length cost.

*Two limits on the mechanism-1 lanes, stated:* the five span three families, not five
independent ones (three of them are one family's rungs). And **`gemma4_e2b`'s
contribution is one saturated failure mode, not graded difficulty**: 93.7% of its
extensional traces stop enumerating at position 252 of 2520 and report roughly
answer/10 — median response/answer ratio 0.101, 86.2% of 268 numeric responses inside
[0.08, 0.13]× truth, against a median ratio of 1.000 in its own `intens`/`noise` arms and
in every other lane's `extens` arm. Its arm is 99.3% *format*-compliant, so the ≥25%
non-compliance gate structurally cannot see a well-formed-but-order-of-magnitude-wrong
integer. In a measurable minority (18 of 240 h1–h8 traces) the model demonstrably
*induced the period correctly* and still halted at 252, so for this lane the failure is
strategy elicitation and execution — the enumerated presentation elicits an
enumerate-and-count strategy it cannot complete — and the "label density" gloss should be
dropped for `gemma4_e2b` specifically. Its direction and its p stand; the mechanism story
does not transfer.

**Mechanism 2 — padding a prompt with whitespace destroys the output contract in 6 of 21
models.** This is a first-class result of this study, not an exclusion criterion. Held at
a matched token count against a 122-word rule, `exaone_32b` and `exaone_33b` emit nothing
parseable on 99.6% of marks and score 0.000; `min3_8b` and `min3_14b` are 100%
non-compliant; `glm_flash` is 60.0% non-compliant (48.9% of its marks are *empty
completions*); `glm_air` is 30.7%. Their `intens` arms — the same rule text, unpadded —
are 0.0%, 0.0%, 78.9%, 58.1%, 0.4% and 0.0% non-compliant respectively, so the whitespace
is the attributable cause in four of these six, while `min3_8b` and `min3_14b` were
already failing the contract unpadded. Counting by the criterion rather than by the named
list, **7** lanes carry a `noise_intens` arm at ≥25% non-compliance — the six above plus
`min3_3b` at 44.8% — and the pad pushes **6** of the 21 lanes over that line (`exaone_33b`
+99.6 pts, `exaone_32b` +99.6, `glm_flash` +59.6, `min3_14b` +41.9, `min3_3b` +31.1,
`glm_air` +30.7); `min3_8b`'s +21.1 lands on an arm that was broken already. Either way
the result is the same size: whitespace padding to a matched token count breaks the output
contract in **6 of 21 models**.

Within that 7-lane collapse class, 4 contrasts are Holm-significant and the direction is
**3 extens-higher (`glm_flash`, `exaone_32b`, `exaone_33b`) — mechanically**, since a
collapsed arm scores near zero and the enumerated arm wins by default — plus 1
noise-higher (`min3_3b`, whose *extensional* arm is the more broken of the two at 57.0%).
These rows measure padding robustness, not induction, and they are reported as such — as a
finding about the models, alongside mechanism 1, never as a filtered-out direction. The
same collapse is what makes those lanes' `noise`-vs-`zero` positive controls fail (§1).

**A third, single-lane class:** `gemma4_12b` is the one lane where the *enumeration*
broke the format while the noise arm stayed intact (`extens` 28.5% non-compliant, mostly
empty, against `noise` 0.4%). Its noise-higher result is therefore partly a format effect
too, and it belongs with neither mechanism cleanly.

**The takeaway is therefore two-part, and neither half should be quoted alone:** at
matched token length an enumerated listing is harder to induce from than a stated rule
wherever the length control survives contact with the model (14 of 21 lanes point that
way raw; of the 10 significant lanes the 7 noise-higher ones all kept a scoring noise arm,
and the 5 with a fully clean pad span three families); *and* whitespace padding at that
same length breaks the output contract outright in 6 of 21 models, which is both a real
robustness result and the mechanical reason those six point the other way.

**The remaining counter-example, restated.** `glm_47` is the one lane with an intact noise
arm (0.4% non-compliant) whose extensional arm nonetheless beats it:

| model | extens | noise | direction | p (item) | p (cluster) |
|---|---|---|---|---|---|
| glm_47 | 0.889 | 0.789 | **extens higher** | 2.44e-03 | 5.19e-02 |

[Rewritten 2026-08-21; the previous text called it "the sixth-ranked clean lane", "the
strongest lane just below the line", and said "re-correcting at m=21 would admit it".
All three are wrong.] It is genuinely opposite in sign to mechanism 1 — information at
fixed length *helps* it by +0.100 — and it should stay on the page. But it is weak on
three independent grounds:

1. **Not significant under the corrected test, at any family size.** Its margin is
   replicate-level: the noise arm collapses on 7 of 30 seeds (to 3/9, 5/9, 2/9, 2/9, 3/9,
   5/9, 6/9), and those 7 seeds supply +33 of the +27 net while the other 23 sum to −6.
   Item-level exchangeability is itself rejected at p=2.0e-04, so 2.44e-03 is
   demonstrably anticonservative. The exact seed-level sign-flip gives **p=5.19e-02**
   (cluster bootstrap 3.4e-02, paired *t* 4.4e-02): rank 145 at m=210 against a 7.6e-04
   threshold, **rank 15 at the m=21 sensitivity level against a 7.14e-03 threshold — not
   admitted there either** — and not significant uncorrected. A non-significant reversal,
   not a clean counter-example.
2. **It is 8th of 13 clean lanes, not 6th.** Under cluster p the two clean lanes
   immediately below the line are `qwen35_397b` (p=1.56e-02, 0.974 vs 1.000) and
   `qwen35_27b` (p=3.13e-02, 0.974 vs 1.000), and both point **noise-higher**, with
   mechanism 1.
3. **Its own length control is broken** — the only lane outside the six where that is
   true at low non-compliance. The pad costs it −0.170 (b/c 52/6, item p=3.16e-10, cluster
   p=2.29e-05) at 0.4% non-compliance. Its three-arm decomposition reads
   `intens` 0.959 / `extens` 0.889 / `noise` 0.789: pure length costs 0.170, and
   information at fixed length recovers 0.100. Note that its extensional arm is still
   *below* its own unpadded rule arm (−0.070). It is a pad-fragility counter-example, and
   a mild mechanism-2 case at compliant output, rather than an information one.

This study's own record — the `gpt-oss` opposite-ends crossover that the pilot mistook for
a general result — remains the reason to publish the direction table above rather than a
significance-filtered count.

Re-sizing a family to a subset chosen after seeing the data is not a valid primary
analysis, so m=21 is reported as sensitivity only. [Updated 2026-08-21: under cluster p
that sensitivity is Holm 10 / Hochberg 10, not 12 / 12 — `glm_47` and `glm_air` drop out
of it.]

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
[Pool stamp 2026-08-21: those figures are the published **drop**-rule pool. Under the
count-as-failure rule now default in `error_bars.py` the same quantities are **218 blocks,
712 cells, 1.39× (median), range 1.16–1.45×** — the argument and its magnitude are
unchanged.]

Intervals are **BCa** (bias-corrected and accelerated, jackknife over blocks), which
matters for the near-floor lanes where the resample distribution is right-skewed. No
lane needed the percentile fallback. [Measured 2026-08-21: BCa is correctly implemented
and does move endpoints — but by at most 0.0029 (`ministral-3-3b`), and at
`nemotron-3-nano-30b-a3b`'s 0.041 by 0.0022 on a 0.034-wide interval, ≈6% of width. Above
the document's own 0.0005 drift tolerance, so worth doing; well short of "visibly
mis-centred". |z₀| ≤ 0.036 everywhere and no conclusion turns on it.]

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
ladder contrasts separate despite overlapping marginal bars [17 → **14** under the
corrected clustered test; see §2.4]. **Overlapping marginal CIs in the table above do not
imply a null contrast**; read the contrast intervals.

### 2.4 Ladder contrasts — 14 of 21 significant under Holm

[Heading corrected 2026-08-21; published as "17 of 21". The tables and diffs in this
section are unchanged — only the significance column moves.]

> **What the p-values in this section are, and the correction to them
> [2026-08-21].** The published Holm and BH columns were **exact McNemar over the 707
> paired cells**, i.e. the cell-independence assumption §2.1 explicitly rejects when it
> builds every interval on this page. The document never said so, which let a reader
> infer that the block bootstrap supplied the inference; it did not. Intervals are
> block-bootstrap BCa over 216 theorem blocks, p-values were cell-level McNemar, and the
> two disagree.
>
> The corrected primary test is the **block sign-flip permutation over theorem blocks** —
> the exact clustered generalisation of exact McNemar, validated by reducing to exact
> McNemar on singleton clusters (B = 10⁶; cluster-Wald, studentized bootstrap-*t* and
> percentile inversion agree on every count below). On the study pool it rejects
> **14 of 21**, not 17. A control that resamples *cells* with the same machinery
> reproduces 17/21 with the identical rejection set, so the entire gap is clustering;
> median block/cell SE ratio 1.141.
>
> | contrast | diff | p · 707 pool | Holm 707 | p · 828 pool | Holm 828 |
> |---|---|---|---|---|---|
> | qwen 27b → 122b | +0.050 | 0.0121 | — | 0.0065 | yes |
> | qwen 27b → 397b | +0.095 | 2e-06 | **yes** | 1e-06 | **yes** |
> | qwen 122b → 397b | +0.045 | 0.0162 | — | 0.0129 | — |
> | nemo 4b → 30b | −0.055 | 1.11e-04 | **yes** | 3.12e-04 | **yes** |
> | nemo 4b → 120b | +0.068 | 6.8e-05 | **yes** | 7e-06 | **yes** |
> | nemo 30b → 120b | +0.123 | 1e-06 | **yes** | 1e-06 | **yes** |
> | gemma e2b → 12b | +0.074 | 1.21e-04 | **yes** | 8.1e-05 | **yes** |
> | gemma e2b → 31b | +0.242 | 1e-06 | **yes** | 1e-06 | **yes** |
> | gemma 12b → 31b | +0.168 | 1e-06 | **yes** | 1e-06 | **yes** |
> | glm flash → air | +0.069 | 1.05e-03 | **yes** | 1.6e-05 | **yes** |
> | glm flash → 4.7 | +0.215 | 1e-06 | **yes** | 1e-06 | **yes** |
> | glm air → 4.7 | +0.146 | 1e-06 | **yes** | 1e-06 | **yes** |
> | min3 3b → 8b | +0.007 | 0.68 | — | 0.463 | — |
> | min3 3b → 14b | +0.037 | 0.0247 | — | 0.0073 | yes |
> | min3 8b → 14b | +0.030 | 0.0542 | — | 0.0411 | — |
> | exaone 32b → 33b | −0.021 | 0.256 | — | 0.547 | — |
> | exaone 32b → 236b | −0.078 | 3.2e-05 | **yes** | 9.6e-05 | **yes** |
> | exaone 33b → 236b | −0.057 | 1.88e-04 | **yes** | 1.86e-04 | **yes** |
> | ds flash → v3.1 | +0.091 | 1.3e-05 | **yes** | 1e-06 | **yes** |
> | ds flash → v4-pro | +0.057 | 2.67e-03 | **yes** | 1.58e-04 | **yes** |
> | ds v3.1 → v4-pro | −0.034 | 0.0957 | — | 0.171 | — |
>
> **Corrected counts: 14 of 21** on the 707-cell / 216-block study pool this document
> reports, **16 of 21** on the post-recovery 828-cell / 250-block pool of caveat 12
> (published: 17/21 on both — the extended-pool scope check had re-used the contested
> cell-level test). BCa-inversion at Holm thresholds, i.e. this document's *own* interval
> method turned into a test, gives 16/21 on the study pool and is reported as a
> sensitivity rather than the primary: at qwen 27b→122b its nuisance parameters are
> near-null (z₀=+0.013, a=+0.011) yet shift p by 28% in the far tail, and it returns
> p≈1.4e-06 where the bootstrap floor is 1e-06.

Scaling holds cleanly in **3 of 7 families** — qwen3.5, gemma-4 and GLM, where every
rung-pair is positive and Holm-significant. The other four each break monotonicity in a
different way.
[**Superseded — corrected 2026-08-21 to 2 of 7**, gemma-4 and GLM. Under the doc's own
definition (all three rung-pairs positive *and* Holm-significant), qwen3.5 keeps only
27b→397b at the cluster step and so leaves the clean set. This is the most robust correction on this
page: 2 of 7 holds on both pools (707 and 828) and with or without the process term of
caveat 11. It is a **deduction-leg** statement; the induction leg is not scored this way
anywhere in this document.]

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

[Corrected 2026-08-21 — clustered per-family counts, study (707) pool: gemma-4 3, GLM 3,
Nemotron-3 3 (one negative rung), DeepSeek 2, EXAONE 2 (both negative), qwen3.5 1,
Ministral-3 0 = **14 of 21**. On the 828 pool qwen3.5 returns to 2 and Ministral-3 to 1,
for 16 — so "Ministral-3 0" is pool-specific and should not be quoted bare. Unchanged by
the correction: **EXAONE's inversion and Nemotron-3's V-shape survive on both pools**, as
does DeepSeek's rise-then-plateau; the three tables above are exactly the three whose
verdicts do not move. Ministral-3 "flat" is if anything reinforced — its one published
rejection was the endpoint contrast, and it does not survive clustering on the study
pool.]

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

[Corrected 2026-08-21: **the refutation is pool-sensitive and must be quoted with that
fragility.** The +0.050 qwen 27b→122b contrast doing the refuting is *not*
Holm-significant under the clustered test on the study pool (p=0.0121) and *is* on the
post-recovery 828 pool (p=0.0065). The point estimate is positive on both, so the
hypothesis is still not supported — but "qwen3.5 contradicts it" rests on a contrast that
the corrected primary test does not reject on the pool this document reports.]

**Holm vs the raw CI agree on 20 of 21.** The one disagreement (ministral-3-8b vs
ministral-3-14b, +0.030 [+0.003, +0.060]) is exactly what multiplicity control is for:
an interval that just excludes zero, in a family of 21.

[Corrected 2026-08-21: that agreement statistic pairs a *block*-bootstrap interval with a
*cell*-level p and is void with the test that produced it. Three inference machines run
over this one table — block sign-flip permutation (the corrected primary, 14/21),
BCa-inversion at Holm thresholds (16/21, sensitivity), and the published cell-level
McNemar (17/21) — beside 18 BCa intervals excluding zero. Under the corrected primary the
uncorrected-p<0.05 count on the study pool is 17, so Holm removes three, not one:
qwen 27b→122b (0.0121), qwen 122b→397b (0.0162) and min3 3b→14b (0.0247). Read the
rejection **set** in the box at the head of this section, not any single scalar.]

### 2.5 Secondary tier — cross-family, size-matched

63 contrasts, pre-registered at Benjamini–Hochberg q = 0.05 (exploratory, so FDR rather
than FWER). **BH rejects 56 of 63**, identical to both the uncorrected p<0.05 count and
the count of CIs excluding zero — the cross-family effects are large enough that the
correction is not binding at this tier. BH runs inside `error_bars.py --mode report`, so
this figure regenerates with the rest.

For contrast, at the PRIMARY tier Holm *is* binding: 17 rejections against 18
uncorrected. The single contrast it removes (ministral-3-8b vs ministral-3-14b, +0.030
[+0.003, +0.060]) is exactly what multiplicity control is for.

[Corrected 2026-08-21: these are cell-level McNemar figures. Under the corrected clustered
primary the PRIMARY tier is 14 rejections against 17 uncorrected, and the three contrasts
Holm removes are qwen 27b→122b, qwen 122b→397b and min3 3b→14b — ministral-3-8b vs
ministral-3-14b (cluster p=0.0542) is not uncorrected-significant to begin with. Holm is
still binding, on a different set. The BH secondary-tier figure above (56 of 63) is the
published cell-level figure on the 707 pool. **[Amended later on 2026-08-21: it HAS since
been re-run. On the regenerated 712/218 pool the block sign-flip test gives **BH 52 of
63**, against 54 uncorrected and 56 CIs excluding zero; cell-level McNemar + BH on the
same cells gives 57. So the correction *is* binding at this tier under the clustered test —
the "not binding" reading above was an artefact of the cell-level p. See
`notebooks/deduction/ERROR_BARS_REPORT.txt`.]**]

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
   consumes a whole theorem), not 944. [Sharpened 2026-08-21: 712/218 is exact for 16
   lanes; **five lanes hold 711 cells** (`nemotron-3-nano-4b`, `glm-4.7`,
   `ministral-3-3b`, `ministral-3-14b`, `exaone-4.0-32b`), and of those two —
   `nemotron-3-nano-4b` and `glm-4.7` — are also 217 blocks, which is where the
   intersection's 216 = 218 − 2 comes from.] **[Post-recovery accounting, 2026-08-18: the
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

   [Corrected 2026-08-21 — the conclusion holds, the timing argument does not. It is
   confirmed that 0 of 56 `gemma-4-12b` and 0 of 48 `deepseek-v4-flash` duplicate cells
   carry `server_config` in either version. But `gemma-4-12b`'s newest attempts span
   01:47:56Z–03:08:31Z and **16 of the 56 ran *after* the 02:06:44Z stamping commit**, up
   to an hour later, still unstamped; only `deepseek-v4-flash` (max 01:40:31Z) is actually
   bounded by the commit. The real mechanism is that stamping depends on the **code
   deployed to the serving box**, not on when the object landed: gemma's fleet was
   provisioned before `040d2e83` and kept writing unstamped objects long past it. The
   boxed lesson below therefore extends — dating the commit is necessary and *not
   sufficient*; you must also date the fleet. Related, and relevant to caveat 5: under
   earliest-wins all three multi-attempt lanes are internally era-split rather than
   single-config (`gemma-4-12b` 14+16 seeds across eras, `ministral-3-14b` 9+14+7,
   `deepseek-v4-flash` 12+18). [Re-derived 2026-08-21 from the per-seed `date:` fields:
   `ministral-3-14b` is 9 (seeds 0-8, Aug 11-12) + 14 (seeds 9-18, 20-23, Aug 14) + 7
   (seeds 19, 24-29, Aug 16), not 9+12+9; the 7-seed third era matches
   `PASS_AT_1_REVIEW_PLAN` §2.5's "28 = 7 seeds × 4 arms".]]

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

   [Corrected 2026-08-21 — wrong pointer, and the thing being priced was never named.
   "The next item" is caveat 6, which supplies **no rate** and explicitly refuses one
   ("do not treat 0/8 as 'the' cross-process rate"). The only *measured* process term in
   this document is **caveat 11**, and it is a deduction-leg measurement
   (`nemotron-3-nano-4b`, 200 cells) borrowed here for an induction-leg issue — a real
   stretch, stated rather than hidden. What is actually being priced, from
   `CONFOUND_AUDIT_2026-08-13.md:16-27`: the analysed `gemma-4-12b` lane spans **tp=1**
   (seed 0), tp unresolvable (seeds 1–4) and **tp=4 on `g6e.12xlarge`** (seeds 5–13) — a
   serving change correlated with seed index, which is exactly what the discarded re-run
   was collected to cure. Mitigating, and worth stating: all four arms at a given seed
   share that seed's configuration, so the mixing largely cancels inside within-lane arm
   contrasts (§1.1) and bites on ladder contrasts.]

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

   [Corrected 2026-08-21 — this inference runs the wrong way and the last sentence should
   not stand. "Every lane runs on its own hardware" means process identity is
   **uncorrelated with model *size*** but **perfectly aliased with model *identity***.
   For a between-model contrast — which every contrast in §2.4/§2.5 is — an aliased term
   does not average out; it enters the difference directly. Caveat 11 quantifies it at
   ≈1.1 pt per lane and none of the intervals on this page include it (§2.4 now carries
   that sensitivity explicitly). Correct statement: *process identity is uncorrelated with
   model size but aliased with model identity, so it contributes an unmodelled ≈1.1 pt
   variance component to every between-model contrast, and the reported intervals exclude
   it.* Re-runs still cannot remove it — but "do not chase it" was the sentence licensing
   the omission, and it is withdrawn.]

   The 8/8 within-process figure is **genuine kernel determinism, not prefix-cache
   replay** — the obvious alternative explanation, since pass 2 could simply be replaying
   pass 1 from cache. Tested directly: the stock configuration logged 3,904 prefix-cache
   hits, and a caching-off configuration logged 0 queries and 0 hits *and still scored
   8/8*. The noise floor stands without a caveat.
   [Scoped 2026-08-21: keep the conclusion, drop "without a caveat". The caching-off arm
   changed **four flags together** (`--no-enable-prefix-caching --max-num-seqs 1
   --enforce-eager --seed 0`); caching-off alone was never run, so the residual confound
   is CUDA-graph capture. Two things push against it mattering — the probe is sequential,
   so `--max-num-seqs` is not live, and `ministral-3-3b`'s stock arm logged 10,320 cache
   hits yet scored 0/8, so cache hits plainly do not force byte-identity. The arm proves
   determinism is *achievable* cache-free; it does not isolate caching as irrelevant under
   the stock configuration the study actually collected under.]

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

9. **Whitespace padding destroys the output contract in 6 of 21 models — a RESULT, not
   an exclusion.** [Rewritten 2026-08-21 under the ruling that retires the "quarantined"
   category. Original text, kept visible: *"Six `noise_intens` lanes are quarantined for
   output-contract collapse, not low accuracy … Contrasts involving them measure
   whitespace-padding-induced degeneration, not induction, and are reported separately
   from the findings."* The measurement was right; the disposition was wrong.]

   Padding the compact rule with whitespace to the extensional listing's token count
   collapses the output contract in six lanes, at these per-arm rates (share of marks the
   compliance parser rejects, `noise_intens` arm):

   | lane | `noise_intens` | its own `intens` | note |
   |---|---|---|---|
   | `exaone_32b` | **99.6%** | 0.0% | accuracy 0.000; total generative collapse |
   | `exaone_33b` | **99.6%** | 0.0% | accuracy 0.000; total generative collapse |
   | `min3_8b` | **100%** | 78.9% | |
   | `min3_14b` | **100%** | 58.2% | |
   | `glm_flash` | **60.0%** | 0.4% | of which 48.9% are *empty completions* |
   | `glm_air` | **30.7%** | 0.0% | of which 17.8% empty |

   These six contrasts are **not excluded and not fenced off from the findings**. They
   measure padding robustness rather than induction, and that is reported as its own
   result in §1.1 (mechanism 2), alongside the encoding effect (mechanism 1) — never as a
   filtered-out direction. Two consequences follow and are stated there: a collapsed arm
   scores ~0, so these lanes are extens-higher *mechanically*; and three of them fail
   their `noise`-vs-`zero` positive controls, which is the control working (§1).

   The acting criterion is **≥25% non-compliance on the arm**. As published it was applied
   by inspection to noise arms only, which is why the six above are a hand-written list;
   the regenerated report applies it **symmetrically to all four arms**, and the arithmetic
   of that should be stated rather than smoothed:

   * **7** noise arms clear the criterion, not 6 — the six named above plus `min3_3b` at
     44.8%, which is *higher* than the lowest named lane (`glm_air`, 30.7%) and was
     nonetheless handled by the contamination tag instead of the collapse list.
   * **16 of 84 cells** clear it across all arms, so 9 of them are non-noise cells:
     `min3_14b/extens` 84.4%, `min3_8b/intens` 78.9%, `min3_8b/zero` 67.8%,
     `min3_14b/intens` 58.1%, `min3_3b/extens` 57.0%, `exaone_32b/extens` 57.0%,
     `min3_14b/zero` 48.5%, `min3_8b/extens` 47.0%, `gemma4_12b/extens` 28.5%.
   * Two of the qualifying cells are `zero`-baseline cells (`min3_8b`, `min3_14b`): those
     lanes are non-compliant even with an **empty** context, so their collapse is not
     padding-specific — which is also why the *pad-attributable* count is 6 while the
     criterion count is 7 (§1.1).

   Sensitivity, measured on the pre-retirement buckets: applying one threshold
   symmetrically moved the counts from 48 findings / 20 collapse-lane / 57 controls to
   32/44/49 at 0.25 and 36/39/50 at 0.307, and at every threshold tested (0.25 / 0.307 /
   0.50) **all five `min3` ladder findings and both significant EXAONE `extens` ladder
   findings reclassify** — the "Ministral inverts with scale" induction story does not
   survive a symmetric rule. The mechanism-1 headline survives all of them (max cell
   non-compliance among those five lanes: 7.8%).

   Separately: 16 of 84 cells are ≥25% non-compliant (including the six noise arms above,
   so 10 further); findings touching them are flagged `[!]` in the report, because the
   mechanism may be format collapse rather than task difficulty. **A limit of that gate,
   now known:** it sees *format*, so it structurally cannot detect a well-formed but
   order-of-magnitude-wrong answer — `gemma4_e2b`'s extens arm is 99.3% compliant and
   uniformly ~10× low (§1.1).

10. **`glm_flash` has 132/270 empty completions** on a 110-token prompt against an 86,751
   token budget — an infrastructure symptom, not truncation, and it has not been
   investigated.
   [Corrected 2026-08-21 — the premise is wrong and it contradicted caveat 9. The 132
   empties are **all in one arm**: per-arm empty counts over all 120 `glm_flash` rep files
   are `intens` 0/270, `extens` 1/270, **`noise_intens` 132/270**, `zero` 2/270. That arm's
   prompt is **56,856 characters** — the 122-word rule padded with ~56k characters of
   whitespace to `extens`'s token count — not 110 tokens; the genuinely short arms
   (`intens` 748 chars, `zero` 496) have 0 and 2 empties. So this is the caveat-9 collapse
   showing up as empty returns, and "an infrastructure symptom, not truncation" was
   licensed only by the false 110-token premise. The 86,751-token budget figure is not
   checkable from the analysed objects.]

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

   [Sharpened 2026-08-21, five points. **(a) The lane SD is ≈1.09–1.16 pt, not "roughly
   ±1.2".** √(0.095/712) = 1.15 pt is the naive value; the *measured* design effect on
   the signed flip sum is 0.895 (95% [0.68, 1.00]), so ±1.2 pt slightly **over**-states
   the term. **(b) It is already a two-process *difference* SD.** √(p_flip/N) is the SD
   of (c−b)/N, and (c−b)/N is identically p_rerun − p_orig, so the per-run σ is 1.15/√2
   ≈ **0.82 pt**. A contrast between two independently-served lanes adds (0.0115)²
   **once, not twice** — adding it twice, the natural misreading, doubles the variance
   and costs three rejections in §2.4 (13/21 → 10/21 on the 707 pool). **(c) Quote the
   rejection set, not the scalar.** With the process term added the clustered Holm count
   is 13/21 (707) and 14/21 (828), but Holm cascades: a 0.06 pt change in σ — inside
   this measurement's own uncertainty — swings the 828 count by one. The cascade-free
   Bonferroni counts are stable at 11/21 (707) and 12/21 (828). **(d) 178/200 is the
   extracted *candidate proof* differing.** The full generation text differs in 199/200
   (99.5%), and the raw response alone in 191/200 — which strengthens the point being
   made, that byte agreement is the wrong metric. **(e) The two bounds, reconciled.** As
   an estimate *for this lane* 9.5% is an **upper** bound (it pinned image and
   checkpoint where the study's own build is unrecoverable); as an estimate *for other
   lanes* it is plausibly a **lower** bound (this is the study's most stable lane). Both
   were stated thirteen lines apart without reconciliation. And "noise, not bias" is
   established only for the process component: the build/checkpoint component folded
   into the same 9.5% is assigned by a lane's **collection date** (five-plus vLLM builds
   under a mutable `:nightly` tag — caveat 4 here, `DETERMINISM_PLAN_2026-08-16.md`
   §1.4), which is staggered per model and therefore partially confounded with the model
   axis. Unmeasured, because builds were never recorded.]

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

**[2026-08-21] Which column is primary.** The commands above are unchanged — no new
flags — but the corrected tests are what the regenerated reports lead with. On the
induction side (`notebooks/induction/SIGNIFICANCE_REPORT.txt`,
`notebooks/induction/EXTENS_VS_NOISE_REPORT.txt`) the **seed-level cluster p-value is the
primary column**, with item-level exact McNemar retained beside it as a descriptive
column; that is why the headline count is 119 rather than 125 and the m=21 sensitivity is
10 rather than 12. On the deduction side the corrected primary is the **block sign-flip
permutation over theorem blocks** (§2.4, 14 of 21 on the study pool).
[Tightened 2026-08-21: `error_bars.py` has since been regenerated —
`notebooks/deduction/ERROR_BARS_REPORT.txt` now prints `p_block` as the PRIMARY column
with `p_cell` beside it as descriptive, on the count-as-failure 712/218 pool, and rejects
the same 14 of 21. Where that report and §2.4 differ it is only the pool (712/218 vs the
707/216 figures §2 reports), and the rejection set is identical.] Anywhere this document shows a superseded number it is stamped as
such.
