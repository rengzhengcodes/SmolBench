<!--
Blind replication of the MoE family slate research (moe_slate_replication_prompt.md).
Run 2026-08-10, workflow wf_72a1c622-ebb (27 agents: 8 discovery, 1 consolidation,
9 verify, 9 refute/judge/synthesize; sonnet artifact workers, opus adversarial
checkers + judge + synthesis). Conducted BLIND: no worker prompt contained the
2026-08-02 locked slate or any of its family names.
-->

# Open-weight family ladders for a cross-lab parameter-scaling study
**Knowledge state: 2026-08-10.** No model released after this date is counted. All evidence below was fetched anonymously from huggingface.co and raw.githubusercontent.com on 2026-08-10; where a claim rests on evidence I could not date-bound, it is flagged.

---

## 1. Recommended slate

Six families, one lab each: **CN 2 / US 2 / EU 1 / KR 1**. All arithmetic is against a **1,128 GB** node (8× H200, 141 GB each); the "+10%" column applies a runtime-overhead heuristic (activations, CUDA graphs, allocator slack) that is an **assumption, not a measurement**.

| # | Lab / country | Family (counted rungs, total→active) | Span | Context (shipped `config.json`) | Reasoning mechanism | Toggle class | License | Gated | Best official precision | Largest counted rung: weights + 128k KV | Node verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Qwen / Alibaba** (CN) | Qwen3.5: 27B dense · 35B-A3B · 122B-A10B · **397B-A17B** | 27.78B→403.42B = **14.5×** | 262,144 on all 4, `rope_type:"default"` (native, no scaling) | `enable_thinking` in shipped `chat_template.jinja`, md5 `94f89e03…` identical on all 4 rungs | **same-weights toggle** (tier 1) | Apache-2.0 | No | **BF16** (`Qwen3.5-397B-A17B`, created 2026-02-16, *older* than the FP8 repo) | 806.80 + 4.03 = **810.82 GB** (KV: only 15/60 layers are `full_attention`; 2·15·2·256·131072·2 B = 4.0265 GB) | **Fits**, ~204 GB headroom at BF16; 410.16 GB at FP8 |
| 2 | **NVIDIA** (US) | Nemotron 3: Nano-4B · Nano-30B-A3B · **Super-120B-A12B** (*Ultra-550B not counted*) | 3.97B→123.61B = **31×** | 262,144 on all counted rungs (no `rope_scaling` key; `rope_theta` 10000) | `enable_thinking` at L12 of every shipped jinja; Super adds `low_effort` → `{reasoning effort: low}` | **same-weights toggle** + effort string | NVIDIA custom / OpenMDW ("other") | No | BF16 | 247.22 + 1.07 = **248.30 GB** (×1.1 = 273.1) | **Fits**, ~78% of node unused |
| 3 | **Google DeepMind** (US) | Gemma 4: E2B · E4B · 12B · 26B-A4B · **31B** (all `-it`) | 5.12B→31.27B = **6.1×** | 131,072 (E2B/E4B) / 262,144 (12B, 26B, 31B) | `enable_thinking \| default(false)` → injects `<|think|>` into the opening system turn; grep-confirmed at L186/L190/L193-195 in **all five** templates | **same-weights toggle** (tier 1) | Apache-2.0 | No (contrast: `google/gemma-3-*` are `gated:"manual"`) | BF16 | 62.55 + ~11.6 = **74.1 GB** (×1.1 = 81.6) | **Fits trivially** |
| 4 | **Zhipu AI / Z.ai** (CN) | GLM-4.x: 4.7-Flash 31.2B-A3B · 4.5-Air 110.5B-A12B · 4.5 358.3B-A32B · **4.7 358.3B-A32B** — **cross-generation** | 31.22B→358.34B = **11.5×** (only **3 distinct size tiers**) | 202,752 (4.7, 4.7-Flash) / 131,072 (4.5, 4.5-Air) | `enable_thinking` in all 4 shipped templates, **default ON**; 4.5/Air use a `/nothink` marker + forced `<think></think>`, 4.7/Flash use bare `</think>` vs `<think>` | **same-weights toggle** (tier 1, but no true "off-by-default") | MIT | No | BF16 (an official ungated GLM-4.7-FP8 also exists) | 716.68 + 49.39 = **766.07 GB** (×1.1 = 842.68) | **Fits**, ~285 GB headroom |
| 5 | **Mistral AI** (FR — EU seat) | Ministral-3 Reasoning 2512: 3B · 8B · **14B** (+14B-Instruct as the non-think pair) | 4.6× nameplate; **3.3×** measured (4.25B→13.95B) | 262,144, via **shipped YaRN** (`rope_parameters` type `yarn`, factor 16, orig 16,384) | `[THINK]…[/THINK]` protocol baked into the default system message of a byte-identical template (md5 `f9ce03df…`, 12,207 B) on all 3; added tokens 34/35 | **paired thinking / non-thinking siblings** (tier 2) | Apache-2.0 | No | BF16 | 27.89 + 21.47 = **49.36 GB** (×1.1 = 54.3) | **Fits trivially** (single-GPU class) |
| 6 | **LG AI Research** (KR) | EXAONE 4.0-32B · EXAONE 4.5-33B · **K-EXAONE-236B-A23B** (*750B not counted*) — **cross-generation** | 32.0B→237.1B = **7.4×** | 131,072 (4.0-32B, llama3 rope factor 16) / 262,144 (4.5-33B, 236B) | `enable_thinking` line-cited per rung (4.0-32B L141 default **off**; 4.5-33B L156 / 236B L154 default **on**) | **same-weights toggle** (tier 1, inconsistent default across rungs) | EXAONE custom ("other") | No | BF16 | 474.20 + 25.77 = **499.97 GB** (×1.1 = 550.0) | **Fits**, ~51% of node unused |

**Standby (verified, not seated):** Deep Cogito v1-preview 3B/8B/70B (US). The adversarial checker's own summary: *"Refutation FAILED: all 7 claims SURVIVE re-fetch"* ([registry](https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/model_executor/models/registry.py), [405B template](https://huggingface.co/deepcogito/cogito-v2-preview-llama-405B/resolve/main/chat_template.jinja)). 20× span, tier-1 toggle, `LlamaForCausalLM` = the most mature vLLM path, 131,072 shipped rope on all three, trivial fit. It is off the slate only because its rungs are **Llama fine-tunes, not an original pretrained ladder**, and because a third US seat would unbalance CN/US. Swap it in for the Korean seat if three US labs are preferred.

### Single-node arithmetic, shown per family

- **Qwen3.5-397B-A17B (BF16)** — `model.safetensors.index.json` `metadata.total_size = 806,795,875,168` → 806.80 GB ([source](https://huggingface.co/Qwen/Qwen3.5-397B-A17B/resolve/main/model.safetensors.index.json)). KV from config: `Counter({'linear_attention':45,'full_attention':15})`, `num_key_value_heads=2`, `head_dim=256` → 2·15·2·256·131072·2 B = 4,026,531,840 B = 4.0265 GB. **810.82 / 1,128 = 71.9%.** Linear-attention recurrent state adds ~0.19 GB/seq — negligible at batch 1, **not negligible at high concurrency**.
- **Nemotron-3-Super-120B (BF16)** — index `total_size` 247.22 GB; `layers_block_type` gives 8 attention sublayers of 88 → 8·2·2·128·131072·2 B = 1.0737 GB. **248.30 GB raw, 273.1 GB with overhead.** Mamba/SSM state (~0.2 GB/seq on Ultra-class configs) is a term this formula omits entirely — harmless here, material for anything sized near the node limit.
- **Gemma-4-31B (BF16)** — index `total_size = 62,546,177,752`, exactly 2 × the 31,273,088,876 BF16 params, ruling out packed-quant inflation. **KV corrected during verification**: the naive uniform-GQA figure (128.85 GB) is wrong; the config ships `num_global_key_value_heads=4`, `global_head_dim=512` on 10 `full_attention` layers and `sliding_window=1024` on the other 50 → **~11.6 GB**, so 74.1 GB total. Fit holds *a fortiori*.
- **GLM-4.7 (BF16)** — tree-API sum of 93 shards = 716,681,196,792 B. **Trap handled:** `index.json metadata.total_size = 358,337,791,296` is the *parameter count mislabelled as bytes*; the tree sum is exactly 2×, confirming BF16. KV: 2·92·8·128·131072·2 = 49,392,123,904 B = 49.39 GB (conservative — one of the 92 layers is MTP). **766.07 raw, 842.68 with overhead.**
- **Ministral-3-14B-Reasoning (BF16)** — index `total_size = 27,890,063,360`; ÷2 = 13,945,031,680 = the API's BF16 param count exactly. KV 2·40·8·128·131072·2 = 21.47 GB. **49.36 GB.**
- **K-EXAONE-236B-A23B (BF16)** — index `total_size = 237,099,669,632 × 2` → 474.199339264 GB. KV 2·48·8·128·131072·2 = 25.77 GB. **499.97 GB.**

---

## 2. Compliance matrix

**pass** = artifact inspected, claim survived refutation · **bend** = accepted with a named deviation · **fail** = would have been disqualifying (none remain on the slate).

| Criterion | Qwen3.5 | Nemotron 3 | Gemma 4 | GLM-4.x | Ministral-3 | EXAONE 4.x |
|---|---|---|---|---|---|---|
| **F1 Reasoning in shipped template/config** | pass | pass | pass | pass | **bend** | pass |
| **F2 ≥128k in shipped `config.json`** | pass (262,144 native) | pass (262,144) | pass (131,072 / 262,144) | pass (131,072 / 202,752) | **bend** (262,144 via shipped YaRN) | pass (131,072 / 262,144) |
| **F3 Open weights, ungated (host API)** | pass | pass | pass | pass | pass | pass |
| **F4 Released ≥ ~2024-08** | pass (2026-02) | pass (2025-12 → 2026-03) | pass (2026-03 → 2026-05) | pass (2025-07 → 2026-01) | pass (2025-10 repo / 2025-12 push) | pass (2025-07 → 2026-04) |
| **F5 One node, upstream vLLM, best official precision** | pass | **bend** (Ultra excluded) | pass | pass | pass | **bend** (750B excluded) |
| **P-a ≥3 rungs (hard)** | pass (4) | pass (3 counted) | pass (5) | pass (4 repos / **3 size tiers**) | pass (3) | pass (3 counted) |
| **P-b Toggle quality** | pass (tier 1) | pass (tier 1 + effort) | pass (tier 1) | **bend** (tier 1, default-on) | **bend** (tier 2) | **bend** (tier 1, split defaults) |
| **P-c Same generation** | pass | **bend** (dense vs MoE) | pass (sub-gen split) | **fail→bend** (cross-gen, flagged) | pass | **fail→bend** (4 generations, flagged) |
| **P-d1 Span ≥10×** | pass (14.5×) | pass (31×) | **bend** (6.1×) | pass (11.5×) | **bend** (3.3–4.6×) | **bend** (7.4×) |
| **P-d2 License permissiveness** | pass (Apache-2.0) | **bend** (custom) | pass (Apache-2.0) | pass (MIT) | pass (Apache-2.0) | **bend** (custom; 750B is Apache but uncounted) |
| **P-d3 vLLM maturity** | pass (in tagged **v0.26.0**, not just main) | pass (+`MIXED_PRECISION` path validated SM75+) | **bend** (arch new; main-only) | pass | pass | **bend** (main-only) |

### Every bend, named

1. **Ministral-3, F1 — toggle is a system-message protocol, not a boolean.** Accepted: the `[THINK]…[/THINK]` instruction block is *in the shipped `chat_template.jinja`* (md5 `f9ce03df8c692f42b2aeb78024e29f4f`, L6, with L36-37 rendering `'[THINK]' + block['thinking']`) and the tokens are real vocabulary entries (`('34','[THINK]'),('35','[/THINK]')`) — [source](https://huggingface.co/mistralai/Ministral-3-3B-Reasoning-2512/resolve/main/chat_template.jinja). Why: the filter asks for a mechanism in the shipped artifact, which this is. **Caveat surfaced:** the THINK text is injected *only if* `messages[0].role != 'system'` — supplying your own system prompt silently disables it. This is a live experimental hazard for a benchmark harness.
2. **Ministral-3, F2 — YaRN, not native.** Accepted per the filter's explicit allowance for officially-shipped rope scaling: `text_config.rope_parameters = {rope_type:'yarn', factor:16.0, original_max_position_embeddings:16384, …}`, 16,384 × 16 = 262,144, self-consistent, plus `generation_config.max_length=262144` ([source](https://huggingface.co/mistralai/Ministral-3-14B-Reasoning-2512/resolve/main/config.json)). **Fidelity caveat:** upstream vLLM's yarn branch (`rope/__init__.py:243`) **drops** `llama_4_scaling_beta` and `mscale`, so served long-context behaviour may differ from the reference implementation.
3. **Ministral-3, P-b — paired siblings, not one checkpoint.** The 14B-Instruct template (11,913 B, md5 `6bd9253…`) greps **zero** THINK / `enable_thinking` / `reasoning_effort` tokens and its `render_content` macro lacks `support_thinking`. Two checkpoints = tier 2.
4. **Nemotron 3, F5 — Ultra-550B excluded.** REFUTED at the strict reading: NVIDIA ships an ungated BF16 Ultra created *four minutes before* the NVFP4 repo, index `total_size = 1,121,049,257,984` → **1,121.05 GB = 99.4% of the node** before KV ([source](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16/resolve/main/model.safetensors.index.json)). Under "best *official* precision read strictly," Ultra is not countable and the ladder tops out at Super-120B. (At the lenient reading — NVFP4 is also official, 352.28 GB, and `ModelOptMixedPrecisionConfig.get_min_capability()` returns 75 with an SM75/SM80 end-to-end validation comment, so H200=SM90 is covered — Ultra returns as a 4th rung and span goes to 141×. No admission changes either way.)
5. **Nemotron 3, P-c — Nano-4B is dense, siblings are hybrid MoE.** All four declare `model_type: nemotron_h`, but Nano-4B has 17 plain MLP layers and no `n_routed_experts`. A parameter-scaling study across it crosses a dense→MoE boundary at the bottom rung.
6. **Nemotron 3, P-d2 — custom license** ("other"; NVIDIA Open Model / OpenMDW). Non-blocking, ranked below Apache/MIT.
7. **Gemma 4, P-d1 — 6.1× span**, under the 10× preference. Accepted for the tier-1 toggle, five rungs, Apache-2.0, and genuinely ungated status (its own `gemma-3` siblings are `gated:"manual"`, so this is a real difference, not a default).
8. **Gemma 4, P-d3 — vLLM maturity is a paper check.** `Gemma4ForConditionalGeneration → gemma4_mm` (registry L410) and `Gemma4UnifiedForConditionalGeneration → gemma4_unified` (L411-413) exist on **main**; no tagged release was confirmed and no wheel was built.
9. **GLM-4.x, P-c — cross-generation, and the checker refuted the dossier for not flagging it.** Verbatim: *"createdAt proves two trains: 2025-07-20 (4.5, Air) vs 2025-12-22 (4.7) and 2026-01-19 (4.7-Flash) … 4.7-Flash is a different architecture class: `Glm4MoeLiteForCausalLM`, model_type `glm4_moe_lite`, MLA (kv_lora_rank 512, q_lora_rank 768) vs `Glm4MoeForCausalLM` GQA head_dim 128"* ([source](https://huggingface.co/zai-org/GLM-4.7-Flash/resolve/main/config.json)). Accepted because gen-4.7 alone has only 2 rungs, so the mix is *required* — and the report flags it, per the task's cross-generation allowance. Additional bend: **only 3 distinct size tiers** (4.5 and 4.7 are both 358,337,791,296 params). For a parameter-scaling study, use 4.7-Flash / 4.5-Air / 4.7 and treat GLM-4.5 as a same-size replicate.
10. **GLM-4.x, P-b — thinking is default ON.** `enable_thinking` suppresses rather than enables. Still a one-checkpoint, per-request flag = tier 1, but a benchmark's "non-thinking" arm depends on the harness setting the flag, not on the default.
11. **EXAONE, F5 — 750B excluded** under the same strict rule as Nemotron Ultra: BF16 1,498.72 + 41.88 = **1,540.59 GB > 1,128 GB**. Its official FP8 sibling (`-750B-A37B-FP8`, verified `quant_method:'fp8'`, `total_size = 752,076,344,832` ≈ 1.0036 B/param) **does** fit at 793.95 GB (873.35 with overhead) — so under the lenient reading the 750B returns and span rises to 23×.
12. **EXAONE, P-c — four generations, refuted.** *"`model_type: exaone4` vocab 102400, vs `exaone4_5` + `exaone4_5_vision` vocab 153600 (tokenizer swap), vs two `exaone_moe` rungs split by `transformers_version` 5.1.0 (128 experts, `first_k_dense_replace`) vs 5.9.0 (those keys gone, 256 experts, `swiglu_limits`, `mtp_num_speculative_steps 4`)"* ([source](https://huggingface.co/LGAI-EXAONE/K-EXAONE-236B-A23B/resolve/main/config.json)). Accepted and flagged; hard filters unaffected. Additional bends: 32B and 33B are **near-duplicate scales** (a weak bottom of the ladder), 4.5-33B is a **multimodal wrapper** whose `head_dim` is not shipped (only derivable as 5120/40), and reasoning defaults **differ across rungs** (off on 4.0-32B, on elsewhere).
13. **Qwen3.5, F5 — precision bookkeeping corrected, not bent.** The only refutation in the whole family: the dossier costed the top rung at FP8 (406.13 GB) when an ungated BF16 repo exists and is *older*. Corrected to 806.80 GB; filter still passes. Recorded here because the *number* in an earlier draft was wrong.

---

## 3. Killed candidates

Each with the specific filter and the artifact that proves it.

| Family | Killing filter | Proof |
|---|---|---|
| **DeepSeek V3.1 / V3.2 / V4** (CN) | **F1 — reasoning mechanism in the *shipped* template/config** | `chat_template.jinja` → **HTTP 404 on all four repos**; `tokenizer_config.json` shows `has chat_template: False` for V3.2, V4-Flash, V4-Pro (keys stop at `tokenizer_class`); `config.json`/`generation_config.json` carry no reasoning field; upstream vLLM `_MODEL_TYPE_TO_CHAT_TEMPLATE_FALLBACK` has **no `deepseek_v32` / `deepseek_v4` entry**. Only V3.1 ships the toggle → [tokenizer_config](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/main/tokenizer_config.json). With one compliant rung it also fails the ≥3-rung floor. **Explicitly surfaced, not smoothed:** a real same-weights toggle *does* exist in shipped Python tooling — `encoding_dsv4.py` L241 `assert thinking_mode in ["chat","thinking"]`, L389 `prompt += thinking_start_token`, L261 `assert reasoning_effort in ['max', None, 'high']` ([source](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/resolve/main/encoding/encoding_dsv4.py)). That is exactly the "toggle in a Python encoder rather than the shipped template" case the task names as disqualifying. Everything else about DeepSeek passes: MIT, ungated, 163,840–1,048,576 ctx, V4-Pro 864.72 GB + ~9.21 GB KV = 961.3 GB with overhead, all archs in upstream vLLM with `vllm/models/deepseek_v4/` in-tree. |
| **gpt-oss** (OpenAI, US) | **P-a, ≥3 rungs (hard)** | Only 2 tiers exist; the "safeguard" repos are fine-tunes, not size rungs. **No hard-filter defect was claimed** — this is the first promotion if the 3-rung rule is relaxed. *Screen-stage claim; not independently re-verified.* |
| **Hermes 4** (Nous Research, US) | **F2 — context** | `Hermes-4-14B` ships 40,960 ctx, leaving only 2 counted rungs. Toggle quality was rated best-in-sweep. *Screen-stage claim; unverified.* |
| **Ling 2.6** (InclusionAI / Ant, CN) | **F5 — one-node fit**, plus ≥3 rungs | Only 2 rungs in gen 2.6 (gen 2.0 caps at 32,768 ctx); `Ling-2.6-1T` has no official FP8/Int8 sibling found, so BF16 ~2 TB fails one node. Would have been the natural third Chinese seat. *Unverified.* |
| **ERNIE 4.5** (Baidu, CN) | **F1 on the larger tiers** — **partly BLOCKED** | Only the 21B-A3B tier has a Thinking checkpoint; `300B-A47B-Thinking` **returns HTTP 401**. Per the evidence standard this is a **blocked verification, not a pass and not a clean fail** — it is recorded as unresolved and the family is not seated. |
| **Solar Open** (Upstage, KR) | **P-a, ≥3 rungs** | Clears every hard filter but has 2 rungs; older Solar Pro repos are tokenizer-only. Also cross-generation (Solar-Open 2025-12 + Solar-Open2 2026-07). *Unverified.* |
| **Trinity** (Arcee AI, US) | **F1 on Trinity-Nano-Preview** | Zero think handling in tokenizer or template → only 2 counted rungs; reasoning style is also inconsistent (always-on Mini vs paired Large sibling). *Unverified.* |
| **LFM2.5** (Liquid AI, US) | **F1 — per-tier reasoning unproven** | Only the 1.2B has an explicit Thinking SKU; LFM custom license. Four same-gen rungs and ~24× span make it the best re-check candidate if a seat opens. *Unverified.* |

### Screen-stage kills (single-pass, **not** adversarially re-verified — treat as leads)

- **Meta (Llama 4 / 3.1)** — F1: no reasoning mechanism in either family; Scout is `gated:"manual"` so its config is **unfetchable anonymously (BLOCKED)**; Llama 3.1 is 2024-07, outside the window.
- **IBM (Granite 4.1)** — F1: ships `<think>`/`<think_on>` control *tokens* but `chat_template.jinja` has no think logic — the toggle is not wired. Granite 3.2 has a real thinking template but only 2 rungs.
- **Microsoft (Phi-4-reasoning)** — F2: 14B/15B tiers cap at 32,768 with `rope_scaling: null`; what remains is two same-size ~3.8B checkpoints.
- **Ai2 (OLMo 3 / 3.1 Think)** — F2: every Think and Instruct repo ships 65,536 (YaRN 8× over 8,192); also only 2 distinct sizes.
- **Tencent (Hunyuan)** — F2: 7B and the A13B flagship ship 32,768 with dynamic-NTK rope, contradicting the card's 256K claim — the textbook card-only case the filter excludes.
- **Huawei (openPangu 2.0)** — F5: `OpenPanguV2ForCausalLM` absent from upstream vLLM with no `modeling_*.py` shipped; also 2 rungs.
- **InclusionAI (Ring 2.0/2.6)** — F2: Ring-mini/flash 32,768; Ring-1T-FP8 65,536 and ~1 TB; only Ring-2.6-1T clears 128k → one rung.
- **Moonshot (Kimi K2/K3)** — P-a: every K2 is ~1.03 T and K3 ~2.78 T; no Air/Lite sibling. Kimi-Linear-48B and Kimi-Dev-72B are separate architectures.
- **MiniMax (Text-01/M1/M2/M3)** — P-a: one text size per generation; M1 was **removed from upstream vLLM after v0.23**.
- **Thinking Machines Lab (Inkling)** — P-a: only 2 sizes (975B-A41 + 276B-A12, 3.5× span). Otherwise passes everything (Apache-2.0, 1M ctx, effort map in the shipped template, NVFP4 ~592 GB fits). **A third size flips this family onto the slate.**
- **Also killed at screen:** Skywork-OR1 (2 rungs, both DeepSeek-R1-Distill fine-tunes), ServiceNow Apriel (F1 on the small rung; version ladder not size ladder), TII Falcon-H1 (F1; only H1R-7B has think tags, one size), xAI Grok (no ladder, no toggle, grok-1 pre-window), Sarvam (2 rungs; custom archs unconfirmed upstream — F5 risk), StepFun (same-size version bumps; Step3 at 65.5k), OpenBMB/Baichuan/ByteDance (F2 at 32–65k, or single sizes), Cohere Command-A-Reasoning (single gated size), Zyphra ZAYA1 (absent upstream), Databricks DBRX-2 (unshipped), Snowflake Arctic (pre-window).

---

## 4. Rest of field — what would have to change

| Family | Change required to qualify |
|---|---|
| **gpt-oss** (OpenAI) | A third size tier. Nothing else blocks it — it is the top alternate. |
| **Thinking Machines Inkling** | A third size. Everything else already verified in a prior study. |
| **Hermes 4** | A 14B (or any third tier) shipping ≥128k in `config.json`. |
| **DeepSeek** | Ship a `chat_template.jinja` (or a `chat_template` key, or an upstream vLLM fallback entry) for V3.2/V4 that exposes `thinking_mode`. The behaviour already exists in `encoding_dsv4.py`; it is a packaging gap, and a one-line upstream fallback registration would resurrect the strongest CN alternate. |
| **Ling 2.6** | An official FP8/Int8 1T checkpoint, plus a third ≥128k rung. |
| **ERNIE 4.5** | Ungate `300B-A47B-Thinking` so the config can be verified, and ship Thinking checkpoints on the larger tiers. |
| **LFM2.5** | Thinking SKUs above the 1.2B tier. |
| **Arcee Trinity** | Think handling in Trinity-Nano's shipped template; consistent toggle semantics across tiers. |
| **Solar Open** | A third rung with real weights. |
| **IBM Granite 4.1** | Wire the existing `<think_on>` tokens into `chat_template.jinja`. Closest "almost" in the whole sweep — the tokens are already in the vocabulary. |
| **Ai2 OLMo** | Raise shipped `max_position_embeddings` past 131,072 (currently 65,536) and add a third size. |
| **Sarvam / Huawei / Zyphra** | Upstream vLLM registry entries for their custom architectures. |

---

## 5. Watch triggers

Any one of these changes the slate:

1. **A third gpt-oss size** → seats OpenAI immediately; likely displaces Gemma 4 (weakest span among US seats) or takes a 7th slot.
2. **A third Inkling size** from Thinking Machines → seats a second Apache-2.0 US family with a 1M-context effort map.
3. **DeepSeek ships a chat template for V4** (or vLLM adds a `deepseek_v4` fallback) → DeepSeek displaces GLM-4.x as the CN #2, because DeepSeek's ladder is genuinely three sizes (291B / 671B / 1.6T) whereas GLM has only three *distinct* tiers across two generations.
4. **A Qwen3.5 rung above 397B, or an FP8-only flagship** → re-run F5; the BF16 headroom (204 GB) is comfortable but not unlimited.
5. **NVIDIA ships an official Nemotron-3 Ultra that fits BF16 headroom**, or the study adopts the lenient precision reading → Ultra returns, span 31×→141×.
6. **A K-EXAONE rung between 33B and 236B** → fixes the 32B/33B near-duplicate bottom and makes the Korean seat a genuine 4-rung ladder.
7. **Mistral ships a Ministral-3 rung ≥30B, or a same-weights `enable_thinking` flag** → upgrades the EU seat from two bends to zero.
8. **Google ships a Gemma 4 rung >60B** → fixes the 6.1× span, the slate's weakest soft criterion.
9. **Granite 4.1 wires its think tokens into the template** → seats IBM, a well-cited US lab, with a genuine same-gen ladder.
10. **Any lab publishing a ≥3-rung ladder after 2026-08-10** — out of scope for this report by construction; re-run the sweep.

---

## 6. Method and caveats

### What was done
Two independent passes per finalist. Pass 1 (dossier) fetched `api/models/*`, `config.json`, `chat_template.jinja`, `tokenizer_config.json`, `model.safetensors.index.json`, the paginated tree API, and the upstream vLLM `registry.py` for every candidate rung. Pass 2 (adversarial) re-fetched all of it independently and attempted to **refute** each of 7 numbered claims per family (c1 reasoning / c2 context / c3 gating / c4 date / c5 single-node / c6 params / c7 generation), with the rule that a refutation requires a verbatim quote plus URL and that "looks right" is not a verdict. **Six refutations landed across the slate** and all are reflected above: Qwen c5b (BF16 is the older, better official precision), Nemotron c5 (Ultra BF16 = 99.4% of node), Gemma reasoning.mechanism (templates are *not* byte-identical — two variants, though the `enable_thinking` gate is in both), GLM c7 (cross-generation, undeclared), EXAONE c7 (four generations, undeclared), DeepSeek c1 + c1b (no shipped template; toggle is Python-only).

### Methodology traps that actually fired
- **Index metadata mislabelled as bytes.** GLM's `metadata.total_size` equals the *parameter count*, and the tree sum is exactly 2×. Trusting the index would have understated GLM by half.
- **Stale 2 B/param index metadata on FP8 checkpoints.** DeepSeek V3.1's `total_size = 1,369,062,772,000` is exactly 2 × its 684,531,386,000 params, but the checkpoint is FP8 and really sums to 688.59 GB. Tree-sums were used instead.
- **Packed low-bit inflation.** DeepSeek V4-Pro's `I8: 1,572,763,336,704` is *logical*, not bytes — the shard header shows `experts.0.w1.weight` as `[3072, 3584]` where 3584 = 7168/2, i.e. FP4 packed two-per-byte, matching `"expert_dtype": "fp4"`. Nemotron Ultra's `U8: 257,698,037,760` is likewise packed 4-bit. Qwen's FP8 figure by contrast reconciles to **zero bytes of delta** against per-dtype counts.
- **KV formulas that ignore hybrid attention.** Naive uniform-GQA overstated Gemma-4-31B by **11×** (128.85 → ~11.6 GB) and would overstate Qwen and Nemotron severely. Every KV figure above counts only the layers that actually keep a standard cache.
- **307 redirects.** Bare `curl` on `resolve/main/config.json` returns 307 to `cdn-lfs`; unfollowed, it looks like a failure.

### Single-sourced claims — flagged
- **Every** release date rests solely on HuggingFace `createdAt` (repo creation), with one cross-check: Ministral-3-14B-Reasoning's oldest commit is `2025-12-02T15:10:29Z "Super-squash branch main"`, consistent with the `-2512` tag, so the Oct-2025 `createdAt` is pre-release repo creation ([commits](https://huggingface.co/api/models/mistralai/Ministral-3-14B-Reasoning-2512/commits/main)). No lab blog or paper was cross-checked for any family.
- **Every** gated/param/byte fact rests on **one host** (huggingface.co). No mirror. Mitigation: params × 2 (BF16) independently reproduces the byte totals for Qwen, Gemma, GLM, Ministral, EXAONE and Cogito, making those effectively two-source.
- **Active-parameter counts are name-derived** for most MoE rungs — no config field publishes them. Where derivation was attempted: Qwen's 397B config yields ~15.3–16.2B against the "A17B" label (vendor rounding, not a refutation); Gemma-4-26B-A4B derives to 4.395B; K-EXAONE 750B derives to 37.3B and 236B to 23.7B, both confirming their names. Nemotron's `~3.5B` for a repo named **A3B** is internally inconsistent and should be treated as unverified.
- **`1,128 GB` and the `×1.1` overhead factor are assumptions**, not hardware measurements.
- **No vLLM was ever launched.** Every serving verdict is a static-artifact inference from `registry.py` plus arithmetic. Only Qwen's support was confirmed in a **cut release** (tag `v0.26.0`, published 2026-07-27, L573-576); all other families rest on `main` **HEAD as of 2026-08-10**, so merge-date-versus-release is unknown for them. Nemotron's `MIXED_PRECISION` path was checked at source level only.

### BLOCKED verifications (stated, not inferred)
1. **`baidu/ERNIE-4.5-300B-A47B-Thinking` returns HTTP 401** — config unfetchable anonymously. Baidu is therefore recorded as *unresolved*, not as a clean fail.
2. **`meta-llama/Llama-4-Scout` is `gated: "manual"`** — config unfetchable anonymously. The Meta kill rests on the absence of any reasoning repo in the org listing plus a prior in-repo study, **not** on inspecting Scout's shipped template.
3. **Every other repo across all six slate families returned HTTP 200/206 anonymously**, including ranged GETs of real weight shards. Nothing on the slate was dropped for access reasons.

### Confidence per claim class
- **Very high** (byte-level, reproduced by two independent passes to the digit): all weight totals, param counts, `max_position_embeddings`, gated status, template md5s and the verbatim `enable_thinking` lines for all six slate families.
- **High**: KV arithmetic (derived from shipped config fields, deliberately conservative), toggle-class assignments, cross-generation determinations.
- **Medium**: single-node *verdicts* — the arithmetic is sound but the node budget, overhead factor, and vLLM runtime behaviour are all unvalidated on hardware; concurrency beyond batch-1 is unmodelled, and Mamba/SSM state is omitted entirely from the Nemotron figure.
- **Low / lead-grade**: the eight killed alternates and all twenty screen-stage kills. These came from a single non-adversarial pass and are labelled *unverified* throughout. Do not cite them as settled.

### One study-design caveat the filters do not capture
**Four of six slate families are multimodal wrappers** whose serving weights include a vision tower: Qwen3.5 (all rungs carry `vision_config`), Gemma 4, Ministral-3 (Pixtral), and EXAONE-4.5-33B. The weight bytes above are therefore *not* pure-LLM parameter counts, and a "parameter-scaling" x-axis built from them mixes text and vision capacity in a ratio that is not constant across rungs. For a clean scaling curve, either derive text-only parameter counts from `text_config` per rung, or restrict the x-axis to active text parameters.
