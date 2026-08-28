# EXAONE family (LG AI Research, KR) — architecture brief

**Scope.** Three rungs of the SmolBench family ladder, deliberately cross-generation:
`exaone-4.0-32b` (July 2025), `k-exaone-236b-a23b` (Dec 2025), `exaone-4.5-33b` (Apr 2026).
Ground truth is `scripts/arch/arch_configs_raw.json` / `arch_facts.json` (fetched
2026-08-12T01:18:07Z, commit SHAs below). Everything else is cited.

**Verification convention.** `VERIFIED` = read in a config field, a checkpoint tensor
index, or a source line I actually read. `INFERRED` = my reasoning over verified facts.
`UNVERIFIED` = asserted by a source I could not cross-check.

**The one-sentence family signature.** All three rungs are the *same* attention design:
a 3:1 local/global hybrid (`LLLG`) in which **RoPE runs only on the sliding-window layers
and the global layers carry no positional encoding at all (NoPE)**, with per-head RMSNorm
on Q and K. The rungs differ in what surrounds that: norm placement, FFN sparsity, window
size, tokenizer, and the presence of an MTP head.

---

## 0. Sources

| # | Source | What it establishes |
|---|---|---|
| [1] | `LGAI-EXAONE/EXAONE-4.0-32B` `config.json` @ `a1d54d1c148c30881ed27e035b650da489b51b92` (in `arch_configs_raw.json`) | 4.0 config ground truth |
| [2] | `LGAI-EXAONE/EXAONE-4.5-33B` `config.json` @ `570aa4b15a4f45ba1133072b45f50198f6e3b4fd` | 4.5 config ground truth |
| [3] | `LGAI-EXAONE/K-EXAONE-236B-A23B` `config.json` @ `61e6d578eb102b578e5704e2916ac841df9eca0a` | K-EXAONE config ground truth |
| [4] | EXAONE 4.0 tech report, arXiv 2507.11407 — https://arxiv.org/html/2507.11407 | hybrid attention, QK-Reorder-Norm, NoPE, shapes, licence |
| [5] | K-EXAONE tech report, arXiv 2601.01739 — https://arxiv.org/html/2601.01739v2 | MoE routing, window 4096→128, SuperBPE, MTP, Muon/FP8 |
| [6] | EXAONE 4.5 tech report, arXiv 2604.08644 — https://arxiv.org/html/2604.08644v1 | VLM framing, 1D RoPE retained, 256K via SFT-stage extension |
| [7] | Model cards: https://huggingface.co/LGAI-EXAONE/EXAONE-4.0-32B , `.../EXAONE-4.5-33B` , `.../K-EXAONE-236B-A23B` (README.md, fetched 2026-08-12) | vendor config blocks, NoPE statement, licences, serving recipes |
| [8] | `transformers` `models/exaone4/modular_exaone4.py`, `models/exaone_moe/{modular,modeling}_exaone_moe.py`, `models/exaone4_5/configuration_exaone4_5.py` (main, fetched 2026-08-12) — https://github.com/huggingface/transformers/tree/main/src/transformers/models | per-layer RoPE gating, QK-norm, router maths, norm placement |
| [9] | vLLM `model_executor/models/{exaone4,exaone4_5,exaone4_5_mtp,exaone_moe,exaone_moe_mtp}.py` and `config/model.py` (main, fetched 2026-08-12) — https://github.com/vllm-project/vllm/tree/main/vllm/model_executor/models | what actually served the study: `sliding_windows` array, MTP gating, sampling defaults |
| [10] | `model.safetensors.index.json` for all three repos | parameter *names* and exact totals — settles norm placement independently of any prose |
| [11] | `chat_template.jinja` + `tokenizer.json` for all three repos | `enable_thinking` defaults, think-token ids |
| [12] | LG press release, 2026-04-09 — https://www.prnewswire.com/news-releases/lg-reveals-next-gen-multimodal-ai-exaone-4-5-302736993.html | 4.5 announcement date, 1.2B vision encoder |

**Parameter counts are not guessed.** For each rung I reconstructed the parameter count
analytically from the config shapes and checked it against `metadata.total_size` in the
safetensors index (bf16, 2 bytes/param). All three reconcile **exactly**, to the parameter:

| rung | analytic total | `total_size / 2` |
|---|---|---|
| 4.0-32B | 32,003,216,384 | 32,003,216,384 |
| 4.5-33B | 34,350,097,664 | 34,350,097,664 |
| K-EXAONE | 237,099,669,632 | 237,099,669,632 |

`VERIFIED` [1][2][3][10].

---

## 1. EXAONE-4.0-32B

### 1.1 Identity

- **Full name** EXAONE 4.0 32B. Vendor **LG AI Research** (LG Management Development
  Institute is the licensor). Repo `LGAI-EXAONE/EXAONE-4.0-32B` @ `a1d54d1…`.
- **Release** HF repo created **2025-07-11**; tech report arXiv 2507.11407, July 2025.
  `VERIFIED` (HF repo API `createdAt`) [4][7].
- **Parameters** 32.00 B total, all active (dense). Card states "30.95 B without
  embeddings"; my reconstruction gives 30,954,640,384. `VERIFIED` [7][10].
- **Licence EXAONE AI Model License Agreement 1.2 – NC — non-commercial.** `VERIFIED` [7].
- **Tokenizer** BBPE, `tokenizer_class: GPT2Tokenizer`, **vocab 102,400**, untied
  embeddings (`tie_word_embeddings: false`). BOS `[BOS]`=1, EOS `[|endofturn|]`=361,
  PAD `[PAD]`=0. `<think>`=356 / `</think>`=355 are *special added tokens*.
  `VERIFIED` [1][11].
- **dtype** bf16, no quantisation config. Served tp=4 at `max_model_len=131072` (= native).

### 1.2 Positional encoder — *per layer type*

This is the crux of the whole family.

| layer type | count | positional treatment |
|---|---|---|
| `sliding_attention` (window 4096) | 48 | **RoPE**, θ = 1e6, llama3-scaled |
| `full_attention` | 16 | **NoPE — no positional encoding at all** |

`VERIFIED` in the implementation, not inferred. `transformers`:

```python
cos, sin = position_embeddings
# We use global NoPE for hybrid attention model
if self.sliding_window is None or self.is_sliding:
    query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)
```
(`modular_exaone4.py`, `Exaone4Attention.forward`) [8]. vLLM mirrors it in `exaone4.py`:
`self.sliding_window = config.sliding_window if is_sliding else None`, then
`if self.sliding_window or self.apply_rope_all_layers: q, k = self.rotary_emb(...)`, where
`apply_rope_all_layers` is `"sliding_attention" not in config.layer_types`, i.e. False
here [9]. The 4.0 model card says it in prose: *"We do not use RoPE … for global
attention for better global context understanding"* [7]; the tech report repeats it [4].

**RoPE parameters.** A *single* rotary embedding is built for the whole stack (an
`Exaone4RotaryEmbedding`, subclassing Gemma-2's) — there is **no separate local/global
theta** the way Gemma-3 has `rope_local_base_freq`; there is simply one θ that the global
layers never consume. `rope_theta: 1000000`, `rope_scaling: {rope_type: "llama3",
factor: 16.0, low_freq_factor: 1.0, high_freq_factor: 4.0,
original_max_position_embeddings: 8192}`, `max_position_embeddings: 131072` = 16 × 8192
exactly. `VERIFIED` [1][8].

**How llama3 band scaling works here (computed, not recalled).** With head_dim 128 there
are 64 frequency bands, band *i* having wavelength λᵢ = 2π·(1e6)^(i/64), from 6.28 tokens
up to 5.06 M tokens. llama3 scaling splits them at two thresholds derived from
`original_max_position_embeddings`:

- λ < orig/high_freq_factor = 8192/4 = **2048** → **left untouched**: bands *i* = 0…26 (**27 bands**).
- λ > orig/low_freq_factor = 8192/1 = **8192** → **inverse frequency divided by `factor`=16**
  (full interpolation, the band is stretched 16×): bands *i* = 34…63 (**30 bands**).
- 2048 ≤ λ ≤ 8192 → **smooth ramp** between the two regimes: bands *i* = 27…33 (**7 bands**).

So the high-frequency (short-wavelength) half of the spectrum, which encodes fine local
offsets, is preserved bit-for-bit; the low-frequency half, which would otherwise run off
the end of the trained position range, is interpolated. `VERIFIED` (computed from the
config values against the HF `llama3` rope-init rule).

**INFERRED, and the reason the rest of the ladder can drop scaling entirely:** because
RoPE only ever runs on a 4096-token windowed layer, the *largest relative offset any RoPE
dot-product ever sees is the window size*, not the context length. Positional
extrapolation past 4096 is structurally impossible in this design — the global layers
handle long-range mixing and they are position-blind. The llama3 scaling in 4.0 is
therefore a leftover of the staged 4K→32K→128K context-extension recipe [4] rather than
a load-bearing long-context mechanism.

### 1.3 Attention

- **GQA** 40 query heads / 8 KV heads (ratio 5:1), `head_dim: 128`. Note q_proj is square
  here: 40 × 128 = 5120 = `hidden_size`.
- **No attention bias** (`attention_bias` absent → False in both implementations); the
  checkpoint contains no `self_attn.*.bias` tensors. `VERIFIED` [9][10].
- **QK-norm**: `self_attn.q_norm` / `k_norm`, RMSNorm over **head_dim = 128** (not over the
  full projection), applied after projection+reshape and **before** RoPE. `VERIFIED`
  (tensors present in the index; code order in `Exaone4Attention.forward`) [8][10].
- **Interleave** `sliding_window_pattern: "LLLG"`, materialised in `layer_types` as
  `[S,S,S,F] × 16` over 64 layers: 48 sliding + 16 full. Last layer is global.
- **KV-cache footprint** 8 KV heads × 128 dim × 2 (K and V) × 2 bytes = **4 KiB per token
  per layer**. Global layers are uncapped: 16 × 131072 × 4 KiB = **8.0 GiB** per 131k
  sequence. Sliding layers are capped by the window: 48 × 4096 × 4 KiB = **0.75 GiB**,
  flat regardless of context. Total ≈ **8.75 GiB** vs **32 GiB** if all 64 layers were
  global — a 3.7× reduction. `INFERRED` (arithmetic over verified shapes).
  `generation_config` sets `cache_implementation: "hybrid"` [1].

### 1.4 FFN

Dense SwiGLU, `hidden_act: silu`, `intermediate_size: 27392` (gate/up/down), every layer.
No MoE fields anywhere in the config. `VERIFIED` [1][10].

### 1.5 Other blocks — norm placement (**QK-Reorder-Norm**)

The checkpoint settles this without needing the paper. Per-layer tensors are:

```
model.layers.N.post_attention_layernorm.weight
model.layers.N.post_feedforward_layernorm.weight
model.layers.N.self_attn.{q_norm,k_norm}.weight
```

There is **no `input_layernorm`**. That is the OLMo-2 arrangement — normalisation applied
to the *output* of each sublayer, inside the residual branch:

```
h  = x + post_attention_layernorm(Attn(x))
y  = h + post_feedforward_layernorm(MLP(h))
```

which is exactly what LG calls **QK-Reorder-Norm**: *"we reorder the LayerNorm position
from the traditional Pre-LN scheme by applying LayerNorm directly to the attention and MLP
outputs, and we add RMS normalization right after the Q and K projection"* [7], matching
the report's "QK-Reorder-LN" [4]. `transformers` implements it by deriving
`Exaone4DecoderLayer` from `Olmo2DecoderLayer` [8]. All norms are RMSNorm, `eps 1e-5`;
one final `model.norm`. `VERIFIED` [4][7][8][10].

No MTP head, no embedding tying, no quantisation.

### 1.6 The repeating motif

```
[ SWA(win=4096, RoPE θ=1e6 llama3×16) + SwiGLU-27392 ] ×3
[ FULL(NoPE)                         + SwiGLU-27392 ] ×1
                                                       ← repeat ×16 = 64 layers
```
Each block internally: `x → Attn(QK-RMSNorm) → post_attention_layernorm → +residual →
MLP → post_feedforward_layernorm → +residual`.

---

## 2. EXAONE-4.5-33B

### 2.1 Identity

- **Full name** EXAONE 4.5 33B — LG's first open-weight vision-language model.
  Repo `LGAI-EXAONE/EXAONE-4.5-33B` @ `570aa4b1…`, architecture class
  `Exaone4_5_ForConditionalGeneration`, `model_type: exaone4_5`.
- **Release** HF repo created **2026-04-04**; announced **2026-04-09**; tech report
  arXiv 2604.08644. `VERIFIED` [7][12][6].
- **Parameters** 34.35 B total in the checkpoint, decomposing exactly as:
  embed 786,432,000 + lm_head 786,432,000 + 64 layers 30,954,635,264 + final norm 5,120 +
  **MTP 536,110,336** + **vision tower 1,286,482,944** = 34,350,097,664. `VERIFIED` [2][10].
  The card's "1.29 B vision encoder" matches to three digits; its "31.7 B language model"
  does **not** match any natural grouping except *64 layers + one embedding matrix*
  (31,741,067,264) — see §5. Active = all (dense).
- **Licence EXAONE AI Model License Agreement 1.2 – NC — non-commercial**, same as 4.0.
  `VERIFIED` [7].
- **Tokenizer** the K-EXAONE tokenizer, **vocab 153,600**, untied. New special-token
  syntax vs 4.0: EOS `<|endofturn|>`=53, roles `<|system|>`=50/`<|user|>`=51/
  `<|assistant|>`=52, `<think>`=54, `</think>`=55. `VERIFIED` [2][11].
- Served tp=4 at `max_model_len=131072` with `--language-model-only`, i.e. the vision
  tower was never loaded for this study.

### 2.2 Positional encoder

**Text stack: identical scheme to 4.0** — `layer_types` is byte-identical (`[S,S,S,F] × 16`),
`sliding_window: 4096`, RoPE on sliding layers only, **NoPE on the 16 global layers**. The
model card states it outright: *"Global Attention … No Rotary Positional Embedding Used
(NoPE)"* [7]. `VERIFIED` [2][7][8].

**Serialization difference, not an architecture difference.** 4.0 writes
`rope_theta: 1e6` at top level plus a `rope_scaling` dict (transformers 4.54 style). 4.5
writes `rope_scaling: {rope_type: "llama3", factor: 16.0, low_freq_factor: 1.0,
high_freq_factor: 4.0, original_max_position_embeddings: 8192, rope_theta: 1000000.0}` —
θ *nested inside* the dict, which is the transformers-v5 `rope_parameters` container
(`transformers_version: 5.3.0.dev0`). Same numbers, same band split as §1.2
(27 untouched / 7 ramp / 30 scaled). `VERIFIED` [2][8].

**Contradiction to report:** `max_position_embeddings: 262144`, but llama3 `factor 16` ×
`original_max_position_embeddings 8192` = **131072**. The declared window is 2× what the
RoPE scaling nominally supports. The report says 256K was reached by *"integrating context
extension directly into the SFT stage"* with context parallelism [6] rather than by
enlarging the scaling factor — and per §1.2 the scaling factor is not what carries long
context here anyway. Reported as a config/scaling mismatch, not smoothed over.

Vision tower uses **2D RoPE** over patch coordinates, separate from the text RoPE; the text
side keeps *"standard 1D RoPE"* [6][7]. There is no M-RoPE / `mrope_section` anywhere in
the config or in vLLM's `exaone4_5.py`. `VERIFIED` [2][9].

### 2.3 Attention

Text stack is shape-identical to 4.0: 40 Q / 8 KV heads, GQA 5:1, head_dim 128 (implicit —
`head_dim` is *absent* from `text_config`, so both implementations fall back to
`hidden_size // num_attention_heads` = 5120/40 = 128), no bias, per-head QK-RMSNorm,
`LLLG` with window 4096. Same 4 KiB/token/layer KV; at the served 131072 that is again
≈8.0 GiB global + 0.75 GiB windowed. `VERIFIED` [2][10].

### 2.4 FFN

Dense SwiGLU `27392`, silu, every layer. No MoE. `VERIFIED` [2][10].

### 2.5 Other blocks

**Norms — still QK-Reorder-Norm.** The index shows `post_attention_layernorm` +
`post_feedforward_layernorm` and **no `input_layernorm`** on all 64 layers (and on the MTP
layer). The card names it: *"Reordered Norm: Apply normalization after Attention/MLP, and
before residual connection"* [7]. `VERIFIED` [7][10].

**MTP head — present in the weights, inert in this study.** Config:
`num_nextn_predict_layers: 1`, `mtp_share_layers: true`, `mtp_loss_scaling_factor: 0.05`.
Checkpoint tensors: `mtp.pre_fc_norm_embedding`, `mtp.pre_fc_norm_hidden`, `mtp.fc`
(10240→5120), `mtp.layers.0.*` (a full decoder layer, post-norm like the main stack, with
its own QK-norms), `mtp.norm`. This is the DeepSeek-V3 MTP shape: normalise the embedding
of token *t+1* and the final hidden state of token *t*, concatenate, project 2h→h, run one
transformer layer, normalise, and reuse the **shared** `lm_head` and `embed_tokens` — there
are no `mtp.embed_tokens` / `mtp.lm_head` tensors, which is presumably what
`mtp_share_layers: true` records. `VERIFIED` for the structure [2][9][10];
`INFERRED` for the meaning of `mtp_share_layers` (see §5 — no implementation reads it).

Inference-active? **No, not as served.** vLLM only instantiates `Exaone4_5_MTP` under
`--speculative-config '{"method":"mtp",...}'`; the card's own recipe additionally requires
`--no-enable-prefix-caching`. The study passed neither (it passed `--enable-prefix-caching`),
so the MTP weights sat unused. `transformers` goes further and drops them at load
(`_keys_to_ignore_on_load_unexpected = [r"mtp.*"]`). `VERIFIED` [7][8][9].

**Vision tower (`vision_config`, `model.visual.*`).** Not loaded in this study, described
for completeness. A Qwen2.5-VL-shaped ViT — vLLM literally subclasses it
(`EXAONE4_5_VisionTransformer(Qwen2_5_VisionTransformer)`,
`Exaone4_5_ForConditionalGeneration(Qwen2_5_VLForConditionalGeneration)`) [9]:

- depth **28** blocks, hidden **2048**, FFN **5120** SwiGLU **with bias**, act silu;
- **GQA 32 Q heads / 8 KV heads**, head_dim 64; qkv and proj carry **bias** (unlike the
  text stack);
- patch **14**, `temporal_patch_size` **2** (Conv3d patch embed, so images and video share
  a path), `spatial_merge_size` **2**, `tokens_per_second` 2;
- **window attention** with `window_size: 112` (= 8×14 px), except
  `fullatt_block_indexes: [6, 13, 20, 27]` which are full-attention blocks — i.e. 4 global
  blocks among 28, the same local/global idea as the text stack;
- **pre-norm** RMSNorm (`norm1`/`norm2`, eps 1e-6) — note this is the *opposite* placement
  from the text stack;
- merger `ln_q` + 2-layer MLP → `out_hidden_size: 5120` (matches text hidden).
- Vision placeholders: `<vision>`=73 / `</vision>`=74 wrap `<|image_pad|>`=67 or
  `<|video_pad|>`=68. `VERIFIED` [2][9][10][11].

**Sampling defaults.** `generation_config.json` ships `temperature 1.0`, `top_p 0.95`,
`presence_penalty 1.5`. vLLM's default `--generation-config auto` applies model defaults
for `repetition_penalty, temperature, top_k, top_p, min_p, max_new_tokens` **only** —
`presence_penalty` is not on that whitelist, so the 1.5 is silently ignored under vLLM
(it would apply under HF `generate`). `VERIFIED` (`vllm/config/model.py`,
`get_diff_sampling_param`) [9].

### 2.6 The repeating motif

```
[ SWA(win=4096, RoPE θ=1e6 llama3×16) + SwiGLU-27392 ] ×3
[ FULL(NoPE)                         + SwiGLU-27392 ] ×1
                                                       ← repeat ×16 = 64 layers
+ 1 MTP block (shared embed/lm_head → 2 norms → fc 2h→h → 1 post-norm decoder layer → norm)
+ (unloaded here) 28-block window-attention ViT, 4 full blocks, 2D RoPE, → merger → 5120
```

---

## 3. K-EXAONE-236B-A23B

### 3.1 Identity

- **Full name** K-EXAONE 236B-A23B — LG's Korean sovereign-AI model. Repo
  `LGAI-EXAONE/K-EXAONE-236B-A23B` @ `61e6d578…`, class `ExaoneMoeForCausalLM`,
  `model_type: exaone_moe`, `transformers_version: 5.1.0`.
- **Release** HF repo created **2025-12-26**; tech report arXiv 2601.01739 (Jan 2026).
  `VERIFIED` [7][5].
- **Parameters 236 B total / ~23 B active.** Reconstructed: main model 236,571,156,352 +
  MTP 528,513,280 = 237,099,669,632, matching the index exactly. Without embeddings:
  234.68 B (card: "234 B"). Active per token = attention 5.436 B + layer-0 dense FFN
  0.340 B + 47 × (8 routed + 1 shared experts + router) 16.005 B + lm_head 0.944 B ≈
  **22.72 B**, excluding the embedding table — i.e. the "A23B" name. `VERIFIED`/`INFERRED`
  (arithmetic) [3][7][10].
- **Licence: K-EXAONE AI Model License Agreement — permits commercial *and*
  non-commercial use** (redistribution to third parties for commercial purposes needs a
  separate agreement). **This rung is not NC**, unlike 4.0 and 4.5. `VERIFIED` (LICENSE
  file text, "…for commercial and non-commercial purposes") [7].
- **Tokenizer** the same 153,600-entry SuperBPE tokenizer as 4.5 (same ids: EOS 53,
  `<think>` 54, `</think>` 55). Report: vocabulary redesigned 100k→150k, ~20% superword
  tokens in a 2:3:1 English:Korean:multilingual split, NFKC→**NFC** normalisation, ~30%
  better bytes-per-token than EXAONE 4.0 [5]. `VERIFIED` for ids [11]; report claims
  `UNVERIFIED` beyond the vocab size.
- Served tp=8 at `max_model_len=131072` (native 262144, down-capped by the study's uniform
  window).

### 3.2 Positional encoder

`rope_parameters: {rope_type: "default", rope_theta: 1000000}` — **no scaling of any kind**
at `max_position_embeddings: 262144`. `VERIFIED` [3].

Layer treatment is the family scheme, unchanged: `ExaoneMoeAttention` is a bare subclass of
`Exaone4Attention` [8], so **RoPE on sliding layers, NoPE on global layers**. vLLM's
`exaone_moe.py` gates it as `if self.sliding_window_size or self.apply_rope_all_layers:` —
and since `sliding_windows[i] == 0` on global layers, `0` is falsy and RoPE is skipped [9].
The model card states it: *"Global Attention … No Rotary Positional Embedding Used
(NoPE)"* [7]. The K-EXAONE report says RoPE is applied *"only to SWA layers, preventing
interference with global token interactions"* [5]. `VERIFIED`.

**Why no scaling is needed at 256K (this is the payoff of the NoPE design).** `INFERRED`,
but tightly: RoPE's dot product depends only on relative offset, and here RoPE exists only
on layers whose mask caps the relative offset at **128 tokens**. No RoPE frequency in the
model is ever evaluated at an offset it was not trained on, no matter how long the context.
Length generalisation is carried entirely by the position-blind global layers. Dropping
llama3 scaling between 4.5 and K-EXAONE is therefore not a regression — it is the design
finally admitting that the scaling was never doing the work.

### 3.3 Attention — the 128-token window

**Verified from the raw config**, both ways it is expressed:

- scalar `sliding_window: 128` (vs 4096 on the other two rungs);
- explicit per-layer `sliding_windows: [128,128,128,0, 128,128,128,0, …]`, 48 entries,
  with `0` on exactly the 12 positions where `layer_types` says `full_attention`.

**The `0` reading is confirmed**, and it is load-bearing in the stack that served the study:
vLLM does `self.sliding_window_size = config.sliding_windows[layer_idx]`, then
`if config.layer_types[layer_idx] == "full_attention": self.sliding_window_size = None`,
then passes `per_layer_sliding_window=self.sliding_window_size` to `Attention` and uses the
same variable to gate RoPE. So `0` means "global, and NoPE" [9]. HF `transformers` does not
read the array at all — `ExaoneMoeConfig` never declares `sliding_windows`, and
`Exaone4Attention` uses the scalar plus `layer_types`, which is numerically equivalent [8].

The report's stated motive: the window was *"reduced from 4,096 to 128"* for inference
efficiency [5]; the card frames it as *"a 128-token sliding window to significantly
minimize memory usage during long-document processing"* [7].

- **GQA** 64 Q heads / 8 KV heads (ratio **8:1**), `head_dim: 128`. Note 64 × 128 = **8192
  ≠ hidden_size 6144**: q_proj is 6144→8192 and o_proj is 8192→6144, i.e. **non-square**
  attention projections — the attention operates in a wider space than the residual stream.
  This is a genuine difference from 4.0/4.5, where 40 × 128 = 5120 = hidden. `VERIFIED` [3][10].
- **No attention bias.** `VERIFIED` [9][10].
- **QK-norm** retained: `self_attn.q_norm` / `k_norm`, RMSNorm over head_dim 128,
  before RoPE. `VERIFIED` [8][9][10].
- **KV-cache footprint** 4 KiB/token/layer. Global: 12 × 4 KiB = 48 KiB/token → **12.0 GiB**
  at 262144, **6.0 GiB** at the served 131072. Sliding: 36 × 128 × 4 KiB = **18 MiB**,
  flat. Total at 256K ≈ **12.02 GiB** vs 48 GiB for an all-global 48-layer stack — a 4×
  reduction, and the windowed half of the model contributes essentially nothing.
  `INFERRED` (arithmetic).

### 3.4 FFN / MoE

- **Layer 0 dense**, layers 1–47 sparse. Both `first_k_dense_replace: 1` and the explicit
  `mlp_layer_types: ["dense", "sparse" × 47]` say so; `is_moe_layer` says it a third time.
  HF prioritises `mlp_layer_types` over `first_k_dense_replace` [8]; vLLM reads
  `mlp_layer_types` [9]. The dense layer uses `intermediate_size: 18432`.
  The checkpoint agrees: exactly one `model.layers.N.mlp.{gate,up,down}_proj` and 47 sets
  of `mlp.experts.*`. `VERIFIED` [3][8][9][10].
- **Fine-grained MoE**: `num_experts: 128`, `num_experts_per_tok: 8`,
  `num_shared_experts: 1`, `moe_intermediate_size: 2048`. The shared expert is a single MLP
  of width `moe_intermediate_size × num_shared_experts` = 2048, added **un-gated** to the
  routed output. Expert count in the index: 47 × 128 × 3 = 18,048 expert tensors. `VERIFIED`.
- **Routing** — this is a DeepSeek-V3 gate, and `transformers` implements it by literally
  subclassing `DeepseekV3TopkRouter` [8]. Per token:
  1. `router_logits = Linear(6144→128)(h)` **computed in fp32**;
  2. `scores = sigmoid(router_logits)` — `scoring_func: "sigmoid"`, not softmax;
  3. `scores_for_choice = scores + e_score_correction_bias` — an **aux-loss-free load-balance
     bias**, a per-expert buffer that is *added for selection only* and never multiplies the
     output. It is present in the checkpoint (`model.layers.N.mlp.e_score_correction_bias`,
     47 of them) and is force-kept in fp32
     (`_keep_in_fp32_modules_strict = ["e_score_correction_bias"]`);
  4. group-limited top-k with `n_group: 1`, `topk_group: 1` — **degenerate**: one group
     containing all 128 experts, so this reduces to a plain top-8;
  5. weights = `scores.gather(topk_indices)`, renormalised to sum 1 (`norm_topk_prob: true`),
     then multiplied by `routed_scaling_factor: 2.5`.
  vLLM builds the same thing, hardcoding `scoring_func="sigmoid"`, `use_grouped_topk=True`,
  `renormalize=config.norm_topk_prob`, `e_score_correction_bias=…` [9]. `VERIFIED`.
- **Training-side balancing** (not visible in the config): the report describes a
  **dropless** routing policy with *sequence-level* load balancing, an auxiliary loss
  coefficient of **1.0e-4** and an **expert-bias update factor of 1.0e-4** [5]. So the
  scheme is bias-correction-first with a *small residual aux loss* — accurately described
  as "aux-loss-free-style bias plus a light sequence-level auxiliary term", not as strictly
  aux-loss-free. `UNVERIFIED` beyond the report's own statement (I read it in the report,
  but nothing in the checkpoint can confirm a training-time coefficient).
- Activation `silu` (SwiGLU) throughout, experts included. `VERIFIED` [3][10].

### 3.5 Other blocks

**Norms — K-EXAONE DROPS QK-Reorder-Norm and reverts to conventional pre-norm.** This is
the single biggest cross-generation surprise, and the checkpoint proves it independently of
any prose. K-EXAONE's per-layer tensors are:

```
model.layers.N.input_layernorm.weight          ← 48, present
model.layers.N.post_attention_layernorm.weight ← 48, present
                                               ← NO post_feedforward_layernorm
model.layers.N.self_attn.{q_norm,k_norm}       ← 48, retained
```

versus 4.0/4.5, which have `post_attention_layernorm` + `post_feedforward_layernorm` and
**no** `input_layernorm`. Same tensor *names*, opposite *meaning*: in K-EXAONE
`post_attention_layernorm` is the classic Llama pre-MLP norm, not an output norm. The
generated `modeling_exaone_moe.py` confirms the forward pass:
`residual = h; h = input_layernorm(h); h = attn(h); h = residual + h; residual = h;
h = post_attention_layernorm(h); h = mlp(h); h = residual + h` [8], and vLLM's
`ExaoneMoeDecoderLayer` matches [9]. Corroborating evidence from the vendor: the 4.5 card
lists a "Reordered Norm" bullet; **the K-EXAONE card's configuration block does not** [7].
So: **QK-norm kept, Reorder-Norm dropped.** `VERIFIED`.

**MTP head.** `num_nextn_predict_layers: 1`, `mtp_layer_types: ["full_attention"]`,
`mtp_sliding_windows: [0]`. Same DeepSeek-V3 shape as 4.5 —
`mtp.{pre_fc_norm_embedding, pre_fc_norm_hidden, fc (12288→6144), layers.0.*, norm}`,
sharing `embed_tokens` and `lm_head` — except that the MTP decoder layer here is
**pre-norm** (matching its own stack) and its **MLP is dense**, not MoE
(`mlp.{gate,up,down}_proj`, width 18432; 0.53 B params, matching the report's "dense layer
with 0.52 B parameters" [5]). Its single attention layer is `full_attention` with window
`0`, therefore **NoPE**. The card claims ~1.5× decode throughput from MTP self-speculation
[7][5]. `VERIFIED` for structure [3][9][10].

**Inference-active? No, not as served.** vLLM's `ExaoneMoeForCausalLM.load_weights` carries
`skip_prefixes=[..., "mtp."]`; the weights are only picked up by the separate
`ExaoneMoeMTP` module, instantiated under `--speculative-config '{"method":"mtp",
"num_speculative_tokens":2}'`, which the card pairs with `--no-enable-prefix-caching`.
The study ran with prefix caching on and no speculative config. `VERIFIED` [7][9].

**Other:** untied embeddings, RMSNorm eps 1e-5, one final `model.norm`, bf16, no
quantisation config in-repo (a third-party NVFP4+GPTQ build exists but is not what was
served). `VERIFIED` [3][7][10].

### 3.6 The repeating motif

```
L0            : SWA(win=128, RoPE θ=1e6, no scaling) + DENSE SwiGLU-18432
L1, L2        : SWA(win=128, RoPE)                   + MoE(128 experts, top-8, +1 shared, 2048)
L3            : FULL(NoPE)                           + MoE
[ SWA, SWA, SWA, FULL ] + MoE                        ← repeat ×11 = layers 4…47
+ 1 MTP block (shared embed/lm_head → 2 pre-fc norms → fc 2h→h → 1 pre-norm
               FULL/NoPE decoder layer with DENSE MLP → norm)
```
Block internals: `x → input_layernorm → Attn(QK-RMSNorm) → +residual →
post_attention_layernorm → MoE/MLP → +residual`.

---

## 4. What changes across the ladder — scale vs generation

**Constant across all three (the family's actual identity):**
`LLLG` 3:1 local:global hybrid; **RoPE on local layers only, NoPE on global layers**;
per-head RMSNorm on Q and K; 8 KV heads and head_dim 128 on every rung; SwiGLU/silu;
untied embeddings; RMSNorm eps 1e-5; bf16; `<think>`/`</think>` reasoning protocol.

**Pure scale (4.0-32B → K-EXAONE):** hidden 5120→6144, layers 64→48 (*fewer*, not more),
Q heads 40→64, FFN width 27392→18432 dense / 2048 per expert, params 32 B→236 B.

**Generation, not scale:**

| axis | 4.0-32B (Jul 2025) | K-EXAONE (Dec 2025) | 4.5-33B (Apr 2026) |
|---|---|---|---|
| norm placement | **post-norm** (QK-Reorder-Norm) | **pre-norm** (reverted) | **post-norm** (restored) |
| FFN | dense | **MoE 128e/top-8/1 shared**, layer 0 dense | dense |
| local window | 4096 | **128** | 4096 |
| RoPE scaling | llama3 ×16 (orig 8192) | **none** (`default`) | llama3 ×16 (orig 8192) |
| declared window | 131072 (= 16×8192 ✓) | 262144 | 262144 (≠ 16×8192) |
| vocab / tokenizer | 102,400 BBPE, `[|role|]` tags | **153,600 SuperBPE**, `<\|role\|>` tags | 153,600 SuperBPE (same tokenizer) |
| MTP | none | 1 layer (dense, NoPE) | 1 layer (post-norm) |
| modality | text | text | **+1.29 B ViT** |
| `enable_thinking` default | **false** | true | true |
| licence | NC | **commercial-permitting** | NC |
| config era | transformers 4.54 | transformers 5.1 | transformers 5.3.0.dev0 |

The ladder is **not** a clean scale sweep, and the atlas should say so. K-EXAONE is a
*separate line* (Korean sovereign model, commercial licence, MoE, its own tokenizer), and
4.5 is 4.0's text stack — same 64 layers, same 5120/27392, same 40/8 heads, byte-identical
`layer_types` — re-tokenised, given an MTP head and a vision tower. The two "32B/33B" rungs
are the same dense body one generation apart; the 236B rung shares only the attention
*scheme*.

Two of the three generation changes point the same way: **K-EXAONE optimises for
long-context serving** (window 4096→128, MoE, MTP self-speculation) and pays for it by
reverting the norm reordering, which 4.5 then restores on the dense line. Whether the
pre-norm revert on K-EXAONE was a stability requirement at 236 B or an MoE-specific choice
is **not stated in any source I read** — it is a real open question about this checkpoint.

---

## 5. Reasoning protocol, and the study's client-side split

| rung | template default | prefix emitted when thinking ON | when OFF |
|---|---|---|---|
| 4.0-32B | `enable_thinking` undefined → **OFF** | `<think>\n` (left open) | `<think>\n\n</think>\n\n` |
| 4.5-33B | `enable_thinking is not defined or is true` → **ON** | `<think>\n` | `<think>\n\n</think>\n\n` |
| K-EXAONE | same as 4.5 → **ON** | `<think>\n` | `<think>\n\n</think>\n\n` |

`VERIFIED` by reading `chat_template.jinja` from each repo [11]; the 4.0 card documents the
open-`<think>` behaviour, and both newer cards carry the note *"Different from EXAONE-4.0,
… uses `enable_thinking=True` as default"* [7]. **The study's handling is correct**: it
must force `enable_thinking: true` on 4.0-32B, and it is a no-op on the other two.

Think tokens are the literal special tokens `<think>` / `</think>` — ids 356/355 in the 4.0
tokenizer, 54/55 in the 4.5 / K-EXAONE tokenizer. Splitting client-side on the string
`</think>` is exactly what the templates themselves do when re-serialising an assistant
turn. `VERIFIED` [11].

**One correction to `smolbench/evals/providers/ec2.py`'s comment** ("no vLLM reasoning parser exists
for it"): no *EXAONE-named* parser exists — I checked `vllm/reasoning/` and there is none
[9] — but all three vendor cards recommend reusing a generic one: `--reasoning-parser
deepseek_r1` for 4.0, `qwen3` for 4.5, `deepseek_v3` for K-EXAONE (SGLang: `qwen3`) [7].
Functionally the client-side split yields the same content, since all three parsers key on
the same literal tags; the note is over-broad rather than wrong, and nothing about the
study's results depends on it.

---

## 6. Contradictions and unexplained fields

**Contradictions (reported, not smoothed):**

1. **4.5 RoPE scaling vs declared window.** `factor 16.0` × `original_max_position_embeddings
   8192` = 131072, but `max_position_embeddings: 262144`. 4.0's numbers match exactly
   (16 × 8192 = 131072); 4.5's are off by 2×. Immaterial in practice (§1.2), but it is a
   real inconsistency in the shipped config. [2]
2. **4.5 card parameter count.** Card says "Number of Parameters (Language Model): 31.7B";
   the checkpoint's text stack is 32.53 B (or 33.06 B including MTP). 31.7 B reconciles only
   as *64 layers + one embedding matrix* (31.74 B), i.e. excluding the untied `lm_head` and
   the MTP block. The vision figure (1.29 B) matches exactly. [7][10]
3. **K-EXAONE tokenizer class.** `config.json` declares `tokenizer_class: "GPT2Tokenizer"`;
   `tokenizer_config.json` declares `PreTrainedTokenizerFast`. The latter wins at load;
   harmless, but the two files disagree. [3]
4. **`vision_token_id: 67` == `image_token_id: 67`** in the 4.5 config, both pointing at
   `<|image_pad|>`. The token that looks like the intended "vision" placeholder,
   `<|vision_pad|>`, is id **66** and is referenced by no config field. [2][11]
5. **K-EXAONE ships the multimodal tokenizer and chat template but has no vision tower.**
   Its `chat_template.jinja` contains full `image`/`video` branches emitting
   `<vision><image_pad></vision>`, and its tokenizer reserves ids 66/67/68/73/74 — on a
   `ExaoneMoeForCausalLM` text-only model. Inherited artefacts, dead at inference. [3][11]
6. **`--language-model-only` and `--enable-prefix-caching` are correct for this study**, but
   note the vendor's own MTP recipe requires `--no-enable-prefix-caching` — i.e. the study's
   serving flags foreclose MTP by construction on both MTP-bearing rungs. [7][9]

**Config fields no implementation reads** (`arch_facts.json` `derived.unclassified`, plus
some the classifier did absorb). I grepped `transformers` main and vLLM main for each:

| field | rung | status |
|---|---|---|
| `mtp_share_layers: true` | 4.5 | **Read by neither** transformers nor vLLM. `INFERRED` meaning: records that the MTP block reuses the main `embed_tokens` and `lm_head` — consistent with the checkpoint having no `mtp.embed_tokens` / `mtp.lm_head`. Training/bookkeeping metadata. |
| `mtp_loss_scaling_factor: 0.05` | 4.5 | Read by neither. Training-time MTP loss weight; the K-EXAONE report states the same 0.05 [5]. Inert at inference. |
| `is_moe_layer: [false, true × 47]` | K-EXAONE | **Read by neither.** Exactly redundant with `mlp_layer_types`, which both implementations *do* read. Dead metadata that happens to agree. |
| `scoring_func: "sigmoid"` | K-EXAONE | Read by neither — both hardcode sigmoid (`DeepseekV3TopkRouter` in HF; a literal `scoring_func="sigmoid"` in vLLM). Descriptive only, and it agrees with the code. |
| `sliding_windows: [128,128,128,0,…]` | K-EXAONE | **Read by vLLM** (per-layer window + RoPE gate), **not** by transformers (which reconstructs the same thing from the scalar + `layer_types`). Load-bearing in the stack that served the study. |
| `mtp_layer_types` / `mtp_sliding_windows` | K-EXAONE | Read by vLLM only, and only inside the MTP module (`is_mtp=True` branch). Say: the MTP layer is global, window 0 ⇒ NoPE. |
| `n_group: 1`, `topk_group: 1` | K-EXAONE | Read, but **degenerate** — one group of 128 experts makes group-limited routing equal to plain top-8. Present so the DeepSeek-V3 router code path can be reused unchanged. |
| `first_k_dense_replace: 1` | K-EXAONE | Read, but **overridden** by `mlp_layer_types` when present (HF: *"Prioritized over `first_k_dense_replace`"*). Both agree here. |
| `head_dim` absent | 4.5 text_config | Falls back to 5120/40 = 128, identical to 4.0's explicit value. Not a difference. |
| `attention_dropout: 0.0` | all | Training-only; inert at inference. |
| `image_token_id` / `video_token_id` / `vision_start_token_id` / `vision_end_token_id` | 4.5 | All resolve to real tokenizer ids (67/68/73/74) — explained, not mysterious; the classifier only flagged them because they are not architecture shape fields. |

Nothing else in the three configs is unexplained.

---

## 7. What I did not cover

- I did not run the models; every claim is from configs, checkpoint tensor indices,
  implementation source, and vendor documents.
- I read the K-EXAONE and EXAONE 4.5 reports through the arXiv HTML renderings, and
  extracted architecture facts from them; I did not read either PDF end to end, so training
  details (data mixture, RL recipe, eval protocol) are outside this brief. Both reports are
  thin on the language-model architecture relative to what the configs and code show —
  the 4.5 report in particular defers to "the EXAONE 4.0 32B base model" rather than
  restating shapes [6].
- The 4.5 vision tower is described from its config, the checkpoint tensor names and vLLM's
  implementation; the study never loaded it (`--language-model-only`), so none of the study
  results depend on it.
- I did not verify the reports' *training* claims (SuperBPE token-efficiency gain, Muon
  optimiser, FP8 native training, 11 T tokens, aux-loss coefficients) against anything
  outside the reports themselves — those are marked `UNVERIFIED`.
- I did not check whether the FuriosaAI NVFP4+GPTQ K-EXAONE build differs structurally; it
  is not what the study served.
