# Deduction (Lean4) coverage diagnosis — why 24.6% of the eval is unmeasurable

> ## Correction, 2026-08-16 (post-review, measured)
>
> Two claims below were wrong and are superseded by this box. They are left in
> place in situ so the reasoning that produced them stays legible.
>
> **A. Five lanes have a 711 denominator, not two.** Counting cells with no
> surviving measurable row directly from `analysis/2026-08-16/`:
> `nemotron-3-nano-4b`, `glm-4.7`, `ministral-3-3b`, `ministral-3-14b` and
> `exaone-4.0-32b` each hold exactly one `exception`-only cell
> (`Polynomial.natSepDegree_eq_natDegree_iff`, `Submodule.iSup_toAddSubmonoid`,
> `IntermediateField.card_algHom_adjoin_integral` ×2,
> `CategoryTheory.GradedObject.ιMapObjOrZero_mapMap`). `qwen3.5-27b` and
> `gemma-4-31b` are 712. The `imeout`-substring field scan that found two missed
> three because the snapshot strips error strings to `null` — the same stripping
> this document flags as step P1. Count cells, not error text.
>
> **B. `error_bars.py` never bootstrapped against 300, so no published CI is too
> narrow.** `n_thm` is derived from the blocks the loader returns
> (`error_bars.py:266`, `:360-361`); it has no hardcoded theorem count. The paired
> analysis runs on the 21-lane intersection, which is **216** blocks — smaller than
> the 218 derived here, because two of the five 711-lanes lose a whole theorem. The
> `300 − 45 − 37 = 218` decomposition is correct **per lane** and wrong as a claim
> about the analysis. Intervals are conservative, not narrow.
>
> Both were caught by `smolbench-4d` checking against the data rather than
> accepting the hand-off. Neither affects the scope finding in §3a, which was
> independently reproduced there from `file_path`.



**Date:** 2026-08-16 · **Branch:** `periodic-induction` · **Status:** DIAGNOSIS AND PLAN ONLY —
nothing was fixed, no study code/data/config was modified, no verification pass was re-run, no
EC2 instance was touched, no money was spent. S3 was read-only (`ls` / `cp` into scratchpad).

**Bottom line up front.**

1. Generation is complete; **verification** is not. 232 of 944 cells per lane are unmeasurable,
   in **all** lanes, on the **same** cell keys. Measurable denominator = **712/lane**.
2. The 232 splits cleanly into two classes with **different causes and opposite bias profiles**:
   **151 cells / 45 theorems** are `DojoInitError` (verification could not open the theorem) and
   are **100% `.lake/packages/std/`** — a *scope* restriction (Mathlib only); whether those
   theorems would score comparably is unmeasured, see §3a;
   **81 cells / 37 theorems** are ground-truth-prefix replay failures and are **100% `Mathlib/`**
   with **median proof length 8 tactics vs 2** for the measurable set (permutation p = 5e-5) — a
   **real difficulty skew**.
3. So: **the measurable 712 IS a biased subsample — but the bias does not move the rates.** A
   length-matched imputation of what the lost 37 would have scored shifts every lane's `stepk:1`
   rate by **+0.000 to +0.005 absolute** (5 lanes measured), because next-tactic success is
   **non-monotonic** in proof length. The *scope* loss (100% of `std`) is the caveat that actually
   matters. Section 3.
   Separately: the block-bootstrap effective block count is **218**, not 300 and not 255 — the 37
   prefix theorems lose **every** rung, so they are not blocks either. Section 2 F4.
4. Top root-cause hypothesis for the 151: **the traced-repo cache used by the 2026-08-14
   verification pass did not contain the `std` dependency package's build tree**, and the cache
   now on this box **does**. Evidence: an archived `verified_rows_BROKEN-dojoinit_*` in which
   **944/944** cells were `replay_failed` (total cache failure), repaired to 232 the same day; a
   sibling cache directory `CORRUPT-20260801-…` that is **missing `.lake/packages/std/.lake/build`
   entirely**; and the fact that today `to_json_path()` resolves and the `.ast.json` **exists for
   all 17 `std` files involved**. If that holds, the 151 are recoverable with **verification-only
   compute and zero model tokens**.
5. `DojoTacticTimeoutError`: **found, 2 cells in 13 lanes scanned**, one each in `glm-4.7` and
   `ministral-3-3b`. They are recorded as `verdict="exception"` with `error="DojoTacticTimeoutError: "`,
   they have **no surviving retry**, and so they make the measurable denominator **711** in those
   two lanes rather than 712. The brief's "~5 cells" is plausible at 21 lanes. Section 5.

---

## 1. What actually did not run

### 1.1 Generation vs measurement

Every lane's published analysis input has exactly the same shape. Verified by direct count over
`s3://smolbench-results-414266451290/analysis/2026-08-16/deduction/<model>/verified_rows.jsonl`
(copied read-only into scratchpad). **`verified_rows.jsonl` is a raw multi-attempt log, not one
row per cell** — the analysis loader applies the snapshot's "earliest surviving (non-`exception`)
row per cell" rule first:

```
                    raw rows   distinct cells   sanity
gemma-4-e2b              944              944      300
glm-4.7-flash            944              944      300
ministral-3-8b           944              944      300
qwen3.5-397b-a17b        944              944      300
deepseek-v4-pro          944              944      300
glm-4.7                  944              944      300
ministral-3-3b          1524              944      300   <-- 580 retry rows, 480 of them `exception`
```

The 944 cells decompose by rung (one replicate — `replicate_idx` is 0 for every cell, so R = 1):

| rung | cells | theorems |
|---|---|---|
| `stepk:1` | 300 | 300 |
| `hint:2` | 222 | 222 |
| `hint:3` | 211 | 211 |
| `noise:3` | 211 | 211 |
| **total** | **944** | 300 distinct |

`scripts/audit_run_completeness.py` reporting 944/944 clean is therefore **correct and not in
conflict** with this document: it audits that a *candidate* exists for every cell. It says nothing
about whether Lean was ever able to *judge* that candidate.

### 1.2 The unmeasurable classes — corrected against the snapshot

The task brief lists three unmeasurable classes (`exception`, `replay_failed`, plus ~5
`DojoTacticTimeoutError`). All three are real, but the brief's arithmetic attributes them wrongly.
Cell-verdict tallies **after** the earliest-surviving-row dedup:

| lane | success | lean_error | incomplete | given_up | replay_failed | no survivor |
|---|---|---|---|---|---|---|
| gemma-4-e2b | 78 | 566 | 68 | 0 | **232** | 0 |
| glm-4.7-flash | 104 | 578 | 30 | 0 | **232** | 0 |
| ministral-3-8b | 52 | 609 | 50 | 1 | **232** | 0 |
| qwen3.5-397b-a17b | 279 | 387 | 46 | 0 | **232** | 0 |
| deepseek-v4-pro | 288 | 396 | 28 | 0 | **232** | 0 |
| glm-4.7 | 256 | 434 | 21 | 0 | **232** | **1** |
| ministral-3-3b | 47 | 651 | 13 | 0 | **232** | **1** |

**Correction 1 — `exception` is not part of the 232.** The 232 is **entirely** `replay_failed`.
Raw `exception` rows do exist and are numerous in one lane (480 in `ministral-3-3b`, 1 in
`glm-4.7`, 0 in the other five), but the snapshot's selection rule ("take the EARLIEST SURVIVING
(non-exception) row per cell", `scripts/snapshot_analysis_data.py` MANIFEST `notes`) resolves all
but one per lane against a surviving retry. `exception` therefore contributes a **third,
much smaller** unmeasurable class — the **no-survivor** cells — not a share of the 232.

**Correction 2 — `DojoTacticTimeoutError` exists but has no verdict of its own.** It is recorded as
`verdict="exception"`, `error="DojoTacticTimeoutError: "`. Both no-survivor cells found are exactly
these. See §5.

So the accurate statement is: **944 generated; 232 unmeasurable via `replay_failed` (one verdict,
two distinct internal causes); plus 0-1 further cells per lane lost to an unretried
`DojoTacticTimeoutError`; measurable = 712 per lane, or 711 in `glm-4.7` and `ministral-3-3b`.**

### 1.3 The 232 = 151 + 81, re-derived from the snapshot

The 300 `sanity` rows are the ground-truth full-proof replay, one per theorem — the ideal
diagnostic, because a theorem whose Dojo session cannot be created fails there too:

```
sanity verdicts (gemma-4-e2b): {'success': 255, 'exception': 45}
sanity non-success, all 45 identical shape:
  DojoInitError: Cannot find the *.ast.json file for Theorem(repo=LeanGitRepo(url='https://g…
```

Joining sanity to cells:

```
theorems with DojoInitError sanity            : 45
  replay_failed cells inside those 45 theorems: 151
  NON-replay_failed cells inside those 45     :   0     <-- total loss, no partial measurement
replay_failed cells in OTHER theorems         :  81   across 37 theorems
                                                232   across 82 theorems
```

This **independently reproduces** the provenance note in `scripts/snapshot_analysis_data.py`
(151 DojoInit + 81 prefix = 232) and commit `39e73a0d`. The brief's framing of the split is
confirmed; only its attribution of `exception` to the 232 is not.

### 1.4 "The same 232 in every lane" — verified, with scope stated

Set-equality on the cell key `(theorem_id, rung, k, replicate_idx)`:

```
replay_failed cell-key sets identical across 7 lanes : True   (symmetric difference 0)
DojoInit theorem sets identical across 7 lanes       : True   (45 theorems, same 45)
lanes checked: gemma-4-e2b, glm-4.7-flash, ministral-3-8b, qwen3.5-397b-a17b,
               deepseek-v4-pro, glm-4.7, ministral-3-3b        (5 families)
```

Six further lanes were stream-grepped without downloading (`nemotron-3-nano-30b-a3b`,
`k-exaone-236b-a23b`, `exaone-4.5-33b`, `nemotron-3-super-120b-a12b`, `gemma-4-31b`,
`deepseek-v3.1`) and all show `replay_failed = 232`. **13 of 21 lanes checked; the remaining 8 are
asserted from the provenance note, not verified here.**

A trap worth recording: the raw stream-grep for `ministral-3-3b` returns 246, not 232 — because
that lane has 580 duplicate attempt rows. **The count is 232 only after dedup.** Anyone re-checking
this with `grep -c` on the raw file will get the wrong number for the multi-attempt lanes.

### 1.5 A coincidence to kill before someone re-derives it

`notebooks/deduction/data/replay_passing_novel_premises_val.jsonl` holds 1104 records of which
805 are `success`; 300 × 299/1104 = 81.25, tantalisingly equal to the 81 prefix failures. **It is
a coincidence.** `smolbench/deduction/lean/corpus.py:348` filters the pool with
`if rec.get("verdict") == "success":`, so the 299 non-success records never entered the sample —
consistent with `notebooks/deduction/run_study.py:500` ("300 of its 805").

---

## 2. Findings verified NOW

Each claim below was produced by a command run during this investigation. Claims I did **not**
verify are labelled as such.

### F1 — The DojoInit 45 are 100% `std`, the other two groups 100% `Mathlib`

Joining each theorem's `file_path` (present on every cell row) to the three groups:

```
group           n  file-path buckets
measurable    218  {'Mathlib/': 218}
DojoInit       45  {'.lake/packages/std/': 45}
prefix         37  {'Mathlib/': 37}
```

**Complete separation.** Not "concentrated in", not "enriched for" — every single DojoInit
theorem is a Lean `std` (Batteries) dependency-package theorem, and every measurable and every
prefix-fail theorem is Mathlib. The 45 span **17 distinct files**:

```
 10  .lake/packages/std/Std/Data/List/Lemmas.lean       3  …/Std/Data/BinomialHeap/Basic.lean
  6  .lake/packages/std/Std/Data/String/Lemmas.lean     2  …/Std/Data/PairingHeap.lean
  5  .lake/packages/std/Std/Data/RBMap/Lemmas.lean      2  …/Std/Data/List/Basic.lean
  4  .lake/packages/std/Std/Data/Rat/Lemmas.lean        1  each: List/Perm, Int/DivMod, Nat/Gcd,
  4  .lake/packages/std/Std/Data/Array/Lemmas.lean         ByteArray, Int/Order, HashMap/WF,
                                                           UnionFind/{Basic,Lemmas}, Fin/Lemmas
```

### F2 — DojoInit is NOT a difficulty skew; prefix-failure IS

Difficulty proxy = `n_tactics` from the corpus sidecar (recorded by the pre-study filter pass,
independent of this study), joined on `full_name` → `theorem_id`; cross-checked against
`n_total_tactics` on the cell rows (medians agree exactly).

| group | n | n_tactics p25/p50/p75/p90 | mean | max | frac ≥5 tactics | corpus `wall_ms` median |
|---|---|---|---|---|---|---|
| measurable | 218 | 1 / **2** / 4 / 6 | 3.05 | 16 | 0.188 | 3146 |
| DojoInit | 45 | 1 / **2** / 4 / 6 | 3.04 | 13 | 0.244 | 3020 |
| prefix | 37 | 5 / **8** / 11 / 17 | 9.43 | 24 | **0.865** | 2621 |

Two-sided permutation test on the mean (20 000 shuffles, seed 0), each group vs the 218 measurable:

```
DojoInit   n= 45  mean 3.04 vs 3.05   diff -0.01   p = 1.00000
prefix     n= 37  mean 9.43 vs 3.05   diff +6.38   p = 0.00005
```

DojoInit is **indistinguishable** from the measurable set on proof length. Prefix-failure is a
**4× longer-proof** subpopulation and is not remotely compatible with random loss.

### F3 — Per-rung loss, and which paired contrasts survive

| rung | cells | lost | (DojoInit / prefix) | measurable | % lost | measurable theorems |
|---|---|---|---|---|---|---|
| `stepk:1` | 300 | 82 | 45 / 37 | 218 | 27.3% | 218 |
| `hint:2` | 222 | 52 | 36 / 16 | 170 | 23.4% | 170 |
| `hint:3` | 211 | 49 | 35 / 14 | 162 | 23.2% | 162 |
| `noise:3` | 211 | 49 | 35 / 14 | 162 | 23.2% | 162 |
| **total** | **944** | **232** | **151 / 81** | **712** | **24.6%** | — |

Measurable-theorem set symmetric differences between rungs:

```
hint:3 vs noise:3  : 0     <-- IDENTICAL. The hint-vs-noise paired contrast is intact.
hint:2 vs hint:3   : 8
stepk:1 vs hint:2  : 48
stepk:1 vs hint:3  : 56
```

**The `hint:3` / `noise:3` pairing that `notebooks/deduction/hint_vs_noise.py` rests on is
unharmed** — both rungs lose exactly the same 49 cells. Cross-rung comparisons involving
`stepk:1` or `hint:2` are on different theorem sets, but they already were pre-loss (the rungs
have 300/222/211/211 cells by construction; a theorem needs enough tactics to have a `hint:2`
rung at all). I did **not** compute how much of the 8-theorem `hint:2`↔`hint:3` gap is
loss-induced vs by-design.

### F4 — Block-bootstrap effective block count is **218**, not 300 and not 255

`notebooks/deduction/error_bars.py` blocks over theorems. Direct count of theorems holding at
least one non-`replay_failed` cell:

```
BLOCK COUNT (theorems with >=1 measurable cell): 218
  non-blocks: 45 DojoInit + 37 prefix = 82
```

My first estimate of 255 (= 300 − 45) was **wrong**: the 37 prefix theorems lose **every rung they
have**, not just some. Cells-per-theorem confirms this is a whole-theorem loss, not a partial one:

```
cells per theorem, 37 prefix   : {1: 21, 4: 14, 2: 2}   -- all cells replay_failed
cells per theorem, 218 measurable: {4: 162, 1: 48, 2: 8}
cells per theorem, 45 DojoInit  : {4: 35, 1: 9, 2: 1}
```

(The per-rung table in F3 shows only 16/14/14 prefix losses outside `stepk:1` because only 16 of
the 37 have a `hint:2` rung at all — 21 of them are single-cell theorems.)

**Effective blocks = 218, a 27.3% reduction from 300.** Bootstrap CIs computed against 300 blocks
are too narrow. Note also that 255 is *not* independently corroborated by the sanity-success count
— that count is the same 300 − 45 subtraction, so it was never a check.

### F5 — An earlier verification pass failed 944/944 and was repaired on 2026-08-14

The live run prefix retains the audit trail:

```
2026-08-11 11:49:39   6996212  deduction/runs/scaling_gemma-4-e2b/all_rows.jsonl
2026-08-14 11:59:19   7816268  …/verified_rows_BROKEN-dojoinit_archived-2026-08-14.jsonl
2026-08-14 20:07:50   7426432  …/verified_rows.jsonl
```

Tally of the archived BROKEN file:

```
rows 1244  kinds {'cell': 944, 'sanity': 300}
cell verdicts: {'replay_failed': 944}      <-- 100% failure
```

So on 2026-08-14 ~12:00 the verification cache failed **completely**; something was repaired; the
20:07 re-run recovered 712/944 and left the 232 residual. `~/.cache/lean_dojo/.smolbench_verify.lock`
has mtime `2026-08-14 12:01:20`, i.e. verification ran **on this box**, not on EC2.

### F6 — The cache **now on disk** would not reproduce the DojoInit failure

`lean_dojo` 4.20.0 (`.venv-lean`), `LEAN4_PACKAGES_DIR = .lake/packages`,
`LEAN4_BUILD_DIR = .lake/build`. Its real path resolver, run read-only:

```
.lake/packages/std/Std/Data/Rat/Lemmas.lean
   -> .lake/packages/std/.lake/build/ir/Std/Data/Rat/Lemmas.ast.json   exists=True
.lake/packages/std/Std/Data/List/Lemmas.lean
   -> .lake/packages/std/.lake/build/ir/Std/Data/List/Lemmas.ast.json  exists=True
Mathlib/FieldTheory/RatFunc.lean
   -> .lake/build/ir/Mathlib/FieldTheory/RatFunc.ast.json              exists=True
```

Sweeping **all 17** DojoInit files against `to_json_path()`:

```
17 DojoInit files: ast.json present for 17/17; sibling(.dep_paths/.trace.xml)-incomplete: 0
Lean4Repl.lean present: True
.lean sources for the std files: present
```

**This refutes the naive "LeanDojo looks in the wrong place for dependency packages" hypothesis**
— `lean_dojo/utils.py:_from_lean_path` has an explicit `LEAN4_PACKAGES_DIR` branch that maps
`.lake/packages/std/X.lean` → `.lake/packages/std/.lake/build/ir/X.ast.json`, and that file is
there. The DojoInit error therefore reflects the cache **as it was at 20:07 on 2026-08-14**, not
the code.

### F7 — A sibling cache directory is missing the `std` build tree entirely

```
~/.cache/lean_dojo/
  .smolbench_verify.lock                                   2026-08-14 12:01:20
  CORRUPT-20260801-leanprover-community-mathlib4-fe4454af…/  <-- .lake/packages/std/.lake/build : ABSENT
  CORRUPT2-bak/                                              <-- .lake/packages/std/.lake/build : present
  leanprover-community-mathlib4-fe4454af…/  (live)           <-- .lake/packages/std/.lake/build : present
```

A traced-repo directory that is complete for Mathlib but **has no `std` build tree** is exactly
the state that produces "`Cannot find the *.ast.json file`" for 45 `std` theorems and nothing
else. All inner mtimes are tarball-preserved (`2024-07-02`), so I **could not date** when the live
directory acquired its `std` build tree — that is the single missing link in this chain and step
D1 below closes it.

### F8 — A code asymmetry that can independently manufacture `replay_failed`

`smolbench/deduction/lean/verify.py` uses **two different replay loops**:

- full-proof replay (`replay_proof`, ~L212-234) classifies each step: `LeanError` → `lean_error`,
  `ProofGivenUp` → `given_up`, **`ProofFinished` → `success`**;
- prefix replay (`open_at_step`, L407-412) is strictly:
  ```python
  state = dojo.run_tac(state, tac)
  if not isinstance(state, TacticState):
      raise RuntimeError(f"prefix tactic {tac!r} -> {type(state).__name__} on {bt.full_name}")
  ```
  and `verify_proof_tail` maps that `RuntimeError` → `verdict="replay_failed"` (L~466).

`ProofFinished` is **not** a `TacticState`. So a prefix that *closes the goal early* is
`success` under the corpus filter that admitted the theorem, and `replay_failed` here. Likewise a
timeout surfacing as `LeanError` becomes `replay_failed` rather than a diagnosable `lean_error`.
Because `error` is stripped to `None` on `replay_failed` rows in the published snapshot, **the
`type(state).__name__` that would settle this is not in the snapshot** — it is in the run log.
This is *hypothesis-grade*, not verified: I did not obtain the error strings.

### F9b — A third, tiny, model-dependent loss class exists

Two cells (one in `glm-4.7`, one in `ministral-3-3b`) are `verdict="exception"` with
`error="DojoTacticTimeoutError: "` and **no surviving retry**, so the dedup rule drops them
entirely. Their lanes' measurable denominator is 711. Full treatment in §5. `verify_ms` over the
712 measurable cells: p50 = 212 ms, p90 = 2 676 ms, max = 12 466 ms — normal verification is
~3 orders of magnitude below the 600 s cap.

### F9 — What is not in the snapshot

`replay_failed` rows carry `error: None` in `verified_rows.jsonl` (232/232 for gemma-4-e2b), and
the per-theorem `theorems/<thm>/outputs/*.jsonl` files are **generation-time** records
(`verdict: "unverified"`). So the discriminating error text for the 81 exists only in the
verification pass's own logs, not in the published analysis input.

---

## 3. The bias question — is the measurable 712 a biased subsample?

**Yes, and it must be reported as two separate caveats, because pooling them cancels the signal.**

### 3a. The 151 / 45 theorems: a **scope** restriction, not a difficulty one

- Verified (F2): `n_tactics` distribution is statistically indistinguishable from the measurable
  set (means 3.04 vs 3.05, permutation p = 1.000; identical quartiles 1/2/4/6).
- Verified (F1): but it is **100% of the study's `std`/Batteries theorems** — every Lean-core
  data-structure lemma (`List`, `Array`, `String`, `RBMap`, `Rat`, `HashMap`, `UnionFind`,
  `BinomialHeap`, `PairingHeap`, `ByteArray`, `Int`, `Nat`, `Fin`) is gone.

So the eval is silently **narrowed to Mathlib**. The honest description is: *the deduction leg
measures next-tactic prediction on Mathlib, not on Mathlib + Lean's standard library.*

**State it as a scope restriction, not as "not a difficulty loss" — the stronger phrasing
overclaims.** Proof length is a *proxy*; the quantity that would settle difficulty is the models'
success RATE on those 45 theorems, and no such rate exists, because no model ever attempted them
under a setup that could verify the answer. So "these theorems are no harder" is **not
measurable from the collected data**, and steps D1/P1 below do not close it either — only
recovering the 45 into the measurable set would. What *is* established is narrower and still
sufficient for the write-up: the excluded set is not distinguishable from the measurable set on
proof length, and it is defined by a property (source tree) that is independent of any model's
behaviour. Prefer: *"the leg measures Mathlib only; whether `std` theorems would score
comparably is unmeasured."*

That matters for any claim about "Lean4 theorem proving"
generally, and it matters for contamination/memorisation arguments (`std` lemmas are short,
computational, and very differently distributed from Mathlib's algebra/category-theory bulk).
It does **not** invalidate any model-vs-model contrast, because the loss is identical across all
21 lanes (F1.4) and therefore perfectly concordant in every paired test.

### 3b. The 81 / 37 theorems: a **real difficulty skew** that does **not** move the rates

- Verified (F2): median 8 tactics vs 2; 86.5% have ≥5 tactics vs 18.8% of the measurable set;
  permutation p = 5e-5.
- Mechanically expected, which raises confidence it is causal rather than coincidental: the
  `stepk:1` rung sets `k = n_total_tactics − 1`, so a long proof requires replaying a long
  ground-truth prefix before the model's tail is even reachable. More prefix tactics = more
  chances for one of them not to yield a `TacticState`. The prefix-fail k-values run 2…23.

**Direction and magnitude of the rate bias — measured, not inferred.** My first draft asserted the
rates were *optimistic* because "the removed theorems are the long ones, the ones every model is
worst at." **That inference is wrong.** `stepk:1` success rate by proof length, over the
measurable set only:

| lane | 1-2 tactics (n=126) | 3-4 (n=51) | 5-7 (n=25) | 8+ (n=16) |
|---|---|---|---|---|
| qwen3.5-397b-a17b | 0.127 | **0.431** | 0.280 | 0.188 |
| deepseek-v4-pro | 0.135 | **0.412** | 0.200 | 0.188 |
| gemma-4-e2b | 0.071 | **0.137** | 0.120 | 0.062 |

Success is **non-monotonic in length and peaks at 3-4 tactics**; the single *worst* bin is the
shortest one, which is where 126/218 (58%) of the measurable set sits. Imputing the 37 lost
theorems at their own length bins' observed rates (lost-37 bins: 5 in 3-4, 12 in 5-7, 20 in 8+):

```
lane                observed stepk:1   imputed rate for the 37   bias-corrected (218+37)    delta
qwen3.5-397b-a17b   48/218 = 0.220              0.250                     0.225            +0.004
deepseek-v4-pro     46/218 = 0.211              0.222                     0.213            +0.002
gemma-4-e2b         20/218 = 0.092              0.091                     0.092            -0.000
glm-4.7             35/217 = 0.161              0.184                     0.165            +0.003
ministral-3-3b       3/218 = 0.014              0.049                     0.019            +0.005
```

**The length skew is real but the rate bias it induces is under half a percentage point, and its
sign is (very slightly) pessimistic, not optimistic.** All five lanes move the same direction and
by a similar amount, so it cannot flip a contrast either. This is the answer to the brief's
question for this class: *skewed, but not materially.*

Caveat on the imputation: it assumes the 37 behave like measurable theorems of the same length.
That is the standard missing-at-random-within-strata assumption and it is untestable here — the
whole point is that nobody has an observation for them.

### 3c. What survives and what needs a caveat

| Claim type | Affected? | Why |
|---|---|---|
| Model-vs-model paired McNemar / rank order | **No** | Loss is byte-identical across lanes (§1.4); dropped cells are concordant-missing, not concordant-zero. |
| `hint:3` vs `noise:3` paired contrast | **No** | Identical measurable theorem sets (F3). |
| Absolute success **rates** | **Denominator yes, value barely** | Denominator is 712 not 944; but the length skew moves `stepk:1` rates by only +0.000…+0.005 (3b). The Mathlib-only restriction (3a) is the real qualifier. |
| Bootstrap CIs from `error_bars.py` | **Yes (width)** | **218** effective blocks, not 300 (F4) — a 27.3% reduction. CIs computed against 300 are too narrow. |
| Any "Lean4 / theorem-proving in general" framing | **Yes** | `std` is 100% absent (3a). |

### 3d. The one test I could not run that would sharpen 3b

I characterised the 37 on proof length, file, and corpus wall-time. I did **not** characterise
them on **premise count / import depth / declaration kind**, because the snapshot rows do not
carry those and `smolbench/deduction/lean/premises.py` would need the traced repo. If 3b needs to
be stated more strongly than "longer proofs", run:

```bash
.venv-lean/bin/python - <<'PY'
from smolbench.deduction.lean.corpus import iter_replay_passing
from smolbench.deduction.lean.premises import referenced_premises
# for each of the 37 vs a length-matched sample of the 218: len(referenced_premises(t)),
# t.file_path import depth, and declaration kind (theorem/lemma/instance/private).
PY
```
A length-matched comparison is the right form: it separates "the 37 are long" (already known)
from "the 37 are additionally premise-heavy", which would be an independent skew.

---

## 4. Root-cause diagnosis plan

Ordered cheapest-and-most-discriminating first. **The two classes are kept separate — they have
different causes.** Nothing below was executed.

### Track D — the 151 DojoInit cells (45 `std` theorems)

**D1. Did the 2026-08-14 20:07 pass run against a cache that lacked `std`?** *(cost: minutes,
read-only, no Lean)*
- *Hypothesis:* the live traced-repo directory did not contain
  `.lake/packages/std/.lake/build/ir/` at 20:07; it does now (F6, F7).
- *Test:*
  ```bash
  # a) recover the verification pass's own log for the 20:07 run
  aws s3 ls --recursive s3://smolbench-results-414266451290/deduction/runs/ | grep -iE 'log|stderr|verify'
  # b) the pass writes a server_config/manifest sidecar; check for a cache fingerprint
  aws s3 cp s3://smolbench-results-414266451290/deduction/runs/scaling_gemma-4-e2b/manifest.json -
  # c) local: which directory was mounted, and when did the std build tree appear
  find ~/.cache/lean_dojo -maxdepth 6 -name 'build' -newermt '2026-08-14 12:00' -printf '%T+ %p\n'
  stat -c '%y %n' ~/.cache/lean_dojo/*/mathlib4/.lake/packages/std/.lake/build
  ```
- *Confirms:* the `std` build tree postdates 20:07, or the log names `CORRUPT-20260801-…`.
  → **the 151 are a pure cache artifact and are fully recoverable.**
- *Refutes:* the `std` tree predates the pass → go to D2.
- *Fix cost if confirmed:* re-verify 151 cells × 21 lanes = 3 171 verifications, **no model
  tokens**. See §6.

**D2. Does the current cache actually open one of the 45 theorems?** *(cost: ~1 min CPU,
read-only, no Lean build — but see the caveat)*
- *Hypothesis:* if D1 is refuted, the FileNotFoundError comes from inside
  `TracedFile.from_traced_file` (a sibling artefact or a `.dep_paths` entry), not from the
  `.ast.json` itself.
- *Test:* the exact code path `lean_dojo/interaction/dojo.py:120-126` takes is
  `to_json_path` → `TracedFile.from_traced_file` → `get_traced_theorem`. Parse-only reproduction:
  ```bash
  .venv-lean/bin/python - <<'PY'
  from pathlib import Path
  from lean_dojo.utils import to_json_path
  from lean_dojo.data_extraction.traced_data import TracedFile
  root = Path.home()/'.cache/lean_dojo/leanprover-community-mathlib4-fe4454af900584467d21f4fd4fe951d29d9332a7/mathlib4'
  fp = Path('.lake/packages/std/Std/Data/List/Lemmas.lean')
  tf = TracedFile.from_traced_file(root, to_json_path(root, fp, None), None)
  print(type(tf), len(list(tf.get_traced_theorems())))
  PY
  ```
  **Caveat:** constructing a real `LeanGitRepo` hits the GitHub API and `Dojo(...)` would build
  Lean — do **not** instantiate `Dojo` here; keep it to `TracedFile` parsing, and run with
  `GITHUB_ACCESS_TOKEN` unset and no network need. If `repo=None` is rejected, reconstruct the
  repo object from `manifest.json`'s pinned URL/commit rather than resolving it live.
- *Confirms (raises FileNotFoundError):* a genuine per-file gap → identify the missing artefact
  from the traceback; fix = re-trace `std` only.
- *Refutes (parses fine, 45 theorems locatable):* cache is now good → D1 was right by elimination,
  and re-verification is a straight win.

**D3. Is it `get_traced_theorem` returning `None` rather than a missing file?** *(cost: free)*
- *Hypothesis:* rejected in advance — `dojo.py` raises a **different** message
  (`"Failed to locate the theorem with … as its fully qualified name"`) for that case, and all 45
  sanity errors are the `Cannot find the *.ast.json file` string (§1.3). Recorded so nobody
  re-tests it.

**D4. Toolchain/revision mismatch between corpus snapshot and traced repo?** *(cost: free)*
- *Hypothesis:* the benchmark's `file_path`s use a package layout the traced repo does not have.
- *Test:* `cat notebooks/deduction/data/leandojo_benchmark_4/metadata.json` and compare its pinned
  mathlib4 commit against the cache dirname `…-fe4454af900584467d21f4fd4fe951d29d9332a7`.
- *Confirms:* different SHAs → the whole corpus is being replayed against the wrong revision,
  which would predict Mathlib failures too — **and there are none** (F1: 218/218 Mathlib
  measurable), so this hypothesis is **already 95% dead**. Listed only to close it on the record.

### Track P — the 81 prefix-replay cells (37 Mathlib theorems)

**P0. When was the ground truth last known to replay? — RUN, result below.** *(cost: one command)*
- *Hypothesis:* if the filter pass that recorded these 37 as `success` is old, "the environment
  drifted between the filter and the study" leads; if it is recent, a code-path asymmetry (F8)
  leads.
- *Result:*
  ```
  git log --follow --format='%h %ad %s' --date=short -- notebooks/deduction/data/replay_passing_novel_premises_val.jsonl
  2fa76a9b 2026-07-10 a bunch of training infrastructure     <-- sidecar first committed
  f13b60d0 2026-08-11 archive: move retired experiment trees into archive/   (path move only)
  ```
- *Reading:* the ground truth was certified replay-passing on **2026-07-10**, one month before
  generation (2026-08-11) and five weeks before verification (2026-08-14) — and **before** the
  2026-08-01 cache corruption (F7). A month of environment drift across a cache corruption event
  is ample. **Environment drift is the leading explanation for the 81; F8's `ProofFinished`
  asymmetry drops to secondary** but is not excluded, since it would also have been latent on
  2026-07-10 (the filter uses the full-replay path, the study uses the prefix path — the asymmetry
  is time-invariant and would produce exactly this pattern with no drift at all). P1 separates
  them outright.

**P1. Recover the error strings — this is the whole ballgame and costs nothing.** *(cost: minutes)*
- *Hypothesis:* `open_at_step`'s `RuntimeError` message embeds `type(state).__name__`
  (`LeanError` vs `ProofFinished` vs `TimeoutError`), which names the cause outright. The
  published snapshot strips it (F9), but the verification driver logged it.
- *Test:*
  ```bash
  aws s3 ls --recursive s3://smolbench-results-414266451290/deduction/runs/scaling_gemma-4-e2b/ | grep -viE '/theorems/'
  # look for a pre-snapshot verified_rows variant or a driver log that retained `error`;
  # scripts/lean_verify_rows.py writes rows with `error` populated -- the stripping happens later.
  ```
  If no log survives, one **local, model-free** re-verification of the 37 theorems reproduces it
  (see P2) — the prefix replay does not involve the model at all.
- *Confirms `LeanError`:* the ground truth genuinely no longer replays → environment/tactic drift,
  or a timeout (see P3).
- *Confirms `ProofFinished`:* **code bug (F8)** — the prefix closes the goal before step k, so
  there is nothing for the model to do; these cells are ill-posed, not failed. Fix = one-line
  special-case in `open_at_step` plus a decision about what such a cell *means*.

**P2. Does the ground-truth prefix replay today?** *(cost: ~37 Dojo sessions, no model tokens)*
- *Hypothesis:* the failures are transient (session pressure, memory, timeout) rather than
  deterministic.
- *Test:* replay just the 37 theorems' prefixes with `verify.open_at_step`, serially, one at a
  time. **Do not run this while the induction fleet babysitter is live** — it competes for the
  same box, and `scripts/lean_verify_rows.py` takes an exclusive flock on
  `DOJO_CACHE_DIR/.smolbench_verify.lock` (L907-928) which would collide.
- *Confirms (all 37 replay):* the failure was load/timing → recover by re-running under lower
  concurrency. *Refutes (same 37 fail):* deterministic → P1's error string is the answer.

**P3. Is it the 600 s per-session timeout, given the 4× longer prefixes?** *(cost: free to test
from data already held)*
- *Hypothesis:* `verify_proof_tail(..., timeout=600)` is a whole-session budget; the 37 replay
  a median of 7 ground-truth tactics before the tail, vs 1 for the measurable set (F2).
- *Test attempted, inconclusive:* `verify_ms` is **`0` for all 232** `replay_failed` rows (the
  field is only populated on a completed verification), so the snapshot cannot answer this. For
  scale, `verify_ms` over the 712 measurable cells is p50 = 212 ms, p90 = 2 676 ms, **max
  = 12 466 ms** — normal verification sits ~3 orders of magnitude under the 600 s cap, which makes
  a plain timeout on the *ground-truth prefix* unlikely a priori. Settle it with P1's error string
  (a LeanDojo timeout surfaces as a distinguishable exception type) or with the timing emitted by
  P2's re-run.
- *Fix if timeout:* raise the cap for high-`k` cells; cheap, verification-only.

**P4. Naming instability (metavariable / autobound / universe counters).**
- *Hypothesis:* the corpus filter recorded `success` under one naming regime and the study replays
  under another; `smolbench/deduction/lean/decontam.py` exists precisely because these counters
  are unstable.
- *Test:* only worth running if P1 says `LeanError` and the message mentions an unknown
  identifier / `?m.NNNN` / `inst✝`. Then diff the failing tactic text against the traced tactic
  in `leandojo_benchmark_4`.
- *Priority:* **last** — it is the most expensive to chase and the least likely given that these
  same theorems passed the filter with the same tactic text.

---

## 5. The `DojoTacticTimeoutError` cells

**Found: 2 cells across the 13 lanes scanned. They are a genuinely separate, model-dependent
class, and they are NOT part of the 232.**

### 5.1 How many, and which lanes

```
lane            DojoTacticTimeout cells
glm-4.7                         1   Submodule.iSup_toAddSubmonoid          stepk:1  k=15
ministral-3-3b                  1   IntermediateField.card_algHom_adjoin_integral  hint:2  k=0
11 other lanes scanned          0
```

Scanned: `gemma-4-e2b`, `glm-4.7-flash`, `ministral-3-8b`, `qwen3.5-397b-a17b`, `deepseek-v4-pro`,
`glm-4.7`, `ministral-3-3b` (full field scan for `imeout` in `error`/`lean_error`), plus
`nemotron-3-nano-30b-a3b`, `k-exaone-236b-a23b`, `exaone-4.5-33b`, `nemotron-3-super-120b-a12b`,
`gemma-4-31b`, `deepseek-v3.1` (stream-grep). **8 lanes unscanned** — at this rate the brief's
"roughly 5 across 21" is a reasonable extrapolation, but only 2 are verified.

### 5.2 How they are recorded — this is the part that matters

They do **not** have a verdict of their own. They are:

```
verdict = "exception",  error = "DojoTacticTimeoutError: "
```

and in **both** cases the cell has **no surviving non-`exception` attempt**. So the snapshot's
earliest-surviving-row rule finds nothing to keep and the cell **drops out of the analysis
entirely**. That is why they are invisible in the deduped verdict tally (§1.2) and why they were
easy to miss: they reduce the denominator silently.

**Consequence:** the measurable denominator is **711** for `glm-4.7` and `ministral-3-3b`, and 712
for the other five verified lanes. A per-lane denominator that is not constant is exactly the kind
of thing that quietly breaks a paired analysis if the loader assumes 712 everywhere.

### 5.3 Would raising the 600 s cap recover them?

**Unknown from the snapshot, and I could not test it.** `verify_ms` is `0` for every
`replay_failed` and every dropped row (the field is only populated on a completed verification),
so there is no recorded duration to compare against the cap. What *is* known: `verify_ms` across
the 712 measurable cells runs p50 = 212 ms, p90 = 2 676 ms, **max = 12 466 ms** — i.e. normal
verification is three orders of magnitude below the 600 s cap. A cell that hits 600 s is not
"slightly over budget"; it is a pathological tactic (`decide`, a `simp` bomb, an unbounded
`omega`). Raising the cap would most likely convert a timeout into a much slower timeout.

### 5.4 How they should be treated

They are categorically different from the 232: generation **succeeded**, and whether a candidate
tail blows the 600 s cap depends on **what the model produced**. Therefore:

- Do **not** pool them with `replay_failed`. `replay_failed` is excludable precisely because it is
  model-independent (§1.4); excluding a model-dependent class the same way flatters whichever
  model emits the most pathological tactics.
- Default: **count them as failures in the denominator**, exactly as `incomplete` is
  (`snapshot_analysis_data.py` note: "`incomplete` IS model-dependent … and stays in the
  denominator as a genuine failure"). A tactic that cannot be checked in 600 s is not a
  successful next tactic. **Note this is a change from current behaviour**, which drops them.
- If the cap is ever raised, it must be raised **and the pass re-run for all 21 lanes**, not just
  the affected two, or the lanes stop being comparable.
- At ~2-5 cells out of 712 (≤0.7%) the choice cannot move any reported contrast. Document it,
  pick "count as failure", move on.

**How they should be treated if any are found.** They are categorically different from the 232:
generation **succeeded**, and whether a candidate tail exceeds the 600 s tactic cap depends on
what the model produced (a `simp`-bomb or a deep `decide` from one model, a one-liner from
another). That makes them **model-dependent**, so:

- Do **not** pool them with `replay_failed`. `replay_failed` is excluded precisely because it is
  model-independent (§1.4); a model-dependent class excluded the same way would flatter whichever
  model times out most.
- Default: **count them as failures** in the denominator, exactly as `incomplete` is
  (`snapshot_analysis_data.py` note: "`incomplete` IS model-dependent … and stays in the
  denominator"). A tactic that cannot be checked in 600 s is not a successful next tactic.
- Raising the cap would "recover" them only in the sense of converting a timeout into a verdict,
  and would do so **asymmetrically across models** — which is a worse bias than leaving them in.
  If the cap is raised, it must be raised and re-run for **all 21 lanes**, not just the affected
  ones.
- At ≤5 cells out of 712 (≈0.7%) the choice cannot move any reported contrast; document it and
  move on.

---

## 6. Recovery options — cost/benefit

Generation is done and paid for. Everything below is **verification-only compute** (Lean/LeanDojo
on CPU); **no model tokens, no GPU, no EC2 required** — the 2026-08-14 pass ran on this box (F5).

| Option | Recovers | Compute | Risk | Verdict |
|---|---|---|---|---|
| **A. Re-verify the 45 `std` theorems against the current cache** | 151 cells/lane = **65% of the loss**; 712 → 863/lane; denominator 21 lanes × 151 = 3 171 verifications | Dojo session per cell; empirically ~3 s median ground-truth replay (corpus `wall_ms`), realistically minutes/theorem incl. session setup → order **hours**, single box, CPU only | Low. Must not run while the induction fleet is live (flock contention, §P2). Must re-run **all 21 lanes** or the lanes become non-comparable. | **Do it, if D1/D2 confirm the cache is now complete.** Best value in this document. |
| **B. Re-verify the 37 prefix theorems** | up to 81 cells/lane = 35% of the loss | 21 × 81 = 1 701 verifications, but long prefixes (median 7 tactics) → slower per cell | Medium: if P1 says `ProofFinished` (F8), re-running changes nothing without a code fix; if it says `LeanError`, re-running may reproduce identically | **Run P1/P3 first (free).** Only re-verify if the cause is transient or timeout. |
| **C. Re-sample the corpus to replace the 82** | restores n=300 measurable | full re-generation across 21 lanes = the entire deduction leg again | High: new theorems ≠ paired with existing results; breaks every paired McNemar already computed | **No.** |
| **D. Do nothing, document the caveat** | 0 | 0 | The write-up must carry §7 | **Acceptable fallback.** The rank orderings and the hint-vs-noise contrast are unaffected (§3c). |

**Is A worth it?** Yes, on two grounds beyond the extra 151 cells: it restores the `std` half of
the corpus, which is the *only* thing that makes the leg a "Lean" benchmark rather than a
"Mathlib" benchmark (§3a); and it is the cheap half — no model spend, no new sampling, and the
paired structure is preserved because the same 45 theorems are added back to every lane.

**Is B worth it?** Only if P3 shows timeouts. If the ground truth genuinely does not replay,
those 37 theorems should be **dropped from the corpus** (and the sidecar regenerated) rather than
retried, because a theorem whose recorded prefix does not replay cannot pose a well-defined
next-tactic question.

---

## 7. What the write-up must say, whether or not anything is fixed

Non-negotiable, in `notebooks/FAMILY_LADDER_ANALYSIS_2026-08-16.md` and anywhere deduction rates
are quoted. Hand this list to **smolbench-4d**.

1. **The denominator is 712, not 944.** 24.6% of generated cells could not be verified.
   Per-rung: `stepk:1` 218/300, `hint:2` 170/222, `hint:3` 162/211, `noise:3` 162/211.
2. **The loss is measurement, not generation.** All 944 candidates exist for every lane; 232 of
   them could not be *judged*. `audit_run_completeness.py` reporting clean is about generation.
3. **The loss is identical in all lanes** (verified on 5 lanes / 4 families, byte-identical cell
   keys; count confirmed on 2 more). Therefore **every model-vs-model contrast, rank ordering, and
   paired McNemar is unaffected** — the missing cells are concordant-missing. Say this explicitly
   so a reader does not discount the comparative findings.
4. **The `hint:3` vs `noise:3` paired contrast is on identical theorem sets** and is unaffected.
5. **Scope caveat (the 151):** 45/300 theorems — **100% of the `std`/Batteries theorems in the
   sample, 17 files** — were never verifiable. The leg measures next-tactic prediction on
   **Mathlib only**. Do not describe it as covering Lean's standard library.
6. **Difficulty caveat (the 81) — state it WITH its measured magnitude, which is small.** 37/300
   theorems were lost to ground-truth prefix-replay failure and they are **4× longer** than the
   measurable set (median 8 vs 2 tactics, 86.5% vs 18.8% at ≥5 tactics, permutation p = 5e-5).
   **But** length-matched imputation puts the resulting rate bias at **+0.000 to +0.005 absolute,
   in the pessimistic direction**, across all 5 lanes measured — because next-tactic success peaks
   at 3-4 tactics rather than falling monotonically with length. Report it as "length-skewed
   subsample, rate effect < 0.5 pt, sign slightly pessimistic". Do **not** repeat the intuitive
   but wrong claim that the rates are optimistic because the hard theorems were dropped.
7. **Bootstrap blocks are 218, not 300** (`error_bars.py` blocks over theorems; the 45 DojoInit
   *and* all 37 prefix theorems lose every cell they have). CIs computed against 300 blocks are
   too narrow by a 27.3% reduction in blocks. An intermediate figure of 255 appears in an earlier
   draft of this document and is **wrong** — do not use it.
8. **Never score the 232 as 0.** Doing so deflates every marginal rate by up to 24.6%
   (commit `39e73a0d`: gemma-4-e2b 0.110→0.083, glm-4.7-flash 0.146→0.110, ministral-3-8b
   0.073→0.055). `incomplete` is the opposite case — model-dependent, stays in the denominator.
9. **State that the sample was drawn from 805 replay-passing theorems** and that the 82 lost were
   lost *after* sampling, so the 218/712 is a non-random subsample of a random sample — which is
   why 5 and 6 are needed at all.
10. **The denominator is not constant across lanes.** `glm-4.7` and `ministral-3-3b` each lose one
    further cell to an unretried `DojoTacticTimeoutError` (recorded as `verdict="exception"` with
    no surviving attempt), so their measurable denominator is **711**, not 712. These cells are
    **model-dependent** and should be counted as failures in the denominator rather than dropped
    (§5.4) — that is a change from current loader behaviour. 8 lanes remain unscanned.
11. **`verified_rows.jsonl` is a multi-attempt log.** `ministral-3-3b` has 1 524 raw rows for 944
    cells. Any recount must apply the earliest-surviving-non-`exception` rule first; a raw
    `grep -c` gives 246 instead of 232 for that lane.

---

## Appendix — provenance of every number

| Fact | Source |
|---|---|
| 944 cells + 300 sanity/lane; verdict tallies | count over `analysis/2026-08-16/deduction/<m>/verified_rows.jsonl`, 5 lanes |
| 232 = 151 + 81; 82 = 45 + 37 | join of `sanity` verdicts to `cell` verdicts, this session |
| identical cell-key sets across lanes | set equality on `(theorem_id, rung, k, replicate_idx)`, 5 lanes |
| 232 in 6 further lanes | `aws s3 cp … - \| grep -c '"replay_failed"'` (raw; valid only for single-attempt lanes) |
| dedup rule reproduces 232 for `glm-4.7` / `ministral-3-3b` | earliest-surviving-non-`exception` per `(theorem_id, rung, k, replicate_idx)`, this session |
| 2 `DojoTacticTimeoutError` cells, no survivor | scan of `error`/`lean_error` for `DojoTacticTimeout`, 7 downloaded + 6 stream-grepped lanes |
| `verify_ms` 0 on all 232; measurable p50 212 / p90 2 676 / max 12 466 ms | `verify_ms` percentiles over gemma-4-e2b rows |
| block count 218; cells-per-theorem distributions | count of theorems with ≥1 non-`replay_failed` cell, post-dedup |
| `stepk:1` rate by length bin; imputed +0.000…+0.005 | bin rates over measurable cells, 5 lanes; imputation weights = lost-37 bin counts |
| corpus filter sidecar dated 2026-07-10 | `git log --follow -- notebooks/deduction/data/replay_passing_novel_premises_val.jsonl` |
| DojoInit error text | `sanity` rows, `error` field: `DojoInitError: Cannot find the *.ast.json file…` |
| 100% `std` / 100% `Mathlib` split | `file_path` on cell rows, bucketed |
| `n_tactics` / `wall_ms` by group | `notebooks/deduction/data/replay_passing_novel_premises_val.jsonl` joined on `full_name` |
| permutation p-values | 20 000-shuffle two-sided permutation test on the mean, seed 0 |
| per-rung loss and set differences | this session, over gemma-4-e2b |
| 805 of 1104 corpus records are `success` | `Counter` over the sidecar; `corpus.py:348` filter |
| BROKEN pass = 944/944 `replay_failed` | `deduction/runs/scaling_gemma-4-e2b/verified_rows_BROKEN-dojoinit_archived-2026-08-14.jsonl` |
| cache paths resolve, 17/17 `.ast.json` present | `lean_dojo.utils.to_json_path` + `os.path.exists`, `.venv-lean` (lean_dojo 4.20.0) |
| `CORRUPT-20260801-…` lacks the `std` build tree | `ls -ld ~/.cache/lean_dojo/*/mathlib4/.lake/packages/std/.lake/build` |
| code asymmetry | `smolbench/deduction/lean/verify.py` L212-234 vs L407-412, L~466 |
| rate deflation figures | commit `39e73a0d` message |
| `exception` excluded / `incomplete` retained rules | `scripts/snapshot_analysis_data.py` MANIFEST `notes` |

**Explicitly NOT verified in this document:** the `replay_failed` count in 8 of the 21 lanes; the
timing of the `std` build tree's appearance in the live cache (F7, closed by D1); the error strings
behind the 81 prefix failures (F9, closed by P1); whether the 81 are timeouts (P3 — `verify_ms` is
0 on every failed row, so the snapshot cannot answer it); premise-count / import-depth /
declaration-kind characterisation of the 37 (§3d); `DojoTacticTimeoutError` in the 8 unscanned
lanes; how much of the 8-theorem `hint:2`↔`hint:3` set gap is loss-induced vs by-design; and
whether the D1/D2 cache hypothesis is correct — it is the best-supported explanation, not a
confirmed one.
