# Evaluations

Evaluation infrastructure for OpenAI-compatible inference providers:
OpenRouter, Prime Intellect, AWS Bedrock/SageMaker, and a self-provisioned
EC2 spot instance running vLLM.

The retry loop, response parsing (content/reasoning channels, `<think>`
splitting, token guard), and parallel quiz evaluation live once in
`openai_compat.py`; each provider module is a thin configuration over it.
Select a provider with `INFERENCE_PROVIDER` (read at call time) and import
`query`/`evaluate` from `provider.py`. Result files round-trip through
`Marks.dump`/`Marks.load` (plain-mapping YAML).

## Layout

```
smolbench/evals/
  __init__.py       re-exports quiz.py's datamodel, so "from smolbench.evals
                    import Marks" keeps working for every caller; no other code
  quiz.py           QnA / ToF / Numeric / Quiz / Mark / Marks
  openai_compat.py  the shared HTTP+parsing engine
  provider.py       name -> provider module registry, call-time dispatch
  providers/        one module per inference backend
    openrouter.py  primeintellect.py  aws.py  ec2.py
  _aws.py           AWS primitives shared by providers/ and results_store
  parsing.py  tokenization.py  replicates.py  results_store.py
  study_config.py   loads study_config.toml (below)
  study_config.toml the committed results bucket/fleet/roster config
  payloads/         byte-exact on-instance assets for providers/ec2.py
```

Only backends live under `providers/`. `provider.py` is the registry, and
putting it inside the package it dispatches to would invert the dependency;
`openai_compat.py` is the engine every backend configures and has no registry
entry of its own; `_aws.py` is a provisioning toolkit shared with
`results_store.py`, not a provider. `payloads/` and `study_config.toml` are
frozen data whose paths cannot move: each is named literally by a
`pyproject.toml` `package-data` anchor, and `.gitattributes` pins `payloads/`
to LF bytes.

`providers/__init__.py` holds a docstring and nothing else, so resolution
stays a call-time act: `provider.provider_module(name)` `importlib`s exactly
one backend, so naming the subpackage never drags in the other three, never
trips `ec2.py`'s read-env-at-first-import contract, and cannot cycle back
through `smolbench.evals`. Below, bare `aws.py`/`ec2.py` mean the modules
under `providers/`.

## Shared AWS provisioning primitives (`_aws.py`)

`aws.py` (Bedrock/SageMaker) and `ec2.py` (EC2 Spot) both stand up an
inference endpoint through IAM/EC2/SageMaker/S3; `_aws.py` is the single copy
of the primitives they share (see its module docstring for the roster and the
lazy-boto3 rule). Two shapes there are load-bearing: `fresh_client` builds a
brand-new `boto3.session.Session` per call, so a rotated `~/.aws/credentials`
is picked up on the next call instead of raising `ExpiredToken` until the
process restarts, and `error_code` degrades to `""` for anything without a
mapping-shaped `.response["Error"]`, including a non-`ClientError`.
`SAGEMAKER_SPEC_KEYS` / `EC2_SPEC_KEYS` say which optional `DeploySpec` fields
each backend actually reads.

Each provider wires its model-specific logic on top through locally-named thin
wrappers (`aws.py`'s `_ensure_exec_role`/`_sagemaker_client`, `ec2.py`'s
`_ec2_client`/`_ensure_instance_profile`/`_error_code`) so existing
`monkeypatch.setattr(module, "_name", ...)` patches keep working.

### Lifecycle correspondence

The two lifecycles are different shapes on purpose; the last row says why.

| | `aws.py` — `provision_endpoint` (SageMaker) | `ec2.py` — `provision_spot_instance` + `serve_model` + `shutdown_instance` (EC2 Spot) |
|---|---|---|
| **Create step** | One `@contextmanager` per model: `create_model` → `create_endpoint_config` → `create_endpoint` (via the pure, offline-pinnable `_create_*_kwargs` helpers). | Split in two: `provision_spot_instance` launches (or reattaches/recovers) ONE shared instance per experiment; `serve_model` only swaps which model its vLLM container serves. |
| **Readiness poll** | `_aws.poll_until` on `describe_endpoint` until `EndpointStatus == "InService"` (raises on `Failed`/`OutOfService`). | `_aws.poll_until` at three points: `_wait_public_ip`, `_wait_agent` (control agent answering after boot/reattach/recovery), and the agent's model-readiness poll inside `serve_model`. |
| **Teardown semantics** | GUARANTEED in a `finally`: delete endpoint → endpoint-config → model, on success, error or `KeyboardInterrupt`, because the billed instance runs until the endpoint is deleted. | `serve_model` tears down NOTHING: the instance is meant to outlive any single archetype section. Abandonment is covered by an on-instance idle watchdog plus an absolute max-lifetime backstop; `shutdown_instance()` is the explicit teardown. |
| **Idempotency** | NOT idempotent against an already-`InService` endpoint of the same name — every call issues fresh `CreateX` calls (a per-model, ephemeral-endpoint contract, not a reattach one). | Idempotent: state-file reattach → tagged-instance recovery (rebuilt from the live instance's user-data if the state file is lost) → fresh launch, in that order, so re-running the cell never strands or duplicates a box. |
| **Why this shape** | A SageMaker endpoint bills per hour for as long as it exists, so every deploy needs a matching unconditional teardown scoped to that model. | Multi-GPU SageMaker quotas default to 0 while EC2 Spot P5 capacity is available, and a fresh multi-GPU box takes minutes to boot, so one instance swapped in place amortizes that cost across the experiment. |

### Resolver correspondence (deliberately not merged)

`aws.py`'s call-time resolvers (`_base_url_template`/`_api_key`/`_connection`)
correspond 1:1 to `ec2.py`'s (`_base_url`/`_api_key`/`_connection`) -- same
job, but kept as two implementations because each reads different env vars and
different state (a static Bedrock/SageMaker bearer token vs. EC2's per-instance
state file), so a merged function would need one branch per call site.

### `metadata_get` and the `check_status` fidelity split

`openai_compat.metadata_get` backs all four provider metadata GETs
(`get_model_context_length` on OpenRouter and Prime Intellect, `list_models`
on AWS and EC2). They differ only in URL and in whether the status is checked
before parsing: `check_status=True` (both `list_models`) calls
`raise_for_status()` first, `check_status=False` parses an error body straight
into the caller's shape-specific indexing. `check_status` has no default, so
the split can never be silently unified.

## Results store

`results_store.py` routes a `ReplicateHarness`'s replicate YAMLs to S3 --
durable across an ephemeral spot instance, and shared between the box that
generated a result and whatever machine analyses it. Local files
(`{prefix}{tag}_{info}/rep_{seed}.yaml` under `notebooks/<notebook>/results/`)
stay the default, the offline/test fallback, and the layout every analysis
script reads; S3 is a separate append-only log with its own key scheme
(`results_store.py`'s module docstring has the full contract).

### Env contract

- `SMOLBENCH_RESULTS_S3=s3://<bucket>[/<base-prefix>]` -- set to route a
  results directory's reads/writes through S3; unset, empty or
  whitespace-only keeps the local store.
- `SMOLBENCH_RESULTS_S3_REGION` -- the S3 client's region. Defaults to
  `AWS_REGION`, then to boto3's own resolution chain.

Both are read inside `resolve_store` at CALL time: a notebook's first cell
runs `load_dotenv(keys.env)` AFTER its imports, so a module-level constant
would freeze to unset (local store) for the rest of the kernel's life and every
replicate would quietly land on the ephemeral box's local disk. `resolve_store`
also falls back to local for any results directory outside `repo_root()`, which
is what keeps `tmp_path` tests hermetic on a shell that exports the variable.

### The S3 log key scheme

```
<base-prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml
induction/gemma-4-12b/seed=0/extens--20260810T193000Z.yaml
```

`experiment` comes from the results directory (`notebooks/<nb>/results` →
`<nb>`), with a harness `prefix` such as `one_hop_` becoming a sub-level
`<nb>/one_hop` instead of folding into the filename as it does locally.
`run_ts` is captured ONCE per seed-collection event, so every info type pooled
for that seed shares one timestamp, and its fixed-width UTC spelling makes
lexicographic order chronological -- earliest-wins is then a string
comparison, with no timestamp parsing in the read path.

### Syncing down for analysis

`ReplicateHarness.sync_down()` (`InductionExperiment` reaches it as
`.harness.sync_down()`) translates an experiment's S3 log into the local
analysis layout. It is the primary entry point because it knows the model →
archetype-tag mapping, which the log does not carry. Outside a notebook,
supply that mapping explicitly:

```
python -m smolbench.evals.results_store notebooks/induction/results --tag gpt-oss-120b=moe
```

`--tag model=tag` is repeatable (one per model in the study); `--prefix
one_hop_` supplies a harness prefix.

**Run this before analysis, not after** -- `notebooks/*/analysis/` scripts read
local trees, so results that only ever landed in S3 are invisible to them
until `sync_down` has pulled them down. It is one-way and OVERWRITES the
matching local path, and a score flip (`1` → `0`) is byte-length preserving,
so a clobbered local edit leaves no size or presence signal that anything was
lost.

## Provisioning the bucket

`scripts/results/provision_results_bucket.py` is the one-time (idempotent)
runbook that provisions the bucket named in `study_config.toml`, with all four
block-public-access flags on and versioning enabled. It also creates the
managed IAM policy `SmolbenchResultsBucketRW` -- `s3:ListBucket` on the
bucket, `s3:GetObject`/`s3:PutObject`/`s3:DeleteObject` on its contents -- and
attaches it to the `smolbench-ec2-operators` group. This needs ADMIN
credentials: the scoped operator key the eval drivers use day-to-day is
EC2-only and cannot manage S3 or IAM. See the script's module docstring for
the runbook and its exit-status contract.
