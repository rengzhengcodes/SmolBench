# Evaluations

Evaluation infrastructure for OpenAI-compatible inference providers:
OpenRouter, Prime Intellect, AWS Bedrock/SageMaker, and a self-provisioned
EC2 spot instance running vLLM.

The retry loop, response parsing (content/reasoning channels, `<think>`
splitting, token guard), and parallel quiz evaluation live once in
`openai_compat.py`; each provider module is a thin configuration over it.
Select a provider with `INFERENCE_PROVIDER` (read at call time) and import
`query`/`evaluate` from `provider.py`. Result files round-trip through
`Marks.dump`/`Marks.load` (plain-mapping YAML; the loader also reads the
legacy `!!python/object`-tagged files).

## Layout

```
smolbench/evals/
  __init__.py       re-exports the quiz.py datamodel; no other code
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

Only the four backends live under `providers/`. Everything that is not a
backend deliberately stays at the `evals/` level:

- `provider.py` is the registry; putting it inside the package it dispatches
  to would invert the dependency.
- `openai_compat.py` is the engine every backend configures, and is not
  itself selectable by `INFERENCE_PROVIDER` — it has no registry entry.
- `_aws.py` is shared by `providers/aws.py`, `providers/ec2.py` AND
  `results_store.py` (S3); it is a provisioning toolkit, not a provider.
- `parsing.py`, `tokenization.py`, `replicates.py`, `results_store.py` are
  provider-agnostic; `payloads/` is frozen data (`.gitattributes` pins its
  bytes to LF and `pyproject.toml`'s `package-data` anchor names
  `smolbench.evals.payloads` literally), so its path does not move.
- `study_config.py`/`study_config.toml` are the single committed source for
  the induction family-ladder study's results bucket/region, fleet
  regions/tag vocabulary, and 21-checkpoint roster — read by `providers/ec2.py`,
  `results_store.py`, `notebooks/induction/run_study.py` and
  `notebooks/induction/analysis/power_analysis.py` instead of each carrying
  its own copy. `study_config.toml` needs its own `pyproject.toml`
  `package-data` entry for the same reason `payloads/` does (see above).

Below this section, bare `aws.py` and `ec2.py` mean `providers/aws.py` and
`providers/ec2.py`; the shorter names are kept because the lifecycle and
resolver tables read as comparisons between the two backends.

`providers/__init__.py` holds a docstring and nothing else — no imports, no
re-exports. Provider resolution therefore stays a call-time act:
`provider.provider_module(name)` `importlib`s exactly one backend, so
naming the subpackage never drags in the other three, never trips
`ec2.py`'s read-env-at-first-import contract, and cannot cycle back through
`smolbench.evals`.

The on-disk mark YAML is also read by an independent regex parser
(`notebooks/induction/analysis/power_analysis.py` matches `score:` lines
rather than loading the document), so the per-mark `score:` line shape is
a format contract, not an implementation detail.

### The `__init__.py` -> `quiz.py` split

The datamodel lives in `quiz.py`; `__init__.py` re-exports `Answer`, `QnA`, `ToF`, `Numeric`, `Quiz`, `Mark`
and `Marks` from it. That re-export is load-bearing twice over: it keeps
`from smolbench.evals import Marks` working for every caller, and it keeps
the legacy YAML tag `!!python/object:smolbench.evals.Marks` resolving in
result files written before the split (pinned by
`tests/evals/test_marks_io.py`'s legacy fixture).

## Shared AWS provisioning primitives (`_aws.py`)

`providers/aws.py` (Bedrock/SageMaker) and `providers/ec2.py`
(self-provisioned EC2 Spot) both
need to talk to IAM/EC2/SageMaker/S3 to stand up an inference endpoint.
`smolbench/evals/_aws.py` is the single copy of those primitives: `fresh_client` (a
brand-new `boto3.session.Session` per call, so a rotated
`~/.aws/credentials` file is picked up on the next call instead of raising
`ExpiredToken` until the process restarts), `error_code` (a
`ClientError.Code` extractor that degrades to `""` for any input without a
mapping-shaped `.response["Error"]`, including a non-`ClientError`),
`assume_role_trust_policy` (parameterized on the service principal),
`ensure_sagemaker_execution_role` / `ensure_instance_profile` (IAM
role/profile creation, idempotent against "already exists"), the generic
`poll_until` wait loop, `best_effort_teardown` (runs every teardown step,
never raises, logs each outcome), and the `DeploySpec` TypedDict shape
(`SAGEMAKER_SPEC_KEYS` / `EC2_SPEC_KEYS` enumerate which optional fields
each backend actually reads). Each provider module wires its own
model/endpoint-specific logic on top, through locally-named thin wrappers
(`aws.py`'s `_ensure_exec_role`/`_sagemaker_client`, `ec2.py`'s
`_ec2_client`/`_ensure_instance_profile`/`_error_code`) so existing
`monkeypatch.setattr(module, "_name", ...)` test patches keep working
unchanged. boto3/botocore are imported lazily inside every `_aws.py`
function, same convention as both provider modules — the pure-inference
path never needs AWS credentials or the SDK installed.

### Lifecycle correspondence

The two providers' endpoint lifecycles are deliberately different shapes,
not accidentally divergent — a SageMaker endpoint bills per hour until
deleted, so it is provisioned and torn down once per model; an EC2 instance
is shared across an entire experiment, so it is provisioned once and only
ever swapped between models.

| | `aws.py` — `provision_endpoint` (SageMaker) | `ec2.py` — `provision_spot_instance` + `serve_model` + `shutdown_instance` (EC2 Spot) |
|---|---|---|
| **Create step** | One `@contextmanager` per model: `create_model` → `create_endpoint_config` → `create_endpoint` (via the pure, offline-pinnable `_create_model_kwargs`/`_create_endpoint_config_kwargs`/`_create_endpoint_kwargs`). | Split in two: `provision_spot_instance` launches (or reattaches/recovers) ONE shared instance per experiment; `serve_model` only ever swaps which model its vLLM container serves — no new instance, no new AWS resources. |
| **Readiness poll** | `_aws.poll_until` on `describe_endpoint` until `EndpointStatus == "InService"` (raises on `Failed`/`OutOfService`). | `_aws.poll_until` at three points: `_wait_public_ip` (a fresh launch), `_wait_agent` (control agent answering after boot/reattach/recovery), and the control agent's own model-readiness poll inside `serve_model`. |
| **Teardown semantics** | GUARANTEED in a `finally`: delete endpoint → endpoint-config → model, on success, error, or `KeyboardInterrupt` — because the billed instance keeps running until the endpoint is deleted. | `serve_model` tears down NOTHING on exit — the instance is meant to outlive any single archetype section. Abandonment is instead covered by an on-instance idle watchdog + an absolute max-lifetime backstop; `shutdown_instance()` is the explicit, once-per-experiment teardown. |
| **Idempotency** | Re-entering `provision_endpoint(model)` is NOT idempotent against an already-`InService` endpoint of the same name — each call always issues fresh `CreateX` calls (this is a per-model, ephemeral-endpoint contract, not a reattach one). | `provision_spot_instance()` IS idempotent: state-file reattach → tagged-instance recovery (rebuilt from the live instance's user-data if the state file is lost) → fresh launch, in that order — re-running the cell (or restarting the kernel) never strands or duplicates a box. |
| **Why this shape** | A SageMaker endpoint bills per hour for as long as it exists, so every deploy must have a matching, unconditional teardown scoped to that one model's lifetime. | Multi-GPU SageMaker endpoint quotas default to 0, while EC2 Spot capacity for the P5 family is available — but a fresh multi-GPU box takes minutes to boot, so re-provisioning per archetype would be wasteful; one instance, swapped in place, amortizes that cost across the whole experiment. |

There is deliberately no shared `provision → poll → yield → teardown`
framework above these primitives: each lifecycle shape has exactly one
consumer, so a framework generalized over a single call site would just be
this module's functions with extra ceremony. Sharing the genuinely-repeated
small pieces gets the deduplication benefit without inventing an
abstraction neither caller asked for. See `_aws.py`'s module docstring for
the full version of this rationale.

### Resolver correspondence (deliberately not merged)

`aws.py`'s call-time resolvers (`_base_url_template`/`_api_key`/
`_connection`) correspond 1:1 to `ec2.py`'s (`_base_url`/`_api_key`/
`_connection`) — same job (build a chat-completions URL + bearer token per
call) but deliberately kept as two independent implementations rather than
one shared resolver: each reads different env vars and different state (a
static Bedrock/SageMaker bearer token vs. EC2's per-instance state file), so
a merged function would need as many branches as there are call sites
today, buying nothing over two small independent functions.

### `metadata_get` and the `check_status` fidelity split

`openai_compat.metadata_get` backs all four provider metadata GETs:
OpenRouter's and Prime Intellect's
`get_model_context_length`, and AWS's and EC2's `list_models`. All four
issue the same bearer-authenticated `requests.get(...).json()` call and
differ only in URL and in whether the response status is checked before
parsing — `check_status=True` (AWS/EC2's `list_models`, both) calls
`raise_for_status()` first; `check_status=False` (OpenRouter/Prime
Intellect's context-length lookups) parses an error body straight into the
caller's shape-specific indexing. `check_status` has no default specifically so this split
can never be silently unified into one "correct" choice.

## Results store

`results_store.py` gives replicate results a second backend. Every
replicate YAML a `ReplicateHarness` produces
(`{prefix}{tag}_{info}/rep_{seed}.yaml`)
is written straight to a local directory under `notebooks/<notebook>/
results/`. With `results_store.py` in the loop, the same file can instead
be logged to S3 — durable across an ephemeral EC2 spot instance's lifetime,
and shared between the box that generated it and whatever machine later runs
the analysis.

### Two layouts, one interface

LOCAL storage is the default and the offline/test fallback (see "Local
fallback" below): `{prefix}{tag}_{info}/rep_{seed}.yaml` under
`notebooks/<notebook>/results/`. Every analysis script and notebook reads
this layout regardless of where a study's replicates were originally
written.

S3 is a separate, append-only EXPERIMENT LOG, not a mirror of the local
layout — see "The S3 log key scheme" below for its own key shape, and
"Syncing down for analysis" for how a log gets turned back into a local
tree the existing analysis tooling can read.

### Env contract

Two environment variables select and configure the S3 backend:

- `SMOLBENCH_RESULTS_S3=s3://<bucket>[/<base-prefix>]` — set to route a
  results directory's reads/writes through S3; unset, empty, or
  whitespace-only keeps the local store.
- `SMOLBENCH_RESULTS_S3_REGION` — the S3 client's region. Defaults to
  `AWS_REGION` if unset, and to boto3's own resolution chain (profile
  config, instance metadata, …) if that is unset too.

Both are read INSIDE `resolve_store`, at CALL time — never captured as
module-level constants. This matters because every notebook's first cell
calls `load_dotenv(keys.env)` *after* `import smolbench...`-style statements
have already run; a module-level constant would freeze to the un-overridden
default (unset → local store) for the rest of the kernel's life, silently,
with every subsequent replicate quietly landing on the ephemeral box's local
disk instead of S3.

### The S3 log key scheme

A logged replicate's S3 key has the shape:

```
<base-prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml
```

worked example:

```
induction/gemma-4-12b/seed=0/extens--20260810T193000Z.yaml
```

Each level:

- `base-prefix` — the optional path component carried by
  `SMOLBENCH_RESULTS_S3`'s URI (``s3://<bucket>/<base-prefix>``); omitted
  entirely when the URI names the bucket root.
- `experiment` — derived from the results directory, repo-relative:
  `notebooks/<nb>/results` → `<nb>`. A harness `prefix` such as
  `one_hop_` becomes a sub-level, `<nb>/one_hop`, rather than folding into
  the filename the way it does locally.
- `model` — the model id exactly as passed to `run_replicates`.
- `seed=<seed>` — a literal, browsable marker (not a bare number) so a
  console/CLI listing of an experiment+model prefix reads as one row per
  seed.
- `<info>--<run_ts>` — `info` is the info type (e.g. `extens`, `intens`);
  `run_ts` is a fixed-width UTC timestamp, `YYYYMMDDTHHMMSSZ`, captured ONCE
  per seed-collection event so every info type pooled for that seed shares
  one timestamp.

Fixed-width UTC matters specifically because it makes lexicographic key
order the same as chronological order: "the earliest run for this
(model, seed, info)" is answered by a plain string comparison / sort over
sibling keys, with no timestamp parsing required anywhere in the read path.

### Append-only, and earliest-wins

Writes always create a new `<info>--<run_ts>.yaml` object; they never
overwrite a prior run's object. Re-running an experiment against an
already-logged (model, seed) therefore accumulates history rather than
replacing it. Every read path resolves the EARLIEST `run_ts` per
(model, seed, info), so a forced re-run stays in the log but is invisible
to analysis -- voiding data requires an explicit exclusion, not a newer
object. `ReplicateHarness`'s resume-skip check asks only whether ANY run
has been logged for that (model, seed, info), not which one.

### Local fallback and test-suite hermeticity

`resolve_store` falls back to `LocalResultsStore` whenever the results
directory is not under `repo_root()` — even with `SMOLBENCH_RESULTS_S3` set.
`pytest`'s `tmp_path` fixtures are always outside the repo checkout, so this
is what keeps the offline test suite exercising the local store
unconditionally, even on a developer's shell that happens to export
`SMOLBENCH_RESULTS_S3` for their own interactive notebook work. No test needs
to unset the variable to stay hermetic.

### Syncing down for analysis

`ReplicateHarness.sync_down()` (an `InductionExperiment` reaches it as
`.harness.sync_down()`) is the bridge: it translates an experiment's S3 log into the
local analysis layout, resolving the earliest run per (model, seed, info) and
writing `{prefix}{tag}_{info}/rep_{seed}.yaml`. It is the primary entry
point because it is the piece that knows the model → archetype-tag mapping
— information the log itself does not carry, since the log keys on the
model id, not the tag.

The module is also runnable as a CLI, for use outside a notebook, where that
mapping has to be supplied explicitly:

```
python -m smolbench.evals.results_store notebooks/induction/results --tag gpt-oss-120b=moe
```

`--tag model=tag` is repeatable (one per model in the study); `--prefix
one_hop_` supplies a harness prefix for a prefixed experiment.

**Run this before analysis, not after** — `notebooks/*/analysis/power_analysis.py`
and the figure scripts all read local trees, so any results that only ever
landed in S3 are invisible to them until `sync_down` has pulled them down.

### sync_down is destructive and one-way

`sync_down` goes S3 → local only: it never uploads, and it OVERWRITES
whatever is already at the matching local path. This matters for anything
that edits a results tree locally — concretely, `scripts/results/regrade.py
--write`, which rewrites `rep_*.yaml` in place. A local regrade is silently
clobbered back to the stale synced copy by the very next `sync_down`,
because a score flip (e.g. `1` → `0`) is byte-length preserving and so
leaves no size/presence signal that anything was lost. For exactly this
reason, `regrade.py` refuses to run at all while an S3 store is configured
(see its module docstring's "S3-backed results guard" section) — the safe
sequence to regrade an S3-backed study is: sync down, unset
`SMOLBENCH_RESULTS_S3`, run the regrade, then deliberately re-write the
regraded results back through the store (so the write lands in the current
log layout, not bulk-uploaded).

### Provisioning the bucket

`scripts/results/provision_results_bucket.py` is the one-time (idempotent, safe to
re-run) runbook that provisions the bucket itself, named and located as
recorded in `study_config.py`'s committed `study_config.toml`
(`smolbench-results-414266451290` in `us-west-2`, at the time of writing),
with public access blocked (all four block-public-access flags on) and
versioning enabled. It also creates the managed IAM policy
`SmolbenchResultsBucketRW` — `s3:ListBucket` on the bucket,
`s3:GetObject`/`s3:PutObject`/`s3:DeleteObject` on its contents — and
attaches it to the `smolbench-ec2-operators` group.

This needs ADMIN credentials: the scoped operator key used day-to-day by the
eval drivers is deliberately EC2-only and cannot manage S3 or IAM.

The bucket holds no pre-migration results and none should be seeded into
it. Any import of historical results must go THROUGH `results_store.py` so
it lands in the log layout above -- never bulk-synced in a repo-mirroring
layout, which nothing reads.

See the script's module docstring for the full runbook and its
exit-status contract.
