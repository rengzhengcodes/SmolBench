# Replication task: open-weight MoE family ladders for a cross-lab scaling study

Conduct a deep, multi-source, adversarially fact-checked survey and return a **slate of
open-weight model families that each ship a size ladder**, for use in a within-family
parameter-scaling study on a reasoning/induction benchmark.

**Anchor every judgment to a knowledge state of 2026-08-02.** Do not count models
released after that date. State explicitly wherever your evidence post-dates it.

## What counts as a family

A *family* is one lab's ladder of checkpoints that differ in size but share a
generation/architecture line. One family per lab — no two entries may come from the
same lab. Target a slate balanced across Chinese and American labs; grant a European
seat only if a European family genuinely clears every hard filter.

## Hard filters (a family fails if ANY counted tier fails)

1. **Mixture-of-experts.** Every *counted* tier must be MoE. Report total and active
   params per tier. Dense siblings may be mentioned but never count toward a ladder.
   A dense family may appear ONLY if you explicitly label it a control arm and mark
   this filter failed by design.
2. **Explicit reasoning mechanism.** A thinking variant, hybrid/toggleable think mode,
   or reasoning-effort control. Verify against the **shipped chat template / config**
   in the actual repo — not the model card's prose, not a blog claim.
3. **>=128,000 context on every counted tier**, as it appears in the **shipped
   `config.json`**. An officially-shipped YaRN/rope-scaling config counts. A card-only
   claim, a community RoPE patch, or a "supports up to" marketing number does NOT.
4. **Open weights, downloadable.** Note gated vs ungated status per repo (check the
   host API, not the web page).
5. **Released within ~24 months** of 2026-08 (i.e. >= ~2024-08). Give a sourced date.
6. **Single-node deployability.** The largest counted member must serve on ONE node of
   8x H200 (1,128 GB total HBM) via **upstream vLLM** at the best *official* precision
   the lab published. Fork wheels, vendor plugins, and out-of-tree backends do NOT
   count as upstream support — check the upstream architecture registry. Show the
   arithmetic: measured weight bytes at that precision + KV-cache headroom for a
   128k-token sequence, against 1,128 GB.

## Priority stack (applies after the hard filters, in this order)

1. **>= 3 rungs per family — treat as hard.** A cross-generation ladder is acceptable
   if you flag it as such.
2. **Reasoning-toggle quality**, ranked best to worst:
   same-weights on/off toggle > paired thinking/non-thinking sibling checkpoints >
   effort-level-only (no true off) > always-on thinking (no control).
3. **Same generation** across the ladder.
4. Soft tiebreakers, in rough order: ladder span (total-param spread; >=10x preferred),
   license permissiveness (Apache-2.0/MIT > custom > research-only), vLLM serving
   maturity, US origin where it helps balance.

The lab must be reputable and well-cited in the ML literature (NeurIPS/ICML/ICLR/EMNLP
and similar), but it need NOT be a top-5 frontier lab.

## Evidence standard — this is the core of the task

- Ground every architectural, context, and reasoning claim in **primary repo
  artifacts**: `config.json`, the model host's API metadata (param counts by dtype,
  storage bytes, gated status), the shipped Jinja chat template, and the upstream
  vLLM architecture registry. Model cards are a lead, not a source.
- Run an **adversarial verification pass**: for each hard-filter claim about each
  finalist, an independent checker attempts to REFUTE it. A claim may be marked
  refuted **only with a cited verbatim quote plus URL**. A claim may be marked
  surviving only if the checker actually inspected the artifact — "looks right" is
  not a verdict. If a checker is blocked (gated repo, rate limit), it must say so
  rather than infer.
- When a finalist dies, promote the next alternate and re-verify it. Iterate until the
  slate is stable.
- Flag every single-sourced claim as such. Never silently drop something you could not
  verify — label it.

## Methodology pitfalls to guard against

- Parameter counts derived from quantized safetensors metadata can be systematically
  wrong (packed low-bit formats report inflated counts). Cross-check suspicious tiers
  against byte-level tensor sizes before believing a size claim.
- Total repository storage often includes non-inference files (original/consolidated
  checkpoints, multiple precisions). Measure the serving weights, not the repo.
- A gated repo will 401 anonymous config fetches — say so instead of substituting a
  card claim.
- "Preview"/experimental cards, and toggles implemented in a Python encoder rather
  than the shipped template, are real caveats — surface them, don't smooth them over.
- Some architectures are supported only by a vendor fork. Verify against upstream.

## Sweep at least these labs, and go beyond them

Alibaba/Qwen, DeepSeek, Zhipu/Z.ai, Moonshot, MiniMax, Baidu, Tencent, ByteDance,
InclusionAI, Huawei, OpenAI, NVIDIA, Meta, Google, Microsoft, IBM, Ai2, Arcee, Deep
Cogito, xAI, Mistral, and any lab surfaced by 2025-2026 open-weight release roundups
or leaderboards. Explicitly cover releases in the first half of 2026.

## Deliverable

A cited markdown report containing:

1. **Recommended slate** — one row per family: lab, country, rungs (total/active
   params each), ladder span, context per tier, reasoning mechanism and its toggle
   class, license, gated status, best official precision, measured largest-rung weight
   bytes, and the single-node verdict with arithmetic.
2. **A compliance matrix** — hard filters and priority criteria as rows, families as
   columns, with pass / bend / fail marks. Every bend must name what was accepted and
   why.
3. **Killed candidates** — each with the *specific* filter that rejected it and the
   citation that proves it.
4. **Rest of field** — near-misses and what would have to change for each to qualify.
5. **Watch triggers** — concrete future releases that would change the slate.
6. **Method and caveats** — sources, what was unverifiable, confidence per claim.

Lead your final answer with the slate itself, then the compliance matrix.
