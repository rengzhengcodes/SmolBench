# Architecture facts for the family-ladder roster

Records what each of the study's 21 checkpoints actually is: how every layer
mixes tokens, how every layer encodes position, where the feed-forward goes
sparse — read from each checkpoint's own `config.json`.

The study's own record (`smolbench/evals/providers/ec2.py`, `scripts/fleet/run_fleet.py`,
`notebooks/induction/run_study.py`) captures how each checkpoint was *served* —
tensor parallelism, context window, reasoning wiring — but nothing about what
each one *is*. This closes that gap so the results can be read mechanistically.

## Contents

```
fetch_arch_facts.py      HF config.json + generation_config.json for all 21 repos
                         -> arch_configs_raw.json   (verbatim, the audit trail)
                         -> arch_facts.json         (normalised + provenance)

kv_budget.py             KV-cache sizing for the roster, over
                         arch_configs_raw.json
```

`arch_configs_raw.json` is tracked: it is the audit trail `kv_budget.py` and
`tests/tooling/test_kv_budget.py` read, and the archived config record
`smolbench/evals/providers/ec2.py` cites. `arch_facts.json` is not tracked; regenerate it
with `fetch_arch_facts.py` (needs network).

## Where each claim comes from

**Structural numbers** — layer counts, head counts and dimensions, RoPE bases
and scaling parameters, expert counts, window sizes, SSM state sizes, vocab
sizes — are read from each checkpoint's own `config.json`, fetched from the
exact repo the fleet served, and stamped with that repo's resolved commit SHA.
Nothing structural is transcribed by hand.

**Prose** — what a mechanism is called, how many parameters a checkpoint
has, and which config fields the reference implementation actually reads —
cannot come from a config file. That is the table below; each row's
sources column is where those names come from.

Where the two layers disagree, the config wins, and the divergence column
says which fields an implementation ignores (Nemotron-3, for one, declares
RoPE fields nothing reads).

## Family facts

One row per family. Only claims read from `config.json` or confirmed
against the cited source; nothing inferred. Divergences are config fields
the served implementation does not read, or reads differently than the
field suggests.

| Family | Rungs (spec keys, params) | Token mixing | Positional encoding | FFN / sparsity | Reasoning toggle (as served) | Config-vs-implementation divergences | Primary sources |
|---|---|---|---|---|---|---|---|
| **DeepSeek** | `deepseek-v3.1` 671B/37B; `deepseek-v4-flash` 284B/13B; `deepseek-v4-pro` 1.6T/49B | V3.1 MLA (512-d latent KV + 64-d decoupled RoPE key, 128 Q heads). V4 shared-KV MQA (one 512-d row, K=V), CSA 4:1 / HCA 128:1 alternation, unconditional 128-token window every layer, Lightning Indexer top-512/1024, attention sinks | V3.1 partial RoPE on 64 of 192 Q/K dims, θ=1e4 + YaRN ×40 (4096→163840). V4 same 64-dim slice, YaRN ×16 (65536→1048576), second base `compress_rope_theta` 1.6e5 on the compressed stream, inverse RoPE on output | V3.1: 3 dense SwiGLU + 58 MoE, 256 experts top-8 +1 shared, sigmoid, `noaux_tc`. V4: all-MoE, 3 hash-routed layers, 256/384 experts top-6, √softplus scoring, clamped SwiGLU 10.0, FP4 routed experts. Residual stream: mHC, 4 lanes, Sinkhorn-20, two sites per layer | V3.1 Jinja template with a `thinking` kwarg. V4 ships none: `<think>`/`</think>` prefill toggle in `encoding_dsv4.py`, three `reasoning_effort` modes, `--reasoning-parser deepseek_v4` | `compress_rope_theta` in config and both implementations, absent from the paper; attention sinks, per-head Q/KV RMSNorms and inverse RoPE have no config field; V3.1 `num_key_value_heads: 128` vestigial under MLA; vLLM and the reference disagree on MTP `compress_ratios` polarity. Neither V4 rung produced results; crash cause undiagnosed | arXiv:2412.19437 · arXiv:2606.19348 · https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash |
| **EXAONE** | `exaone-4.0-32b` 32.00B dense; `k-exaone-236b-a23b` 237.1B / ≈22.7B active; `exaone-4.5-33b` 34.35B (incl. MTP + 1.29B ViT) | GQA with per-head QK-RMSNorm, head_dim 128, no bias; 3:1 `LLLG` local/global tiling. 40Q/8KV (4.0, 4.5), 64Q/8KV (K-EXAONE); windows 4096 / 128 / 4096 | RoPE on sliding layers only; global layers NoPE. θ=1e6 throughout; llama3 scaling ×16 over 8192 on 4.0 and 4.5, `rope_type: default` on K-EXAONE | Dense SwiGLU 27392 (4.0, 4.5). K-EXAONE: layer 0 dense 18432 + 47 MoE, 128 experts top-8 +1 shared, sigmoid + `e_score_correction_bias`, `norm_topk_prob`, scale 2.5. Post-norm (QK-Reorder-Norm) on 4.0/4.5, pre-norm on K-EXAONE | `<think>`/`</think>` special tokens; template default off on 4.0 (study forces `enable_thinking: true`), on for the other two; split client-side, no EXAONE-named vLLM parser | `mtp_share_layers`, `mtp_loss_scaling_factor`, `is_moe_layer`, `scoring_func` read by neither implementation; `sliding_windows` read by vLLM only; `n_group`/`topk_group`=1 degenerate; 4.5's `presence_penalty 1.5` ignored under vLLM; MTP weights present but unloaded | arXiv:2507.11407 · arXiv:2601.01739 · arXiv:2604.08644 |
| **Gemma 4** | `gemma-4-e2b` 2.3B effective / 5.12B raw; `gemma-4-12b` 11.96B; `gemma-4-31b` 30.7B card / 31.27B safetensors | Two distinct attention blocks per model: sliding head_dim 256, global head_dim 512 with fewer KV heads. E2B MQA 8Q/1KV plus cross-layer KV sharing (layers 15–34 hold no KV); 12B/31B `attention_k_eq_v` → values = keys, no `v_proj`. QK-norm, unscaled V-norm, `scaling = 1.0` | Two regimes keyed by layer type: global p-RoPE θ=1e6, `partial_rotary_factor` 0.25 → 128 of 512 dims rotated, 384 NoPE; sliding `rope_type: default` θ=1e4, all 256 dims rotated. Windows 512 / 1024 / 1024 | Dense GeGLU (`gelu_pytorch_tanh`), 4.0× hidden; `enable_moe_block: false`. E2B `use_double_wide_mlp` on KV-shared layers 15–34. Gemma double-norm: pre + post around both sublayers, 4 norms/layer, 5 on E2B; `final_logit_softcapping 30.0` | `--reasoning-parser gemma4`, delimiters `<\|channel>` / `<channel\|>`, turn end `<turn\|>`; stop ids `[1, 106, 50]` | The 37.5% global-KV saving is unrealised — transformers writes both K and V, vLLM reconstructs `v_proj` at load; the global KV-head override is gated on `attention_k_eq_v`, so E2B's `num_global_key_value_heads` is inert; MoE code path present but unused | arXiv:2607.02770 · arXiv:2410.06205 · https://ai.google.dev/gemma/docs/core/model_card_4 |
| **GLM** | `glm-4.5-air` 106B/12B; `glm-4.7` 355B/32B; `glm-4.7-flash` 30B/≈3B | Air, 4.7: GQA 96Q/8KV head_dim 128, q/k/v bias, `o_proj` bias-free; QK-norm off (Air) / on (4.7). Flash: MLA (DeepSeek-V2/V3 lineage), first GLM checkpoint to use it — 20 heads, q_lora 768, kv_lora 512, nope192‖rope64, v256, latent RMSNorms, no bias | Air, 4.7: partial RoPE 0.5 — 64 of 128 dims rotated, θ=1e6, no scaling, `rotate_half`. Flash: decoupled rotary sub-head, `qk_rope_head_dim` 64 of 256, `rope_interleave: true`, θ=1e6 | Dense prefix then uniform MoE, SwiGLU: 1+45 / 3+89 / 1+46 layers; 128 top-8 / 160 top-8 / 64 top-4 experts, +1 shared each; sigmoid + `e_score_correction_bias`, `norm_topk_prob`; `routed_scaling_factor` 1.0 / 2.5 / 1.8 | `--reasoning-parser glm45` (Air), `glm47` (4.7, Flash); no `--speculative-config`, so the MTP head was unused | `topk_method: "noaux_tc"` read by nothing; Flash's `first_k_dense_replace` superseded by `mlp_layer_types`; Flash's `partial_rotary_factor: 1.0` frozen; transformers drops MTP weights via depth-hardcoded regexes; HF's `attention_bias` doc wrong (`o_proj` bias-free). arXiv:2508.06471 describes GQA and cannot source Flash's MLA | arXiv:2508.06471 · https://huggingface.co/docs/transformers/model_doc/glm4_moe_lite · https://github.com/ggml-org/llama.cpp/pull/18936 |
| **Ministral-3** | `ministral-3-3b` 3.43B LM; `ministral-3-8b` 8.49B; `ministral-3-14b` 13.51B (each + 0.4B Pixtral tower, not loaded) | Identical on all three: GQA 32Q/8KV, head_dim 128, `sliding_window: null` → global causal attention every layer, no QK-norm, no bias, scale `head_dim**-0.5` | Uniform: `rope_theta` 1e6 / 1e6 / 1e9, YaRN `factor 16` (16384 → 262144), `beta_fast 32` / `beta_slow 1`, `mscale`/`mscale_all_dim` 1.0, plus a `llama_4_scaling_beta: 0.1` query-temperature term | Dense SwiGLU, no MoE fields: `intermediate_size` 9216 / 14336 / 16384. RMSNorm pre-norm, eps 1e-5. Embeddings tied on the 3B only | `[THINK]`/`[/THINK]` single tokens (ids 34/35); protocol lives only in the Reasoning template's `default_system_message`, no `enable_thinking` kwarg, so any caller system message disables it — the study injects the default text; `--reasoning-parser mistral` | transformers reads `rope_parameters.llama_4_scaling_beta`; vLLM expects a top-level `llama_4_scaling` dict absent from the shipped config. `mscale`/`mscale_all_dim` are dropped by vLLM's plain-`yarn` filter, which computes `mscale = 1.2773`. Both stated against vLLM main, not the served digest | https://github.com/huggingface/transformers/tree/main/src/transformers/models/ministral3 · https://huggingface.co/docs/transformers/main/en/model_doc/llama4 · https://mistral.ai/news/mistral-3/ |
| **Nemotron-3** | `nemotron-3-nano-4b` 3.97B dense; `nemotron-3-nano-30b-a3b` 31.6B/3.2B; `nemotron-3-super-120b-a12b` 120B/12B | `NemotronHForCausalLM` hybrid, one mixer per layer: Mamba-2 ×21/23/40 (N=128, 8 groups, conv k=4) and GQA ×4/6/8 (40Q/8KV then 32Q/2KV, head_dim 128, no QK-norm, no bias). Every attention layer is immediately preceded by a Mamba-2 layer | NoPE on all three rungs — no rotary embedding anywhere. Position comes from the Mamba-2 recurrence and the depthwise causal conv (k=4) | Ungated squared ReLU (`relu2`), never SwiGLU. 4B: 17 dense MLPs at 4× hidden. 30B/120B: all-sparse — 128 top-6 / 512 top-22 experts +1 double-width shared; fp32 sigmoid router + `e_score_correction_bias`, `norm_topk_prob`; 120B LatentMoE routes experts in 1024-d | none served: `--enable-prefix-caching` only, no reasoning parser or thinking protocol; `query()` splits the plain-text `<think>` block client-side | `rope_theta: 10000` and `partial_rotary_factor: 1.0` (30B, 120B) unread by both implementations; `expand: 2` never computes `d_inner` and is numerically wrong on 2 of 3 rungs; `time_step_rank` (4B) inert; `n_group`/`topk_group`=1 degenerate; cards' "1M" vs `max_position_embeddings: 262144` | arXiv:2512.20848 · arXiv:2604.12374 · arXiv:2512.20856 |
| **Qwen3.5** | `qwen3.5-27b` 27B dense; `qwen3.5-122b-a10b` 122B/10B; `qwen3.5-397b-a17b` 397B/17B (FP8 repo) | 3:1 tile `3×(Gated DeltaNet → FFN) + 1×(gated GQA → FFN)`, `full_attention_interval 4`. GDN: 16 QK heads broadcast to 48/64 V heads, 128×128 state, conv k=4. Attention head_dim 256, 24Q/4KV then 32Q/2KV, QK-norm before RoPE, sigmoid output gate from a double-width `q_proj` | RoPE only on the 25% `full_attention` layers, and only on 64 of 256 head dims there (`partial_rotary_factor` 0.25, θ=1e7, no scaling); the other 192 dims are NoPE. GDN layers carry position via conv and recurrence; M-RoPE degenerates to 1-D for text | 27B dense SwiGLU 17408. 122B/397B: every layer MoE — 256 top-8 / 512 top-10 experts (hidden 1024) +1 sigmoid-gated shared expert; bias-free softmax router, renormalised top-k. Zero-centred RMSNorm, pre-norm only | `enable_thinking` in `chat_template_kwargs`, default on; `--reasoning-parser qwen3` with `--language-model-only`; no `--speculative-config`, so the MTP head was unused | `attn_output_gate` unread by transformers but read by vLLM; `mlp_only_layers` and `deepstack_visual_indexes` deleted by the config classes; transformers discards MTP weights; `norm_topk_prob` / `scoring_func` absent, behaviour hardcoded. No technical report exists; the 3:1 ratio, partial-rotary claim, shared-expert gate, MTP and router scheme are unpublished | arXiv:2412.06464 · arXiv:2505.06708 · arXiv:2510.23095 |

## Checks

```bash
.venv/bin/python scripts/arch/fetch_arch_facts.py --check   # configs vs the fleet's fixture
.venv/bin/python -m pytest tests/tooling/test_kv_budget.py  # KV formulas vs the audit table
```

`--check` compares the fetched configs against
`tests/fixtures/roster_configs.json`, the fixture `tests/evals/test_deploy_specs.py`
pins against, on the four fields both hold; a mismatch means an upstream
checkpoint moved under the study.

## Not here: an HTML atlas page

There is no page builder in this directory and none should be added -- the
page was a presentation artifact, not study tooling. Its two built outputs
(`page_data.json`, `model_architectures.html`) survive only in the release
archives; see `notebooks/ARCHIVE.md`.
