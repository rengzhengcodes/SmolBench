# Open-weight MoE model families for a cross-lab scaling study

**Date:** 2026-08-02 · **Method:** routed multi-agent deep research (47 agents across 2 workflow runs: 7 search sweeps → 16 primary-source extractions → slate judge → 23 adversarial verifiers), every load-bearing claim adversarially verified against primary sources (HF `config.json`, model cards, HF API blob listings, official lab blogs). See [Method & caveats](#method--caveats).

## Question

Find four families of open-weight MoE models, each from a different frontier lab, balancing Chinese and American labs (a 5th European family, e.g. Mistral, only if it genuinely qualifies). Scope decisions confirmed with the user:

1. **Every counted tier is MoE** (dense siblings noted, not counted).
2. **Explicit reasoning mode required** (hybrid think mode, reasoning-effort control, or dedicated thinking variant).
3. **Same-generation ladders preferred**; flagged cross-gen fallback allowed.
4. **Hard deploy filter:** largest counted tier serves on one p5e node (8×H200, 1128 GB HBM) via vLLM at its best *official* precision.
5. Plus: ≥128k official context on every counted tier; released within ~24 months (≥ 2024-08); ladder spanning a wide total-param range (~20B/~80B/~320B archetype).

## Recommended slate

**FINAL (user decisions, 2026-08-02): six families — five MoE (3 Chinese + 2 American) plus Llama 3.1 as a dense control arm.** After the US-exhaustive verdict (NVIDIA is the only US lab with a ≥3-rung reasoning-MoE ladder), the user accepted a 3+2 MoE slate — three 3-rung ladders (Qwen3.5, Nemotron-3, DeepSeek V3/V4) plus two 2-rung ladders (GLM-4.5, gpt-oss restored as the second US family) — and then added **Llama 3.1 (8B/70B/405B, dense)** as a sixth family: it fails the MoE and reasoning criteria by construction but supplies the canonical same-generation dense scaling ladder as a control. 16 checkpoints total, all ungated except the license-gated meta-llama repos; every load-bearing claim adversarially verified. The European slot stays empty — see [EU verdict](#eu-verdict-mistral--denied-for-now).

| Family (lab) | Counted MoE tiers (total/active) | Span | Ctx (official) | Reasoning mechanism | License | Largest-tier p5e serving |
|---|---|---|---|---|---|---|
| **Qwen3.5** (Alibaba, CN) | 35B-A3B · 122B-A10B · 397B-A17B | 11.3× | 262,144 native | thinking default-on, `enable_thinking` toggle | Apache-2.0 | BF16 807 GB or official FP8 406 GB |
| **Nemotron-3** (NVIDIA, US) | Nano-30B-A3.5B · Super-120B-A12B · Ultra-550B-A55B | 18.3× | 262,144 native | `enable_thinking` toggle (+ effort options on Super/Ultra) | Nemotron Open (Nano/Super), OpenMDW-1.1 (Ultra) | **official NVFP4 327 GB only** (BF16 1,121 GB doesn't fit) |
| **GLM-4.5** (Z.ai, CN) | Air 106B-A12B · 355B-A32B | 3.4× | 131,072 native | hybrid thinking/non-thinking, same weights | MIT | official FP8 ~358 GB (BF16 717 GB fits but little KV room) |
| **DeepSeek V3/V4 assembly** (DeepSeek, CN) | V4-Flash 284B-A13B · V3.1 671B-A37B · V4-Pro 1.6T-A49B | 5.6× | 1M · 163,840 · 1M (all shipped configs) | same-weights think/non-think toggle on every rung | MIT | V4-Pro FP4-experts+FP8, 864.7 GB measured, ~263 GB KV headroom |
| **gpt-oss** (OpenAI, US) | 20b (20.9B-A3.6B) · 120b (116.8B-A5.1B) | 5.6× | 131,072 (official YaRN) | reasoning-effort low/medium/high + native CoT | Apache-2.0 | MXFP4 65 GB |
| **Llama 3.1 — dense control** (Meta, US) | 8B · 70B · 405B (all dense) | 50.6× | 131,072 (Meta launch docs; config gated) | **none** | Llama 3.1 Community (gated: manual) | official FP8 487 GB measured |

### How the final six square against the restrictions

| Restriction | Qwen3.5 | GLM-4.5 | DeepSeek V3/V4 | Nemotron-3 | gpt-oss | Llama 3.1 (control) |
|---|---|---|---|---|---|---|
| Open weights, ungated on HF | ✓ Apache-2.0 | ✓ MIT | ✓ MIT | ✓ Nemotron-Open (Nano/Super), OpenMDW-1.1 (Ultra) | ✓ Apache-2.0 | **△ gated "manual"**, Llama 3.1 Community license (access already in place in our harness) |
| Every rung MoE (config-verified experts) | ✓ 256/256/512 | ✓ 128+1/160+1 | ✓ 256+1/256+1/384+1 | ✓ 128+1/512+1/512+1 | ✓ 32/128 | **✗ dense ×3 — by design (control arm)** |
| ≥3 rungs | ✓ 3 (11.3×) | **△ 2 (3.4×) — accepted** | ✓ 3 (5.6×) | ✓ 3 (18.3×) | **△ 2 (5.6×) — accepted** | ✓ 3 (50.6×) |
| ≥128k shipped-config ctx per rung | ✓ 262,144 ×3 | ✓ 131,072 ×2 | ✓ 1M / 163,840 / 1M | ✓ 262,144 ×3 | ✓ 131,072 ×2 (official YaRN) | ✓ 131,072 ×3 (**△ config behind gate — per Meta docs + our own harness runs**) |
| Reasoning; thinking-toggle preferred | ✓ same-weights toggle (default-on) | ✓ same-weights toggle | ✓ same-weights toggle all rungs (**△ V4's off-switch lives in the Python encoder, not the shipped template**) | ✓ same-weights toggle + effort options | **△ effort-only (low/med/high, no true off)** | **✗ none — no thinking variant in the org (API-verified)** |
| Same generation | ✓ one wave (Feb 2026) | ✓ one wave (Jul 2025) | **△ adjacent gens** (V3.1 Aug 2025 + V4 Apr 2026) | ✓ one wave (Dec 2025–Jun 2026) | ✓ one wave (Aug 2025) | ✓ one wave (2024-07-23) |
| Released ≥ 2024-08 | ✓ | ✓ | ✓ | ✓ | ✓ | **△ 2024-07-23, 9 days outside — waived** |
| Largest rung on 1×p5e via upstream vLLM, official precision | ✓ FP8 406 GB (**△ nightly pin, vllm#36236**) | ✓ FP8 ~358 GB | ✓ 864.7 GB, ~263 GB free (**△ SM90 FP4 fallback; LoRA blocked on V4; "preview" cards**) | ✓ (**△ Ultra via NVFP4 327 GB only — BF16 1,121 GB doesn't fit**) | ✓ MXFP4 65 GB | ✓ official FP8 487 GB (BF16 ~811 GB also fits); most mature vLLM arch, LoRA ✅ |
| Distinct, reputable lab | ✓ Alibaba | ✓ Z.ai | ✓ DeepSeek | ✓ NVIDIA | ✓ OpenAI | ✓ Meta |
| Country | CN | CN | CN | US | US | US |

Llama 3.1's role is explicitly the **dense control**: the canonical same-recipe dense ladder (widest span in the slate at 50.6×) against which the MoE families' scaling curves can be contrasted. Its ✗ cells are definitional, not oversights. Bonus continuity: `llama-31-405b` is already validated in this harness (deduction archetype trio; Lean LoRA fine-tune), and `LlamaForCausalLM` is the one slate architecture with first-class vLLM LoRA support. Verification notes: dense/params/gating/license/FP8-size/no-thinking-variant were API-verified 2026-08-02 (405B-Instruct-FP8 safetensors: 324.5B params F8 + 81.3B BF16 ≈ 487 GB); the 131,072-ctx config values could not be anonymously fetched (HTTP 401, gated) and rest on Meta's launch documentation plus our own prior serving runs.

*(This seat changed twice. Round 2 — original criteria — retained gpt-oss (20b/120b, Apache-2.0, MXFP4 65 GB): no lab beat its ladder same-generation. Round 3 — revised criteria: ≥3 rungs hard, thinking-toggle then same-generation as priorities, reputable-lab bar — selects the DeepSeek cross-generation assembly; gpt-oss, now failing the 3-rung floor, becomes the documented fallback. Slate balance shifts to 3 CN + 1 US, accepted by the user's fallback instruction. See Addenda 1–2.)*

Notes on the composition:

- **Nemotron-3 and Qwen3.5 are the two ladders that match the ~20B/~80B/~320B archetype** (30/120/550 and 36/125/403 by real safetensors counts) — both 3-tier, same-generation, >10× span. GLM-4.5 (2 tiers, 3.4×) and gpt-oss (2 tiers, 5.6×) are the weakest ladders but the only qualifying second families per country; both are otherwise impeccable (permissive licenses, ungated, trivial/comfortable deploys).
- The slate contains **all three models already validated in the periodic_moe trio study** (`gpt-oss-120b`, `Nemotron-3-Super-120B-A12B`, `Qwen3.5-397B-A17B`) as interior/anchor tiers — existing results and serving configs carry over.
- Cross-checked: one lab per family; every counted tier is config-verified MoE with ≥128k official context and a reasoning mechanism in the shipped chat template/config; earliest counted release 2025-07-20 (GLM-4.5), well inside the 24-month window.

---

## Verified families (all three lenses SURVIVES unless noted)

### 1. Qwen3.5 — Alibaba (China) · 3 same-generation MoE tiers · 11.3× span

The cleanest ladder found. One release wave (2026-02-16 / 2026-02-24), one architecture (`model_type: qwen3_5_moe`, hybrid Gated DeltaNet + Gated Attention), unified thinking models (no Instruct/Thinking split).

| Tier | Total (safetensors) | Active | Experts | Native ctx | BF16 | Official FP8 | Released |
|---|---|---|---|---|---|---|---|
| Qwen3.5-35B-A3B | 35.95B | ~3B | 256, top-8 + 1 shared | 262,144 | ~72 GB | 37.5 GB | 2026-02-24 |
| Qwen3.5-122B-A10B | 125.1B | ~10B | 256, top-8 + 1 shared | 262,144 | ~250 GB | 127.2 GB | 2026-02-24 |
| Qwen3.5-397B-A17B | 403.4B | ~17B | 512, top-10 + 1 shared | 262,144 | 806.8 GB | 406.2 GB | 2026-02-16 |

- **Reasoning:** thinking mode default-on (`<think>…</think>`, token ids 248068/248069), disabled via `chat_template_kwargs: {"enable_thinking": false}` — verified in all three shipped `tokenizer_config.json` templates, not just marketing copy.
- **Context:** `max_position_embeddings: 262144` in all three configs, `rope_scaling` null/absent (native, not a YaRN hack; YaRN only extends toward ~1M).
- **License/gating:** Apache-2.0, `gated: false` on all three tiers and their `-FP8` siblings (HF API).
- **p5e fit (largest tier):** BF16 403.4B × 2 B = 806.8 GB = 66.6% of node, ~377 GiB free; KV is tiny (~3.75 GiB per 128k sequence — hybrid attention). Official FP8 = 406.2 GB, trivial fit. *Verifier arithmetic from HF blob sums, not card claims.*
- **Deploy caveat:** cards require vLLM main/nightly; vLLM issue #36236 reports a transformers-5.x config-rename break — pin a known-good nightly. (Matches our harness experience: the trio study ran 397B on a nightly image, FP8.)
- **Dense siblings** (0.8B–27B) exist and are not counted. No uncounted MoE sibling found in the org listing.

### 2. GLM-4.5 (+ GLM-4.6 top-tier swap) — Z.ai / Zhipu (China) · 2 same-generation MoE tiers · 3.35× span

Strongest reasoning-mechanism evidence after Qwen3.5; weakest ladder in the slate (2 tiers, smallest span).

| Tier | Total (safetensors) | Active | Experts | Native ctx | BF16 | Official FP8 | Released |
|---|---|---|---|---|---|---|---|
| GLM-4.5-Air | 110.5B (docs: 106B) | ~12B | 128 routed + 1 shared, top-8 | 131,072 | 220.9 GB | yes (ungated) | 2025-07-20 (HF), announced 07-28 |
| GLM-4.5 | 358.3B (docs: 355B) | ~32B | 160 routed + 1 shared, top-8 | 131,072 | 716.7 GB | ~358 GB | 2025-07-20 (HF) |

- **Reasoning:** hybrid thinking / non-thinking modes in the *same weights*, on both tiers — model-card verbatim, plus identical toggle in both shipped chat templates; serving-time toggle documented for vLLM/SGLang.
- **Context:** `max_position_embeddings: 131072`, `rope_scaling: null` in both configs (verifier fetched raw configs).
- **License/gating:** MIT, ungated (both tiers and both official FP8 repos).
- **p5e fit:** BF16 716.7 GB fits (411 GB free) but KV is heavy (~49.4 GB per 128k sequence; 92 layers, 8 KV heads, head_dim 128) → **use the official FP8 repo (~358 GB)** for real 128k batching headroom.
- **Cross-gen option:** GLM-4.6 (356.8B, `max_position_embeddings: 202752`, MIT ungated, 2025-09-30) is an architecturally-identical top-tier swap if recency matters more than same-generation purity.
- Verifier corrections folded in above: the shortlist's "~358 GB BF16" figure was a params/GB unit error (BF16 is ~717 GB; ~358–361 GB is FP8); "expert counts undisclosed" was false (configs disclose them).

### 3. gpt-oss — OpenAI (USA) · 2 same-generation MoE tiers · 5.6× span

| Tier | Total | Active | Experts | Ctx | Official MXFP4 | Released |
|---|---|---|---|---|---|---|
| gpt-oss-20b | 20.9B | 3.6B | 32, top-4 | 131,072 (official YaRN) | ~13.7 GB | 2025-08-05 |
| gpt-oss-120b | 116.8B | 5.1B | 128, top-4 | 131,072 (official YaRN) | ~65 GB (60.8 GiB) | 2025-08-05 |

- **Reasoning:** configurable reasoning effort (low/medium/high) + native CoT — the only slate family with *effort-level* control rather than a binary think toggle.
- **License/gating:** Apache-2.0, ungated (verified via HF API).
- **p5e fit:** trivial — the card itself notes MXFP4 fits the 120b on a single 80 GB GPU.
- **Verification status:** 3/3 SURVIVES. Arch lens in run 1 (config expert counts, params, ladder verified against the OpenAI-authored arXiv model card; openai.com returned 403 to the verifier); capability + availability lenses recovered in the rescue pass — YaRN confirmed as OpenAI's own config (not a community hack), reasoning-effort confirmed on both tiers, license confirmed unmodified Apache-2.0 from the repo LICENSE file, 120b weights measured at 65.25 GB by summing the 15 official MXFP4 shards, worst-case 128k KV ≈ 9 GiB/seq (~4.5 GiB with the sliding-window layers).
- `gpt-oss-safeguard-*` are fine-tunes, not size tiers (correctly excluded). Only 2 tiers; no larger MoE released since 2025-08.

### 4. Nemotron-3 — NVIDIA (USA) · 3 same-generation MoE tiers · 18.3× span

Recovered in the rescue pass (its run-1 extraction was the one agent failure) and verified 3/3. The headline: **Nemotron-3-Ultra-550B-A55B shipped weights on 2026-06-04**, turning the family into the widest qualifying ladder. All tiers are LatentMoE hybrids (Mamba-2 + MoE + attention, MTP; `model_type: nemotron_h`).

| Tier | Total | Active | Experts | Native ctx | Official precisions | Released | License |
|---|---|---|---|---|---|---|---|
| Nemotron-3-Nano-30B-A3B | 30B | 3.5B | 128 routed + 1 shared, top-6 | 262,144 | FP8, BF16 (~30 GB FP8) | 2025-12-15 | NVIDIA Nemotron Open Model License |
| Nemotron-3-Super-120B-A12B | 120B | 12B | 512 routed + 1 shared, top-22 | 262,144 | FP8 (ModelOpt), BF16, F32 (~120 GB FP8) | 2026-03-11 | NVIDIA Nemotron Open Model License |
| Nemotron-3-Ultra-550B-A55B | 550B (560.5B safetensors) | 55B | 512 routed + 1 shared, top-22 | 262,144 | BF16, **NVFP4** (326.6 GB measured) | 2026-06-04 | **OpenMDW-1.1** |

- **Reasoning:** `enable_thinking` chat-template toggle (on by default, `<think>` traces) — verified in all three shipped Jinja templates; Super adds a low-effort and Ultra a medium-effort reduced-token option. *Not* always-on as run-1 search claimed.
- **Context:** `max_position_embeddings: 262144` in every tier's config (cards advertise "up to 1M" via serving-time extension — treat 256k as the official native figure).
- **p5e fit (Ultra):** BF16 is 560.5B × 2 B = **1,121 GB vs 1,128 GB HBM — does not fit** (the card itself recommends 8×B200 for BF16). The qualifying precision is the **official NVIDIA NVFP4 repo** (4-bit routed experts + FP8 attention/shared-expert): 326.6 GB measured from the file tree, ~800 GB free for KV, vLLM-supported on Hopper. A third-party claim of an official FP8 Ultra was refuted (HTTP 401; only BF16/NVFP4/Base/GenRM exist).
- All repos ungated (verified via anonymous raw-file fetches + HF API). Release dates: run-1's "all 2025-12-15" was wrong — Super is 2026-03-11.

---

## EU verdict: Mistral — denied, for now

Mistral is the only European lab anywhere near qualification, and it is *close* — but the capability lens **refuted** the family on hard evidence:

- **Mistral Large 3 675B-A41B** (2025-12-02, Apache-2.0, ungated, official FP8 681.5 GB — fits p5e with 446 GB to spare, MLA KV only ~9.2 GB/128k seq) **has no reasoning mode**. Its own card: *"Not a dedicated reasoning model."* The launch post promised a reasoning version "coming soon"; a full `mistralai` org listing on 2026-08-02 shows **no** Large-3 Reasoning/Thinking/Magistral-Large repo has shipped.
- **Mistral Small 4 119B-A6.5B** (2026-03-16, native FP8 ~121 GB, config ctx 1,048,576) *does* have a genuine same-weights `reasoning_effort` toggle (it unified the former Magistral line).
- The bind is structural: count Large 3 → the largest counted tier fails the explicit-reasoning criterion; drop it → the ladder collapses to one MoE tier and fails the ≥2-tier rule. (Also: `same_generation` was overstated — Large 3 and Small 4 are differently-numbered generations ~3.5 months apart with different config shapes.) No third MoE tier exists in the org (Medium-3.5-128B and Devstral-2-123B are dense; Leanstral-1.5-119B-A6B is a Small-4-shaped derivative, not a new size).

**Watch trigger:** the day a Mistral-Large-3-class reasoning checkpoint ships open-weight, Mistral immediately qualifies (2 MoE tiers, 5.7× span, Apache-2.0, both fit one p5e at official FP8) and the slate can grow to 5.

---

## Killed finalists (adversarially refuted)

### Llama 4 — Meta (USA) · killed on the reasoning criterion

Scout (109B-A17B) and Maverick (400B-A17B) are genuine same-generation MoE, but **no reasoning mechanism exists anywhere in the family**: neither model card mentions any thinking/reasoning mode; the meta-llama org listing contains no thinking/reasoning variant (only Scout/Maverick base+Instruct+FP8 and Llama-Guard-4); press reports Meta *delayed* the reasoning version of Llama 4. Behemoth never shipped. Secondary caveat: the repos are gated, so the verifier could not fetch raw `config.json` (10M/1M context figures rest on cards/blog only).

### Granite 4.0-H — IBM (USA) · killed on the same criterion

H-Tiny (7B-A1B) and H-Small (32B-A9B) are real MoE (72-expert/top-10 and 64-expert/top-6 configs) with official 131,072 context, Apache-2.0 ungated — but **instruct-only**: no `<think>` handling in either shipped `chat_template.jinja`, no thinking repo among all 73 `ibm-granite` granite-4* repos, Granite 4.1 (Apr 2026) went *dense and explicitly non-reasoning*, and an IBM staffer confirms reasoning Granite models are still "in the works". (`granite-switch-4.1` is LoRA-adapter routing, not CoT reasoning.) Also sub-hard weaknesses: 4.6× span at small scale, borderline frontier-lab status.

---

## Rest of the field (alternates, in the judge's order)

| Family (lab) | Countable MoE tiers | Why not in the slate |
|---|---|---|
| **Ling/Ring 2.0** (InclusionAI/Ant, CN) | Ring-mini-2.0 16.8B-A1.4 + Ring-flash-2.0 100B-A6.1 (dedicated thinking branch of Ling) | Top CN alternate. MIT ungated, 128K (official YaRN over 32K native), 6× span. Ring-1T uncountable: BF16 ~2 TB, official FP8 ~1 TB leaves no KV headroom on 1128 GB. Frontier-lab status borderline. |
| **MiniMax M-series** (CN) | M1 456B-A45.9 (thinking budgets, 1M ctx) + M2 229.9B-A9.8 (interleaved `<think>`, 192k) | Cross-generation (2025-06 vs 2026-05, 32 vs 256 experts), only 2× span, M1 BF16 ~912 GB is tight on one node. |
| **ERNIE 4.5** (Baidu, CN) | 21B-A3B(-Thinking) + 300B-A47B | 14× span, Apache-2.0, 131,072 ctx, ~600 GB BF16 fits — but **no Thinking variant exists for 300B-A47B** (confirmed against Baidu's GitHub/HF), so the top tier fails the reasoning criterion. |
| **Hunyuan** (Tencent, CN) | A13B 80B-A13 (enable_thinking, 256K) + Large A52B 389B-A52 | A52B has no reasoning mode and is prior-generation (2024-11); custom license. |
| **Kimi K2** (Moonshot, CN) | K2-Thinking 1043B-A32 only | No ladder — every K2 is 1T/32B. Otherwise excellent: native INT4 QAT ~594 GB fits one node, 256K ctx, interleaved CoT+tools. |
| **DeepSeek V3.x/R1** (CN) | all 671B-A37 | No ladder: six releases, one size; distills are dense. R1 is a real reasoning mode and 685 GB BF16 fits, but there is nothing to scale across. |
| **Qwen3 / Qwen3-Next** (Alibaba, CN) | 30B-A3B, 235B-A22B, Next-80B-A3B-Thinking | Blocked by one-family-per-lab (Qwen3.5 wins); also cross-gen (128 vs 512 experts) and core tiers are 32K native ctx (131K only via YaRN). |

**2026-generation single-tier releases** (from the untargeted sweep; single-sourced from mixed-quality secondary pages, *not* verified — watch-list only): DeepSeek-V4 (Flash 284B-A13 + Pro 1.6T, 2026-04; Pro would fail the node filter), GLM-5.2 (~753B-A40, adjustable reasoning effort, 2026-06), Kimi K2.6 (1T, thinking/instant modes, 2026-04), MiniMax-M3 (428B-A23, 2026-06). None showed a same-generation multi-tier MoE ladder at search time.

**Non-qualifying US/other:** Ai2 OLMo 3 (dense, incl. Think variants; a sparse OLMo-MoE is planned, not released), Microsoft Phi (only open reasoner is dense Phi-4-reasoning-vision-15B, 16K ctx), xAI Grok (Grok-1 MoE is 2024/8K-ctx; Grok-2.5 has no reasoning toggle and no ladder), TII Falcon-H1/H1R (dense hybrid Mamba), Apertus/Aleph Alpha/OpenEuroLLM (no qualifying MoE).

---

## Fit to the SmolBench harness

- Three of the four families anchor on models already validated in the periodic_moe trio study (`openai/gpt-oss-120b`, `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B`, `Qwen/Qwen3.5-397B-A17B`) — existing R=28/R=30 results and known-good vLLM configs carry over, and each trio model becomes an interior tier of its family's ladder.
- Every counted tier fits one p5e (8×H200, 1128 GB) at an official precision with 128k KV headroom. Recommended serving repos for the flagships: Qwen3.5-397B-A17B-FP8 (406 GB; matches our previous nightly-image FP8 run), GLM-4.5-FP8 (~358 GB — BF16 fits but leaves only ~330 GB for ~49 GB/seq KV), Nemotron-3-Ultra NVFP4 (327 GB — BF16 does *not* fit), gpt-oss MXFP4 (65 GB).
- A full-slate scaling sweep is 10 checkpoints: Qwen3.5 ×3, Nemotron-3 ×3, GLM-4.5 ×2, gpt-oss ×2 — all ungated, no HF token gymnastics.
- Known deploy quirks: Qwen3.5 needs a pinned vLLM nightly (transformers-5.x config-rename break, vllm#36236); Nemotron `nemotron_h` and Ultra-NVFP4 are vLLM-supported on Hopper per NVIDIA's own recipes but were not live-tested in this research.

## Addendum (2026-08-02, same day): gpt-oss replacement search — verdict: KEEP gpt-oss

Follow-up question: replace gpt-oss (the slate's narrowest ladder: 2 counted tiers, 5.6× span) with a better *same-generation* open MoE ladder — family names may differ within a generation — preferring a US lab (Meta/Google/other), falling back to a Chinese lab. All other hard criteria retained; slate-seated labs (NVIDIA, Alibaba, Z.ai) excluded. Run as a second routed workflow (21 agents: 5 sonnet sweeps → 6 haiku extractions → opus judge → 9 opus refuter lenses over three finalists) plus one opus forensic check.

**Verdict: no lab, US or Chinese, beats gpt-oss's ladder under the hard criteria.** Every challenger that passed the criteria tied or trailed the 5.6× span, and every wider ladder failed a hard criterion. The judge's summary stands verbatim: *"No ladder gained, confidence lost."*

Per-lab US verdict (all checked definitively this pass):

- **Google** — first time searched: the Gemma 4 wave (Apr 2026) contains exactly **one** MoE (26B-A4B; DiffusionGemma reuses the same backbone). No second tier, no ladder.
- **Meta** — nothing shipped past Llama 4 Scout/Maverick (still no reasoning variant); "Llama 5" claims are blogspam.
- **xAI** — the Feb 2026 Grok-3 open-sourcing pledge remains unmet.
- **Microsoft** — MAI-Thinking-1 (MoE reasoner) is API-only; the only open MAI weight is MAI-DS-R1 (DeepSeek arch).
- **Ai2 / Databricks** — sparse OLMo-MoE and DBRX-2 unshipped.
- **Thinking Machines Lab — Inkling** (new find): Inkling 975B-A41 + Inkling-Small 276B-A12 is a genuine same-gen US MoE pair passing *every* hard criterion — Apache-2.0 ungated, official 1M ctx, reasoning-effort map verified in the shipped chat template, official NVFP4 (~592 GB) fits one p5e with vLLM. Refuted only on the ladder test: 2 tiers at **3.5× span**, narrower than gpt-oss. **This is the standing US alternative if span is ever de-prioritized.**
- **Arcee — Trinity**: Trinity-Mini 26B-A3 + Trinity-Large-Thinking 398B-A13 is the **widest span found anywhere (15.3×)** but verifiably *not* same-generation (Arcee documents sequential waves, Large's lessons "flow back down" to future Mini/Nano) — and Arcee is not an established frontier lab.

Chinese fallback outcome:

- **DeepSeek V4 is real** (round 1's watch-list caveat resolved from the deepseek-ai org): Flash 284B-A13B + Pro 1.6T-A49B, same generation, MIT, ungated, official 1M ctx (YaRN ×16 in shipped configs), three-level reasoning-effort on both, Pro's shipped FP8/I8 weights measured at 864.8 GB — fits one p5e with ~263 GB headroom. But it is **2 tiers at ~5.3–5.6× span** (HF-measured 1.599T / 304B incl. Flash's speculative-decode module; card basis 1.6T/284B) — a tie/narrower, not a better ladder. A tantalizing "158B Flash" third rung turned out to be an **HF FP4 packed-parameter counting artifact**: forensic check reconstructed Flash-0731's 304B total exactly from the preview repo's packed record (ratio exactly 2.0000×, byte-identical expert tensors via safetensors header range-reads). V4 = exactly two rungs. *If 1M context ever matters more than ladder width, V4 is the lateral swap — same span, adds 1M ctx, at the cost of slate balance (3 CN + 1 US).*
- **Ant/InclusionAI Ring 2.0**: the core wave collapses to 1 qualifying tier (Ring-flash-2.0 ships 32.7k-ctx config; Ring-1T-FP8 is 65,536-ctx and ~1,003 GB — fails context *and* fit). The linear pair (16.4B + 104B, 6.3× span) passes per-tier criteria but its `BailingMoeLinearV2ForCausalLM` architecture is **absent from upstream vLLM** (official card mandates a third-party fork wheel; SGLang is the supported path) — refuted on deployability for our harness.
- **StepFun** (Step3 65.5k ctx, cross-gen), **Meituan LongCat** (Flash-Lite explicitly non-thinking, cross-gen, 1 counted tier): both fail.
- Not searched this pass (budget): Reka, ByteDance Seed, RedNote dots, OpenBMB, Baidu ERNIE-5, Cohere Command-A MoE status — none showed ladder signals in the sweeps.

**Conditions that would flip the verdict:** (1) relaxing same-generation → Arcee Trinity (US, 15.3×) wins immediately, with the frontier-lab caveat; (2) prioritizing 1M context over ladder width → DeepSeek V4 as a lateral swap; (3) de-prioritizing span → Inkling restores a heavyweight US pair. Watch triggers: a Gemma-4.x MoE sibling, Grok-3 weights, sparse OLMo-MoE, DBRX-2, a third DeepSeek V4 size, upstream vLLM support for Ring's linear architecture.

## Addendum 2 (2026-08-02): three-rung revision — DeepSeek V3/V4 assembly takes the gpt-oss seat

Revised criteria from the user: **≥3 MoE rungs is a hard requirement** (cross-generation rungs within one lab now allowed); then rank by **thinking-toggle quality** (same-weights on/off toggle > paired thinking sibling > effort-only > always-on), then **same-generation**, with the frontier-lab bar relaxed to "reputable, well-cited at major ML venues." gpt-oss (2 rungs) fails the new floor by construction. Run as a third routed workflow (14 agents) plus three targeted verifiers.

**Winner — DeepSeek V3/V4 lineage, verified 3/3 lenses:**

| Rung | Total/Active | Experts | Shipped ctx | Official precision (measured) | Released | Toggle |
|---|---|---|---|---|---|---|
| DeepSeek-V4-Flash | 284B/13B | 256 routed + 1 shared, top-6 | 1,048,576 (YaRN ×16 in config) | FP4-experts+FP8, ~167 GB | 2026-04-22 | Non-think / Think-High / Think-Max (`thinking_mode`) |
| DeepSeek-V3.1 | 671B/37B | 256 routed + 1 shared, top-8 | 163,840 (YaRN in config) | native FP8 e4m3, ~671 GB | 2025-08-21 | `thinking=True/False` **in the shipped Jinja template** |
| DeepSeek-V4-Pro | 1.6T/49B | 384 routed + 1 shared, top-6 | 1,048,576 (YaRN ×16 in config) | FP4-experts+FP8, 864.7 GB measured | 2026-04-22 | Non-think / Think-High / Think-Max |

- The only ladder found with a **same-weights runtime toggle on every rung** — the top of the user's #1 ranking criterion. All rungs MIT, ungated, in-window; `DeepseekV3ForCausalLM` and `DeepseekV4ForCausalLM` both in upstream vLLM (registry + in-tree `models/deepseek_v4/`); largest rung fits p5e with ~263 GB free (MLA KV ≈ 4.6 GB per 128k seq FP8; tp=8 shards cleanly: 128 heads, 384 experts, 61 layers).
- **Same-generation status: adjacent generations, one lineage** (V3.1 Aug 2025 + the V4 Flash/Pro wave Apr 2026) — the compromise the revised priority order explicitly permits (criterion 2 < criterion 1).
- **Serving caveats for the harness:** (1) V4's non-think switch lives in `encoding_dsv4.py`, *not* a shipped chat template — `vllm serve` needs a custom `--chat-template` to reach non-think (V3.1's toggle is template-native). (2) On H200, FP4 experts run vLLM's SM90 Marlin/Triton fallback (upstream, weights stay 4-bit; the fast DeepGEMM path is Blackwell-only). (3) vLLM's LoRA column is blank for `DeepseekV4ForCausalLM` — a LoRA leg on the V4 rungs is currently blocked. (4) V4-Pro at 864.7 GB serves 128k easily but not its 1M ctx on one node. (5) V4 cards self-describe as "preview" releases. (6) Verifier corrections: V4-Pro config arithmetic gives ~1.48T (card says 1.6T); V3.2's toggle equivalence was not verified (V3.1 chosen as the mid rung for its template-verified toggle; V3.2 is a possible swap pending that check).

**Ranked field (all adversarially checked):**

- **MiniMax M1/M2/M3** — refuted as assembled: M3 is natively multimodal (`minimax_m3_vl`, vision tower → excluded by the text-eval VL rule) and M1 was **removed from upstream vLLM** after v0.23. The repairable text-only ladder (M2 + M2.1 + …) degenerates to two same-size 230B rungs, and its toggle classes (always-on/effort-only) sit at the bottom of criterion 1.
- **Huawei openPangu** (surfaced by a post-hoc HF-org sweep; 4 MoE tiers 74B/100B/541B/718B with fast/slow-think toggles) — killed on deploy: the entire openPangu-2.0 generation is unservable (`OpenPanguV2ForCausalLM` absent from upstream vLLM **and** no `modeling_*.py` shipped), the 718B BF16 is 1.47 TB with only an Ascend-toolchain Int8 alternative, and the license bans EU use. At most 2 qualifying rungs (R-72B solid; Ultra conditional).
- **Arcee Trinity (US)** — fails at 2/3 rungs. A dedicated re-adjudication (fetching the shipped chat templates directly) *corrected* the round-3 kill: Trinity-Mini 26B-A3B **does** reason (always-on `<think>`, auto-opened in the shipped template), and with Trinity-Large 398B-A13B (Preview/Thinking pair) that's two qualifying rungs — `afmoe` is even in upstream vLLM natively. But Trinity-Nano-Preview 6B has verifiably zero reasoning (no think tokens in tokenizer, none in template) and all Trinity-Large repos are one size rung → 2 counted, not 3.
- HF-org sweep nulls (checked via API, no web search): Reka (dense), Cohere (one MoE size; Command A gated-config, dense-tagged), OpenBMB (dense), XVERSE (MoE sizes but no reasoning), Skywork (pre-window), ByteDance-Seed (dense), Tencent (single-size generations, no thinking tags), StepFun (Step-3.5/3.7-Flash are same-size version bumps), LLM360/Nous/EleutherAI (none), FreedomIntelligence Apollo-MoE (3 tiers, no reasoning).

### Definitive US verdict (follow-up pass, 2026-08-02)

Direct user question: "Is there no US lab that accomplishes this otherwise?" — settled by a dedicated 5-agent pass (Trinity re-adjudication from shipped artifacts, first-ever Deep Cogito check, frontier org re-checks, US org sweep incl. Databricks/Snowflake/Liquid/Zyphra/Together/Apple/Amazon/Perplexity). **Answer: No. NVIDIA is the only US lab with a qualifying ≥3-rung MoE reasoning ladder (Nemotron-3, already seated); every other US lab caps at 2 rungs or fails a hard criterion:**

| US lab | Verdict |
|---|---|
| Arcee (Trinity) | **Closest: 2/3** — Mini 26B (always-on think) + Large 398B count; Nano-Preview 6B has zero reasoning (template/tokenizer-verified) |
| Deep Cogito | 2/3 — 109B-A17B + 671B-A37B both have genuine same-weights `enable_thinking` toggles, but both are **derivative** (Llama-4-Scout / DeepSeek-V3 bases → arch-heterogeneous); 671B fits p5e only via official FP8 |
| OpenAI | 2 rungs (gpt-oss); no third size |
| Thinking Machines | 2 rungs (Inkling); no third size |
| Meta / IBM | MoE ladders with zero reasoning mechanism (Llama 4; Granite through 4.1) |
| Google | Exactly one open MoE ever (Gemma-4 26B-A4B) — re-confirmed |
| Microsoft | MoE reasoner is API-only |
| xAI | Grok-3 open-weight pledge unmet (grok-2 config unverified, but ≤2 rungs regardless) |
| Ai2 | Only tiny academic OLMo-MoE ablations; flagship sparse OLMo unshipped |
| Databricks / Snowflake | DBRX-2 unshipped / Arctic outside the window |
| Liquid AI | Only LFM2.5-8B-A1B qualifies (24B card says "without reasoning traces"; 8B is 32k-ctx) = 1 rung |
| Zyphra | ZAYA1 sizes exist but `zaya` is absent from upstream vLLM — disqualified on serving |
| Cohere | Canadian; one MoE size anyway |

Most likely flip events, in order: Arcee ships any reasoning-capable third Trinity size (instant arch-homogeneous 3-rung US ladder); OpenAI or Thinking Machines ship a third size; Cogito adds a third MoE rung (still derivative). Residual open items: the Arcee org listing data was ~4 months stale at check time; grok-2's config and Meta's 80+ non-Llama facebook repos were not individually config-checked.

**Coverage caveat (honest limits):** round 3's web-search quota exhausted mid-run (all four search legs degraded to WebFetch-only; the refutation sweep never executed as designed). The gap was closed with an HF-API org sweep (13 orgs) plus targeted opus verifications of the two candidates it surfaced — but labs outside those orgs and any non-HF-hosted ladders remain unswept this round. Unresolved unknowns: a third Inkling size, Gemma 4.x MoE siblings, V3.2's toggle, Cohere Command-A's config (gated 401).

## Method & caveats

- **Pipeline:** custom routed workflow (`moe-family-deep-research`, run `wf_fc405781-73a`; rescue `wf_66e7cea5-b69`): 7 sonnet search sweeps (per-lab clusters + untargeted 2025–26 sweep + deployment angle) → merge/dedupe (26 families) → 14 haiku primary-source extractions → 1 opus slate judge → 3 opus adversarial refuter lenses per finalist (architecture/ladder, capability, availability/deploy), kill-and-replace up to 2 rounds. Verifiers were instructed to *refute* and to cite the exact config line / API output for every confirmation.
- **Incidents (all recovered in the rescue run):** (1) the one haiku extraction that died without structured output was exactly Nemotron-3 — recovered with sonnet extraction + full 3-lens opus verification (all SURVIVES, and the extraction surfaced the shipped Ultra tier); (2) the extraction cap (top-14 by MoE-row count) dropped the thinly-documented "Mistral Large 3 / Small 4" candidate — run 1's "EU denied for absence of evidence" was an artifact; the rescue re-adjudication *confirms* the denial, but on primary-source evidence (Large 3 has no reasoning mode); (3) two of twelve run-1 verify agents (gpt-oss capability + availability) exhausted structured-output retries on field-length caps — re-run with explicit length discipline, both SURVIVES; (4) a workflow-args templating bug made the release-window placeholder read "undefined" in run-1 prompts — the slate judge independently anchored the identical window (≥ ~2024-08-02) and flagged it, so no conclusion changed; hardcoded in the rescue run.
- **Trust levels:** every claim in the family sections above is verifier-confirmed against primary sources unless explicitly marked otherwise; the "2026-generation single-tier" watch-list is unverified secondary sourcing; active-param counts are from official cards (not recomputed from tensor shapes); no live serving test was run as part of this research.
