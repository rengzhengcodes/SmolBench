# PACKAGE moe-tp8 — closing the last two determinism-certification gaps

**Status: COMPLETE.** 2026-08-22 UTC. Spent ~$61.9 of a $90 cap in ~3 h 15 min of a
4.5 h wall. Both boxes terminated and verified across three regions.

**Headline:** the determinism bundle **holds for an MoE at tp=8** (2/2 within-process,
two independent processes, ~35k tokens, one prompt) and **holds on the
`--disable-custom-all-reduce` NCCL path** (1/1 full-length row, flag confirmed in
vLLM's own engine config). The stock positive control **fired 0/4**. Not "certified":
the MoE arm has zero prompt diversity — see the verdict for the recommended follow-up.

## What was already certified (context)
The bundle `--no-enable-prefix-caching --max-num-seqs 1 --enforce-eager --seed 0`
(+ digest/revision pins) is certified at **tp=1**, **tp=4** (g6e.12xlarge, 4x L40S,
8/8 both models, stock control 1/4), and **tp=8 dense with the custom all-reduce
kernel active** (p5.48xlarge, 8x H100, `tp8hinge_ministral-3-3b.json`, 8/8).

## The two gaps this package attacks
- **A — MoE expert routing TP-sharded at tp=8.** Every tp=8 spec in the study is an
  MoE and none carries `--enable-expert-parallel`, so experts are TP-sharded and
  each layer carries a second reduction. Nothing measured so far exercises it.
- **B — the `--disable-custom-all-reduce` NCCL-fallback path**, which both deepseek
  specs pin. tp=8 was certified only with the custom NVLink kernel active.
- **C — stock@tp8 positive control** (tonight's run deadline-missed it), so a clean
  result cannot be dismissed as "the probe went blind on this silicon".

## Pre-registered method and rules (fixed before any data was seen)
- Protocol is the hinge's, unchanged: the same deterministically-selected real
  deduction prompts from each model's own S3 run dir, seed 0, temperature 0.7,
  `max_tokens=32768`, streaming, two back-to-back passes inside **one** server
  process, byte-compared.
- **k (number of prompts) is the only knob.** `max_tokens` stays 32768 so every row
  stays comparable to the tp=1/tp=4/tp=8-dense arms; a reduced cap would not be.
  k is chosen from a **measured** tokens/s (a discarded 256-token probe issued right
  after each serve), not a guess.
- Prompt selection is **prefix-stable**: `load_prompts(model, 8)[:k]`, never
  `load_prompts(model, k)` (the stride `keys[::len//n]` picks a different set for a
  different n unless the count divides cleanly). Verified pre-flight: both models
  resolve to the *same* 8 prompt ids, so arm B/C rows are directly SHA-comparable
  to the committed tp=8 dense arm.
- Empty rows (len <= 1) are **unmeasured, not divergent** (DETERMINISM_PLAN §1.3).
- **Verdict rule:** k/k byte-identical after that exclusion => the bundle HOLDS for
  that arm at tp=8. Any non-empty divergence => it does not, and the first differing
  byte offset is reported. **k is stated in every verdict sentence.**
- P2 covers exactly the rows P1 completed, so a truncated arm reports k/k over a
  smaller k rather than a spurious divergence.

## Pre-flight findings (before any spend)
1. **`capture_serve_log`'s fixed, authenticated version has never run live.**
   Tonight's committed report carries the OLD 3-key shape
   (`serve_log_tail_chars/serve_log_tail/topology_lines`, all empty) — the fixes
   were written *after* that run. Since that function is the sole producer of arm
   B's headline evidence ("custom all-reduce is actually OFF"), the driver asserts
   and logs it immediately after each serve, and arm B carries **two independent
   fallbacks**: the recorded launch payload (proves the flag was passed) and a SHA
   comparison against tonight's custom-all-reduce run (proves the collective kernel
   actually changed).
2. **Region us-west-2 chosen**, not tonight's us-east-2: the S3 model cache
   (`s3://smolbench-model-cache-414266451290/hf`, `EC2_S3_CACHE_REGION=us-west-2`)
   is local there, which for a ~240 GB pull beats us-east-2's ~$0.40/h price edge
   plus ~$5 of cross-region egress and a slower pull.
3. **Spot prices probed** (2026-08-22, `describe-spot-price-history`, cheapest AZ):
   p5.48xlarge us-east-2a $19.98, us-west-2b $20.38, us-east-1d $20.64;
   p5e.48xlarge us-east-2a $23.99, us-west-2c $24.57; p5en ~$26.3–26.9.
   The task's ~$36/h figure is stale — at ~$20/h the $90 cap buys ~4.4 h of box.
4. **Instance family taken from the study's own record**, not guessed:
   `run_fleet.TIER_MEMBERS` puts nemotron-3-super-120b-a12b in tier C, whose hunt
   list is `p5.48xlarge,p5e.48xlarge`. Driver uses exactly that.
5. `derive_tp` = gcd(32 heads, 8 GPUs) = **8** for both models; asserted from the
   recorded launch payload after every serve, and a mismatch aborts that arm.

## Results
_(filled in as rows land)_

### Box (single instance, us-west-2)
`i-047406b97c0d2a80f`, **p5.48xlarge @ us-west-2b**, 8x H100 80GB, launched
2026-08-21T23:48:45Z. Bid cap $25.81/h (1.25x the 13-AZ median); prevailing
us-west-2b price $20.38/h. vLLM image pinned by digest
`sha256:26354b5e…0e93f7` = `0.27.2rc1.dev122+g8efa13b70` — the same build tonight's
tp=8 dense arm and the whole study used.

### Arm A — MOE-DET-TP8 (nemotron-3-super-120b-a12b, bundle, tp=8)
Serve took **4.9 min** (S3 model-cache hit; the ~240 GB pull did not have to go to
HF). **tp GATE PASSED: tp=8** from the recorded launch payload; `8x H100 80GB`.
Served args are the spec's, bundle intact:
`--revision d51eab0d… --tokenizer-revision d51eab0d… --gpu-memory-utilization 0.92
--no-enable-prefix-caching --max-num-seqs 1 --enforce-eager --seed 0`.
KV: `enable_prefix_caching="False"`, `kv_cache_size_tokens=10584064`.

**Pre-flight finding #1 resolved — the fixed `capture_serve_log` works.** First live
run of the authenticated version: HTTP 200, 14 000 chars of vLLM's own log.
Topology evidence recorded rather than inferred:
- `Worker_TP0 … Worker_TP7` — **all 8 ranks**, independently corroborating the tp gate.
- `[routed_experts.py:1074] Unexpected gate/up projection names…` on **every one of the
  8 ranks** — the MoE routed-expert code path is live and TP-sharded across all ranks,
  which is precisely gap A.
- `[compilation.py:329] Enabled custom fusions: norm_quant, act_quant, allreduce_rms`
  — the fused all-reduce+RMS kernel, i.e. arm A runs the same NVLink collective
  tonight's dense arm certified. **Caveat:** this same line also appears in arm B's
  log *with* `--disable-custom-all-reduce` set, so it does **not** discriminate
  between the two collectives; only the parsed `disable_custom_all_reduce` config
  value does.
- `engine_config_lines` is empty: the agent's `/status` returns `docker logs --tail 300`,
  and vLLM's "Initializing a V1 LLM engine" banner has already scrolled off by the time
  the server is healthy. Not a capture failure — the flags are proven from the launch
  payload and `vllm_cache_config` instead.

**Measured throughput → k.** The 256-token probe returned 859 chars in 25.5 s ≈
**8.4 tok/s** (a ~120B-A12B MoE at tp=8 in eager mode, batch 1 — latency-bound, not
FLOP-bound). Against a 119.7-min remaining window and two passes, the pre-registered
rule selects **k=1**: one full-length (`max_tokens=32768`) row, twice. This is the
honest landing of the "k is the only knob" rule — a 4-prompt arm at this rate needs
~4.5 h of box and would breach both caps. It is reported as 1/1 over N tokens, **not**
as "certified".

**ARM A RESULT — 1/1 byte-identical.**

| | prompt | P1 sha256[:12] | P2 sha256[:12] | chars |
|---|---|---|---|---|
| A | `AlgHom.fieldRange_of_normal/prompts/hint-2.md` | `8e16725af290` | `8e16725af290` | 33 897 |

- 0 empty rows excluded, 0 divergent rows, n before exclusion = 1.
- **Cache counters, before and after the arm (from the running server's own metrics):**
  `prefix_cache_queries_total 0.0`, `prefix_cache_hits_total 0.0`,
  `external_prefix_cache_queries_total 0.0`, `external_prefix_cache_hits_total 0.0` —
  unchanged at zero across both passes, so P2 was genuinely recomputed and not
  served from a cache.
- Row cost: 33 897 chars ≈ 8.5k output tokens in 15.6 min ⇒ **9.1 tok/s** sustained
  (the 8.4 tok/s probe was slightly pessimistic, as intended). Arm total 36.6 min
  including the 4.9-min serve.
- The row did **not** hit the 32768 cap, so this is a complete generation compared
  end-to-end, not a truncation compared against a truncation.

**Because arm A came in at 36.6 min instead of the 125-min worst case, ~90 min of
budget was freed.** It is being spent on an **extended MoE arm (A2)** on a fresh
box after arms B and C — same model, spec, bundle and prompt prefix, k=3 — so the
MoE verdict rests on more than a single row. A2 also yields a free **cross-process**
MoE reading (run 1 arm A vs run 2 arm A2 share row 1), the regime where the study has
so far measured only a *dense* 9.5% flip rate.

### Arm B — DENSE-DET-TP8-NOCAR (ministral-3-3b, bundle + `--disable-custom-all-reduce`, tp=8)
Same box, same process lineage, served after arm A (one instance at a time).
Serve 1.9 min. **ARM B RESULT — 1/1 byte-identical.**

| | prompt | P1 sha256[:12] | P2 sha256[:12] | chars |
|---|---|---|---|---|
| B | `AlgHom.fieldRange_of_normal/prompts/hint-2.md` | `00d27a22e6af` | `00d27a22e6af` | 92 486 |

0 empty rows excluded, 0 divergent rows. Cache counters `0.0` for all four
prefix-cache metrics before **and** after the arm. Arm total 24.0 min.

**Was the custom all-reduce actually OFF? Three independent confirmations.**
1. **vLLM's own engine config**, parsed live out of the container log:
   `tensor_parallel_size=8, disable_custom_all_reduce=True, enforce_eager=True,
   enable_prefix_caching=False, seed=0, pipeline_parallel_size=1`.
   (This is the fix that had never run live — it works, and here it even caught the
   startup banner, because the 3B loads fast enough that it is still in `--tail 300`.)
2. **The recorded launch payload** carries `--disable-custom-all-reduce` as the last arg.
3. The bytes differ from tonight's committed tp=8 dense arm — **0/1 identical**:
   `8f093ac12c9a` (93 555 chars, custom AR, us-east-2) vs `00d27a22e6af`
   (92 486 chars, NCCL fallback, us-west-2). **CORRECTED — this is NOT proof the
   collective changed the arithmetic.** Run 2 refutes that reading: arm A and arm A2
   are the same model, spec, bundle, image digest and instance type, differing only
   in process and box, and they produced 33 897 vs 105 359 chars on the same prompt
   at the same seed. Byte differences across processes are the *expected* baseline,
   so this comparison is confounded and can only be reported as **consistent with**
   a changed collective. Arm B's verdict does not rest on it: confirmations #1 and
   #2 are unconfounded and sufficient.
   Note also that this flag's byte-level effect is **not isolable by any design
   here** — it is a server-launch argument, so no same-process A/B of it exists.

### Arm C — STOCK-TP8 positive control (ministral-3-3b, stock config, tp=8)
Serve confirmed genuinely stock, again from vLLM's own config line:
`disable_custom_all_reduce=False, enforce_eager=False, enable_prefix_caching=True,
seed=0, tensor_parallel_size=8` — CUDA graphs on, prefix caching on, custom AR on.
Aside: stock is ~12x faster than the bundle here (54 554 chars in 33 s ≈ 400 tok/s
with graphs, vs ~33 tok/s under `--enforce-eager`) — that speed gap is the price the
determinism bundle charges, now measured at tp=8.

**ARM C RESULT — 0/1 identical. The positive control FIRED.**

| | prompt | P1 sha256[:12] | P2 sha256[:12] | chars P1 / P2 | first differing byte |
|---|---|---|---|---|---|
| C | `AlgHom.fieldRange_of_normal/prompts/hint-2.md` | `409c5aa4fff8` | `21a8c826e162` | 54 554 / 78 125 | **243** |

Two same-process passes of the *same* prompt at the *same* seed diverged after a
243-character common prefix and ended 43% apart in length. So on this exact box, this
exact silicon and this exact vLLM build, **the probe demonstrably detects
nondeterminism** — arms A and B being byte-identical is a property of the bundle, not
a blind instrument.

The cache counters make the contrast mechanical rather than nominal:

| arm | config | `prefix_cache_queries_total` after | `prefix_cache_hits_total` after |
|---|---|---|---|
| A (MoE, bundle) | `--no-enable-prefix-caching` | 0.0 | 0.0 |
| B (dense, bundle + no-custom-AR) | `--no-enable-prefix-caching` | 0.0 | 0.0 |
| C (dense, **stock**) | `--enable-prefix-caching` | **2638.0** | **1312.0** |

### Run 1 close-out
Elapsed 66.1 min (provision 2.0 min). Instance `i-047406b97c0d2a80f` terminated at
00:54:36Z; teardown verified by `describe-instances` across us-east-1 / us-east-2 /
us-west-2 (saved as `teardown_sweep_run1.txt`).
**Other people's boxes seen and deliberately NOT touched:** `i-0e52cb0bb33999a94`
(m7i.16xlarge, us-west-2c, tag `verify-lean`, state *stopped*). The task's
`flip2-nemotron-3-nano-4b` g6e.2xlarge in us-east-1 was not present in any region.

## Run 2 — extended MoE arm (second box, `i-0164bd9c5a9957a60`, p5.48xlarge @ us-west-2b)
Launched 00:59:30Z after run 1's box was confirmed terminating. Same spec, same
bundle, same prompt prefix; `k` requested = 4. Serve 5.1 min (S3 cache hit again),
**tp GATE PASSED tp=8**, 8x H100 80GB, same vLLM digest.

The throughput-probe bug found in run 1 was fixed here first: at `max_tokens=256` a
reasoning model never leaves its reasoning block, so the response carries
`content=None, finish_reason="length"`, the harness rejects it ("Body returned none
value"), and the measured rate collapses to 0 tok/s — which is exactly why run 1's
arms B and C fell back to k=1. Run 2 probes at 2048 tokens and falls back to the
rate measured tonight rather than to zero. It then read **8.9 tok/s** (vs the
engine's own `Avg generation throughput: 11.3 tokens/s` steady-state).

**A2 P1 row 1: 105 359 chars in 47.6 min** — this row ran to the `max_tokens=32768`
cap (~26k output tokens). The pre-registered pass deadline then did its job: at
55.8 min it stopped issuing new prompts, so **A2 lands at k=1 over a full-length
row** rather than overrunning the window. P2 covers exactly that row.

**An unplanned but notable cross-process observation.** The *same* prompt, *same*
seed 0, *same* bundle, *same* spec and instance type produced **33 897 chars on run
1's box and 105 359 chars on run 2's** — a 3.1x length difference. That is the
cross-process/cross-instance regime the study already documented for dense models
(9.5% flip rate, plan §6.2); this is the first MoE reading of it, and it is a
reminder that the bundle's guarantee is explicitly *within-process*. It is **not** a
within-process failure and must not be reported as one.

**ARM A2 RESULT — 1/1 byte-identical.**

| | prompt | P1 sha256[:12] | P2 sha256[:12] | chars |
|---|---|---|---|---|
| A2 | `AlgHom.fieldRange_of_normal/prompts/hint-2.md` | `197393c7f365` | `197393c7f365` | 105 359 |

0 empty rows, 0 divergent rows. Cache counters `0.0` on all four metrics after the
arm. Arm total 103.4 min (serve 5.1). **This row is cap-truncated** — it ran into
`max_tokens=32768` — whereas arm A's row was a complete generation that stopped on
its own. Both are valid byte comparisons; the distinction is noted because a reader
should not assume either shape.

Cross-process (run 1 arm A vs run 2 arm A2), same model/spec/bundle/instance type,
different process and box: **0/1 identical** — `8e16725af290` (33 897 chars) vs
`197393c7f365` (105 359 chars). Expected and documented, **not** a within-process
failure.

### Run 2 arm C — STOCK-TP8 control at k=4 (the upgrade run 1 could not afford)
Stock confirmed from vLLM's own config: `disable_custom_all_reduce=False,
enforce_eager=False, enable_prefix_caching=True, seed=0, tensor_parallel_size=8`.
Cache counters after the arm: **14 036 queries / 7 840 hits** (vs `0.0/0.0` in every
bundle arm). **0/3 identical**, 1 row excluded as empty (unmeasured, not divergent):

| prompt | P1 sha / chars | P2 sha / chars | first differing byte |
|---|---|---|---|
| `AlgHom.fieldRange_of_normal/…/hint-2.md` | `9b716dfd16c3` / 104 990 | `ba1da0a11ecf` / 76 751 | 85 |
| `CategoryTheory.essentiallySmall_iff/…/noise-3.md` | `3d510e74f8c1` / 61 398 | `2a2a05654a71` / 27 573 | 1 735 |
| `Filter.compl_mem_comap/…/noise-3.md` | `770e09f85115` / 57 335 | `cb7949e532c0` / 26 700 | 264 |
| `CategoryTheory.Limits.Types.Pushout.condition/…/hint-2.md` | — | — | excluded (empty) |

Across both runs the control is **0/4 identical**. The instrument is not blind on
this silicon, this build, or this tp degree.

### Optional arm B extension — deliberately NOT run
Run 2's arm B (no-custom-AR at k=3) began serving at 02:54 and would have finished
~03:43 against a 03:55 wall, on a question already answered by three independent
confirmations. The driver was killed and the box terminated instead. Two extra
prompts were not worth risking the deliverable.

## Spend ledger
Actual spot price for p5.48xlarge in us-west-2b throughout the window (from
`describe-spot-price-history`, not an estimate): **$20.3808/h**.

| box | window (UTC) | minutes | cost |
|---|---|---|---|
| `i-047406b97c0d2a80f` (run 1: arms A, B, C) | 23:48:45 → 00:54:36 | 65.9 | **$22.38** |
| `i-0164bd9c5a9957a60` (run 2: arms A2, C) | 00:59:24 → 02:54:53 | 115.5 | **$39.23** |
| EBS, 700 GB gp3 x2 boxes, pro-rated | — | — | ~$0.24 |
| S3 | model-cache reads/writes intra-region; results reads | — | ~$0.00 |
| **TOTAL** | | **181.4** | **≈ $61.9** |

Under the $90 cap with ~$28 unspent. Wall ~3 h 15 min of the 4.5 h allowed.
Spot capacity was found first try in the first AZ tried, both times: **zero spot
failures**, so the two-failure stop rule never engaged.

## Teardown
`shutdown_instance()` terminated run 1's box at 00:54:36Z; run 2's box was terminated
by hand at 02:54:53Z after the driver was killed. Verified by `describe-instances`
across **us-east-1, us-east-2, us-west-2** — saved as `teardown_sweep_run1.txt` and
`teardown_sweep_final.txt`. No `moetp8` instance is running or pending in any region.
**Other people's boxes seen and NOT touched:** `i-0e52cb0bb33999a94` (m7i.16xlarge,
us-west-2c, tag `verify-lean`, *stopped*). The task's `flip2-nemotron-3-nano-4b`
g6e.2xlarge in us-east-1 never appeared in any sweep.

## VERDICT

**Gap A — MoE at tp=8: the bundle HOLDS, on 2/2 within-process comparisons.**
nemotron-3-super-120b-a12b under the bundle at tp=8 reproduced byte-for-byte in two
*independent* server processes on two *different* boxes: arm A 1/1 (33 897 chars,
complete generation) and arm A2 1/1 (105 359 chars, cap-truncated) — together
**~35k output tokens byte-identical**, with prefix-cache counters flat at zero
throughout, and with vLLM's log showing the routed-expert path live on all 8 TP ranks.
**This is 2/2, not "certified".** Both comparisons use the *same single prompt*, so
the MoE arm has **zero prompt diversity** and therefore no coverage of alternate
expert-routing trajectories — the very mechanism gap A exists to probe. Nemotron rows
cost 15–48 min each at ~9–11 tok/s under `--enforce-eager`, which is why one prompt
was all tonight's caps bought. **Recommended follow-up: 3–4 additional MoE prompts
(~$40, ~2 h) to buy routing diversity.**

**Gap B — the `--disable-custom-all-reduce` path: the bundle HOLDS, 1/1** over one
full-length row (92 486 chars ≈ 23k tokens), with the flag confirmed OFF *twice
over*: parsed straight out of vLLM's own engine-config line
(`disable_custom_all_reduce=True` alongside `tensor_parallel_size=8, enforce_eager=True,
enable_prefix_caching=False, seed=0`) and present in the recorded launch payload.
This is the collective both deepseek specs pin.

**Control: fired, 0/4.** Stock@tp8 diverged on every measurable row across both runs,
first differing bytes at offsets 85–1 735. The clean arms are a property of the
bundle, not of a blind probe.

**Caveat carried forward:** the bundle's guarantee is *within-process*. Arm A vs A2
— identical model, spec, bundle, image digest and instance type, differing only in
process and box — gave 33 897 vs 105 359 chars on the same prompt at the same seed.
That is the first MoE reading of the cross-process regime the study measured at 9.5%
for dense models, and it is consistent with it.

---

## CORRECTION 2026-08-23 — run 2's arm C control was 0/4, not 0/3

*Appended, not rewritten. Everything above records what was believed on 2026-08-22
and is left intact; this block supersedes it on the points named here.*

### What was wrong

The "Run 2 arm C" table above marks
`CategoryTheory.Limits.Types.Pushout.condition/…/hint-2.md` as `— / — / excluded
(empty)`. That row was **not** unmeasured. It was the most divergent outcome the
arm produced:

| pass | sha256_12 | stored chars | what it actually was |
|---|---|---|---|
| P1 | `1e6e5acf9886` | 83 661 | a normal generation |
| P2 | `6e340b9cffb3` | 1 | a **106 545-character reasoning-only cap-hit** (`finish_reason=length`, `completion_tokens=32768`) that the client DISCARDED on delivery |

The P2 request was issued twice — the length-≤1 delivery-fault retry fired — and
**both attempts returned the same 106 545-character reasoning body**, so the row
was reproducible on the wire. It was the *client* that threw the text away, not
the network. Recovered from the run log, that discarded P2 body and P1 share a
common prefix of **754 characters** and diverge thereafter. (Against the row as
actually stored, `"\x00"`, the common prefix is 0.)

Two defects combined to produce the `—` cells:

1. **The client's null-content early return hardcoded `reasoning=None`**, so a
   generation that spent its whole budget in the reasoning channel collapsed to
   the single `\x00` separator byte and became indistinguishable from a row that
   was never delivered.
2. **`guarded_compare` excluded a row when EITHER pass was ≤ 1 character**, so an
   83 661-vs-nothing row left the denominator entirely instead of counting as the
   divergence it is.

Both are fixed as of this commit
(`smolbench/evals/openai_compat.py`, `scripts/tp4_hinge_probe.py`,
`scripts/tp8_hinge_probe.py`; pinned by `tests/test_openai_compat.py` and
`tests/test_determinism_probes.py`).

### Corrected numbers

Under the corrected rule a one-sided empty row is **DIVERGENT** and stays in the
denominator. Replayed against the archived pass texts:

| | published 2026-08-22 | corrected |
|---|---|---|
| run 2 arm C (stock@tp8 control) | 0/3, 1 row excluded | **0/4**, 0 rows excluded |
| pooled control, run 1 + run 2 | 0/4 | **0/5** |

The two `—` cells in the run-2 arm C table should be read as `1e6e5acf9886` /
83 661 (P1) and `6e340b9cffb3` / 1 (P2). Every row in that arm diverged.

### Blast radius: this row and no other

Every other comparison in the committed archive recorded
`excluded_empty_rows: []`, so the corrected rule changes no other number —
verified across `moe_tp8_report.json` (arms A, B, C), `moe_tp8_report_run2.json`
(arm A2), `tp4hinge_ministral-3-3b.json`, `tp4hinge_nemotron-3-nano-4b.json` and
`tp8hinge_ministral-3-3b.json`.

**No HOLD verdict changes.** The correction moves only the positive control's
denominator, and the control still fired on every measurable row — now 0/5 rather
than 0/4. "The clean arms are a property of the bundle, not of a blind probe"
stands, with one more divergence behind it than was reported.

The committed report JSONs are deliberately **not** edited: they are the primary
record of what the run observed, and the corrected reading belongs here.

### Verdict lines restated with their control scope

`HOLDS` on its own does not say what would have caught a failure, so the two
verdicts are restated with the scope of the control that backs them:

- **Gap A — MoE at tp=8: HOLDS, 2/2** — control: stock@tp8 **0/5** pooled; per-arm
  perturbation sensitivity row **ABSENT** (that mechanism postdates this run).
  Both comparisons use the same single prompt, so this remains evidence, not
  certification.
- **Gap B — the `--disable-custom-all-reduce` path: HOLDS, 1/1** — control:
  stock@tp8 **0/5** pooled; per-arm perturbation sensitivity row **ABSENT**.

Arms run after this commit carry a per-arm perturbation sensitivity row
(`hardware_equivalence_probe.run_sensitivity_row` / `evaluate_sensitivity` /
`verdict_line`). An arm whose control comes back BLIND now reports **UNMEASURED**
and can no longer report HOLD, and every emitted verdict string names its own
control scope.

---

## FURTHER CORRECTIONS 2026-08-23 — adversarial-audit findings applied

*Appended, not rewritten; same convention as the block above. Source: the
2026-08-22 adversarial verification campaign (65 agents, two refutation
rounds) plus the 2026-08-23 independent re-verification. Each item names
what the text above (or the commit message) got wrong.*

1. **Commit e3068d21's "~12x" is wrong as written; this document's is right.**
   The commit message pairs "~12x throughput" with "(~9-11 tok/s on the 120B
   MoE vs ~400 stock)". Those numbers give 36-44x and cross models: ~400 tok/s
   was measured on the DENSE 3B stock arm, 9-11 tok/s on the 120B MoE bundle.
   The ~12x above (Arm C aside: 400 vs ~33 tok/s) is dense-vs-dense and
   correct. **No MoE stock arm exists, so the eager-vs-graphs cost for the MoE
   is unmeasured.**

2. **A2 "cap-truncated" is unsupported and probably wrong.** No finish_reason
   or token count was recorded for A2's accepted row (the run-2 log carries
   them only for arm C's client-REJECTED bodies; recording on accepted rows
   was added at fadfab16); the doc's own chars/4 proxy gives ~26.3k tokens,
   BELOW the 32,768 cap; and the raw text ends in a complete final answer
   (`rw [AlgHom.fieldRange_eq_map]`, exactly the tactic the reasoning
   announced). The one pairing that lands near the cap — 47.6 min at the
   engine's 11.3 tok/s = 32,273 tokens, 1.5% below — means truncation cannot
   be fully excluded, only unsupported.

3. **"First differing byte" columns are CHARACTER offsets.** The comparator
   zipped Python strings. As UTF-8 bytes: 243 -> 243, 85 -> 85, 1,735 ->
   1,763, 264 -> 276. Identity verdicts are unaffected (sha256 is computed
   over encoded bytes).

4. **The "k is the only knob, from a measured tokens/s" rule governed 1 of 5
   arms.** Run-1 arms B and C picked k from a 0.0 tok/s broken probe (the
   256-token bug disclosed above) via the `max(1, k - 1)` floor. Run-2 arms
   A2 AND C overrode the estimator (k_from_estimator=1) with `--force-k 4`;
   A2's override is disclosed above ("k requested = 4"), arm C's was not —
   this line is that disclosure. Under the corrected control counting above
   (0/5), 4 of the 5 pooled control rows exist only via that override
   (run-2 arm C's 4 rows; run-1 contributed 1); they strengthen the
   control, so no verdict changes.

5. **Line "run 2 ... same ... prompt prefix; k=3" conflicts with "k requested
   = 4".** The record: `k_forced=4, k_chosen=4, k_from_estimator=1`; the
   deadline landed A2 at k=1. The "k=3" was the pre-run plan and is wrong as
   a description of the request.

6. **"tp=4 ... stock control 1/4" (context section) folds a rate the tp=4
   record forbids.** TP4HINGE_SUMMARY.txt: "3/3 divergent among rows compared
   as-drawn; the 4th (AlgHom) was a length-1 delivery fault in P1 whose
   SEPARATE retry happened to match P2 -- do not fold into a rate."

7. **Spend-ledger details.** (a) "EBS, 700 GB gp3 x2": the probe never set a
   volume size, so the harness default **300 GB** applied; EBS is ~$0.10, not
   ~$0.24. (b) "~3 h 15 min ... wall" matches no artifact: the ledger's
   box-time sums to 3h01m, launch-to-final-teardown spans ~3h06m; the figure
   is session clock, unauditable from the record. (c) The prose launch times 23:48:45Z /
   00:59:30Z are LOCAL post-IP-wait stamps. The ledger is mixed-basis: box
   1's row starts from the local stamp (AWS LaunchTime 23:48:39Z, a 6 s /
   ~$0.03 gap), while box 2's row starts from 00:59:24, which IS the AWS
   LaunchTime.

8. **The two vLLM API keys embedded in the committed report JSONs were
   redacted on 2026-08-23** (`api_key` values inside the captured
   `engine_config_lines`, 9 occurrences in `moe_tp8_report.json`, 6 in
   `moe_tp8_report_run2.json`, replaced by `REDACTED-DEAD-KEY-2026-08-23`).
   Both keys were per-run server credentials for boxes terminated on
   2026-08-22. The original bytes remain BOTH in git history at e3068d21 AND
   in plaintext inside the committed r7-moe-tp8 evidence tarball (unmodified
   here — evidence archives are not rewritten), so this redaction is hygiene
   for the working reports, not removal from the record. The EVIDENCE.json
   shas for both files were updated in the same commit.
