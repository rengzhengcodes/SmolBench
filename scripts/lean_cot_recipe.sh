#!/bin/bash
# CoT-recipe LoRA training orchestrator, run ON THE lean-train BOX.
#
# Implements the 2026-07-12 deep-research recipe (notebooks/lean/research/
# 2026-07-12_sft_recipe_deep_research.md): CoT-augmented SFT targets at a
# higher LoRA rank than the earlier real-only/synthetic-pretrain runs
# (lean_qwen_4way.sh), which produced no significant eval gain.
#
# Two modes, selected by the FULL env var (default 0 = smoke):
#   SMOKE (default): Qwen-only, TWO arms -- `bare8k-r128` (bare tactic-tail
#     targets, the control; trains on cot_stepk1_bare_8k.jsonl, the
#     annotator's PAIRED bare-control sibling of cot_stepk1_think_8k.jsonl --
#     see scripts/annotate_lean_cot.py's module docstring, Pipeline step 5)
#     and `cot8k-r128` (CoT-augmented targets; cot_stepk1_think_8k.jsonl) --
#     same rank/schedule AND the two arms train on the EXACT SAME theorem
#     set by construction (the sibling is byte-identical minus the CoT
#     wrapping), so a win is attributable to the CoT format alone, not to
#     the rank bump or a sampling difference between the two files (see the
#     plan's "Attribution control" design decision). This is the de-risking
#     run gating the trio commitment below.
#   FULL=1: the whole trio (Qwen think-style + Llama-405B/Nemotron-Ultra
#     fenced-style), one `cot-full-r128` stage each, on the FULL annotated
#     pool (cap 0 = all rows). *** Only run this after the smoke's
#     pre-registered improvement gate (pass@8, McNemar cot-r128 vs
#     bare-r128 AND base) has come back green -- see the plan's live-gate
#     list. Nothing in this script enforces that; it is a spend decision
#     the operator makes, same as the cb-purchase gate below it. ***
#
# Sizing (COMMON: --grad-accum 16 --batch-size 1 -> effective batch 16;
# --epochs 2):
#   8k rows:  8000/16 = 500 steps/epoch x2 epochs = 1000 steps
#             ~40s/step (trio-class model, QLoRA 4-bit) -> ~11h per arm.
#   56k rows: 56000/16 = 3500 steps/epoch x2 epochs = 7000 steps
#             ~40s/step -> ~78h/model PRE-PRUNE (the plan's WP3 near-dup
#             prune is expected to cut this ~30-40%). This spans the 48h
#             spot horizon -- capacity-block territory; see
#             `lean_train_ec2.py cb-search`/`cb-purchase`/
#             `provision --capacity-reservation`.
#
# Resumable + idempotent, same durability contract as lean_qwen_4way.sh:
# per stage (1) if S3 already has the stage's FINAL adapter -> skip (cheap
# S3 head, no download); (2) else pull partial state from S3 and resume
# from the latest checkpoint (--resume-from-checkpoint auto); (3) else
# start fresh. A background loop syncs the output dir to S3 every 90s, plus
# a final sync, so an interruption loses at most ~90s + the
# since-last-checkpoint steps (--save-steps 100). Uploaded to /opt/train by
# `lean_train_ec2.py setup` (as COT_ORCHESTRATOR, alongside the Qwen
# 4-way's ORCHESTRATOR); launch with
# `nohup bash /opt/train/lean_cot_recipe.sh &` (or `FULL=1 nohup ... &`).
#
# DRYRUN=1: print the exact command each stage WOULD run (fully resolved
# flags/dataset/output-dir) and return immediately -- no aws/python calls,
# no filesystem writes, no self-halt. Lets the stage list/flag wiring be
# checked (offline, off-box) before ever touching a GPU or S3; see
# tests/test_lean_cot_recipe.py.
set -uo pipefail

DRYRUN=${DRYRUN:-0}
FULL=${FULL:-0}

VENV=/opt/train/venv/bin
REG=us-west-2
BUCKET=s3://smolbench-model-cache-414266451290/lean-train-checkpoints
ORCH=/opt/train/out/cot-recipe.orch.log

# Design: real box setup (source the HF token, cd into the working tree,
# pre-create out/ for the orchestrator log) is skipped entirely under
# DRYRUN so this script can be smoke-tested off-box with no /opt/train tree
# and no HF_TOKEN -- DRYRUN never touches the filesystem or reads secrets.
if [ "$DRYRUN" != "1" ]; then
  . /opt/train/hf_env
  cd /opt/train
  mkdir -p /opt/train/out
fi

# CoT-recipe hyperparameters shared by every stage (rank/epochs/schedule,
# per the plan's "Epochs" design decision: 2 epochs, cosine, 0.03 warmup).
# Per-model target-modules/moe/trust-remote-code are appended by run().
COT_COMMON="--lora-r 128 --lora-alpha 256 --epochs 2 --lr-scheduler-type cosine --warmup-ratio 0.03 --batch-size 1 --grad-accum 16 --seed 1776 --save-steps 100"

# Attention-only + moe-unquantized for the Qwen MoE (its fused-Parameter
# experts OOM peft's ParamWrapper at higher rank -- see lean_train_ec2.py's
# TRIO comment); attention+MLP for the dense bases; Nemotron additionally
# needs trust_remote_code for its NAS (DeciLM) modeling code.
QWEN_FLAGS="--target-modules q_proj,k_proj,v_proj,o_proj --moe-unquantized"
DENSE_FLAGS="--target-modules q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj"
NEMOTRON_FLAGS="$DENSE_FLAGS --trust-remote-code"

log() {
  # DRYRUN never writes $ORCH (it may not exist off-box); tee only for real runs.
  if [ "$DRYRUN" == "1" ]; then
    echo "[$(date -u +%H:%M:%S)] $*"
  else
    echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$ORCH"
  fi
}

# run BASE_KEY BASE_MODEL STAGE MODEL_FLAGS DATASET CAP
#   BASE_KEY   TRIO key (S3 lives under $BUCKET/$BASE_KEY/$STAGE/, matching
#              lean_train_ec2.py's per-model checkpoint layout).
#   BASE_MODEL HF repo of the base to LoRA-tune.
#   STAGE      this run's name (== S3 subprefix; the coordination constant
#              other packages key off of, e.g. "bare8k-r128"/"cot8k-r128"/
#              "cot-full-r128").
#   MODEL_FLAGS --target-modules (+ --moe-unquantized / --trust-remote-code).
#   DATASET    uploaded SFT jsonl name under /opt/train/.
#   CAP        --max-examples value (0 = all rows, for FULL mode).
run() {
  local base_key=$1 base_model=$2 stage=$3 model_flags=$4 ds=$5 cap=$6
  local dest="$BUCKET/$base_key/$stage/"
  local out="/opt/train/out/$base_key/$stage"
  local log_file="/opt/train/out/$base_key-$stage.log"
  local ss="/opt/train/out/$base_key-$stage.SYNCSTOP"
  local cmd="$VENV/python scripts/lean_lora_sft.py --base-model $base_model $COT_COMMON $model_flags --dataset /opt/train/$ds --max-examples $cap --output-dir $out"

  if [ "$DRYRUN" == "1" ]; then
    log "DRYRUN $base_key/$stage: $cmd"
    return 0
  fi

  # (1) Completion check: a top-level adapter_model.safetensors in S3 means
  # the stage's final save_model() ran -> done. Cheap S3 head, no download.
  if $VENV/aws s3 ls "$dest"adapter_model.safetensors --region $REG >/dev/null 2>&1; then
    log "SKIP $base_key/$stage (final adapter already in S3)"
    return 0
  fi

  # (2) Pull any partial state (checkpoints) from S3 to resume.
  mkdir -p "$out"
  $VENV/aws s3 sync "$dest" "$out" --only-show-errors --region $REG 2>/dev/null || true
  local resume=""
  if ls -d "$out"/checkpoint-* >/dev/null 2>&1; then
    resume="--resume-from-checkpoint auto"
    log "RESUME $base_key/$stage from $(ls -d "$out"/checkpoint-* | sort -t- -k2 -n | tail -1)"
  fi

  log "START $base_key/$stage ds=$ds cap=$cap ${resume:+(resuming)}"
  rm -f "$ss"
  ( while [ ! -f "$ss" ]; do $VENV/aws s3 sync "$out" "$dest" --only-show-errors --region $REG 2>/dev/null; sleep 90; done ) &
  $cmd $resume > "$log_file" 2>&1
  local rc=$?
  touch "$ss"; $VENV/aws s3 sync "$out" "$dest" --only-show-errors --region $REG
  log "END $base_key/$stage rc=$rc"
  return $rc
}

if [ "$FULL" == "1" ]; then
  log "===== COT RECIPE FULL (trio, cot-full-r128) START ====="
  run qwen3-235b-a22b     Qwen/Qwen3-235B-A22B                    cot-full-r128 "$QWEN_FLAGS"     cot_stepk1_think_full.jsonl  0 \
    || { log "ABORT qwen3-235b-a22b/cot-full-r128"; exit 1; }
  run llama-31-405b       SillyTilly/Meta-Llama-3.1-405B-Instruct cot-full-r128 "$DENSE_FLAGS"    cot_stepk1_fenced_full.jsonl 0 \
    || { log "ABORT llama-31-405b/cot-full-r128"; exit 1; }
  run nemotron-ultra-253b nvidia/Llama-3_1-Nemotron-Ultra-253B-v1 cot-full-r128 "$NEMOTRON_FLAGS" cot_stepk1_fenced_full.jsonl 0 \
    || { log "ABORT nemotron-ultra-253b/cot-full-r128"; exit 1; }
  log "===== COT_RECIPE_FULL_DONE ====="
else
  log "===== COT RECIPE SMOKE (8k, bare vs cot) START ====="
  # bare8k-r128's dataset/cap: cot_stepk1_bare_8k.jsonl is annotate_lean_cot.py's
  # paired bare-control sibling of cot_stepk1_think_8k.jsonl -- already
  # EXACTLY the same 8k theorem set as the cot8k-r128 arm below, so cap 0
  # (train on the whole file, no further subsampling) keeps the pairing exact.
  run qwen3-235b-a22b Qwen/Qwen3-235B-A22B bare8k-r128 "$QWEN_FLAGS" cot_stepk1_bare_8k.jsonl  0 \
    || { log "ABORT qwen3-235b-a22b/bare8k-r128"; exit 1; }
  run qwen3-235b-a22b Qwen/Qwen3-235B-A22B cot8k-r128  "$QWEN_FLAGS" cot_stepk1_think_8k.jsonl  8000 \
    || { log "ABORT qwen3-235b-a22b/cot8k-r128"; exit 1; }
  log "===== COT_RECIPE_SMOKE_DONE ====="
fi

# Self-halt: everything is synced to S3 by now, and an idle p5 burns
# $40+/h until someone notices (lean_qwen_4way.sh's rationale). OS halt
# terminates a one-time spot instance; on a capacity-block box it just ends
# the instance (the prepaid window is unaffected). Skipped under DRYRUN
# (no real box, nothing to halt).
if [ "$DRYRUN" != "1" ]; then
  sudo shutdown -h +5 "cot recipe complete; self-terminating" || true
fi
