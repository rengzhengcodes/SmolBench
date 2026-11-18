# Attention capture inside vLLM's prefill -- the interface contract

Decided 2026-09-25. Supersedes the earlier HF-transformers replay
container, which is not shipped on this branch, for the induction
regeneration of Nemotron-3, Gemma-4 and gpt-oss WITH attention scores.

## Why capture inside vLLM

Generation runs the study's exact serving config with `return_token_ids`, so
every mark stores vLLM's exact prompt and completion token ids. Capture then
teacher-forces that exact sequence through the SAME checkpoint in the SAME
serving stack (same kernels, same precision -- MXFP4 gpt-oss stays MXFP4) as
one prefill (`max_tokens=1`), and a vLLM *general plugin* wrapping
`Attention.forward` computes the softmax rows of the answer token(s) from the
post-RoPE queries and keys the layer receives. Causal attention at a position
depends only on the prefix, so these rows are the attention of generation.

## The two serves of one checkpoint

1. **Generation serve**: unchanged study args (`--no-enable-prefix-caching`,
   `--max-num-seqs 1`, ...). Requests carry `return_token_ids: true`.
2. **Capture serve** (`ec2.serve_model(model, capture=True)`): the same
   spec plus
   `--enforce-eager --max-num-batched-tokens <max_model_len>` (a Python
   wrapper with tensor math and file IO cannot live inside vLLM's fullgraph
   compile, and one un-chunked prefill is what puts the whole sequence's
   queries and keys in one `Attention.forward`), and the container env
   `PYTHONPATH=/root/.cache/huggingface/attn_plugin`,
   `VLLM_PLUGINS=smolbench_attn`,
   `SMOLBENCH_ATTN_DIR=/root/.cache/huggingface/attn`.
   The agent's `/serve` payload gains optional `env: {NAME: value}` (each
   becomes `-e NAME=value`), and optional `files: {relpath: text}` written
   under `/opt/hf-cache/<relpath>` before `docker run` (the plugin package).
   `--kv-sharing-fast-prefill` must never be set (Gemma-4 shared layers
   would skip the query positions we need).

## Plugin package on the box (written by the client via `/serve files`)

```
/opt/hf-cache/attn_plugin/smolbench_attn/__init__.py          (ATTENTION_CAPTURE_PLUGIN_PY)
/opt/hf-cache/attn_plugin/smolbench_attn-0.1.dist-info/METADATA
/opt/hf-cache/attn_plugin/smolbench_attn-0.1.dist-info/entry_points.txt
    [vllm.general_plugins]
    smolbench_attn = smolbench_attn:register
```
`importlib.metadata` discovers the dist-info on `PYTHONPATH`; vLLM loads
general plugins in every process, including tensor-parallel workers.

## Job trigger: one file per job, one request at a time

The agent writes `<SMOLBENCH_ATTN_DIR>/current.json` atomically (tmp +
rename) BEFORE posting the request, then posts
`POST /v1/completions {"model": name, "prompt": <ids>, "max_tokens": 1,
"temperature": 0}` to the local vLLM (bearer `VLLM_API_KEY`), then waits for
`<SMOLBENCH_ATTN_DIR>/done/<job_id>.r<rank>.json` from every rank
(`tp` files), then moves to the next job. `--max-num-seqs 1` and
`--enforce-eager` (no CUDA-graph padding) make `query.shape[0] == n_tokens`
an identity check for "this forward is that job".

```json
{"job_id": "q3", "seq": 17, "n_tokens": 31877, "positions": [31870, 31871],
 "put_urls": ["<presigned PUT for rank 0 .npz>", "..."],
 "meta_put_urls": ["<presigned PUT for rank 0 .json>", "..."]}
```
`positions` index into prompt + completion ids. `seq` is a monotonically
increasing counter so a re-written file with the same job id is a new job.

## What each rank captures and uploads

Rank `r` (tensor-parallel shard `r` of `tp`) computes, for every `Attention`
layer it runs (and every `MLAAttention` layer, see the last section; Mamba
blocks never call in and are absent; the captured layer indices are
recorded), rows
`softmax(scale * q_p . k_j [+ softcap] )` over `j <= p`, with the layer's
sliding window (vLLM convention: keys `j >= p - (w - 1)`), grouped-query
head mapping, `logits_soft_cap` (tanh) when the impl has one, and, for
layers with attention sinks (gpt-oss), the per-head sink logit as one extra
softmax column whose mass is stored separately so the row over tokens is
exactly what the kernel used. For KV-shared layers (Gemma-4: `key is None`,
`kv_sharing_target_layer_name` set) the target layer's keys/values are used.

Self-consistency gate, per layer, every job: `rows @ V` at the captured
positions vs the kernel's own output rows from the same forward; max abs and
max relative difference are recorded in the meta and the job FAILS (no
upload, `ok: false`) above `SMOLBENCH_ATTN_GATE_TOL` (default 3e-2, bf16).
The tolerance is an env var of the capture serve on purpose: a systematic
small drift on one family (a kernel that accumulates differently) can be
assessed by loosening it deliberately and recording the measured
`gate_max_rel`, instead of failing every job silently-alike. It can be set per serve; the
client side caps the tolerance a capture may declare at 0.05 in the audit.

Upload (per rank, via the presigned URLs in the job file):
* `.npz`: `rows` float16 `[L, P, H_local, T]`, `sink` float16 `[L, P, H_local]`
  (all-zero where a layer has no sink), `layers` int32 `[L]` (model layer
  index), `positions` int32 `[P]`, `has_sink` bool `[L]`,
  `sliding_window` int32 `[L]` (0 = full), `kv_shared_from` int32 `[L]`
  (-1 = own KV).
* `.json` meta: `job_id, rank, tp, n_tokens, positions, layers, num_heads_local,
  num_kv_heads_local, head_size, capture_version (2; 3 for summary mode; absent = 1), attention ("mha" | "mla" | "mixed"; see
  the last section), dtype ("float16"), gate: {layer: {max_abs,
  max_rel}}, gate_tol, vllm_commit, model, bytes, wall_s`.
* then `<SMOLBENCH_ATTN_DIR>/done/<job_id>.r<rank>.json`:
  `{"ok": bool, "error": str|null, "gate_max_rel": float, "bytes": int,
  "uploaded": bool, "http_status": [npz_status, json_status]}`; each entry is
  an int or one of the strings `"412-landed-earlier"` and `"412-exists"` (the
  latter only in fill mode, see below).

Order: the `.npz` is PUT first, and the `.json` meta only when the npz PUT
succeeded (a 2xx, `"412-landed-earlier"` or, in fill mode, `"412-exists"`). When the npz PUT fails, no meta
PUT is attempted, the done file has `ok: false`, `uploaded: false` and
`http_status` holds the npz status alone (one entry). Reason: a meta without
its npz would be a permanently partial job in an append-only bucket.

Every PUT carries `If-None-Match: *`, signed into the presigned URL, so S3
answers 412 instead of replacing an existing key. A 412 on the first attempt
means the key already existed: a failure, not retried. A 412 on a retry,
after an attempt that raised or returned >= 500 (the object may have been
stored without a usable answer), is recorded as `"412-landed-earlier"` and
counts as uploaded; a 412 after only clear failures (e.g. 403) stays 412.
These rules hold unless fill mode is on.

### Fill mode: completing a partly stored job

Some jobs are stored only partly (for example 7 of 8 ranks hold both objects
and the 8th holds nothing, or one rank's npz landed and its meta did not). The
recapture goes under the SAME keys: the replay is a deterministic teacher-forced
prefill, so objects that already exist stay as they are and only the missing
ones are added. The capture serve is started with `SMOLBENCH_ATTN_FILL=1` for
such a run.

* The variable is read at each PUT. Only the exact string `1` enables fill mode;
  `0`, empty, `true` and unset keep the behaviour above.
* In fill mode a 412 on the FIRST attempt means an earlier run stored the
  object. It is not retried, is recorded as `"412-exists"` in `http_status`, and
  counts as stored. Existing objects are never replaced (the `If-None-Match: *`
  condition still applies to every PUT). Every other path is unchanged: a 412
  after an unclear attempt is still `"412-landed-earlier"`, and a 412 after a
  clear refusal (e.g. 403) is still 412.
* The meta of a rank whose npz answered `"412-exists"` carries
  `npz_put: "existing"`; a fresh npz upload adds no such key. `bytes` stays the
  size of the blob this run built, while the stored npz comes from an earlier
  run and its size may differ. A consumer skips only the npz size-equality check
  for such a rank; every other check, array content included, still applies.
* The meta PUT may also answer `"412-exists"`, which counts as stored.
* Why a serve env var and not a job field: the agent copies a fixed set of job
  keys into `current.json`, so a new job field would need an agent change.

### Serve-time variable `VLLM_EXECUTE_MODEL_TIMEOUT_SECONDS`

vLLM bounds one model step by this variable; its default of 300 s killed the
engine during a capture of about 300 s on a cell of about 87K tokens. The
client's capture serve sets it (default 3600, never below 300). The plugin logs
its value (or `unset`) and the fill mode in the final `registered (...)` line,
so the server log shows which bound the engine ran under.

S3 keys (beside the marks run, invisible to the marks-log parser):
`<exp>/<model>/seed=<seed>/attn/<info>--<run_ts>/q<idx>.r<rank>.npz` and
`.r<rank>.json`; one `index.json` per address once verified. Analysis
concatenates ranks along the head axis in rank order (`tp` from the index).

The key layout is chosen by the client that mints the presigned URLs; the
agent and plugin only PUT to the URLs they are given. The rebuttal replay
(`rebuttal/attention_replay.py`) files captures under
`bedrock-trio/attention/induction/<model>/seed=<s>/<arm>--<stamp>/q<idx>.r<rank>.{npz,json}`.

## Agent endpoint `/attn`

`POST /attn {"served_model_name": str, "tp": int, "jobs": [job, ...]}`
(a job = `job_id, prompt_token_ids, completion_token_ids, positions,
put_urls, meta_put_urls`) starts a background thread that runs the trigger
loop above; replies 202. `/status["attn"]` reports
`{"running": bool, "total": n, "done": n, "current": job_id|null,
  "results": {job_id: {"<rank>": done-json}}, "error": str|null}`.
The client polls `/status` (which also feeds the idle watchdog), verifies
every upload by HEAD + a sampled download whose `rows.shape[-1]` must equal
`n_tokens`, and writes the address `index.json`. The longest sequence of a
model is sent FIRST so an out-of-memory prefill fails before hours of work.

## Mode `mass` (added 2026-09-26): every response token's attention by key class

The analysis the user wants: for the noise arm, do the RESPONSE tokens put
less attention mass on the whitespace padding than the uniform-dispersion
prediction `|pad| / d` (d = the causal context length)? That needs, for
every completion query position, the row's mass summed over key CLASSES --
not the T x T matrix (a single 40k-token mark would be ~1.8 GB per
layer-head; infeasible at 22k marks). The job therefore carries a class
label per token and the plugin reduces each row on the box.

Job file additions (the agent copies them from the `/attn` job verbatim):

```json
{"mode": "mass", "query_start": 21883, "classes": [0, 0, ..., 1, 1, ..., 3, 3],
 "positions": [22000, 30000, 40010]}
```
* `classes`: uint8 per token of prompt + completion:
  `0` prompt token carrying information, `1` prompt whitespace PAD token
  (the appended `pad_unit * n` run of the noise arm: a whitespace-only
  token inside the prompt's longest whitespace run of >= 32 characters),
  `2` other prompt whitespace / template token (short structural
  whitespace, chat-template specials), `3` completion token (reasoning +
  response). The client derives them from the stored token ids with the
  served tokenizer's per-token decode; they are stored in the npz so the
  uniform baseline `n_c(p) / (p + 1)` (class counts over the causal prefix)
  is computable offline for every query.
* `query_start`: first completion index; queries are `query_start .. T-1`.
* `positions`: the GATE positions in mass mode (a few completion indices,
  always including `T-1`): full rows are computed there and checked by
  `rows @ V` against the kernel output exactly as in rows mode.

Per rank the plugin computes, in query chunks sized to keep the float32
logits under ~1 GB, `A = softmax(...)` for the chunk and reduces it with the
one-hot class matrix, storing:
* `mass` float16 `[L, P, H_local, 4]` -- attention mass per class (with
  sinks: over the token columns only, so the four classes plus `sink` sum
  to 1),
* `entropy` float16 `[L, P, H_local]` -- row entropy in nats over tokens
  (+ the sink column when present), the dispersion statistic itself,
* `sink` float16 `[L, P, H_local]` (zeros without sinks),
* `prompt_entropy` float16 `[L, P, H_local]` -- entropy in nats of the row's
  attention restricted to the prompt keys `[0, query_start)` and renormalized
  to 1 (computed as a softmax over those keys' logits; see the 2026-11-16
  note below),
* `classes` uint8 `[T]`, `query_start` int32, `positions` int32 (the gate
  positions), `layers`, `has_sink`, `sliding_window`, `kv_shared_from` as in
  rows mode. `P = T - query_start`.
Meta json gains `mode`, `query_start`, `n_classes`, and (both modes)
`capture_version`. Rows mode (`mode` absent
or `"rows"`) is unchanged. `verify` checks `mass.shape[1] == n_tokens -
query_start` and `mass.shape[-1] == 4`.

## Prompt entropy and `capture_version` (added 2026-11-16)

Mass mode also stores `prompt_entropy`, the statistic a paper defines as: for
each response token, renormalize the attention weights on the input prompt to
1 and take the Shannon entropy. Per row and head it is the entropy in nats of
the attention restricted to prompt keys `[0, query_start)` and renormalized to
1, computed as a softmax over those keys' logits (never by dividing stored
low-precision probabilities). The sink column is excluded: the sink is not a
prompt key. Masked keys contribute exactly 0.

On sliding-window layers it renormalizes over the in-window prompt keys only.
The window admits keys `j >= p - (w - 1)`, so completion row
`i = p - query_start` sees a prompt key iff `i < w - 1`. The value is NaN where
the row has no attendable prompt key: sliding-window rows with `i >= w - 1`,
and every row when `query_start == 0`. On such rows the stored prompt mass
(classes 0+1+2) is exactly 0.

The meta json carries `capture_version`: 2 for rows and mass captures (3 for
summary captures, see the next section); a meta without the field is version 1.
Version 2 added `prompt_entropy` (mass mode) and the field itself. Rows mode has
no `prompt_entropy`.

A new masking rule (a layer type that masks prompt keys other than causally or
by the sliding window) must encode its geometry in the npz: the audit derives
which rows must be NaN from `sliding_window` and `query_start` alone.

## Mode `summary` (added 2026-11-16): the mass statistics summed on the box

Mass mode stores `[L, P, H_local, ...]` arrays, so its size grows with P, the
number of completion rows. Deduction responses run to 10k-120k tokens, which
makes those arrays too large to store per mark. Summary mode keeps what an
analysis needs from them: sums over the rows, per layer and local head.

Job fields: the same as mass mode (`mode: "summary"`, `query_start`, `classes`,
`positions`); the agent forwards them unchanged, so no agent change is needed.
`classes` must have `n_tokens` entries and `0 <= query_start < n_tokens`, as in
mass mode; a job that violates this is ignored. The gate runs exactly as in
mass mode, at `positions`.

npz layout (stacked over layers in layer order; `P = n_tokens - query_start`):
* float64 `[L, H_local]`: `sum_entropy`, `sum_prompt_entropy`, `sum_sink`,
  `sum_pad_ratio`, `sum_m_hp`, `sum_chain_hi`, `sum_chain_lo`.
* float64 `[L, H_local, 4]`: `sum_mass`.
* int64 `[L, H_local]`: `n_prompt_entropy`, `n_pad_ratio`.
* `rows` int64, a 0-d scalar holding `P`; `capture_version` int32, a 0-d scalar
  holding 3.
* `classes` uint8 `[T]`, `query_start` int32, `positions` int32, `layers`,
  `has_sink`, `sliding_window`, `kv_shared_from` as in mass mode.
* It holds no `mass`, `entropy`, `prompt_entropy` or `sink` array.

Definitions. Row `i` (`i = 0 .. P-1`) is the query at absolute position
`p = query_start + i`. Let `m` = the row's mass of classes 0+1+2, `r` = its
class-3 mass, `s` = its sink mass (0 on a layer without a sink), `H` = the
whole-row entropy, `Hp` = the prompt entropy (as defined above; NaN where
undefined) and `plogp(x) = x ln x` with `plogp(0) = 0`, so that no row gives
`0 * -inf = NaN`. Let `G = -(plogp(m) + plogp(r) + plogp(s))`.
* `sum_entropy`: sum of `H` over all `P` rows.
* `sum_prompt_entropy`, `n_prompt_entropy`: sum and count of `Hp` over the rows
  where `Hp` is finite. A row where it is NaN adds exactly 0 to both.
* `sum_mass` `[H_local, 4]`: sum over rows of the per-class mass. `sum_sink`:
  sum over rows of the sink mass (all zeros without a sink).
* `sum_pad_ratio`, `n_pad_ratio`: the per-row quantity that `whitespace_ratio`
  averages. `baseline(p)` = (number of class-1 entries in `classes[:p+1]`) /
  `(p + 1)`. For rows with `baseline > 0` the ratio is the row's class-1 mass
  divided by `baseline`; the sum is over those rows and the count is their
  number (the same for every head).
* Over the rows where `Hp` is finite: `sum_m_hp` = sum of `m * Hp`;
  `sum_chain_hi` = sum of `H - G`; `sum_chain_lo` = sum of
  `H - G - r * ln(i + 1)`. An offline audit can check the grouping rule
  `sum_chain_lo <= sum_m_hp <= sum_chain_hi` from these three sums without the
  rows.
* Every chunk of rows contributes; none is skipped.

Precision: the sums are float64 and are accumulated from the float32 chunk
values (cast to float64, never through float16), so they carry no float16
rounding. Counts are exact int64 integers, so an audit can compare them with
the window geometry: `n_prompt_entropy` is `P` on a global layer with
`query_start > 0`, `min(P, w - 1)` on a layer with window `w`, and 0 when
`query_start == 0`.

One reduction: summary and mass mode both consume the same row reduction in the
plugin (`_row_chunks`). A summary is the sum of the rows that mass mode would
have stored, taken before mass mode's float16 rounding.

Meta json: as for mass mode except `mode: "summary"`, `capture_version: 3`,
`dtype: "float64"` and `rows_shape: [L, P, H_local, 4]`. `rows_shape` is the
shape of the per-row statistics that were summed (what mass mode would have
stored), not the shape of any stored array; it keeps the shape check of the
offline audit reading the same field. `n_classes` is 4 and `query_start` is the
job's.

`capture_version` by kind:

| `capture_version` | Kind |
|---|---|
| 1 (field absent) | mass without `prompt_entropy` |
| 2 | mass with `prompt_entropy` (and rows mode) |
| 3 | summary |

## Multi-head latent attention (DeepSeek-V3.1)

The plugin also wraps `MLAAttention.forward(q, kv_c_normed, k_pe,
output_shape=None, q_dcp_replicated=None)` from
`vllm.model_executor.layers.attention.mla_attention`, in addition to
`Attention.forward`. The import is defensive: a vLLM without the module
captures `Attention` layers only. Both wrappers share one class tuple, so a
job finalizes only after every layer of either class has been captured. Job
protocol, upload, gate and done file are as above.

Tensors a rank sees per layer (`T` tokens, `H` local heads, `P` = nope dim,
`R` = rope dim, `V` = value dim, `L` = latent rank):
* `q [T, H, P+R]`, post-RoPE;
* `kv_c_normed [T, L]`;
* `k_pe [T, 1, R]`, shared by all heads, post-RoPE;
* output `[T, H*V]`, before `o_proj`.

For DeepSeek-V3.1: `P=128`, `R=64`, `V=128`, `L=512`, 128 heads, `tp=8` so
`H=16` per rank, 61 attention layers.

### Keys and values

Rebuilt from the layer's own `kv_b_proj(kv_c_normed)[0].view(T, H, P+V)`,
split into `k_nope | v`; the key is `[k_nope | k_pe broadcast over heads]`.
This is vLLM's prefill path (`forward_mha`, `mla_attention.py:2851-2855` at
vLLM commit `8efa13b7`), not the decode path's absorbed `W_UK_T`/`W_UV`. Why:
it is the same FP8 block GEMM the kernel's keys came from.

### Logits

`logit(p, j) = scale * (q_nope[p,h] . k_nope[j,h] + q_pe[p,h] . k_pe[j])` for
`j <= p`, `-inf` otherwise. No soft cap, window, sinks or ALiBi. `scale` is
read from `layer.impl.scale` (which must equal `layer.scale`), never
recomputed. For DeepSeek-V3.1 the design derivation is
`192**-0.5 * mscale**2` with YaRN `mscale = 0.1*ln(40) + 1`, about 0.1352
(derived, not measured).

The gate is unchanged: `rows @ rebuilt v` against the layer's output at the
gate positions. `prompt_entropy` and the mass statistics are produced for MLA
layers by the same code as for `Attention` layers.

### Head order across ranks

Local head `j` of rank `r` is global head `r * num_heads_local + j` (`16r + j`
for `tp=8`). Concatenate the ranks' arrays in rank order along the head axis,
as for `Attention`.

### Guards

Each guard fails the job: `ok: false`, nothing uploaded, error
`MLA guard <name> failed at <layer>: <detail>` in the done file. None skips
silently. Guards run only on the job's forward (never on a warm-up or
other-length forward), in this order, first failure wins:

| guard | fails when | why it exists |
|---|---|---|
| `prefill-only` | no attention metadata for the layer, `num_decode_tokens != 0`, or no prefill part | a sequence that vLLM classifies as decode is served from latents, not from the keys rebuilt here; such a job fails loudly instead of being captured from the wrong path. vLLM's FLASH_ATTN_MLA builder classifies sequences of up to `reorder_batch_threshold = 512` tokens as decode, so `register()` sets that class attribute to 1 (the value of vLLM's other MLA builders) before any builder exists; short sequences then take the prefill path |
| `chunked-context` | `prefill.chunked_context` is not None | the prefill reads context in chunks, not the one pass reconstructed here |
| `fp8-prefill` | `layer.kv_cache_dtype != "auto"`, or `prefill.q_data_type` differs from `q.dtype` | an FP8 prefill uses quantized queries/keys the rebuild would not reproduce |
| `dcp` | `layer.dcp_q_replicate` set, or `impl.dcp_world_size != 1` | decode context parallelism changes what a rank holds |
| `pcp` | `layer.use_pcp` set | prefill context parallelism changes what a rank holds |
| `sparse` | `layer.use_sparse` set | sparse attention does not attend to all causal keys |
| `sliding-window` | `layer.sliding_window` is not None | the logit formula has no window |
| `output-dtype` | output dtype is not `torch.bfloat16` | the gate compares against a bf16 output; a quantized output would make it meaningless |
| `scale` | `impl.scale` not a finite positive number, or `layer.scale` differs from it by more than relative 1e-6 | the scale must be the one the kernel used |
| `shape` | `q`, `kv_c_normed`, `k_pe` or the output do not have the shapes listed above | the rebuild assumes them |

### Meta

* `attention`: `"mha"`, `"mla"` or `"mixed"`; present for every job, plain
  `Attention` jobs included.
* Only when an MLA layer was captured: `qk_head_dim`, `v_head_dim`,
  `kv_lora_rank`, `head_order` (the head-order rule above, as text).
* For MLA, `num_kv_heads_local == num_heads_local` and `head_size == P+R`
  (192), not the layer's latent-cache attributes (`num_kv_heads = 1`,
  `head_size = 576`).
* In a `"mixed"` job the head counts and `head_size` describe the last
  captured layer (the plugin reads them from that layer's view).
* `capture_version` is not changed by MLA: the new fields are additive (2 for rows and mass, 3 for summary).

### Limits

The design's optional `n_layers` job field (to fail fast when a never-called
MLA layer, e.g. a multi-token-prediction drafter, sits in the forward
context) is NOT implemented, because it needs an agent change. Such a layer
keeps the job from ever finalizing: no rank uploads and the job fails only
when the agent's per-job wait expires, on a billed box. (The replay audit's
layer-count check covers the different case of a capture that finalized with
fewer layers than the model has.)

### Not verified live

* The MLA path has only run against a CPU stub of vLLM; nothing has run on
  the pinned vLLM image.
* DeepSeek-V3.1 failed at engine start on that image on 2026-09-19 with a
  tokenizer error (cause undiagnosed).
* That FA3 prefill against the float32 recompute stays within the 3e-2 gate.
* That repeated `kv_b_proj` calls are bit-identical.
* That `prefill.q_data_type` equals the bf16 query dtype in the default
  config.
* That the pinned image's vLLM matches the source clone (only the version
  string was matched).
