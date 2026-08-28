# scripts/

Operational scripts, grouped by job. `scripts/arch/` is a separate,
already-coherent subpackage with its own README (`scripts/arch/README.md`)
covering the model architecture atlas pipeline; it is not described here.

None of these directories are importable packages via an `__init__.py` --
they're implicit namespace packages, and every cross-script or test import
loads a sibling module either by relative path (`Path(__file__).parent`,
for scripts within the same subdirectory) or via `importlib.util` loading
by file path (for tests reaching into a script as a module).

## scripts/fleet/ -- launching and babysitting the family-ladder EC2 fleet

| File | What it's for | Venv |
| --- | --- | --- |
| `run_fleet.py` | The 21-lane EC2 fleet supervisor for the family-ladder scaling study: launches one subprocess per study model/lane, each provisioning its own EC2 spot instance, and supervises restarts (reclaim vs. crash-loop classification). | `.venv` |
| `fleet_status.py` | Read-only listing of the fleet's live EC2 instances. Loaded as a library by `run_fleet.py` and `fleet_teardown.py`, and also runnable standalone. | `.venv` |
| `fleet_teardown.py` | Lists, and optionally terminates, the fleet's live instances -- the safety net for lanes a `run_fleet.py` run didn't shut down itself. | `.venv` |
| `run_shards.py` | Babysits direct (supervisor-less) `notebooks/induction/run_study.py` shard fleets: adopts already-running shard processes, relaunches dead ones, and tears down completed shards' boxes. | `.venv` |

`run_fleet.py` and `fleet_teardown.py` load `fleet_status.py` as a sibling
module via `Path(__file__).parent`, so all three files must stay in this
directory together.

## scripts/deduction/ -- the Lean deduction study's sharding and verification passes

| File | What it's for | Venv |
| --- | --- | --- |
| `split_lean_run_into_shards.py` | Splits an unsharded deduction run's outputs into pre-seeded shard run directories, so a lane can be resharded mid-flight. | `.venv` |
| `merge_lean_shards.py` | Merges a sharded deduction lane's run directories back into the canonical run the verify pass and analysis read. | `.venv` |
| `lean_verify_rows.py` | The deferred Lean verification pass: replays recorded generation rows against a real Lean/Dojo session and writes real verdicts. Needs `lean_dojo`, which pins `python<3.13`. | `.venv-lean` (`--dry-run` also works under `.venv`) |

## scripts/results/ -- results-store admin, grading, and audit tooling

| File | What it's for | Venv |
| --- | --- | --- |
| `provision_results_bucket.py` | ADMIN-credentialed, one-time (idempotent) runbook that provisions the S3-backed replicate results bucket `smolbench.evals.results_store` reads and writes. | `.venv` |
| `regrade.py` | Re-grades already-collected replicates with the current compliance-aware parser, in place. | `.venv` |
| `audit_run_completeness.py` | Audits content-level run completeness against S3 (or a local run directory) to catch silent data faults that row/key counts alone would miss. | `.venv` |
| `snapshot_analysis_data.py` | Publishes an analysis-ready snapshot of the family-ladder study to S3, tagging superseded/stale/broken prior snapshots. | `.venv` |
| `evidence_manifest.py` | Builds and verifies `EVIDENCE.json`, the manifest that pins the artifacts (by sha256) a results writeup cites. | `.venv` |

## scripts/smoke/ -- live AWS smoke tests

**These scripts spend real money and touch live AWS accounts.** Never run
them without explicit user opt-in; they provision real EC2 instances /
invoke real Bedrock models and are billed accordingly.

| File | What it's for | Venv |
| --- | --- | --- |
| `bedrock_smoke.py` | Live smoke test of the Bedrock-mantle provider: `list_models` plus one seeded `evaluate` call. | `.venv` |
| `ec2_lifecycle_smoke.py` | Staged live smoke test of the smolbench EC2 provider's provision/serve/shutdown lifecycle. Run as `ec2_lifecycle_smoke.py <step>`. | `.venv` |
