# Lean-4 Deduction: Powered Results for Two Model Trios

Model-comparison study on the `smolbench.deduction.lean` next-tactic harness. Two
completed base-model runs live under `notebooks/lean/results/runs/`:

- **`lean_arch`** — the ARCHETYPE trio (same models as the `notebooks/periodic`
  induction study): `llama-31-405b` (decode), `nemotron-ultra-253b` (cot),
  `llama4-maverick` (moe).
- **`lean_moe`** — the all-MoE trio (same models as `notebooks/periodic_moe`):
  `gpt-oss-120b`, `nemotron-3-super-120b-a12b`, `qwen3.5-397b-a17b`.

## Setup

- Theorems: `novel_premises/val`, `limit=300`, `seed=1776`, source `replay_passing`.
  After model-independent corpus/trivial skips, **252 theorems are paired** across
  all three models of each trio (840 gradeable `(theorem, rung)` cells per model).
- Rungs (ladder of proof context handed to the model): `stepk:1` (baseline, least
  context) → `hint:2` → `hint:3` (help ladder) → `noise:3` (length control).
- `R=1` rollout, `temperature=0.7`, `max_tokens=32768`, base (non-LoRA) models.
- **Success** = the generated tactic Lean-verifies as `ProofFinished`
  (`verdict == "success"`), measured **pass@1**.

## Method — `notebooks/lean/power_analysis.py`

The "result" being measured is a **ranking of models by next-tactic success rate**.
The sizer asks, for each of the three model pairs in a trio, whether the pair is a
genuine DIFFERENCE (and at what `n_theorems` it separates at ≥80% power) or a
near-TIE (certified equivalent within a ±0.10 band) rather than left ambiguous.

- **Unit** = one `(theorem_id, k, rung)` cell; the three models see the SAME cells,
  so every pair is a PAIRED comparison. Test = **McNemar's exact test on the
  discordant cells**, **stratified by rung** (difficulty varies systematically with
  the rung; pooled McNemar is the conservative single-stratum collapse used for
  sizing).
- **`n_theorems` sizing = block bootstrap of the REAL joint cells.** Resample whole
  theorems (each block carries all its rungs, preserving within-theorem cross-rung
  correlation) up to a target `n_theorems`, recompute each pair's McNemar p, report
  the rejection rate. Uses the effect sizes actually observed — no parametric
  assumption. The equivalence verdict reads the 90% bootstrap CI of the paired
  rate-gap against the ±0.10 band.
- **pass@N advisory** = a Beta-mixture projection of unobserved rollouts (shared
  coarse per-theorem difficulty + idiosyncratic per-model skill), asking whether
  adding rollouts buys separation.

### Headline methodological finding

**`n_theorems` is the confidence lever; adding rollouts does NOT separate models.**
For a near-tie, the pass@N advisory shows power *falling* as N grows (e.g. MoE
gpt-oss~qwen3.5: `1.00→…` for the true differences but `0.02→0.00` for the tie as
`N: 1→8`). This is the **pass@N ceiling effect**: as N rises, both models saturate
toward the theorem's solvable ceiling, discordant cells vanish, and McNemar loses
power. Only adding theorems adds discordant cells. Rollouts are therefore useless
for separating close models — a wider theorem sample is the only lever.

---

## Archetype trio (`lean_arch`) — a certified three-way near-tie

Per-model pass@1 over the 252-paired-theorem / 840-cell set:

| Model | pass@1 | cells | stepk:1 | hint:2 | hint:3 | noise:3 |
|---|---|---|---|---|---|---|
| Llama-4-Maverick (moe) | **0.205** | 172/840 | 0.06 | 0.27 | 0.27 | 0.26 |
| Llama-3.1-405B (decode) | **0.182** | 153/840 | 0.03 | 0.25 | 0.26 | 0.23 |
| Nemotron-Ultra-253B (cot) | **0.181** | 152/840 | 0.05 | 0.25 | 0.26 | 0.21 |

Union-solvable (any model): 0.360. Per-rung n ≈ 252/200/195/195 (stepk:1/hint:2/hint:3/noise:3).

**Pairwise power verdicts** (Bonferroni α = 0.05/3 = 0.0167; band ±0.10):

| Pair | gap | verdict |
|---|---|---|
| Llama-3.1-405B vs Llama-4-Maverick | −0.023 | **NEAR-TIE** — equivalent within [−0.06, +0.01] at n=300 |
| Llama-3.1-405B vs Nemotron-Ultra-253B | +0.001 | **NEAR-TIE** — equivalent within [−0.03, +0.03] at n=300 |
| Llama-4-Maverick vs Nemotron-Ultra-253B | +0.024 | **NEAR-TIE** — equivalent within [−0.01, +0.06] at n=300 |

**No difference pair reaches 80% power within n≤300** — the bootstrap power for the
two maverick pairs is only ~0.27 even at n=300. All three pairs are certified
equivalent within ±0.10. The pass@N advisory tops out at 0.14 (N=1) and *falls* with
more rollouts, confirming rollouts cannot rescue separation.

The full-run spread is only **~2pp** (maverick 20.5% vs 18.2% / 18.1%). The study's
earlier 30-theorem pilot sizing had left an impression of a larger (~7pp) maverick
edge; the full n=252 run dissolves it to ~2pp, and the power analysis shows even that
2pp is **statistically indistinguishable from zero** at any feasible n. This is the
"replicate, don't re-size" lesson made concrete: a ~2pp truth is pure noise at n=30.

---

## MoE trio (`lean_moe`) — gpt-oss ≈ qwen3.5 near-tie ≫ nemotron-3

Per-model pass@1 over the 252-paired-theorem / 840-cell set:

| Model | pass@1 | cells | stepk:1 | hint:2 | hint:3 | noise:3 |
|---|---|---|---|---|---|---|
| gpt-oss-120B | **0.330** | 277/840 | 0.23 | 0.38 | 0.37 | 0.38 |
| Qwen3.5-397B | **0.320** | 269/840 | 0.16 | 0.40 | 0.37 | 0.39 |
| Nemotron-3-Super-120B | **0.106** | 89/840 | 0.07 | 0.15 | 0.10 | 0.12 |

Union-solvable (any model): 0.455. Per-rung n ≈ 252/200/194/195.

**Pairwise power verdicts** (Bonferroni α = 0.0167; band ±0.10):

| Pair | gap | verdict |
|---|---|---|
| gpt-oss-120B vs Nemotron-3-Super-120B | +0.224 | **DIFFERENCE** — ≥80% power at n=30 |
| Nemotron-3-Super-120B vs Qwen3.5-397B | −0.214 | **DIFFERENCE** — ≥80% power at n=30 |
| gpt-oss-120B vs Qwen3.5-397B | +0.010 | **NEAR-TIE** — equivalent within [−0.02, +0.04] at n=300 |

gpt-oss and qwen3.5 are a **dead heat** (gpt-oss nominally +1.0pp, certified
equivalent within ±0.10 by n=300). Both crush nemotron-3, which is separated from
each at ≥80% power with only n=30 theorems. The pass@N advisory for the tie runs
`0.02→0.00` as `N: 1→8` (rollouts hurt, not help); the two differences stay at
1.00 throughout.

**Pilot → full-n contrast (real numbers).** The R=1 30-theorem pilot
(`lean_moe_pilot`, 22 paired theorems) point-estimated **qwen3.5 0.299 > gpt-oss
0.247 ≫ nemotron-3 0.065** — i.e. it put qwen ~5pp *ahead* and nemotron at 6.5%.
The full n=252 run **reverses the nominal order to a certified tie** (gpt-oss 0.330 ≈
qwen 0.320) and lifts nemotron-3 to **0.106**. The pilot over-stated qwen's lead and
under-stated the weakest model's floor; note that even the pilot's bootstrap refused
to separate the gpt-oss~qwen pair (equivalent within [−0.09, −0.01] at n=300),
correctly flagging it as a near-tie despite the misleading point estimate.

---

## Cross-eval synthesis

- **The Nemotron variant is the weakest of its trio on deduction, in both studies.**
  In the MoE trio, `nemotron-3-super-120b` collapses to 0.106 while its two
  trio-mates sit at ~0.32 — the same Nemotron-specific weakness the induction studies
  found (`notebooks/periodic_moe`: nemotron-3 extensive-listing collapse to 0.444
  vs ~0.97 trio-mates). Qwen leads (or ties for the lead on) both evals.
- **The near-ties are genuine, not underpowering.** gpt-oss≈qwen3.5 (~1pp) and the
  entire archetype trio (~2pp spread) are certified equivalent within ±0.10 at n=300.
  Sub-~5pp gaps between these models are **not separable at any feasible `n`**, and
  the pass@N ceiling effect means **rollouts cannot buy the separation** — only more
  theorems can, and even n=300 is not enough for a ~2pp gap.
- **Where a real gap exists it is cheap to certify.** The gpt-oss / qwen3.5 vs
  nemotron-3 differences (~0.22) clear ≥80% power at just n=30 theorems, R=1. The
  cost asymmetry is the whole story: big gaps are trivially confident, small gaps are
  hopeless — so report them as ties rather than chase them with more compute.

---

## Artifacts

- Figure: `notebooks/lean/figures/deduction_success_bars.png` (two panels, per-model
  next-tactic success by rung; generated by
  `notebooks/lean/figures/deduction_success_bars.py`).
- Power analysis: `notebooks/lean/power_analysis.py` (defaults to both full runs;
  run as `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python
  notebooks/lean/power_analysis.py`).
- Raw data: `notebooks/lean/results/runs/lean_arch/` and `.../lean_moe/`
  (`all_rows.jsonl`, `analysis.txt`, `manifest.json`).
