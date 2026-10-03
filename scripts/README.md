# scripts/

`scripts/arch/` documents roster architecture in its [README](arch/README.md).

`scripts/` uses implicit namespace packages; fleet scripts load siblings by
path to avoid collisions with test-loader module names.

## scripts/fleet/ -- launching and babysitting the family-ladder EC2 fleet

| File | What it's for |
| --- | --- |
| `run_fleet.py` | Fleet entry point: arguments, lane selection, dry-run plan. |
| `lane_env.py` | Roster, per-lane environment/argv, and required `EC2_*` import order. |
| `supervisor.py` | Live supervision, gates, restarts, shutdown, and resumable state. |
| `policy.py` | Shared reclaim/crash classification, relaunch caps, and backoff. |
| `fleet_status.py` | Read-only live-instance listing; library and standalone CLI. |
| `fleet_teardown.py` | Lists or terminates instances left by `run_fleet.py`. |
| `run_shards.py` | Supervises direct induction shard fleets. |
| `shards.py` | Supervised shard process, logs, state, and restart counters. |

Keep these files together: sibling loading resolves via `Path(__file__).parent`.

## scripts/deduction/horn/ -- Horn sweep and calibration drivers

The Horn sweep and calibration drivers live in [`scripts/deduction/horn/`](deduction/horn/); see the [Horn benchmark documentation](../smolbench/deduction/horn/README.md).

## scripts/results/ -- results-store admin, grading, and audit tooling

| File | What it's for |
| --- | --- |
| `provision_results_bucket.py` | ADMIN-credentialed, one-time idempotent runbook that provisions the S3-backed results bucket. |
| `audit_run_completeness.py` | Finds data faults that row/key counts miss. |
| `snapshot_analysis_data.py` | Publishes current data with its repair audit trail. |

## scripts/smoke/ -- live AWS smoke tests

These scripts spend real money and touch live AWS accounts. Never run without
explicit user opt-in: they provision EC2 or invoke Bedrock and are billed.

| File | What it's for |
| --- | --- |
| `bedrock_smoke.py` | Live smoke test of the Bedrock-mantle provider: `list_models` plus one seeded `evaluate` call. |
| `ec2_lifecycle_smoke.py` | Staged live smoke test of the smolbench EC2 provider's provision/serve/shutdown lifecycle. Run as `ec2_lifecycle_smoke.py <step>`. |

### Live smoke runbook

With fresh creds for profile `<your-profile>`:

```bash
export AWS_PROFILE='<your-profile>' AWS_REGION=us-east-1
export EC2_EXPERIMENT_TAG=smoke-test \
       EC2_STATE_FILE=/tmp/cleanup_smoke_state.json \
       EC2_INSTANCE_TYPES=g6.2xlarge,g5.2xlarge \
       EC2_REGIONS=us-east-1 EC2_ROOT_VOLUME_GB=100 EC2_IDLE_TIMEOUT_MIN=25

# 1. EC2 lifecycle (~15 min, ~$0.30): each step must print "OK".
.venv/bin/python scripts/smoke/ec2_lifecycle_smoke.py provision   # fresh-launch branch, port threading, _wait_agent
.venv/bin/python scripts/smoke/bedrock_smoke.py                   # (while it boots) aws.py: list_models, ctx default, seeded evaluate
.venv/bin/python scripts/smoke/ec2_lifecycle_smoke.py serve_eval  # vLLM port end-to-end; 4-question seeded evaluate
.venv/bin/python scripts/smoke/ec2_lifecycle_smoke.py reattach    # state-file branch (must return in seconds)
.venv/bin/python scripts/smoke/ec2_lifecycle_smoke.py recover     # deletes state file; tag-recovery branch must find the same instance
.venv/bin/python scripts/smoke/ec2_lifecycle_smoke.py shutdown

# 2. Confirm nothing is left running/billing:
aws ec2 describe-instances --region us-east-1 \
  --filters "Name=tag:smolbench:experiment,Values=smoke-test" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output table
```

The 25-minute idle watchdog and max-lifetime backstop terminate a failed run.
For dry spot capacity, widen `EC2_INSTANCE_TYPES` and `EC2_REGIONS`.
