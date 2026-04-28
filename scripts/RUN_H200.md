# H200 SmolBench deductive run — operator guide

Two boxes (us-east-2b), one model each:
- **box-1** `18.221.11.252` → `AI-MO/Kimina-Prover-72B`
- **box-2** `3.132.214.192` → `Goedel-LM/Goedel-Prover-V2-32B`

S3: `s3://smolbench-deductive/` (us-east-2). All artifacts (cache, results, logs, metrics, spot events) go there.

SSH key: `~/.ssh/gpu-training.pem` (user `ubuntu`). IPs change on stop/start.

## Layout on each box

```
/opt/dlami/nvme/sb/
├── smolbench/         # repo (rsynced from local; deduction-rewrite branch)
├── external/
│   ├── kimina-lean-server/   (with no-mathlib-collapse patch applied)
│   └── repl/                 (lake-built REPL binary)
├── data/
│   ├── leandojo_benchmark_4/
│   ├── lean_dojo_cache/.../mathlib4/   (read-only)
│   └── replay_pool.jsonl
├── .cache/huggingface/   (model weights)
├── logs/
│   ├── bootstrap.log
│   ├── vllm.log + vllm.pid
│   ├── kimina.pid
│   ├── s3_sync.log + s3_sync.pid
│   └── spot_handler.log + spot_handler.pid
└── runs/<RUN_NAME>/
    ├── cells.jsonl              # per-cell results (the primary output)
    ├── cells.jsonl.meta.jsonl   # one record per process invocation (incl. restarts)
    ├── metrics.jsonl            # GPU/system snapshots from s3_sync
    └── spot_events.jsonl        # any spot-interruption notices
```

S3 mirror at `s3://smolbench-deductive/runs/<hostname>/<RUN_NAME>/`.

## Launch the run

`launch_run.sh` brings up everything needed: kimina + vLLM (if not up), s3_sync daemon, spot watchdog, then execs the runner.

### Box-1 (Kimina-72B)
```bash
ssh -i ~/.ssh/gpu-training.pem ubuntu@18.221.11.252
ROOT=/opt/dlami/nvme/sb \
RUN_NAME=kimina72b_pilot1 MODEL_KIND=kimina72b \
KS=0,1,2,3 BS=0,1,2,3,4 K_SEEDS=4 \
TARGET_LIMIT=100 WORKERS=4 MAX_TOKENS=4096 \
nohup bash /opt/dlami/nvme/sb/smolbench/scripts/launch_run.sh \
  > /opt/dlami/nvme/sb/logs/run.log 2>&1 &
disown
```

### Box-2 (Goedel-32B)
```bash
ssh -i ~/.ssh/gpu-training.pem ubuntu@3.132.214.192
ROOT=/opt/dlami/nvme/sb \
RUN_NAME=goedel32b_pilot1 MODEL_KIND=goedel32b \
KS=0,1,2,3 BS=0,1,2,3,4 K_SEEDS=4 \
TARGET_LIMIT=100 WORKERS=4 MAX_TOKENS=4096 \
nohup bash /opt/dlami/nvme/sb/smolbench/scripts/launch_run.sh \
  > /opt/dlami/nvme/sb/logs/run.log 2>&1 &
disown
```

Tune `TARGET_LIMIT`, `KS`, `BS`, `K_SEEDS` to your grid. `WORKERS` is concurrent
cells in flight — 4 is conservative; H200 can handle more.

`MAX_PROMPT_CHARS=100000` (default) skips cells whose prompt is too big to fit
the 32K-token model context. Bump or lower to taste.

## Monitor

```bash
# pass rate ticker
ssh ... 'tail -f /opt/dlami/nvme/sb/logs/run.log'

# raw cell stream
ssh ... 'tail -f /opt/dlami/nvme/sb/runs/<RUN_NAME>/cells.jsonl | jq -c "{id:.target_id,K,B,seed,pass:.verify_pass,err:.error_class}"'

# GPU
ssh ... 'nvidia-smi'

# s3 mirror status (run from local)
aws s3 ls --human-readable s3://smolbench-deductive/runs/
```

## Resume after spot interruption

`launch_run.sh` is idempotent. If the box was reclaimed and is back up:
```bash
ssh ... 'bash /opt/dlami/nvme/sb/smolbench/scripts/launch_run.sh ...'
```
Same command — runner will read existing `cells.jsonl`, skip completed
cells, and pick up the rest. The `meta.jsonl` will gain one new line
(useful: you can count restarts).

If the box is *replaced* (different instance ID):
1. Re-rsync source if you've changed code.
2. Re-run `bootstrap_h200.sh` (idempotent, but pulls cache+model fresh).
3. **Pull** the existing run JSONL down from S3 first so resume sees it:
   ```bash
   aws s3 cp s3://smolbench-deductive/runs/<old-host>/<RUN_NAME>/cells.jsonl \
     /opt/dlami/nvme/sb/runs/<RUN_NAME>/cells.jsonl
   ```
4. Then `launch_run.sh` as above.

## Stop

```bash
ssh ... 'bash /opt/dlami/nvme/sb/smolbench/scripts/stop_run.sh'
# add STOP_SERVERS=1 to also stop kimina + vLLM
```

## Smoke test (single cell, sanity check)

```bash
RUN_NAME=smoke MODEL_KIND=kimina72b \
TARGET_LIMIT=1 KS=0 BS=0 K_SEEDS=1 WORKERS=1 \
bash /opt/dlami/nvme/sb/smolbench/scripts/launch_run.sh
```

Should produce one JSONL row in `runs/smoke/cells.jsonl` and one row in S3
within 60s of completion.
