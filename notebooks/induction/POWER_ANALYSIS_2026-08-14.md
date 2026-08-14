# Family-ladder induction — power analysis run, 2026-08-14

Run of `notebooks/induction/power_analysis.py` against the landed results of
the in-flight family-ladder scaling study. Raw stdout and the S3 listing that
produced it are in the session scratchpad
(`induction_power_2026-08-14.txt`, `s3_snapshot_2026-08-14.txt`).

## READ THIS FIRST — the underlying statistic is under active challenge

`MULTIPLICITY_PLAN.md` (uncommitted, same directory, written 2026-08-14) argues
that **the test every number below is sized against is the wrong test for this
design**, on two counts:

1. **The design is paired; `cmh_reject` is not.** All 21 models and all 4 info
   arms face byte-identical items at a given seed, so all 210 PRIMARY contrasts
   are matched on item — yet `cmh_reject` draws two *independent* binomials.
   Its table: to match a **paired** R=30, an unpaired test needs **R = 35–85**
   (1.17x–2.83x, worst at ceiling, where `DE = 2pq/d` blows up).
2. **The stratified CMH does not hold its nominal level here** — each seed
   contributes one unit to all 9 harmonic strata, which CMH sums as if
   independent; reportedly up to 56x the nominal alpha = 2.38e-4.

**UPDATE 2026-08-14 (later): the pairing hypothesis is REFUTED; the real cause
is compliance contamination.** The paired re-analysis has since been run
(`paired_analysis.py`, exact McNemar on item-matched marks, Holm over the 210):
it changes **exactly one** contrast of 210 (`[nemo3 ladder | intens]
nemo3_30b vs nemo3_120b`). Pairing buys almost nothing here because the real
ceiling pairs have *exactly zero* discordant items (b/c = 0/0), and no test
extracts signal from zero discordance — the 53x figure held only for the
simulated low-but-nonzero-discordance regime. The measured clustering design
effect is likewise modest: median **1.124**, p90 **1.881**, max 2.97 (not the
56x worst-case bracket).

So R=78 is **not** a pairing artifact. It is contaminated at source: the
headline is driven by `[min3 ladder | intens] min3_3b vs min3_14b`
(0.44 vs 0.33), and those two lanes' *intens* marks are **13.7%** and **56.5%**
non-compliant respectively (verified independently over the landed data);
min3_14b is additionally incomplete at **23/30 seeds** (PROVISIONAL — see below).
The runner-up driver, min3 extens (77), is 57.0% / 82.6% non-compliant. Do not
act on R=78.

**PROVISIONAL — the 23/30 figure is expected to expire.** The min3_14b lane is
MID-REPAIR, not frozen: the silent-delivery root cause is fixed (27fd1c1a, TCP
keepalive on completion sockets) and the 7 remaining seeds are queued to
relaunch behind an A/B gate (e59b81f0). Do **not** harden 23/30 into a "77% of
intended data" caveat — re-derive the min3 contrasts once the lane drains.
Note the two defects are independent: draining fixes 23/30 and does nothing for
the 27.5%-compliant problem, which more seeds cannot improve.

Everything below is a faithful run of `power_analysis.py` **as it exists
today** (the plan is explicitly "not yet implemented"). It is reported because
it was asked for, not because its R recommendation should be acted on.

## What this analysis is (and is not)

It is a **PROSPECTIVE sizing** analysis. `load_outcomes()` reads exactly one
replicate per condition — `{model}_{info}/rep_0.yaml`, the seed-0 pilot — and
simulates forward to recommend R. It does **not** consume the ~30 landed
replicates per lane, and it is **not** an achieved-power statement about the
data already collected. Read every number below as "what the pilot implies R
should be", not "the study is/isn't powered".

## Provenance

- `EXPERIMENT.harness.sync_down()` pulled **2492 objects** from
  `s3://smolbench-results-414266451290/induction` into the local
  `{model}_{info}/rep_{seed}.yaml` layout (local tree was empty beforehand,
  so nothing was overwritten).
- All **84/84** pilot files (21 models x 4 infos) present, each with exactly
  9 `score:` lines.
- **Landed depth: R=30 for 20 of 21 lanes.** `min3_14b` was at 23/30 and
  still collecting during this run (the live ministral-3-14b re-run).
- **Pilot contamination check (per `CONFOUND_AUDIT_2026-08-13.md`):** the
  three homogeneity re-run lanes each have a *complete, single-timestamp*
  seed 0, so newest-wins yields a single-config pilot with no mixing:
  gemma-4-12b `20260814T014756Z`, ministral-3-14b `20260814T044724Z`,
  deepseek-v4-flash `20260813T210643Z`. The 96 seed-0 objects in S3 = 84 live
  + 12 superseded.
- Run **locally**, deviating from the [[analysis-on-remote-compute]]
  directive — see "Deviation" below.

## Headline

```
Recommended replicates per condition (max feasible PRIMARY R at 80%): 78
```

Driven by `[min3 ladder | intens] min3_3b vs min3_14b` at 0.44 vs 0.33.
Runners-up: min3 extens (77), glm_flash vs glm_air extens (75).

As in the parent periodic study, this headline is the
**"treat every PRIMARY contrast as a difference test"** number, which the
design explicitly declines. Decomposed under the study's own hybrid logic:

| family | n | R needed |
|---|---|---|
| separated contrasts (R80 <= 20) | 131 | **<= 17** |
| near-ties (R80 > 20 or > 200) | 79 | TOST: **109** @ +/-0.10, **49** @ +/-0.15, **28** @ +/-0.20 |

(131 + 79 = 210 PRIMARY contrasts.)

## Tier-1 family omnibus gates

The script reports these at `r_star` = 78 only. Recomputed here at the
collected R=30 (`omnibus_power`, freshly-seeded rng per call, matching the
script's convention):

| family | R=30 | R=49 | R=78 |
|---|---|---|---|
| qwen35, nemo3, gemma4, glm, min3, exaone, ds | 1.000 | 1.000 | 1.000 |

All seven gates are saturated at R=30. **The gates are not the constraint.**
(At R=1 they are not: qwen35 0.000, ds 0.001, min3 0.030, nemo3 0.642.)

## Bottom line for the R=30 being collected

- Of the 210 PRIMARY contrasts, the **131 the pilot could resolve** are covered
  (need <= 17), and all 7 family gates are at 1.000. The remaining **68 came
  back `>200`** — pairs at 1.00 vs 1.00 or otherwise indistinguishable *in a
  9-question pilot*. They are in the near-tie/TOST family **by assumption, not
  by evidence**: if any is a real difference at R=30, nothing in this table
  anticipated it. (This is also precisely the population the paired test would
  rescue — see the banner; ceiling pairs are where `DE = 2pq/d` pays most.)
- What R=30 **cannot** support is periodic's equivalence standard. The 79
  near-ties can only be certified equivalent within **+/-0.20** at R=30
  (needs 28); matching the parent study's **+/-0.15** would require R=49,
  i.e. R=50 with periodic's +1 headroom.
- So: R=30 is adequate for the difference claims and one notch loose on the
  equivalence claims. The paired re-analysis does **not** close the gap (it
  moves 1 of 210 contrasts), so this was a real choice and not an artifact of
  the statistic: widen the stated bound to +/-0.20, or extend to R=50.

**DECIDED (2026-08-14): WIDEN TO +/-0.20, collect nothing further.** Recorded in
`35e7cfb8`; the decision was taken in the `smolbench-4d` session, whose
ownership of this workstream was contested and unresolved at the time (see the
study memory brief) — so attribute it rather than reading it as the study's
uncontested final word. Rationale, which belongs in the methods and not a
footnote because a reader comparing to the parent periodic study will ask why
the bound differs: the ceiling near-ties sit at 1.00 vs 1.00 with **zero
discordant items**, and at zero discordance NO replicate count resolves them.
That is an identification limit, not a power shortfall — which is the argument
against buying 20 more replicates to tighten a bound around them.

## Caveats

1. Prospective, pilot-sized (one 9-question quiz per condition), c=1
   shrinkage toward the condition mean — same assumptions as the parent
   study, and the same sensitivity: the `R80 pooled` column is the check.
2. **Mid-flight.** `min3_14b` was actively collecting during this run and its
   seed-0 pilot was ~6 h old; min3 contrasts drive the headline, so this
   lane's numbers are the least stable in the table.
3. Not an achieved-power analysis. Computing achieved power over the 30
   landed seeds is different code that does not exist yet.

## Deviation from the remote-compute directive

[[analysis-on-remote-compute]] (2026-08-01) says results analysis runs on
Claude remote compute, with artifacts committed first so the remote
environment can see them. That mechanism predates the S3 store (live
2026-08-10): this study's results are **not** in the repo, and `sync_down()`
needs local AWS credentials from gitignored `keys.env` / `ec2-operator.env`,
which a remote checkout does not have. The sync therefore had to happen
locally; the compute was run locally too rather than shipping a 2492-file
untracked tree to a remote agent. The directive's *why* (flaky local box)
still stands — the run completed cleanly in ~9 min, exit 0.
