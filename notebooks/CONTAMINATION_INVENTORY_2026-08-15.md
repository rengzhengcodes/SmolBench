# Hardware-contamination inventory and rerun record — family-ladder study

**2026-08-15.** Which of the 21 lanes had their cells generated on more than one
serving configuration, what was done about each, and — for the first time in this
study — a *measurement* rather than an argument about whether that matters.

## Why this exists

The 2026-08-13 confound audit cleared the `g6e.4xlarge` → `g6e.2xlarge`/`g6e.8xlarge`
substitution on the tp=1 lanes with the reasoning that both sizes carry exactly one
L40S 48GB and run the same tp under the same image, so the difference could affect
throughput but not sampling. That is a claim about a mechanism, and it is wrong.

## The measurement

`scripts/hardware_equivalence_probe.py` runs the lane's own real deduction prompts at
the study's own temperature/seed/max_tokens. Its load-bearing design choice is the
**same-box baseline**: two back-to-back passes on ONE box, before any cross-hardware
comparison. vLLM is not guaranteed bitwise-reproducible even on one machine — with
continuous batching, what else is in flight changes reduction order — so without a
noise floor a naive cross-size diff would blame hardware for vLLM's own jitter.

| model | same-box baseline | 4xlarge vs 2xlarge | reading |
|---|---|---|---|
| `nemotron-3-nano-4b` | **8/8 identical** | **0/8 identical** | hardware IS a variable |
| `ministral-3-3b` | 0/8 identical | 0/8 identical | neutral within noise |

`nemotron-3-nano-4b` is bitwise-reproducible at a fixed seed on one box, so 0/8 across
sizes cannot be jitter. Outputs diverged from the **first token**, with an identical
`1x L40S 48GB` and `tp=1` served on both sides (verified in the probe logs). Host
vCPU/RAM change batching and therefore floating-point reduction order.

`ministral-3-3b` is not reproducible even on one box. For that lane the substitution is
real but **undetectable, and unverifiable by rerunning** — a rerun would produce
different outputs by construction, so it cannot demonstrate a fix.

Reports: `notebooks/deduction/results/hwprobe_archive/<model>_4xl-vs-2xl.json`.

## Method for the inventory

Lanes were classified from what **actually landed**, not from the deploy spec: every
`launched i-… (<type> @ <az>` and `reattached to i-…` line across
`notebooks/induction/results/fleet_logs/*.log`, plus the deduction `server_config.yaml`
sidecars and this run's repair logs. That distinction is not academic — see
`deepseek-v3.1` below, where spec and reality disagreed and nobody had checked.

"Cured by re-run" claims were **verified against S3 timestamps**, not taken on trust.

## Inventory

### Contaminated, unresolved → rerunning

| lane | configs that generated its cells | status |
|---|---|---|
| `nemotron-3-nano-4b` | induction `g6e.4xlarge` + `g6e.8xlarge`; deduction `g6e.4xlarge` (59 cells) + `g6e.2xlarge` (885 cells) | **deduction leg re-running in full on ONE `g6e.4xlarge`** via `--force-rerun`. Prior rows preserved at `all_rows_SUPERSEDED-mixed-4xl-2xl-2026-08-15.jsonl` (67,197,216 bytes, sha256 `df17ff29aff89e6e`, byte-verified). Induction leg still mixed — see open items. |

### Contaminated, not worth rerunning

| lane | configs | why not |
|---|---|---|
| `ministral-3-3b` | induction `g6e.4xlarge` + `g6e.12xlarge`; deduction `g6e.2xlarge` + `g6e.4xlarge` | Baseline 0/8 — the model is not reproducible on a single box at a fixed seed, so contamination here is undetectable *and* a rerun could never be shown to have fixed it. Spending on it buys nothing measurable. Documented instead. |

### Cleared — verified, not assumed

| lane | apparent issue | verification |
|---|---|---|
| `gemma-4-12b` | 4 instance types across its history | all 30 seeds' newest arm files postdate the `g7.12xlarge` re-run cutoff → single-config |
| `ministral-3-14b` | `g6e.12xlarge` + `g7.24xlarge` | all 23 landed seeds postdate the `g7.24xlarge` re-collection → single-config (lane ships at R=23; see the induction note) |
| `deepseek-v4-flash` | p5 + p5e + p6-b200 | seeds 0–11 all re-collected on B200 with full 4-arm coverage; seeds 12–29 were B200 originally, so their older timestamps are expected, not stale |
| `deepseek-v4-pro` | p5en + p6-b200 | zero rows predate the final B200 recipe — the p5en boxes wrote nothing |

### Single-configuration lanes (no action)

`exaone-4.0-32b`, `exaone-4.5-33b`, `gemma-4-31b`, `gemma-4-e2b`, `glm-4.5-air`,
`glm-4.7`, `glm-4.7-flash`, `k-exaone-236b-a23b`, `ministral-3-8b`,
`nemotron-3-nano-30b-a3b`, `nemotron-3-super-120b-a12b`, `qwen3.5-27b`,
`qwen3.5-122b-a10b`, `qwen3.5-397b-a17b`, `deepseek-v3.1`.

Several of these ran on **several boxes of the same type** (e.g. `exaone-4.5-33b` ×3,
`glm-4.7-flash` ×4, `qwen3.5-27b` ×3). Whether two boxes of the same type agree is a
question the size probe does **not** answer, because its cross-size arm changed the
machine and the size together. A box-to-box probe at fixed size is running; note in
advance that a disagreement there would not prove "box identity matters" — a different
box also means a fresh vLLM process, a cold prefix cache, and possibly a different
unpinned nightly image digest. If it disagrees, the honest conclusion is that **no
rerun can restore bit-identity to any lane**, and the output is documentation rather
than compute.

### A separate defect this inventory surfaced

`deepseek-v3.1`'s 944 original cells were all generated on **`p5en.48xlarge`**
(i-0f25d11e3090d452e, us-east-2a). `scripts/relaunch_damaged_deduction.sh` asked for
**`p5e.48xlarge`**. For ~15 hours the repair hunted an instance type this lane has
never run on, reported no capacity everywhere, escalated to on-demand, and gave up —
leaving 415 of 944 cells untouched for the wrong reason. Had a `p5e` landed it would
have *created* the confound this document is about, and `EC2_REQUIRE_GPU=H200:8` would
not have caught it, because p5e and p5en both expose 8× H200.

**Pinning silicon is necessary and not sufficient. The serving config is more than the
accelerator.**

## Open items

- `nemotron-3-nano-4b` **induction** leg is still mixed (`g6e.4xlarge` + `g6e.8xlarge`)
  across its 30 seeds. The deduction rerun does not address it; a full 30-seed
  re-collection on one instance type would.
- `ministral-3-3b` remains mixed on both legs, by decision.
- Unpinned `vllm/vllm-openai:nightly` digest drift within multi-day lanes remains a
  residual from the 2026-08-13 audit and is orthogonal to instance type.

## The generalisable lesson

Both silent faults this study has produced were cleared by an argument about a
mechanism instead of a measurement of the outcome — the completeness gates counted rows
instead of asserting content, and the hardware substitution was defended as "same
silicon, same tp, so it cannot affect sampling." When a substitution is justified on the
grounds that it *cannot* matter, the cheap move is to run the thing twice and diff it,
with a same-box baseline so the comparison has a noise floor to be judged against.
