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
