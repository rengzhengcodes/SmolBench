#!/bin/bash
# Qwen3-235B-A22B synthetic-pretrain 4-way LoRA, run ON THE lean-train BOX.
#
# Stages (all on the DECONTAMINATED sets, cap 8000): real-only baseline +
# goedel(stage1->stage2) + leannav(stage1->stage2). Spot-interruption RESUMABLE
# and idempotent -- safe to re-launch on a fresh box after an interruption:
#   per stage (1) if S3 already has the stage's FINAL adapter -> skip (cheap
#   S3 head, no download); (2) else pull partial state from S3 and resume from
#   the latest checkpoint (--resume-from-checkpoint auto); (3) else start fresh.
# Durability: a background loop syncs the output dir to S3 every 90s, plus a
# final sync, so an interruption loses at most ~90s + the since-last-checkpoint
# steps (--save-steps 100). Uploaded to /opt/train by `lean_train_ec2.py setup`;
# launch with `nohup bash /opt/train/lean_qwen_4way.sh &`.
#
# Flags mirror lean_train_ec2.py's Qwen TRIO config exactly (attention-only LoRA,
# --moe-unquantized for the bf16 fused-Parameter experts). S3BASE/REG are the
# checkpoint bucket + its region (NOT the box region) -- every aws call passes
# --region so a box in another region still reaches the us-west-2 bucket (avoids
# the 301 that a region-less sync hit before).
set -uo pipefail
. /opt/train/hf_env
cd /opt/train
VENV=/opt/train/venv/bin
REG=us-west-2
S3BASE=s3://smolbench-model-cache-414266451290/lean-train-checkpoints/qwen3-235b-a22b
COMMON="--base-model Qwen/Qwen3-235B-A22B --target-modules q_proj,k_proj,v_proj,o_proj --moe-unquantized --lora-r 16 --lora-alpha 32 --batch-size 1 --grad-accum 16 --seed 1776 --save-steps 100"
ORCH=/opt/train/out/qwen4way.orch.log
mkdir -p /opt/train/out/qwen3-235b-a22b

run() {  # $1=stage $2=dataset $3=cap $4=init_local_dir(or "")
  local stage=$1 ds=$2 cap=$3 init=$4
  local out=/opt/train/out/qwen3-235b-a22b/$stage
  local dest=$S3BASE/$stage/
  local log=/opt/train/out/qwen4way-$stage.log
  local ss=/opt/train/out/qwen4way-$stage.SYNCSTOP

  # (1) Completion check: a top-level adapter_model.safetensors in S3 means the
  # stage's final save_model() ran -> done. Cheap S3 head, no download.
  if $VENV/aws s3 ls "$dest"adapter_model.safetensors --region $REG >/dev/null 2>&1; then
    echo "[$(date -u +%H:%M:%S)] SKIP $stage (final adapter already in S3)" | tee -a "$ORCH"; return 0
  fi

  # (2) Pull any partial state (checkpoints) from S3 to resume.
  mkdir -p "$out"
  $VENV/aws s3 sync "$dest" "$out" --only-show-errors --region $REG 2>/dev/null || true
  local resume=""
  if ls -d "$out"/checkpoint-* >/dev/null 2>&1; then
    resume="--resume-from-checkpoint auto"
    echo "[$(date -u +%H:%M:%S)] RESUME $stage from $(ls -d "$out"/checkpoint-* | sort -t- -k2 -n | tail -1)" | tee -a "$ORCH"
  fi

  # Stage-2 init: pull stage-1 from S3 if the local dir is gone (fresh box).
  if [ -n "$init" ] && [ ! -f "$init/adapter_config.json" ]; then
    echo "[$(date -u +%H:%M:%S)] pull init adapter for $stage from S3" | tee -a "$ORCH"
    $VENV/aws s3 sync "$S3BASE/$(basename "$init")/" "$init" --only-show-errors --region $REG
  fi
  local initflag=""; [ -n "$init" ] && initflag="--init-adapter $init"

  echo "[$(date -u +%H:%M:%S)] START $stage ds=$ds cap=$cap ${init:+init=$init} ${resume:+(resuming)}" | tee -a "$ORCH"
  rm -f "$ss"
  ( while [ ! -f "$ss" ]; do $VENV/aws s3 sync "$out" "$dest" --only-show-errors --region $REG 2>/dev/null; sleep 90; done ) &
  $VENV/python scripts/lean_lora_sft.py $COMMON --dataset /opt/train/$ds --max-examples $cap --output-dir "$out" $initflag $resume > "$log" 2>&1
  local rc=$?
  touch "$ss"; $VENV/aws s3 sync "$out" "$dest" --only-show-errors --region $REG
  echo "[$(date -u +%H:%M:%S)] END $stage rc=$rc" | tee -a "$ORCH"
  return $rc
}

echo "[$(date -u +%H:%M:%S)] ===== QWEN 4-WAY (8k, resumable) START =====" | tee -a "$ORCH"
run real-only      novel_premises_train_stepk1_decontam.jsonl 8000 ""                                            || { echo "ABORT real-only"     | tee -a "$ORCH"; exit 1; }
run goedel-stage1  synth_goedel_v2_24k.jsonl                  8000 ""                                            || { echo "ABORT goedel-stage1"  | tee -a "$ORCH"; exit 1; }
run goedel-stage2  novel_premises_train_stepk1_decontam.jsonl 8000 /opt/train/out/qwen3-235b-a22b/goedel-stage1  || { echo "ABORT goedel-stage2"  | tee -a "$ORCH"; exit 1; }
run leannav-stage1 synth_leannavigator_24k.jsonl             8000 ""                                            || { echo "ABORT leannav-stage1" | tee -a "$ORCH"; exit 1; }
run leannav-stage2 novel_premises_train_stepk1_decontam.jsonl 8000 /opt/train/out/qwen3-235b-a22b/leannav-stage1 || { echo "ABORT leannav-stage2" | tee -a "$ORCH"; exit 1; }
echo "[$(date -u +%H:%M:%S)] ===== QWEN_4WAY_DONE =====" | tee -a "$ORCH"
# Self-halt: everything is synced to S3 by now, and an idle p5 burns ~$40+/h
# until someone notices (the 07-10 run idled from DONE until a lucky spot
# reclaim). OS halt terminates a one-time spot instance; on a capacity-block
# box it just ends the instance (the prepaid window is unaffected).
sudo shutdown -h +5 "qwen 4-way complete; self-terminating" || true
