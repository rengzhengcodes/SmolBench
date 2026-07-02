# Refactor record: `/simplify` + code-review cleanup pass

This documents two related efforts on the `periodic-induction` branch:

1. The **`/simplify` refactor** (commit `26e75cb`, 2026-07-01): collapsed the
   provider stack onto one shared client, made configuration call-time, and
   deduplicated the benchmark generators and figure scripts.
2. The **code-review cleanup pass** (2026-07-02): an xhigh review of that
   refactor plus a follow-up modularization/readability/de-hardcoding pass,
   implemented by five scoped implementer agents and re-verified.

---

## Part 1 — the `/simplify` refactor (26e75cb)

### 1.1 Provider consolidation onto `ChatClient`

Before: `aws.py`, `openrouter.py`, `primeintellect.py`, and `ec2.py` each
carried a hand-copied ~150-line query/retry/parse/evaluate implementation that
had drifted apart. After: one engine, four thin configs.

- `smolbench/evals/openai_compat.py` — the shared core. `ChatClient` is a
  frozen dataclass holding connection resolution (a `connection: Callable`
  returning `(base_url, api_key)` at call time), retry policy
  (`is_retryable_request_error`, per-provider backoff), the chat-completions
  round trip (`query`, including reasoning-channel extraction from
  `reasoning_content` / `<think>` tags), answer grading (`grade`), and the
  joblib thread-pool fan-out (`evaluate`).
- Each provider module now defines only: a `_connection()` resolver (env →
  base URL + key), `get_model_context_length`, one `_CLIENT = ChatClient(...)`
  instance, and re-exports `query = _CLIENT.query` / `evaluate =
  _CLIENT.evaluate`. This thin-config shape is the intended endpoint — do not
  collapse the modules further.

### 1.2 Call-time provider dispatch

`smolbench/evals/provider.py` maps `INFERENCE_PROVIDER` names to modules
(`aws`/`bedrock`/`sagemaker` alias the same module) and imports the target
inside `_provider_module()` at each call. Setting `INFERENCE_PROVIDER` or
provider env vars after import Just Works — the import-order trap and the
module-global mutation it replaced are gone. A guard gives an actionable
error for `sagemaker` without a base URL.

**Scope note:** the call-time guarantee covers the *inference path* (base
URLs, bearer tokens, state-file path, context-length overrides). The
*provisioning* constants (`EC2_INSTANCE_TYPES`, `EC2_VLLM_IMAGE`,
`EC2_EXPERIMENT_TAG`, `EC2_S3_*`, `SAGEMAKER_VLLM_DLC`, ...) are import-time
captures, because the notebooks bind them as module attributes. Set them (via
`keys.env` / `load_dotenv`) **before** the first import. The module
docstrings now state this precisely (fixed in Part 2).

### 1.3 `Marks.dump` / `Marks.load` (plain-dict YAML IO)

Result files used to be written with `yaml.dump` of dataclass objects,
producing `!!python/object` tags that require `unsafe_load` forever.
`Marks.dump` now writes `asdict()` plain dicts via `safe_dump`; `Marks.load`
sniffs the leading bytes and routes legacy tagged files through
`unsafe_load`, everything else through `CSafeLoader`. Old committed results
stay loadable; new results are safe and portable. The on-disk format is
deliberately parsed in three places (`Marks.load` plus the two standalone
regex-based `power_analysis.py` scripts) — **do not change the format**.

### 1.4 `ReplicateHarness` (`smolbench/evals/replicates.py`)

The replicate-running harness that each eval notebook used to hand-copy (and
had begun to fork) moved into the package: per-(archetype, info-type, seed)
result files under a `results_dir`, pooling of outstanding info-types into a
single `provider.evaluate` call per seed, idempotent resume (existing files
skipped, missing replicates re-run without touching others), `summarize`, and
`cot_chain_lengths`. Notebooks now hold only configuration.

### 1.5 Induction + figure deduplication

`smolbench/induction/_common.py` owns the pieces that must stay calibrated
across the periodic and chromatic benchmarks (`Prompter`, noise charset,
unique-label sampling, quiz assembly). `lean/figures/_util.py` owns row
loading, the rung vocabulary, and model family/color helpers for the six
figure scripts. (Both were deduplicated further in Part 2.)

### 1.6 Offline test suite (27 tests at the time)

`tests/` gained a stub OpenAI-compatible HTTP server (`conftest.py`,
`ThreadingHTTPServer` on an ephemeral port) and suites covering: per-provider
round trips, call-time dispatch, Marks IO (including real committed legacy
files), EC2 payload validity (payloads must stay 3.10-parseable, stdlib-only,
runnable **unrendered**, with rendered user-data < 16 KB), golden quiz
regression (SHA-256 of full quizzes at production configs, seeds 1776/1777 —
**never re-baseline these to make a failure pass**), and harness
pooling/resume semantics.

### 1.7 How `/simplify` was verified (2026-07-02, all passed)

- Offline: the 27-test suite.
- Live EC2 lifecycle: provision → serve (`qwen2.5-1.5b`) → evaluate 4/4 →
  shutdown on a g6.2xlarge spot in us-east-1 (~13 min end-to-end), isolated
  via its own `EC2_EXPERIMENT_TAG` and `EC2_STATE_FILE`; live harness
  resume-skip verified against the box.
- Live Bedrock-mantle: `list_models` (51), plain-content sanity, seeded
  `qwen.qwen3-32b` with `reasoning_effort=high` → CoT landed in
  `Mark.reasoning`, content parsed and scored.
- SageMaker: `mint_sagemaker_token()` well-formed; call-time
  `AWS_INFERENCE_API_KEY` override semantics confirmed. (Full endpoint
  provisioning is environmentally blocked and was deliberately skipped.)

---

## Part 2 — the code-review cleanup pass (2026-07-02)

An xhigh multi-agent review of the branch plus a scoped cleanup, implemented
as five parallel agents with disjoint file ownership, each gated on the full
test suite; induction changes additionally gated on byte-identical golden
quizzes, figure changes on byte-identical output PNGs.

### 2.1 Providers (`aws.py`, `openrouter.py`, `primeintellect.py`, `openai_compat.py`)

- `METADATA_TIMEOUT_S = 120` in `openai_compat.py` replaces the `timeout=120`
  literal copied into every catalog/context-length lookup (chat completions
  keep their own, much longer, configurable timeouts).
- `aws.py`: the bedrock-mantle default URL is now
  `AWS_BEDROCK_DEFAULT_BASE_URL_TEMPLATE` (formatted with the region at call
  time) and the context-length fallback is
  `AWS_BEDROCK_DEFAULT_CONTEXT_LENGTH = 200000` (env override
  `AWS_BEDROCK_CONTEXT_LENGTH` still read at call time).
- Deleted `aws._CONTEXT_LENGTHS`: a module-global override dict that was read
  but never written anywhere — permanently empty, i.e. dead code.
- Module docstrings corrected re: import-time vs call-time env (see 1.2).

### 2.2 EC2 provider (`ec2.py`)

- **Ports named**: `EC2_VLLM_PORT = 8000` / `EC2_AGENT_PORT = 9000` replace
  literals scattered across `_base_url`, `_connection`, security-group
  ingress, and agent URLs. The vLLM port is threaded into the instance via a
  new `SMOLBENCH_VLLM_PORT` line in the bootstrap env file (new
  `_render_user_data(..., vllm_port=EC2_VLLM_PORT)` parameter, defaulted so
  existing callers are unchanged); `AGENT_PY`/`WATCHDOG_PY` read it with a
  `"8000"` string default so they still run unrendered (a frozen-test
  requirement). The `8000`s that are docker log-tail sizes were deliberately
  left alone.
- **`provision_spot_instance` decomposed** from ~240 lines into an ~50-line
  orchestrator over four documented helpers, preserving branch order, log
  messages, and side effects exactly:
  `_reattach_existing_instance` (state-file reuse) →
  `_recover_tagged_instance` (state file lost, live tagged instance found via
  its user-data) → `_launch_fresh` (type-major capacity hunt), with the
  45-line `run_instances` kwargs dict extracted into the pure
  `_run_instances_kwargs` — now pinned by a unit test transcribed from the
  pre-refactor literal, so extraction drift is caught offline.
- **Bug fix**: `_wait_agent`'s liveness check wrapped `describe_instances` in
  `except ImportError:` — dead code, since describe failures raise botocore
  `ClientError`. Now catches `ClientError` (transient describe blips no
  longer risk aborting the wait) while the genuine instance-died
  `RuntimeError` still propagates.
- **Bug fix**: `WATCHDOG_PY`'s `STARTUP_GRACE_MIN` fallback said `"120"`
  while the module default is 180; aligned to `"180"` so a failed env
  propagation can't silently halve the startup grace window.
- Poll/timeout magic numbers named (`_WAIT_IP_TIMEOUT_S`, `_WAIT_IP_POLL_S`,
  `_AGENT_POLL_S`, `_AGENT_PROGRESS_EVERY_N_POLLS`, `_MODEL_READY_POLL_S`,
  `_IAM_PROPAGATION_SLEEP_S`, `_METADATA_TIMEOUT_S` — the last deliberately
  local, not shared with `openai_compat`, to keep the modules decoupled).
- `_instance_state(region, instance_id)` helper added where it fit
  (`_wait_agent`); the other describe sites keep their inline form because
  they reuse other fields from the same describe call (the helper would
  double the API calls) — each carries a NOTE comment saying so.
- `EC2_EXPERIMENT_TAG`'s comment now flags that its default
  (`periodic-induction`) is experiment-specific and must be overridden via
  env **before** import (chromatic does this in its `keys.env`).

### 2.3 Induction (`_common.py`, `periodic.py`, `chromatic.py`)

All changes byte-identical under the golden quiz tests (seeds 1776/1777).

- **Bug fix — `chromatic.duration_query_gen`**: `if not intervals:` on a 2-D
  ndarray raises `ValueError` for any color holding ≥1 interval (each row has
  2 elements), so the function could never run against real data. Fixed with
  `len(intervals) == 0` — a *count* check, chosen over the superficially
  similar `.any()` because `.any()` tests element values and would wrongly
  drop a color holding a single degenerate `(0, 0)` interval whose correct
  answer is `total=0`. Covered by a new semantic regression test.
- **Calibration-critical logic hoisted into `_common.py`** (the module whose
  stated purpose is keeping the two benchmarks calibrated): `noise_pad`
  (the `seed + 1` noise-RNG derivation + pad-to-extensional-length math,
  previously copy-pasted byte-identically), `random_labels` (the
  `ceil(log_charset(count)) * LABEL_LENGTH_SAFETY_FACTOR` length formula,
  *parameterized* — periodic uses lowercase charset + `min_length=2`,
  chromatic `ascii_letters` + no floor; the two blocks were NOT identical and
  a naive hoist would have broken the goldens), `build_substitution` (the
  `query | prompter.substitution | {"positive_info": ...}` merge, repeated
  4×), and `Prompter.resolved_extens_template` (the `extens_template or
  template` fallback).
- Readability: the nested-quote line-broken f-string in
  `get_random_exclusive_prompts` unpacked into locals (with the
  loop-invariant `role` lookup hoisted); `random_unique_strings`'s `l`
  parameter renamed `length`; `_prompt_intervals` / `_prompt_extensional`
  now share `_join_english_list` (verified byte-identical for 1/2/3/4-item
  lists, including the two-item no-comma form).

### 2.4 Lean figures (`lean/figures/`)

- `_util.py` gained `DEFAULT_RUNS`, `DEFAULT_FIGSIZE`, `parse_runs_args()`,
  `figure_out_path()`, `save_figure()` — removing the header/argparse/footer
  boilerplate copied (with drift) across all six scripts — and
  `build_success_buckets(...)` → `SuccessBuckets`, the ~40-line
  trivial-skip/solvable-subset/EXCLUDE_MODELS/low-n pipeline previously
  duplicated by `success_rate_per_model_rung.py` and
  `success_rate_with_noise.py` (their one real difference, the `keep_rungs`
  intersection, is now an explicit parameter).
- Deliberately NOT forced into the shared pipeline:
  `response_length_per_model_rung.py` (accumulates token counts, not
  verdicts), `success_rate_bars.py` (needs family-color grouping),
  `marginal_content_vs_noise.py` (never handles the no-hint rung).
- Verified by SHA-256 PNG comparison on a deterministic synthetic fixture
  (fixed `MPLBACKEND=Agg`, `PYTHONHASHSEED=0`, `SOURCE_DATE_EPOCH=0`): all
  six scripts byte-identical before/after; fixture and smoke PNGs removed.

### 2.5 Tests (27 → 52)

New/extended coverage: EC2 state-file lifecycle (round trip, 0600 mode,
corrupt-JSON fallback, call-time `EC2_STATE_FILE`), `_run_instances_kwargs`
pinned against the pre-refactor literal, `_instance_state`,
`cot_chain_lengths` (print contract, via `capsys`), a primeintellect stub
round trip (last uncovered provider), and `tests/test_induction_semantics.py`
— answers recomputed from the underlying rules (brute-force divisibility
counts, successor pairs rebuilt from the raw interval map, annealed duration
totals) so a wrong-but-self-consistent generator drift cannot be silently
re-baselined into the golden hashes.

### 2.6 Review findings & resolutions

<!-- FILLED AFTER THE XHIGH REVIEW WORKFLOW COMPLETES -->
(pending)

### 2.7 Verification status for this pass — ALL PASSED (2026-07-02)

- Offline: full suite green after every wave (final: 52 passed). Golden
  quizzes byte-identical throughout; figure PNGs byte-identical on the
  synthetic fixture; `python -m smolbench.induction.periodic` / `.chromatic`
  demos run clean.
- Live Bedrock-mantle (covers every aws.py change): `list_models` → 51
  models via `METADATA_TIMEOUT_S` + the URL-template constant;
  `get_model_context_length` default 200000 via the new constant; seeded
  `evaluate` 2/2 on `google.gemma-3-12b-it`, clean content, no phantom
  reasoning.
- Live EC2 lifecycle (isolated `EC2_EXPERIMENT_TAG=cleanup-smoke-0702`, own
  state file, g6.2xlarge spot us-east-1, instance `i-0050fb83db8d92f2d`):
  - Fresh launch in 65 s: `_launch_fresh` + `_run_instances_kwargs` accepted
    by the real API, user-data with `SMOLBENCH_VLLM_PORT` threading booted,
    agent answered, security group opened on the named port constants. (A
    prior attempt correctly exhausted 2 types × 6 AZs of dry spot capacity
    and raised the aggregated actionable error — the hunt path works.)
  - `serve_model("qwen2.5-1.5b")` healthy at ~5.8 min → seeded 4-question
    `evaluate` 4/4 (vLLM port constant proven end-to-end).
  - Reattach branch: second `provision_spot_instance()` returned the same
    instance in 2.6 s via the state file.
  - Recovery branch: state file deleted → re-provision recovered the SAME
    instance in 2.9 s from its `smolbench:experiment` tag + user-data
    secrets.
  - `shutdown_instance()`: tag-filtered `describe-instances` shows
    `terminated`; state file cleared. Nothing left running.

### 2.8 Live-verification runbook (for future re-runs)

Smoke drivers are committed under `scripts/` (they are `__main__` scripts,
not pytest tests). With fresh creds for profile `rengz`:

```bash
cd /workspace/SmolBench
export AWS_PROFILE=rengz AWS_REGION=us-east-1
export EC2_EXPERIMENT_TAG=cleanup-smoke-0702 \
       EC2_STATE_FILE=/tmp/cleanup_smoke_state.json \
       EC2_INSTANCE_TYPES=g6.2xlarge,g5.2xlarge \
       EC2_REGIONS=us-east-1 EC2_ROOT_VOLUME_GB=100 EC2_IDLE_TIMEOUT_MIN=25

# 1. EC2 lifecycle (~15 min, ~$0.30): each step must print "OK".
.venv/bin/python scripts/ec2_lifecycle_smoke.py provision   # fresh-launch branch, port threading, _wait_agent
.venv/bin/python scripts/bedrock_smoke.py                   # (while it boots) aws.py: list_models, ctx default, seeded evaluate
.venv/bin/python scripts/ec2_lifecycle_smoke.py serve_eval  # vLLM port end-to-end; 4-question seeded evaluate
.venv/bin/python scripts/ec2_lifecycle_smoke.py reattach    # state-file branch (must return in seconds)
.venv/bin/python scripts/ec2_lifecycle_smoke.py recover     # deletes state file; tag-recovery branch must find the same instance
.venv/bin/python scripts/ec2_lifecycle_smoke.py shutdown

# 2. Confirm nothing is left running/billing:
aws ec2 describe-instances --region us-east-1 \
  --filters "Name=tag:smolbench:experiment,Values=cleanup-smoke-0702" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output table
```

What each step certifies: `provision` exercises `_launch_fresh` +
`_run_instances_kwargs` + user-data rendering with the new port threading +
security-group setup + the fixed `_wait_agent`; `reattach`/`recover` cover
the other two decomposed branches; `serve_eval` proves the vLLM port constant
end-to-end; `bedrock_smoke` covers every aws.py change. Skips (justified):
SageMaker provisioning (untouched, environmentally blocked),
openrouter/primeintellect live (non-AWS, stub-covered), big-model serves and
notebook reruns (nothing they exercise changed beyond what the smoke covers).
Even if a smoke step dies mid-run, the instance's own idle watchdog
(25 min) and max-lifetime backstop terminate it. If spot capacity is dry,
widen the hunt (this run needed
`EC2_INSTANCE_TYPES=g6.2xlarge,g5.2xlarge,g6e.2xlarge` and
`EC2_REGIONS=us-east-1,us-east-2,us-west-2` on the second attempt).

---

## Deferred / known items

- **Notebook scaffold dedup** (deferred): the three eval notebooks share a
  near-identical 14-cell harness/provision/serve-loop scaffold, and the two
  chromatic notebooks differ only in query generator, prefix, CoT tuning,
  and near-identical templates. Extracting a package-level driver is a real
  win but can't be cheaply verified (requires expensive p5 provisioning), so
  it was deliberately left for a dedicated session.
- `power_analysis.py` scripts stay standalone-by-regex (`uv run
  --no-project`) by design; `induction_eval_analysis.ipynb` stays pinned to
  the archived `result2/` pilot.
- `ChatClient.query`'s `context_length=0` default fails any usage-reporting
  response by design (documented footgun; `evaluate` supplies the real
  value). `seed` must remain in every request.
- Rendered user-data is at 16074/16384 bytes — ~310 bytes of headroom under
  the frozen 16 KB cap. The next payload edit will likely need to reclaim
  space (trim payload comments first).
- `ReplicateHarness.run_replicates` raises a bare `KeyError` for a model
  missing from `archetype_tags` (documented-by-test; an actionable message
  would be nicer). `cot_chain_lengths` is print-only by contract, like
  `summarize`.
