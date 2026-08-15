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

| comparison (`nemotron-3-nano-4b`) | byte-identical | what it isolates |
|---|---|---|
| same box, same process, back to back (A1 vs A2) | **8/8** | the noise floor: this model IS deterministic at a fixed seed |
| `g6e.4xlarge` vs `g6e.2xlarge` (different size **and** different box) | **0/8** | size *and* box, confounded |
| `g6e.4xlarge` vs `g6e.4xlarge` (**same size**, different box) | **0/8** | box/process alone |

`ministral-3-3b` scored 0/8 on its OWN same-box baseline, so it is not deterministic even
within one process and nothing can be measured for it.

**The third row corrects the second, and corrects what I first concluded.** I initially
reported the 4xl-vs-2xl result as "instance SIZE changes generations." It does not show
that: the 2xlarge was also a *different machine running a different vLLM process*. When
the size is held fixed and only the box changes, agreement is still 0/8, with common
prefixes of 0–149 characters — outputs diverge almost immediately. **Size was never
shown to matter. What matters is that it is a different serving process at all.**

So the honest statement is narrower than "hardware is a variable" and broader in its
consequences: **vLLM output here is reproducible within one server process and not
across processes**, at identical instance type, GPU, tp, and (as far as could be
checked) image build — two boxes brought up 12 minutes apart either side of the pull
both reported `vllm 0.27.2rc1.dev110+gacb0f1dcd`, so an unpinned-nightly digest change
does not explain it, though the probe's own two boxes were not directly fingerprinted.

Reports: `notebooks/deduction/results/hwprobe_archive/` — `<model>_4xl-vs-2xl.json` and
`nemotron-3-nano-4b_4xl-vs-4xl-BOX2BOX.json`. (In the box-to-box file the field named
`cross_size` is cross-*box* at fixed size; the script's key names assume the size
comparison.)

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
| `nemotron-3-nano-4b` | induction `g6e.4xlarge` + `g6e.8xlarge`; deduction WAS `g6e.4xlarge` (59 cells) + `g6e.2xlarge` (885 cells) | **DEDUCTION LEG DECONTAMINATED 2026-08-15 22:37Z.** Full 944-cell re-run on ONE box via `--force-rerun`. Induction leg still mixed — see open items. |

Verification of that re-run, all four checks rather than the driver's own completion message:

| check | result |
|---|---|
| `audit_run_completeness.py --lane nemotron-3-nano-4b` | 944 cells, **0 infra, 0 genuine**, exit 0 |
| `server_config.yaml` | **1 capture, 1 box** — `i-05428528f2aef631f`, `g6e.4xlarge`, 1× L40S 48GB, tp=1 |
| pass@1 | 944 cells, `replicate_idx` ∈ {0}, **exactly 1 surviving attempt per cell**, 0 cells with more |
| superseded data | `all_rows_SUPERSEDED-mixed-4xl-2xl-2026-08-15.jsonl` intact in S3, 67,197,216 bytes |

This is the only lane in the study whose deduction cells all come from a single serving
process, and therefore the only one that is internally bit-reproducible. Box terminated on
completion.

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

### What the box-to-box result means for the other lanes

Every lane that used more than one box has cells from more than one serving process, and
therefore cannot be bit-reproducible internally. That is **most of the study**:
`gemma-4-12b` ×21 boxes, `ministral-3-14b` ×48, `glm-4.7-flash` ×4, `exaone-4.5-33b` ×3,
`qwen3.5-27b` ×3, `gemma-4-e2b` ×3, and every lane whose sweep was resumed after a spot
reclaim. Single-box lanes are the exception, not the rule.

**This is a property of the design, not a repairable defect, and it is noise rather than
bias.** Every lane already runs on its own hardware by construction — the study compares
models *across* lanes — so per-process nondeterminism does not correlate with the model
axis. Re-running twenty lanes single-box would cost weeks of compute to remove a term
that does not bias the comparison.

What it does mean:

1. **No rerun can restore a lane to its original outputs.** A rerun can only make a lane
   internally homogeneous going forward. That is why the `nemotron-3-nano-4b` rerun is
   still correct — one box, one process, one image is the only way any lane achieves it —
   and why nothing is gained by rerunning the rest.
2. **`deepseek-v3.1`'s remaining 415 cells will differ from its other 529 no matter what**,
   because they must come from a new box. Region choice adds nothing to a split that
   already exists.
3. Analysis must not assume bitwise reproducibility across a lane's cells, and the
   write-up should state this as a known noise term with its measured size (0/8 agreement
   across processes, 8/8 within one).

### Single-configuration lanes (no action)

`exaone-4.0-32b`, `exaone-4.5-33b`, `gemma-4-31b`, `gemma-4-e2b`, `glm-4.5-air`,
`glm-4.7`, `glm-4.7-flash`, `k-exaone-236b-a23b`, `ministral-3-8b`,
`nemotron-3-nano-30b-a3b`, `nemotron-3-super-120b-a12b`, `qwen3.5-27b`,
`qwen3.5-122b-a10b`, `qwen3.5-397b-a17b`, `deepseek-v3.1`.

Several of these ran on **several boxes of the same type** (e.g. `exaone-4.5-33b` ×3,
`glm-4.7-flash` ×4, `qwen3.5-27b` ×3, and — after re-runs — `gemma-4-12b` ×21 and
`ministral-3-14b` ×48). **The box-to-box probe has now reported, and it changes the
reading of everything above.**

### Authorised within-lane split: `deepseek-v3.1` p5en → p5e (2026-08-15)

After p5en.48xlarge proved unavailable in **all 9 offering AZs across 4 regions, spot AND
on-demand, for a full day** and two exhausted 40-attempt supervisors, the user authorised
generating the lane's missing 415 cells on **p5e.48xlarge** — also 8× H200 at tp=8.

Resulting lane, if p5en never frees up:

| segment | cells | hardware |
|---|---|---|
| original | 529 | `p5en.48xlarge`, i-0f25d11e3090d452e, us-east-2a |
| repair | 415 | `p5e.48xlarge`, us-east-2 a/b/c or us-west-2c |

The hunt is **type-major and ordered p5en first**, so every p5en AZ is exhausted before a
single p5e is requested: if capacity returns the lane completes on its original hardware with
no split at all. `EC2_REQUIRE_GPU=H200:8` passes for both types, which is precisely why it
cannot be relied on to catch this — hence this entry.

Two things make the split less costly than it would have been this morning. The box-to-box
result means those 415 cells could never have matched the original 529 anyway, since they must
come from a new serving process regardless of type; and the analysis loader now excludes
unmeasured cells rather than scoring them 0, so the alternative (shipping at 529/944) would
have been unbiased too. The choice was between fewer paired cells and a nameable type split;
the user took the split.

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

## Resampling bias — 67 cells, and the analysis rule that removes it

Separate from hardware, and self-inflicted. Between 2026-08-14 and 2026-08-15 the resume
rule re-ran any contentless cell that owned an `exception` row. A cell that lost its FIRST
attempt to a spot kill keeps that row forever, so it was re-run on every relaunch even
after later attempts had run cleanly and answered emptily. Since generation is not
deterministic across server processes (see above), each retry is an independent draw — so
retrying an empty answer until a proof appears **manufactures successes**.

**67 cells went empty → proof this way**, 0.4% of all cells carrying a proof:

| lane | resampled cells | share of that lane's cells with proofs |
|---|---|---|
| `ministral-3-3b` | 56 | 6.6% |
| `qwen3.5-27b` | 6 | 0.6% |
| `gemma-4-31b` | 5 | 0.5% |

The rule is fixed going forward (`aab747e4`): a cell is re-run only when no attempt both
reached the model and survived, evidenced by `prompt_tokens > 0` on a non-`exception` row.

**For the already-collected data, the analysis must take the FIRST surviving
(non-`exception`) row per cell, not the last and not "any row with content."** That is the
unbiased estimator, and it is correct universally — where an infra failure forced a legitimate
re-run, the first *surviving* row is still the first real measurement. Taking any-row-with-content
inflates `ministral-3-3b` by up to 56 cells and would flatter it against its own family.

Cells are identified as: a clean (non-`exception`) empty row that is followed, later in
`all_rows.jsonl`, by a row carrying content. File order is append order, so "later" is
chronological.

## pass@1 verification (all 21 deduction lanes)

Checked three ways, because the configured value and the collected data can disagree:

1. **Configured** — every lane: `n_replicates: 1`. No lane was ever run with multiple rollouts.
2. **Recorded** — every lane: `replicate_idx` ∈ {0} only, 944 cells each, 19,824 total.
3. **Actual attempts per cell** — 18 of 21 lanes have exactly ONE surviving (non-`exception`)
   row per cell. Three do not, as fallout from the resampling bug above: **74 cells hold more
   than one surviving attempt** (`ministral-3-3b` 63, `qwen3.5-27b` 6, `gemma-4-31b` 5).

For those three lanes the metric is pass@1 only under the first-surviving-row rule. Taking
any-row-with-content instead:

| lane | any attempt | first surviving | difference |
|---|---|---|---|
| `ministral-3-3b` | 850 / 944 = 90.0% | **794 / 944 = 84.1%** | **+5.9 pt** |
| `qwen3.5-27b` | 929 / 944 = 98.4% | **923 / 944 = 97.8%** | +0.6 pt |
| `gemma-4-31b` | 943 / 944 = 99.9% | **938 / 944 = 99.4%** | +0.5 pt |

One `ministral-3-3b` cell's surviving attempts have proof lengths `[0, 0, 0, 65]` — three empty
answers and then a proof on the fourth draw. Reported as-is that is **pass@4 presented as
pass@1**, and it moves that lane's headline by nearly six points against its own family.

These are proof CANDIDATES, not verified successes; the verification pass has not yet run, so
nothing downstream has consumed the inflated figures. The `nemotron-3-nano-4b` rerun generates
each cell exactly once on one box and will be textbook pass@1.

(The induction leg is not a pass@1 metric: R=30 replicates per model by design, R=23 for
`ministral-3-14b`.)

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
