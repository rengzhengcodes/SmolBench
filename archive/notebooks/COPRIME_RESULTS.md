# The coprime-period study: lengthening the evidence

**Status:** complete. R=30, 360/360 replicates, three MoE checkpoints x four
arms x seeds 1776–1805. Collected 2026-08-09.

**Headline: it did not work, and the way it failed is informative.** The study
set out to de-saturate the intensional-vs-noise contrast by making the
extensional listing 1.6x longer. Intensional accuracy went to a *perfect*
1.000 for all three models — more saturated than the baseline it was meant to
fix. The contrast it did sharpen is a different one: extensional.

## What it was for

`periodic_moe` saturated. Intensional and noise-padded-intensional sat at
ceiling for all three models at *every* harmonic, so no harmonic separated
them (paired McNemar p=0.549 for gpt-oss, 1.000 for the other two). The
obvious remedy — more harmonics — is unavailable, because on the default
pathway sequence length is `lcm(1..n)`, a step function:

    lcm(1..9)  =  2,520     extensional listing ~26k tokens
    lcm(1..10) =  2,520     IDENTICAL; n=10 lengthens nothing
    lcm(1..11) = 27,720     x11; ~341k tokens vs a 131,072 context window

There is no n in between. So this study dials length directly with a
pairwise-coprime period set, where `lcm == prod`: `(1, 3, 4, 5, 7, 11)` ->
4,620 positions, a ~1.6x longer listing, 6 harmonics.

## Results

`acc_valid` = correct / (correct + incorrect); invalids excluded from the rate
and reported separately.

| model | Intensional | Extensional | Noise | Zero-info |
|---|---|---|---|---|
| gpt-oss-120B | **1.000** (180/180) | 0.939 (169/180) | 0.994 (179/180) | 0.000 |
| Nemotron-3-120B | **1.000** (180/180) | **0.792** (141/180, 2 inv) | 1.000 (180/180) | 0.000 (3 inv) |
| Qwen3.5-397B | **1.000** (180/180) | 0.976 (166/180, **10 inv**) | 1.000 (180/180) | 0.033 |

Baseline (`periodic_moe`, periods 1..9, 2,520 positions, 9 harmonics):

| model | Intensional | Extensional | Noise | Zero-info |
|---|---|---|---|---|
| gpt-oss-120B | 0.974 | 0.941 (17 inv) | 0.985 | 0.011 |
| Nemotron-3-120B | 0.996 | **0.452** | 1.000 | 0.022 |
| Qwen3.5-397B | 1.000 | 0.978 | 1.000 (3 inv) | 0.033 |

## Reading it

### The intensional arm got *more* saturated, not less

All three models are now perfect on intensional, where the baseline at least
left gpt-oss 7 errors to work with. In hindsight this should have been
predicted: the intensional prompt is a six-line rule list plus one division
(`4620 / k`). Lengthening the *listing* does not touch it — the two arms share
a question but not a task.

Consequence: the intens-vs-noise contrast this study was built to separate is
now **less** answerable here than in the baseline. That question belongs to
the sibling `periodic_divisor` study, which lengthens the rule list instead.

The equivalence verdicts reflect this rather than refuting it. Every
intens-vs-noise contrast comes back EQUIVALENT with a zero-width interval —
but that is equivalence *at ceiling*, which is a weaker claim than equivalence
mid-range. It says the two arms are indistinguishable at this benchmark's
resolution, not that no difference exists.

### The extensional arm is where the signal moved

| contrast | difference | p (CMH) | verdict |
|---|---|---|---|
| `[extens] gptoss vs nemotron3` | +0.156 | 2.8e-05 | DECIDED |
| `[extens] nemotron3 vs qwen35` | −0.139 | 2.5e-04 | DECIDED |
| `[nemotron3] intens vs extens` | +0.217 | 6.5e-11 | DECIDED |
| `[qwen35] intens vs extens` | +0.078 | 3.1e-04 | DECIDED |
| `[nemotron3] extens vs noise` | −0.217 | 6.5e-11 | DECIDED |

Nemotron-3 remains the outlier on extensional evidence, and the intens-vs-extens
gap is decisively non-zero for two of three models. Same questions, same
answers, different representation — the models are not indifferent to how the
evidence is presented.

### Nemotron-3's collapse partly recovered — and this is confounded

Nemotron-3's extensional accuracy went 0.452 -> 0.792. That is a large move
and it is tempting to read it as "longer listings are easier for Nemotron",
which would be backwards. **Do not read it that way.**

Pairwise coprimality forbids keeping both 2 and 4, or 3 and 9, so this period
set fires ~2.02 labels per position against the baseline's ~2.83. The listing
is longer *and sparser*. Sparser compounds are plausibly easier to scan, so
length and density moved together and this design cannot separate them. The
recovery is real; its cause is not established.

### Qwen's 10 invalids are a finding, not a defect

All 10 sit in the extensional arm and are `compliance=empty`: empty response
*and* empty reasoning, meaning the `<think>` block never closed and the parser
had nothing to return. That is truncation.

Qwen's completion budget here is a derived 63,851 tokens, which is *below* the
65,536 that already truncated it during the pilot. The reason is arithmetic,
not configuration: its worst prompt in this study is 59,221 tokens, and
59,221 + template + 63,851 is already near the 131,072 ceiling. **At ~59k-token
prompts Qwen3.5 cannot reliably both reason and answer inside its context
window.** No budget on this checkpoint fixes it; a shorter period set would.

## Power

`scripts/posterior_power.py periodic_coprime --mei 0.05`, CMH stratified by
harmonic, Bonferroni alpha 0.05/30, bootstrap CIs over replicates.

| verdict | count |
|---|---|
| DECIDED | 15 |
| EQUIVALENT | 10 |
| UNDECIDED | 5 |

**25 of 30 contrasts are settled at R=30.** The five undecided ones, with the
replicates needed to detect a 0.05 effect:

| contrast | R for MEI |
|---|---|
| `[gptoss] intens vs extens` | 50 |
| `[extens] gptoss vs qwen35` | 200 |
| `[gptoss] extens vs noise_intens` | 200 |
| `[zero] gptoss vs qwen35` | >400 |
| `[zero] nemotron3 vs qwen35` | >400 |

Only the first is worth buying: R=50 would settle whether gpt-oss's 0.061
intens-vs-extens gap is real. The two `zero` contrasts compare 0.033 against
0.000 at the chance floor and are not worth any replicates. Note the analysis
reports no observed power by design — observed power is a monotone function of
the p-value and would restate it while sounding like new evidence.

## Caveats

- **Budget seam in Qwen's arm.** Replicates collected before a mid-study host
  restart used a 65,536 completion budget; the rest used the derived 63,851.
  Qwen's extensional invalid rate is therefore approximate. Re-collect that arm
  uniformly if the truncation rate matters to a claim.
- **The zero-info floor is harder here.** gpt-oss and Nemotron-3 score exactly
  0.000 against the baseline's 0.011/0.022. With 6 harmonics over 4,620
  positions the answers are larger numbers, so a blind guess lands less often.
  The floor moved; the models did not get worse at guessing.
- **Length and density are confounded**, as above. Any comparison against the
  baseline listing changes both.
- **`vllm/vllm-openai:nightly` is a moving tag.** The baseline arms were served
  by a 2026-07-19 build and these by a 2026-08-09 one. Prompts are
  byte-identical and decoding is seeded, so this is a caveat rather than a
  confound.

## What this leaves

The intensional-vs-noise question is now squarely the sibling study's:
`periodic_divisor` holds the listing fixed at 2,520 positions and roughly
doubles the rule list (26 harmonics, all dividing 2,520). Noise adds length
without adding rules, so it cannot distinguish a context-length limit from a
rule-tracking one; more rules against unchanged evidence can.

Early divisor signal already looks sharper than anything here: on gpt-oss the
two arms fail at *opposite ends* of the harmonic range — extensional only at
large periods (needles in 2,520 lines), intensional only at small ones
(large-number division).
