# Ministral-3 Reasoning 2512 (Mistral AI) — architecture brief

Family section of the SmolBench architecture atlas. Three rungs: `ministral-3-3b`, `ministral-3-8b`,
`ministral-3-14b`.

**Ground truth**: `/workspace/SmolBench/scripts/arch/arch_configs_raw.json` and `arch_facts.json`,
fetched 2026-08-12 at pinned commit SHAs
(3B `4a36357c811bf511a7b625d132e12f22408aac91`, 8B `81eaece1948f3875421d9a45bc55487d10e2d894`,
14B `51f9210f3cd20f3452a80d5819d15dc61cc50630`). Every claim tagged **VERIFIED** is either a config
field I read in that file, a weight-map entry, an arithmetic result, or a source line I actually read
(URL given). **INFERRED** = my deduction from verified facts. **UNVERIFIED** = could not confirm.

---

## Bottom line

All three rungs are the *same* dense decoder block repeated 26 / 34 / 40 times, with a **head
configuration that is byte-identical across the ladder** (32 Q heads, 8 KV heads, head_dim 128) —
so the ladder scales by depth and residual width only, never by head count. The interesting parts are
positional: the family drops the interleaved sliding-window attention that defined Ministral 2410 in
favour of **uniform global attention**, and stacks three separate long-context mechanisms on top of
each other — a very high RoPE base, YaRN interpolation (16×, 16384 → 262144), and a Llama-4-style
position-dependent query-temperature term. The 14B's `rope_theta: 1e9` is **real and deliberate**, not
a config artefact (proof below). Two config fields are silently ignored by the stack that actually
served this study.

---

## 1. `ministral-3-3b` — Ministral-3-3B-Reasoning-2512

### Identity
| Field | Value | Status |
|---|---|---|
| Full name | Ministral 3 3B Reasoning 2512 | VERIFIED (repo id) |
| Vendor | Mistral AI (France) | VERIFIED |
| Release | 2025-12-02 (Mistral 3 launch; "available today") | VERIFIED — [mistral.ai/news/mistral-3](https://mistral.ai/news/mistral-3/) |
| Licence | Apache 2.0 | VERIFIED — model card: *"Apache 2.0 License: Open-source license allowing usage and modification for both commercial and non-commercial purposes."* |
| Params (card) | "3.4B Language Model" + "0.4B Vision Encoder" | VERIFIED — model card |
| Params (computed) | LM **3,429,006,336** (3.43B); Pixtral tower 403,305,472; projector ≈17M | VERIFIED (arithmetic from config) |
| Params (safetensors metadata) | `total_parameters: 4,251,743,232`; **distinct stored params 3,849,090,048** (3.85B) | VERIFIED — index metadata |
| Active params | = total (dense, no MoE) | VERIFIED |
| Tokenizer | Tekken, `vocab_size: 131072`, 566 reserved control slots (IDs 0–565) | VERIFIED |
| Weights dtype | `bfloat16`, `quantization: null` — **unquantised** | VERIFIED |

> **Reconciling the two parameter counts.** `total_parameters` (4.2517B) exceeds the sum of stored
> tensors because it counts the tied embedding twice. 4,251,743,232 − (131072 × 3072) =
> **3,849,090,048**, which matches my computed grand total to within the projector estimate. This is
> itself independent evidence of embedding tying (§3B "Other blocks"). VERIFIED (arithmetic).

### Positional encoder
`rope_parameters` (all VERIFIED, verbatim):
```json
{"rope_type":"yarn","type":"yarn","rope_theta":1000000.0,"factor":16.0,
 "beta_fast":32.0,"beta_slow":1.0,"original_max_position_embeddings":16384,
 "mscale":1.0,"mscale_all_dim":1.0,"llama_4_scaling_beta":0.1}
```
- **Base**: θ_i = 1e6^(−2i/128). Wavelengths span 2π ≈ 6.3 tokens (i=0) to **5.06e6 tokens** (i=63).
  **27 of 64** frequency pairs (42%) have a wavelength longer than the 16384-token pre-extension
  window — they never complete a rotation in-window and act as slow positional-magnitude channels
  rather than oscillators. VERIFIED (arithmetic).
- **YaRN**, `factor: 16.0`: extension ratio **16384 → 262144 = 16×**. VERIFIED.
- **`beta_fast: 32` / `beta_slow: 1`** define the NTK-by-parts ramp in *rotations-per-original-window*
  units. Solving `yarn_find_correction_dim` at base 1e6, d=128, orig=16384 gives low = 20.38, high =
  36.44, truncated to **[20, 37]**. Dims 0–20 (high frequency) are **pure extrapolation, left
  untouched**; dims 37–63 (low frequency) are **fully interpolated by 1/16**; dims 20–37 are a linear
  blend. VERIFIED (arithmetic against the vLLM implementation I read).
- **`mscale` / attention temperature**: this is genuinely ambiguous between stacks — see
  §"Unexplained and inert fields". Under DeepSeek-style semantics (`mscale == mscale_all_dim`) the
  factor is exactly **1.0** (no temperature change); under vLLM's plain-`yarn` path it is
  `0.1·ln(16)+1 = **1.2773**`. VERIFIED (both code paths read).
- **Llama-4 query-temperature term**, `llama_4_scaling_beta: 0.1`: multiplies the *query* vector by
  `1 + 0.1·ln(1 + ⌊pos / 16384⌋)`. Exactly 1.0 below position 16384, then 1.0693 at 16384, 1.1099 at
  32768, **1.2079 at 131072** (this study's served window), 1.2773 at 262144. VERIFIED (formula read
  in HF `modeling_ministral3.py`; arithmetic mine).
- **Uniform across layers** — no `layer_types`, no per-layer rope config. VERIFIED.

### Attention
Plain GQA, **identical on all three rungs**. VERIFIED.
- 32 query heads, 8 KV heads → **4:1 GQA ratio**; `head_dim: 128`.
- `sliding_window: null` → **global causal attention on every layer**.
- **No QK-norm**: no `q_norm`/`k_norm` tensors in the weight map. VERIFIED (weight-level).
- **No attention bias**: only `.weight` on q/k/v/o projections, no `.bias`. VERIFIED (weight-level).
- `attention_dropout: 0.0`.
- Softmax scale `head_dim**-0.5`. VERIFIED — HF `modeling_ministral3.py`.
- **KV cache**: 2 × 8 × 128 × 26 layers = 53,248 elements/token = **104.0 KiB/token @ bf16**
  (≈13.0 GiB at the served 131072-token window). VERIFIED (arithmetic).

### FFN
Dense SwiGLU. `hidden_act: "silu"`, three projections per layer (`gate_proj`, `up_proj`, `down_proj`)
→ `down_proj(silu(gate_proj(x)) * up_proj(x))`. VERIFIED (weight map + HF modeling file).
`intermediate_size: 9216` = **exactly 3.0 × hidden_size**. No MoE fields anywhere — `derived.moe` is
`{}` on all three rungs. **Dense confirmed.** VERIFIED.

### Other blocks
- **Norm**: RMSNorm (`Ministral3RMSNorm`), `rms_norm_eps: 1e-05`, **pre-norm** — `input_layernorm`
  before attention, `post_attention_layernorm` before the MLP, plus one final `model.norm`. VERIFIED
  (weight map + HF modeling file).
- **Embedding tying**: `tie_word_embeddings: true`, **explicitly set**. Weight map has
  `language_model.model.embed_tokens.weight` and **no `lm_head` tensor at all**. VERIFIED
  (weight-level) — this is the only tied rung.
- **Reasoning tokens**: `[THINK]` = token ID **34**, `[/THINK]` = ID **35** — real single-token
  vocabulary items, not multi-token text. VERIFIED (`tokenizer_config.json` `added_tokens_decoder`).
- `bos_token_id: 1`, `eos_token_id: 2`, `pad_token_id: 11`; `image_token_index: 10` = the `[IMG]`
  control token. VERIFIED (generation_config + tokenizer_config cross-check).

### Vision tower (present, not used)
`vision_config` is a **Pixtral** encoder: 24 layers, hidden 1024, 16 heads × head_dim 64, intermediate
4096, patch 14, image_size 1540, its own `rope_theta: 10000.0` (`rope_type: "default"` — plain RoPE, no
YaRN). Bridged by `multi_modal_projector` (`patch_merger.merging_layer`, `linear_1`, `linear_2`,
`norm`), `spatial_merge_size: 2` (2×2 patch pooling before projection), `projector_hidden_act: "gelu"`,
`multimodal_projector_bias: false`, `vision_feature_layer: -1` (last layer's features). ≈403M params.
VERIFIED (config + weight map).

**The study served `--language-model-only`.** In vLLM this sets `MultiModalConfig.language_model_only`,
whose only effect on the text path is `get_limit_per_prompt() → 0` for every modality. The text tower's
weights, shapes and forward pass are **untouched**; the vision tower and projector are simply never
built or invoked. VERIFIED (vLLM `config/multimodal.py:350`). **The text tower is unaffected.**

### Repeating motif
**26 × [ RMSNorm → GQA(32Q/8KV, d128, global, RoPE-YaRN) → residual → RMSNorm → SwiGLU(3072→9216→3072)
→ residual ]**, then final RMSNorm → tied unembedding.

---

## 2. `ministral-3-8b` — Ministral-3-8B-Reasoning-2512

### Identity
Release, vendor, licence, tokenizer, dtype as the 3B (Apache 2.0, Tekken 131072, bf16 unquantised —
all VERIFIED).
- Params (card): **"8.4B Language Model" + "0.4B Vision Encoder"** — VERIFIED, model card.
- Params (computed): LM **8,489,553,920** (8.49B) + Pixtral tower 403,305,472 + projector ≈25M.
  Safetensors `total_parameters: **8,918,026,240**`, and `total_size` = exactly 2 × that → **bf16 with
  no double-count ⇒ untied**. VERIFIED (arithmetic).
  - *Minor contradiction*: card says 8.4B LM, config arithmetic gives 8.49B. Rounding direction is odd
    (8.49 → "8.4") but the gap is <1.1%. Reported, not smoothed over.

### Positional encoder
**Identical to the 3B, including `rope_theta: 1e6`.** Same YaRN block, same 16× extension
(16384 → 262144), same `[20, 37]` correction range, same `llama_4_scaling_beta: 0.1`, same uniform
per-layer scheme. VERIFIED.

### Attention
**Byte-identical to the 3B**: 32 Q / 8 KV / head_dim 128, `sliding_window: null`, no QK-norm, no bias.
VERIFIED.
- **KV cache**: 2 × 8 × 128 × 34 = 69,632 elements/token = **136.0 KiB/token @ bf16**.

### FFN
Dense SwiGLU, `intermediate_size: 14336` = **3.5 × hidden_size** — the widest ratio on the ladder.
VERIFIED.

### Other blocks
- RMSNorm pre-norm, eps 1e-05, as the 3B.
- **Embedding tying**: `tie_word_embeddings` is **ABSENT** from the config. The `Ministral3Config`
  default is `tie_word_embeddings: bool = False` → **untied**. VERIFIED both ways: the documented
  default ([HF Ministral3 docs](https://huggingface.co/docs/transformers/main/en/model_doc/ministral3),
  *"tie_word_embeddings (`bool`, optional, defaults to `False`)"*), **and** the weight map, which
  contains a separate `language_model.lm_head.weight`. Note this is the *opposite* of the generic
  `PretrainedConfig` default (`True`) — reading the base-class default here would give the wrong answer.
- `[THINK]`/`[/THINK]` = 34/35, as the 3B.

### Vision tower
Identical Pixtral encoder (same 24×1024 config, ≈403M params); only the projector's output width
changes (→4096). Served `--language-model-only`; text tower unaffected. VERIFIED.

### Repeating motif
**34 × [ RMSNorm → GQA(32Q/8KV, d128, global) → residual → RMSNorm → SwiGLU(4096→14336→4096) →
residual ]**, then final RMSNorm → untied `lm_head`.

---

## 3. `ministral-3-14b` — Ministral-3-14B-Reasoning-2512

### Identity
Release, vendor, licence, tokenizer, dtype as above (Apache 2.0, Tekken 131072, bf16 unquantised).
- Params (card): **"13.5B Language Model" + "0.4B Vision Encoder"** — VERIFIED, model card.
- Params (computed): LM **13,506,073,600** (13.51B) — matches the card exactly. Plus Pixtral tower
  403,305,472 + projector ≈36M; safetensors `total_parameters: **13,945,031,680**`, `total_size` =
  exactly 2× ⇒ bf16, untied. VERIFIED.

> **Sibling-checkpoint note (not this study's checkpoint):** `Ministral-3-14B-Instruct-2512` ships
> **FP8** (`quant_method: "fp8"`, `activation_scheme: "static"`, with `lm_head`, `vision_tower` and
> `multi_modal_projector` in `modules_to_not_convert`), while the **Reasoning** checkpoint this study
> served is **BF16**. Do not carry FP8 into the diagram for this rung. VERIFIED (both configs read).

### Positional encoder — the ladder's one real divergence
```json
{"rope_type":"yarn","rope_theta":1000000000.0,  ...  everything else identical to 3B/8B}
```

**Is 1e9 real, or a config artefact? It is real and deliberate.** Evidence:

1. **Two independent fetches of the study's checkpoint agree** — this repo's
   `arch_configs_raw.json` (2026-08-12, pinned SHA) and a separately downloaded copy of the same
   config. VERIFIED.
2. **Decisive: all three 14B post-trains carry it.** `Ministral-3-14B-**Base**-2512` → `1e9`,
   `Ministral-3-14B-**Instruct**-2512` → `1e9`, `Ministral-3-14B-**Reasoning**-2512` → `1e9`.
   Meanwhile `Ministral-3-**8B**-Base-2512` → `1e6` and `Ministral-3-8B-Reasoning-2512` → `1e6`.
   A typo would not survive into three independently released 14B checkpoints while leaving both 8B
   checkpoints at 1e6. This is a **pretraining choice made for the 14B rung**. VERIFIED (Base/8B-Base
   configs fetched from HF).
3. **Precedent**: the previous-generation `Ministral-8B-Instruct-2410` already used
   `rope_theta: 100000000.0` (**1e8**). Very high bases are established Mistral practice, so 1e9 is
   not out of family. VERIFIED (2410 config.json).

**What 1e9 does to the spectrum** (VERIFIED arithmetic):

| | base 1e6 (3B, 8B) | base 1e9 (14B) |
|---|---|---|
| Wavelength range | 6.3 → 5.06e6 tokens | 6.3 → **4.55e9** tokens |
| Dims with λ > 16384 | 27/64 (42%) | **39/64 (61%)** |
| YaRN correction range | [20, 37] | **[13, 25]** |
| Ramp width | 17 dims | **12 dims** |
| Dims fully interpolated (÷16) | 27/64 (42%) | **39/64 (61%)** |

Raising the base stretches the whole geometric frequency ladder: far more dimensions become
slow, non-oscillatory position channels, and the fastest-rotating dims stay fixed at λ = 2π. It is a
*flatter* spectrum in log-frequency terms across the useful range.

**How it interacts with YaRN.** YaRN's correction range is computed *from the base* — so the 1e9 base
does not merely sit under YaRN, it **moves YaRN's boundaries**. The ramp shifts down to dims 13–25 and
narrows from 17 to 12 dims, and the fraction of dimensions getting the full 1/16 interpolation rises
from 42% to 61%. The band left in pure extrapolation shrinks from 21 dims to 14. Net effect
(**INFERRED**, from the verified arithmetic): the 14B relies *less* on high-frequency extrapolation and
*more* on interpolating an already very slow spectrum — a more conservative long-context recipe. Note
also that at base 1e9 the longest wavelength after interpolation is ≈7.3e10 tokens, ~280,000× the
262144 window, so the low-frequency tail is far beyond anything the position range exercises.

Everything else in the RoPE block — `factor: 16.0`, `beta_fast: 32`, `beta_slow: 1`,
`original_max_position_embeddings: 16384`, `mscale`/`mscale_all_dim: 1.0`,
`llama_4_scaling_beta: 0.1`, uniform across layers — is **identical to the 3B and 8B**. VERIFIED.

### Attention
**Byte-identical head configuration to the 3B and 8B**: 32 Q / 8 KV / head_dim 128,
`sliding_window: null`, no QK-norm, no bias. VERIFIED.
- **KV cache**: 2 × 8 × 128 × 40 = 81,920 elements/token = **160.0 KiB/token @ bf16**
  (≈20.0 GiB at 131072 tokens).
- **Note the inversion**: at hidden 5120, the attention block is *narrower* than the residual stream
  (32 × 128 = 4096 < 5120) — the opposite of the 3B. See §"Structural quirk".

### FFN
Dense SwiGLU, `intermediate_size: 16384` = **3.2 × hidden_size**. VERIFIED.

### Other blocks
- RMSNorm pre-norm, eps 1e-05.
- **Embedding tying**: `tie_word_embeddings` **ABSENT** → default `False` → **untied**; weight map has
  `language_model.lm_head.weight`. VERIFIED both ways.
- `[THINK]`/`[/THINK]` = 34/35.

### Vision tower
Identical Pixtral encoder (≈403M). Served `--language-model-only`; text tower unaffected. VERIFIED.

### Repeating motif
**40 × [ RMSNorm → GQA(32Q/8KV, d128, global) → residual → RMSNorm → SwiGLU(5120→16384→5120) →
residual ]**, then final RMSNorm → untied `lm_head`.

---

## Structural quirk worth drawing: attention width vs residual width

`head_dim: 128` is **fixed** while `hidden_size` moves, so the attention projection width
(32 × 128 = 4096) crosses the residual stream between rungs:

| Rung | hidden | q/o width (32×128) | ratio | shape |
|---|---|---|---|---|
| 3B | 3072 | 4096 | **1.333×** | attention **wider** than residual (up-projection) |
| 8B | 4096 | 4096 | **1.000×** | exactly square |
| 14B | 5120 | 4096 | **0.800×** | attention **narrower** than residual (down-projection) |

VERIFIED (arithmetic). The 3B genuinely computes attention in a 4096-d space wider than its own
3072-d residual stream: `q_proj` is 3072→4096 and `o_proj` is 4096→3072. The KV path is 3072→1024
either way. Worth drawing explicitly — a block diagram that assumes `num_heads × head_dim ==
hidden_size` will be wrong on two of the three rungs.

---

## What changes across the ladder

**Moves (3 knobs only):**

| Knob | 3B | 8B | 14B |
|---|---|---|---|
| `num_hidden_layers` | 26 | 34 | 40 |
| `hidden_size` | 3072 | 4096 | 5120 |
| `intermediate_size` | 9216 (3.0×) | 14336 (3.5×) | 16384 (3.2×) |
| `rope_theta` | 1e6 | 1e6 | **1e9** |
| `tie_word_embeddings` | `true` | absent → False | absent → False |
| KV cache @ bf16 | 104.0 KiB/tok | 136.0 KiB/tok | 160.0 KiB/tok |
| Served TP | 1 | 4 | 4 |

**Fixed across all three:**
- **Head configuration is identical** — `num_attention_heads: 32`, `num_key_value_heads: 8`,
  `head_dim: 128`, 4:1 GQA. This is unusual for a size ladder and is the single most important
  "same block, different count" fact for the diagram. Because head_dim and KV heads are fixed, KV cache
  per token scales with **depth alone**.
- `sliding_window: null`, no QK-norm, no attention bias, `attention_dropout: 0.0`.
- Entire YaRN block except the base: `factor: 16.0`, `beta_fast: 32`, `beta_slow: 1`,
  `original_max_position_embeddings: 16384`, `mscale`/`mscale_all_dim: 1.0`,
  `llama_4_scaling_beta: 0.1`; `max_position_embeddings: 262144`.
- `hidden_act: "silu"` (SwiGLU), RMSNorm pre-norm `rms_norm_eps: 1e-05`, `vocab_size: 131072`,
  `dtype: bfloat16`, no quantisation, dense (no MoE).
- The **Pixtral vision tower is byte-identical** on all three (24 layers × 1024, ≈403M params) — the
  family scales the text tower only. Only the projector's output width tracks `hidden_size`.
- `Mistral3ForConditionalGeneration` wrapper; `text_config.model_type: "ministral3"`.

The intermediate/hidden ratio is **not** monotone (3.0 → 3.5 → 3.2). Flagging as a genuine
non-uniformity rather than an error; I found no published rationale. UNVERIFIED as to intent.

---

## Generational change: interleaved SWA is gone

**Confirmed.** The 2410 generation used interleaved sliding-window attention; Ministral-3 does not.

| | Ministral-8B-Instruct-**2410** | Ministral-3-8B-Reasoning-**2512** |
|---|---|---|
| `sliding_window` | **32768** | **null** |
| `layer_types` | present — *"one full attention layer followed by three sliding attention layers, repeated"* | **absent** |
| `num_hidden_layers` | 36 | 34 |
| `intermediate_size` | 12288 | 14336 |
| `rope_theta` | 1e8 | 1e6 |
| `max_position_embeddings` | 32768 | 262144 |
| head config | 32 Q / 8 KV / d128 | 32 Q / 8 KV / d128 (unchanged) |
| `vocab_size` | 131072 | 131072 |

VERIFIED — 2410 `config.json` read directly. Mistral's 2410 announcement described the interleaved
scheme as enabling *"faster, memory-efficient inference"*
([mistral.ai/news/ministraux](https://mistral.ai/news/ministraux/)).

So the generational trade is explicit: **2410 bought cheap long context with a 1:3 global:local layer
interleave and a 32k window; 2512 pays full quadratic global attention on every layer and buys its
256k context purely with positional engineering** (high base + YaRN + query-temperature). This is a
notable and diagram-relevant change — the 2512 block diagram has *one* attention block type, where a
2410 diagram needed two alternating kinds.

Side note (INFERRED, relevant to the atlas): the 2410 interleave was the reason vLLM originally capped
those models at 32k. Dropping it makes Ministral-3 straightforwardly servable at the 131072-token
window this study used.

---

## `llama_4_scaling_beta` — what it is, and who actually consumes it

**What it is.** Meta's Llama 4 introduced inference-time **attention temperature tuning**: scaling the
query vector by a factor that grows with position, to keep attention entropy stable at long context.
HF's `Llama4TextConfig` exposes it as `attn_temperature_tuning: bool = True`, `floor_scale: int = 8192`,
`attn_scale: float = 0.1`, documented as *"Whether to dynamically scale the attention temperature for
each query token based on sequence length. Recommended for long sequences (e.g., >32k tokens) to
maintain stable output results"*, with `floor_scale` = *"Base scale (in tokens) … Larger value delays
scaling to longer positions"* and `attn_scale` = *"Strength of attention temperature tuning."*
VERIFIED — [HF Llama4 docs](https://huggingface.co/docs/transformers/main/en/model_doc/llama4).

Ministral-3 adopts the same mechanism with `beta` ≡ Llama 4's `attn_scale` (both **0.1**) and
`original_max_position_embeddings` (16384) playing the role of `floor_scale` (Llama 4 default 8192).

**Does the `mistral3`/`ministral3` implementation consume it? Yes in HF transformers — but the two
stacks disagree.**

- **HF transformers (main) — YES, reads the nested form.** `modeling_ministral3.py`:
  ```python
  def get_llama_4_attn_scale(positions_ids, beta, max_position_embeddings):
      scaling = 1 + beta * torch.log(1 + torch.floor(positions_ids / max_position_embeddings))
      return scaling[:, None, :, None]
  ...
  query_states = query_states * get_llama_4_attn_scale(
      position_ids,
      self.config.rope_parameters.get("llama_4_scaling_beta"),
      self.config.rope_parameters.get("original_max_position_embeddings"),
  ).to(query_states.dtype)
  ```
  VERIFIED — read at
  [`modeling_ministral3.py`](https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/ministral3/modeling_ministral3.py).
  `configuration_ministral3.py` additionally lists it in
  `ignore_keys_at_rope_validation = {"llama_4_scaling_beta", "max_position_embeddings"}` — i.e. it is
  deliberately exempted from RoPE-parameter validation *because* it is not a RoPE parameter; it is an
  attention-temperature parameter parked inside the RoPE dict. VERIFIED.

- **vLLM — reads a DIFFERENT, top-level shape.** `vllm/model_executor/models/mistral.py`
  (both v0.27.1 on disk and **main**, fetched 2026-08-12):
  ```python
  llama_4_scaling_config = getattr(config, "llama_4_scaling", None)
  self.do_llama_4_scaling = llama_4_scaling_config is not None
  ...
  self.llama_4_scaling_beta = llama_4_scaling_config["beta"]
  scaling = 1 + self.llama_4_scaling_beta * torch.log(
      1 + torch.floor(positions / self.llama_4_scaling_original_max_position_embeddings))
  q = (q * attn_scale).to(q.dtype)
  ```
  It expects a **top-level `config.llama_4_scaling` dict** with keys `original_max_position_embeddings`
  and `beta`. The shipped HF `config.json` has **no such key at any level** — it has
  `text_config.rope_parameters.llama_4_scaling_beta`, a flat float. VERIFIED (raw config + both source
  reads).

  That top-level dict is produced only by vLLM's **Mistral-native `params.json` adapter**,
  `vllm/transformers_utils/configs/mistral.py::adapt_config_dict`, which is invoked from
  `transformers_utils/config.py` only on the Mistral config-format path. VERIFIED (read).

**Consequence for this study.** The served path is: `Mistral3ForConditionalGeneration` → vLLM
`mistral3.py` → `init_vllm_registered_model(hf_config=config.text_config)` with `architectures=None` →
`with_hf_config` resolves `model_type: "ministral3"` via `MODEL_FOR_CAUSAL_LM_MAPPING_NAMES` →
`Ministral3ForCausalLM` → registry entry `"Ministral3ForCausalLM": ("mistral", "MistralForCausalLM")` →
`MistralAttention`, which finds no top-level `llama_4_scaling` → **`do_llama_4_scaling = False`**.
And `smolbench/evals/providers/ec2.py` explicitly forbids `--tokenizer-mode mistral` for these entries, so the
`params.json` adapter never runs.

**INFERRED conclusion**: under vLLM loading the HF config, the Llama-4 query-temperature term is **not
applied**, whereas HF transformers **does** apply it. The divergence is exactly 1.0 below position
16384 and grows to **1.2079 at position 131071** (this study's window ceiling) — so it is a genuine
no-op for prompts under 16k tokens and a real ~21% query-magnitude difference at the long end.

**Caveat, stated plainly**: the study served `vllm/vllm-openai:nightly` (`scripts/fleet/run_fleet.py:151`), a
build I cannot pin. I verified vLLM **main** as of 2026-08-12 still uses the top-level form; I did not
verify the specific nightly digest used at run time. Treat the conclusion as VERIFIED-for-main,
**UNVERIFIED for the exact nightly**. GitHub code search is login-walled, so I could not exhaustively
grep the vLLM repo for `llama_4_scaling_beta`; my greps covered the full v0.27.1 tree on disk (2 hits,
both the variable name in `mistral.py`) and `mistral.py` on main.

---

## Unexplained and inert fields (findings, not noise)

`arch_facts.json` lists five fields under `derived.unclassified` for all three rungs. All five are
explained — they are the multimodal wrapper's fields, not text-tower fields:

| Field | Value | Explanation |
|---|---|---|
| `image_token_index` | 10 | The `[IMG]` control token's ID — cross-checked against `tokenizer_config.json`. VERIFIED |
| `spatial_merge_size` | 2 | 2×2 pooling of Pixtral patches before projection. VERIFIED |
| `vision_feature_layer` | -1 | Take the vision encoder's last hidden layer. VERIFIED |
| `projector_hidden_act` | "gelu" | Activation inside the 2-layer multimodal projector (note: GELU, unlike the text tower's SiLU). VERIFIED |
| `multimodal_projector_bias` | false | No bias in projector linears — matches the weight map (`linear_1.weight`, `linear_2.weight`, no `.bias`). VERIFIED |

**Two fields the serving stack silently ignores** — the real finding here:

1. **`mscale: 1.0` / `mscale_all_dim: 1.0`.** These are DeepSeek-YaRN key names. vLLM's dispatcher
   filters `extra_kwargs` for `rope_type: "yarn"` to exactly
   `{extrapolation_factor, attn_factor, beta_fast, beta_slow, apply_yarn_scaling, truncate}` — `mscale`
   and `mscale_all_dim` are only forwarded for `deepseek_yarn` and `telechat3-yarn`. So on the plain
   `yarn` path they are **dropped**, and `YaRNScalingRotaryEmbedding` instead computes
   `mscale = yarn_get_mscale(16.0) * attn_factor = 0.1·ln(16) + 1 = **1.2773**`.
   Under DeepSeek semantics the config's own values (`mscale == mscale_all_dim`) would give **exactly
   1.0**. So the two readings differ by ~28% in RoPE cos/sin magnitude. VERIFIED (vLLM
   `rotary_embedding/__init__.py`, `yarn_scaling_rope.py`, `common.py`, `deepseek_scaling_rope.py` all
   read). **Which one Mistral intended, I could not establish** — no published source addresses it.
   UNVERIFIED as to intent; flagged as a live ambiguity.
2. **`llama_4_scaling_beta: 0.1`** — dropped by the same filter and not read as a top-level key
   (previous section).

**`type: "yarn"` duplicating `rope_type: "yarn"`** is a transformers-v5 back-compat artefact; vLLM reads
`rope_type`. Harmless. INFERRED.

**Not explained**: nothing else. No config field in these three repos is left unaccounted for.

---

## Reasoning variant: post-training only

**Architecture is identical between Instruct and Reasoning.** Evidence:
- Every architectural field matches between `Ministral-3-14B-Instruct-2512` and
  `Ministral-3-14B-Reasoning-2512` — same `hidden_size` 5120, `num_hidden_layers` 40,
  `intermediate_size` 16384, and the same `rope_parameters` block including `rope_theta: 1e9`.
  VERIFIED (both configs read).
- Safetensors `total_parameters`: Reasoning 13,945,031,680 vs Instruct 13,945,032,240 — a difference of
  **560**, fully accounted for by the Instruct checkpoint's FP8 scale tensors
  (`weight_scale_inv`, `activation_scale`). No architectural delta. VERIFIED.
- Model card: *"this reasoning post-trained version, trained for reasoning tasks, making it ideal for
  math, coding and stem related use cases."* VERIFIED.

**The difference is post-training plus the chat template.** The thinking protocol lives **only** in the
Reasoning template's `default_system_message` — there is no `enable_thinking` kwarg anywhere in the
template. Verbatim:

> `# HOW YOU SHOULD THINK AND ANSWER` … *"Your thinking process must follow the template
> below:[THINK]Your thoughts or/and draft, like working through an exercise on scratch paper. Be as
> casual and as long as you want until you are confident to generate the response to the user.[/THINK]
> Here, provide a self-contained response."*

The template injects this **only when the caller supplies no system message**
(`{%- if messages[0]['role'] != 'system' and default_system_message != '' %}`). The Reasoning template
also adds a `thinking` content-block type that the Instruct template lacks
(`{{- '[THINK]' + block['thinking'] }}`, closed with `[/THINK]`), and threads
`reasoning_content`/`reasoning` fields into it. The Instruct template's `default_system_message` is
instead the Le Chat persona prompt. VERIFIED (both templates read in full).

`[THINK]` (34) and `[/THINK]` (35) are **real single-token vocabulary items**, matching
mistral-common's `SpecialTokens` enum entries `begin_think = "[THINK]"` / `end_think = "[/THINK]"`.
VERIFIED ([mistral-common `base.py`](https://raw.githubusercontent.com/mistralai/mistral-common/main/src/mistral_common/tokens/tokenizers/base.py)).

**Study-relevant**: because the protocol is template-defaulted rather than kwarg-gated, supplying any
system message silently disables thinking. `smolbench/evals/providers/ec2.py` handles this by injecting the exact
default text as `system_prompt` (`MINISTRAL_THINK_SYSTEM`, md5 of the shipped template
`f9ce03df8c692f42b2aeb78024e29f4f`, identical across all three rungs). Served with
`--reasoning-parser mistral`. VERIFIED (repo source read).

---

## Tokenizer

**Tekken**, `vocab_size: 131072`. VERIFIED (config). `tokenizer_config.json` defines **566** special
tokens (IDs 0–565), including `[INST]`=3, `[AVAILABLE_TOOLS]`=5, `[TOOL_RESULTS]`=7/8,
`[TOOL_CALLS]`=9, `[IMG]`=10, `<pad>`=11, `[AUDIO]`=24, `[ARGS]`=32, `[CALL_ID]`=33, `[THINK]`=34,
`[/THINK]`=35, with unused slots up to `<SPECIAL_565>`. Model cards require
*"mistral-common >= 1.8.6 to use our tokenizer."* VERIFIED.

**Version not pinned.** mistral-common's `TokenizerVersion` enum documents v7 (*"improved system prompt
and function calling"*), v11 (*"improved function calling"*), v13 (*"no call id and better prompt
caching"*), v15 (*"model settings"*, 131072 tekken tokens). The shipped `tokenizer_config.json` exposes
**no version string**, and contains **no `[BEGIN_MODEL_SETTINGS]`/`[END_MODEL_SETTINGS]` tokens**, which
rules out v15. Presence of `begin_think`/`end_think` places it at v13 or later in the think-token era.
Best statement: **Tekken, 131,072 vocab, ≥v13, not v15** — exact version UNVERIFIED. I did not fetch
`tekken.json` itself (large); that would settle it.

---

## Serving configuration (for the atlas caption)

All three: `--reasoning-parser mistral --language-model-only --enable-prefix-caching`,
`max_model_len: 131072` (**half** the 262144 the config allows), `system_prompt =
MINISTRAL_THINK_SYSTEM`. TP: 3B = 1, 8B = 4, 14B = 4. Image `vllm/vllm-openai:nightly`.
VERIFIED (`arch_facts.json` `served` block + `smolbench/evals/providers/ec2.py`).

---

## Contradictions and open items

1. **Card vs config, 8B parameter count**: card says "8.4B Language Model", config arithmetic gives
   8.49B. <1.1% gap, odd rounding. Reported as-is. The 3B ("3.4B" vs 3.43B) and 14B ("13.5B" vs 13.51B)
   both match cleanly.
2. **`mscale` semantics are genuinely ambiguous** (1.0 vs 1.2773) between the DeepSeek-YaRN reading the
   key names imply and vLLM's plain-`yarn` computation. Unresolved; no published source addresses it.
3. **`llama_4_scaling_beta` is consumed by HF transformers but not by vLLM's HF-config path** — a real
   behavioural divergence at positions ≥16384, reaching a 1.21× query scale at 131k. Verified against
   vLLM main; **not** verified against the specific nightly digest served.
4. **`intermediate_size / hidden_size` is non-monotone** across the ladder (3.0 → 3.5 → 3.2). No
   published rationale found.
5. **Mistral publishes almost no architecture detail.** Neither the Mistral 3 announcement nor any of
   the model cards mentions RoPE, YaRN, rope base, or sliding windows. NVIDIA's Megatron-Bridge page
   corroborates the shapes (26/34/40 layers, 3072/4096/5120 hidden, "32 attention heads, 8 query groups
   (GQA)", "YaRN RoPE Scaling … up to 256K tokens") and names "Llama 4 Attention Scaling" as a feature,
   but gives no per-size rope base. **No published source anywhere confirms or denies the 14B's 1e9** —
   my confidence rests entirely on the three-checkpoint config evidence, which I consider decisive.
6. **Not covered**: `tekken.json` itself (exact tokenizer version); the specific vLLM nightly digest;
   benchmark numbers beyond the headline 85% AIME'25 for the 14B.

---

## Sources

Configs (ground truth): `/workspace/SmolBench/scripts/arch/arch_configs_raw.json`,
`arch_facts.json` (fetched 2026-08-12, pinned SHAs above).

1. Mistral AI — *Introducing Mistral 3*. https://mistral.ai/news/mistral-3/ (release date, Apache 2.0, 85% AIME'25)
2. Model cards: https://huggingface.co/mistralai/Ministral-3-{3B,8B,14B}-Reasoning-2512 (params, 256k context, licence, mistral-common ≥1.8.6)
3. `mistralai/Ministral-3-{14B,8B}-Base-2512` `config.json` — the 1e9 / 1e6 discriminator
4. HF transformers `modeling_ministral3.py` / `configuration_ministral3.py` — https://github.com/huggingface/transformers/tree/main/src/transformers/models/ministral3
5. HF Ministral3 docs (config defaults incl. `tie_word_embeddings=False`) — https://huggingface.co/docs/transformers/main/en/model_doc/ministral3
6. HF Llama4 docs (`attn_temperature_tuning`, `floor_scale`, `attn_scale`) — https://huggingface.co/docs/transformers/main/en/model_doc/llama4
7. vLLM source: `model_executor/models/mistral.py` (main + v0.27.1), `models/mistral3.py`, `models/registry.py`, `layers/rotary_embedding/{__init__,yarn_scaling_rope,common,deepseek_scaling_rope}.py`, `transformers_utils/configs/mistral.py`, `config/multimodal.py`, `config/vllm.py`
8. Mistral AI — *Un Ministral, des Ministraux* (2410 interleaved SWA). https://mistral.ai/news/ministraux/
9. `mistralai/Ministral-8B-Instruct-2410` `config.json` (sliding_window 32768, layer_types, rope_theta 1e8)
10. mistral-common `SpecialTokens` / `TokenizerVersion` — https://github.com/mistralai/mistral-common/blob/main/src/mistral_common/tokens/tokenizers/base.py
11. NVIDIA Megatron-Bridge — Ministral 3. https://docs.nvidia.com/nemo/megatron-bridge/latest/models/mistral/ministral3.html
12. Study serving config: `/workspace/SmolBench/smolbench/evals/providers/ec2.py`, `/workspace/SmolBench/scripts/fleet/run_fleet.py`
