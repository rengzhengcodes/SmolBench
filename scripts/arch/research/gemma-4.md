# Gemma 4 (Google) — architecture brief

**Scope:** the three rungs this study served — `google/gemma-4-E2B-it`, `google/gemma-4-12B-it`,
`google/gemma-4-31B-it`.

**Ground truth:** `scripts/arch/arch_facts.json` + `scripts/arch/arch_configs_raw.json`, fetched
2026-08-12 at the SHAs pinned in §1. Where a published source disagrees with the config, the config
wins and the disagreement is reported (§8).

**Label key:** `[V]` verified — a config field, or a source line I actually read · `[I]` inferred —
reasoning stated · `[U]` unverified — could not confirm.

---

## 0. Bottom line

Gemma 4 is a dense, decoder-only Transformer whose defining move is that **the global
(full-attention) layers are a structurally different block from the local (sliding) layers** —
2× wider heads (512 vs 256), fewer KV heads, a different RoPE scheme, and on 12B/31B no `v_proj`
at all. A block diagram of Gemma 4 needs **two distinct attention blocks per model**, not one.

Two further structural facts shape the ladder: **E2B** carries a Per-Layer Embedding table,
cross-layer KV sharing, and a double-width MLP on its shared span, none of which 12B/31B have;
and **12B is a different architecture class** (`gemma4_unified`) that post-dates the family launch.

---

## 1. Provenance

| key | repo | revision (SHA) | arch class | model_type | transformers |
|---|---|---|---|---|---|
| `gemma-4-e2b` | `google/gemma-4-E2B-it` | `3e22461f65e89153144f8adb70e3b8c2cc9845a7` | `Gemma4ForConditionalGeneration` | `gemma4` | 5.5.0.dev0 |
| `gemma-4-12b` | `google/gemma-4-12B-it` | `707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7` | `Gemma4UnifiedForConditionalGeneration` | `gemma4_unified` | **5.10.0.dev0** |
| `gemma-4-31b` | `google/gemma-4-31B-it` | `842da3794eaa0b77d5f08bae87a17459d91ff475` | `Gemma4ForConditionalGeneration` | `gemma4` | 5.5.0.dev0 |

All three served `--language-model-only --enable-prefix-caching --reasoning-parser gemma4` at
`max_model_len 131072`; tp=1 (E2B), tp=4 (12B, 31B). `[V]` `arch_facts.json:served`

**The middle rung is not the same architecture as its siblings, and it shipped later.** `[I]` The
launch blog (2026-04-02) announces **four** sizes — E2B, E4B, 26B-A4B MoE, 31B Dense — and **does
not include the 12B** `[V]`. The 12B carries a later `transformers_version` (5.10.0.dev0 vs
5.5.0.dev0) and a distinct architecture class, and it appears in the technical report (internal
date 2026-06-19, arXiv v1 2026-07-02). The consistent reading is that **12B Unified was added to
the family after the April launch**. Treat this ladder as three related-but-not-nested designs.

---

## 2. Family context

The Gemma 4 technical report (Gemma Team, Google DeepMind, arXiv:2607.02770; v1 2026-07-02,
v2 2026-07-24) describes **five** checkpoints; this study serves three. `[V]`

| variant | total | active / effective | modalities | in study |
|---|---|---|---|---|
| E2B | ~5.1B | 2.3B effective | text+image+audio | ✅ |
| E4B | ~8B | 4.5B effective | text+image+audio | ❌ |
| 12B (unified) | ~11.96B | dense | text+image+audio | ✅ |
| 26B-A4B | 25.2B | 3.8B active (**MoE**) | text+image | ❌ |
| 31B | 30.7B / 31.27B | dense | text+image | ✅ |

Report Table 1 (columns *Audio Encoder / Vision Encoder / Embedder / Einsums / Drafter*) `[V]`,
independently reproduced by two separate reads of the paper:

| | audio enc | vision enc | embedder | einsums | drafter |
|---|---|---|---|---|---|
| E2B | 305M | 150M | 400M + 2,340M | 1,870M | 76M |
| 12B | — | — | 1,000M | 10,890M | 400M |
| 31B | — | 550M | 1,410M | 29,290M | 500M |

**These reconcile exactly with the configs** `[I]` — the strongest available evidence that the
report and these checkpoints describe the same weights:

- E2B embedder `262144 × 1536 = 402.7M` ✓ "400M"; PLE table `262144 × 35 × 256 = 2,349M` ✓ "2,340M".
  Effective `= 0.40 + 1.87 = 2.27B` ✓ "2.3B"; total `= 0.40 + 2.34 + 1.87 + 0.15 + 0.305 = 5.07B`
  ✓ safetensors **5,123,178,051**.
- 12B embedder `262144 × 3840 = 1,006M` ✓ "1,000M"; `1.00 + 10.89 = 11.89B` ✓ safetensors
  **11,959,730,224**.
- 31B embedder `262144 × 5376 = 1,409M` ✓ "1,410M"; `1.41 + 29.29 = 30.70B` ✓ the card's "30.7B".

**Licence: Apache 2.0** `[V]` — `license: apache-2.0`, `license_link` → `ai.google.dev/gemma/apache_2`,
genuine Apache text, **not** the bespoke "Gemma Terms of Use" of prior generations. All three repos
are **ungated** (`gated: false`) `[V]`.

**Tokenizer:** `GemmaTokenizer`; report: *"a SentencePiece tokenizer with split digits, preserved
whitespace, and byte-level encodings. The vocabulary has 262k entries"*, and *"All models share the
same tokenizer"* `[V]` = config `vocab_size: 262144` on all three. **Training-data cutoff** January
2025 `[V]`.

---

## 3. Positional encoding — two regimes in one stack

`rope_parameters` is a **dict keyed by layer type** `[V]`, byte-identical across all three rungs:

```json
"full_attention":    {"rope_type": "proportional", "rope_theta": 1e6, "partial_rotary_factor": 0.25},
"sliding_attention": {"rope_type": "default",      "rope_theta": 1e4}
```

### 3.1 `rope_type: "proportional"` is a published scheme — it is p-RoPE

`[V]` It is HuggingFace's registered name for **p-RoPE**, from **Barbero, Vitvitskyi,
Perivolaropoulos, Pascanu & Veličković, "Round and round we go! What makes rotary positional
encodings useful?", ICLR 2025 (arXiv:2410.06205)** — the paper the Gemma 4 report cites at exactly
this point. Federico Barbero is also a listed Gemma 4 contributor. The model card writes it
"Proportional RoPE (p-RoPE)". It is **not** NTK-aware, YaRN, linear or LongRoPE scaling, and **not**
YaRN's "proportional attention" temperature.

`transformers/modeling_rope_utils.py`, `"proportional": _compute_proportional_rope_parameters`: `[V]`

```python
rope_proportion = rope_parameters_dict.get("partial_rotary_factor", 1.0)
attention_factor = 1.0  # Unused in this type of RoPE
rope_angles      = int(rope_proportion * head_dim // 2)
inv_freq_rotated = 1.0 / (base ** (torch.arange(0, 2 * rope_angles, 2, ...) / head_dim))
nope_angles      = head_dim // 2 - rope_angles
if nope_angles > 0:
    inv_freq = torch.cat((inv_freq_rotated, torch.zeros(nope_angles, ...)), dim=0)
```

**What it actually does.** The exponent denominator is the **full `head_dim`, not `rotary_dim`**.
That one detail is the entire scheme: the retained frequencies are *identical to standard RoPE's
highest-frequency quarter*, and the **lowest** frequencies are **deleted, not rescaled**. This is
frequency *truncation*, not the context-length *interpolation* the name "proportional" suggests.
Contrast the ordinary GPT-NeoX partial-rotary convention, which divides by `rotary_dim` and so
compresses the whole spectrum into the rotated slice.

Barbero et al.: *"p-RoPE, with 0≤p≤1 being the fraction of RoPE 'kept'"*; *"we … truncate the very
lowest frequencies"*; *"p=0 coincides with NoPE, while the case p=1 with RoPE"* — motivated by
giving the model *"robust semantic channels that are distance agnostic."* `[V]`

Frequencies only — no attention or logit scaling (`attention_factor = 1.0  # Unused`). `[V]`

### 3.2 The un-rotated 75% become NoPE channels

`[V]` `partial_rotary_factor` multiplies the **global** head dim (512), not 256, because the config
injects a per-layer `head_dim` override for full-attention layers *before* RoPE init (§4.1). So on
every global layer `[I]`:

- `rope_angles = int(0.25 × 512 // 2) = 64` → **128 of 512 dims rotated (25%)**
- `nope_angles = 256 − 64 = 192` → **384 of 512 dims un-rotated (75%)**

The un-rotated dims are **not** sliced out and re-concatenated. Gemma 4 has no `rotary_dim` slicing
anywhere; the zero-padded `inv_freq` entries yield `cos=1, sin=0`, so the full-width
`x*cos + rotate_half(x)*sin` reduces to `x` **exactly** — an algebraic identity rather than a code
branch. `[I]` Those 384 dims are pure **NoPE**: position-agnostic content channels that compare on
semantics alone regardless of token distance. With NeoX half-split pairing the rotated indices are
`{0..63} ∪ {256..319}`. `[I]`

Sliding layers use `rope_type: "default"` — **all 256 dims rotated**, θ=1e4. `[V]`

### 3.3 The 10k / 1M local–global split

`[V]` Report: *"The RoPE frequencies are set to 1M and 10k on global and local attention layers,
respectively."* This is the Gemma 3 scheme carried forward (`configuration_gemma3.py`:
`default_theta = {"global": 1_000_000.0, "local": 10_000.0}`). Gemma 4's addition over Gemma 3 is
the *partial* rotary layered on top.

**Google's stated motivation is memory, not retrieval quality.** `[V]` Report: *"we encode position
with p-RoPE with p=0.25 on global attention layers … effectively reducing the global KV cache by
37.5%"*; model card: *"To optimize memory for long contexts, global layers feature unified Keys and
Values, and apply Proportional RoPE (p-RoPE)."* The report contains **no** occurrence of "NoPE" and
no discussion of what the un-rotated channels are for `[V]` (verified absence); that rationale
exists only in the cited Barbero paper.

### 3.4 ⚠️ The 37.5% figure — architecturally real, not realised by the runtimes

Report both halves of this; they do not agree.

- `[V]` In `transformers`, the attention writes **both** tensors even when `v_proj is None`:
  `key_states, value_states = past_key_values.update(key_states, value_states, self.layer_idx)`.
  K and V have already diverged (K: `k_norm` *with* scale, then RoPE; V: `v_norm` *without* scale,
  no RoPE), so the HF cache is exactly the size of an untied one. vLLM likewise materialises a
  duplicate `v_proj` weight at load time. **No KV-cache saving in either runtime.**
- `[I]` **The architecture nevertheless permits precisely 37.5%.** `v_norm` has `with_scale=False`
  while `k_norm` has a scale, applied to the *same* projected vector — so `K = diag(k_scale) · V`
  elementwise; and on the 384 NoPE dims RoPE is the identity, so those dims of K and V are the same
  tensor up to a fixed diagonal that folds into `q_proj`. A runtime can therefore cache the shared
  512-dim tensor plus only the 128 rotated K dims:
  `(384 + 2×128) / (2×512) = 640/1024 = 62.5%` → **a 37.5% reduction, matching the published figure
  to the digit.** This also explains why p-RoPE and K=V are applied to *the same* layers.
- **Finding:** the saving is a property of the weights that Google's own serving stack presumably
  exploits; `transformers` and `vLLM` as of 2026-08-12 do not. **For this study's vLLM runs, assume
  the unreduced global KV footprint.**

---

## 4. Attention

### 4.1 Global layers are a wider, leaner block — confirmed in the implementation

`[V]` `configuration_gemma4.py` builds a per-layer override applied **only** to `full_attention`:

```python
global_head_dim = kwargs.pop("global_head_dim", 512)
num_global_key_value_heads = kwargs.pop("num_global_key_value_heads", None)
layer_overrides = {"head_dim": global_head_dim}
num_key_value_heads = num_global_key_value_heads if getattr(self, "attention_k_eq_v", True) else None
if num_key_value_heads is not None:
    layer_overrides["num_key_value_heads"] = num_key_value_heads
kwargs["per_layer_config"] = {i: layer_overrides for i, t in enumerate(self.layer_types)
                              if t == "full_attention"}
```

The model then reads `self.head_dim = layer_config.head_dim`. vLLM mirrors it in
`vllm/transformers_utils/configs/gemma4.py`, whose docstring states it outright: *"Gemma4 uses a
larger head dimension on its full attention layers than on its sliding ones, and with
`attention_k_eq_v` it uses more KV heads there too."* `[V]`

**Answer to the atlas question: yes — full-attention layers use 2× wider heads (512) than sliding
layers (256), and fewer KV heads. 512 is the Q, K and V head dim simultaneously** (q/k/v/o all use
`self.head_dim`). `[V]` Derived projection shapes `[I]`:

| rung | sliding layer | global layer |
|---|---|---|
| **E2B** h=1536 | q 1536→2048 (8×256), k/v 1536→256 (1×256), o 2048→1536 | q 1536→4096 (8×512), k/v 1536→512 (1×512), o 4096→1536 |
| **12B** h=3840 | q 3840→4096 (16×256), k/v 3840→2048 (8×256), o 4096→3840 | q 3840→8192 (16×512), **k 3840→512 (1×512), v = None**, o 8192→3840 |
| **31B** h=5376 | q 5376→8192 (32×256), k/v 5376→4096 (16×256), o 8192→5376 | q 5376→16384 (32×512), **k 5376→2048 (4×512), v = None**, o 16384→5376 |

GQA groups: 12B 2:1 sliding → **16:1** global; 31B 2:1 → **8:1** global; E2B **8:1 in both**
(a single KV head throughout — MQA). Note `num_attention_heads × head_dim ≠ hidden_size` anywhere,
the long-standing Gemma convention of decoupling head width from model width. `[I]`

**⚠️ Config trap `[V]`:** the KV-head override is gated on **`attention_k_eq_v`**, not on
`num_global_key_value_heads` being set. E2B has `attention_k_eq_v: false`, so even had it declared a
global KV-head count, HF would silently drop it. vLLM replicates the same gate. Consistent across
runtimes, but the two features are logically independent. E2B's `num_global_key_value_heads: null`
is therefore doubly inert.

### 4.2 `attention_k_eq_v` — weight tying, on global layers only

`[V]` `self.use_alternative_attention = config.attention_k_eq_v and not self.is_sliding` →
**global layers only**, where `v_proj` is literally `None`:

```python
key_states   = self.k_proj(hidden_states).view(hidden_shape)
value_states = self.v_proj(hidden_states).view(hidden_shape) if self.v_proj is not None else key_states
key_states   = self.k_norm(key_states);   key_states = apply_rotary_pos_emb(...)
value_states = self.v_norm(value_states); value_states = value_states.transpose(1, 2)
```

Report: *"We improve memory efficiency by re-using keys as values in the global attention layers
(except in E2B and E4B), i.e., values=keys."* `[V]` — matching `attention_k_eq_v` true on 12B/31B,
false on E2B. Cited to *Kayyam et al., 2026* `[V]` (paper not retrieved `[U]`).

**What it saves:** parameters, checkpoint bytes, and one GEMM per global layer — **not** KV-cache
bytes in current runtimes (§3.4). vLLM reconstructs the dropped weight at load:
`yield name.replace("k_proj", "v_proj"), weight.clone()`. `[V]`
Parameter saving `[I]`: 31B `10 × 5376 × 2048 ≈ 110M`; 12B `8 × 3840 × 512 ≈ 16M`.

### 4.3 Cross-layer KV sharing — E2B only

`[V]` `num_kv_shared_layers: 20` of 35 (E2B); `0` on 12B/31B.

```python
first_kv_shared_layer_idx = config.num_hidden_layers - config.num_kv_shared_layers
self.is_kv_shared_layer   = layer_idx >= first_kv_shared_layer_idx >= 0
```

The **last N layers** hold no KV of their own. Consumption is
`key_states, value_states = shared_kv_states[self.layer_type]` — **the donor dict is keyed by layer
type**, so sliding layers reuse the last non-shared *sliding* layer and full layers reuse the last
non-shared *full* layer. `[V]` Shared layers own **no `k_proj`, `v_proj`, `k_norm` or `v_norm` at
all** (*"Layers sharing kv states don't need any weight matrices"*) and never write cache. `[V]`

**E2B concretely `[I]`** (from that code plus the real `layer_types`; full layers at 4, 9, 14, 19,
24, 29, 34): `first_kv_shared_layer_idx = 35 − 20 = 15`. **Donors are layer 13 (sliding) and layer
14 (full).** Layers **15–34** — 16 sliding + 4 full — are pure consumers. **Only 15 of 35 layers
hold KV (57% of layers eliminated).**

Report: *"we share the KV cache with ratios of 20/35 and 18/42 for the E2B and E4B model"* `[V]`,
citing Shazeer 2019; cf. Cross-Layer Attention (arXiv:2405.12981) `[U]`. vLLM implements it via
`kv_sharing_target_layer_name` plus a `KVSharingFastPrefillMetadata` split-prefill path. `[V]`

### 4.4 QK-norm, a third V-norm, and no `1/√d`

- `[V]` **QK-norm present**: `q_norm` / `k_norm` are `Gemma4RMSNorm(dim=self.head_dim)`, applied
  pre-RoPE. Report: *"QKNorm [Henry et al., 2020]"*. Because `dim=head_dim`, these norms are
  **512-wide on global layers and 256-wide on sliding layers**.
- `[V]` **A third, unscaled `v_norm`** — `Gemma4RMSNorm(self.head_dim, with_scale=False)` — which
  Gemma 3 did not have. It is precisely what makes the K=V tie work (§3.4).
- `[V]` **`self.scaling = 1.0`** — the standard `1/√d_head` softmax scale is **absent**, and there is
  no `query_pre_attn_scalar`. vLLM comments: *"Gemma4 uses scaling=1.0. Unlike Gemma2/3,
  query_pre_attn_scalar is NOT used here; Q/K norms with learnable weights handle scaling
  implicitly."* `[I]` This is what lets one weight set cope with `head_dim` changing 256↔512 between
  layer types — the temperature is learned into `q_norm`. **Worth drawing; it is unusual.**

### 4.5 Softcapping

- `[V]` **Attention-logit softcapping is gone from the text tower.** No `attn_logit_softcapping`
  field exists in `Gemma4TextConfig`. `eager_attention_forward` still accepts a `softcap` argument,
  but the text attention never passes one; vLLM resolves
  `getattr(config, "attn_logit_softcapping", None)` → `None`. The only surviving attention cap is in
  the **audio encoder** (`attention_logit_cap: 50.0`, E2B's `audio_config`).
- `[V]` **`final_logit_softcapping: 30.0` IS applied at inference, in both runtimes.**
  transformers: `logits = logits / cap; logits = torch.tanh(logits); logits = logits * cap`.
  vLLM: `LogitsProcessor(config.vocab_size, soft_cap=getattr(config, "final_logit_softcapping", None))`,
  inherited by the multimodal and unified wrappers via `self.language_model`. Unlike the Gemma 2
  situation this one is honoured — **relevant to this study**, since a tanh cap at ±30 compresses
  the logit range every sampler sees.
- `[V]` **No output gating**, no sigmoid gate, no temperature in the attention block:
  `attn_output = self.o_proj(attn_output)` directly.

### 4.6 `use_bidirectional_attention`

`[V]` `"vision"` on 12B/31B, `null` on E2B. Non-causal attention over image/audio token blocks
inside the causal LM — but **only on sliding layers**:

```
For global (full attention) layers:  causal only (no bidirectional)
For local (sliding window) layers:   AND(sliding_window, OR(causal, blockwise))
Unlike Gemma 3 (which applies bidirectional attention on all layers), Gemma 4
explicitly disables bidirectional attention on global attention layers.
```

Under `--language-model-only` with text-only prompts this path is inert for this study. `[I]`

---

## 5. FFN, norms, embeddings

- **Dense GeGLU** `[V]`: `down_proj(act_fn(gate_proj(x)) * up_proj(x))` with
  `act_fn = ACT2FN["gelu_pytorch_tanh"]` — **GeGLU, not SwiGLU** (SwiGLU would require SiLU/Swish),
  consistent with Gemma 1–3. Three matrices per FFN. `intermediate_size / hidden_size = 4.0×` on all
  three rungs (6144/1536, 15360/3840, 21504/5376). `[I]`
- **`use_double_wide_mlp` applies ONLY to KV-shared layers** `[V]` — not guessable from the config:
  ```python
  first_kv_shared_layer_idx = config.num_hidden_layers - config.num_kv_shared_layers
  is_kv_shared_layer  = layer_idx >= first_kv_shared_layer_idx > 0
  use_double_wide_mlp = config.use_double_wide_mlp and is_kv_shared_layer
  self.intermediate_size = config.intermediate_size * (2 if use_double_wide_mlp else 1)
  ```
  It widens a *single* MLP (gate/up/down all sized to 2×), not two parallel MLPs. So **E2B layers
  0–14 have `intermediate_size 6144` and layers 15–34 have 12288.** It is an explicit trade: the 20
  layers that gave up their KV projections get 2× FFN width back. On 12B/31B the flag is `false`
  *and* `num_kv_shared_layers == 0`, so it is doubly inert.
- **Norms — RMSNorm, Gemma's double-norm retained, `eps 1e-6`** `[V]`. Decoder-layer module order:
  `input_layernorm` → attn → `post_attention_layernorm` → +residual → `pre_feedforward_layernorm`
  → MLP → `post_feedforward_layernorm` → +residual → *(E2B only)* `post_per_layer_input_norm` →
  +residual → `hidden_states *= self.layer_scalar`. That is **four norms per layer (five on E2B)**,
  wrapping both sublayers pre *and* post — draw all of them.
- **Embedding scaling** `[V]`: `Gemma4TextScaledWordEmbedding` with `embed_scale = hidden_size**0.5`;
  the PLE table uses `hidden_size_per_layer_input**0.5`.
- **`tie_word_embeddings: true`** on all three `[V]` — the LM head reuses the input embedding matrix.
  `dtype bfloat16`, **`quantization: null`** — unquantised BF16 repos `[V]`. Google separately ships
  official QAT INT4 checkpoints in distinct repos (e.g. `google/gemma-4-12B-it-qat-w4a16-ct`,
  `compressed-tensors`, 4-bit, group_size 32) — **not** what this study served `[V]`.

### 5.1 Per-Layer Embeddings — E2B is a PLE model, and "E" means *effective*

`[V]` **E2B = "Effective 2B": 2.3B effective out of ~5.1B raw.** Report: *"E2B and E4B use per-layer
embeddings as in Gemma 3n, making them 2.3B and 4.5B effective out of 5B and 8B total parameters
respectively"*; Table 1 notes *"the extra embedder parameters in E2B and E4B are per-layer
embeddings."* The convention is inherited from Gemma 3n: the PLE table is a *second* embedding table
that can be held in host memory and streamed per token, so it need not occupy accelerator memory —
hence the raw-vs-effective split. (The offload framing is documented for Gemma 3n; the Gemma 4
report itself does not restate it `[U]`.)

Mechanism `[V]`:
```python
self.embed_tokens_per_layer = Gemma4TextScaledWordEmbedding(
    config.vocab_size_per_layer_input,                                  # 262144
    config.num_hidden_layers * config.hidden_size_per_layer_input,      # 35 * 256
    self.padding_idx, embed_scale=config.hidden_size_per_layer_input**0.5)
...
per_layer_projection = self.per_layer_model_projection(inputs_embeds) * self.per_layer_model_projection_scale
# reshape -> [batch, seq, num_layers, hidden_size_per_layer_input]
return (per_layer_projection + per_layer_inputs) * self.per_layer_input_scale
```

Each token gets a `35 × 256` block: one 256-d conditioning vector **per decoder layer**, formed as
the **sum of a looked-up per-layer embedding and a projection of the token's own main embedding**,
rescaled by `1/√2`. Each layer consumes its slice through a gated path —
`per_layer_input_gate → act_fn → × per_layer_input → per_layer_projection → post_per_layer_input_norm
→ residual add` `[V]`. Table size `262144 × 35 × 256 = 2,349M` `[I]`, matching report Table 1's
"2,340M" and accounting for the entire 5.1B ↔ 2.3B gap.

**Gemma 3n's other tricks are GONE.** `[V]` (verified absence: zero hits for `altup`, `laurel`,
`matformer` across the full `modeling_gemma4.py` and the full report text, while `modeling_gemma3n.py`
has real `Gemma3nTextAltUp` and `Gemma3nTextLaurelBlock` classes.) Gemma 4 E2B keeps **PLE +
cross-layer KV sharing** from 3n and **drops AltUp, LAuReL and MatFormer**. **It is not a MatFormer
model** — there is no nested/elastic submodel and no "mix-n-match". This is the single most likely
thing for a reader to get wrong by analogy with Gemma 3n.

### 5.2 MoE: code path present, unused

`[V]` All three configs: `enable_moe_block: false`, `num_experts: null`, `top_k_experts: null`, and
(E2B/31B) `expert_intermediate_size: null` / (12B) `moe_intermediate_size: null`. **These three
checkpoints ship dense GeGLU FFNs.**

The architecture *does* carry a real MoE path `[V]`: `modeling_gemma4.py` defines `Gemma4TextExperts`
(*"Collection of expert weights stored as 3D tensors"*, `gate_up_proj`/`down_proj` shaped
`[num_experts, …]`) and `Gemma4TextRouter` (top-k softmax routing), gated behind
`if self.enable_moe_block:`; the decoder layer conditionally builds `pre_feedforward_layernorm_2` and
`post_feedforward_layernorm_1/_2`. The family ships an MoE checkpoint that exercises it —
**`google/gemma-4-26B-A4B-it`: `enable_moe_block: true, num_experts: 128, top_k_experts: 8,
moe_intermediate_size: 704`, hidden 2816, 30 layers, 25.2B total / 3.8B active, 1 shared expert**
`[V]` — which this study does not serve. Note the **field-name skew**: the same concept is
`expert_intermediate_size` in `gemma4` and `moe_intermediate_size` in `gemma4_unified`. `[V]`

---

## 6. Multimodal towers (all served `--language-model-only`)

`--language-model-only` is a **generic vLLM flag**, not Gemma-specific: *"If True, disables all
multimodal inputs by setting all modality limits to 0"* `[V]`. Cross-validated against report
Table 10 `[I]`:

- **E2B** — `vision_config` (`gemma4_vision`): ViT, hidden 768, 16 layers, 12 heads, patch 16, MLP
  3072, its own `rope_theta: 100.0`, 280 soft tokens/image — exactly the report's *"150M encoder: 768
  model dim, 3072 MLP dim, 12 heads, 16 layers"*. `audio_config` (`gemma4_audio`): USM-style
  conformer, hidden 1024, 12 layers, `subsampling_conv_channels [128, 32]`, `attention_logit_cap 50.0`
  = the report's 305M encoder (*"reduce the number of parameters by 55% (from 680M to 305M)"*).
- **31B** — `vision_config`: hidden 1152, 27 layers, 16 heads, MLP 4304 = the report's *"550M
  encoder: 1152 model dim, 4304 MLP dim, 16 heads, 27 layers"*. **`audio_config: null`** ✓ the card's
  "31B: no audio" — a rare case of card and config agreeing to the field.
- **12B (`unified`) — encoder-free.** Its `vision_config` (`gemma4_unified_vision`) and `audio_config`
  (`gemma4_unified_audio`) **declare no layers and no attention heads at all** — only
  `mm_embed_dim 3840`, `model_patch_size 48`, `num_soft_tokens 280` / `audio_embed_dim 640`,
  `audio_samples_per_token 640`. `[V]` The transformers docs confirm the design: *"Gemma 4 12B
  Unified is an encoder-free multimodal model… projects raw inputs directly into the language
  model's embedding space through lightweight linear pipelines"*; *"No Vision Tower: Raw pixel
  patches are projected directly into LM space via a `Dense + LayerNorm` pipeline"*; *"No Audio
  Tower: Raw 16 kHz waveform samples are chunked into fixed-length frames and projected through a
  simple `RMSNorm → Linear` pipeline"* `[V]`. Report: *"takes in 48×48×3 RGB patches, but replaces
  the 550M vision encoder by a single large matmul (35M parameters)"* `[V]`.
  **Arithmetic check `[I]`: 640 samples ÷ 16 kHz = exactly 40 ms** — the config's
  `audio_samples_per_token: 640` is the report's 40 ms chunk, to the sample.
  Precisely: this is *shallow-projection early fusion*, not "the LM is the encoder" — the projectors
  (`Gemma4UnifiedVisionEmbedder`, `Gemma4UnifiedMultimodalEmbedder`) are real modules, just linear
  and shallow instead of deep transformer towers. `[V]`

**What the text tower inherits:** nothing structural. Under `--language-model-only` vLLM skips the
projectors; the residue in the text stream is the reserved multimodal vocabulary (§8) and the inert
`use_bidirectional_attention` path. `[I]` Beyond the towers, `gemma4_unified_text` differs from
`gemma4_text` by **dropping PLE fields and all MoE fields**, and by two defaults
(`max_position_embeddings` 262144 vs 131072, `sliding_window` 1024 vs 512); everything else —
`head_dim`, `global_head_dim`, `rope_parameters` logic, `attention_k_eq_v`, `num_kv_shared_layers`,
`final_logit_softcapping` — is identical. `[V]`

---

## 7. Per-rung cards

### 7.1 `gemma-4-e2b` — `google/gemma-4-E2B-it`
1. **Identity** — Gemma 4 E2B ("Effective 2B"), Google DeepMind, launched 2026-04-02. **2.3B
   effective / 5,123,178,051 raw** (400M embedder + 2,340M PLE + 1,870M transformer + 150M ViT +
   305M audio) `[V+I]`. Apache 2.0, ungated. `GemmaTokenizer`, vocab 262,144. Context **131,072**.
   Thinking model.
2. **Positional** — sliding: full RoPE, θ=1e4, all 256 dims rotated. Global (layers 4, 9, 14, 19, 24,
   29, 34): **p-RoPE**, θ=1e6, `p=0.25` over `head_dim 512` → 128 rotated, **384 NoPE**.
3. **Attention** — MQA, 8 Q heads, **1 KV head throughout**; head_dim **256 sliding / 512 global**.
   `sliding_window 512`. **KV sharing: layers 15–34 hold no KV**, reusing layer 13 (sliding) /
   layer 14 (full); only 15/35 layers cache. `attention_k_eq_v false` → global layers keep a real
   `v_proj`. QK-norm + unscaled V-norm; `scaling = 1.0`; no attn softcap; final logit softcap 30.0
   applied; no output gate.
4. **FFN** — dense GeGLU, `hidden 1536`, `intermediate 6144` — **12288 on layers 15–34** via
   `use_double_wide_mlp` `[V]`.
5. **Other** — RMSNorm ×5 per layer (`input`, `post_attention`, `pre_feedforward`, `post_feedforward`,
   `post_per_layer_input`) + `layer_scalar`; **PLE table 262144×35×256**; tied embeddings; BF16
   unquantised; ViT-768/16L + USM-conformer-1024/12L towers (unused here).
6. **Motif** — `[Sliding ×4, Full] × 7` = 35 layers. `[V]`

### 7.2 `gemma-4-12b` — `google/gemma-4-12B-it`
1. **Identity** — Gemma 4 12B **Unified**, Google DeepMind; added after the April launch.
   **11,959,730,224 raw** `[V]`. Apache 2.0, ungated. Vocab 262,144. Context **262,144** (this study
   served 131,072). Thinking model. **Different architecture class from its siblings**
   (`Gemma4UnifiedForConditionalGeneration`).
2. **Positional** — same regime: sliding θ=1e4 full-rotary 256-dim; global **p-RoPE** θ=1e6,
   128/512 rotated, 384 NoPE.
3. **Attention** — GQA, 16 Q heads. Sliding: 8 KV heads × 256 (2:1). Global: **1 KV head × 512
   (16:1)** with **`v_proj` dropped** (`attention_k_eq_v true`). `sliding_window 1024`. No cross-layer
   KV sharing. QK-norm + V-norm; `scaling = 1.0`; final logit softcap 30.0 applied.
   `use_bidirectional_attention: "vision"` (sliding layers only).
4. **FFN** — dense GeGLU, `hidden 3840`, `intermediate 15360` (4.0×), uniform across layers.
5. **Other** — RMSNorm ×4 per layer; **no PLE** (`hidden_size_per_layer_input: 0`); tied embeddings;
   BF16; **encoder-free** vision (48×48×3 patch → Dense+LN) and audio (640 samples = 40 ms →
   RMSNorm→Linear) projectors. `generation_config` uniquely sets `suppress_tokens: [258883, 258882]`
   = `<audio|>`, `<image|>` `[V]`.
6. **Motif** — `[Sliding ×5, Full] × 8` = 48 layers. `[V]`

### 7.3 `gemma-4-31b` — `google/gemma-4-31B-it`
1. **Identity** — Gemma 4 31B Dense, Google DeepMind, launched 2026-04-02. **31,273,088,876 raw**
   (safetensors) vs **30.7B** in the card/report Table 1 — see §8. Apache 2.0, ungated. Vocab
   262,144. Context **262,144** (served 131,072). Thinking model. **Text+image only — no audio**
   (`audio_config: null`) `[V]`.
2. **Positional** — same regime: sliding θ=1e4 full-rotary; global **p-RoPE** θ=1e6, 128/512 rotated,
   384 NoPE.
3. **Attention** — GQA, 32 Q heads. Sliding: 16 KV heads × 256 (2:1). Global: **4 KV heads × 512
   (8:1)** with **`v_proj` dropped**. `sliding_window 1024`. No cross-layer KV sharing. QK-norm +
   V-norm; `scaling = 1.0`; final logit softcap 30.0 applied.
4. **FFN** — dense GeGLU, `hidden 5376`, `intermediate 21504` (4.0×), uniform.
5. **Other** — RMSNorm ×4 per layer; no PLE; tied embeddings; BF16; ViT-1152/27L tower (unused).
6. **Motif** — `[Sliding ×5, Full] × 10` = 60 layers. `[V]`

---

## 8. Contradictions and unexplained fields

**Contradictions**

1. **31B parameter count: 30.7B (card + report Table 1) vs 31,273,088,876 (safetensors metadata).**
   `[V]` The ~0.55B gap matches the table's own 550M vision-encoder line, so the published figure
   most likely quotes the text backbone only while HF sums the whole checkpoint. `[I]` Reported, not
   resolved.
2. **Release date: 2026-04-02 (launch blog) vs 2026-06-19 (report internal date) vs 2026-07-02
   (arXiv v1) vs 2026-07-30 (model-card page footer).** `[V]` Best reading `[I]`: family launched
   2026-04-02 **without the 12B** (the blog lists only E2B, E4B, 26B-A4B, 31B); the report and card
   are later documents that fold the 12B in. See §1.
3. **The report's 37.5% global-KV reduction is not realised by transformers or vLLM** (§3.4). The
   architecture permits it exactly; the open-source runtimes cache K and V separately.
4. **Secondary write-ups render p-RoPE as "pp-RoPE"** — an artifact of the LaTeX `$p$-RoPE` in the
   HTML. The primary text and the model card both say **p-RoPE**. `[I]`

**Config fields now explained** (initially flagged as unknown; resolved by decoding the checkpoints'
`tokenizer.json` and reading vLLM's parser `[V]`):

- `generation_config.eos_token_id: [1, 106, 50]` vs `config.eos_token_id: [1, 106]` — **1 = `<eos>`,
  106 = `<turn|>`, 50 = `<|tool_response>`**. Token 50 is an extra generation-time stop used by the
  reasoning parser to close reasoning at a tool-response boundary.
- `suppress_tokens: [258883, 258882]` (12B only) — `<audio|>` and `<image|>`, the end-of-audio /
  end-of-image structural markers, suppressed from free-text generation because the unified LM hosts
  multimodal soft tokens directly.
- `--reasoning-parser gemma4` delimiters: `_THINKING_START_TAG = "<|channel>"`,
  `_THINKING_END_TAG = "<channel|>"`, `_TURN_END_TAG = "<turn|>"`. The report's `<|think|>` is the
  *activation* token placed in a leading system turn, distinct from these output delimiters.

**Still unexplained**

- **`boa_token_id: 256000`** sits apart from its siblings (`boi 255999`, `image 258880`,
  `audio 258881`, `eoi 258882`, `eoa 258883`, `video 258884`). Begin-markers cluster at 255999/256000
  and end-markers at 258882/258883, so it is probably deliberate, but I found no source documenting
  the layout. `[U]`
- **`eoa_token_id` vs `eoa_token_index`** — duplicated with the *same* value (258883) on E2B/31B,
  while 12B carries only `eoa_token_index`. Looks like a rename mid-flight; harmless but inconsistent
  across rungs. `[U]`
- **Report "Drafter" weights** (76M / 400M / 500M) have no corresponding field in any served config —
  no `speculative_config`, no MTP entry. vLLM *does* register a `Gemma4MTPModel` → `gemma4_mtp`
  class `[V]`, so the drafters are multi-token-prediction heads shipped elsewhere; whether the `-it`
  repos contain them is unverified `[U]`. The study did not use them.
- **`Gemma4DSparkModel` → `gemma4_dspark`** is registered in vLLM alongside the Gemma 4 classes; I
  did not determine what it is. `[U]`
- **`use_clipped_linears`** (E2B vision `true` / 31B vision `false`; E2B audio `true`) and
  **`standardize`** (E2B `false` / 31B `true`) — vision/audio-tower-only flags not chased, since all
  three rungs were served language-model-only. `[U]`
- **`vision_soft_tokens_per_image: 280`** (E2B/31B) vs `vision_config.num_soft_tokens: 280` (12B) —
  same value, different field name across architecture classes. `[V]`, benign.

---

## 9. What changes across the ladder

**Fixed across all three rungs** `[V]`: `head_dim 256` / `global_head_dim 512`; the entire RoPE
regime (p-RoPE p=0.25 θ=1e6 global; default θ=1e4 sliding); `vocab_size 262144`; `rms_norm_eps 1e-6`;
`gelu_pytorch_tanh` GeGLU; FFN ratio 4.0×; `tie_word_embeddings true`; `final_logit_softcapping 30.0`;
`enable_moe_block false`; `attention_bias false`; `scaling = 1.0`; BF16 unquantised.

**Moves monotonically with size** `[V]`: layers 35 → 48 → 60; hidden 1536 → 3840 → 5376;
intermediate 6144 → 15360 → 21504; Q heads 8 → 16 → 32; sliding KV heads 1 → 8 → 16.

**Moves structurally / non-monotonically:**

| knob | E2B | 12B | 31B |
|---|---|---|---|
| arch class | `gemma4` | **`gemma4_unified`** | `gemma4` |
| local:global | **4:1** | 5:1 | 5:1 |
| `sliding_window` | **512** | 1024 | 1024 |
| `max_position_embeddings` | **131072** | 262144 | 262144 |
| `attention_k_eq_v` | **false** | true | true |
| global KV heads | 1 (null → inert) | **1** | **4** |
| global GQA ratio | 8:1 | **16:1** | 8:1 |
| `num_kv_shared_layers` | **20 / 35** | 0 | 0 |
| PLE (`hidden_size_per_layer_input`) | **256** | 0 | 0 |
| `use_double_wide_mlp` | **true** (layers 15–34) | false | false |
| vision tower | ViT-768/16L | **encoder-free** | ViT-1152/27L |
| audio tower | conformer-1024/12L | encoder-free | **none** |

**E2B differs structurally, not merely in size**: PLE, cross-layer KV sharing, a double-wide MLP on
the shared span, a 4:1 interleave, a 512 window, an untied `v_proj`, and half the context. **12B
differs structurally too, in a different direction**: a distinct architecture class with an
encoder-free multimodal front end, added after the family launch. Only 12B→31B approximates a pure
width/depth scale-up, and even that pair diverges on global KV heads (1 vs 4) and audio support.

---

## 10. Sources

Config ground truth — `scripts/arch/arch_facts.json`, `scripts/arch/arch_configs_raw.json` (SHAs §1).

1. Gemma Team, Google DeepMind. *Gemma 4 Technical Report.* arXiv:2607.02770 (v1 2026-07-02, v2 2026-07-24). https://arxiv.org/html/2607.02770v1
2. Barbero, Vitvitskyi, Perivolaropoulos, Pascanu, Veličković. *Round and round we go! What makes rotary positional encodings useful?* ICLR 2025. arXiv:2410.06205. https://arxiv.org/abs/2410.06205
3. Gemma 4 model card, Google AI for Developers. https://ai.google.dev/gemma/docs/core/model_card_4
4. Gemma 4 launch post, 2026-04-02. https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/
5. HF transformers `modeling_rope_utils.py`. https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/modeling_rope_utils.py
6. HF transformers `models/gemma4/{configuration,modeling}_gemma4.py`. https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/gemma4/modeling_gemma4.py
7. HF transformers `models/gemma4_unified/*` + `docs/source/en/model_doc/gemma4_unified.md`. https://raw.githubusercontent.com/huggingface/transformers/main/docs/source/en/model_doc/gemma4_unified.md
8. HF transformers `models/gemma3n/modeling_gemma3n.py` (AltUp/LAuReL comparison). https://github.com/huggingface/transformers/blob/main/src/transformers/models/gemma3n/modeling_gemma3n.py
9. vLLM `model_executor/models/gemma4.py`, `gemma4_mm.py`, `gemma4_unified.py`, `registry.py`; `transformers_utils/configs/gemma4.py`; `reasoning/gemma4_utils.py`; `parser/gemma4.py`; `config/multimodal.py`. https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/model_executor/models/gemma4.py
10. vLLM `gemma4_rope` API docs. https://docs.vllm.ai/en/latest/api/vllm/model_executor/layers/rotary_embedding/gemma4_rope/
11. HF repos + safetensors metadata: https://huggingface.co/google/gemma-4-E2B-it · https://huggingface.co/google/gemma-4-12B-it · https://huggingface.co/google/gemma-4-31B-it · https://huggingface.co/google/gemma-4-26B-A4B-it · https://huggingface.co/google/gemma-4-12B-it-qat-w4a16-ct
12. *Welcome Gemma 4* (HF blog) — used as a lead only, not cited for any fact. https://huggingface.co/blog/gemma4
13. Shazeer 2019 (MQA); Cross-Layer Attention arXiv:2405.12981; "Do Transformers Need Three Projections?" arXiv:2606.04032; Kayyam et al. 2026 (K=V, cited by the report) — context only, not read in full `[U]`.
