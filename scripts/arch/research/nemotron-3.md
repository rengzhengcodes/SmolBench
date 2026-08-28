# Nemotron-3 (NVIDIA) — architecture brief for the SmolBench family ladder

Ground truth: `scripts/arch/arch_facts.json` and `scripts/arch/arch_configs_raw.json`, fetched 2026-08-12 at the pinned commit SHAs below. Every claim is tagged **VERIFIED** (a config field I read, or a source line I actually read), **INFERRED** (my derivation from verified facts), or **UNVERIFIED**.

**Reference implementation used.** vLLM 0.27.1 source tree, files
`vllm/transformers_utils/configs/nemotron_h.py` and `vllm/model_executor/models/nemotron_h.py` / `nemotron_h_mtp.py`. Caveat: `scripts/fleet/run_fleet.py:151` sets `NIGHTLY_IMAGE = "vllm/vllm-openai:nightly"` for every lane except the two DeepSeek-V4 lanes, so the served engine was a 2026 nightly, not 0.27.1 exactly. The 0.27.1 tree is a close proxy, and the HF in-repo `modeling_nemotron_h.py` was cross-checked on the points that matter. **UNVERIFIED**: byte-level equivalence between 0.27.1 and the nightly that ran.

---

## Bottom line

All three rungs are `NemotronHForCausalLM`: a **NoPE hybrid Mamba-2 / attention stack** in which each config character is one whole layer carrying exactly one mixer — not a Transformer block. **There is no rotary embedding anywhere in this family, on any rung.** The `rope_theta: 10000` and `partial_rotary_factor: 1.0` fields in the two MoE configs are inert export residue, contradicted by NVIDIA's own reports and by both reference implementations. Position is carried entirely by the Mamba-2 recurrence and the depthwise causal conv; attention layers see only a causal mask. The 4B is a dense, differently-descended outlier — pruned and distilled from **Nemotron Nano 9B v2** (the previous generation), not a Nemotron-3 pretrain — which is why the ladder's hidden size is non-monotonic (3136 → 2688 → 4096).

---

## 1. The `hybrid_override_pattern` alphabet — confirmed, exactly as you guessed

**VERIFIED.** `vllm/transformers_utils/configs/nemotron_h.py` states it twice — once in the docstring, once as a runtime assertion:

```
hybrid_override_pattern (`str`, ...):
    The pattern of the hybrid model. The pattern is a string of
    characters where each character represents
    M: Mamba2, *: Attention, -: MLP
...
assert len(self.hybrid_override_pattern) == self.num_hidden_layers
assert re.match(r"^[*-ME]+$", self.hybrid_override_pattern)
```

and the `layers_block_type` property maps `M → "mamba"`, `* → "attention"`, `- → "mlp"`, else `"moe"`. The dispatch table in `vllm/model_executor/models/nemotron_h.py` closes the loop:

```python
ALL_DECODER_LAYER_TYPES = {
    "M": NemotronHMambaDecoderLayer,
    "-": NemotronHMLPDecoderLayer,
    "*": NemotronHAttentionDecoderLayer,
    "E": NemotronHMoEDecoderLayer,
}
```

So: **`M` = Mamba-2 mixer, `*` = self-attention, `-` = dense MLP, `E` = MoE MLP.** Your reading is correct; no correction needed. The HF in-repo `modeling_nemotron_h.py` agrees (`NemotronHBlock.__init__` switches on `config.layers_block_type[layer_idx]` into `NemotronHMamba2Mixer` / attention / `NemotronHMLP` / `NemotronHMOE`) — **VERIFIED** by reading the file.

**The single most important structural consequence for the block diagram** (**VERIFIED** from the four decoder-layer classes): a Nemotron-H "layer" is `residual + mixer(RMSNorm(x))` with **exactly one** mixer. There is no attention-then-FFN pairing inside a layer. A drawn block must be one box per character, not the usual two-sublayer Transformer block.

---

## 2. Positional encoding — NoPE on all three rungs

**VERIFIED, four independent ways.**

**(a) vLLM.** `nemotron_h.py` imports no rope helper (`get_rope` appears nowhere in the file). `NemotronHAttention.forward` is:

```python
def forward(self, hidden_states: torch.Tensor, **kwargs) -> torch.Tensor:
    qkv, _ = self.qkv_proj(hidden_states)
    q, k, v = qkv.split([self.q_size, self.kv_size, self.kv_size], dim=-1)
    attn_output = self.attn(q, k, v)
```

`NemotronHAttentionDecoderLayer.forward` *accepts* `positions` — because `NemotronHModel.forward` passes it uniformly to every layer — and then **discards it**, calling `self.mixer(hidden_states=hidden_states)`. The threading is vestigial plumbing.

**(b) HF in-repo implementation.** The attention class takes `position_ids` and `cache_position` in its signature and applies no rotation: `query_states = self.q_proj(hidden_states)` / `key_states = self.k_proj(hidden_states)` go straight into `scaled_dot_product_attention`. It reads neither `config.rope_theta` nor `config.partial_rotary_factor`. **VERIFIED** by reading `modeling_nemotron_h.py` from the 30B repo.

**(c) NVIDIA's reports, per generation.**
- Nemotron-H (arXiv 2504.03624, §2.1): *"We do not use any position embeddings... We also use RMSNorm for normalization, separate embedding and output layer weights, and no dropout. We do not use bias weights for linear layers."*
- Nemotron Nano 2 (arXiv 2508.14444, §2.1): *"we do not use any position embeddings and use RMSNorm"*.
- **Nemotron 3 Nano** (arXiv 2512.20848): *"We do not use any positional embeddings, dropout, or bias on linear layers."* → covers the 30B directly.
- **Nemotron 3 Super** (arXiv 2604.12374): *"Consistent with prior Nemotron models, we omit positional embeddings, dropout, and bias terms in linear layers, use RMSNorm for normalization, and maintain un-tied embedding and output weights."* → covers the 120B directly.
- Nemotron 3 white paper (arXiv 2512.20856), the clearest statement of intent: *"Since Mamba layers provide implicit positional information, Nemotron 3 models do not use RoPE in attention layers and therefore do not suffer from out-of-distribution RoPE issues during context extension."*

**(d) The 4B config simply has no rope fields at all** — consistent by omission.

### Where position actually comes from

**VERIFIED** (mechanism from the code; the attribution sentence is NVIDIA's, quoted above):
- The **depthwise causal conv1d, kernel 4**, inside every Mamba-2 block gives a strict local order over a 4-token window.
- The **Mamba-2 SSD recurrence** is a causal scan with input-dependent decay `A`, so hidden state at step *t* depends on order.
- Attention layers get **only the causal mask** — no absolute, relative, or rotary signal. An attention layer's own view of two tokens is order-blind except for what the preceding Mamba/conv layers wrote into the residual stream. Since attention is always inserted immediately *after* a Mamba layer in all three patterns (see §6), it never runs on a positionally-naked residual stream.

### ⚠️ CONTRADICTION #1 — the config declares RoPE that nothing implements

| rung | `rope_theta` | `partial_rotary_factor` |
|---|---|---|
| 4B | absent | absent |
| 30B-A3B | `10000` | `1.0` |
| 120B-A12B | `10000` | `1.0` |

`NemotronHConfig.__init__` has **no `rope_theta` or `partial_rotary_factor` parameter**. Both land in `**kwargs` → `PretrainedConfig`, are stored, and are read by nothing in the model path. **Answer to your targeted question: NoPE on every rung — the fields are inert.** They are almost certainly Megatron→HF export residue. **INFERRED**: the export origin. **VERIFIED**: that they are unread.

Treat this as a cautionary case for the atlas: a `rope_theta` in a config.json is not evidence of RoPE.

---

## 3. Mamba-2 block — layout and what every knob controls

**VERIFIED** from `NemotronHMambaDecoderLayer` → `MambaMixer2` (`vllm/model_executor/layers/mamba/mamba_mixer2.py`).

Signal path for one `M` layer, hidden width *h*:

```
x  ──RMSNorm──►  in_proj  ──►  [ z | xBC | dt ]
                                 │    │     │
                                 │    ├─ depthwise causal conv1d(k=4, bias) ─► SiLU
                                 │    │
                                 │    └─ split into  x (d_inner) │ B (n_groups·N) │ C (n_groups·N)
                                 │
                                 └─ gate z ──────────────┐
   dt ─► softplus(dt + dt_bias), clamped [1e-3, 0.1]     │
   A (per-head, from A_log), D (per-head skip)           │
              ▼                                          ▼
        chunked SSD scan  ────────────────►  gated group-RMSNorm(eps 1e-5)
                                                         │
                                                    out_proj ──► + residual
```

Knob by knob (**VERIFIED**):

| field | what it controls |
|---|---|
| `mamba_num_heads` (96 / 64 / 128) | number of independent SSM heads; each has its own scalar `A`, `D`, `dt_bias`. Also sets the `dt` slice width of `in_proj`. |
| `mamba_head_dim` (80 / 64 / 64) | channels per SSM head. `d_inner = mamba_num_heads × mamba_head_dim`. |
| `ssm_state_size: 128` | *N*, the latent state width per channel. Recurrent memory is `num_heads × head_dim × N` scalars — **the entire long-range memory of the layer**, and it does not grow with sequence length. |
| `n_groups: 8` | how many heads share a `B`/`C` projection (Mamba-2's multi-value-attention analogue). Adds `2 × n_groups × N = 2048` channels to the conv path. |
| `conv_kernel: 4` | depthwise causal conv width applied to `x‖B‖C` before the scan. `use_conv_bias: true`. |
| `chunk_size` (256 / 128 / 128) | SSD block size — a **kernel/throughput** knob for the chunked-scan algorithm, mathematically neutral. |
| `mamba_hidden_act: "silu"` | activation after the conv, and on the gate branch. |
| `time_step_min/max/floor` | `dt` clamp `[1e-3, 0.1]` and init floor `1e-4`; controls the effective decay-rate range. |
| `mamba_proj_bias: false`, `use_bias: false` | no bias on `in_proj`/`out_proj` (conv keeps its bias). |
| `expand: 2` | **INERT — see below.** |

### ⚠️ FLAG — `expand: 2` does not compute `d_inner`

**VERIFIED.** Both the layer constructor and the state-shape calculator use `mamba_num_heads × mamba_head_dim`:

```python
self.mixer = MambaMixer2(..., intermediate_size=config.mamba_num_heads * config.mamba_head_dim, ...)
...
intermediate_size = hf_config.mamba_num_heads * hf_config.mamba_head_dim   # get_mamba_state_shape_from_config
```

The stored `expand` is never read. For the 4B, `2 × 3136 = 6272 ≠ 7680`; for the 30B, `2 × 2688 = 5376 ≠ 4096`. So `expand: 2` is not merely unused, it is **numerically wrong** on two of three rungs. Only the 120B coincides (`2 × 4096 = 8192`). Do not draw `expand` in the diagram.

### Derived Mamba geometry (**INFERRED** — arithmetic from verified fields)

| | 4B | 30B-A3B | 120B-A12B |
|---|---|---|---|
| hidden *h* | 3136 | 2688 | 4096 |
| `d_inner` | **7680** | **4096** | **8192** |
| `n_groups·N` (each of B, C) | 1024 | 1024 | 1024 |
| `conv_dim` = `d_inner + 2·1024` | 9728 | 6144 | 10240 |
| `in_proj` out = `d_inner + conv_dim + heads` | 17504 | 10304 | 18560 |
| SSM state / layer (scalars) | 983,040 | 524,288 | 1,048,576 |
| SSM state / sequence, fp32 | 82.6 MB (21 layers) | 48.2 MB (23) | 167.8 MB (40) |
| conv state / sequence, bf16 | ~1.2 MB | ~0.85 MB | ~2.5 MB |

Both the SSM and conv state are **O(1) in sequence length** — the whole point of the hybrid.

---

## 4. `mlp_hidden_act: relu2` — confirmed, and it is **ungated**

**VERIFIED.** `NemotronHMLP` in vLLM is two matrices, no gate:

```python
self.up_proj   = ColumnParallelLinear(hidden_size, intermediate_size, bias=bias)
self.down_proj = RowParallelLinear(intermediate_size, hidden_size, bias=bias)
self.act_fn    = ReLUSquaredActivation()

def forward(self, x):
    x, _ = self.up_proj(x); x = self.act_fn(x); x, _ = self.down_proj(x)
```

So `y = W_down · ReLU(W_up x)²`. No `gate_proj`, no SwiGLU. The MoE path is explicitly the same — vLLM's `get_expert_mapping` comment says *"FusedMoe.w3 (aka up_proj) should be ignored since we're using non-gated MoE"*, and the class sets `is_non_gated_moe: bool = True`.

NVIDIA's own statements: Nemotron-H (arXiv 2504.03624) — *"squared ReLU activation for FFN layers"*; Nemotron 3 Nano (arXiv 2512.20848) — *"For the MoE layers, we use squared ReLU activation and a standard learnt MLP router with sigmoid gating."*

**Why NVIDIA uses it: not stated in any Nemotron paper I read.** I checked 2504.03624, 2512.20848, and 2512.20856 for a justification and found none — the choice is asserted, not argued. Reporting the gap rather than inventing a story.

**INFERRED** context, clearly labelled as mine, not NVIDIA's:
- Squared ReLU entered Transformer LMs via **Primer** (So et al., *Searching for Efficient Transformers for Language Modeling*, NeurIPS 2021, arXiv 2109.08668), which found it by architecture search and reported training-compute savings.
- An ungated FFN has 2 weight matrices instead of SwiGLU's 3, so at a fixed parameter budget it can be ~1.5× wider. The 4B's `intermediate_size: 12544` is exactly `4 × hidden` — the classic ungated ratio, where a SwiGLU model of the same size would sit near `2.67 ×`. **VERIFIED** arithmetic, **INFERRED** motive.
- ReLU² produces exactly-zero activations, which is a prerequisite for activation-sparsity kernels. Plausible but **UNVERIFIED** as NVIDIA's reason.

---

## 5. MoE — routing, LatentMoE, MTP

### Routing (30B and 120B; **VERIFIED** from `NemotronHMoE`)

- **Gate:** `GateLinear(hidden_size → n_routed_experts)` with `out_dtype=torch.float32, force_fp32_compute=True`. Router logits are always fp32 regardless of model dtype.
- **Score function:** vLLM hard-codes `scoring_func="sigmoid"` for this architecture (not softmax). Confirmed by the paper: *"a standard learnt MLP router with sigmoid gating."*
- **Bias correction:** the gate carries a loaded parameter `e_score_correction_bias` of shape `[n_routed_experts]`, added to the scores **before** top-k selection but not used to weight the outputs — the **DeepSeek-V3 aux-loss-free load-balancing** scheme. The Nemotron 3 Nano paper names it: *"we used DeepSeek's aux-loss-free load balancing strategy with an update rate of 10⁻³ in conjunction with the standard load balancing loss. We used a load balancing loss coefficient of 10⁻⁴."* (So: bias-based balancing **plus** a small conventional aux loss, not either/or.)
- **Grouping is degenerate:** `use_grouped_topk=True` is passed, but `n_group: 1` and `topk_group: 1` make it a plain global top-k over all experts. No DeepSeek-style device/node-limited routing.
- **Renormalisation:** `norm_topk_prob: true` → the *k* selected sigmoid gates are rescaled to sum to 1.
- **Output scaling:** `routed_scaling_factor` (2.5 / 5.0) with `apply_routed_scale_to_output=True`, i.e. `y = s · Σ_k g_k E_k(x) + Shared(x)` — the scale multiplies the routed sum only, never the shared branch.
- **Every channel-mixer is sparse.** Both MoE patterns contain zero `-` characters. Unlike DeepSeek-V3 / Qwen3-MoE, Nemotron-3 keeps **no dense warm-up layers**.

### ⚠️ CONTRADICTION #2 — "1 shared expert" vs the paper's "2"

`n_shared_experts: 1`, but `moe_shared_expert_intermediate_size` is exactly **twice** the routed expert width (3712 = 2 × 1856; 5376 = 2 × 2688), while arXiv 2512.20848 Table 1 lists *"Number of Shared Experts: 2"*.

Resolved: it is bookkeeping, not disagreement. vLLM builds the shared branch as `intermediate_size = moe_shared_expert_intermediate_size × n_shared_experts` = 3712 — one MLP of double width, arithmetically identical to two experts of standard width. **Draw it as one wide shared MLP**, and note the paper counts it as two.

### LatentMoE — 120B only (**VERIFIED** config + code + paper)

`moe_latent_size: 1024`. In `NemotronHMoE`, `use_latent_moe = getattr(config, "moe_latent_size", None) is not None`; when set, `moe_hidden_size = 1024` and two `ReplicatedLinear` layers (deliberately **not** tensor-parallel) are inserted:

```python
self.fc1_latent_proj = ReplicatedLinear(config.hidden_size, self.moe_hidden_size)   # 4096 → 1024
self.fc2_latent_proj = ReplicatedLinear(self.moe_hidden_size, config.hidden_size)   # 1024 → 4096
...
FusedMoEFactory(..., hidden_size=self.moe_hidden_size,
                routed_input_transform=self.fc1_latent_proj,
                routed_output_transform=self.fc2_latent_proj, ...)
```

So **all 512 routed experts live entirely in 1024-d**: each is `1024 → 2688 → 1024`, ungated ReLU². The **shared expert stays in the full 4096-d space** (`4096 → 5376 → 4096`) — `apply_routed_input_transform` returns a separate untransformed `shared_experts_input`. The router also reads the full 4096-d hidden state (`GateLinear(config.hidden_size, ...)`), not the latent.

NVIDIA's description (arXiv 2512.20856): *"Each token embedding is first projected from the original hidden dimension d into a latent representation of smaller dimension ℓ<d, routed to an expanded set of experts that operate entirely in this latent space, and then projected back to the original hidden dimension d."* The compression ratio is `d/ℓ = 4096/1024 = 4×`, matching vLLM's blog framing *"Latent MoE enables calling 4 experts for the inference cost of only one."*

**Parameter arithmetic reproduces the published headline numbers exactly** (**INFERRED**, my computation):

| | 30B-A3B | 120B-A12B |
|---|---|---|
| routed experts | 128 × (2688·1856·2) × 23 = 29.37 B | 512 × (1024·2688·2) × 40 = 112.74 B |
| latent projections | — | 40 × 4096·1024·2 = 0.34 B |
| shared experts | 23 × 4096·2688·... = 0.46 B | 40 × 4096·5376·2 = 1.76 B |
| Mamba layers | 0.89 B | 4.39 B |
| attention layers | 0.14 B | 0.29 B |
| embeddings (untied, ×2) | 0.70 B | 1.07 B |
| **total** | **31.6 B** ✓ (paper: 31.6 B) | **120.7 B** ✓ (card: 120 B) |
| **active / token** | **3.2 B** ✓ (excl. input embed) | **12.2 B** ✓ |

The 4B checks out too: 1.66 + 1.34 + 0.15 + 0.82 = **3.97 B**, against the card's `3.97 × 10⁹`. Three-for-three agreement is strong evidence the structural reading above is right.

### MTP — 120B only (**VERIFIED** from `nemotron_h_mtp.py`)

`num_nextn_predict_layers: 1`, `mtp_hybrid_override_pattern: "*E"`.

```python
self.num_mtp_layers = getattr(config, "num_nextn_predict_layers", 1)
assert self.num_mtp_layers == 1, "Only one MTP layer is supported for NemotronH-MTP"
self.pattern_str = config.mtp_hybrid_override_pattern
total_layers = self.num_mtp_layers * self.pattern_len     # = 1 × 2
```

So the MTP head is **one prediction step realised as two physical layers**, using the same alphabet as the main stack: an attention layer then an MoE layer. **No Mamba layer in the MTP head.** Its first layer (`has_start_projections`) carries two extra RMSNorms `enorm`/`hnorm` and a fusion projection `eh_proj: 2h → h` that concatenates the next token's embedding with the previous hidden state; its last layer carries `final_layernorm`. Embedding table and LM head are shared with the main model. This is the DeepSeek-V3 MTP design rebuilt from Nemotron-H blocks.

Purpose, per arXiv 2512.20856: *"Predicting multiple future tokens provides richer training signals... These auxiliary predictions also serve naturally as draft tokens for speculative decoding"*, with a claimed ~2.4% average benchmark gain during training.

**Important for this study:** `served.vllm_args` is `["--enable-prefix-caching"]` only — no `--speculative-config`. **INFERRED**: the MTP head was present in the checkpoint but not driving speculative decoding during the eval, so it did not affect outputs.

### ⚠️ FLAG — `moe_shared_expert_overlap: false` is unexplained

`grep -rn "shared_expert_overlap"` over the entire vLLM 0.27.1 tree returns **zero hits**, and it is not a `NemotronHConfig` parameter. By name it matches a vLLM engine-level scheduling flag (`--moe-shared-expert-overlap`) that runs the shared expert concurrently with the routed experts' all-to-all dispatch — a throughput knob with no effect on outputs. **UNVERIFIED**: whether any runtime reads it from `config.json`. Setting it to `false` in a model config is odd either way. Do not draw it.

---

## 6. GQA — confirmed, and the KV-cache consequence is the story

**VERIFIED** from config and `NemotronHAttention`:

| | 4B | 30B-A3B | 120B-A12B |
|---|---|---|---|
| `num_attention_heads` | 40 | **32** | **32** |
| `num_key_value_heads` | 8 | **2** | **2** |
| `head_dim` | 128 | 128 | 128 |
| Q:KV ratio | 5:1 | **16:1** | **16:1** |
| attention layers | 4 / 42 | 6 / 52 | 8 / 88 |
| `attention_bias` | false | false | false |
| `sliding_window` | null | null | null |
| QK-norm | **none** | **none** | **none** |

Your reading is right: 32 query heads to 2 KV heads on both MoE rungs. Note `head_dim` is explicit and **not** `hidden/heads` — for the 4B, `40 × 128 = 5120 ≠ 3136`, so the attention projection widens then contracts. QK-norm is absent **by construction**: `NemotronHAttention` has no `q_norm`/`k_norm` member and applies nothing between `qkv_proj` and `self.attn`.

### KV-cache consequence (**INFERRED** arithmetic, bf16, from verified fields)

Per token: `2 (K,V) × num_kv_heads × head_dim × 2 bytes × n_attention_layers`

| | per token | at served 131,072 ctx |
|---|---|---|
| 4B | **16 KiB** | **2.0 GiB** |
| 30B-A3B | **6 KiB** | **768 MiB** |
| 120B-A12B | **8 KiB** | **1.0 GiB** (8 GiB at 1M) |

Two things worth drawing:

1. **The 4B has a 2.7× larger KV cache per token than the 30B**, despite being ~8× smaller in parameters — five KV heads' worth of extra width times fewer but fatter layers. The ladder's KV footprint is non-monotonic.
2. **The 120B's 8 KiB/token is ~44× smaller** than a hypothetical 88-layer, 8-KV-head all-attention model of the same depth (352 KiB/token). Eight attention layers out of 88, at 2 KV heads, is where the hybrid's memory win lives — and it is the reason a 1M-token claim is even arguable.

---

## 7. Other blocks

**VERIFIED unless noted.**

- **Norms.** RMSNorm everywhere, `eps = 1e-5` (`layer_norm_epsilon`). **Pre-norm with fused residual**: every layer does `hidden_states, residual = self.norm(hidden_states, residual)` — the residual is carried in-flight, not re-added per layer. A final `norm_f` sits before the LM head. Mamba blocks contain one *additional* gated group-RMSNorm inside the mixer.
- **Embeddings.** `tie_word_embeddings: false` on all three — separate `embed_tokens` and `lm_head`. Vocab 131,072 = 2¹⁷ on all three.
- **Tokenizer.** vocab 131,072; byte-level BPE fast tokenizer. Token IDs 0–4 are `<unk>`, `<s>`, `</s>`, `[INST]`, `[/INST]`, with `[AVAILABLE_TOOLS]` / `[TOOL_RESULTS]` / `[TOOL_CALLS]` also present — **the Mistral "Tekken" special-token layout, and 131,072 is Tekken's vocab size**. NVIDIA does not name the tokenizer in any Nemotron-3 report I read, so the Tekken lineage is **INFERRED** from the token table, not stated. IDs 10/11 are `<|im_start|>` / `<|im_end|>` (ChatML), added on top.
- **Stop tokens differ across the ladder.** `generation_config.eos_token_id` is `2` for the 4B but `[2, 11]` for the 30B and 120B — i.e. the MoE rungs also stop on `<|im_end|>`. Relevant to harness behaviour, worth a footnote in the atlas.
- **No logit softcapping.** Absent from every config and from the model code.
- **Quantisation of the shipped weights: none.** `quantization: null`, `torch_dtype/dtype: bfloat16` on all three — these are the `-BF16` repos. NVIDIA separately ships NVFP4 and FP8 variants that this study did not use. Note the 120B was *trained* with NVFP4 GEMMs (arXiv 2512.20856) but the weights served here are BF16. No `--kv-cache-dtype` was passed, so the KV cache was BF16 too.
- **Attention backend.** No sliding window, no attention sinks, no bias.

---

## 8. The repeating motif — and exactly where it breaks

**VERIFIED** by enumerating the pattern strings. **None of the three tiles exactly.**

### 4B — dominant motif `M-` (Mamba → dense MLP), 42 layers

```
idx  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20
     M  -  M  -  M  -  M  M  -  M  -  M  *  -  M  -  M  *  -  M  -
idx 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41
     M  -  M  *  -  M  -  M  -  M  M  *  -  M  M  M  -  M  -  M  -
```
- Counts: 21 `M`, 17 `-`, 4 `*`. Attention = **9.5%** of layers.
- **Where it breaks:** `M` and `-` are *not* 1:1 (21 vs 17). Removing the `*` leaves `M-M-M-MM-M-M-M-M-M-M-M-M-M-MM-MMM-M-M-` — three unpaired Mamba runs: **`MM` at 6–7, `MM` at 30–31, `MMM` at 34–36**. Four dense MLPs' worth of channel-mixing were removed relative to a clean `M-` tiling.
- Attention sits at **12, 17, 24, 32** — strides of 5, 7, 8. Irregular.
- **INFERRED**: this ragged pattern is what structured pruning produces. The 4B was *"pruned and distilled from Nemotron Nano 9B v2 using the Nemotron Elastic framework"* using *"structured pruning guided by a router"* (NVIDIA HF blog, `huggingface.co/blog/nvidia/nemotron-3-nano-4b`), which also states the layer census as *"21 Mamba, 4 Attention, 17 MLP"* — an exact match to the config.

### 30B-A3B — motif `ME`, 52 layers

```
MEMEM*EMEMEM*EMEMEM*EMEMEM*EMEMEM*EMEMEMEM*EMEMEMEME
```
- Counts: 23 `M`, 23 `E`, 6 `*`. Attention = **11.5%**.
- **Removing the `*` yields a perfectly alternating `MEMEME…`** — verified programmatically. So the base tiling is exactly 23 `(Mamba-2 → MoE)` pairs, and attention layers are **inserted into** the stack rather than substituting for anything. That is why `M` and `E` counts are equal and `23 × 2 + 6 = 52`.
- **Where it breaks:** the insertion stride. Attention sits at **5, 12, 19, 26, 33, 42** — gaps of 7, 7, 7, 7, **9**. The last gap is stretched, and the stack ends with a 9-layer attention-free tail.

### 120B-A12B — motif `ME`, 88 layers

```
MEMEMEM*EMEMEMEM*EMEMEMEM*EMEMEMEMEM*EMEMEMEMEM*EMEMEMEMEM*EMEMEMEMEM*EMEMEMEM*EMEMEMEME
```
- Counts: 40 `M`, 40 `E`, 8 `*`. Attention = **9.1%**.
- Same rule: removing `*` gives perfect `ME` alternation; 40 pairs + 8 inserted attention = 88.
- **Where it breaks:** attention at **7, 16, 25, 36, 47, 58, 69, 78** — gaps of 9, 9, **11, 11, 11, 11**, 9. Denser attention at the two ends, sparser through the middle six-elevenths of the stack.

### The invariant worth putting in the diagram

**In all three rungs, every attention layer is immediately preceded by a Mamba-2 layer** (context `M*` in 4/4, 6/6, 8/8 cases; `M*E` on the MoE rungs, `M*-` on the 4B). Attention never runs directly on the output of a channel-mixer. Given NoPE, this is not a coincidence: an attention layer's only source of order information is what the Mamba recurrence just wrote into the residual stream. **VERIFIED** as a pattern fact; **INFERRED** as a design intent — NVIDIA does not state it. The published rule they *do* state (arXiv 2504.03624) is looser: *"We set the number of attention layers to be roughly 8% of the total number of layers and evenly disperse them throughout the model."* — 9.1–11.5% here, so Nemotron-3 runs slightly above the Nemotron-H target.

---

## 9. Per-rung identity cards

### `nemotron-3-nano-4b` — `nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16` @ `dfaf35de3e30f1867dd8dbc38a7fc9fb52d3914f`

| | |
|---|---|
| Full name | NVIDIA Nemotron 3 Nano 4B (BF16) |
| Release | **2026-03-16** (HF card "Release Date: 3/16/2026"); NVIDIA blog post 2026-03-17 |
| Params | **3.97 × 10⁹ total, dense — all active.** Card: *"Number of model parameters 3.97 x 10⁹"*. My arithmetic: 3.973 B ✓ |
| Lineage | *"pruned and distilled from Nemotron Nano 9B v2 using the Nemotron Elastic framework"* — **a Nemotron-2-generation descendant, not a Nemotron-3 pretrain**. Pretraining cutoff **September 2024** (vs June 2025 for the 30B). |
| Licence | NVIDIA Nemotron Open Model License |
| Tokenizer | 131,072-vocab BPE, Tekken-style special tokens (**INFERRED**); untied embeddings |
| Positional encoder | **NoPE.** No rope fields in config at all. Position from Mamba-2 recurrence + causal conv(4); attention causal-mask only. |
| Token mixing | 21 × Mamba-2 (96 heads × 80 dim, N=128, 8 groups, chunk 256, `d_inner` 7680); 4 × GQA (40 Q / 8 KV, head_dim 128, no QK-norm, no bias) |
| Channel mixing | 17 × **dense** MLP, 3136 → 12544 → 3136 (`4×h`), ungated ReLU². No MoE. |
| Norms | RMSNorm 1e-5, pre-norm fused residual, final `norm_f`; gated group-RMSNorm inside each Mamba block |
| Other | No MTP. No softcapping. BF16. `max_position_embeddings` 262144; card claims 262K; served at 131072, tp=1 |
| Motif | `M-` dominant; breaks at `MM`(6–7), `MM`(30–31), `MMM`(34–36); `*` at 12/17/24/32 |
| KV cache | 16 KiB/token → 2.0 GiB at 131k ctx |

### `nemotron-3-nano-30b-a3b` — `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16` @ `2d59de1cbd51c0adf384eb906b766d1aee0e0517`

| | |
|---|---|
| Full name | NVIDIA Nemotron 3 Nano 30B-A3B (BF16) |
| Release | **2025-12-15** (HF card) |
| Params | **31.6 B total / 3.2 B active** per arXiv 2512.20848 (*"3.6B including embeddings"*). HF card says *"3.5B active"* — a minor **discrepancy** between card and paper; my arithmetic lands on 3.2 B excluding the input embedding, matching the paper. |
| Licence | NVIDIA Nemotron Open Model License |
| Tokenizer | 131,072-vocab; `eos_token_id: [2, 11]` (`</s>` and `<|im_end|>`) |
| Positional encoder | **NoPE.** *"We do not use any positional embeddings, dropout, or bias on linear layers."* (arXiv 2512.20848). ⚠️ Config nonetheless declares `rope_theta: 10000`, `partial_rotary_factor: 1.0` — **inert**. |
| Token mixing | 23 × Mamba-2 (64 heads × 64 dim, N=128, 8 groups, chunk 128, `d_inner` 4096); 6 × GQA (**32 Q / 2 KV**, head_dim 128, no QK-norm) |
| Channel mixing | 23 × **MoE**, no dense layers. 128 routed experts (2688 → 1856 → 2688, ungated ReLU²), top-6, 1 shared expert of double width (2688 → 3712 → 2688). Sigmoid router in fp32, `e_score_correction_bias` (aux-loss-free), `norm_topk_prob`, `routed_scaling_factor 2.5` on the routed sum only. `n_group=topk_group=1` → plain global top-k. |
| Norms | as 4B |
| Other | No MTP, no latent MoE, no softcapping. BF16. `mamba_ssm_cache_dtype: "float32"`. Served 131072 ctx, tp=4 |
| Motif | 23 × `ME`, exact alternation; `*` inserted at 5/12/19/26/33/42 (gaps 7,7,7,7,**9**) |
| KV cache | 6 KiB/token → 768 MiB at 131k ctx |

Independent corroboration of the layer census: the HF card states *"23 Mamba-2 and MoE layers, along with 6 Attention layers"* and *"128 experts plus 1 shared expert, with 6 experts activated per token"* — exact match to config.

### `nemotron-3-super-120b-a12b` — `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16` @ `d51eab0d1f979ebc26b546e634a04f450d99158e`

| | |
|---|---|
| Full name | NVIDIA Nemotron 3 Super 120B-A12B (BF16) |
| Release | **2026-03-11** |
| Params | **120 B total / 12 B active** (HF card: *"120B Total / 12B Active"*). My arithmetic: 120.7 B / 12.2 B ✓ |
| Architecture name as published | *"Mamba2-Transformer Hybrid Latent Mixture of Experts (LatentMoE) with Multi-Token Prediction (MTP)"*; network architecture *"Nemotron Hybrid LatentMoE"* (HF card, verbatim) |
| Licence | NVIDIA Nemotron Open Model License |
| Tokenizer | 131,072-vocab; `eos_token_id: [2, 11]` |
| Positional encoder | **NoPE.** *"Consistent with prior Nemotron models, we omit positional embeddings, dropout, and bias terms in linear layers"* (Nemotron 3 Super report, arXiv 2604.12374). ⚠️ Config declares `rope_theta: 10000`, `partial_rotary_factor: 1.0` — **inert**. |
| Token mixing | 40 × Mamba-2 (128 heads × 64 dim, N=128, 8 groups, chunk 128, `d_inner` 8192); 8 × GQA (**32 Q / 2 KV**, head_dim 128, no QK-norm) |
| Channel mixing | 40 × **LatentMoE**, no dense layers. `fc1_latent_proj` 4096→1024, **512 routed experts entirely in 1024-d** (1024 → 2688 → 1024, ungated ReLU²), **top-22**, `fc2_latent_proj` 1024→4096. Shared expert bypasses the latent space: 4096 → 5376 → 4096. Router reads full 4096-d, fp32, sigmoid + `e_score_correction_bias`, `norm_topk_prob`, `routed_scaling_factor 5.0`. |
| MTP | 1 prediction step = 2 physical layers `"*E"` (attention + MoE, **no Mamba**), with `enorm`/`hnorm` + `eh_proj (2h→h)` fusion at the head and `final_layernorm` at the tail; embedding and LM head shared. Not activated during this study (no `--speculative-config`). |
| Other | No softcapping. Weights BF16 (trained with NVFP4 GEMMs). `mamba_ssm_cache_dtype: "float32"`; `moe_shared_expert_overlap: false` (**unexplained**, see §5). Served 131072 ctx, tp=8 |
| Motif | 40 × `ME`, exact alternation; `*` at 7/16/25/36/47/58/69/78 (gaps 9,9,**11,11,11,11**,9) |
| KV cache | 8 KiB/token → 1.0 GiB at 131k ctx, 8 GiB at 1M |

---

## 10. What changes across the ladder

**Fixed on all three rungs (**VERIFIED**):** `NemotronHForCausalLM`; **NoPE**; `ssm_state_size 128`; `n_groups 8`; `conv_kernel 4`; `use_conv_bias true`; attention `head_dim 128`; ungated **ReLU²** channel mixers; RMSNorm `eps 1e-5` pre-norm with fused residual; `vocab_size 131072`; `tie_word_embeddings false`; `max_position_embeddings 262144`; `sliding_window null`; no QK-norm; no bias on any linear (`attention_bias`, `mlp_bias`, `use_bias`, `mamba_proj_bias` all false); `time_step_min/max/floor` identical; BF16; `torch_dtype` bfloat16; every attention layer preceded by a Mamba layer; attention ≈ 9–12% of layers.

**Moves:**

| knob | 4B | 30B-A3B | 120B-A12B | note |
|---|---|---|---|---|
| channel mixer | dense MLP | MoE | **LatentMoE** | the ladder's defining axis |
| `hidden_size` | 3136 | 2688 | 4096 | **non-monotonic** — 4B > 30B |
| `num_hidden_layers` | 42 | 52 | 88 | |
| layer census (M/E-or-–/*) | 21 / 17 / 4 | 23 / 23 / 6 | 40 / 40 / 8 | |
| `mamba_num_heads` × `mamba_head_dim` | 96 × 80 | 64 × 64 | 128 × 64 | `d_inner` 7680 / 4096 / 8192 |
| `chunk_size` | 256 | 128 | 128 | throughput only |
| Q / KV heads | 40 / 8 | 32 / 2 | 32 / 2 | 5:1 → 16:1 |
| `n_routed_experts` | — | 128 | 512 | |
| `num_experts_per_tok` | — | 6 | 22 | |
| expert width | — | 2688→1856 | **1024→2688** | latent input |
| `moe_latent_size` | — | — | 1024 | 4× compression |
| shared expert width | — | 3712 | 5376 | = 2× routed width in both |
| `routed_scaling_factor` | — | 2.5 | 5.0 | |
| MTP | — | — | 1 step (`"*E"`) | |
| `rope_theta` present | no | **yes (inert)** | **yes (inert)** | |
| `time_step_rank` present | **yes (inert)** | no | no | Mamba-1 residue |
| `eos_token_id` | `2` | `[2, 11]` | `[2, 11]` | |
| tensor parallel served | 1 | 4 | 8 | |
| pretrain cutoff | Sept 2024 | June 2025 | June 2025 | |
| lineage | pruned from **Nemotron Nano 9B v2** | Nemotron-3 pretrain | Nemotron-3 pretrain | |

**The single most consequential ladder fact:** the 4B is not a small Nemotron-3 — it is a compressed Nemotron-2. Its larger hidden size, larger Mamba head dim, 5:1 GQA, dense MLPs, `chunk_size 256`, vestigial `time_step_rank`, absent rope fields, and 18-month-older data cutoff all follow from that. Any "size effect" read across this ladder confounds scale with generation on the bottom rung.

---

## 11. Long-context behaviour and the prior collapse finding

You asked me to report published sources on long-context behaviour without inventing a causal story for the earlier Nemotron-3-Super extensional-listing collapse. Here is what exists, and what does not.

### What NVIDIA publishes

- **Nemotron 3 Super base model, RULER** (arXiv 2604.12374, Table 4): 64K **92.26** → 128K **88.26** → 256K **84.56** → 512K **82.49** → 1M **71.00**. Monotonic 21-point decay.
- **Nemotron 3 Super aligned model, RULER** (HF card): 256K **96.30**, 512K **95.67**, 1M **91.75**. **⚠️ These two tables disagree sharply** — the card's 1M figure exceeds the base model's 128K figure, and the card publishes no 128K row at all. Stating the discrepancy; not explaining it.
- **Nemotron-H 8B-Instruct, RULER** (arXiv 2504.03624, Table 10): 16K 91.5 → 131K **81.7**, with hedged framing: *"Despite having only four self-attention layers, Nemotron-H-8B-Instruct is competitive with these models on the RULER long-context benchmark."*
- **NVIDIA concedes long-context extension cost them elsewhere** (arXiv 2604.12374): after 34 B tokens of CPT at 1,048,576 context, *"we added another stage to alternatingly train on both 1m and 4k sequences in order to mitigate the minor impact we observed on the math-related benchmarks."*
- **Nemotron Nano 2** (arXiv 2508.14444, §3.2): *"Although Stage 1 improved performance on most benchmarks, tool-calling accuracy degraded. We attribute this to sample concatenation at 128k."*
- **No model card carries a Limitations or Known-issues section on long context.**

### ⚠️ CONTRADICTION #3 — context length: 262,144 vs "1M"

`max_position_embeddings: 262144` on all three, but the cards advertise 1M. The 120B card: *"the model supports up to a 1M context size, although the default context size in the Hugging Face configuration is 256k due to higher VRAM requirements"*, reached by setting `VLLM_ALLOW_LONG_MAX_MODEL_LEN=1` — vLLM's explicit *override* for exceeding a model's declared limit. **NVIDIA staff have conceded the 1M documentation is wrong on the sibling 30B checkpoint**: on HF discussion #12 for `NVIDIA-Nemotron-3-Nano-30B-A3B-BF16`, an NVIDIA account replies *"sorry for the confusion on 1M context, we will fix documentation."* No equivalent acknowledgement exists on the Super card. **This study served all three at 131,072, well inside the declared 262,144.**

Because the architecture is NoPE, the 1M claim rests on **continued pretraining alone** — there is no RoPE to scale, so no YaRN/NTK/PI step exists or is needed. That is the architectural upside NVIDIA claims for NoPE (arXiv 2512.20856: *"therefore do not suffer from out-of-distribution RoPE issues during context extension"*).

### Literature on the relevant failure modes — general, not Nemotron-specific

I found **no published source that ties Nemotron-3-Super specifically to degeneration or repetition on long prompts.** That is a negative result and I am stating it as one. The nearest things that exist are serving-stack bug reports, not model properties: sglang #31833 (SSM-state offset miscomputation under a non-default Mamba scheduler strategy, real AIME accuracy drop on this exact BF16 checkpoint), TensorRT-LLM #12183 (NVFP4 per-expert weight-scale bug producing off-topic output on a *short* prompt), vLLM #39809 (Mamba prefix-caching + MTP startup crash on the NVFP4 checkpoint). None attributes anything to prompt length. One operational note is worth carrying: the vLLM recipe page for this checkpoint advises `VLLM_FLOAT32_MATMUL_PRECISION=high` to keep *"the Mamba scan numerically stable"* — so the scan is acknowledged to be precision-sensitive.

Published results about the *class* of architecture, offered as context and explicitly **not** as an explanation of the SmolBench finding:

- **Merrill, Petty & Sabharwal, "The Illusion of State in State-Space Models," ICML 2024** — *"SSMs cannot express computation outside the complexity class TC⁰... they cannot solve simple state-tracking problems like permutation composition... provably unable to accurately track chess moves with certain notation, evaluate code, or track entities in a long narrative."*
- **Jelassi et al., "Repeat After Me: Transformers are Better than State Space Models at Copying," ICML 2024** — *"transformer models dramatically outperform state space models at copying and retrieving information from context"*; fixed-state models are bounded where a 2-layer transformer is not.
- **Chen et al., "Stuffed Mamba: Oversized States Lead to the Inability to Forget," COLM 2025** — *"information interference, where different token data conflicts, resulting in performance degradation and incoherent outputs beyond a certain context length"*; retrieval length scales with state size.
- **Wang et al., "Length Generalization of Causal Transformers without Position Encoding," Findings of ACL 2024** — on NoPE specifically: *"although NoPE can extend to longer sequences than the commonly used explicit position encodings, it still has a limited context length. We identify a connection between the failure of NoPE's generalization and the distraction of attention distributions."*
- **Kazemnejad et al., NeurIPS 2023** — the pro-NoPE result NVIDIA is implicitly relying on.
- **Waleffe et al. (NVIDIA), "An Empirical Study of Mamba-based Language Models"** — NVIDIA's own stated rationale for hybridising: pure SSMs *"lag behind Transformers on tasks which require strong copying or in-context learning abilities... or long-context reasoning."*

**I found no paper analysing NoPE or Mamba-2 on enumeration, listing, or counting many items specifically.** The state-tracking and copying results above are the closest available, and they are about *different* tasks on *different* models. Anyone connecting them to the SmolBench extensional-listing collapse is doing new work, not citing existing work.

---

## 12. Config fields I could not fully explain — flagged, not smoothed over

| field | rungs | status |
|---|---|---|
| `rope_theta: 10000`, `partial_rotary_factor: 1.0` | 30B, 120B | **CONTRADICTION.** Not a `NemotronHConfig` parameter; unread by vLLM and by the HF in-repo model; contradicted by four NVIDIA reports. Inert. |
| `moe_shared_expert_overlap: false` | 120B | **UNEXPLAINED.** Zero hits across the vLLM 0.27.1 tree; not a `NemotronHConfig` parameter. Name matches a vLLM engine scheduling flag. **UNVERIFIED** whether any runtime reads it from config.json. |
| `expand: 2` | all 3 | **INERT and numerically wrong on 2 of 3.** `d_inner` is `mamba_num_heads × mamba_head_dim` in both implementations. |
| `time_step_rank: 256` | 4B only | **INERT.** A Mamba-**1** field (low-rank `dt` projection). Not a `NemotronHConfig` parameter; Mamba-2 has no `dt_rank`. Residue of the 4B's older lineage. |
| `mamba_ssm_cache_dtype: "float32"` | 30B, 120B | **MISPLACED.** vLLM 0.27.1 reads this from `CacheConfig` (CLI `--mamba-ssm-cache-dtype`), never from `hf_config`. **UNVERIFIED** whether the nightly plumbs it from config.json; if not, the served SSM state dtype followed the `"auto"` default, not this field. |
| `norm_eps: 1e-5` | 30B, 120B | **REDUNDANT.** Duplicates `layer_norm_epsilon`; the model code reads `layer_norm_epsilon`. Appears in `derived.unclassified`. |
| `n_group: 1`, `topk_group: 1` | 30B, 120B | **DEGENERATE.** Grouped-top-k machinery is instantiated but has exactly one group — plain global top-k. |
| `time_step_limit` | all 3 | Config default `(0.0, inf)` — stored but not emitted in the JSON; no clamping beyond `dt_min/dt_max`. |
| `residual_in_fp32: false`, `rescale_prenorm_residual: true`, `initializer_range`, `hidden_dropout`, `num_logits_to_keep`, `use_cache`, `use_mamba_kernels` | all 3 | Training/HF-runtime fields with no vLLM inference-graph effect. Not diagram-relevant. |
| `max_position_embeddings: 262144` vs cards' "1M" | all 3 | **CONTRADICTION #3**, §11. NVIDIA has conceded the doc error on the 30B. |
| `num_key_value_heads: 8` default in `NemotronHConfig` | — | Not a finding, but note the class default (8) differs from what the MoE rungs set (2); don't read defaults as values. |

---

## 13. What I did not cover

- **The HF in-repo `modeling_nemotron_h.py`** was read only for the RoPE question and the block dispatch. Its MoE and Mamba internals were not line-by-line verified against vLLM; I assumed they agree because the parameter arithmetic reconciles to within 0.3% on all three rungs.
- **The exact vLLM nightly** that served the study. I read 0.27.1. Any nightly-only change to `nemotron_h.py` (e.g. new handling of `moe_shared_expert_overlap` or `mamba_ssm_cache_dtype`) would not appear in my reading.
- **Tokenizer identity.** NVIDIA names no tokenizer in any Nemotron-3 report I read. The Tekken attribution is my inference from the special-token table and the 2¹⁷ vocab, not a sourced claim. I also could not read `tokenizer_class` — the `added_tokens_decoder` block is large enough that the fetch truncated before it.
- **The Nemotron 3 Ultra report** (arXiv 2606.15007) — not fetched; out of scope for these three rungs.
- **Nemotron Elastic**, the pruning framework that produced the 4B, was not read in detail; only NVIDIA's one-sentence description of it.

---

## 14. Sources

Config ground truth (outranks everything below):
1. `/workspace/SmolBench/scripts/arch/arch_facts.json`, `/workspace/SmolBench/scripts/arch/arch_configs_raw.json` — fetched 2026-08-12; SHAs `dfaf35de…`, `2d59de1c…`, `d51eab0d…`.

Reference implementations (read locally):
2. vLLM 0.27.1 — `vllm/transformers_utils/configs/nemotron_h.py`, `vllm/model_executor/models/nemotron_h.py`, `nemotron_h_mtp.py`, `vllm/model_executor/layers/mamba/mamba_mixer2.py`, `vllm/model_executor/layers/fused_moe/{layer.py,runner/latent_moe_runner.py}`.
3. `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16` → `modeling_nemotron_h.py` (HF in-repo custom code).

Papers:
4. Nemotron 3 Nano technical report — arXiv 2512.20848 — https://arxiv.org/abs/2512.20848
5. NVIDIA Nemotron 3 white paper — arXiv 2512.20856 — https://arxiv.org/abs/2512.20856
6. Nemotron 3 Super technical report — arXiv 2604.12374 — https://arxiv.org/html/2604.12374v1
7. Nemotron-H — arXiv 2504.03624 — https://arxiv.org/abs/2504.03624
8. NVIDIA Nemotron Nano 2 — arXiv 2508.14444 — https://arxiv.org/abs/2508.14444
9. So et al., *Primer: Searching for Efficient Transformers for Language Modeling*, NeurIPS 2021 — https://arxiv.org/abs/2109.08668
10. Merrill, Petty & Sabharwal, *The Illusion of State in State-Space Models*, ICML 2024 — https://arxiv.org/abs/2404.08819
11. Jelassi et al., *Repeat After Me: Transformers are Better than State Space Models at Copying*, ICML 2024 — https://arxiv.org/abs/2402.01032
12. Chen et al., *Stuffed Mamba: Oversized States Lead to the Inability to Forget*, COLM 2025 — https://arxiv.org/abs/2410.07145
13. Wang et al., *Length Generalization of Causal Transformers without Position Encoding*, Findings of ACL 2024 — https://aclanthology.org/2024.findings-acl.834/
14. Kazemnejad et al., *The Impact of Positional Encoding on Length Generalization in Transformers*, NeurIPS 2023 — https://arxiv.org/abs/2305.19466
15. Waleffe et al. (NVIDIA), *An Empirical Study of Mamba-based Language Models* — https://arxiv.org/abs/2406.07887

Model cards / vendor pages:
16. https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16
17. https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16 (and discussion #12, NVIDIA staff on the 1M doc error)
18. https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16
19. https://huggingface.co/blog/nvidia/nemotron-3-nano-4b — 4B pruning/distillation lineage and the "21 Mamba, 4 Attention, 17 MLP" census
20. https://developer.nvidia.com/blog/inside-nvidia-nemotron-3-techniques-tools-and-data-that-make-it-efficient-and-accurate/
21. https://vllm.ai/blog/2026-03-11-nemotron-3-super
22. https://recipes.vllm.ai/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16 — `VLLM_FLOAT32_MATMUL_PRECISION=high` for Mamba-scan stability

Bug reports (labelled as such, not evidence of model properties):
23. sgl-project/sglang#31833; NVIDIA/TensorRT-LLM#12183; vllm-project/vllm#39809.
