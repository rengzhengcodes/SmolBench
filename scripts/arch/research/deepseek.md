# DeepSeek — architecture atlas section

Three rungs, deliberately cross-generation. **V4-Flash** (284B/13B) and **V4-Pro** (1.6T/49B) share a
genuinely new architecture (`DeepseekV4ForCausalLM`); **V3.1** (671B/37B, `DeepseekV3ForCausalLM`) is the
previous-generation anchor, and at the Pro rung the two generations are shape-matched (61 layers, hidden
7168, 128 query heads), which makes the V3.1↔V4-Pro comparison a clean A/B.

Ground truth is `scripts/arch/arch_configs_raw.json` / `arch_facts.json` (fetched 2026-08-12, repo commit
SHAs pinned). Every non-config claim is cited and labelled **VERIFIED** (I or a delegated reader read the
source line quoted), **INFERRED** (my arithmetic/reading over config + source), or **UNVERIFIED** (no source
found). Where a source disagrees with the config or with another source, the disagreement is reported in
§5 rather than smoothed over.

---

## 1. DeepSeek-V3.1 — the known quantity

### 1.1 Identity

| | |
|---|---|
| Full name | DeepSeek-V3.1 |
| Repo / SHA | `deepseek-ai/DeepSeek-V3.1` @ `c0781d039fb7a1ba2abc4add0bdc293e92d2b8db` |
| Vendor | DeepSeek-AI |
| Released | 2025-08-19, announced 2025-08-21 [2] — **VERIFIED** (vendor API news post) |
| Total / active params | 671B total, 37B activated [1] — **VERIFIED** (model-card table). The HF repo advertises 685B; the ~14B delta is the MTP module, which the card's 671B excludes — **INFERRED** |
| Licence | MIT [1] — **VERIFIED** |
| Tokenizer | DeepSeek byte-level BPE, `vocab_size: 129280` (config) — **VERIFIED**. Sentinels `<｜begin▁of▁sentence｜>` (id 0), `<｜end▁of▁sentence｜>` (id 1), `<｜User｜>`, `<｜Assistant｜>`, `<think>`, `</think>` [1] |
| Context | 128K advertised; config `max_position_embeddings: 163840` — see §1.2 |
| Served here | tp=8, `max_model_len` 131072, `--enable-prefix-caching`. Ships its own Jinja chat template with a `thinking` kwarg — no override needed |

Config arithmetic reproduces the published counts, which is the check that the shape fields mean what they
appear to mean (**INFERRED**): 58 MoE layers × 256 experts × 3·7168·2048 = 654B expert weights + 11.4B
attention + 1.19B dense FFN + 1.85B embed/head ≈ **669B**; active = 11.4B attention + 58 × 9 experts ×
44.0M = 23.0B + embed/head ≈ **36B**.

### 1.2 Positional encoder — partial RoPE + YaRN

- `rope_theta: 10000`, applied **only to the 64-dim `qk_rope_head_dim` slice**. The 128-dim
  `qk_nope_head_dim` slice and the entire 128-dim value head are **not** rotated.
- `rope_scaling`: `{type: yarn, factor: 40, original_max_position_embeddings: 4096, beta_fast: 32,
  beta_slow: 1, mscale: 1.0, mscale_all_dim: 1.0}`. 4096 × 40 = **163840** = `max_position_embeddings`,
  exactly — the YaRN factor is what defines the window. **VERIFIED (arithmetic over config).**
- **What the two-stage extension is.** YaRN is NTK-by-parts: RoPE dimensions whose wavelength exceeds the
  original 4096 window (selected by `beta_slow: 1`) are position-interpolated; high-frequency dimensions
  (`beta_fast: 32`) are left untouched; a linear ramp covers the middle. `mscale` and `mscale_all_dim` both
  pinned to 1.0 **disables** YaRN's attention-logit temperature correction (the √t factor is 1). The
  *training* staging is separate and coarser than the config: the V3.1 card reports a 32K extension phase
  of **630B tokens** and a 128K phase of **209B tokens** [1] — **VERIFIED**. So the architecture is one
  YaRN configuration spanning 4K→163840, the model was trained into it in two data phases (32K then 128K),
  and the vendor advertises the 128K it actually trained rather than the 163840 the config permits. The
  study served 131072.
- Treatment is uniform across all 61 layers.

### 1.3 Attention — Multi-head Latent Attention (MLA)

128 query heads; `num_key_value_heads: 128` is vestigial (MLA replaces GQA sharing entirely). Per token,
per layer:

```
h (7168) ─W_DQ─► q_latent (1536) ─RMSNorm─► W_UQ ─► 128 heads × 192 = [128 nope | 64 rope]
h (7168) ─W_DKV─► kv_latent (512) ‖ k_rope (64)     ◄── THE ONLY CACHED TENSOR (576 elems)
                       └─RMSNorm─► W_UK / W_UV ─► 128 × [128 nope k | 128 v]
```

- **Compression path.** Keys and values are never materialised in cache. Only the 512-dim `kv_lora_rank`
  latent plus the 64-dim RoPE key are stored: **576 elements per token per layer**, against 128 × 256 =
  32768 for the equivalent MHA — a **57×** reduction. Across 61 layers, 35,136 elements/token; in the same
  576-byte-per-slot FP8 layout V4 uses (64 dims BF16 + 512 dims FP8), that is 61 × 576 B ≈ **34 KB/token**.
  As actually served here (no `--kv-cache-dtype`, BF16 KV) it is ~69 KB/token. **INFERRED (arithmetic).**
- **Decoupled RoPE — why only 64 dims are rotated.** MLA's efficiency depends on absorbing `W_UK` into
  `W_UQ` at inference, so the query is scored against the *latent* and the key up-projection never runs.
  RoPE does not commute with that absorption: rotating the key's 128 nope dims would make `W_UK`
  position-dependent and unfoldable. DeepSeek's fix carves out a separate 64-dim key that carries **all**
  the positional information, is shared MQA-style across all 128 query heads, and is cached next to the
  latent. The 128 nope dims stay absorbable; the 64 rope dims are cheap to broadcast. Cost of full-rank
  positional encoding: 64/576 = 11% cache overhead. **VERIFIED** (DeepSeek-V2/V3 reports [3]).
- Head-dim asymmetry worth drawing: Q/K are 192-dim (128 nope + 64 rope) while V is 128-dim.
- `attention_bias: false`, `attention_dropout: 0.0`.

### 1.4 FFN / MoE — DeepSeekMoE, aux-loss-free, node-limited

- Layers **0–2 dense** (`first_k_dense_replace: 3`), `intermediate_size: 18432`, SwiGLU (`hidden_act: silu`).
- Layers **3–60 MoE** (`moe_layer_freq: 1`): **256 routed experts**, `num_experts_per_tok: 8`, **1 shared
  expert**, `moe_intermediate_size: 2048`.
- **Routing score.** `scoring_func: "sigmoid"` — affinity = σ(token · centroid), not a softmax over
  experts. `norm_topk_prob: true` renormalises the 8 selected gates to sum to 1; `routed_scaling_factor:
  2.5` then rescales the routed contribution before it is summed with the shared expert's.
- **Aux-loss-free load balancing** (`topk_method: "noaux_tc"`). Instead of an auxiliary balance loss (which
  injects an interference gradient into the LM objective), a **per-expert learnable bias**
  `e_score_correction_bias` is added to the affinity **for top-k selection only** and never to the gate
  value used for weighting. Training nudges the bias down for overloaded experts and up for underloaded
  ones. Balance without polluting the LM gradient. [3] **VERIFIED.** V3.1's card additionally requires this
  bias be loaded and computed in FP32 [1].
- **Node-limited (grouped) routing.** `n_group: 8`, `topk_group: 4`: the 256 experts are partitioned into 8
  groups; a token first selects its top-4 groups (each group scored by the sum of its top-2 affinities),
  then draws its 8 experts only from those. With expert parallelism mapping one group per node, a token's
  activations reach at most 4 nodes, capping all-to-all cost. [3] **VERIFIED.**

### 1.5 Other blocks

- **Norm.** RMSNorm, `rms_norm_eps: 1e-6`, pre-norm, plus the two extra RMSNorms inside MLA (on `q_latent`
  and `kv_latent`).
- **MTP.** `num_nextn_predict_layers: 1` — one Multi-Token Prediction module: an extra transformer block
  that consumes the trunk's hidden state for token *t* together with the embedding of token *t+1* and
  predicts *t+2*, sharing the embedding matrix and output head with the trunk. An auxiliary densification
  objective in training; at inference discarded or repurposed as a self-speculative draft head. [3]
  **VERIFIED.**
- **Quantisation.** Shipped FP8: `quant_method: fp8`, `fmt: e4m3`, `weight_block_size: [128,128]`
  (one scale per 128×128 weight tile), `activation_scheme: dynamic`, `scale_fmt: "ue8m0"`.
  **UE8M0** = 8-bit *unsigned exponent, zero mantissa*: the scale factor is constrained to an exact power
  of two, so applying it is an exponent add and is mantissa-lossless. This is exactly the scale encoding
  OCP microscaling (MX) formats mandate. The card states the motive verbatim — trained "using the UE8M0
  FP8 scale data format on both model weights and activations to ensure compatibility with microscaling
  data formats" [1]. **VERIFIED.**
- `tie_word_embeddings: false`; `torch_dtype: bfloat16` is the master dtype (weights ship FP8).

### 1.6 The repeating motif

```
[embed] → 3 × (MLA + dense SwiGLU FFN) → 58 × (MLA + MoE[256 routed, top-8, +1 shared])
        → RMSNorm → lm_head                  (+ 1 MTP block hanging off the trunk)
```

One pattern break (dense→MoE at layer 3); otherwise homogeneous. `derived.unclassified` is **empty** for
this rung — every field is accounted for.

---

## 2. DeepSeek-V4-Flash — the new generation, small rung

### 2.1 Identity

| | |
|---|---|
| Full name | DeepSeek-V4-Flash |
| Repo / SHA | `deepseek-ai/DeepSeek-V4-Flash` @ `60d8d70770c6776ff598c94bb586a859a38244f1` |
| Released | **2026-04-24** (vendor transparency PDF: "Release date: April 24, 2026"; doc published 2026-04-27) [4] — **VERIFIED** |
| Total / active params | **284B total, 13B activated** (arXiv abstract [5], HF card [6]). ⚠️ DeepSeek's own transparency PDF says **285B** [4] — see §5 |
| Licence | MIT [4][6] — **VERIFIED** |
| Tokenizer | Same DeepSeek BPE family, `vocab_size: 129280`, bos/eos ids 0/1 — identical to V3.1 (config) — **VERIFIED** |
| Context | 1M (`max_position_embeddings: 1048576`) |
| Paper | *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*, arXiv **2606.19348**, submitted 2026-04-26, explicitly a **preview** report [5] |
| Served here | tp=8, `max_model_len` 131072, `--attention-backend FLASHMLA_SPARSE_DSV4`, `--kv-cache-dtype fp8_ds_mla`, `--moe-backend marlin`, `--block-size 256`, `--tokenizer-mode deepseek_v4`, `--reasoning-parser deepseek_v4`, inline chat template. **Never produced results — see §5** |

Config arithmetic reproduces 284B/13B **only if every layer is MoE** (§2.4): 43 × 256 × 3·4096·2048 = 277B
routed + 1.08B shared + ~5.4B attention + 0.53B embed ≈ **284B**; active = 43 × 7 × 25.2M = 7.6B + 5.4B
attention + embed ≈ **13.5B**. **INFERRED**, and it is the load-bearing cross-check on the no-dense-prefix
reading.

### 2.2 Positional encoder — two RoPE bases and three per-layer regimes

This is the field where V4 differs most from every other model in the atlas: **positional treatment is not
uniform across layers.**

- **Main / uncompressed stream:** `rope_theta: 10000`, **partial RoPE on the last 64 of 512 dimensions**
  (`qk_rope_head_dim: 64`, `head_dim: 512`) of every query vector and of the single KV entry. The paper
  states it literally — "for each query vector and KV entry vector used in CSA and HCA, we apply RoPE to
  its last 64 dimensions" [5] — and the reference implementation matches
  (`apply_rotary_emb(q[..., -rd:], freqs_cis)`) [10]. **VERIFIED.** The other 448 dims are unrotated.
- **`compress_rope_theta: 160000`** — a second, larger RoPE base applied to the **compressed** KV stream and
  to the indexer, on every layer that has a compressor. vLLM's `deepseek_v4/common/rope.py`:
  `rope_parameters["rope_theta"] = config.compress_rope_theta if compress_ratio > 1 else config.rope_theta`
  [10]. **VERIFIED.** (The paper does not mention a second base — §5.) Arithmetic aside: 10000 × 16 =
  160000 exactly, i.e. the compressed base equals the main base times the YaRN factor; whether that is the
  design intent is **UNVERIFIED**.
- **Sliding-only layers disable YaRN entirely.** DeepSeek's reference sets
  `original_seq_len, rope_theta = 0, args.rope_theta` under the comment *"disable YaRN and use base
  rope_theta in pure sliding-window attention"* [10] — **VERIFIED**. A layer that only ever looks 128
  tokens back needs no context extension.
- **YaRN (compressed layers):** `{type: yarn, factor: 16, original_max_position_embeddings: 65536,
  beta_fast: 32, beta_slow: 1}` → 65536 × 16 = **1048576**. The base window moved from V3.1's 4096 to
  **65536**: V4 is natively long-context and YaRN only carries the final 16×. Note `mscale` /
  `mscale_all_dim` are **absent** from V4's `rope_scaling` where V3.1 pinned both to 1.0; whether the
  runtime therefore applies YaRN's default logit temperature is **UNVERIFIED**.
- **Inverse RoPE on the attention output.** Because V4 uses the same tensor as K and V (§2.3), the value
  picked up K's rotation, so the output's trailing 64 dims are counter-rotated at the query position:
  `apply_rotary_emb(o[..., -rd:], freqs_cis, True)` in the reference; HF's comment reads *"K=V in V4, so V
  picked up rope on its trailing rope slice. Apply the conjugate rotation (-sin) at the query position to
  undo it."* [10] The paper describes the same as "RoPE with position −i" [5]. **VERIFIED.** The net effect
  is that each KV entry's contribution depends only on its *relative* distance to the query. RoPE therefore
  appears **twice** in the block diagram — on the way in and on the way out.

### 2.3 Attention — hybrid CSA / HCA over a single shared KV head

This is the headline change and it is **not** MLA. V4 drops `kv_lora_rank`, `qk_nope_head_dim` and
`v_head_dim` outright; there is no key/value up-projection left to absorb.

**Shared-KV MQA.** `num_key_value_heads: 1`, `head_dim: 512`: one 512-dim KV row per token serves all 64
query heads, and **the same tensor is read as both key and value** — HF's `DeepseekV4Attention` calls
`attention_interface(self, q, kv, kv, ...)` [10]. **VERIFIED.** The 512 dims split implicitly as
`nope = 512 − 64 = 448` plus `rope = 64`. Queries remain low-rank: `q_lora_rank: 1024` down-projection →
RMSNorm → up-projection to 64 × 512; that post-norm latent `qr` is **reused as the indexer's input**.

**Sequence-axis compression by learned gated pooling — not strided subsampling.** Two projections produce
content `C = H·W^KV` and compression weights `Z = H·W^Z`; every *m* consecutive entries collapse into one
via a softmax over the window plus a **learnable per-slot positional bias** `B ∈ R^{m×c}` (`self.ape` in
the reference) [5][10]. **VERIFIED:**

```python
kv = self.wkv(x); score = self.wgate(x)
kv    = kv.unflatten(1, (-1, ratio))
score = score.unflatten(1, (-1, ratio)) + self.ape
if overlap: kv, score = self.overlap_transform(kv, 0), self.overlap_transform(score, -inf)
kv = (kv * score.softmax(dim=2)).sum(dim=2)
```

`self.overlap = compress_ratio == 4`, so **CSA windows overlap** — a compressed entry is a weighted sum of
**8** source tokens at **stride 4** — while HCA is non-overlapping (128 tokens, stride 128) [10].
**VERIFIED.**

**Three layer types, selected per layer by `compress_ratios` (§2.6).** HF transformers encodes the mapping
as a literal dict [10] — **VERIFIED**:

| value | `layer_types` name | compressor | long-range selection | KV rows held |
|---|---|---|---|---|
| `0` | `sliding_attention` | none | none — **local only** | 128 |
| `4` | `compressed_sparse_attention` (CSA) | 4:1, overlapping (8 @ stride 4) | Lightning Indexer top-`index_topk` | 128 + L/4 |
| `128` | `heavily_compressed_attention` (HCA) | 128:1, non-overlapping | none — attends **all** compressed entries densely | 128 + L/128 |

**The 128-token sliding window is unconditional and additive.** It is not a fourth layer type and not an
alternative — `sliding_window: 128` uncompressed recent entries are attended by **every** layer, and the
compressed/selected entries are **concatenated** onto them in a single sparse-attention call:
`topk_idxs = torch.cat([window_idxs, compress_topk_idxs], dim=-1)` [10]. **VERIFIED.** Compression destroys
local detail; the window restores it. `n_win = 128` is thus read directly off the config, not inferred.

**Lightning Indexer** (`index_n_heads: 64`, `index_head_dim: 128`, `index_topk: 512`). Same ReLU-weighted
multi-head scoring as DeepSeek-V3.2-Exp's DSA [7][8] —
`I_{t,s} = Σ_h w^I_{t,h} · ReLU(q^I_{t,h} · K^IComp_s)` — with three V4-specific differences [10],
**VERIFIED**:
1. It scores **compressed** entries, not raw tokens. `index_topk: 512` at m=4 selects 512 compressed
   entries ≈ **2048 source tokens** of long-range reach, on a score matrix 4× smaller than V3.2's.
2. It runs **its own private compressor** at `index_head_dim: 128`, separate from the attention's 512-dim
   compressor, with Hadamard rotation before quantisation.
3. It is **FP4 end-to-end** (`fp4_act_quant` on both q and kv; vLLM budgets 68 bytes per indexer entry
   against V3.2's 132).

**Grouped low-rank output projection.** `o_lora_rank: 1024`, `o_groups: 8`. The 64 head outputs are split
into 8 groups of 8 heads (4096 dims each), each projected independently 4096 → 1024 by a batched einsum,
and the concatenated 8×1024 then projected to `hidden_size`:
`o = einsum("bsgd,grd->bsgr", o, wo_a); x = wo_b(o.flatten(2))` [10]. **VERIFIED.** Parameters:
8·(4096×1024) + 8192×4096 ≈ **67M** vs 32768×4096 ≈ 134M dense — a 2× saving. **INFERRED (arithmetic).**
vLLM fuses this with the inverse RoPE and FP8 quantisation in one op [10].

**Attention sink.** Per-head learnable sink logits added to the softmax denominator,
`s = exp(z) / (Σ exp(z) + exp(z′_h))`, citing the GPT-OSS lineage [5]; implemented as
`nn.Parameter(torch.empty(n_local_heads))` [10]. **No config field exposes this** — flag for the diagram.

**Per-head normalisation.** An extra RMSNorm on each query head and on the single compressed-KV head
immediately before core attention, "to avoid exploding attention logits" [5]. Also no config field.

**KV cache.** The served `--kv-cache-dtype fp8_ds_mla` is V4's default layout
(`use_fp8_ds_mla_layout = True`, auto-forced by vLLM), described as UE8M0 block-scaled FP8 packed as
`uint8` with a **576-byte per-token slot** [10] — matching the paper's "BF16 … for the RoPE dimensions,
FP8 … for the remaining dimensions" (64×2 + 448×1 = 576) [5]. **VERIFIED.**

**Footprint (INFERRED arithmetic over the verified per-layer cache formula).** Amortised per token: a CSA
layer costs 1/4 row, an HCA layer 1/128 row, a sliding-only layer **zero** (its 128 rows are a constant).
Flash: 21 CSA + 20 HCA + 2 sliding-only = 21·144 B + 20·4.5 B ≈ **3.0 KB/token**, against V3.1's
61 × 576 B ≈ 34 KB/token — **~9%**, consistent with the Flash card's "10% of KV cache" and "27% of
single-token inference FLOPs" versus V3.2 [6].

### 2.4 FFN / MoE

- **No `intermediate_size`, no `first_k_dense_replace`, no `moe_layer_freq` in the config — V4 has no dense
  FFN anywhere.** All 43 layers are MoE: DeepSeek's `Block.__init__` sets `self.ffn = MoE(layer_id, args)`
  unconditionally with no dense branch in the file, and HF routes the missing name through
  `attribute_map = {"intermediate_size": "moe_intermediate_size", ...}` with the comment *"V4 only ships
  `moe_intermediate_size`"* [10]. **VERIFIED.** The parameter arithmetic in §2.1 independently closes only
  under this reading.
- **What replaced the dense prefix: `num_hash_layers: 3` — Hash-MoE bootstrap.** The first 3 MoE layers
  select experts from a **frozen token-ID lookup table**, not a learned router [5][10]. **VERIFIED:**
  ```python
  self.hash = layer_id < args.n_hash_layers
  if self.hash: self.tid2eid = nn.Parameter(..., requires_grad=False)   # [vocab, top_k] int32
  indices = self.tid2eid[input_ids] if self.hash else scores.topk(self.topk, -1)[1]
  weights = original_scores.gather(1, indices)          # weights still learned
  ```
  Selection is pure token identity (perfectly balanced by construction, zero router parameters, no
  aux-loss bias); the *weights* still come from the learned affinity score. The mapping onto V3.1's
  `first_k_dense_replace: 3` is exact — same 3 layers, different replacement. Practical consequence:
  token ids must be threaded down into the FFN, which is why vLLM raises
  `ValueError("DeepSeek V4 hash MoE routing requires input_ids.")` [10].
- **256 routed experts, `num_experts_per_tok: 6`, 1 shared expert, `moe_intermediate_size: 2048`.** Top-k
  drops 8→6 versus V3.1.
- **`scoring_func: "sqrtsoftplus"` — new.** Literally `F.softplus(scores).sqrt()` = √(log(1+e^x)) [10],
  replacing V3's sigmoid; the paper confirms the swap [5]. **VERIFIED.** Unlike sigmoid it is **unbounded
  above**, so a strongly-matched expert is not saturated toward 1.0, while the √ tempers tail growth to
  sub-linear. No ablation is published — **the motivation is UNVERIFIED.**
- **`topk_method: "noaux_tc"` retained**, but now meaning *only* the bias-corrected aux-loss-free top-k
  (bias shifts selection, never the routing weight), "augmented by a slight sequence-wise balance loss that
  prevents extreme imbalance within individual sequences" [5]. **VERIFIED.**
- **`n_group` / `topk_group` are gone — node-limited routing was dropped.** `Gate` does a flat
  `scores.topk(self.topk, dim=-1)` and vLLM falls back to `getattr(config, "n_group", 1)` [10].
  **VERIFIED.** The reason is **UNVERIFIED**.
- `norm_topk_prob: true` (renormalise the 6 gates), `routed_scaling_factor: 1.5` — Flash is the odd rung
  here; V3.1 and V4-Pro both use 2.5.
- **`expert_dtype: "fp4"` — routed experts only.** Stored as `float4_e2m1fn_x2` (`[out, in//2]`) with a
  `float8_e8m0fnu` scale per 32-element block; the **shared** expert is *not* FP4, and the top-level
  `quantization_config` remains FP8 e4m3 / UE8M0 / `[128,128]` [10]. Card: "MoE expert parameters use FP4
  precision; most other parameters use FP8" [6]. **VERIFIED.** Mixed precision *inside one checkpoint* —
  worth drawing.
- **`swiglu_limit: 10.0` — clipped SwiGLU, asymmetrically.** `hidden_act` is still `silu`, and the clamp is
  applied to the pre-activations [10]. **VERIFIED:**
  ```python
  up   = torch.clamp(up,   min=-10.0, max=10.0)   # two-sided
  gate = torch.clamp(gate,             max=10.0)  # upper only
  x = F.silu(gate) * up
  ```
  Same shape as GPT-OSS's clamped SwiGLU (whose attention-sink trick V4 also borrows). Bounds activation
  magnitude for the FP4 expert path.
- **"DeepGEMM MegaMoE"** — the entire routed-MoE layer (dispatch → grouped FP8×FP4 GEMM → clamped SwiGLU →
  second GEMM → combine) fused into one CUDA megakernel over a symmetric cross-rank buffer, called as
  `deep_gemm.fp8_fp4_mega_moe(...)` [10]; the paper announces both ("we replace it end-to-end with
  DeepGEMM"; "We have open-sourced the CUDA-based mega-kernel implementation named MegaMoE") [5].
  **VERIFIED.** It is an **opt-in** vLLM backend (`--kernel-config moe_backend=deep_gemm_mega_moe`) gated
  on `torch.cuda.get_device_capability()[0] != 10` (exactly SM100 — SM90 *and* SM120 both fail), plus
  expert parallelism, `sqrtsoftplus` routing and FP4 experts. See §5.

### 2.5 Other blocks

- **Manifold-Constrained Hyper-Connections (mHC)** — `hc_mult: 4`, `hc_sinkhorn_iters: 20`, `hc_eps: 1e-6`.
  This is the **residual stream**, not a hash or clustering component (see §5.5). The model carries
  **4 parallel residual streams end-to-end**: the embedding is expanded
  `h.unsqueeze(2).repeat(1, 1, hc_mult, 1)` and the head collapses them at the end [10]. **VERIFIED.**
  There are **two mHC sites per layer**, one wrapping attention and one wrapping the FFN:
  ```python
  residual = x
  x, post, comb = self.hc_pre(x, ...)   # 4 streams → 1, token-dependent sigmoid mix
  x = self.attn(self.attn_norm(x), ...)
  x = self.hc_post(x, residual, post, comb)   # 1 → 4, remixing the 4 old streams
  #   … identical pair around self.ffn …
  ```
  The **manifold constraint** is on the 4×4 stream-mixing matrix, which is projected onto the doubly
  stochastic matrices (the Birkhoff polytope: M·1 = 1, 1ᵀM = 1ᵀ, M ≥ 0, hence ‖B‖₂ ≤ 1 and non-amplifying
  propagation) by **Sinkhorn-Knopp**: softmax, then alternating row/column normalisation for
  `hc_sinkhorn_iters = 20` rounds, with `hc_eps = 1e-6` as the numerical floor in every denominator [10].
  The paper's `t_max = 20` matches the config exactly [5]. **VERIFIED.** Parameter shape per site:
  `(2 + hc_mult) · hc_mult = 24` mixing outputs split `pre(4) | post(4) | comb(4×4)`, plus a `[24]` base
  and a `[3]` scale. The final head collapses the 4 streams with a sigmoid gate only, no Sinkhorn.
- **Norm.** RMSNorm, `rms_norm_eps: 1e-6`, plus the per-head Q and KV RMSNorms before core attention.
- **MTP.** `num_nextn_predict_layers: 1`, "same strategy for DeepSeek-V4 series without modification" [5].
  **VERIFIED.** Its attention layer is **sliding-window-only** (§2.6).
- **Quantisation.** FP8 e4m3 / UE8M0 / `[128,128]` blocks for the trunk, FP4 for routed experts (§2.4).
- `tie_word_embeddings: false`, `torch_dtype: bfloat16`, `attention_bias: false`.
- **No chat template.** The repos ship no `chat_template` (verified in-repo 2026-08-11,
  `smolbench/evals/ec2.py:284-293`); the protocol lives in `encoding/encoding_dsv4.py` — model card: *"This
  release does not include a Jinja-format chat template."* [6] Reading the shipped module (vendored at
  `tests/fixtures/dsv4/encoding_dsv4_vendored.py`) [10] — **VERIFIED**:
  - Prompt shape: `<｜begin▁of▁sentence｜>{system}<｜User｜>{content}<｜Assistant｜>` then **`<think>` to
    enable reasoning or `</think>` to suppress it** — a prefill toggle, same idea as V3.1. There is **no
    system-role token**: system content sits bare after BOS.
  - **Three reasoning modes**, matching the vendor card's Non-think / Think High / Think Max [4]:
    `reasoning_effort ∈ {None, 'high', 'max'}`. `'max'` is not a sampling setting — it **prepends a literal
    system paragraph** (`REASONING_EFFORT_MAX`, "Reasoning Effort: Absolute maximum with no shortcuts
    permitted…") at message index 0. The card recommends ≥384K context for Think Max [6]; sampling
    `temperature = 1.0, top_p = 1.0` (matching `generation_config.json`).
  - Tool calls use a bespoke **DSML** XML dialect (`｜DSML｜` sentinel: `<｜DSML｜tool_calls>`,
    `<｜DSML｜invoke name=…>`, `<｜DSML｜parameter name=… string=…>`), replacing V3.1's
    `<｜tool▁calls▁begin｜>` token family. Tool *results* are folded into the user turn as
    `<tool_result>…</tool_result>`; a bare `role: "tool"` message raises `NotImplementedError`.
  - Roles/tokens with no V3 analogue: `developer`, `<｜latest_reminder｜>`, and six internal task sentinels
    (`<｜action｜>`, `<｜query｜>`, `<｜authority｜>`, `<｜domain｜>`, `<｜title｜>`, `<｜read_url｜>`) — an
    agent/search product protocol baked into the base model.
  - Earlier turns' reasoning is dropped by default (`drop_thinking=True`).

### 2.6 The repeating motif — two interleaved patterns

`compress_ratios` has **44 entries for 43 layers** (Pro: 62 for 61). **The trailing entry is the MTP
module.** DeepSeek's reference constructs MTP blocks with layer ids continuing past the main stack
(`MTPBlock(args.n_layers + layer_id, args)` → `self.compress_ratio = args.compress_ratios[layer_id]`), and
the shipped toy default makes it unambiguous: `n_layers = 7` with an 8-entry `compress_ratios` [10].
**VERIFIED.** Both checkpoints set that entry to `0`, so **the MTP layer is sliding-window-only**.

Flash: `[0, 0, 4, 128, 4, 128, …, 4, 0]` — layers 0–1 **sliding-only** (strictly local, 128-token
receptive field, no long-range path at all), then layers 2–42 alternate **CSA (m=4)** on even indices and
**HCA (m′=128)** on odd, closing on a CSA layer. Totals: 21 CSA, 20 HCA, 2 sliding-only, + the MTP entry.

```
[embed] → expand to 4 residual streams (mHC)
  ├ L0  : sliding-only (128 local)                     + MoE-hash   ┐
  ├ L1  : sliding-only (128 local)                     + MoE-hash   ├ hash-routed
  ├ L2  : CSA m=4, indexer top-512   ∪ 128 local       + MoE-hash   ┘   (3 layers)
  ├ L3  : HCA m'=128, dense compressed ∪ 128 local     + MoE
  ├ L4  : CSA m=4, indexer top-512   ∪ 128 local       + MoE
  │  … alternating CSA / HCA …
  └ L42 : CSA m=4, indexer top-512   ∪ 128 local       + MoE
  every residual junction (2 per layer) wrapped by mHC: 4 lanes, Sinkhorn-20
[collapse 4 → 1] → RMSNorm → lm_head        + 1 MTP block (sliding-only)
```

Two orthogonal periodicities in one stack: a **period-2 attention schedule** (CSA/HCA) and a **3-layer
hash-routed MoE prefix**. They are deliberately *not* aligned — the hash prefix (0,1,2) straddles the
sliding-only/CSA boundary.

---

## 3. DeepSeek-V4-Pro — same architecture, larger rung

Deltas from §2 only.

### 3.1 Identity

| | |
|---|---|
| Repo / SHA | `deepseek-ai/DeepSeek-V4-Pro` @ `b5968e9190ef611bbf34a7229255be88a0e937c1` |
| Released | 2026-04-24, same series [4] |
| Total / active | **1.6T total, 49B activated** [4][5][6] — **VERIFIED**, and reproduced by config arithmetic: 61 × 384 × 3·7168·3072 = 1547B routed + 4.0B shared + ~19.5B attention + 0.93B embed ≈ **1.57T**; active = 61 × 7 × 66.1M = 28.2B + 19.5B attention + embed ≈ **49B**. **INFERRED** — this is the check that (a) every layer is MoE and (b) the grouped-output-projection reading is right, since both feed the active count. |
| Licence / tokenizer / context | MIT; `vocab_size: 129280`; 1M — identical to Flash |
| Served here | as Flash plus `--gpu-memory-utilization 0.93`. Weights measured at **865 GB** (`ec2.py:389`). **Never produced results — see §5** |

### 3.2 Positional encoder

Identical to Flash in every parameter: `rope_theta 10000` + YaRN `factor 16` over `original 65536` →
1048576, partial RoPE on 64 of 512 dims, `compress_rope_theta: 160000`, inverse RoPE on the output.
**Scale does not touch positional encoding at all.** The one difference is downstream of §3.6: Pro has no
sliding-only layers, so the "YaRN disabled" regime never occurs in the main stack — it applies only to
Pro's MTP block.

### 3.3 Attention

Same CSA/HCA hybrid, same shared-KV MQA with one 512-dim row, same unconditional `sliding_window: 128`,
same indexer geometry (`index_n_heads: 64`, `index_head_dim: 128`). Deltas:

- **128 query heads** (vs 64), `hidden_size: 7168` (vs 4096), `q_lora_rank: 1536` (vs 1024).
- **`index_topk: 1024`** (vs 512) — Pro selects twice as many compressed entries, ≈4096 source tokens of
  long-range reach per query against Flash's ≈2048. The retrieval *budget* scales with model size; the
  indexer's *width* does not.
- **`o_groups: 16`** (vs 8), `o_lora_rank: 1024` (same). 128 heads / 16 groups = **8 heads per group —
  identical group width to Flash**, so `o_groups` tracks head count rather than signalling a design change
  (**INFERRED**, confirmed by both checkpoints landing on a 4096-dim per-group input). Parameters:
  16·(8·512)·1024 + (16·1024)·7168 ≈ **184M** against 469M dense — a 2.6× saving.
- KV footprint: 30 CSA · 144 B + 31 HCA · 4.5 B ≈ **4.4 KB/token**, ~13% of V3.1's ~34 KB/token despite
  Pro carrying 2.4× V3.1's total parameters. **INFERRED.**

### 3.4 FFN / MoE

- **384 routed experts** (vs 256) and `moe_intermediate_size: 3072` (vs 2048), still **top-6 + 1 shared**.
  Scale is bought with *more and wider* experts at a constant activation count. (vLLM's fused router kernel
  hardcodes `_TOPK = 6` and asserts `gating_output.shape[1] in (256, 384)` — exactly these two rungs [10].)
- `routed_scaling_factor: 2.5` (Flash 1.5; V3.1 2.5).
- Everything else identical: `sqrtsoftplus`, `noaux_tc`, no `n_group`/`topk_group`, `norm_topk_prob: true`,
  `expert_dtype: "fp4"`, `swiglu_limit: 10.0`, `num_hash_layers: 3`.

### 3.5 Other blocks

`hc_mult: 4`, `hc_sinkhorn_iters: 20`, `hc_eps: 1e-6`, `num_nextn_predict_layers: 1`, RMSNorm 1e-6,
FP8/UE8M0 trunk with FP4 routed experts — all identical to Flash. Same missing chat template, same
`encoding_dsv4.py` protocol.

### 3.6 The repeating motif

`compress_ratios` = `[128, 128, 4, 128, 4, 128, …, 4, 0]`, 62 entries for 61 layers. **Pro has no
sliding-only layers at all**: layers 0–1 are **HCA**, then 2–60 alternate CSA (even) / HCA (odd), closing
on CSA. Totals: 31 HCA, 30 CSA, + the MTP entry (`0`, sliding-only). HF transformers documents this shape
as canonical: *"V4-Pro default: 2× HCA bootstrap + interleaved CSA / HCA"* [10] — **VERIFIED.**

The single structural difference from Flash is the head of the stack: Flash's first two layers see only
128 local tokens, Pro's first two see the whole sequence at 128:1 compression. Verified from config and
from the transformers default; **the reason is UNVERIFIED.**

---

## 4. What changes across the ladder

**Scale (Flash → Pro), same generation.** Everything mechanistic is held fixed: positional scheme,
attention family, the compression ratios {4, 128}, the 128-token window, indexer width, expert top-k,
shared-expert count, hash-layer count, mHC lane count and Sinkhorn depth, MTP, `swiglu_limit`,
`expert_dtype`. What moves: `hidden_size` 4096→7168, layers 43→61, query heads 64→128, `q_lora_rank`
1024→1536, routed experts 256→384, `moe_intermediate_size` 2048→3072, `o_groups` 8→16 (at constant 8
heads/group), `index_topk` 512→1024, `routed_scaling_factor` 1.5→2.5, and the two head-of-stack layers
(sliding-only → HCA). Read as a design statement: DeepSeek scales V4 by **width + depth + expert count +
retrieval budget**, never by changing the mechanism.

**Generation (V3.1 → V4-Pro), shape-matched at 61 layers / 7168 hidden / 128 heads.**

| | V3.1 | V4-Pro |
|---|---|---|
| Attention | MLA: 512-dim latent KV + 64-dim decoupled RoPE key, dense over all tokens | CSA/HCA hybrid: sequence-**compressed** shared-KV MQA (one 512-dim row, K=V), Lightning-Indexer top-1024 on CSA layers, dense-over-compressed on HCA layers, **+128-token uncompressed window on every layer**, per-head attention sinks |
| KV per token per layer (matched FP8 layout) | 576 B, uniform | 144 B (CSA) / 4.5 B (HCA) / 0 amortised (sliding-only) |
| Output projection | dense 16384 × 7168 | grouped low-rank: 16 groups × rank 1024, fused with inverse RoPE |
| Positional | RoPE 10000 + YaRN ×40 over 4096 → 163840, uniform across layers | RoPE 10000 + YaRN ×16 over **65536** → **1048576**, **second base 160000** on the compressed stream, YaRN **disabled** on sliding-only layers, inverse RoPE on the output |
| Dense prefix | 3 dense FFN layers | **none** — 3 **hash-routed** MoE layers (`tid2eid[input_ids]`) |
| MoE routing score | sigmoid | **√(softplus(·))** |
| Routing topology | node-limited: 8 groups, top-4 groups | **dropped** — flat top-6 |
| Experts | 256, top-8, ffn 2048 | 384, top-6, ffn 3072 |
| Residual stream | single, plain pre-norm | **mHC**: 4 lanes, token-dependent mixing projected onto doubly stochastic matrices via Sinkhorn-20, two sites per layer |
| Precision | FP8 e4m3, UE8M0 scales | same trunk, **plus native FP4 routed experts** (shared expert excluded) |
| Activation | SwiGLU | SwiGLU **clamped at 10.0** (two-sided on `up`, upper-only on `gate`) |
| Chat protocol | shipped Jinja template, `<｜tool▁calls▁begin｜>` family | **no template**; Python `encoding_dsv4.py`, DSML tool markup, 3 reasoning modes, agent task sentinels |
| Unchanged | MTP ×1, RMSNorm 1e-6, vocab 129280, 1 shared expert, `noaux_tc` bias balancing, bos/eos 0/1, partial-RoPE-on-64, `silu` | ← |

The through-line: **V3 compressed the head dimension (a latent KV per token); V4 compresses the sequence
dimension (fewer KV entries) and adds selection (indexer) plus a locality patch (sliding window).** MLA
made each token's KV small; CSA/HCA makes the *number* of KV entries small. V4 chose not to stack both —
its KV row is a plain 512-dim vector with no up-projection to absorb, which is why the MLA-specific fields
vanish from the config.

---

## 5. Serving status, contradictions, and unexplained fields

### 5.1 Serving status (footnote — does not affect the architecture above)

Neither V4 rung produced results in this study. **The task brief handed me a closed root cause that this
repo's own current state contradicts.** The brief states the failure is closed as
`vllm/models/deepseek_v4/nvidia/model.py` raising `NotImplementedError("DeepGEMM MegaMoE requires SM100
GPUs.")`, i.e. V4's FP4 expert path being Blackwell-only against an 8×H200 (SM90) envelope.
`smolbench/evals/ec2.py:379-396` (comment dated 2026-08-12, commit `28fac794` *"SM100 claim refuted — pin
DeepSeek-V4's official SM90 path"*) records an adversarial re-read of vLLM v0.27.1 concluding that closure
was **also wrong**.

Independent source reading confirms the repo's newer position [10]: the raise lives in
`_check_runtime_supported` behind `use_mega_moe`, i.e. the **opt-in** `--kernel-config
moe_backend=deep_gemm_mega_moe`, alongside three further opt-in gates (expert parallelism required,
`sqrtsoftplus` only, FP4 experts only), and the fallback `FusedMoEFactory` path "runs anywhere". The study
passed `--moe-backend marlin`, never the mega-MoE backend, so this raise cannot have been the crash. The
gate is `torch.cuda.get_device_capability()[0] != 10` — exactly SM100; SM90 *and* SM120 both fail it.
**Per the repo, the actual crash cause remains UNDIAGNOSED.** I report both positions and did not
re-investigate, per instruction.

### 5.2 Contradictions found

1. **Flash parameter count: 284B vs 285B.** arXiv 2606.19348's abstract and the HF card say 284B [5][6];
   DeepSeek's own transparency PDF says 285B [4]. Vendor-internal disagreement.
2. **`compress_rope_theta` is in the config and the implementations but not in the paper.** Paper §2.3.3
   describes partial RoPE with no separate base for compressed entries [5]; vLLM selects it explicitly for
   any layer with `compress_ratio > 1` [10]. Code wins; the paper is incomplete.
3. **vLLM and DeepSeek's reference disagree about how MTP reads `compress_ratios`** — DeepSeek indexes
   `compress_ratios[n_layers]` for the MTP block; vLLM comments *"MTP layer is not included in the compress
   ratio list"* and hardcodes 1. Numerically harmless (the trailing entry is 0 and vLLM's `max(1, ·)` folds
   0→1, both yielding sliding-only), but note the polarity flip: **in vLLM, `compress_ratio == 1` means "no
   compressor"; in DeepSeek's code, `0` does.** [10]
4. **The vLLM release blog claims HCA layers use a "default k = 8192"**, contradicting the reference
   implementation where ratio-128 layers have **no indexer** and attend all compressed entries [10]. Code
   treated as authoritative; the blog line is **UNVERIFIED**.
5. **A community blog [9] states "8×H100-80GB minimum" for V4-Pro.** Not credible: 1.6T parameters with FP4
   experts is ~800 GB of weights against 640 GB of HBM, and this repo measured Pro's weights at 865 GB
   (`ec2.py:389`). Cited only because the same post independently corroborates the `compress_ratios`
   reading ("Layers 0–1 use HCA exclusively. Layers 2–60 alternate CSA and HCA"), which matches V4-Pro's
   array exactly. Lead-tier, not evidence.
6. **The atlas brief's premise that `num_hash_layers` + `hc_*` form one "hash/Sinkhorn clustering"
   component is wrong.** They are two independent blocks in different parts of the layer: `num_hash_layers`
   is the MoE **router** (frozen token-ID→expert table for the first 3 layers), `hc_*` is the **residual
   stream** (manifold-constrained hyper-connections, Sinkhorn-projected mixing). No config field encodes a
   clustering component. Both are §2.4 and §2.5 respectively — do not draw them as one block.

### 5.3 `derived.unclassified` — all fields now explained

The fetcher flagged ten fields on both V4 rungs. Every one is resolved above: `compress_ratios` (§2.6),
`compress_rope_theta` (§2.2), `expert_dtype` (§2.4), `hc_eps` / `hc_mult` / `hc_sinkhorn_iters` (§2.5),
`num_hash_layers` (§2.4), `o_groups` / `o_lora_rank` (§2.3), `swiglu_limit` (§2.4). V3.1's
`unclassified` was already empty.

### 5.4 What I still could not establish

- **Architectural elements with no config field at all** — they must be drawn from the paper, not the JSON:
  per-head learnable **attention-sink logits**; the per-head **Q and KV RMSNorms** before core attention;
  the **inverse RoPE** on the attention output; `hc_post_alpha = 2.0`, which appears hardcoded in vLLM with
  no config field and no paper reference [10].
- **Why `mscale` / `mscale_all_dim` are absent from V4's `rope_scaling`** where V3.1 pinned both to 1.0,
  and whether the runtime therefore applies YaRN's default logit temperature. **UNVERIFIED.**
- **Why node-limited routing was dropped.** **UNVERIFIED.**
- **Why Flash keeps two sliding-only head-of-stack layers where Pro uses HCA.** **UNVERIFIED.**
- **Why the routing score changed to √softplus**, and why `routed_scaling_factor` differs between the two
  V4 rungs (1.5 vs 2.5). No ablation published. **UNVERIFIED.**
- **Provenance caveat on the paper quotations.** The V4 paper body was read through arXiv's HTML
  rendering (summarised, not transcribed byte-for-byte) plus a delegated reader's quotation of the
  transformers docstrings that cite it; the PDF was not parsed. Machine summarisation of long papers is
  known to invent numbers, so **no numeric value in this brief rests on a paper paraphrase**: every one
  comes from the config or from a reference implementation, and the published 284B/13B and 1.6T/49B counts
  were independently reconstructed from the config to within ~1% (§2.1, §3.1). The paper's role here is
  restricted to supplying mechanism *names* and qualitative formulations, each of which is separately
  corroborated by code. The V4 report is an explicit *preview* and ships **no hyperparameter table** at
  all, so it could not have supplied numbers in any case.

## Sources

1. DeepSeek-V3.1 model card — https://huggingface.co/deepseek-ai/DeepSeek-V3.1
2. DeepSeek-V3.1 Release, DeepSeek API Docs — https://api-docs.deepseek.com/news/news250821/
3. DeepSeek-AI, *DeepSeek-V3 Technical Report*, arXiv:2412.19437 — https://arxiv.org/abs/2412.19437
4. *DeepSeek V4 Technical Documentation* (vendor transparency PDF, published 2026-04-27) —
   https://fe-static.deepseek.com/chat/transparency/deepseek-V4-model-card-EN.pdf
5. DeepSeek-AI, *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*,
   arXiv:2606.19348 (2026-04-26) — https://arxiv.org/abs/2606.19348 · HTML: https://arxiv.org/html/2606.19348v1
6. DeepSeek-V4 model cards — https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash ·
   https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro
7. DeepSeek-AI, *DeepSeek-V3.2*, arXiv:2512.02556 — https://arxiv.org/abs/2512.02556 (DSA lightning
   indexer: `I_{t,s} = Σ_j w^I_{t,j}·ReLU(q^I_{t,j}·k^I_s)`, top-2048 raw tokens, MQA-mode MLA)
8. DeepSeek-V3.2-Exp — https://github.com/deepseek-ai/DeepSeek-V3.2-Exp
9. *DeepSeek V4 GA: Architecture, Inference Efficiency* — community blog, **lead-tier and partly
   unreliable, see §5.2.5** — https://huggingface.co/blog/ResterChed/deepseek-v4-ga-architecture
10. **Reference implementations** (read directly; the authority for every mechanism claim above):
    - DeepSeek's own inference code — https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/raw/main/inference/model.py
    - DeepSeek's chat encoder — https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash/raw/main/encoding/encoding_dsv4.py
      (vendored in-repo at `tests/fixtures/dsv4/encoding_dsv4_vendored.py`)
    - vLLM `deepseek_v4` package — `vllm/models/deepseek_v4/{nvidia/model.py, attention.py, compressor.py,
      sparse_mla.py, common/rope.py, nvidia/ops/o_proj.py}`;
      `vllm/model_executor/kernels/mhc/torch.py`; `vllm/model_executor/layers/fused_moe/router/dsv4_topk.py`
      — https://github.com/vllm-project/vllm
    - HF transformers — `src/transformers/models/deepseek_v4/{configuration_deepseek_v4.py,
      modular_deepseek_v4.py}` — https://github.com/huggingface/transformers
11. In-repo: `smolbench/evals/ec2.py:284-408`; `scripts/arch/arch_configs_raw.json`;
    `scripts/arch/arch_facts.json`.
