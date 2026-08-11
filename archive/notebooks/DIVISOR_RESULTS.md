# The divisor-period study: lengthening the rule

**Status:** complete. R=30, 360/360 replicates, three MoE checkpoints x four
arms x seeds 1776–1805, 9,360 marks. Collected 2026-08-09/10.

**Headline: this is the manipulation that worked — but not on the question it
was built for.** Divisor holds the extensional listing fixed at 2,520
positions and roughly doubles the intensional rule list (26 harmonics instead
of 9). It moved gpt-oss's intensional arm off ceiling, the only one of three
studies to do so, and it collapsed gpt-oss's *extensional* arm from 0.941 to
0.588 without adding a single token of evidence. Yet intensional-vs-noise —
the contrast the whole exercise was for — is *still* not separated for any
model.

## What it was for

`periodic_moe` saturated: intensional and noise-padded-intensional both sat at
ceiling for all three models at every harmonic. The sibling `periodic_coprime`
study attacked this by lengthening the extensional listing and
[failed](COPRIME_RESULTS.md) — lengthening the listing never touches a
six-line rule list, so intensional went to a *perfect* 1.000.

Divisor attacks from the other side. Every period divides 2,520, so `lcm` is
unmoved and the listing stays exactly as long, while the rule list grows from
9 lines to 26:

    periods  1..9                    -> lcm 2,520,  9 rules
    periods  1..9, 105, 120, 126,
             140, 168, 180, 210,
             252, 280, 315, 360,
             420, 504, 630, 840,
             1260, 2520              -> lcm 2,520, 26 rules

Noise adds length without adding rules, so it cannot distinguish a
context-length limit from a rule-tracking one. More rules against unchanged
evidence can.

## Results

`acc_valid` = correct / (correct + incorrect); invalids excluded from the rate
and counted separately. All three studies on identical footing:

| model | study | Intensional | Extensional | Noise | Zero-info |
|---|---|---|---|---|---|
| **gpt-oss-120B** | baseline | 0.974 | 0.941 (17 inv) | 0.985 | 0.011 |
| | coprime | 1.000 | 0.939 | 0.994 | 0.000 |
| | **divisor** | **0.924** | **0.588** | **0.924** | 0.013 |
| **Nemotron-3-120B** | baseline | 0.996 | 0.452 | 1.000 | 0.022 |
| | coprime | 1.000 | 0.792 (2 inv) | 1.000 | 0.000 |
| | **divisor** | 0.994 | **0.655** (10 inv) | 0.999 | 0.009 |
| **Qwen3.5-397B** | baseline | 1.000 | 0.978 | 1.000 | 0.033 |
| | coprime | 1.000 | 0.976 (10 inv) | 1.000 | 0.033 |
| | **divisor** | 1.000 | 0.982 | 0.996 | 0.009 |

## Reading it

### The intensional arm came off ceiling for exactly one model

gpt-oss fell to 0.924 — 59 wrong marks out of 780, against the baseline's 20
and coprime's 0. That is the first time any manipulation has produced usable
intensional signal. Nemotron-3 (0.994) and Qwen (1.000) did not move.

So the study half-worked. Doubling the rule list is the right lever, but 26
rules is only enough to trouble the weakest of the three. Separating
Nemotron-3 or Qwen on this contrast needs a longer rule list still, and the
divisor construction has room: 2,520 has 48 divisors, of which this study uses
26.

### Intensional-vs-noise is still not separated — and the reason is subtle

| model | intens | noise | diff | verdict |
|---|---|---|---|---|
| gpt-oss | 0.9244 | 0.9244 | **+0.0000** | UNDECIDED |
| Nemotron-3 | 0.9936 | 0.9987 | −0.0051 | EQUIVALENT |
| Qwen3.5 | 0.9987 | 0.9949 | +0.0038 | EQUIVALENT |

gpt-oss's two arms score *identically* — 721/780 each. It would be easy to
read that as "whitespace padding is inert." **It is not.** Per-mark, the two
arms agree on only **676 of 780 marks (86.7%)**: 104 marks flip, almost
exactly 52 in each direction, and the flips cancel to a difference of zero.

| model | per-mark agreement, intens vs noise |
|---|---|
| gpt-oss | 676/780 (**0.867**) |
| Nemotron-3 | 774/780 (0.992) |
| Qwen3.5 | 775/780 (0.994) |

For gpt-oss, padding the prompt to ~35k tokens changes the answer on one mark
in eight. It just doesn't change *how often* the answer is right. That is a
sharper and more useful statement than the aggregate null, and it is invisible
to any analysis that only compares rates. For the other two models the padding
really is close to inert.

### The extensional collapse is the study's largest effect

gpt-oss went 0.941 -> **0.588** with the listing byte-for-byte the same length
as the baseline's. Nothing about the evidence got longer; there are simply 26
labels to track per position instead of 9. That is a clean demonstration that
extensional difficulty is driven by *label density*, not prompt length — the
confound that made coprime's Nemotron-3 recovery unreadable.

Qwen is the outlier for the opposite reason: 0.978 -> 0.982, flat. It is the
only checkpoint whose extensional performance is indifferent to a near-tripling
of the rule count, and it beats the other two by 0.34–0.39 on this arm:

| contrast | difference | p (CMH) | verdict |
|---|---|---|---|
| `[extens] gptoss vs qwen35` | −0.394 | 6.8e-90 | DECIDED |
| `[extens] nemotron3 vs qwen35` | −0.336 | 6.1e-67 | DECIDED |
| `[extens] gptoss vs nemotron3` | −0.058 | 1.3e-02 | UNDECIDED |

### The opposite-ends crossover is real, and it is gpt-oss-specific

The gpt-oss pilot suggested the two arms fail at opposite ends of the harmonic
range. With all three models in, that pattern **does not generalize** — it is a
property of gpt-oss, not of the task.

Accuracy split by period size (small = periods 1–9, whose answers are large
numbers like 1260; large = periods 105–2520, whose answers are small numbers
like 4 but which are needles in a 2,520-line listing):

| model | arm | small p<=9 | large p>=105 | gap |
|---|---|---|---|---|
| gpt-oss | intens | 0.811 | 0.984 | **+0.173** |
| gpt-oss | extens | 0.915 | 0.416 | **−0.499** |
| Nemotron-3 | intens | 0.993 | 0.994 | +0.002 |
| Nemotron-3 | extens | 0.678 | 0.629 | −0.048 |
| Qwen3.5 | intens | 0.996 | 1.000 | +0.004 |
| Qwen3.5 | extens | 0.978 | 0.984 | +0.007 |

gpt-oss shows a textbook crossover: intensionally it fails on small periods,
where the answer is a large number requiring real division (2520/2 = 1260);
extensionally it fails on large periods, where the answer is a small count of
sparse needles. Nemotron-3's extensional failure is broad and flat — it is
simply bad at the listing everywhere. Qwen has no gradient at all.

**Consequence for reporting:** the two arms do not face equally hard versions
of each harmonic. A large-period question is trivially easy intensionally
(2520/2520 = 1) and hard extensionally. Aggregate arm accuracies are averages
over a difficulty profile that differs by arm, so they should not be read as
"the same task in two representations."

### Nemotron-3 fails extensionally by trying to enumerate

Nemotron-3's extensional arm carries 80 `multiple-values` marks (10.3%) and 10
`degenerate-repetition` invalids. Those 80 score **0.062**, against 0.723 for
the rest of the arm.

They are not parser mistakes. The responses are position-by-position
transcriptions of the listing — `At 965: jx|rn. At 966: jx|de|fa|lg|bo. ...` —
that run for a median of 112,756 characters against 28,482 for clean marks,
and never reach a conclusion. Nemotron-3 attempts an O(n) brute-force scan of
2,520 positions instead of counting structurally, and runs out of room.

**A lenient regrade would be wrong here, and attractively so.** The expected
answer appears somewhere in the response text for 78 of the 80 marks (97.5%) —
which looks like the harness discarding correct answers until you notice that
an enumeration of positions 1–2520 contains *every* candidate integer by
construction. Crediting those would be scoring the model on its own scratch
work. The marks are correctly graded wrong.

This matters for the baseline comparison: Nemotron-3's apparent extensional
improvement (0.452 -> 0.655) is partly a change in failure mode, not
competence.

## Power

`scripts/posterior_power.py periodic_divisor --mei 0.05`, CMH stratified by
harmonic, Bonferroni alpha 0.05/30, bootstrap CIs over replicates.

| verdict | count |
|---|---|
| DECIDED | 19 |
| EQUIVALENT | 9 |
| UNDECIDED | 2 |

**28 of 30 contrasts are settled at R=30** — better than coprime's 25. The two
undecided:

| contrast | R for MEI |
|---|---|
| `[extens] gptoss vs nemotron3` | 80 |
| `[gptoss] intens vs noise_intens` | 50 |

Both are worth buying, and the second is the more interesting: at R=50 it
would settle whether gpt-oss's exactly-zero intens-vs-noise difference is a
true null or a coincidence of cancelling flips. Given the 86.7% per-mark
agreement, a rate-level null with substantial item-level churn is the most
likely answer — but that is a prediction, not a result.

The analysis reports no observed power by design: observed power is a monotone
function of the p-value and would restate it while sounding like new evidence.

## The five empty completions

`scripts/coprime_pilot_gate.py periodic_divisor` **blocks** on 5
`compliance=empty` marks (0.05% of 9,360), all Qwen: 3 in `zero`, 1 in
`intens`, 1 in `noise_intens`.

The gate's blocking rule is right; its inherited diagnosis ("raise
max_completion_tokens") is wrong for this study, and the fix is now in the
gate itself. The empties are **non-termination, not truncation**:

- Qwen ran with a derived **86,751-token** completion budget in a 131,072
  context.
- Three of the five sit on **110-token** prompts and one on 359 — leaving
  ~130k tokens of headroom. No budget fixes those.
- The **extensional arm, with the longest prompts (up to 36,321 tokens), has
  zero empties.** Under a budget-driven explanation it would have been hit
  first.

So Qwen occasionally fails to close its `<think>` block on *short* prompts,
most often in the zero-info arm where there is no derivable answer to reason
toward. Report it as a rate (5/9,360), not a misconfiguration.

The gate now prints the prompt-length range behind the empties and the two
competing explanations, rather than asserting a cause from hardcoded
coprime-era constants.

## Caveats

- **The arms' difficulty profiles differ by harmonic**, as above. This is the
  design working as intended, but it makes aggregate arm accuracy a weighted
  average over unlike questions.
- **Nemotron-3's extensional numbers mix two failure modes** — ordinary wrong
  answers and truncated enumerations (90 of 780 marks). Its 0.655 is not
  comparable to Qwen's 0.982 as a measure of the same capability.
- **The zero-info floor sits at 0.009–0.013**, below the baseline's
  0.011–0.033. With 26 harmonics the answer space is wider, so blind guesses
  land less often. The floor moved; the models did not get worse at guessing.
- **`vllm/vllm-openai:nightly` is a moving tag.** The baseline arms were served
  by a 2026-07-19 build, coprime by 2026-08-09, and divisor's final 18
  replicates by a 2026-08-10 build. Prompts are byte-identical and decoding is
  seeded, so this is a caveat rather than a confound.
- **Divisor's Nemotron-3 and Qwen legs were collected across two sessions** on
  separate boxes (seeds 1776–1797 and 1798–1805 / 1796–1805). Same derived
  budgets both times — 65,536 Nemotron, 86,751 Qwen — so unlike coprime's Qwen
  arm there is no budget seam.

## What the three studies establish together

| lever | what it changes | result |
|---|---|---|
| baseline `1..9` | — | intens/noise saturated, extens separates models |
| coprime `(1,3,4,5,7,11)` | listing 1.6x longer | intens went to 1.000; **more** saturated |
| divisor, 26 periods | rule list 2.9x longer, listing fixed | intens off ceiling for gpt-oss; extens collapses |

The intensional task is governed by the rule count and is indifferent to
evidence length. The extensional task is governed by label density, not prompt
length — divisor tripled extensional difficulty for gpt-oss at a fixed listing
size, while coprime's 1.6x longer listing left it unchanged.

Qwen3.5 is the only checkpoint indifferent to both levers, and it is worth
saying plainly that this benchmark no longer measures anything about it: it
scores 0.982–1.000 on every non-zero arm of every study.

The original question — whether intensional and noise-padded-intensional
differ — remains open, and now has a concrete route: more divisors. 2,520 has
48 of them and this study used 26.
