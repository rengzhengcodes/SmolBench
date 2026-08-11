# The `noise_intens` length control: token-matched re-collection

**Status:** complete, R=30 per arm, 270/270 replicates across three studies
(2026-08-04). Supersedes every `noise_intens` number recorded before
commit `bad377f`.

## Why it was re-collected

`noise_intens` exists to answer one objection: *"intensional prompts are
shorter than extensional ones, so an intens-vs-extens accuracy gap is just a
prompt-length effect."* It pads the intensional context until its prompt
matches the extensional prompt's length, so length is held fixed while
information content varies.

The old implementation padded with random alphanumeric filler sized in
**characters**. Random alphanumerics tokenize far worse than structured text,
so the "control" ran **1.62×** the extensional arm in tokens (periodic) and
**1.39×** (chromatic). It was longer than the thing it was controlling for,
which makes it not a length control. All 270 replicates were deleted
(`bad377f`) and the generator rebuilt to pad with **whitespace to an exact
token count under each model's own tokenizer** (`1365896`).

Consequence: **new noise numbers are not comparable to any pre-`bad377f`
noise figure.** The new prompts are ~40% shorter in tokens.

A real bug was caught before any money was spent: Nemotron-Ultra ships
`truncation: {max_length: 512}` in its `tokenizer.json`, so token counts
saturated at 512 — a 26,379-token prompt measured 512, and so did its pad, so
the search would have called them matched. Fixed by `no_truncation()` on load
plus a 2048-repetition probe that makes any saturating tokenizer fail loudly
(`70a1c21`).

## Headline result

**The control works where the models tolerate it, and destroys the model where
they don't.** Whitespace padding is not a neutral filler.

### It works: the all-MoE trio (`periodic_moe`)

| model | Intensional | Extensional | **Noise** | Zero-info |
|---|---|---|---|---|
| gpt-oss-120B | 0.974 | 0.941 (17 inv) | **0.985** | 0.011 |
| Nemotron-3-Super-120B | 0.996 | **0.452** | **1.000** | 0.022 |
| Qwen3.5-397B | 1.000 | 0.978 | **1.000** | 0.033 |

`acc_valid`; invalids excluded. Noise ≈ Intensional for all three, and TOST
equivalence sizing puts `[qwen35] intens vs noise_intens`,
`[nemotron3] intens vs noise_intens` and `[gptoss] extens vs noise_intens` at
R=1. **Nemotron-3's extensional collapse to 0.452 is therefore not a length
effect** — the same token count delivered as whitespace costs it nothing.
That inference was unavailable under the old over-long padding, and it is the
main thing this re-collection bought.

### It fails: three arms collapse into degenerate repetition

| arm | model | collapse shape | invalid |
|---|---|---|---|
| `periodic/cot` | Nemotron-Ultra-253B | **character**: `"0"` × 24,576, one distinct character, full budget | 270/270 (100%) |
| `chromatic/cot` | Olmo-3.1-32B-Think | **vocabulary**: degenerates into `‐` (U+2010) | 3608/3608 (100%) |
| `periodic/moe` | Llama-4-Maverick | **phrase**: `"## Step 1"` looped, then drifts to unrelated content | 141/270 (52%) |

These are **not** grading failures and are not fixable by a larger completion
budget or a better parser. The models stop emitting answers. Report the arms
as unusable rather than as accuracy 0.000 — a collapsed model has not
"answered incorrectly", it has not answered.

Consequence for periodic: the length control exists for **one of three
archetypes**. The intens-vs-extens gap can be defended against a length
confound for Llama-3.1-405B (`decode`, noise 0.330, 0 invalid) but not for
Nemotron-Ultra or Maverick. Chromatic is better off: 2 of 3 arms are clean.

The collapse does not track "reasoning model": Maverick is a non-reasoning MoE
and collapses; gpt-oss and Nemotron-3 are unaffected at 0.985/1.000.

## Compliance-aware grading

Output-contract violations are now recorded per mark (`Mark.compliance`,
labels in `smolbench.evals.parsing`) **separately from correctness**, so
"wrong" and "right but ignored the format" stop being the same event. A
violation is recovered where the intended answer is unambiguous, and flagged
either way.

Largest effect — Olmo-3.1-Instruct's chromatic noise arm was not failing the
task, it was answering off-contract:

```
chromatic decode_noise_intens   0.385 -> 0.574   invalid 1128 -> 1
    wrong-lexicon=706  prefixed=211  verbose=200
```

The re-grade also fixed **pre-existing silent mis-grades in already-collected
arms**, i.e. bugs that predate the noise work:

| condition | before | after |
|---|---|---|
| `periodic cot_intens` | 0.852 | **0.911** |
| `periodic cot_extens` | 0.811 | 0.819 |
| `periodic moe_intens` | 0.874 | 0.885 |
| `periodic_moe nemotron3_extens` | 0.444 | 0.452 |

`nemotron3_extens` carries 54.4% `multiple-values` violations — the compliance
signature underneath its extensional collapse.

Six `periodic/moe_noise_intens` marks moved from *incorrect* to *invalid*.
This is a correctness improvement, not a regression: all six already had
`score=0`, and the old parser had been mining a trailing number out of
collapsed text — extracting `466` against a truth of 360, and in one case
`-0.375`, which is not a possible count. Accuracy is unchanged either way.

## Power

| study | R collected | R recommended | omnibus |
|---|---|---|---|
| `chromatic` | 30 | 22 | 1.000 |
| `periodic_moe` | 30 | 14 | 1.000 |
| `periodic` | 30 | **31** | 1.000 |

Periodic is **one replicate short of its own sizing recommendation**. The
binding contrasts are `decode vs moe` (Fisher power 0.702/0.707 at R=31 versus
1.000 for every other contrast); they are near-ties (0.970 vs 0.885 on
intens). TOST: `[intens] decode vs moe` needs R=34 for a d=0.10 equivalence
margin, R=15 for d=0.15 — so at R=30 that pair supports an equivalence claim
at d=0.15 but not d=0.10.

Caveat on the highest-powered chromatic contrasts: those involving
`cot/noise_intens` (gaps 0.55–0.78) are statistically overwhelming because the
arm sits at 0.000 from total collapse. They mean "the model stopped producing
output", not "the model was less accurate". Do not report them as accuracy
differences.

## Reproducibility caveat

`periodic_moe/keys.env` pins `EC2_VLLM_IMAGE=vllm/vllm-openai:nightly`, a
moving tag. Its intens/extens/zero arms were collected 2026-07-19 on that
day's build, which is not recoverable from the tag; the noise arm was served
by a different build. Prompts are byte-identical and decoding is seeded, so
this is a caveat rather than a confound. See `periodic_moe/RUN_NOTES.md` for
the digest observed on the re-collection date.
