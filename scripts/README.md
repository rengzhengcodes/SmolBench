# scripts/

Operational scripts, grouped by job. `scripts/arch/` is a separate,
already-coherent subpackage with its own README (`scripts/arch/README.md`)
covering the model architecture atlas pipeline; it is not described here.

There is no `__init__.py` under `scripts/` -- the directories are implicit
namespace packages, so `from scripts.<group>.<module> import ...` works
from the repo root (pytest sets `pythonpath`). Load by file path instead
only when a basename is ambiguous or a module has import-time side
effects (`run_fleet.py`/`fleet_teardown.py` load `fleet_status.py` as a
sibling for that reason).

## scripts/fleet/ -- launching and babysitting the family-ladder EC2 fleet

| File | What it's for |
| --- | --- |
| `run_fleet.py` | The 21-lane EC2 fleet supervisor for the family-ladder scaling study: launches one subprocess per study model/lane, each provisioning its own EC2 spot instance, and supervises restarts (reclaim vs. crash-loop classification). |
| `fleet_status.py` | Read-only listing of the fleet's live EC2 instances. Loaded as a library by `run_fleet.py` and `fleet_teardown.py`, and also runnable standalone. |
| `fleet_teardown.py` | Lists, and optionally terminates, the fleet's live instances -- the safety net for lanes a `run_fleet.py` run didn't shut down itself. |
| `run_shards.py` | Babysits direct (supervisor-less) `notebooks/induction/run_study.py` shard fleets: adopts already-running shard processes, relaunches dead ones, and tears down completed shards' boxes. |

`run_fleet.py` and `fleet_teardown.py` load `fleet_status.py` as a sibling
module via `Path(__file__).parent`, so all three files must stay in this
directory together.

## scripts/deduction/ -- the Lean deduction study's sharding and verification passes

`lean_verify_rows.py` is the only script in this repo that must run under
`.venv-lean` (it needs `lean_dojo`, which pins `python<3.13`; its
`--dry-run` mode also works under `.venv`). Everything else here, and
everywhere else under `scripts/`, runs under `.venv`.

| File | What it's for |
| --- | --- |
| `split_lean_run_into_shards.py` | Splits an unsharded deduction run's outputs into pre-seeded shard run directories, so a lane can be resharded mid-flight. |
| `merge_lean_shards.py` | Merges a sharded deduction lane's run directories back into the canonical run the verify pass and analysis read. |
| `lean_verify_rows.py` | The deferred Lean verification pass: replays recorded generation rows against a real Lean/Dojo session and writes real verdicts. |

## scripts/results/ -- results-store admin, grading, and audit tooling

| File | What it's for |
| --- | --- |
| `provision_results_bucket.py` | ADMIN-credentialed, one-time (idempotent) runbook that provisions the S3-backed replicate results bucket `smolbench.evals.results_store` reads and writes. |
| `regrade.py` | Re-grades already-collected replicates with the current compliance-aware parser, in place. |
| `audit_run_completeness.py` | Audits content-level run completeness against S3 (or a local run directory) to catch silent data faults that row/key counts alone would miss. |
| `snapshot_analysis_data.py` | Publishes an analysis-ready snapshot of the family-ladder study to S3, tagging superseded/stale/broken prior snapshots. |
| `evidence_manifest.py` | Builds and verifies `EVIDENCE.json`, the manifest that pins the artifacts (by sha256) a results writeup cites. |

## scripts/smoke/ -- live AWS smoke tests

**These scripts spend real money and touch live AWS accounts.** Never run
them without explicit user opt-in; they provision real EC2 instances /
invoke real Bedrock models and are billed accordingly.

| File | What it's for |
| --- | --- |
| `bedrock_smoke.py` | Live smoke test of the Bedrock-mantle provider: `list_models` plus one seeded `evaluate` call. |
| `ec2_lifecycle_smoke.py` | Staged live smoke test of the smolbench EC2 provider's provision/serve/shutdown lifecycle. Run as `ec2_lifecycle_smoke.py <step>`. |

### Live smoke runbook

With fresh creds for profile `rengz`:

```bash
export AWS_PROFILE=rengz AWS_REGION=us-east-1
export EC2_EXPERIMENT_TAG=cleanup-smoke-0702 \
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
  --filters "Name=tag:smolbench:experiment,Values=cleanup-smoke-0702" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output table
```

Even if a smoke step dies mid-run, the instance's own idle watchdog (25
min) and max-lifetime backstop terminate it. If spot capacity is dry,
widen the hunt (e.g. `EC2_INSTANCE_TYPES=g6.2xlarge,g5.2xlarge,g6e.2xlarge`
and `EC2_REGIONS=us-east-1,us-east-2,us-west-2`).
