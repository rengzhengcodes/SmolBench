# GLM-4.x — architecture brief for the SmolBench family ladder

**Scope**: the three GLM rungs served in the 21-checkpoint study.
**Ground truth**: `/workspace/SmolBench/scripts/arch/arch_facts.json` and
`/workspace/SmolBench/scripts/arch/arch_configs_raw.json`, fetched 2026-08-12 at the resolved
commits below. Every unqualified numeric claim is a field read directly from those files, or
arithmetic over them. Non-config claims carry a URL and are tagged **VERIFIED** (I read the
line / ran the grep), **INFERRED**, or **UNVERIFIED**.

| key | repo | revision | class / `model_type` |
|---|---|---|---|
| `glm-4.7-flash` | `zai-org/GLM-4.7-Flash` | `7dd20894a642a0aa287e9827cb1a1f7f91386b67` | `Glm4MoeLiteForCausalLM` / `glm4_moe_lite` |
| `glm-4.5-air` | `zai-org/GLM-4.5-Air` | `a24ceef6ce4f3536971efe9b778bdaa1bab18daa` | `Glm4MoeForCausalLM` / `glm4_moe` |
| `glm-4.7` | `zai-org/GLM-4.7` | `602d01efcdd332c5238ca4bcede555defbe83eb7` | `Glm4MoeForCausalLM` / `glm4_moe` |

---

## Bottom line

The ladder is not the cross-generation contrast its labels suggest. **GLM-4.5, GLM-4.6 and
GLM-4.7 (the 355B line) ship a field-for-field identical `config.json` except for
`max_position_embeddings` (131072 → 202752 → 202752)** — I re-fetched GLM-4.5's and GLM-4.6's
configs and diffed them against our pinned GLM-4.7 copy. So the 4.5→4.7 "generation" gap in
this ladder is architecturally null. Every apparent Air-vs-4.7 difference (QK-norm, expert
count, dense-prefix depth, `routed_scaling_factor`) is the **Air-vs-full split inside the
GLM-4.5 generation**, documented as such in the GLM-4.5 report's own Table 1.

The one genuine architectural break in this family is the **Flash rung**: `glm4_moe_lite` is a
different block — Multi-head Latent Attention instead of GQA, a structurally different partial
rotary, no per-head QK-norm, a new 154880-token vocabulary. It is DeepSeek-V2/V3's attention
wearing a GLM name, and the transformers source says so in its own docstring.

**Draw it as: two rungs of one architecture at two sizes, plus one rung of a different
architecture.**

---

## Rung 1 — GLM-4.5-Air (`glm-4.5-air`)

### 1. Identity

- **GLM-4.5-Air**, Z.ai (Zhipu AI). HF repo initial commit **2025-07-20**; family launch
  2025-07-28 (VERIFIED via HF commit history; launch date from press coverage, UNVERIFIED
  against a primary Z.ai page — `z.ai/blog/*` is JS-rendered and returned empty to every
  fetch attempt).
- **106B total / 12B active.** VERIFIED — GLM-4.5 technical report Table 1
  (`# Total Parameters: 355B | 106B`, `# Activated Parameters: 32B | 12B`),
  https://ar5iv.labs.arxiv.org/html/2508.06471. The config cannot state this, but reproduces
  it: summing the config shape gives **106.9B** for the main tower (109.2B including a
  one-layer MoE MTP module) and **12.2B** active per token excluding embedding matrices. The
  match confirms the published figure counts the main tower only.
- **Licence: MIT.** VERIFIED — card metadata `license: mit` and prose *"released under the MIT
  open-source license and can be used commercially and for secondary development"*
  (https://huggingface.co/zai-org/GLM-4.5). No literal `LICENSE` file exists in the repo
  (404), so the SPDX tag and prose are the only confirmable form.
- **Tokenizer**: GLM-4 lineage, `vocab_size: 151552`, untied embeddings → a separate
  151552×4096 input embedding and LM head, **1.24B parameters of pure vocabulary**. EOS is a
  *set*: `[151329, 151336, 151338]`; pad 151329. The GLM-4.5 report says nothing about the
  tokenizer (VERIFIED negative — two full passes); vocab size is config-only.
- **Shipped weights**: `torch_dtype: bfloat16`, `quantization: null`. An official FP8 sibling
  exists (`zai-org/GLM-4.5-Air-FP8`) but the study served the BF16 repo.
- **Served in this study**: `max_model_len 131072`, `tp=8`, `--reasoning-parser glm45
  --enable-prefix-caching`.

### 2. Positional encoder — partial RoPE, half-rotary, base 1e6, no scaling

- `rope_theta: 1000000`, `rope_scaling: null`, `partial_rotary_factor: 0.5`,
  `max_position_embeddings: 131072` (= 128×1024 exactly).
- `head_dim: 128` × 0.5 → **the first 64 dims of every query and key head are rotated; the
  remaining 64 pass through unrotated and are concatenated back.** VERIFIED from
  `transformers/models/glm4_moe/modeling_glm4_moe.py`:
  ```python
  dim = int(head_dim * partial_rotary_factor)
  ...
  q_rot, q_pass = q[..., :rotary_dim], q[..., rotary_dim:]
  q_embed = (q_rot * cos) + (rotate_half(q_rot) * sin)
  q_embed = torch.cat([q_embed, q_pass], dim=-1)
  ```
  The 64 unrotated dims are **NoPE channels**: they contribute a position-independent term to
  the attention logit, letting a head express "match this token wherever it is" alongside the
  rotary half's relative-position term. `apply_rotary_pos_emb` is called on the *full*
  head_dim tensor — the split happens inside, not at the module level.
- The 0.5 is a hard default in the config class, not just this checkpoint. VERIFIED:
  `configuration_glm4_moe.py` line 123 —
  `kwargs.setdefault("partial_rotary_factor", 0.5)  # assign default for BC`.
- **Heritage.** This is inherited GLM convention. ChatGLM's own modeling code builds the
  rotary table at half the head width and splits the tensor — VERIFIED from
  `zai-org/chatglm3-6b/modeling_chatglm.py`:
  `self.rotary_pos_emb = RotaryEmbedding(rotary_dim // 2, ...)`, then in
  `apply_rotary_pos_emb`: `rot_dim = rope_cache.shape[-2] * 2; x, x_pass = x[..., :rot_dim],
  x[..., rot_dim:]` … `return torch.cat((x_out2, x_pass), dim=-1)`. The deeper root is GLM's
  2-D positional encoding — *"We have extended the RoPE to a two-dimensional form to
  accommodate the 2D positional encoding in GLM"* (https://arxiv.org/html/2406.12793v1) — so
  the halved rotary width is the residue of having once budgeted two position axes across one
  head. GLM-130B *"turned back to conventional one-dimensional positional encoding"* while
  keeping the halved width.
- The report names the scheme but not the fraction: *"In the self-attention component, we
  employ Grouped-Query Attention with partial RoPE."* VERIFIED,
  https://ar5iv.labs.arxiv.org/html/2508.06471.
- **Uniform across all 46 layers.** No per-layer RoPE field, no NoPE-layer interleave. Note
  `glm4_moe` has **no** `rope_interleave` field at all (VERIFIED by grep) — it uses the
  `rotate_half` split-half convention, not ChatGLM's adjacent-pair interleave.

### 3. Attention — GQA 12:1, with an unusually wide query side

- `num_attention_heads: 96`, `num_key_value_heads: 8`, `head_dim: 128`. Query width
  96×128 = **12288 = 3.0× hidden_size**; KV width 8×128 = 1024. Each KV head serves 12 query
  heads.
- The 96-head count is deliberate and defended: *"2.5 times more attention heads (96 heads for
  a 5120 hidden dimension)"* … *"Counterintuitively, while this increased head count does not
  improve training loss compared to models with fewer heads, it consistently improves
  performance on reasoning benchmarks such as MMLU and BBH."* VERIFIED,
  https://ar5iv.labs.arxiv.org/html/2508.06471. Air inherits the same 96/8/128 geometry at a
  *narrower* 4096 hidden, so its ratio is more extreme still (3.0× vs GLM-4.7's 2.4×).
- `attention_bias: true` → **bias on q/k/v only**. `o_proj` is hard-coded bias-free. VERIFIED:
  `self.o_proj = nn.Linear(config.num_attention_heads * self.head_dim, config.hidden_size,
  bias=False)` (`modeling_glm4_moe.py:208`). The HF docstring's "and output projection layers"
  wording is wrong for this model.
- `use_qk_norm: false` — **no** per-head Q/K RMSNorm on this rung. A size decision, not a
  generation one: report Table 1 lists `QK-Norm: GLM-4.5 = Yes, GLM-4.5-Air = No`. VERIFIED.
- Attention scale is plain `head_dim**-0.5` (VERIFIED, `modeling_glm4_moe.py:194`).
- **KV-cache footprint**: full per-head K/V is cached (post-projection, post-RoPE).
  2 × 8 × 128 = 2048 elements per layer per token × 46 layers = 94,208 elements →
  **184.0 KiB/token** BF16 → **24.7 GB for a full 131072-token context** (12.3 GB at FP8).
  GQA is buying **12×** over the MHA-equivalent 2208 KiB/token.

### 4. FFN / MoE

- **Dense prefix**: `first_k_dense_replace: 1` — layer 0 is a plain SwiGLU MLP of width
  `intermediate_size: 10944`. VERIFIED dispatch: `if layer_idx >= config.first_k_dense_replace:
  self.mlp = Glm4MoeMoE(config) else: self.mlp = Glm4MoeMLP(config)`
  (`modeling_glm4_moe.py:412`).
- **Sparse body**: layers 1–45 (45 layers). `n_routed_experts: 128`, `num_experts_per_tok: 8`,
  `n_shared_experts: 1`, `moe_intermediate_size: 1408`. Per MoE layer: 2.215B routed-expert
  params, 17.3M shared-expert params, a 4096×128 router.
- **Activation**: `hidden_act: silu` → SwiGLU (gate/up/down) in the dense MLP and every expert.
- **Routing — sigmoid gate + auxiliary-loss-free correction bias.** Report: *"We employ
  loss-free balance routing and sigmoid gates for MoE layers"* (VERIFIED,
  https://ar5iv.labs.arxiv.org/html/2508.06471) — that one sentence is its entire routing
  description. The source is far more specific (VERIFIED, `Glm4MoeTopkRouter.forward`):
  ```python
  scores = router_logits.sigmoid()
  scores_for_choice = scores + self.e_score_correction_bias   # bias affects SELECTION only
  ... grouped mask via n_group / topk_group ...
  topk_indices = torch.topk(scores_for_choice, k=self.top_k, ...)[1]
  topk_weights = scores.gather(1, topk_indices)               # gate weight = UNBIASED sigmoid
  if self.norm_topk_prob: topk_weights /= topk_weights.sum(-1, keepdim=True) + 1e-20
  topk_weights = topk_weights * self.routed_scaling_factor
  ```
  The per-expert `e_score_correction_bias` is a non-gradient buffer nudged by recent expert
  load, so balancing costs no auxiliary-loss gradient. This is DeepSeek-V3's scheme
  (https://arxiv.org/abs/2412.19437), whose config vocabulary GLM's config visibly borrows.
- `norm_topk_prob: true` — the 8 selected raw sigmoid weights renormalise to sum 1.
- `routed_scaling_factor: 1.0` — **the routed branch is not rescaled on this rung.** The
  factor multiplies the *post-normalisation* weights, so 1.0 is a genuine no-op. Contrast 2.5
  on the 355B line.
- `n_group: 1`, `topk_group: 1` — DeepSeek's node-limited group routing is present in the code
  path but **disabled**: one group means plain top-8 over all 128 experts.
- **Shared expert**: one widened MLP, `intermediate_size = moe_intermediate_size ×
  n_shared_experts`, added **unscaled** as a parallel branch:
  `hidden_states = hidden_states + self.shared_experts(residuals)` (VERIFIED).

### 5. Other blocks

- **Norms**: `Glm4MoeRMSNorm`, `rms_norm_eps: 1e-05`, **pure pre-norm, no sandwich norm**.
  VERIFIED from the decoder-layer forward — `input_layernorm` before attention,
  `post_attention_layernorm` before the MLP (Llama-style naming; it is applied *before* the
  MLP, not after the attention output), residual around each.
- **MTP**: `num_nextn_predict_layers: 1`. Report: *"we add an MoE layer as the MTP
  (Multi-Token Prediction) layer to support speculative decoding during inference"* (VERIFIED,
  same source) — inference-time speculation is the only stated purpose. See the MTP section
  below for the transformers-vs-vLLM split.
- **Embeddings**: untied (`tie_word_embeddings: false`).
- **Quantisation**: none in the served repo.

### 6. The repeating motif — dense prefix, then a uniform MoE body

```
embed(151552 → 4096)
├─ ×1   [ RMSNorm → GQA(96q/8kv, d=128, partialRoPE 0.5, qkv-bias) → +residual ]
│       [ RMSNorm → SwiGLU(10944)                                  → +residual ]   dense prefix
└─ ×45  [ RMSNorm → GQA(96q/8kv, d=128, partialRoPE 0.5, qkv-bias) → +residual ]
        [ RMSNorm → MoE(top-8 of 128 ⊕ 1 shared, d_ff 1408, ×1.0)  → +residual ]   sparse body
final RMSNorm → lm_head(4096 → 151552, untied)
[ MTP module at layer index 46 — present in the checkpoint, not loaded by transformers ]
```

---

## Rung 2 — GLM-4.7 (`glm-4.7`)

### 1. Identity

- **GLM-4.7**, Z.ai. HF repo initial commit **2025-12-22** (VERIFIED via commit history,
  author a Z.ai org member); press releases 2025-12-22/23.
- **Parameters — sources conflict; report the conflict.** Z.ai's own GitHub README table says
  **355B-A32B**; vLLM's recipe page for the model says **"moe358B / 32B"**
  (https://recipes.vllm.ai/zai-org/GLM-4.7). The **active count 32B is consistent
  everywhere**. My config arithmetic: **352.8B** main tower, **356.8B** including a one-layer
  MoE MTP module, **32.1B** active per token excluding embeddings. Reading: 355B is the
  marketed tower figure carried over from GLM-4.5 (whose report states *"355B total
  parameters and 32B activated parameters"*, VERIFIED,
  https://ar5iv.labs.arxiv.org/html/2508.06471); 358B is a safetensors-derived count that
  includes the MTP weights and every norm/bias. Not a config contradiction — a counting
  convention — but the two numbers are both in circulation from credible sources.
- **Licence: MIT** (repo metadata; no `LICENSE` file present, same as Air).
- **Tokenizer**: identical to Air — `vocab_size: 151552`, same EOS set
  `[151329, 151336, 151338]` and pad 151329. Untied.
- **No dedicated technical report exists for GLM-4.6 or GLM-4.7.** VERIFIED negative: both
  cards point back to arXiv 2508.06471 (the GLM-4.5 report) as *the* technical report. The
  GLM-4.7 card frames the delta entirely as thinking-mode features and benchmarks — *"GLM-4.7
  further enhances Interleaved Thinking … and introduces Preserved Thinking and Turn-level
  Thinking"*, SWE-bench 73.8% (+5.8), HLE 42.8% (+12.4) over GLM-4.6 — with **no
  architectural claim** (VERIFIED via the transformers doc page, which reproduces the card:
  https://huggingface.co/docs/transformers/model_doc/glm4_moe).
- **Shipped weights**: BF16, no quantisation. Official FP8 sibling `zai-org/GLM-4.7-FP8`.
- **Served in this study**: `max_model_len 131072`, `tp=8`, `--reasoning-parser glm47
  --enable-prefix-caching` — i.e. **at 65% of its architectural window**.

### 2. Positional encoder

Identical scheme to Air: `rope_theta: 1000000`, `rope_scaling: null`,
`partial_rotary_factor: 0.5`, `head_dim: 128` → **64 rotated dims + 64 NoPE pass-through per
head**, uniform across all 92 layers, split-half `rotate_half` convention. The only positional
difference anywhere in the 355B line is `max_position_embeddings: 202752` (vs 131072 in
GLM-4.5).

### 3. Attention — GQA 12:1 with QK-norm

- `num_attention_heads: 96`, `num_key_value_heads: 8`, `head_dim: 128`. Query width
  12288 = **2.4× hidden_size 5120** — the exact configuration the report calls out.
- `attention_bias: true` → q/k/v bias; `o_proj` bias-free (hard-coded).
- `use_qk_norm: true` — **per-head RMSNorm on Q and K, applied before RoPE**, *"to stabilize
  the range of attention logits"* (VERIFIED, report). Order VERIFIED in source:
  ```python
  if self.use_qk_norm:              # main diff from Llama
      query_states = self.q_norm(query_states)
      key_states   = self.k_norm(key_states)
  ...                                # transpose, then apply_rotary_pos_emb
  ```
  Report Table 1 lists QK-Norm as **Yes for GLM-4.5, No for GLM-4.5-Air** — so this flag
  separates *big from small within the 4.5 generation*; its presence on 4.7 is inheritance,
  not a 4.7 change. My independent re-fetch of `zai-org/GLM-4.5/config.json` confirms
  `use_qk_norm: true` there already.
- **KV-cache footprint**: 2048 elements/layer/token × 92 layers = **368.0 KiB/token** BF16 →
  **49.4 GB at 131072 tokens, 76.4 GB at the full 202752** (24.7 / 38.2 GB at FP8).

### 4. FFN / MoE

- **Dense prefix**: `first_k_dense_replace: 3` — layers 0–2 are dense SwiGLU of width 12288.
  Report Table 1: `# Dense Layers 3 | 1`. VERIFIED.
- **Sparse body**: layers 3–91 (89 layers). `n_routed_experts: 160`, top-8, 1 shared,
  `moe_intermediate_size: 1536`. Report Table 1: `# Experts (total) 160 | 128`,
  `# MoE Layers 89 | 45`. VERIFIED. Per MoE layer: 3.775B routed + 23.6M shared.
- **Routing**: identical code path to Air — sigmoid + `e_score_correction_bias` + grouped
  top-k, `norm_topk_prob: true`, `n_group: 1`/`topk_group: 1` (grouping disabled).
- `routed_scaling_factor: 2.5` — the normalised routed mixture is multiplied by 2.5 *before*
  the shared-expert branch is added, i.e. the routed path is deliberately weighted 2.5×
  against the shared path. GLM-4.5 already used 2.5; **Air's 1.0 is the outlier.** No
  published rationale for any of the values — **flagged**.
- `hidden_act: silu` (SwiGLU).

### 5. Other blocks

- RMSNorm eps 1e-05, pure pre-norm, no sandwich norm.
- `num_nextn_predict_layers: 1` — MTP module at layer index 92.
- Untied embeddings; BF16.

### 6. The repeating motif

```
embed(151552 → 5120)
├─ ×3   [ RMSNorm → GQA(96q/8kv, d=128, QK-norm, partialRoPE 0.5, qkv-bias) → +residual ]
│       [ RMSNorm → SwiGLU(12288)                                           → +residual ]   dense prefix
└─ ×89  [ RMSNorm → GQA(96q/8kv, d=128, QK-norm, partialRoPE 0.5, qkv-bias) → +residual ]
        [ RMSNorm → MoE(top-8 of 160 ⊕ 1 shared, d_ff 1536, ×2.5)           → +residual ]   sparse body
final RMSNorm → lm_head(5120 → 151552, untied)
[ MTP module at layer index 92 ]
```

**Deep-and-narrow is the stated design thesis**: *"Different from DeepSeek-V3 and Kimi K2, we
reduce the width (hidden dimension and number of routed experts) of the model and increase its
height (number of layers), as we found that deeper models exhibited better reasoning
capacity."* VERIFIED, https://ar5iv.labs.arxiv.org/html/2508.06471. 92 layers at 5120 hidden
versus DeepSeek-V3's 61 at 7168 is the concrete instance. Note the report's "width" explicitly
includes *expert count*, not just hidden size — and that GLM-4.5 (160 experts) still has fewer
than DeepSeek-V3 (256).

---

## Rung 3 — GLM-4.7-Flash (`glm-4.7-flash`)

### 1. Identity

- **GLM-4.7-Flash**, Z.ai. HF repo initial commit **2026-01-19** (VERIFIED via commit
  history); press coverage 2026-01-20. Roughly four weeks after GLM-4.7 proper.
- **30B total / ~3B active (30B-A3B).** VERIFIED — the HF transformers doc page states
  *"Glm4MoeLite (GLM-4.7-Flash) is a 30B-parameter mixture-of-experts model with approximately
  3B active parameters per token"* (https://huggingface.co/docs/transformers/model_doc/glm4_moe_lite);
  the model card says *"a 30B-A3B MoE model"*. Config arithmetic: **29.9B** main tower
  (30.6B with the MTP module), **3.3B** active excluding embeddings.
- **Licence: MIT** (front-matter `license: mit`).
- **Tokenizer — new and larger: `vocab_size: 154880`**, with a wholly different special-token
  block: EOS `[154820, 154827, 154829]`, pad 154820. That is +3328 tokens over the 151552
  shared by 4.5/4.5-Air/4.6/4.7, in a different id space. **No source, official or
  third-party, explains the expansion** (VERIFIED negative after targeted search) — flagged.
- **Technical report**: none of its own. The card cites arXiv 2508.06471 — a paper describing
  **GQA with partial RoPE**, i.e. a different attention mechanism. Treat that report as
  non-authoritative for this rung.
- **Shipped weights**: `dtype: bfloat16` — note the key is `dtype`, not `torch_dtype`, a
  transformers-v5 rename consistent with `transformers_version: "5.0.0rc0"`. **No official
  FP8 repo** (only third-party quantisations).
- **Served in this study**: `max_model_len 131072`, `tp=4`, `--reasoning-parser glm47
  --enable-prefix-caching`.

### 2. Positional encoder — decoupled rotary sub-head (DeepSeek-V2/V3 split RoPE)

- `rope_theta: 1000000`, `rope_scaling: null`, `max_position_embeddings: 202752`.
- `qk_nope_head_dim: 192` + `qk_rope_head_dim: 64` = 256-dim Q/K heads. **Only the 64 `rope`
  dims carry rotary; the 192 `nope` dims are position-free.** So this rung *also* runs a
  partial rotary — 64/256 = **0.25 effective rotary fraction**, half the 0.5 of its siblings —
  but reaches it structurally rather than by a factor. VERIFIED in source:
  ```python
  q_pass, q_rot = torch.split(q_states, [self.qk_nope_head_dim, self.qk_rope_head_dim], dim=-1)
  ...
  q_rot, k_rot = apply_rotary_pos_emb_interleave(q_rot, k_rot, cos, sin)   # rope_interleave=True
  ...
  query_states = torch.cat((q_pass, q_rot), dim=-1)
  ```
  The rotary key `k_rot` comes from a **separate, MQA-style projection that bypasses the
  latent compression** (see §3) — necessary because a rotation applied after low-rank
  decompression would not commute with MLA's absorbed-matrix trick.
- **Reconciling `partial_rotary_factor: 1.0` with the nope/rope split.** The field is *not*
  saying "rotate everything"; it is scoping the rotary to the `qk_rope_head_dim` sub-head, of
  which 100% is rotated. The mechanism, VERIFIED by grep:
  - `Glm4MoeLiteConfig.attribute_map = {"num_local_experts": "n_routed_experts", "head_dim":
    "qk_rope_head_dim"}` — so `head_dim` resolves to **64**, not 256.
  - `Glm4MoeLiteConfig.__post_init__` **never sets** `partial_rotary_factor` (unlike
    `Glm4MoeConfig`, which does `kwargs.setdefault("partial_rotary_factor", 0.5)`), so it
    falls to the generic default 1.0.
  - The shared rotary-init then computes `dim = int(head_dim * partial_rotary_factor)` =
    `int(64 × 1.0)` = **64** — exactly `qk_rope_head_dim`.

  So 1.0 is the *only* value that makes the rotary table the right size. It is read, but it is
  not a meaningful knob here: a non-1.0 override would break shapes under the default
  `rope_interleave=True` path, which has no pass-through slicing. **Treat it as a frozen
  no-op, not as "full rotary".**
- `rope_interleave: True` (a `Glm4MoeLiteConfig` field with **no counterpart in
  `Glm4MoeConfig`**) — the ChatGLM/DeepSeek adjacent-pair interleave convention, applied to
  the 64 rotary dims. This is a real behavioural difference from the GQA rungs' `rotate_half`.
- Attention scaling goes through `yarn_apply_mscale(config.rope_parameters, qk_head_dim **
  -0.5)` (VERIFIED, `modeling_glm4_moe_lite.py:280`) — a DeepSeek YaRN hook absent from the
  GQA model. With `rope_scaling: null` the mscale is inert, so the effective scale is
  256^-0.5; but the hook's presence is another DeepSeek fingerprint.

### 3. Attention — **Multi-head Latent Attention, confirmed**

Three independent lines of evidence:

1. **The source says so.** `modeling_glm4_moe_lite.py`:
   `class Glm4MoeLiteAttention(nn.Module): """Multi-headed Latent Attention (MLA) from
   Deepseek V2"""`, and the modular source is literally
   `class Glm4MoeLiteAttention(DeepseekV3Attention): pass`. VERIFIED.
2. **The config carries the complete DeepSeek-V2/V3 MLA field set** and nothing else would
   consume it, with HF documenting them as such (*"kv_lora_rank … Rank of the LoRA matrices
   for key and value projections"*). The same doc page's auto-generated example is captioned
   `# Initializing a Deepseek-V3 style configuration` — provenance leaking through
   boilerplate.
3. **Independent reviewers reached the same conclusion.** llama.cpp PR #18936: *"its actually
   a renamed version of GLM4Moe with DeepseekV3Attention (uses MLA) and an added dense expert
   at the start"*; a maintainer who *"compared line-by-line the HF implementation … vs
   deepseek_v3"* found no result-affecting difference, concluding *"from the GGUF perspective
   it's just renamed deepseek"*. VERIFIED, https://github.com/ggml-org/llama.cpp/pull/18936.

**The compression path** (per layer; hidden 2048, 20 heads), all projections VERIFIED:

```
h (2048)
├─ q_a_proj  2048→768  [bias=attention_bias] → q_a_layernorm(768) → q_b_proj 768→20×256=5120 [no bias]
│      └ split per head: q_nope(192) ‖ q_rot(64)→RoPE
└─ kv_a_proj_with_mqa  2048→(512+64)  [bias=attention_bias]
       ├─ c_KV (512) → kv_a_layernorm(512) ──────────────► CACHED
       └─ k_rot (64) → RoPE ──────────────────────────────► CACHED   (1 shared head, MQA-style)
                 ↓ (after cache read)
       kv_b_proj 512 → 20×(192+256)=8960 [no bias] → per-head k_nope(192) ‖ v(256)
score = [q_nope‖q_rot]·[k_nope‖k_rot],  d_k = 256
out = 20×256 = 5120 → o_proj 5120→2048  [bias=attention_bias]
```

- **What is cached is the latent, not per-head K/V.** VERIFIED — the source comment is
  explicit: `# Cache read / write is performed while latent KV is still compressed`, followed
  by `kv_nope, k_rot = past_key_values.update(kv_nope, k_rot, self.layer_idx)` with shapes
  `[b, 1, seq, 512]` and `[b, 1, seq, 64]`. Full per-head K/V is reconstructed by
  `expand_kv` **after** the cache read and never itself cached.
- **`num_attention_heads: 20` = `num_key_value_heads: 20` is not a claim of MHA caching.** It
  makes `num_key_value_groups = 1`, so `repeat_kv` is a no-op — MLA already produces all 20
  heads' K/V from the shared latent via `kv_b_proj`. In the block diagram, do **not** draw 20
  cached KV heads.
- **KV-cache footprint**: `kv_lora_rank + qk_rope_head_dim = 512 + 64 = 576` elements per
  layer per token × 47 layers = 27,072 elements → **52.9 KiB/token** BF16 (26.4 at FP8).
  - At the full 202752-token window: **11.0 GB** (5.5 GB FP8). At the 131072 actually served:
    7.1 GB.
  - Versus its own uncompressed equivalent (20 heads × (256 QK + 256 V) = 10240 elements/layer
    /token = 940 KiB/token): **17.8× compression** — the largest ratio of the three rungs,
    since 96:8 GQA only buys 12×.
  - Versus GLM-4.5-Air's 184.0 KiB/token: Flash carries **3.5× less KV per token** while
    running one more layer and supporting a 1.5× longer window.
- **Attention runs wider than the residual stream**: 20 heads × 256 value dims = 5120 =
  **2.5× the 2048 hidden size**. That is the same "wide attention relative to width" instinct
  the report defends for the 96-head GQA rungs, expressed through MLA head geometry instead of
  head count. **INFERRED** connection — the report does not discuss `glm4_moe_lite`.
- `attention_bias: false` — no biases. Note the *scoping* differs from the GQA rungs: here the
  flag gates `q_a_proj`, `kv_a_proj_with_mqa` **and `o_proj`**, while `q_b_proj`/`kv_b_proj`
  are hard-coded bias-free (VERIFIED). On `glm4_moe` the flag gates q/k/v and `o_proj` is
  hard-coded bias-free — the exact inverse for the output projection.
- **No `use_qk_norm` field and no `q_norm`/`k_norm` anywhere** (VERIFIED by grep over all 728
  lines). The two latent RMSNorms — `q_a_layernorm` (768) and `kv_a_layernorm` (512) — are the
  structural analogue and belong in the block diagram.

### 4. FFN / MoE

- **Dense prefix**: `first_k_dense_replace: 1` — layer 0 dense SwiGLU of width
  `intermediate_size: 10240`. **But that key is not read by transformers v5**:
  `Glm4MoeLiteConfig` has **no** `first_k_dense_replace` field. It uses an explicit per-layer
  list, `mlp_layer_types`, defaulting to `["dense"] + ["sparse"] * (num_hidden_layers - 1)` —
  functionally identical here, but a more general mechanism. VERIFIED.
- **Sparse body**: layers 1–46 (46 layers). `n_routed_experts: 64`, `num_experts_per_tok: 4`,
  `n_shared_experts: 1`, `moe_intermediate_size: 1536`. Per MoE layer: 604M routed + 9.4M
  shared, router 2048×64.
- **Routing**: `Glm4MoeLiteTopkRouter(Glm4MoeTopkRouter): pass` — byte-identical to the GQA
  rungs' router. `norm_topk_prob: true`, `n_group: 1`, `topk_group: 1` (grouping disabled),
  `routed_scaling_factor: 1.8`, `topk_method: "noaux_tc"` (see below — an unread key).
- `hidden_act: silu` (SwiGLU). Shared expert wired identically (one widened MLP, added
  unscaled).
- Note the expert *shape* is inherited from the 355B line (`moe_intermediate_size: 1536`,
  same as GLM-4.7) rather than scaled with hidden size — Flash's experts are unusually wide
  relative to its 2048 hidden dim (**0.75× hidden**, vs GLM-4.7's 0.30× and Air's 0.34×).

### 5. Other blocks

- RMSNorm eps 1e-05, **pure pre-norm, no sandwich** (VERIFIED — identical decoder-layer
  forward to `glm4_moe`), plus the two MLA latent norms inside the attention block.
- `num_nextn_predict_layers: 1` — MTP module at layer index 47.
- Untied embeddings (154880×2048 twice = 634M).
- BF16, no quantisation.

### 6. The repeating motif

```
embed(154880 → 2048)
├─ ×1   [ RMSNorm → MLA(20 heads, q_lora 768, kv_lora 512, nope192‖rope64, v256) → +residual ]
│       [ RMSNorm → SwiGLU(10240)                                                → +residual ]   dense prefix
└─ ×46  [ RMSNorm → MLA(same)                                                    → +residual ]
        [ RMSNorm → MoE(top-4 of 64 ⊕ 1 shared, d_ff 1536, ×1.8)                 → +residual ]   sparse body
final RMSNorm → lm_head(2048 → 154880, untied)
[ MTP module at layer index 47 ]
```

Depth/width ratio 47/2048 makes Flash the **deepest-and-narrowest** of the three (Air
46/4096, GLM-4.7 92/5120) — the GLM design thesis pushed hardest at the smallest scale.

---

## Cross-cutting answers

### `noaux_tc` — a real difference, or a default the others leave implicit?

**A default made explicit — and, in transformers, an unread key.** `topk_method` does not
exist as a field in *either* `Glm4MoeConfig` or `Glm4MoeLiteConfig`, and the string
`topk_method` appears **nowhere** in either modeling file, either configuration file, either
modular file, or vLLM's `glm4_moe.py` / `glm4_moe_lite.py` (VERIFIED — `grep -rn "topk_method"`
over all fetched sources returned zero matches). The sigmoid + `e_score_correction_bias` +
grouped-top-k scheme is the **only, unconditional** implementation; there is nothing to select.

The name is DeepSeek-V3 config vocabulary — `noaux_tc` = "**no aux**iliary loss, **t**op-k with
**c**orrection bias". Air and GLM-4.7 use exactly that scheme; the GLM-4.5 report says so in
words (*"loss-free balance routing and sigmoid gates"*). Their configs simply omit the key.
Flash's config was authored against the DeepSeek-derived `glm4_moe_lite` file and inherited it.

**Conclusion: all three rungs route identically in kind. Only the hyperparameters differ** —
and `routed_scaling_factor` (**1.0 Air / 2.5 GLM-4.7 / 1.8 Flash**) is where they genuinely
do. The mechanism is clear (a post-normalisation gain on the routed branch, before the shared
expert is added); **no source states why these values** — flagged as unexplained.

### MTP — training-only or inference?

**Inference speculation, explicitly.** GLM-4.5 report: *"we add an MoE layer as the MTP
(Multi-Token Prediction) layer to support speculative decoding during inference"* (VERIFIED).
All three rungs declare `num_nextn_predict_layers: 1`; the module is a full extra transformer
block plus an `eh_proj` fusing the previous hidden state with the next token's embedding —
roughly 2.4B / 4.0B / 0.6B parameters on my arithmetic, which is why HF's safetensors-derived
badge for GLM-4.7 exceeds the marketed 355B.

**The runtime split matters for the diagram:**

- **transformers does not implement MTP at all.** The `glm4_moe` doc page states *"The
  implementation in transformers does not include an MTP layer."* Grepping the modeling files
  for `mtp|nextn|MTP` returns **zero matches** (VERIFIED). The only trace is a load-time
  exclusion regex that silently drops the checkpoint's MTP weights:
  ```python
  # modeling_glm4_moe.py:470
  _keys_to_ignore_on_load_unexpected = [r"model\.layers\.92.*", r"model\.layers\.46.*"]
  # modeling_glm4_moe_lite.py:566
  _keys_to_ignore_on_load_unexpected = [r"model\.layers\.47.*"]
  ```
  Those indices are exactly `num_hidden_layers` for GLM-4.7 (92), GLM-4.5-Air (46) and
  GLM-4.7-Flash (47) — confirming the MTP module lives at layer index `num_hidden_layers`, and
  incidentally confirming that these regexes are **hard-coded to the three known checkpoint
  depths** (a `glm4_moe` checkpoint of any other depth would surface its MTP weights as
  unexpected keys — INFERRED fragility, not a documented bug).
- **vLLM does implement it**, as separate registered draft models:
  `"Glm4MoeMTPModel": ("glm4_moe_mtp", "Glm4MoeMTP")` and
  `"Glm4MoeLiteMTPModel": ("glm4_moe_lite_mtp", "Glm4MoeLiteMTP")` (VERIFIED in
  `vllm/model_executor/models/registry.py`), each building a `MultiTokenPredictor` that reuses
  the main model's decoder-layer class with `enorm`/`hnorm`/`eh_proj` Eagle-style fusion and
  `mtp_start_layer_idx = config.num_hidden_layers`. vLLM's own recipe for GLM-4.7 recommends
  `--speculative-config.method mtp --speculative-config.num_speculative_tokens 1`, noting
  *"1 speculative token gives ~90%+ acceptance and best throughput"*
  (https://recipes.vllm.ai/zai-org/GLM-4.7).
- **In this study the MTP head was never used.** `arch_facts.served.vllm_args` for all three
  rungs contains only `--reasoning-parser` and `--enable-prefix-caching` — no
  `--speculative-config`. **Draw the MTP block detached and greyed out.**

### Long context with `rope_scaling: null`

All three declare no scaling scheme yet run 131072 / 202752 / 202752 windows. This is **native
staged long-context training**, not post-hoc interpolation. VERIFIED from the GLM-4.5 report:
*"The maximum sequence length is kept at 4,096 in pre-training, and is extended from 32,768 to
131,072 in mid-training"*, via a dedicated *"Long-Context & Agent Training"* mid-training stage
(https://ar5iv.labs.arxiv.org/html/2508.06471). The enabling architectural choice is
`rope_theta: 1000000` — a 100× larger base than the classic 10000 (still the documented HF
default for `Glm4MoeConfig`), which stretches rotary wavelengths so 128K+ positions stay
distinguishable without rescaling.

For GLM-4.6/4.7's 202752 the mechanism is the same, extended further; the card says only *"The
context window has been expanded from 128K to 200K tokens"* (VERIFIED, GLM-4.6 card).

**Why 202752?** No published rationale — **flagged**. Arithmetically it is exactly
**198 × 1024 = 99 × 2048**, so the true binary size is **198K**; the marketed "200K" rounds up
by ~1%. Being a clean multiple of 2048 makes it evenly splittable across common
sequence/tensor-parallel chunk sizes, which is the usual reason such a figure is not round —
**INFERRED**, not sourced. It is *not* a soft limit: a Z.ai org member settled the repo
discussion with *"202752 is the max"*, explaining that `model_max_length: 128000` in
`tokenizer_config.json` is a conservative tokenizer default, not model capacity
(https://huggingface.co/zai-org/GLM-4.7/discussions/33).

### `attention_bias` and `use_qk_norm` across generations

Both are **within-generation or mechanism-linked, not GLM-4.5→4.7 changes**:

- `use_qk_norm`: GLM-4.5 (355B) = `true`, GLM-4.5-Air = `false` — report Table 1, and
  confirmed by my own re-fetch of GLM-4.5's config. GLM-4.7 inherits `true` unchanged. The
  Air-vs-4.7 QK-norm gap in this ladder is a **big-vs-small contrast inside GLM-4.5**.
- `attention_bias`: `true` on both `glm4_moe` rungs, `false` on Flash. That tracks the
  **mechanism** (GQA→MLA), not the generation — the DeepSeek-derived block ships bias-free,
  and its latent RMSNorms do the conditioning work that bias + QK-norm do on the GQA rungs.

---

## What changes across the ladder

### Scale — within one `glm4_moe` block

| | GLM-4.5-Air | GLM-4.7 |
|---|---|---|
| layers (dense + MoE) | 46 (1 + 45) | 92 (3 + 89) |
| hidden | 4096 | 5120 |
| dense FFN width | 10944 | 12288 |
| routed experts / top-k | 128 / 8 | 160 / 8 |
| expert FFN width | 1408 | 1536 |
| `routed_scaling_factor` | 1.0 | 2.5 |
| QK-norm | off | on |
| total / active | 106B / 12B | 355B / 32B |
| KV cache @128K, BF16 | 24.7 GB | 49.4 GB |
| **unchanged** | 96q/8kv heads, head_dim 128, partial-RoPE 0.5, θ=1e6, no scaling, 1 shared expert, sigmoid+correction-bias routing, `n_group`/`topk_group` = 1, `attention_bias: true`, 1 MTP layer, vocab 151552, untied, pre-norm, BF16 | |

**Every one of those differences already exists inside the GLM-4.5 generation** (GLM-4.5 vs
GLM-4.5-Air). None is a 4.5→4.7 delta.

### Generation — GLM-4.5 → GLM-4.6 → GLM-4.7

**At the config level: `max_position_embeddings` only.** I fetched
`zai-org/GLM-4.5/config.json` and `zai-org/GLM-4.6/config.json` and diffed them against our
pinned GLM-4.7 copy: field-for-field identical except 131072 → 202752 → 202752. Same 92 layers,
5120 hidden, 96/8 heads, 160 experts top-8, `first_k_dense_replace: 3`,
`routed_scaling_factor: 2.5`, `partial_rotary_factor: 0.5`, `rope_theta: 1e6`,
`use_qk_norm: true`, `num_nextn_predict_layers: 1`, vocab 151552, `transformers_version:
4.54.0`.

**The 4.5→4.7 gains are data and post-training, not architecture** — consistent with the
GLM-4.7 card, which claims only thinking-mode features and benchmark improvements and makes no
architectural claim. For the atlas: **do not draw GLM-4.5-Air and GLM-4.7 as
different-generation blocks.** They are the small and large members of one architecture,
released five months apart.

### The genuine architectural break — `glm4_moe_lite`

| | `glm4_moe` (Air, 4.7) | `glm4_moe_lite` (Flash) |
|---|---|---|
| attention | GQA 96q / 8kv, head_dim 128 | **MLA** 20 heads, q_lora 768, kv_lora 512, nope192‖rope64, v256 |
| cached per layer/token | 2048 elements (full K+V) | **576 elements** (latent + shared rotary key) |
| KV cache, BF16 | 184.0 / 368.0 KiB/token | **52.9 KiB/token** |
| compression vs. MHA | 12× | **17.8×** |
| rotary coverage | 64 of 128 dims (0.5) | 64 of 256 dims (0.25), decoupled sub-head |
| `partial_rotary_factor` | 0.5, load-bearing (hard default) | 1.0, frozen no-op (`head_dim`→`qk_rope_head_dim`) |
| rotary convention | `rotate_half` (no `rope_interleave` field) | `rope_interleave: True`, adjacent-pair |
| attention scale | `head_dim**-0.5` | `yarn_apply_mscale(...)` (DeepSeek hook, inert here) |
| `attention_bias` | true → q/k/v; `o_proj` hard-coded off | false → would gate q_a/kv_a **and** `o_proj` |
| QK conditioning | per-head `q_norm`/`k_norm` (flag) | latent `q_a_layernorm` / `kv_a_layernorm` |
| dense/sparse dispatch | `first_k_dense_replace` | `mlp_layer_types` list (`first_k_dense_replace` unread) |
| top-k / experts | 8 of 128 or 160 | 4 of 64 |
| vocab | 151552 | **154880** |
| config dtype key | `torch_dtype` (tf 4.54.0) | `dtype` (tf 5.0.0rc0) |
| **identical** | router code, shared-expert wiring, pre-norm structure, SwiGLU, `rope_theta` 1e6, `rope_scaling` null, 1 shared expert, 1 MTP layer, untied embeddings | |

**Is `Glm4MoeLite` a distinct published architecture?** It is a distinct *implemented* one — it
has its own `model_type`, HF model class and doc page, its own vLLM module
(`Glm4MoeLiteMLAAttention(DeepseekV2MLAAttention)`, VERIFIED), and its own llama.cpp support
PR. It is **not** a distinct *published* one: no paper or technical report describes it, its
card points at a report describing GQA, and every reviewer who read the code concluded it is
DeepSeek-V3's block with GLM's dense-prefix rule. Label it in the atlas as
**"MLA (DeepSeek-V2/V3 lineage) — first GLM checkpoint to use it"**.

---

## Contradictions and unexplained fields

**Contradictions (reported, not smoothed over):**

1. **All three cards cite arXiv 2508.06471 as their technical report.** That paper describes
   GQA with partial RoPE. It does **not** describe MLA and cannot source the Flash rung's
   attention.
2. **transformers MTP, two statements on one page.** The `glm4_moe` overview says *"The
   implementation in transformers does not include an MTP layer"*, while the same page's
   `Glm4MoeConfig` documents `num_mtp_layers` (default 1) as enabling *"speculative decoding
   via `generate(..., use_mtp=True)`"*. My grep resolves it in favour of the overview: no MTP
   code exists, and `use_mtp` appears nowhere. The config field is real but is an
   `attribute_map` alias — `{"num_mtp_layers": "num_nextn_predict_layers"}` — for a value
   nothing reads.
3. **`num_nextn_predict_layers` on the Flash rung is doubly orphaned.** `Glm4MoeLiteConfig`
   has neither the field nor an alias for it (its `attribute_map` is only
   `num_local_experts` and `head_dim`), yet Flash's shipped `config.json` sets it to 1 **and**
   vLLM's `glm4_moe_lite_mtp.py` reads `config.num_nextn_predict_layers` directly. How that
   attribute is surfaced for a real lite checkpoint is unresolved — **open discrepancy**,
   flagged rather than guessed.
4. **GLM-4.7 total parameters: 355B (Z.ai GitHub README) vs 358B (vLLM recipes page).** Active
   32B agrees everywhere. My arithmetic: 352.8B tower / 356.8B with MTP. A counting
   convention, but both figures circulate from credible sources.
5. **Context length: `max_position_embeddings: 202752` vs `model_max_length: 128000`** in the
   tokenizer config. Resolved by a Z.ai maintainer in favour of 202752
   (https://huggingface.co/zai-org/GLM-4.7/discussions/33). Separately, **the marketed "200K"
   overstates the real 198K (= 198 × 1024) by ~1%**, and **this study served all three rungs
   at `max_model_len: 131072`** — so neither 202752-capable rung ran at its architectural
   window.
6. **`Glm4MoeLiteConfig` doc rot**: its documented defaults are Flash's, but the doc text says
   *"Instantiating a configuration with the defaults will yield a similar configuration to
   that of zai-org/GLM-4.5"*, its example is captioned *"Initializing a Deepseek-V3 style
   configuration"*, and the placeholder repo is `meta-glm4_moe_lite/Glm4MoeLite-2-7b-hf`.
   Boilerplate rot — but the DeepSeek-V3 caption is itself evidence of provenance.
7. **HF's documented `attention_bias` description** ("query, key, value **and output**
   projection layers") is wrong for `glm4_moe`, where `o_proj` is hard-coded `bias=False`.
8. **`--reasoning-parser`**: `arch_facts.served` records `glm47` for GLM-4.7-Flash while the
   Flash card's own launch example uses `glm45`. Serving-side only; no architectural
   consequence, but noted.

**Config keys present in the checkpoints but not read by transformers v5** (these are real
findings for a 2026 architecture, not noise):

- `topk_method: "noaux_tc"` (Flash) — no such field in either config class; the string appears
  nowhere in transformers or vLLM GLM code.
- `first_k_dense_replace: 1` (Flash) — superseded by `mlp_layer_types`; functionally
  equivalent here, but the key itself is unread by `Glm4MoeLiteConfig`.
- `num_nextn_predict_layers: 1` (all three) — see contradiction 3; the weights it describes are
  actively excluded at load.
- `partial_rotary_factor: 1.0` (Flash) — read, but frozen at the only value that yields correct
  shapes; not a tunable.

**Fields whose *values* I could not explain from any source:**

- `routed_scaling_factor` = 1.0 / 2.5 / 1.8. Mechanism clear, values unexplained; the GLM-4.5
  report never mentions the field.
- Why `max_position_embeddings` is exactly 202752. My divisibility argument is INFERRED.
- Why Flash's vocabulary grew 151552 → 154880 and moved the special-token ids. No source found,
  official or third-party.
- `n_group: 1` / `topk_group: 1` on all three — DeepSeek's node-limited group routing is
  carried in the code path and switched off. Whether GLM ever intended to use it is unknown.
- `initializer_range: 0.02` (Air, GLM-4.7) — training-only, no inference effect; absent from
  the Flash config.

**`derived.unclassified` is empty for all three rungs** — every field in all three configs was
classified by the fetch script, and every field is accounted for above.

---

## Sources

1. GLM-4.5 technical report, *GLM-4.5: Agentic, Reasoning, and Coding (ARC) Foundation
   Models*, arXiv 2508.06471 — https://arxiv.org/abs/2508.06471 ; full text read via
   https://ar5iv.labs.arxiv.org/html/2508.06471 (arXiv's own HTML rendering 404s).
2. HF transformers docs, `glm4_moe` (v5.14) — https://huggingface.co/docs/transformers/model_doc/glm4_moe
3. HF transformers docs, `glm4_moe` (v4.56 — the version the Air/4.7 configs were written
   against) — https://huggingface.co/docs/transformers/v4.56.0/en/model_doc/glm4_moe
4. HF transformers docs, `glm4_moe_lite` — https://huggingface.co/docs/transformers/model_doc/glm4_moe_lite
5. transformers source (read directly, `main` branch):
   `src/transformers/models/glm4_moe/{modeling,configuration,modular}_glm4_moe.py` and
   `src/transformers/models/glm4_moe_lite/{modeling,configuration,modular}_glm4_moe_lite.py`,
   plus `src/transformers/modeling_rope_utils.py` —
   https://github.com/huggingface/transformers/tree/main/src/transformers/models/glm4_moe
6. vLLM source (read directly): `vllm/model_executor/models/{glm4_moe, glm4_moe_lite,
   glm4_moe_mtp, glm4_moe_lite_mtp, registry}.py` —
   https://github.com/vllm-project/vllm/tree/main/vllm/model_executor/models
7. vLLM recipe page for GLM-4.7 (speculative-decoding flags) — https://recipes.vllm.ai/zai-org/GLM-4.7
8. llama.cpp PR #18936, *support Glm4MoeLite* — https://github.com/ggml-org/llama.cpp/pull/18936
9. `zai-org/GLM-4.5` card + `config.json` — https://huggingface.co/zai-org/GLM-4.5 ,
   https://huggingface.co/zai-org/GLM-4.5/raw/main/config.json
10. `zai-org/GLM-4.6` `config.json` — https://huggingface.co/zai-org/GLM-4.6/raw/main/config.json
11. `zai-org/GLM-4.7` discussion #33 (context-length resolution) —
    https://huggingface.co/zai-org/GLM-4.7/discussions/33
12. `zai-org/GLM-4.5-Air`, `zai-org/GLM-4.7`, `zai-org/GLM-4.7-Flash` model cards and commit
    histories — https://huggingface.co/zai-org/GLM-4.5-Air ,
    https://huggingface.co/zai-org/GLM-4.7 , https://huggingface.co/zai-org/GLM-4.7-Flash
13. ChatGLM paper, *ChatGLM: A Family of Large Language Models from GLM-130B to GLM-4 All
    Tools* — https://arxiv.org/html/2406.12793v1
14. ChatGLM3-6B modeling source (half-rotary implementation) —
    https://huggingface.co/zai-org/chatglm3-6b/raw/main/modeling_chatglm.py
15. DeepSeek-V3 technical report (MLA, auxiliary-loss-free routing, the `noaux_tc` schema
    origin) — https://arxiv.org/abs/2412.19437
