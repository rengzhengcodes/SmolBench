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

## Shared AWS provisioning primitives (`_aws.py`)

`aws.py` (Bedrock/SageMaker) and `ec2.py` (self-provisioned EC2 Spot) both
need to talk to IAM/EC2/SageMaker/S3 to stand up an inference endpoint, and
used to each carry their own copy of the same handful of primitives.
`smolbench/evals/_aws.py` is now the single copy: `fresh_client` (a
brand-new `boto3.session.Session` per call, so a rotated
`~/.aws/credentials` file is picked up on the next call instead of raising
`ExpiredToken` until the process restarts), `error_code` (a
`ClientError.Code` extractor that degrades to `""` for a non-`ClientError`
input), `assume_role_trust_policy` (parameterized on the service principal),
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

`openai_compat.metadata_get` now backs all four provider metadata GETs that
used to be near-identical copies: OpenRouter's and Prime Intellect's
`get_model_context_length`, and AWS's and EC2's `list_models`. All four
issue the same bearer-authenticated `requests.get(...).json()` call and
differ only in URL and in whether the response status is checked before
parsing — `check_status=True` (AWS/EC2's `list_models`, both) calls
`raise_for_status()` first; `check_status=False` (OpenRouter/Prime
Intellect's context-length lookups) parses an error body straight into the
caller's shape-specific indexing, matching each provider's pre-extraction
behavior exactly. `check_status` has no default specifically so this split
can never be silently unified into one "correct" choice.

### Known delta and recommended re-verification

`aws.py`'s SageMaker client construction (`_sagemaker_client`, and every
`_aws.py`-mediated IAM call) moved from `boto3.client(...)` against the
process-wide default session to a fresh `boto3.session.Session()` per call —
the same fix `ec2.py` already used, now shared via `_aws.fresh_client`. This
is payload-invariant (identical API calls and request bodies either way);
it only changes which credentials snapshot signs the request, so a rotated
`~/.aws/credentials` file is picked up on the very next call instead of
raising `RequestExpired`/`ExpiredToken` until the process restarts. Because
this touches every live AWS call this module makes, a live re-verification
(`scripts/bedrock_smoke.py` for aws.py, `scripts/ec2_lifecycle_smoke.py` for
ec2.py) is recommended before the next real provisioning run, even though
the offline suite already pins every request payload byte-for-byte.
