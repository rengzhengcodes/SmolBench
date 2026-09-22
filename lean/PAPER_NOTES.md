# Paper corrections for the deductive benchmark (2026-07-01 draft)

Findings from the 2026-09 review of `lean/` against the paper, and the
changes made. Section numbers refer to the draft. Numbers below come from
`results/runs/main_v3` and `main_v3_2` unless marked rescored.

## 1. Level labels in Figures 5–7 do not match Table 1

Table 1's medians (None 331, MPI 366, MPI+Sig 489, One-Hop 762, Two-Hop
1387) are the rungs `stepk:2, hint:0, hint:1, hint:2, hint:3`. Figures 5–7
were generated with `hint:3` labeled "One-Hop" and `hint:4` labeled
"Two-Hop". So the figures show the 1-hop closure under the One-Hop label and
a 2-hop closure (median 3,592 tokens, not defined in the paper) under the
Two-Hop label, and never show the level the paper defines as One-Hop.

Fix: the figure scripts now use the Table 1 mapping (`figures/_util.py`
`LEVELS`). The per-level claims in §5.2 (which model peaks where, the
degradation at "Two-Hop") must be re-derived from the regenerated figures.
See §8 below for what changed.

## 2. Scoring split every newline into a separate tactic (§4.2)

§4.2 says each line is submitted as a separate LeanDojo call. A single Lean
tactic often spans lines (indented `have` continuations, `induction … with`
arms, `calc` chains). Fragments fail. In `main_v3_2`, candidates with an
indented continuation line scored 230 `lean_error` vs 9 `success` (96%),
against 19% for single-line candidates. The share of such candidates rises
from 9.9% at MPI to 12.8% at the deepest level, so the artifact leaned
toward the paper's conclusion.

Fix: `verify._split_tactics` now attaches indented and `|`-prefixed lines
to the preceding tactic (279 of the benchmark's own traced tactics are
multi-line and replay this way). Existing runs were re-scored offline from
their stored responses (`leaneval rescore`).

Text for §4.2: "we split the block into tactics, treating indented
continuation lines and match arms as part of the preceding tactic, and
submit each tactic as a separate LeanDojo call."

## 3. Verdict taxonomy (§4.2 "Processing outputs")

Three problems in the recorded verdicts:

- Responses that hit the 32,768-token cap were scored `lean_error`. 35 rows
  in the paper runs; 28 had an empty answer after 27k–99k characters of
  reasoning. They cluster in sonnet-4.6-thinking and kimi-k2.6-high at the
  None level, so they depressed the None baseline for reasoning models.
- A tactic that runs past the Dojo timeout raised an exception and was
  recorded as infrastructure failure (201 rows), then dropped from
  denominators and re-run on every resume. It is a model failure.
- 439 cells died on an API read timeout with no retry and were recorded as
  `exception`, then counted as failures in the figures' denominators.

Fix: verdicts `truncated` and `timeout` (both failures), `exception`
excluded from every denominator as missing data, `finish_reason` persisted,
transport errors retried. Re-scoring relabels existing rows; the 301 Dojo
crash rows were re-verified.

Text for §4.2: "We classify each result as success, lean_error,
incomplete, timeout (a tactic exceeded the 300 s verifier timeout), or
truncated (the response reached the output-token cap without a verified
proof). Infrastructure failures are excluded and re-run."

## 4. Theorem pool (§3.4 "Theorem selection")

The draft says 659 theorems remain after requiring at least one traced
tactic. The replay-passing pool with at least one traced tactic has 782
theorems. 659 is the count after the sweep config's `max_tactics: 5`
filter, which the draft does not mention. The 100 evaluated theorems are
sampled (seed 0) from the 659, so the described procedure and the actual
one pick largely different sets.

Text for §3.4: "We restrict to theorems whose proofs have one to five
traced tactics and replay successfully, leaving 659 theorems, and sample
100 with seed 0. Results therefore cover short proofs scored on their
final step."

Also: the frontier subset is 30 sampled theorems (21 with non-trivial
cells, 15 in the analysis set), not 20 as §4.2 states.

## 5. Neutral-information control (§3.2, §4.1 Ablation, §4.2 Ablation)

The draft describes appending neutral text to the MPI prompt until the
character length matches. The implementation (and Figure 6) uses a
different and better design: `noise:N` is the `hint:(N-1)` prompt padded
with lorem ipsum to the cl100k token count of `hint:N`, so `hint:N −
noise:N` is the marginal effect of step N's content at matched length.
Describe that.

Two defects in the matching itself:

- The filler section header ("## Filler (… no informational content)") was
  not counted in the budget, so every noise prompt was 24 tokens over its
  target, and the header text told the model the block was filler.
- Provider tokenizers count lorem ipsum 7–12% higher than cl100k does
  (v3.2-none, provider-reported prompt tokens: MPI+Sig 490 vs 538, One-Hop
  762 vs 816, Two-Hop 1387 vs 1529). Character length is 34–40% higher.

Extra length hurts the noise arm, so `hint − noise` is inflated. Fix: the
filler is now fitted so the whole prompt matches exactly, and the header
carries no commentary (`configs/main_v4_noise.yaml` re-runs the noise
rungs). The provider-token gap cannot be closed without provider
tokenizers; report the measured ratio alongside Figure 6.

Text for §3.2/§4.2: "For each level N above MPI we build a neutral control
by padding the level N−1 prompt with lorem ipsum to the token count of the
level N prompt. Comparing level N with its control isolates the marginal
effect of the content added at N."

## 6. Analysis set and uncertainty (§5)

Trivial-rung skipping is per rung, not per theorem as §3.4 says, so raw
per-level denominators differ (main_v3: None 94, MPI 63, MPI+Sig 61,
One-Hop 61, Two-Hop 59). The figures now use one analysis set per model:
(theorem, k) pairs with scored rows at every paper level and noise level
for that model. Each legend entry shows n.

No figure reported uncertainty. At n≈55 theorems with 3 rollouts, a
between-level pass-rate difference has a 95% interval of roughly ±10 pp.
All figures now carry 95% paired bootstrap intervals over theorems.

## 7. "Full derivations" (§3.4 "Levels of positive information")

One-Hop and Two-Hop are described as full derivations of premises. The
original implementation extracted every identifier from a premise's whole
declaration (docstring, attributes, binder types, proof) and followed those
that named a globally unique corpus premise. For `map_div`, five of seven
extracted names came from typeclass binders and the `@[to_additive]`
attribute.

Fix (2026-09-08): derivation edges now come from the LeanDojo trace when
the premise's own proof was traced, i.e. the premises its tactics used, the
same data the MPI is built from. That is exact for named usage and blind
only to what `simp`/`omega`/typeclass search find internally. Premises
without a trace (definitions, instances, term-mode proofs) fall back to
name matching resolved with the file's `namespace`/`open` context.

Measured on the 100 sampled theorems: 59 of 145 MPI premises have a trace.
Closure sizes change little (1-hop mean 6.0 → 6.4, 2-hop 23.2 → 26.3), so
the old text matcher was already finding most named references. The change
is definitional: One-Hop now is "the premises used in the proof of each MPI
premise" for traced premises.

Two facts to state in the paper:

- 34 of the 100 sampled theorems have an empty MPI: their final tactic
  names no lemma (`simp`, `rfl`, `omega`, `exact h`). They cannot enter the
  hint chain and are dropped from every hint level. The analysis set is
  therefore theorems whose final step cites at least one premise.
- Two-Hop expands mostly through untraced premises (of 423 one-hop
  premises, 337 have no trace), so the second hop is still mostly a
  reference closure.

Text for §3.4: "One-Hop adds, for every MPI premise, the premises used in
its own proof as recorded by LeanDojo (or referenced in its declaration,
for definitions and term-mode proofs); Two-Hop applies the same expansion
once more."

## 8. What the numbers look like after the fixes

From `results/runs/main_v3_rescored` and `main_v3_2_rescored` (re-scored
2026-09-08; the Two-Hop and noise rows still use the pre-fix prompts until
`main_v4_rerun` exists). Analysis set per model; 95% paired bootstrap over
theorems. Re-scoring changed 420 + 109 lean_error rows to success, 28 + 6
success rows to lean_error, relabeled 201 timeouts and 29 truncations, and
left 11 frontier rows as missing after a stuck Lean process was killed.

**Δ pass rate vs MPI (pp)**

| model | n | MPI+Sig | One-Hop | Two-Hop |
|---|---|---|---|---|
| kimi-k2.6-high | 48 | −1.9 [−12.8, +8.8] | −2.2 [−13.8, +10.0] | −2.8 [−14.4, +9.3] |
| kimi-k2.6-none | 57 | +5.3 [−5.9, +16.4] | +8.5 [−3.2, +20.8] | +10.0 [−2.1, +22.6] |
| v3.2-high | 56 | +16.1 [+6.6, +25.3] | +13.7 [+3.8, +23.8] | +18.1 [+8.6, +28.1] |
| v3.2-none | 57 | +20.9 [+9.9, +32.2] | +22.6 [+11.7, +34.0] | +19.4 [+8.3, +30.6] |
| gemini-flash-high | 57 | +18.1 [+8.8, +27.5] | +18.7 [+9.4, +28.7] | +13.5 [+3.5, +24.0] |
| gemini-flash-none | 57 | +6.4 [−4.1, +18.1] | +9.9 [−1.2, +21.6] | +9.4 [−1.2, +20.5] |
| gpt-5.5-high | 15 | −8.3 [−21.6, +7.3] | 0.0 [−11.6, +13.3] | 0.0 [−22.7, +22.2] |
| gpt-5.5-none | 15 | +8.3 [−7.7, +24.4] | +15.6 [−4.4, +35.6] | +8.9 [−8.9, +26.7] |
| sonnet-4.6-none | 15 | +20.0 [+4.4, +40.0] | +17.8 [0.0, +37.8] | +8.9 [−13.3, +33.3] |
| sonnet-4.6-thinking | 15 | +2.2 [−6.7, +11.1] | 0.0 [−8.9, +8.9] | 0.0 [−8.9, +8.9] |

**hint:N − noise:N (pp), marginal content vs matched-length filler**

| model | n | MPI+Sig | One-Hop | Two-Hop |
|---|---|---|---|---|
| kimi-k2.6-high | 48 | −0.1 [−11.3, +10.3] | −0.3 [−8.6, +9.2] | −4.5 [−10.4, +1.2] |
| kimi-k2.6-none | 57 | +3.2 [−7.0, +12.6] | +2.3 [−5.8, +10.5] | −0.2 [−7.0, +6.8] |
| v3.2-high | 56 | +10.8 [+0.9, +21.4] | +0.5 [−6.1, +8.3] | −2.2 [−9.7, +5.6] |
| v3.2-none | 57 | +19.9 [+9.4, +31.6] | +5.3 [−1.8, +12.9] | +0.3 [−7.0, +7.6] |
| gemini-flash-high | 57 | +17.0 [+7.6, +26.3] | +0.6 [−7.0, +7.6] | −2.3 [−7.0, +2.9] |
| gemini-flash-none | 57 | +9.4 [−0.6, +20.5] | −0.6 [−8.8, +7.6] | +0.6 [−9.9, +11.1] |
| gpt-5.5-high | 15 | −8.9 [−24.4, +6.7] | +15.0 [+3.9, +26.2] | +2.3 [0.0, +7.0] |
| gpt-5.5-none | 15 | +15.0 [0.0, +32.5] | +8.9 [0.0, +24.4] | 0.0 [−6.7, +6.7] |
| sonnet-4.6-none | 15 | +17.8 [+2.2, +37.8] | 0.0 [−6.7, +6.7] | −2.2 [−15.6, +13.3] |
| sonnet-4.6-thinking | 15 | +4.4 [−4.4, +15.6] | −1.9 [−10.7, +7.1] | +4.4 [−11.1, +24.4] |

**MPI − None (pp)**: +17.7 to +37.4 for every open model, intervals
excluding zero; +8.9 [−13.3, +33.3] for sonnet-4.6-none, +24 to +51 for the
other frontier arms. Figure 8's claim stands.

What this means for §5:

- Across the defined levels, more positive information does not reduce
  pass rate for any model with n ≥ 48. DeepSeek and Gemini-high are 14 to
  23 points above MPI at One-Hop and Two-Hop with intervals excluding
  zero; Kimi-high is flat. The "sweet spot then degradation" story in §5.2
  came from the mislabeled 2-hop closure level and the scoring artifact.
- Relative to matched-length filler, content clearly helps only at
  MPI+Signatures (v3.2, gemini-high, and the three frontier non-thinking
  arms). At One-Hop and Two-Hop every open-model interval includes zero.
  There is no evidence that positive information hurts more than neutral
  information at these levels and sample sizes. Kimi-high at Two-Hop
  (−4.5 [−10.4, +1.2]) is the closest to it.
- The open-vs-closed contrast (§5.2) cannot be assessed at n = 15.
- The surviving result: the first step past the MPI (type signatures) adds
  real value over filler; further derivational content adds little either
  way, so gains flatten while cost grows. That is a narrower claim than
  pollution, and it is what the data support.

## Runs still needed

| what | config | why |
|---|---|---|
| refill missing cells at stepk:2, hint:0–2 | `configs/main_v3_resume.yaml` | API timeouts, no retry (§3) |
| hint:3 + all noise rungs, open models | `configs/main_v4_rerun.yaml` | fitted filler (§5) and trace-based closure (§7) changed these prompts |
| frontier models on all 100 theorems, paper rungs | `configs/main_v4_frontier.yaml` | n=15 cannot support the open/closed contrast |

Until `main_v4_rerun` exists, the One-Hop marginal (`hint:2 − noise:2`) and
everything at Two-Hop in the rescored figures use the old prompts. Figures
merge runs with last-run-wins per cell, so `--runs main_v3_rescored
main_v4_rerun` replaces the stale rows without editing `main_v3`.
