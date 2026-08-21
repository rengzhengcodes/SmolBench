# Serving-stack confound audit — family-ladder study (2026-08-13)

Adversarial audit of every mid-lane serving-stack change since study launch
(commit 90ded367, 2026-08-11), cross-referencing the commit history against
per-seed S3 timestamps and fleet-log launch records. Run by a dedicated
audit agent at user request; annotations in [brackets] record the operating
session's dispositions. The append-only results store carries NO serving
metadata, so this document is the authoritative timestamp -> config map for
analysis.

A "confound" here = a change to instance/GPU type or count, tp, vLLM
image/flags, or prompt content, with some of a lane's seeds landing on each
side. Timeout/monitoring/scheduling changes are not confounds.

> **[Corrected 2026-08-21 — SELECTION RULING SUPERSEDES THIS DOCUMENT'S
> CONFIG MAP.]** The user ruling of 2026-08-16 is **EARLIEST-logged-run wins,
> both legs**. Consequences for this audit, which was written under
> newest-wins:
>
> * **Contamination rule 4 below is VOID.** Analysis does not read through
>   newest-run_ts-wins, and the re-collections therefore do NOT make the
>   three re-run lanes single-config.
> * The "Per-lane serving configs" table's rows for **`gemma-4-12b`**,
>   **`ministral-3-14b`** and **`deepseek-v4-flash`** describe the NEWEST
>   attempts, i.e. the re-collection stacks — not the data actually analyzed.
> * Under earliest-wins those three lanes are internally **era-SPLIT**, not
>   single-config and not uniformly pre-re-collection: the re-collections
>   also supplied seeds that had no earlier attempt, so each lane mixes
>   stacks within its own 30 seeds. Measured from the per-seed `date:` fields
>   of the earliest-selected tree:
>   * `gemma-4-12b` — 14 seeds (0-13) on the old g6e history + 16 seeds
>     (14-29) from the g7.12xlarge re-run.
>   * `ministral-3-14b` — 9 + 14 + 7 across THREE eras: seeds 0-8 on the
>     2026-08-11/12 g6e stack, seeds 9-18 and 20-23 from the 2026-08-14
>     g7.24xlarge re-collection, seeds 19 and 24-29 from the 2026-08-16
>     streaming-transport refill. (Verified against the per-seed `date:`
>     fields; the 7 refill seeds are the same ones PASS_AT_1 §2.5 counts as
>     "28 = 7 seeds × 4 arms".)
>   * `deepseek-v4-flash` — 12 pre-B200 seeds + 18 B200 seeds.
>
> Everything else in this document (the single-config lane clearances, the
> deduction segmentation, the box-to-box result) is unaffected — but note that
> wherever the text argues a clearance *from* newest-wins selection — as the
> in-flight re-collection bullets under "Cleared" do — that argument is void too. The
> original text is left in place as the dated record of the newest-wins era.

## Confirmed, and their dispositions

### gemma-4-12b: THREE configs across seeds 0-13 -> CURED by full re-run
- seed 0: tp=1 on 1x L40S (certain).
- seeds 1-4: tp UNRESOLVABLE (serving box at 18.217.186.98 has no launch
  record in any log; result YAMLs carry no instance metadata; CloudTrail
  could settle it but re-running is cheaper).
- seeds 5-13: tp=4 on g6e.12xlarge (post-300f51b0).
- [DISPOSITION: all 30 seeds are being re-collected on g7.12xlarge (2x RTX
  PRO 4500, SM120, derived tp=2) via INDUCTION_FORCE_RERUN + 3-way sharding,
  user-approved 2026-08-13. Newest-run_ts-wins supersedes the mixed history;
  the old tp1/tp4 results remain in the log as prior versions. The lane's
  analyzed data will be single-config.]
  [Corrected 2026-08-21: VOID under the 2026-08-16 earliest-wins ruling. The
  analyzed lane is era-split 14 old-g6e seeds (0-13) + 16 g7.12xlarge seeds
  (14-29), not single-config. See the header note.]

### deepseek-v4-flash: SM90 (seeds 0-11) vs SM100/B200 (seeds 12-29)
- Documented deliberately at migration (9f6e98a2). Audit adds:
  (a) within the SM90 era the lane mixed H100 (p5) and H200 (p5e) boxes --
      same kernels/flags, per-seed GPU model recoverable only from log
      ordering; lowest severity.
  (b) the deduction leg runs on the B200 stack -- comparable to induction
      seeds 12-29 but not 0-11.
- [DISPOSITION: pending user decision on re-running seeds 0-11 on the B200
  (~$85, ~2 h at measured pace), which would make the lane fully
  homogeneous incl. the deduction leg.]

## Cleared (verified non-confounds)
- WHITESPACE_UNITS noise-pad change (bf628d1d): predates the first result
  in the bucket by 11 minutes; appended-last so working tokenizers keep
  byte-identical prompts.
- deepseek-v4-pro: despite five config iterations, ZERO results predate the
  final B200 recipe -- all 30 seeds + deduction on one box, one config.
- deepseek-v3.1: whole lane on a single box in one morning.
- CoT threshold/wiring commits: monitoring-only; request args never changed.
- Prompt/template content: untouched since launch.
- ministral-3-14b (through seed 8): one instance type, tp=4 throughout.
  [Seeds 0-29 are being fully re-collected on g7.24xlarge tp=4 anyway,
  user-approved -- so this lane also ends single-config.]
- ~~Mixed 1/4-GPU boxes on tp=1 lanes (ministral-3-3b, nemotron-nano-4b):
  static tp=1 throughout, same L40S silicon; idle GPUs are waste, not
  confounds.~~ **RETRACTED 2026-08-15 — MEASURED FALSE. See "Refuted
  dispositions" below.**

## Residual, documented-not-fixed
1. Unpinned vllm/vllm-openai:nightly digest drift WITHIN five multi-day
   lanes (gemma-4-12b [superseded by re-run], ministral-3-14b [superseded],
   glm-4.7-flash, exaone-4.5-33b, qwen3.5-27b) and across induction ->
   deduction gaps for four lanes. Docker Hub keeps no tag history; which
   pull got which build is unrecoverable. Likely >= 2 vLLM builds inside
   each. All 13 single-day lanes are immune. The replication study should
   pin a digest fleet-wide.
2. The store's append-only keys carry no serving config: this file is the
   map. The replication config should log instance type / tp / image digest
   into each result YAML.

---

# Addendum 2026-08-14: final serving-config record + contamination rules

The user directive of 2026-08-14 ("the results logging pipeline should store
what server configuration it was run on; for now, we still have that info,
so write it down") is discharged in two parts: commit 040d2e83 makes every
FUTURE result self-describing (`Marks.server_config` on induction replicates,
a timestamped `server_config.yaml` sidecar in every deduction run_dir), and
this addendum is the authoritative record for everything collected BEFORE
that commit. Compiled from the per-lane fleet logs' provision/reattach
records (`notebooks/induction/results/fleet_logs/<model>.log`), cross-checked
against S3 per-seed timestamps.

## Re-run resolutions (updates to the 2026-08-13 sections above)

- deepseek-v4-flash: seeds 0-11 re-collected on the B200 box, verified in S3
  (4 fresh arm files per seed, >= 2026-08-13T20:20Z), completed
  2026-08-14T01:55Z. The WHOLE lane -- 30 induction seeds AND the deduction
  leg -- is now homogeneous p6-b200.48xlarge (8x B200, tp=8, marlin-less
  native MXFP4, CUDA graphs). Both confound items for this lane are CLOSED.
- gemma-4-12b: full 30-seed re-collection in flight on 10x g7.12xlarge
  (2x RTX PRO 4500 32GB, SM120, derived tp=2), us-west-2b. Analyzed data =
  newest-run_ts-wins; freshness cross-check: LastModified >= 2026-08-14T01:00Z
  (the two killed interim fleets banked ZERO seeds).
- ministral-3-14b: full 30-seed re-collection in flight on 8x g7.24xlarge
  (4x RTX PRO 4500 32GB, SM120, tp=4), us-east-2c. Same newest-wins rule,
  same >= 2026-08-14T01:00Z cross-check.
  [Corrected 2026-08-21: the "analyzed data = newest-run_ts-wins" rule in both
  bullets is VOID (earliest-wins). The re-collections themselves happened as
  described; what changed is which of a cell's attempts the analysis reads. See
  the header note for the resulting era splits.]

## Per-lane serving configs (analyzed data, after newest-wins)

*[Corrected 2026-08-21: "analyzed data" holds for 18 of 21 lanes. Under the
2026-08-16 earliest-wins ruling the `gemma-4-12b`, `ministral-3-14b` and
`deepseek-v4-flash` rows below describe their NEWEST attempts, not the analyzed
data; those three lanes are era-split. See the header note.]*

| lane | induction | deduction |
|---|---|---|
| qwen3.5-27b | g6e.12xl (4x L40S, tp=4), boxes in us-east-2c + us-east-1d | same type; TWO completed sweeps, see segmentation note |
| qwen3.5-122b-a10b | p5.48xl (8x H100, tp=8) x2 boxes us-east-2c | same type |
| qwen3.5-397b-a17b | p5e.48xl (8x H200, tp=8), ONE box us-west-2c | same box |
| nemotron-3-nano-4b | g6e.4xl/g6e.8xl (both 1x L40S, static tp=1) -- **CONFOUNDED, see Refuted dispositions** | g6e.4xl then g6e.2xl -- **CONFOUNDED (measured 0/8)** |
| nemotron-3-nano-30b-a3b | g6e.12xl (tp=4), ONE box us-west-2b | same box |
| nemotron-3-super-120b-a12b | p5e.48xl (8x H200, tp=8), ONE box us-west-2 | same box |
| gemma-4-e2b | g6e.4xl (1x L40S, tp=1) x3 boxes us-east-2 | same type |
| gemma-4-12b | RE-RUN: g7.12xl (2x RTX PRO 4500, tp=2) x10, us-west-2b **[see 2026-08-21 note: analyzed lane is 14 old-g6e + 16 g7.12xl seeds]** | TO RUN (single lane, sidecar active) |
| gemma-4-31b | g6e.12xl (tp=4), ONE box us-east-2c | same box |
| glm-4.7-flash | g6e.12xl (tp=4) x4 boxes us-east-2 + us-east-1d | same type, resumed sweep |
| glm-4.5-air | p5.48xl (8x H100, tp=8) x2 us-east-2c | same type, resumed sweep |
| glm-4.7 | p5en.48xl (8x H200, tp=8) x2 us-east-2a | same type |
| ministral-3-3b | g6e.4xl + g6e.12xl MIXED, static tp=1 -- **clearance RETRACTED** | g6e.2xl then g6e.4xl MIXED; model not reproducible on one box (0/8 baseline) so undetectable AND unverifiable by rerun |
| ministral-3-8b | g6e.12xl (tp=4), ONE box us-west-2b | same box |
| ministral-3-14b | RE-RUN: g7.24xl (4x RTX PRO 4500, tp=4) x8, us-east-2c **[see 2026-08-21 note: analyzed lane is 9 + 14 + 7 seeds across three eras]** | TO RUN (single lane, sidecar active) |
| exaone-4.0-32b | g6e.12xl (tp=4), ONE box us-east-2c | same box |
| exaone-4.5-33b | g6e.12xl (tp=4) x3 boxes us-east-2 | same type, resumed sweep |
| k-exaone-236b-a23b | p5.48xl (8x H100, tp=8) x2 us-east-2 | same type |
| deepseek-v4-flash | p6-b200.48xl (8x B200, tp=8) after re-run **[see 2026-08-21 note: analyzed lane is 12 pre-B200 + 18 B200 seeds]** | same box class, single segment |
| deepseek-v3.1 | p5en.48xl (8x H200, tp=8), ONE box us-east-2a | same box, single segment |
| deepseek-v4-pro | p6-b200.48xl (8x B200, tp=8), ONE box us-west-2b | same box; first (H200-era) attempt wrote ZERO rows -- the final segment wrote the full 944, so no p5en rows exist |

All lanes: vllm/vllm-openai:nightly (digest drift caveat above still stands),
uniform max_model_len 131072, per-model CoT wiring per EC2_DEPLOY_SPECS.

## Deduction sweep segmentation (resumed lanes)

"sweep wrote N" prints only on a COMPLETED invocation; a crashed segment
prints nothing but leaves its rows in all_rows.jsonl, and the relaunch
resumes past them. Resumed lanes and their final-segment counts: exaone-4.5-33b
(236), glm-4.7-flash (216), glm-4.5-air (434), nemotron-3-nano-30b-a3b (779),
qwen3.5-27b (231, special case below). Every resumed lane's segments ran on
the SAME instance type (verified against the provision records), so each
lane's candidate rows are type-homogeneous even where the physical box or
region changed mid-sweep.

qwen3.5-27b special case: its first sweep COMPLETED (944 rows) but the
2026-08-13 02:26 host outage hit before its end-of-run spool; the relaunch
restored 713 cells from the supervisor's periodic sync and the second sweep
wrote exactly the missing 231 (713 + 231 = 944, NO duplicate cells). Both
segments g6e.12xlarge tp=4 (us-east-2c then us-east-1d).

## Contamination rules for the verifier and the power analyses

1. The Lean verifier replays candidate tactics through LeanDojo on CPU --
   deterministic type-checking, no hardware dependence in the VERDICTS. Its
   contamination surface is row SELECTION only.
2. Deduction has NO superseded runs: exactly one run_dir per lane
   (`deduction/runs/scaling_<key>/`), never re-collected. The verifier reads
   each lane's single all_rows.jsonl; the segment analysis above certifies
   within-lane type-homogeneity. Verdict-sharing across identical tactic
   text (the verifier's dedup) is sound: same tactic + same goal state =
   same Lean outcome regardless of what GPU generated the text.
3. The verification pass should still assert per-lane cell UNIQUENESS
   ((theorem, k, rollout)) as a cheap invariant; qwen3.5-27b's exact
   713+231=944 arithmetic predicts zero duplicates.
4. Induction analysis MUST read through the store's newest-run_ts-wins
   resolution (harness sync_down does this) -- that alone makes the three
   re-run lanes single-config. The freshness cutoffs above are cross-checks,
   not the mechanism.
   **[Corrected 2026-08-21: VOID. The 2026-08-16 user ruling is
   EARLIEST-logged-run wins on both legs; the three re-run lanes are
   era-split in the analyzed data (14/16, 9/14/7, 12/18). See the header
   note.]**
5. Between-rung hardware differences are a DESIGN PROPERTY, not
   contamination: a family's rungs necessarily span GPU tiers (a 397B rung
   cannot run on one L40S), so box type is nested within rung size.
   Serving-stack numerics differences across GPU types are second-order
   relative to the measured effect sizes, and every lane runs the same
   vLLM version-class and request parameters -- but the analysis write-up
   must state this nesting explicitly rather than imply hardware was
   controlled between rungs. WITHIN-lane homogeneity (this document) is the
   property the study actually guarantees.
6. gemma-4-12b and ministral-3-14b deduction legs (to run after their
   induction re-runs drain) get single-lane, single-box runs whose
   server_config.yaml sidecars (040d2e83) record the config; if a resume
   lands on different hardware the sidecar appends a second snapshot and
   the verify pass must check it before pooling.

## Addendum 2026-08-14 (afternoon): sharded deduction lanes + VOID verify pass

7. Point 6 is superseded on lane shape: both remaining deduction legs were
   SHARDED by theorem stride (`theorems.shard = "i/n"`, commit db566cf8 --
   disjoint slices of the identical seeded 300-theorem sample; each
   theorem's 4 rungs + sanity row stay on one box, so paired rung
   contrasts remain within-box).
   - ministral-3-14b: 3 fresh shards, 3x g7.24xlarge us-west-2d (same
     type/tp=4/nightly image as its induction re-run fleet -> whole lane
     type-homogeneous).
   - gemma-4-12b: resharded MID-RUN at cell 502 (commit 559e45ed): the
     unsharded driver (1x g7.12xlarge us-west-2b) was killed and its rows
     pre-split into 4 shard dirs; shard 0 resumed ON THE ORIGINAL BOX,
     shards 1-3 on fresh g7.12xlarge us-west-2. Whole lane =
     4x g7.12xlarge us-west-2, type-homogeneous.
   Each shard appends its own server_config.yaml snapshot; the merged
   sidecar (scripts/merge_lean_shards.py) therefore lists 3 (ministral)
   and 4 (gemma) instance_ids of ONE instance type each. Read multi-entry
   sidecars on these two lanes as designed sharding, NOT as resumed-run
   hardware drift.

8. THE 2026-08-11..13 LEAN VERIFICATION PASS WAS VOID and its outputs are
   superseded. Every lane's verified_rows.jsonl contained zero successes;
   sanity replays (ground-truth proofs that must pass on a healthy
   verifier) were 100% exceptions (`DojoInitError: Unexpected EOF`,
   missing `*.ast.json`) -- the verify host's LeanDojo environment was
   broken (dying Dojo subprocess / incomplete traced-repo cache), so no
   candidate was ever actually tested against Lean. Per user directive
   2026-08-14: all 16 objects were archived in place as
   `verified_rows_BROKEN-dojoinit_archived-2026-08-14.jsonl` and the
   canonical `verified_rows.jsonl` keys DELETED (16/16 size-verified
   copies; bucket versioning additionally retains the originals). The
   re-run pass must (a) first pass a sanity-group smoke (~100% sanity
   success) on a proven LeanDojo environment before touching any lane,
   and (b) write fresh canonical verified_rows.jsonl objects. Analysis
   must treat any BROKEN-suffixed object as non-data.

9. VERIFY-VOID (point 8) ROOT CAUSE, ESTABLISHED 2026-08-14 -- and the
   re-run is clean. Point 8 named two candidate causes; both were
   incomplete. With the Lean toolchain on PATH AND a complete traced
   cache (5,192 `*.ast.json`, byte-matching the known-good host), the
   verify box STILL returned 10/10 sanity `exception`. Isolating the
   layers -- (a) raw `Dojo.__enter__` -> child exits status 1 with an
   EMPTY output buffer; (b) `pexpect.spawn("lake env lean ...")` by hand
   -> exit 0, so pexpect/PATH/lake are sound; (c) reproducing LeanDojo's
   own `_modify_file` and running the generated file under `subprocess`
   to capture stdout -- surfaced the real error: `unknown package
   'Aesop'` on line 1, with every downstream `expected token` being
   Mathlib NOTATION (e.g. `<char>`) failing only because imports had
   already died. Counting build artifacts: the box had 0 `.olean` files
   for each of aesop/std/Qq/proofwidgets where the known-good host had
   88/152/11/30; Mathlib's OWN oleans matched exactly (4,080 both).
   LeanDojo's remote-cache tarball ships Mathlib's build but NOT its
   dependencies' builds, so a host provisioned purely from that cache can
   never compile a theorem file. Fix: a bounded `lake build Std Aesop Qq
   ProofWidgets ImportGraph Cli` (277 modules, ~4 min, does not touch
   Mathlib). After the fix the smoke gate passed -- sanity 10/10
   `success`, cells returning real verdicts (lean_error / incomplete /
   success) -- and the full 21-lane pass was launched on that environment.
   CONSEQUENCE FOR ANALYSIS: an `*.ast.json` count is NOT evidence that a
   verification host is healthy; only sanity-replay verdicts are. The
   superseded 08-11..13 verdicts were an environment artifact end to end
   and carry no signal about any model.

10. DEDUCTION CoT IS NOT UNIFORM WITHIN THE MINISTRAL LADDER -- treat the
    middle rung's rung-effect with caution. Measured over each lane's 944
    canonical cells (share of cells carrying non-empty reasoning content,
    and mean completion tokens):
      ministral-3-3b   373/944 = 39.5%   mean  8,762 tok
      ministral-3-8b    19/944 =  2.0%   mean    508 tok (median 29)
      ministral-3-14b  451/944 = 47.8%   mean  4,707 tok (median 1,423)
      gemma-4-12b (contrast) 672/944 = 71.2%   mean 14,074 tok
    So the earlier read of this as a FAMILY-wide anomaly was wrong: the
    outer rungs both think on roughly 40-48% of Lean prompts, while the
    8B rung is effectively non-thinking (2%). Because CoT mode is not
    constant across the ladder, the ministral within-family rung contrast
    on deduction confounds parameter count with thinking behaviour at the
    middle rung specifically. This was NOT "fixed" mid-study (forcing
    thinking on one rung would confound the contrast in the opposite
    direction and break comparability with the already-collected rungs);
    it is recorded here so the write-up reports the ministral deduction
    ladder with this caveat attached. The wiring was identical across
    rungs (the family's deploy-spec `system_prompt` recipe), so this is a
    model-behaviour difference, not a serving-config difference.

## 11. Hardware deviations in the 2026-08-14 repair runs (user-accepted, pinned going forward)

The repair runs that regenerate infrastructure-lost cells did not all land on the
instance size their lane originally used. Recorded here because the analysis must
know, and because `server_config` stamps `instance_type`/`gpu` onto every row, so
the two are cross-checkable.

**Deduction — `nemotron-3-nano-4b` and `ministral-3-3b`: `g6e.4xlarge` → `g6e.2xlarge`.**
`g6e.4xlarge` capacity was exhausted in all three regions, so the type list was
widened. Both sizes carry exactly ONE L40S 48GB and run tp=1 under the same image
and vLLM args, so **GPU and sharding are unchanged**; the sizes differ only in host
vCPU/RAM, which affects throughput rather than sampling. Disclosed and accepted by
the user on the explicit condition that sharding and GPU stay the same.

**Induction — seed 19 (shard 8 of 11): `us-east-2` → `us-west-2d`.** Identical
instance type (`g7.24xlarge`, 4× RTX PRO 4500, tp=4) and image; region/AZ only.
The other six reshard seeds ran in us-east-2c.

**Prevention (not just documentation).** `EC2_REQUIRE_GPU="<gpu>:<count>"` now pins
the SILICON rather than the instance size: `serve_model` raises before the container
swap when the landed box does not match, so a mismatched box never generates a row.
The pin permits the accepted size substitution (`L40S:1` covers g6e.2/4/8/16xlarge)
and refuses the contaminating one (a 4-GPU `g6e.12xlarge` would silently change
derived tp mid-lane). An instance type missing from the module's GPU tables is
reported rather than treated as a match. Lanes are pinned in
`scripts/relaunch_damaged_deduction.sh` (L40S:1 / L40S:4 / H200:8) and the induction
reshard in `scripts/resume_all_runs.sh` (RTX PRO 4500:4).

---

## Refuted dispositions (added 2026-08-15)

### The `g6e.4xlarge` → `g6e.2xlarge` substitution IS a confound. Measured.

Section 11 above, and the "Cleared" entry for mixed 1/4-GPU boxes on tp=1 lanes,
both argued that because the two sizes carry the same single L40S 48GB and run the
same tp=1 under the same image, the substitution could change throughput but not
sampling. **That argument is wrong, and it was wrong for a reason worth keeping:
"same accelerator, same tp" does not imply "same output."** Host vCPU/RAM change
how vLLM batches and schedules, which changes floating-point reduction order.

The user ordered an empirical check rather than accepting the argument. The design
of `scripts/hardware_equivalence_probe.py` is what makes the result interpretable:
it first measures a SAME-BOX baseline (two back-to-back passes on one box), because
vLLM is not guaranteed bitwise-reproducible even on one machine, and a naive
cross-size comparison would blame hardware for vLLM's own jitter. Real deduction
prompts from the lane's own S3 run dir, the study's own temperature/seed/max_tokens.

| model | same-box baseline | 4xlarge vs 2xlarge | verdict |
|---|---|---|---|
| `nemotron-3-nano-4b` | **8/8 identical** | **0/8 identical** | HARDWARE IS A VARIABLE |
| `ministral-3-3b` | 0/8 identical | 0/8 identical | neutral within noise |

`nemotron-3-nano-4b` is bitwise-reproducible at a fixed seed on one box, so its 0/8
across sizes cannot be jitter — outputs diverged from the FIRST token, with an
identical `1x L40S 48GB` and `tp=1` served on both sides (confirmed in the probe
logs). `ministral-3-3b` is not reproducible even on one box, so for that lane the
substitution is real but undetectable, and no rerun could verify a fix.

Reports: `notebooks/deduction/results/hwprobe_archive/<model>_4xl-vs-2xl.json`.

**Consequences.**
1. `scripts/relaunch_damaged_deduction.sh` no longer widens the type list for the
   tp=1 lanes; both are pinned to `g6e.4xlarge` alone. Wait for the spec type.
2. `EC2_REQUIRE_GPU`, which pins silicon and therefore PERMITS this substitution,
   is necessary but NOT sufficient. It still prevents the worse failure (a 4-GPU
   box silently changing derived tp mid-lane).
3. Affected data is recorded in the study's rerun record rather than here.

**Generalisable lesson.** Both this and the original silent data fault were cleared
by an argument about a mechanism instead of a measurement of the outcome. When a
substitution is defended on the grounds that it "cannot affect results," the cheap
move is to run the thing twice and diff it -- with a same-box baseline, so the
comparison has a noise floor to be judged against.

### Correction to the above (same day): size was never the variable — the PROCESS is

The retraction above concluded that the `g6e.4xlarge` → `g6e.2xlarge` substitution changes
generations. A third comparison, run afterwards, shows that conclusion was too specific:

| comparison (`nemotron-3-nano-4b`, same prompts/seed) | byte-identical |
|---|---|
| same box, same process, back to back | **8/8** |
| `g6e.4xlarge` vs `g6e.2xlarge` (size **and** box differ) | **0/8** |
| `g6e.4xlarge` vs `g6e.4xlarge` (**only** the box differs) | **0/8** |

The 2xlarge in the middle row was also a different machine running a different vLLM
process. With the size held fixed, agreement is still 0/8 (common prefixes 0–149 chars).
**Instance size was never shown to matter. A different serving process is what matters.**

The original clearance ("same L40S silicon, so not a confound") is still wrong — but so
was my first correction of it. The accurate statement:

> vLLM output here is reproducible **within one server process** and not across
> processes, at identical instance type, GPU, tp and image build.

Consequence for this audit's framing: "confound" cannot usefully mean "some of a lane's
cells came from a different box," because that is true of nearly every lane in the study
(`gemma-4-12b` ×21 boxes [corrected 2026-08-21: ×39; ≥ 36 at write time],
`ministral-3-14b` ×48 [corrected 2026-08-21: ×64; ≥ 54 at write time],
`glm-4.7-flash` ×4, `exaone-4.5-33b` ×3,
`qwen3.5-27b` ×3, and every sweep resumed after a spot reclaim). It is a per-process noise
term that does not correlate with the model axis — every lane has its own hardware by
design — and it should be reported as a known noise term with its measured size, not
chased with re-runs. Full reasoning and the per-lane inventory:
`notebooks/CONTAMINATION_INVENTORY_2026-08-15.md`.

Recommendation carried forward: pin `EC2_VLLM_IMAGE` to a DIGEST rather than the
`nightly` tag, so that at least the image is not a second uncontrolled variable.
