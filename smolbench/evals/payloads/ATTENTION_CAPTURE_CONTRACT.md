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
layer it runs (Mamba blocks never call in and are absent; the captured
layer indices are recorded), rows
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
`gate_max_rel`, instead of failing every job silently-alike.

Upload (per rank, via the presigned URLs in the job file):
* `.npz`: `rows` float16 `[L, P, H_local, T]`, `sink` float16 `[L, P, H_local]`
  (all-zero where a layer has no sink), `layers` int32 `[L]` (model layer
  index), `positions` int32 `[P]`, `has_sink` bool `[L]`,
  `sliding_window` int32 `[L]` (0 = full), `kv_shared_from` int32 `[L]`
  (-1 = own KV).
* `.json` meta: `job_id, rank, tp, n_tokens, positions, layers, num_heads_local,
  num_kv_heads_local, head_size, capture_version (2; absent = 1), dtype ("float16"), gate: {layer: {max_abs,
  max_rel}}, gate_tol, vllm_commit, model, bytes, wall_s`.
* then `<SMOLBENCH_ATTN_DIR>/done/<job_id>.r<rank>.json`:
  `{"ok": bool, "error": str|null, "gate_max_rel": float, "bytes": int,
  "uploaded": bool, "http_status": [npz_status, json_status]}`; each entry is
  an int or the string `"412-landed-earlier"`.

Order: the `.npz` is PUT first, and the `.json` meta only when the npz PUT
succeeded (a 2xx or `"412-landed-earlier"`). When the npz PUT fails, no meta
PUT is attempted, the done file has `ok: false`, `uploaded: false` and
`http_status` holds the npz status alone (one entry). Reason: a meta without
its npz would be a permanently partial job in an append-only bucket.

Every PUT carries `If-None-Match: *`, signed into the presigned URL, so S3
answers 412 instead of replacing an existing key. A 412 on the first attempt
means the key already existed: a failure, not retried. A 412 on a retry,
after an attempt that raised or returned >= 500 (the object may have been
stored without a usable answer), is recorded as `"412-landed-earlier"` and
counts as uploaded; a 412 after only clear failures (e.g. 403) stays 412.

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

The meta json carries `capture_version`: 2 now; a meta without the field is
version 1. Version 2 added `prompt_entropy` (mass mode) and the field itself.
Rows mode has no `prompt_entropy`.

A new masking rule (a layer type that masks prompt keys other than causally or
by the sliding window) must encode its geometry in the npz: the audit derives
which rows must be NaN from `sliding_window` and `query_start` alone.
