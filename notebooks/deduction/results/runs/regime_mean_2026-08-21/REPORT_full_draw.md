# regime-completion — the section-7.2 regime-mean draw, finished

## Verdict

**By the preregistered rule the rerun-higher shift SURVIVES — at the bottom edge of
the window — and it does NOT reach significance (McNemar exact p = 0.243).**

The decision rule was fixed *before* these cells were graded
(`preregistered_framing.md`, 21:45Z). Rule 1's test is that the pooled estimate sits in
[2.0, 4.5] pt and the flip rate inside the committed CI: the estimate is
**+2.01 pt** and the flip rate **0.090** in [0.061, 0.127], so both hold. Rule 3's
"dissolves" test (below ~1.5 pt, or a sign flip) does not fire. The scored answer is
therefore *survives*, and it is recorded as such rather than re-scored after the fact.

State the boundary plainly, though: **2.01 pt sits 0.01 pt above a 2.0 pt
floor**, so the classification would flip on a single discordant cell. And two caveats
carry more weight than the label:

1. **The effect roughly halved.** +3.22 pt on the committed n=311
   became +2.01 pt on n=399. The added cells moved the estimate DOWN, not toward
   significance. `preregistered_framing.md` projected the CI lower edge landing on zero and
   p near 0.05 *assuming the new cells behaved like the 311 already drawn*. They did not:
   leg 2 went from +2.70 pt on 111 cells to +0.50 pt on 199.
2. **The one process drawn fresh for this package reversed sign.** Box 4 — 87 cells,
   the largest leg-2 stratum — came back at **-2.30 pt**, the only
   negative stratum of the four. The four are not statistically heterogeneous
   (Q = 2.95, df = 3, p = 0.399), but that test cannot resolve a 2-pt
   effect against per-stratum SEs of 3.2–4.3 pt, so "homogeneous" means "undetectably
   different", not "agreeing".

**What this draw establishes: a BOUND, not an effect.** MDE80 (cluster) is
4.40 pt against a point estimate of 2.01 pt — n=399 is underpowered
for its own effect size. Per rule 2, a p just under and just over 0.05 would carry identical
weight here; at p = 0.243 the question does not arise. Cross-process pass@1
variation is bounded by roughly ±5 pt; a persistent rerun-higher shift is not established.

## Headline (pooled, n = 399 cells over 189 theorems)

| quantity | value |
|---|---|
| a / b / c / d | 19 / 14 / 22 / 344 |
| pass@1 study → rerun | 0.083 → 0.103 |
| **flip rate** (b+c)/n | **0.090** — Clopper-Pearson [0.064, 0.123], cluster-boot [0.061, 0.123] |
| **mean shift** (c−b)/n | **+2.01 pt** |
| **cluster-boot 95% CI** | **[-1.01, 5.19] pt** (boot SE 1.57 pt) |
| naive 95% CI | [-0.94, 4.95] pt (SE 1.50 pt) |
| **McNemar exact p** | **0.243** |
| design effect (cluster/naive) | 1.09 |
| **MDE80 (cluster)** | **4.40 pt** (naive 4.20 pt) |

## Movement from the committed draw

| | committed n=311 | full n=399 |
|---|---|---|
| mean shift | +3.22 pt | **+2.01 pt** |
| cluster CI | [-0.32, 6.86] | [-1.01, 5.19] |
| flip rate | 0.090 | 0.090 |
| McNemar p | 0.087 | 0.243 |
| MDE80 cluster | 5.07 pt | 4.40 pt |

The added cells moved the estimate DOWN, not toward significance. The projection in
`preregistered_framing.md` (CI lower edge landing on zero, p near 0.05) assumed the
new cells would behave like the 311 already drawn. They did not: leg 2 went from
+2.70 pt on 111 cells to **+0.50 pt on 199**.

## Per-leg and leg heterogeneity

| leg | n | theorems | b/c | flip | shift (pt) | cluster CI | McNemar p |
|---|---|---|---|---|---|---|---|
| leg 1 (2026-08-18) | 200 | 137 | 6/13 | 0.095 | +3.50 | [-0.50, 7.65] | 0.167 |
| leg 2 (2026-08-21) | 199 | 130 | 8/9 | 0.085 | +0.50 | [-3.61, 4.93] | 1.000 |

Leg heterogeneity: diff 3.00 pt, SE 3.00 pt, **z = 1.00**.
The legs remain formally consistent, but the gap widened from
0.80 pt (z = 0.22) as leg 2 filled in.

## Per-process split — preregistration rule 5

| stratum | n | b/c | flip | shift (pt) | cluster CI |
|---|---|---|---|---|---|
| `leg1_box0_20260818_g6e2xl_usw2a` | 200 | 6/13 | 0.095 | **3.50** | [-0.50, 7.65] |
| `leg2a_box1_2_20260821_g6e4xl_use2` | 43 | 1/1 | 0.047 | **0.00** | [-6.67, 6.67] |
| `leg2b_box3_20260821_g6e2xl_use1d` | 69 | 2/5 | 0.101 | **4.35** | [-3.17, 13.24] |
| `leg2c_box4_20260821_completion` | 87 | 5/3 | 0.092 | **-2.30** | [-8.75, 3.70] |

Homogeneity across 4 serving processes: **Q = 2.95, df = 3, p = 0.399**;
inverse-variance weighted mean 1.75 pt.

The four strata run 3.50 /
0.00 /
4.35 /
-2.30 pt. Box 3 and box 4 are the SAME instance type in the SAME
AZ (g6e.2xlarge, us-east-1d) on the same day under the same pinned reconstruction,
and they differ by 6.65 pt
with opposite signs. That is the cleanest statement the draw supports: **the sign of the
rerun-vs-study shift is not stable across serving processes.**

Read that claim at its true resolution, though: it rests on **single-digit discordant
counts per stratum**. Box 4's -2.30 pt is b=5, c=3 — 8 discordant cells out of 87;
box 3's +4.35 pt is b=2, c=5 — 7 out of 69. Every
per-stratum McNemar p is ≥ 0.17. The instability is real in the sense that no
stratum reproduces the pooled estimate, but no single stratum on its own excludes zero.

## What was regenerated

* The committed draw stood at n=311 because three spot reclaims cut the leg-2
  sweep at 112 of its 200 whitelisted cells; the COMPLETE-THEOREM rule (a theorem with
  any missing whitelisted cell contributes nothing, so a truncated sweep cannot bias the
  rung mix) left only 111 analyzable pairs.
* This package regenerated **exactly the 88 missing cells** (65 theorems) on
  box 4 under the identical pinned stock reconstruction, then verified and merged them.
* Target was 400 analyzable; **actual is 399** = leg 1 200 + leg 2 199.
  The single missing pair is `CategoryTheory.Limits.Types.colimit_sound k=0 stepk:1`,
  whose rerun candidate is a **110,920-character runaway generation that crashes the Lean
  Dojo subprocess deterministically** (`DojoCrashError: Unexpected EOF`, 2 of 2 isolated
  attempts at workers=1; the theorem's own ground-truth sanity replay succeeds 1/1).
  `load_leg` classes a rerun `exception` as infrastructure rather than a measurement and
  drops the theorem — the same rule that produced the committed n=311, applied unchanged.
  That theorem has exactly one whitelisted cell, so the cost is one pair.

## Two defects found and fixed in the verification tail

`verify_run` could not be used against the run dir for a SECOND generation pass:

1. **Index misalignment (loud).** It seeds `out_rows` from the prior
   `verified_rows.jsonl` (243 rows) but computes `pending` indices against the new
   `all_rows.jsonl` (331 rows), so `fan_out_verdict` raised `IndexError` on the appended
   cells. Its invariant ("a prior upload never reorders or removes anything") holds only
   while `all_rows.jsonl` is frozen after a verification pass. Audited: the first 243
   positions ARE aligned (0 mismatches) and the run crashed before its first checkpoint
   upload, so `verified_rows.jsonl` stayed byte-identical to `backup_pre_r6`
   (sha `12e06467…`). Nothing was corrupted.
2. **Resume-by-group would have silently skipped a cell (quiet — the dangerous one).**
   `resume_done_groups` marks a whole `(theorem_id, k)` group done if ANY of its cells has
   a verdict. Exactly one new cell — `Prod.swap_iInf k=0 hint:2` — shares a group leg 2
   already finished, which is why the crashed run reported 87 pending rows for 88 new
   cells. It would have stayed `unverified` forever and its theorem would have been
   dropped with no error raised.

Fix: verify the 88 in isolation via `_LocalRunClient` in a scratch dir with
`no_resume=True` (the pattern the pre-spend drift gate already proved on this machine
today), then merge explicitly. Same verifier, same env, same workers — the verdicts come
from the verifier that graded legs 1 and 2.

## Gates

* **Pre-spend drift gate (banked, not redone):** 88/88 of the 88 originals'
  verdicts reproduced against BOTH leg-2's same-day verdicts and the study verdicts
  (agreement 1.000, zero disagreements). `GITHUB_ACCESS_TOKEN` UNSET (anonymous LeanDojo),
  identical to legs 1 and 2.
* **Content gate on the rerun side (folded into the merge):** 88/88 completion
  cells graded, verdicts {'lean_error': 75, 'incomplete': 4, 'exception': 1, 'given_up': 2, 'success': 6}; exception+replay_failed = 1,
  under the 5% abort ceiling. This reads VERDICTS, not row counts — counts alone once
  certified a lane that had lost 93.8% of its cells.
* **Leg-completeness gate (run before pooling):** leg 1 200/200 with
  0 theorems dropped; leg 2 199/200 with
  1 dropped, and the one drop is the audited Dojo-crash cell.
* **Verifier drift, pooled:** 399/399 agree (rate 1.000).
* **Transport-fault guard:** empty rerun candidate proofs with prompt_tokens>0 = 0 (both legs).

## Identity of the reconstruction

build dev122, image `vllm/vllm-openai@sha256:26354b5e…`, weights digest `95c2fc6e…`,
hf_revision `dfaf35de`, tp=1, seed 0, temp 0.7, max_tokens 32768, stock args incl.
`--enable-prefix-caching`. Box 3 vs box 4 `server_config` differ ONLY in instance id, GPU
UUID and timestamp (`server_config_box3_vs_box4_diff.json`). Estimator byte-identical to
the committed run: `sha256(pool_analyze.py) = 3824a49b1eb9489f…`, equal in r5 and r6.

## Spend and teardown

```json
{
  "box4_i-0e9b39efb4cdd6c8b": {
    "type": "g6e.2xlarge",
    "az": "us-east-1d",
    "up_start_utc": "21:37:26",
    "rate_usd_hr": 1.9564,
    "status": "TERMINATED (verified 3 regions, teardown_final.txt)",
    "down_utc": "23:26:22",
    "uptime_hours": 1.8156,
    "cost_usd": 3.55
  },
  "cap_usd": 12,
  "note": "single box, single leg, generation only; r5's boxes 1-3 ($5.35) are NOT recharged here. Verification tail is local CPU (LeanDojo), zero EC2.",
  "total_this_package_usd": 3.55
}
```

Box `i-0e9b39efb4cdd6c8b` (g6e.2xlarge, us-east-1d) was terminated by the driver's own
`finally: ec2.shutdown_instance()` at 23:26:22Z — before the verification tail, which is
local CPU only and needed no GPU. Verified terminated across us-east-1 / us-east-2 /
us-west-2: **zero instances tagged `smolbench:experiment=flip2-nemotron-3-nano-4b` in any
region**, and box 4 explicitly `terminated` by instance id (`teardown_final.txt`).

Two teardown notes worth carrying forward:

* `teardown_r6.sh` / `teardown_final.sh` filtered on tag key **`Experiment`**, but the real
  key this repo writes is **`smolbench:experiment`**. That filter matched nothing and its
  terminate step was a silent no-op. It did not cost anything here — the driver terminated
  its own box and the explicit instance-id check is what actually confirms teardown — but a
  run that relied on the tag sweep to catch a leaked box would have been told "clean" while
  the box billed. Fix the key before reusing those scripts.
* One foreign instance is running and is **NOT this package's**:
  `i-047406b97c0d2a80f`, p5.48xlarge spot, us-west-2b, launched 23:48:39Z, tagged
  `smolbench:experiment=moetp8` — the concurrent MoE-tp8 workflow. It was deliberately left
  alone. (Also present: `i-0e52cb0bb33999a94`, m7i.16xlarge, **stopped** since 2026-08-16,
  tagged `verify-lean`.) Flagging it because a p5.48xlarge is the most expensive box in this
  account's rotation and it should be confirmed as intentionally owned by that workflow.
