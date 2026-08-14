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
- Mixed 1/4-GPU boxes on tp=1 lanes (ministral-3-3b, nemotron-nano-4b):
  static tp=1 throughout, same L40S silicon; idle GPUs are waste, not
  confounds.

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

## Per-lane serving configs (analyzed data, after newest-wins)

| lane | induction | deduction |
|---|---|---|
| qwen3.5-27b | g6e.12xl (4x L40S, tp=4), boxes in us-east-2c + us-east-1d | same type; TWO completed sweeps, see segmentation note |
| qwen3.5-122b-a10b | p5.48xl (8x H100, tp=8) x2 boxes us-east-2c | same type |
| qwen3.5-397b-a17b | p5e.48xl (8x H200, tp=8), ONE box us-west-2c | same box |
| nemotron-3-nano-4b | g6e.4xl/g6e.8xl (both 1x L40S, static tp=1) | same 1-GPU L40S types |
| nemotron-3-nano-30b-a3b | g6e.12xl (tp=4), ONE box us-west-2b | same box |
| nemotron-3-super-120b-a12b | p5e.48xl (8x H200, tp=8), ONE box us-west-2 | same box |
| gemma-4-e2b | g6e.4xl (1x L40S, tp=1) x3 boxes us-east-2 | same type |
| gemma-4-12b | RE-RUN: g7.12xl (2x RTX PRO 4500, tp=2) x10, us-west-2b | TO RUN (single lane, sidecar active) |
| gemma-4-31b | g6e.12xl (tp=4), ONE box us-east-2c | same box |
| glm-4.7-flash | g6e.12xl (tp=4) x4 boxes us-east-2 + us-east-1d | same type, resumed sweep |
| glm-4.5-air | p5.48xl (8x H100, tp=8) x2 us-east-2c | same type, resumed sweep |
| glm-4.7 | p5en.48xl (8x H200, tp=8) x2 us-east-2a | same type |
| ministral-3-3b | g6e.4xl + g6e.12xl MIXED, static tp=1 (cleared above: same L40S silicon, idle GPUs) | final box g6e.12xl us-west-2c, tp=1 |
| ministral-3-8b | g6e.12xl (tp=4), ONE box us-west-2b | same box |
| ministral-3-14b | RE-RUN: g7.24xl (4x RTX PRO 4500, tp=4) x8, us-east-2c | TO RUN (single lane, sidecar active) |
| exaone-4.0-32b | g6e.12xl (tp=4), ONE box us-east-2c | same box |
| exaone-4.5-33b | g6e.12xl (tp=4) x3 boxes us-east-2 | same type, resumed sweep |
| k-exaone-236b-a23b | p5.48xl (8x H100, tp=8) x2 us-east-2 | same type |
| deepseek-v4-flash | p6-b200.48xl (8x B200, tp=8) after re-run | same box class, single segment |
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
