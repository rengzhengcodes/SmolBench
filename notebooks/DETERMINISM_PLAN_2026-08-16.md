# Generation determinism: what is measured, what it means, and how to diagnose it

**2026-08-16.** A documentation + diagnosis plan for the family-ladder study's
hardware/seeding anomalies. This document **plans**; it does not fix, does not
re-collect, and nothing in it was executed. No instance was launched and no
study code, data or config was touched in producing it.

**[Corrected 2026-08-21 — scope statement superseded.]** The paragraph above was
true of the document as written on 2026-08-16 and is no longer true of the record
it now carries. Sections 3, 5, 6.2 and the §4 adoption were subsequently executed:
four boxes were launched (2 hinge 2026-08-16, 1 flip 2026-08-18, 1 gzip canary
2026-08-18), S3 objects were written under
`deduction/runs/flip_nemotron-3-nano-4b/`, and study code and config were modified
(`ec2.py`, `agent.py.txt`, `run_fleet.py`, both notebook `keys.env`) by commits
`91cac390`, `57618f26`, `a1cf5033`, `3f6f342f`, `48c08fb8`. Each executed section
carries its own dated banner; read those, not this preamble, for status.

Everything below is labelled **[VERIFIED]** (measured, with the file and line that
shows it) or **[PROPOSED]** (a check to run, not yet run). Where I could not
verify something I say so rather than asserting it.

---

## 0. Headline, and a retraction the inventory needs

`CONTAMINATION_INVENTORY_2026-08-15.md` lines 40–41 state:

> **vLLM output here is reproducible within one server process and not across
> processes**

**That second half is false, and the evidence to refute it was already sitting in
the archive.** [VERIFIED]

Cross-referencing the two archived probe reports by SHA — which nobody did,
because each report was read on its own — two *different boxes, of different
instance sizes, in different regions, ten hours apart* produced **byte-identical
output on all 8 prompts**:

| pass | instance | type | AZ | time (UTC) |
|---|---|---|---|---|
| probe-1 `B1` | `i-039b6c4894f4cdbbf` | `g6e.2xlarge` | us-west-2a | 03:24–03:30 |
| probe-2 `A1` | `i-0d26b6a3178a18ea9` | `g6e.4xlarge` | us-east-2b | 12:54–13:06 |

All eight SHAs coincide: `232661bd9fca`, `cf2d95156f82`, `bfc4db1dda26`,
`0d2a3b5f9a68`, `a764a6856ddd`, `7ef1c77eab9f`, `7664c99e91e4`, `fb2f975bacb5`.

*Evidence path:* `notebooks/deduction/results/hwprobe_archive/nemotron-3-nano-4b_4xl-vs-2xl.json`
field `cross_size.diffs[].sha_b` vs
`nemotron-3-nano-4b_4xl-vs-4xl-BOX2BOX.json` field `cross_size.diffs[].sha_a`.
Output lengths corroborate independently in the logs
(`hwprobe_nemotron-3-nano-4b.log:328-335` and
`hwprobe_box2box_nemotron.log:35-42`), and the launch lines
(`hwprobe_box2box_nemotron.log:27`) confirm probe-2's `A` arm was a freshly
provisioned box, not a reuse of probe-1's data.

A second, weaker coincidence points the same way: the *other* two boxes
(`i-09ec5e5bcdefe8994` 4xl, and `i-08453f45196520f25` 4xl) agree byte-for-byte on
`Filter.compl_mem_comap/prompts/noise-3.md` — SHA `2021ea7368fa`, 3883 chars, the
shortest output in the set — while disagreeing on the other seven. [VERIFIED]

> **[Corrected 2026-08-21: "the shortest output in the set" is wrong — it is the
> SECOND-shortest.]** Per-prompt lengths across all four processes
> (`hwprobe_archive` `len_a`/`len_b`): `Filter.compl_mem_comap`/noise-3 =
> [3883, 3484, 3484, 3883], while `Order.pred_eq_iSup`/stepk-1 =
> [3408, 3348, 3348, 2892] — strictly shorter in every one of the four
> processes. And `Order.pred_eq_iSup` DISAGREED in this very `P1A`/`P2B`
> pairing (SHAs `8ef6509369b5` vs `9c96602656f6`). The 1/8 agreement itself
> stands; only the "shortest" label and the length-based reading of it are
> retracted (see the corrected paragraph below).

**So cross-process agreement is not 0.** The two archived reports together carry
per-prompt digests for **four distinct serving processes**, which is enough to
tabulate all six pairings rather than the two each report printed. Done in full
(orchestrator check, 2026-08-16) [VERIFIED]:

| pairing | agreement | |
|---|---|---|
| `P1B` i-039b **2xl** us-west-2a vs `P2A` i-0d26 **4xl** us-east-2b | **8/8** | different type, different region, ~9.5 h apart |
| `P1A` i-09ec 4xl vs `P2B` i-0845 4xl | **1/8** | only `Filter.compl_mem_comap` [Corrected 2026-08-21: the SECOND-shortest output, not the shortest] |
| `P1A` vs `P1B` · `P1A` vs `P2A` · `P1B` vs `P2B` · `P2A` vs `P2B` | **0/8** | |

Reproduce with the script in Appendix A.

**Three groups, not two.** `{P1B, P2A}` is one regime; `P1A` and `P2B` each sit
alone, agreeing with each other on exactly one prompt — the shortest generation in
the set (3,883 chars, against a median near 15,000). That single agreement is
better read as **short outputs diverging less often** than as regime membership:
divergence is immediate when it happens (common prefixes 0–149 chars on the long
prompts) but every generation is a fresh chance to diverge, so the shortest one is
where two otherwise-different regimes are most likely to coincide.

> **[Corrected 2026-08-21 — the length-based reading is RETRACTED; the regime
> structure is not.]** "Three groups, not two" stands, as does the reading of the
> regime as a switch with a small number of positions. What does not stand is the
> *explanation* of the 1/8 agreement. The agreeing prompt
> (`Filter.compl_mem_comap`, 3,883 chars) is the SECOND-shortest generation in the
> set; the genuinely shortest, `Order.pred_eq_iSup` at 2,892–3,408 chars in all
> four processes, **disagreed in exactly this pairing**. The archive's own lengths
> therefore contradict "short outputs coincide most often", and the inference is
> dropped. The surviving descriptive facts: 1/8 agreement between `P1A` and `P2B`,
> and a median generation length of **13,735.5 chars** (min 2,892, max 146,719) —
> not "near 15,000". The prefix figure in this paragraph is also corrected below
> (§1.2): common prefixes run **0–1,062 chars**, not 0–149.

The regime tracks neither instance size (the 8/8 pair spans `2xl` and `4xl`),
region, nor time. This is not gradual numerical drift; it is a switch with a small
number of positions. That reframes the whole diagnosis: the question is not "why
is floating-point reduction unstable" but **"what per-launch state differs between
boxes, and why does it take only a small number of values."**

The `2xl`/`4xl` pair landing in the *same* regime is the strongest single clue in
this document, and it points away from hardware entirely: those two types differ in
vCPU and host RAM but carry the same 1× L40S 48GB, so whatever varies is orthogonal
to the accelerator — which is precisely where mechanisms 1, 2 and 4 in §2 live and
mechanism 8 does not.

The inventory's *practical* conclusions — noise not bias, do not re-collect —
survive this correction, and section 7 explains why. Its *mechanism* claim does
not.

---

## 1. The anomalies

### 1.1 Same-box, same-process reproducibility — `nemotron-3-nano-4b`: 8/8 [VERIFIED]

**Measurement.** Two back-to-back passes over the same 8 real deduction prompts on
one box, at the study's own temperature 0.7 / seed 0 / max_tokens 32768
(`scripts/hardware_equivalence_probe.py:58-60`). All 8 byte-identical.

**Evidence.** `hwprobe_archive/nemotron-3-nano-4b_4xl-vs-2xl.json` →
`baseline_same_box: {n: 8, identical: 8, rate: 1.0}`; reproduced in the box2box
report on a different box.

**What it does not establish — and this is a real limit.** Prefix caching is ON for
every roster model (`smolbench/evals/ec2.py:268` and per-spec
`"--enable-prefix-caching"`, e.g. lines 372, 398). Pass `A2` re-sends *the identical
prompts* that pass `A1` just sent. With prefix caching, `A2`'s prefill is therefore a
**cache hit that replays `A1`'s KV blocks** rather than recomputing them — so
identical decode from identical KV is close to guaranteed by construction.

**The 8/8 baseline may be measuring the cache, not the kernels.** It is not
established that the same box would reproduce itself on a *cold* cache. Nobody has
tested that, and the probe's design cannot distinguish the two. This is the single
most important limit in the existing measurement set, and §3 is built to close it.

*Honest caveat on the obvious follow-on story:* it is tempting to explain
`ministral`'s failure (§1.3) as cache eviction under heavier load. The measured
volumes do not support that cleanly — `nemotron`'s probe-1 `A1` pass generated
**~344k characters** total versus `ministral`'s **~314k**
(`hwprobe_nemotron-3-nano-4b.log:272-279`, `hwprobe_ministral-3-3b.log:920-927`).
Nemotron, the model that passed, produced *more*. Eviction remains a candidate
(what matters is block residency, not character totals) but it is not demonstrated,
and I am not going to assert it.

### 1.2 Cross-process divergence — 0/8, immediate [VERIFIED]

**Measurement.** `g6e.4xlarge` vs `g6e.2xlarge`: 0/8. `g6e.4xlarge` vs
`g6e.4xlarge` (same size, same AZ, 35 minutes apart): 0/8, common prefixes
0–149 characters.

> **[Corrected 2026-08-21: the prefix range is 0–1,062 characters, not 0–149.]**
> `nemotron-3-nano-4b_4xl-vs-4xl-BOX2BOX.json`
> `cross_size.diffs[].common_prefix_chars` = [0, 149, 0, 1062, 85, 894, 486, 573]
> — four of the eight exceed 149. (The 4xl-vs-2xl file is
> [0, 74, 0, 1062, 1250, 16, 0, 428], range 0–1,250.) The instance facts in the
> sentence are correct: both boxes `g6e.4xlarge` in us-east-2b, launched 12:49:32Z
> and 13:24:34Z, 35m02s apart (`hwprobe_box2box_nemotron.log:27,80`).

**Evidence.** `nemotron-3-nano-4b_4xl-vs-2xl.json` and
`..._4xl-vs-4xl-BOX2BOX.json`, both `cross_size.rate: 0.0`. (Note the field is
*named* `cross_size` in the box2box file but is cross-*box at fixed size* — the
script's key names assume the size comparison,
`hardware_equivalence_probe.py:196`.)

**What it establishes.** Instance size was never shown to matter. Divergence, when
it happens, happens almost immediately — a single early token differs and the
trajectories separate. [Corrected 2026-08-21: "almost immediately" holds for about
half the prompts; on the rest the trajectories stay identical for several hundred
to ~1,000 characters before separating.]

**What it does not establish.** That divergence is the normal case. §0 shows it is
not: the same script's own archive contains an 8/8 cross-process pairing. n = 8
prompts, one model, one prompt set; four processes total. Treating "0/8" as *the*
cross-process rate over-generalises from two of the three measured pairings.

### 1.3 `ministral-3-3b`: 0/8 on its own same-box baseline [VERIFIED, with a correction]

**Measurement.** Two back-to-back passes on one box (`i-0a54cf013b91abc3a`,
`g6e.4xlarge`, us-east-2c): 0/8 identical.

**Evidence.** `hwprobe_archive/ministral-3-3b_4xl-vs-2xl.json`,
`baseline_same_box.rate: 0.0`; log `hwprobe_ministral-3-3b.log:910-936`.

**Correction to the inventory's reading.** The inventory (line 29-30, line 86)
concludes "the model is not reproducible on a single box at a fixed seed... nothing
can be measured for it." Two things qualify that:

1. **Row 1 is a delivery fault, not model nondeterminism.** `len_a: 1` for
   `AlgHom.fieldRange_of_normal/prompts/hint-2.md`. The probe stores
   `(reasoning or "") + "\x00" + (content or "")`
   (`hardware_equivalence_probe.py:112`), so **length 1 is the separator alone —
   a completely empty response.** That is the exact signature of the transport
   fault measured the *next day*: commits `82dc6056`, `73469ad7` and `50ea57f5`
   (all 2026-08-16, i.e. **after** this probe ran on 08-15) document the server
   finishing generations that never cross the wire, with loss perfectly correlated
   with response length. The probe ran on the reverted client stack
   (`2712dbdc`, 2026-08-15 04:44Z, before the 05:05Z launch), i.e. the stack that
   exhibits the fault.
2. **But transport explains 1 of 8 rows, not the baseline.** The other seven have
   non-zero common prefixes — 268, 1735, 1927, 2380, 1863, 335, 258 characters —
   which is genuine mid-generation divergence, not a lost body. The 0/8 stands as
   0/8; only its *interpretation* narrows.

**What it does not establish.** That the cause is "the model." No arm has ever been
run for `ministral-3-3b` with caching off or concurrency pinned, so "a property of
the model" is an inference from one configuration, not a measurement. §3 tests it.

### 1.4 Image identity was never actually pinned — and is partly recoverable [VERIFIED]

**What was known.** The roster runs `EC2_VLLM_IMAGE=vllm/vllm-openai:nightly`
(`scripts/run_fleet.py:484`; the module default is the pinned
`vllm/vllm-openai:v0.11.1`, `ec2.py:127`). A **tag is not a digest**; the inventory
inferred equality from a vLLM *version string*.

**New, and better than the inventory assumed.** `docker pull` digests *were*
captured incidentally in some fleet logs. Across `notebooks/`, **four distinct
image digests** appear, and one lane shows two of them in its own logs:

| digest (12) | log |
|---|---|
| `sha256:cec2df507519` | `deepseek-v4-flash.log`, `deepseek-v4-pro.log` |
| `sha256:0e1ee52750c6` | `deepseek-v4-flash.log`, `deepseek-v4-flash-v0271.log` |
| `sha256:df1979d8cfbc` | `ministral-3-14b-s5of8.log` |
| `sha256:6b084be85c18` | `repair_ministral-3-3b.log` |

*Command:* `grep -rHE "Digest: sha256:" --include="*.log" notebooks/`.

**So nightly digest drift is confirmed real, and it is retroactively answerable for
the minority of lanes whose logs happened to capture a pull line.** It is *not*
answerable for the hardware probe's own four boxes — those logs contain no digest
line, so the probe's central "same image" assumption remains **unverified**.

**Corroborated independently by build strings, and the drift is wider than a
nightly nudge** (orchestrator check, 2026-08-16) [VERIFIED]. vLLM's own version
banner appears in the run logs, and **five distinct RECORDED builds spanning two
minor versions** served this study — recorded is the operative word: the
2026-08-16 `ministral-3-14b` streaming re-collection's 7 boxes pulled `:nightly`
that day and **no version string appears in any of their shard logs**, so the
true build count is ≥6 with at least one build unidentifiable. That is this
section's recording gap demonstrated live, on the study's final collection
event, while this document was already in the repo:

| build | log lines |
|---|---|
| `0.26.1rc1.dev602+g65b7662d3` | 611 |
| `0.27.2rc1.dev18+g3d204dfda` | 483 |
| `0.27.2rc1.dev77+gac7509e2b` | 308 |
| `0.26.1rc1.dev668+g3ee2df303` | 159 |
| `0.27.2rc1.dev110+gacb0f1dcd` | 19 |

*Command:* `grep -rhoaE "0\.2[0-9]\.[0-9]+rc[0-9]+\.dev[0-9]+\+g[0-9a-f]+" notebooks/*/results/ | sort | uniq -c`.

Two consequences. First, `0.26.1 → 0.27.2` is a **minor-version** span, not
adjacent nightlies — kernel and backend selection can differ outright between
those, which is exactly the discrete, few-valued switch §0 is looking for. Second,
the inventory's line 43-44 states both probe boxes reported `dev110`; probe-1's own
log records **`dev77`** (`hwprobe_nemotron-3-nano-4b.log`, sole banner line), so
that sentence describes some other pair of boxes and must not be read as covering
the probe. The regime↔build hypothesis therefore stays **untestable retroactively**
— the one thing that would settle §0 in a single query, and the data was never
written down.

**The fix has a name and a location.** `server_config.yaml`, already emitted per
run, already carries `instance_id` / `instance_type` / `gpu` / `tp` / `region` /
`availability_zone` / `hf_model_id` / `captured_utc` — and records the image as
`vllm_image: vllm/vllm-openai:nightly`, i.e. **the mutable tag**. The sidecar is
the right shape and the right place; it is recording the one field that cannot
identify anything. Adding the resolved digest, the vLLM build string and the HF
revision to *that existing dict* is the whole of §5's recording change.

### 1.5 Silicon pinning is necessary, not sufficient [VERIFIED]

`EC2_REQUIRE_GPU` compares the landed **instance type** against two static tables,
`_INSTANCE_GPU_COUNTS` / `_INSTANCE_GPU_NAMES` (`ec2.py:610-614`). It never calls
`nvidia-smi`. It passed `H200:8` for both `p5e` and `p5en`, which is precisely how
the `deepseek-v3.1` near-miss got through (inventory §"A separate defect").
Driver version, GPU UUID, clock/ECC state and actual SM count are unchecked.

### 1.6 What the serving stack does and does not fix [VERIFIED as of 2026-08-16 — the knob table describes the STUDY-ERA configuration; every row was reversed by `91cac390` on 2026-08-18]

Read from `smolbench/evals/payloads/agent.py.txt:137-153` (the `docker run`
argument vector) and `smolbench/evals/ec2.py`:

> **[Corrected 2026-08-21: this table is a historical record, not the current
> configuration.]** It is accurate for the tree the family-ladder study collected
> under, and that is what it is here to document — but it is present-tense and a
> reader arriving directly would take it for HEAD. The §4 adoption of 2026-08-18
> (`91cac390`) reversed every row: at HEAD the spec audit finds **0 of 22** specs
> with `--enable-prefix-caching`, and **22 of 22** carrying `--revision`,
> `--tokenizer-revision`, an explicit `--gpu-memory-utilization`, `--seed 0`,
> `--max-num-seqs 1` and `--enforce-eager`. Only the two unchanged rows —
> per-request `seed` is still passed, and `EC2_MAX_PARALLEL_REQUESTS` is still
> untouched at its default — read the same today. Nothing about the study-era
> facts below is retracted.

| knob | state | note |
|---|---|---|
| `--seed` (server) | **not passed** | only `--model`, `--served-model-name`, `--tensor-parallel-size`, `--max-model-len`, `--api-key`, plus per-spec `vllm_args` |
| per-request `seed` | **passed** | `smolbench/evals/openai_compat.py:659`, `"seed": seed` |
| `--enable-prefix-caching` | **on, every model** | `ec2.py:268` and per-spec |
| `--max-num-seqs` | **absent** | vLLM default |
| `--enforce-eager` | **absent** | CUDA graphs active |
| `--gpu-memory-utilization` | **absent** | default; KV block count therefore depends on free VRAM at profiling time |
| `--revision` (HF checkpoint pin) | **absent** | `grep revision` over `ec2.py` + `agent.py.txt` returns nothing |
| `EC2_MAX_PARALLEL_REQUESTS` | default **8** | `openai_compat.py:511`; study lanes set 4 (`resume_all_runs.sh:60`) or 8 (`relaunch_damaged_deduction.sh:170`) |

**Critical, and it changes the brief I was given:** the probe **never used
`evaluate()`**. `run_pass` is a plain sequential `for` loop issuing one `ec2.query`
at a time (`hardware_equivalence_probe.py:106-115`), so `EC2_MAX_PARALLEL_REQUESTS`
was **not in play** and **concurrency was exactly 1 in all four passes**.

Continuous batching therefore **cannot** be the variable that produced the 0/8
cross-box results, and "re-run the baseline with requests strictly sequential"
would be **specifying the status quo** — that arm was already, implicitly, the
condition under which every one of these numbers was measured. The batching
hypothesis is not refuted for the *study lanes* (which do run at fan-out 4–8); it
is refuted as an explanation of **the probe measurements themselves**, which are
the only measurements that exist.

---

## 2. Mechanisms ranked

Ranked by expected effect on the *observed pattern* — bimodal, per-launch,
independent of size/region/time — not by generic plausibility.

| # | mechanism | expected effect | how it is distinguished | cheap to test? |
|---|---|---|---|---|
| 1 | **Unpinned checkpoint bytes.** No `--revision`; `EC2_S3_MODEL_CACHE` can serve older mirrored blobs while a cache-miss box pulls current HF | **Large and discrete** — different weights are a different model. Fits bimodality exactly, and fits the size/region independence | Record resolved HF commit SHA + a hash of the loaded safetensors per box. Two regimes ↔ two hashes settles it in one launch | **Yes** — a recording change (§5), no extra box |
| 2 | **Unpinned image digest.** `:nightly` is mutable; ≥4 digests already observed (§1.4), incl. two within one lane | **Large and discrete** — kernel/backend selection changes between builds | Record the digest at serve time. If the two regimes map to two digests, done | **Yes** — recording change; partially recoverable already |
| 3 | **Prefix-cache replay inflating the same-box baseline** | Explains why *within*-process looks perfect while *across*-process is not, without any hardware story at all | Re-run the same-box baseline with caching **off**. If nemotron drops below 8/8, the published noise floor was cache replay | **Yes — this is the hinge, §3** |
| 4 | **Attention-backend / kernel autoselection** (FlashAttention vs FlashInfer vs Triton; chosen from driver + build + head-dim heuristics) | Moderate-to-large, and **discrete** — a different kernel is a different reduction order. Also fits bimodality | Pin `VLLM_ATTENTION_BACKEND` and record the backend line vLLM logs at startup | Yes, once the backend is recorded |
| 5 | **KV block count from free-VRAM profiling** (no `--gpu-memory-utilization`). Different `num_gpu_blocks` → different chunked-prefill / CUDA-graph bucket boundaries | Moderate; near-discrete (a small number of block counts) | vLLM logs `num_gpu_blocks` at startup — record it; pin `--gpu-memory-utilization` | Yes, once recorded |
| 6 | **Continuous batching / batch composition** (`EC2_MAX_PARALLEL_REQUESTS` 4–8 in real lanes) | Real for study lanes; **zero for every probe measurement taken so far** (§1.6) | Set `--max-num-seqs 1` and fan-out 1 | Yes, but it changes nothing in the probe regime |
| 7 | **CUDA-graph capture vs eager** | Small-to-moderate; deterministic within a process either way | `--enforce-eager` | Yes |
| 8 | **Driver / GPU-instance variation** (same L40S SKU, different host, clocks, ECC) | Small, and *continuous* — would produce a smear, not two regimes; poor fit to the data | `nvidia-smi` fingerprint at serve time (§5) | Yes, recording only |
| 9 | **Per-request sampler seeding** | Near-zero. Seed is passed per request and is constant; a *server* `--seed` mainly affects init-time RNG | Pass `--seed 0` and compare | Yes, one flag |
| 10 | **Tokenizer version drift** | Near-zero for divergence *mid*-generation with identical prompts; would change the prompt token IDs, not the 1000th token | Covered by #1's revision pin | Free with #1 |
| 11 | **Transport / silent socket loss** (`73469ad7`, `50ea57f5`) | Not a *sampling* mechanism, but it **corrupts determinism measurements** by turning a delivered response into an empty one — confirmed in 1 of 8 ministral rows (§1.3) | Use the streaming transport, and treat empty rows as unmeasured rather than divergent | Free — already implemented, opt-in |

**Not on this list, deliberately:** temperature and `top_p`. Temperature 0.7 with a
*fixed seed* is not a source of cross-process divergence — the sampler is
seeded and its draws are reproducible given identical logits. Temperature amplifies
a numerical difference into a *visible* token difference, but it does not create
one. Lowering temperature would mask the anomaly, not fix it, and would change the
study's own generation regime. Do not touch it.

---

## 3. The hinge experiment [RUN 2026-08-16 21:08–22:20Z — BOTH PREDICTIONS LANDED] [Corrected 2026-08-21: window was 21:08–23:00Z, and the accurate reading is "both pre-registered decision rules fired cleanly" — see the correction box below]

> **[Corrected 2026-08-21 — header, run window and cost.]** Two errors in the
> header line and the cost note above, both verified from the archived logs.
> (a) **"BOTH PREDICTIONS LANDED" overstates.** §3.2's column is "prediction if
> the cache/serving-config hypothesis holds", and arm A's entry there is "Drops
> below 8/8". Measured, arm A stayed **8/8** — so arm A's *prediction* did not
> land; what fired was §3.3's pre-registered **exoneration** criterion. Arm C's
> prediction did land (ministral 0/8 stock → 8/8 det). Read the header as **"both
> pre-registered decision rules fired cleanly"**. The body table below is faithful
> as written, and the pre-registration in §3-pre is untouched.
> (b) **Run window and cost.** UTC logs: nemotron `i-0a53a6a4624e29667` launched
> 21:07:58, terminate requested 22:22:23; ministral `i-06593b5a0a19b656c` launched
> 21:07:53, terminate requested 22:54:20 (terminations completed 22:27:56 and
> 23:00:08). The true window is **21:08–23:00Z** and the true usage **3.0
> box-hours** (3.2 h to termination complete) — matching §3.5's own ~3 box-hour
> estimate — i.e. **≈$4.2–5.2** at $1.39–1.71/hr, **INSIDE** the $4–7 envelope
> rather than under it. The published "~2.2 box-hours, ≈$3.5" understates box time
> by ~27%; the 22:20Z end is nemotron's arm alone and omits ministral's second arm.
> Independent cross-check from a different field, the reports'
> `serve_plus_passes_s`: 1800.1 + 2624.4 + 3135.0 + 3199.8 = 10,759.3 s = 2.99 h
> excluding boot.
> (c) **Scope.** Both hinge boxes were `g6e.4xlarge` — one L40S, **tp=1**, dense.
> Everything §3 certifies is certified at tp=1 on single-GPU serving; see the
> 2026-08-21 scope correction in §4.

> **Results** (user-authorized; `scripts/hinge_probe.py`; reports
> `notebooks/deduction/results/hwprobe_archive/hinge_<model>.json`; ~2.2 box-hours,
> ≈ $3.5 — under the $4–7 envelope; the section below is preserved verbatim as the
> pre-registration):
>
> | arm | prediction | measured | verdict |
> |---|---|---|---|
> | **B** nemotron stock | 8/8 (replication) | **8/8** | archived baseline replicates |
> | **A** nemotron det | drops if cache replay | **8/8** | **floor EXONERATED** — genuine kernel determinism, not cache replay; mechanism #3 drops out of §2 |
> | **D** ministral stock | 0/8 (replication) | **0/8** | archived anomaly replicates |
> | **C** ministral det | 8/8 if config | **8/8** | **"nothing can be measured for it" was the CONFIGURATION, not the model** — inventory corrected |
>
> The manipulation is content-verified, not flag-asserted: stock configs counted
> 3,904 (nemotron) / 10,320 (ministral) prefix-cache hits — pass 2 replaying pass
> 1's prefill, exactly the suspected mechanism — while both det configs read
> **0 queries / 0 hits**. Both boxes ran build `0.27.2rc1.dev122+g8efa13b70`
> (recorded per §5 — the study's sixth recorded build), same build across both
> configs per box. The one length-1 row (ministral stock:P2) re-asked per §3.3 was
> empty twice → a genuine cap-out, kept as the response.
>
> Two findings beyond the pre-registered questions:
>
> 1. **Cross-config is 0/8 on BOTH models** (same box, same seed, same prompts,
>    different serving flags; common prefixes 85–1502 chars
>    [Corrected 2026-08-21: **85–2,190 chars**. `hinge_nemotron-3-nano-4b.json`
>    `cross_config` = [173, 146, 236, 1062, 452, 459, 606, 505];
>    `hinge_ministral-3-3b.json` `cross_config` = [85, 857, 221, 336, 1379, 2190,
>    324, 209]. The value 1,502 appears in neither list — it is the maximum of
>    ministral's *stock same-box baseline* arm ([452, 1502, 221, 1451, 1379, 452,
>    0, 209]), a different comparison, which itself scored 0/8]).
>    Determinism's scope
>    is one process × one configuration — a config change flips generations as
>    thoroughly as a process change does.
> 2. **Ministral's stock 0/8 is NOT client concurrency** — the probe is strictly
>    sequential, so its within-process nondeterminism under the stock config comes
>    from the serving configuration itself (CUDA graphs vs eager, default
>    `max-num-seqs` scheduling, or cache-path numerics). Which of the three det
>    flags does the work is **not separable from this design** (they changed
>    together, deliberately — the recipe in §4 uses all three, so separating them
>    buys nothing for this study).
>
> Consequences applied: §1.1's "may be measuring the cache" limit is RESOLVED
> (it was not); §1.3's ministral narrowing is RESOLVED (config, not model);
> §2 mechanism #3 dropped; the §4 recipe is now empirically backed — **both
> models reach 8/8 under it**.

## 3-pre. The hinge experiment [as PROPOSED — pre-registration, verbatim]

### 3.1 What it decides

Whether the study's only "noise floor" is a real measurement of kernel determinism
or an artefact of prefix-cache replay — and whether `ministral-3-3b` is genuinely
unmeasurable or was simply measured in the one configuration that hides the answer.

### 3.2 Predictions, stated in advance

| arm | model | config | prediction if the cache/serving-config hypothesis holds |
|---|---|---|---|
| **A** (control, load-bearing) | `nemotron-3-nano-4b` | prefix caching **OFF**, `--max-num-seqs 1`, `--enforce-eager`, `--seed 0` | **Drops below 8/8.** If it does, the published noise floor was cache replay and §1.1's limit is confirmed |
| **B** | `nemotron-3-nano-4b` | unchanged (caching ON) — reproduces the archived baseline | 8/8, confirming the arms are comparable |
| **C** (the correction test) | `ministral-3-3b` | caching **OFF**, `--max-num-seqs 1`, `--enforce-eager`, `--seed 0` | **Goes to 8/8.** Then the inventory's "nothing can be measured for it" is wrong and must be corrected |
| **D** | `ministral-3-3b` | unchanged — reproduces the archived 0/8 | 0/8 (or 1/8; see the refutation note) |

Arm **A** is what makes this discriminating rather than confirmatory. Without it, a
`ministral` improvement in arm C is uninterpretable — it could be caching, eager
mode, or `max-num-seqs`, and there would be no control showing the *baseline itself*
is cache-sensitive.

### 3.3 Refutation criterion — stated so the result can go against me

- **The hypothesis is refuted if arm C stays at 0/8** with caching off, concurrency
  1 and eager execution. `ministral-3-3b` would then be nondeterministic within one
  process under the most restrictive configuration available, and the inventory's
  line stands (though it should still be re-worded: "not reproducible under any
  configuration tested" rather than "a property of the model").
- **The baseline is exonerated if arm A stays 8/8** with caching off. The 8/8 noise
  floor is then a genuine kernel-determinism result, not cache replay, and mechanism
  #3 drops out of the ranking.
- **Discard and re-run any row whose stored length is ≤ 1 character** — that is the
  delivery-fault signature (§1.3), not a divergence. Run these arms with the
  streaming transport (`50ea57f5`) enabled, or the experiment will re-measure the
  transport bug instead of the sampler.

### 3.4 Sample size

**n = 8 prompts per arm, the same 8 the archive used** — reusing them makes arms B
and D direct replications of the archived numbers, which is worth more than a
larger fresh set. n = 8 is adequate *because the effects being tested are
saturating*: 8/8 vs 0/8. Under a binomial with true per-prompt agreement p = 0.5,
the probability of observing 8/8 is 0.5⁸ = 0.4%, so an 8/8 result rules out
p ≤ 0.5. It cannot resolve intermediate rates — if an arm returns, say, 5/8, **the correct response is
to extend that arm to n = 32, not to interpret it.** Budget for that possibility.

### 3.5 Cost and wall-clock [spot price VERIFIED; box-time from archived logs]

- `g6e.4xlarge` spot, us-east-2, 2026-08-16: **$1.39 – $1.71/hr**
  (`aws ec2 describe-spot-price-history`, read-only; us-east-2b $1.3908,
  us-east-2c $1.6915).
- Archived pass timings: boot + serve ≈ 5 min; one 8-prompt pass 11–18 min
  (`hwprobe_nemotron-3-nano-4b.log:264-279`, `hwprobe_ministral-3-3b.log:910-936`).
- One box serves **both** configs for its model — the control agent's `/serve`
  endpoint swaps the container with new `vllm_args`
  (`agent.py.txt:119-153`), and each swap is a fresh process, which is exactly
  what a within-process baseline requires.

| | per box |
|---|---|
| 2 configs × 2 passes | ≈ 60–70 min |
| 2 container swaps + boot | ≈ 15 min |
| **total** | **≈ 1.5 h** |

**2 boxes in parallel → ≈ 1.5–2 h wall-clock, ≈ 3 box-hours, ≈ $4–7. Budget $10
including a re-launch after a spot reclaim, or $20 if an arm needs extending to
n = 32.** This is roughly 0.1% of the study's compute and is the cheapest
open question in it.

### 3.6 Commands

**Flag spellings are [PROPOSED, UNVERIFIED].** I could not check them against the
build actually in use (`0.27.2rc1.dev110+gacb0f1dcd`) without launching a box,
which is out of scope here. `--enable-prefix-caching` is verified present (it is
already in the specs); its *negation*, `--max-num-seqs`, `--enforce-eager` and
`--seed` are inferred from vLLM's conventional CLI and **must be confirmed first**:

```bash
# PRE-CHECK, on the box, before any arm runs:
docker run --rm --entrypoint vllm "$EC2_VLLM_IMAGE" serve --help \
  | grep -iE "prefix-caching|max-num-seqs|enforce-eager|\--seed|gpu-memory-utilization"
```

If `--no-enable-prefix-caching` is not the spelling in this build, the equivalent
is to *omit* `--enable-prefix-caching` — but note that prefix caching is **default-on
in vLLM V1**, so omission is not sufficient and the explicit negation is required.
**Confirm this before spending anything;** an arm that silently leaves caching on
answers nothing.

The probe already supports everything else needed. The only change is the
`vllm_args` the spec sends, so the arms are run by copying
`hardware_equivalence_probe.py` into the scratchpad and overriding
`EC2_DEPLOY_SPECS[model]["vllm_args"]` — **not** by editing the study spec:

```bash
set -a && source notebooks/ec2-operator.env && set +a

# arm B / D: archived config, replication
.venv/bin/python scripts/hardware_equivalence_probe.py \
    --model nemotron-3-nano-4b --type-a g6e.4xlarge --type-b g6e.4xlarge

# arms A / C: determinism config (scratchpad copy with vllm_args overridden to)
#   ["--no-enable-prefix-caching", "--max-num-seqs", "1", "--enforce-eager", "--seed", "0"]
#   (+ "--reasoning-parser","mistral","--language-model-only" for ministral-3-3b)
```

Both arms must additionally **record the §5 fingerprint**, or a null result will be
uninterpretable for the same reason the current archive is.

---

## 4. A determinism recipe for future runs [PROPOSED]

For a lane that must be internally bit-reproducible. Each line states its cost,
because several are not free.

| # | change | reason | cost |
|---|---|---|---|
| 1 | **Pin the image by digest**: `EC2_VLLM_IMAGE=vllm/vllm-openai@sha256:<digest>` | `:nightly` is mutable and ≥4 digests are already in this study's logs (§1.4). Highest-value single change | **Zero throughput cost.** Costs vigilance: someone must bump the digest deliberately |
| 2 | **Pin the checkpoint**: pass `--revision <commit-sha>` and record the resolved SHA | No revision pin today (§1.6); the S3 mirror can serve different bytes than HF. Mechanism #1 | **Zero throughput cost.** One spec field per model |
| 3 | `--seed 0` on the server | Fixes engine-level RNG, not just per-request sampling | Zero |
| 4 | `--gpu-memory-utilization 0.85` (explicit) | Makes `num_gpu_blocks` a function of the spec, not of free VRAM at profiling time (mechanism #5) | Small — slightly less KV headroom than the 0.90 default |
| 5 | Pin `VLLM_ATTENTION_BACKEND` explicitly | Removes autoselection as a per-launch variable (mechanism #4) | Zero to small, depending on whether the pinned backend is the one the heuristic would have chosen |
| 6 | `--enforce-eager` | Removes CUDA-graph capture/padding as a variable | **Real: typically 10–30% decode throughput on small models.** [UNVERIFIED for this build — measure before adopting fleet-wide] |
| 7 | `--max-num-seqs 1` + `EC2_MAX_PARALLEL_REQUESTS=1` | Removes batch composition from reduction order | **Severe: this is the expensive one.** At fan-out 4→1 expect roughly 3–4× wall-clock on a generation-bound lane. A 14-hour lane becomes multi-day |
| 8 | Prefix caching **off** | Removes cache-hit/miss as a source of path variation — and stops the same-box baseline flattering itself (§1.1) | **Large for this study specifically:** `ec2.py:268` notes each induction quiz reuses one long prefix across 9 questions and each Lean theorem reuses its context across 4 rungs. Turning it off re-prefills every one of those. Expect a substantial multiple on prompt-bound lanes |
| 9 | A batch-invariant kernel mode, if this build has one | Would make #7 unnecessary — batch-invariant kernels give identical results regardless of what else is in flight | **[UNVERIFIED — I do not know whether this build exposes such a mode.]** Check the build for a batch-invariance env flag before committing to #7; it is strictly better if present. Historically such modes cost throughput too |
| 10 | Streaming transport for long-generation lanes | Not determinism, but prevents the delivery fault from turning delivered generations into empty rows that *look* like divergence (§1.3) | Already implemented and opt-in per lane (`50ea57f5`); off by default so it does not split the transport under collected data |

**Recommended tiering — do not adopt all ten fleet-wide.**

- **Tier 1, adopt now, zero throughput cost: #1, #2, #3, #4, #5.** These are pins
  and recordings. They cost nothing per token and they remove the top two ranked
  mechanisms outright. There is no argument against them.
- **Tier 2, adopt only for a lane whose purpose is a determinism claim: #6, #7,
  #8.** They are correct and they are expensive. Applying them to the whole study
  would multiply its cost for a property the study does not need (§7).
- **#9 first if it exists** — it would make Tier 2 nearly free.
- **#10 per lane, on evidence of the fault.**

**[ADOPTED 2026-08-18 — user directive: "make sure all configurations for all
models are deterministic". The tiering above is now implemented as the DEFAULT
serving configuration, in the same commit that carries this note.]**

- **#1** `EC2_VLLM_IMAGE`'s default is digest-pinned to the build the §3 hinge
  certified (`0.27.2rc1.dev122+g8efa13b70`; Docker Hub tag
  `nightly-8efa13b700f1836657699cae2503dc2feab27fa0`, digest
  `sha256:26354b5efac552a9a0ac8e46beb16dde7490b14486c9bb7bd6b818f54d0e93f7`).
  The 88-char digest ref did not fit EC2's 16 KB user-data cap — raw
  headroom under real inputs was 7 bytes before the pin, and the digest ref
  put the render 57 bytes over — so user-data is now
  **gzip-compressed at provision time** (cloud-init auto-detects gzip; the cap
  now binds on compressed bytes — ~10.6 KB of headroom at adoption, **9,025
  bytes (~8.8 KB) after the §5 fingerprint additions**, floor-guarded at 6 KB
  by the headroom canary test). One disclosed exception to the dev122 pin:
  `run_fleet` keeps `deepseek-v4-flash`/`-pro` on the v0.27.1 build (digest
  `0e1ee527…`) for SM90 serving correctness — digest-pinned, never
  hinge-certified. Both notebook
  `keys.env` files were repointed at the digest as well, since their env value
  overrides the code default.
- **#2** every deploy spec pins `--revision` AND `--tokenizer-revision` to the
  repo's main-branch SHA resolved 2026-08-18. Belt-and-braces: at the pinned
  build `tokenizer_revision` INHERITS `--revision` when unset
  (`vllm/config/model.py:542`), so the second flag is redundant today —
  pinning both makes the pin independent of that inheritance behavior. Caveat: the study never recorded
  HF revisions, so these pins codify today's branch tips, not (provably) the
  study's bytes — §1.6 remains unrecoverable.
- **#3/#6/#7/#8** the full hinge-certified bundle
  (`--no-enable-prefix-caching --max-num-seqs 1 --enforce-eager --seed 0`,
  byte-identical to `scripts/hinge_probe.py DET_ARGS`) is appended to every
  spec's `vllm_args`; `--enable-prefix-caching` is removed everywhere,
  including the qwen2.5-1.5b canary. The Tier-2 throughput cost is accepted by
  the directive. Flag-level attribution was deliberately not separated (§3):
  relaxing any single flag requires a fresh hinge-style certification.
  **[Corrected 2026-08-21 — scope of the certification.]** "Hinge-certified"
  means certified at **tp=1 on a single L40S**: both hinge models ran on
  `g6e.4xlarge` (one GPU, dense), the only arms ever run, so multi-GPU
  all-reduce reduction order was never exercised. At HEAD, **18 of 22 deploy
  specs default to tp≥4** (9 at tp=4, 9 at tp=8), including every MoE lane
  (`qwen3.5-397b-a17b`, `k-exaone-236b-a23b`, `nemotron-3-super-120b-a12b`,
  `deepseek-v4-pro`). Determinism under the bundle is **UNCERTIFIED** for those
  18 specs; a tp=8 hinge arm is the outstanding certification.
  **[MEASURED 2026-08-21 — tp=4 CERTIFIED; scope narrows to the 9 tp=8 specs.]**
  A tp=4 hinge arm ran on one `g6e.12xlarge` (4× L40S, PCIe): both hinge models
  scored **8/8 byte-identical** across two same-process passes under the bundle
  (`ministral-3-3b` and `nemotron-3-nano-4b`; same build dev122, same image
  digest, same pins, gmu 0.92; prefix-cache counters 0/0 before and after both
  passes, so not cache replay; a stock-config control on the same box diverged
  on every as-drawn row, 3/3). The uncertified set is now the **9 tp=8 specs**
  (every MoE lane among them); that arm needs 8× GPUs with NVLink and remains
  outstanding, and the certification is scoped to this build's default
  all-reduce path (`--disable-custom-all-reduce`, both deepseek specs, is
  unexercised; both probe models are small dense — no expert parallelism).
  **New pooling boundary, measured:** all 8 rows differ in output length
  between the tp=1 and tp=4 det runs on both models — tensor parallelism
  changes generated bytes exactly as the stock/det config change does, and
  `derive_tp` makes tp a function of the landed box, so a lane spanning 1-GPU
  and 4-GPU instances is config-incomparable within itself. Data:
  `notebooks/deduction/results/tp4hinge_*.json` + `TP4HINGE_SUMMARY.txt`.
  **[MEASURED 2026-08-21 — tp=8 CERTIFIED on the dense probe, custom all-reduce
  ACTIVE.]** A tp=8 arm ran on one `p5.48xlarge` (8× H100 80GB,
  NVLink/NVSwitch — the topology the nine tp=8 specs actually use):
  `ministral-3-3b` under the bundle scored **8/8 byte-identical** across two
  same-process passes at tp=8 (8 `Worker_TP*` ranks confirmed via /status;
  `disable_custom_all_reduce=False` with the fused `allreduce_rms` kernel
  enabled in the serve log — the hand-written NVLink all-reduce that no PCIe
  arm could ever exercise; same build dev122 / image digest / pins as every
  prior arm). The stock control collected 0 rows (deadline-cut before its
  first prompt returned; the tp=1 and tp=4 stock divergences stand as the
  positive controls). Cross-tp: tp=4-det vs tp=8-det agree on **0/8** SHAs —
  but GPU model changed with tp (L40S → H100), so this is a cross-CONFIG
  fact, consistent with (not proof of) tp-changes-bytes. Residual: **MoE at
  tp=8 remains the one unexercised case** (TP-sharded expert routing on a
  120B+ model; ~$60-80 more on p5-class, out of the approved cap), and
  `--disable-custom-all-reduce` (both deepseek specs) is still untested.
  Data: `notebooks/deduction/results/tp8hinge_ministral-3-3b.json`,
  `scripts/tp8_hinge_probe.py`. Two further
  recipe rows are unaddressed by this adoption: **#9** (a batch-invariant
  kernel mode, which Appendix B still lists as [UNVERIFIED] and which would
  retire the expensive `--max-num-seqs 1`) and **#10** (streaming; the one
  post-adoption sidecar records `stream: false`). Recipe #6's 10–30%
  throughput cost also remains unmeasured on this hardware while now a
  fleet-wide default.
- **#4** `--gpu-memory-utilization` is explicit on every spec (0.92 where it
  was implicit — vLLM's default AT THE PINNED BUILD, `vllm/config/cache.py:69`,
  and the value the hinge det arms actually resolved to; deepseek-v4-pro
  keeps 0.93, and k-exaone's explicit 0.92 coincides with the default).
- **#5** the attention backend stays UNPINNED per model (except the two
  DeepSeek V4 specs, which already pinned `FLASHMLA_SPARSE_DSV4` for serving
  correctness), deliberately: it was
  never recorded, so any pin today would be a guess; with the image
  digest-pinned and each lane's instance type fixed, autoselection is a pure
  function of pinned inputs. Recording landed 2026-08-18 (best-effort
  log-tail mining, `attention_backend_log` in `server_config`); an explicit
  per-model pin can now be grounded in recorded selections when wanted.
- Client-side `EC2_MAX_PARALLEL_REQUESTS` is untouched: with
  `--max-num-seqs 1` the server serializes compute, and with caching off and
  eager mode each request's computation is isolated, so client arrival order
  cannot change a request's own tokens (the §3 det arms ran sequentially;
  concurrent clients only overlap HTTP wait).
- **Comparability guard:** stock↔det cross-config agreement is 0/8 (§3).
  Nothing generated under the new default may be pooled with the
  family-ladder study's stock-config results.
- **Live-validated 2026-08-18:** the qwen2.5-1.5b lifecycle canary ran the
  full path — gzip user-data booted a g6.2xlarge in 161.8 s (cloud-init
  gunzipped it; the control agent came up), the digest-pinned image served
  under the det bundle + revision pin, a seeded 4-question quiz scored 4/4,
  §5 fields all populated (`/version` = the certified dev122 build), clean
  teardown, and a sweep across all three regions showing zero RUNNING
  instances (one pre-existing STOPPED `verify-lean` box remains in
  us-west-2, deliberately untouched).


---

## 5. What to record so this is diagnosable next time [IMPLEMENTED 2026-08-18]

> **STATUS: implemented and live-verified — with one gap caught by
> adversarial review 2026-08-18 and closed the same day.** Eight of the nine
> fields were captured at the canary; the ninth (the attention backend) was
> NOT — the cache-config metric carries no backend label — and is now mined
> best-effort from the container log tail (`attention_backend_log`; startup
> lines can scroll off a long-serving box's tail, so call `server_config`
> right after serve). **[Corrected 2026-08-21: `attention_backend_log` is
> code-landed but NEVER OBSERVED.]** The field appears in **zero stored data
> files** — a grep for `attention_backend_log` across `notebooks/` returns only
> this document, and the flip run's own `server_config.yaml` omits it entirely.
> Treat the ninth field as implemented-but-unconfirmed until a real lane records
> it populated. Relatedly, the canary's own machine-readable `server_config` was
> never persisted as a tracked artifact: the sole evidence record,
> `.claude/smokes/gzip_det_canary_proof.py`, is untracked prose and asserts
> "`server_config()` populated all fields", which contradicts this section's own
> eight-of-nine. The eight-of-nine statement is the accurate one.
>
> The rest: client-side in `server_config()` (`/version`, the raw
> `cache_config_info` metrics line, the actually-sent vllm_args/tp/max_model_len
> stashed at serve time, client parallelism + streaming flags) and box-side via
> a `fingerprint` object on the control agent's `/status` (docker RepoDigests,
> nvidia-smi observation, HF snapshot dirs, safetensors index+sizes digest).
> Live-verified by the 2026-08-18 gzip canary: the box itself reported
> `vllm_version 0.27.2rc1.dev122+g8efa13b70` (the §3-certified build),
> RepoDigests matching the pinned digest exactly, `enable_prefix_caching="False"`
> and `gpu_memory_utilization="0.92"` in its own cache_config metric — the
> determinism default demonstrably active on a real box.

This is the highest-value item in the document relative to its cost, and the one
thing that is **unrecoverable retroactively**. The reason §0 is a two-regime
mystery rather than a solved problem is that nobody wrote down what differed
between the boxes — and now those boxes are terminated.

`server_config()` (`ec2.py:631-680`) currently records: `instance_type`, `gpu`,
`tp`, `region`, `availability_zone`, `instance_id`, `vllm_image`, `hf_model_id`.

Two of those are weaker than they look: **`gpu` is a static table lookup**
(`_INSTANCE_GPU_NAMES[itype.split(".")[0]]`), not an observation of the box; and
**`vllm_image` is the tag string** `EC2_VLLM_IMAGE`, which for this study is the
literal word `nightly`.

Add, all captured **inside** the `serve_model` block on the box that serves:

| field | source on the box | why it is load-bearing |
|---|---|---|
| `vllm_image_digest` | `docker inspect --format '{{index .RepoDigests 0}}' <image>` | Settles mechanism #2. Already proven capturable — some logs have it by accident (§1.4) |
| `vllm_version` | `GET /version` on the vLLM server | Cheap corroboration; the inventory relied on this and it was the only image evidence that existed |
| `hf_revision` | resolved commit SHA of the loaded snapshot (`refs/main` in the HF cache dir) | **Settles mechanism #1 — the discriminator between "different weights" and "different kernels", which currently fit the §0 data equally well** |
| `weights_digest` | hash of the safetensors index + sizes (cheap; not a full re-read) | Catches an S3-mirror/HF divergence that a matching revision would hide |
| `nvidia_smi` | `nvidia-smi --query-gpu=name,uuid,driver_version,memory.total,ecc.mode.current --format=csv` | Replaces the static GPU table with an observation; would have caught `p5e`/`p5en` (§1.5) |
| `vllm_args` | the actual argv the container was launched with | Today the *spec* is recorded but not the launched command; a spec edit mid-study is invisible |
| `num_gpu_blocks` / attention backend | vLLM's own startup log lines | Mechanisms #4, #5, and free — vLLM already prints them |
| `max_parallel_requests` | `EC2_MAX_PARALLEL_REQUESTS` at call time | Mechanism #6; distinguishes probe-regime from lane-regime |
| `stream` | whether the lane used the streaming transport | §1.3; the transport is now per-lane opt-in, so it varies |

**Where each is written.** `server_config()` is already stamped onto every stored
replicate (`Marks.server_config` via `ReplicateHarness.run_replicates`) and written
as the deduction `server_config.yaml` sidecar — so **extending that one function
propagates everywhere with no other change.** Keep its "never raises" contract
(`ec2.py` Notes: *provenance is a passenger*): a missing digest must not crash a
lane.

Per-request `seed` is already recorded implicitly (it is the replicate address) and
needs nothing.

**Cost: a handful of `docker inspect` / `nvidia-smi` calls once per serve, i.e.
seconds per box-hours-long lane. There is no throughput argument against this.**

---

## 6. The residual noise term [PROPOSED]

### 6.1 Do not report byte-agreement as the noise term

The inventory (line 121-122) proposes the write-up carry "0/8 agreement across
processes, 8/8 within one." **That number overstates the problem and answers the
wrong question.** Byte-identity is not what the study measures. Two processes can
agree on 0/8 bytes and score identically on every cell — and by §0 the true
cross-process byte-agreement is anyway bimodal, so a single figure misrepresents
it.

The paper needs a **score-level** term: *given the same cells, how much does the
headline metric move when the serving process changes?*

### 6.2 The measurement [MEASURED 2026-08-18 — flip rate 9.5%, CI [5.8%, 14.4%]; ±2.1 pts is the flip-RATE SE at n=200, NOT pass@1 noise — lane term ≈±1.1 pt, see the correction in the box]

> **[Corrected 2026-08-21 — header relabel.]** This heading previously read
> "±2.1 pts on pass@1". That is a mislabel with a traceable origin:
> `flip_report.json`'s field is literally named `pass_at_1_se` and equals
> sqrt(0.095 × 0.905 / 200) = 0.02073 — the 1-SE width of the flip **RATE**
> estimate at n=200. The lane-level process-swap quantity is roughly half that;
> see the corrected paragraph in the box below. The same mislabel stands
> uncorrected in commit `48c08fb8`'s subject line, which is not editable here.

> **Run as designed below with two disclosed deviations**: n=200 `Random(0)`
> cells from nemotron-3-nano-4b's 711-cell measurable Mathlib population,
> re-generated on one fresh box (~3 h, ≈$5 — under the $10-17 estimate) under
> the stock SAMPLING config (prefix caching on, no determinism bundle) —
> both sides graded by today's verifier. Deviation 1: the box is a
> **g6e.2xlarge in us-west-2a** — every g6e.4xlarge and 8xlarge AZ was dry —
> while the study lane ran a g6e.4xlarge in us-east-2b (both exactly one
> L40S, enforced by the GPU pin). Deviation 2: the rerun pins the image
> digest and `--revision`, which the study's `:nightly`-era box did not, and
> the study's own build/revision are unrecoverable (§1.4/§1.6) — so the 9.5%
> **upper-bounds the pure process term** (it may include build/weights
> drift, and instance-size/region are crossed with it).
> **b = 6 (orig pass → rerun fail), c = 13 (orig fail → rerun pass), 19/200
> discordant.** The b-vs-c asymmetry is not significant (two-sided
> McNemar-binomial p ≈ 0.17). **Verifier drift: 200/200 exact agreement**
> between the re-verified originals and the study's stored verdicts — every
> flip is generation, not grading (and this doubles as a 200-cell
> comparability certificate for the same-day DojoInit recovery, on top of
> its 30/30 control gate).
> **[Corrected 2026-08-21 — the certificate is scoped to Mathlib and certifies
> no std cell.]** The §6.2 flip sample is Mathlib-ONLY by construction
> (`flip_probe.py` `measurable_cell_keys` excludes `.lake/packages/std/`;
> population 711, all 337 flip-run rows Mathlib), and the 30 controls in
> `controls_report.json` are Mathlib theorems whose intersection with the 45
> recovered std theorems is **zero**. The DojoInit recovery grades **std** cells
> (151/151 std paths per lane). So neither gate compares a single std-cell
> verdict, and this is a **verifier-environment check on Mathlib cells**, not a
> certificate for the recovered class. On std cells the recovery is
> **reachability-certified** (17/17 `.ast.json` resolve, 45/45 ground-truth
> sanity replays succeed) but **not verdict-certified** — and verdict
> certification there is **impossible, not missing**, since all 151 std study
> rows per lane were graded `replay_failed`, so no baseline verdict exists to
> compare against. Separately, the recovery's `report.json` records no grading
> instance metadata (keys: `lanes`, `recovery`, `unrecovered_cells`,
> `n_unrecovered`), so the "same-day" link between the two verifier environments
> is asserted in prose and cannot be checked even for Mathlib cells.
>
> The write-up sentence this section prescribes,
> filled in: *"The per-cell flip probability across processes was measured
> at 9.5% (95% CI [5.8%, 14.4%], n = 200, one lane)."* The ±2.1-point
> figure is the 1-SE width of the flip-RATE estimate at n=200 (the report's
> own field and caveat say exactly this; cells share theorems, so it is
> likely too narrow) — the lane-level quantity is smaller: ≈**±1.2 points
> of process-swap SD on a 712-cell lane's pass@1**.
> **[Corrected 2026-08-21 — the lane term, measured, is ±1.09–1.16 pt, and it
> is a DIFFERENCE SD.]** Two refinements. (a) *Magnitude:* the iid value is
> sqrt(0.095/712) = 0.011546 = **1.155 pt**; multiplying by the measured signed
> design effect **deff = Σ Sᵢ²/#flips = 17/19 = 0.895** (block-bootstrap 95%
> [0.684, 1.000], P(deff>1) = 0.000; within-theorem signed correlation
> ρ = −0.139) gives **1.093 pt**, and the worst case of all-concordant blocks
> (deff 1.105) gives 1.214 pt. Quote **≈±1.1 pt (range 1.09–1.16)**; the
> published "±1.2" over-states by about 0.06 pt. Note the *signed* design
> effect is the one that enters pass@1 variance and it is **below** 1, unlike
> the indicator-level deff of 1.150 (ICC ρ = +0.327, m_adj = 1.458), which does
> not. (b) *How to propagate it:* sqrt(p_flip/N) is the SD of (c−b)/N, and
> (c−b)/N is identically p_rerun − p_orig (from a=11, b=6, c=13, d=170:
> 0.1200 − 0.0850 = +0.0350 = (13−6)/200) — so this is already a **two-process
> difference** SD. The per-run σ is 0.011546/√2 = **0.82 pt**. A contrast
> between two independently-served lanes therefore adds (0.011546)² **once**,
> not twice; adding it twice doubles the variance and, on the deduction ladder,
> costs three Holm rejections on the 707 pool (10/21 instead of 13/21).
>
> And the byte-level
> datum for this sample: **178/200 (89%) of the re-generations differ in
> text** while 9.5% flip score — §6.1's "byte agreement is the wrong
> metric", now quantitative.
> [Corrected 2026-08-21: label the 178/200 precisely — it is the extracted
> **candidate proof** differing. The raw response differs in **191/200 (95.5%)**
> and the (reasoning_content, raw_response) pair in **199/200 (99.5%)**, which
> strengthens §6.1's point rather than weakening it. None of these figures is
> stored in `flip_report.json` and no such field exists in
> `scripts/flip_probe.py`: they are reconstructible from the paired rows but
> were never recorded.]
> Driver: `scripts/flip_probe.py` (sample sha `bf22495e…`); data:
> `s3://…/deduction/runs/flip_nemotron-3-nano-4b/` and
> `notebooks/deduction/results/runs/flip_nemotron-3-nano-4b/flip_report.json`.
>
> **Ops lesson (one wasted verification pass):** a dead `GITHUB_ACCESS_TOKEN`
> in `keys.env` (GitHub answers bad auth with 401/404) made LeanDojo's
> GitHub lookups fail and graded all 400 legs `exception` — producing a
> degenerate d=200 "0 flips" table that LOOKED like the headline result.
> Caught because its verifier-drift check read 0/200 against the recovery's
> fresh 30/30. Unset the token (anonymous API works). Rule: a paired-zeros
> result whose drift check is ALSO zero is a verifier fault, not a finding.

### 6.2 The measurement [as pre-registered]

**Design.** Take one deduction lane with a clean single-process history —
`nemotron-3-nano-4b` is the only candidate (inventory: "the only lane in the study
whose deduction cells all come from a single serving process"). Draw a random
sample of **n = 200 of its 944 cells**, re-run exactly those on **one fresh box**,
grade both sets through the same verification pass, and compare per cell.

**Statistic.** The paired discordance rate (McNemar b + c over n), reported as the
**per-cell flip probability**, plus the resulting standard error on a lane's
pass@1. With n = 200, a discordance rate of ~10% is estimated to about ±2 points —
enough to state a bound. The study already owns the machinery
(`notebooks/lean/power_analysis.py`: paired McNemar + block-bootstrap over theorem
blocks).

**Cost.** One `g6e.4xlarge` for roughly 6–10 h at $1.39–1.71/hr ≈ **$10–17**, no
new code beyond a cell-subset filter. [PROPOSED — not run.]

**What the write-up should then carry:** *"Generation is reproducible within a
serving process and not guaranteed across processes; a lane's cells come from one
or more processes depending on spot interruptions. The per-cell flip probability
across processes was measured at X% (n = 200, one model), contributing ±Y points
to a lane's pass@1. This is noise, not bias: process identity is assigned by spot
capacity and does not correlate with the model axis."*

Until that measurement exists, the write-up should state the **qualitative** claim
with its evidence — that cross-process byte-reproducibility is not guaranteed, that
agreement was measured as bimodal (8/8 in one pairing, 0/8 in two, n = 8 prompts,
one model) — and explicitly say the score-level term has not been quantified. Do
not put a number on it that has not been measured.

### 6.3 A free, biased lower bound that already exists

> **[FIRST MEASUREMENT RETRACTED; REMEASURED 2026-08-18 — 3/74 flips
> (4.1%), exact 95% CI [0.8%, 11.4%].]** The initially published "0/74
> flips, CI [0, 4.9%]" was **VOID, not conservative**: the driver omitted
> the `kind:"cell"` row field, `lean_verify_rows.group_unverified` silently
> skipped every row, and the zero was arithmetically forced from
> `unverified` sentinels. Caught by adversarial verification (the detector:
> a paired-zeros table whose companion drift check ALSO read zero — that
> combination is a verifier fault, never a finding), fixed (`kind` guard +
> a hard no-op assertion that refuses to tabulate unverified rows), and
> re-run. The real result: **3/74 pairs flip**, all fail→pass, all Mathlib
> (69 Mathlib + 5 std pairs; the 63/6/5 lane accounting reproduced). The
> sample's structure, also now measured: in ALL 74 pairs the FIRST
> surviving attempt returned empty text, and no pair holds two distinct
> non-empty generations — so this sample carries **no token-level
> nondeterminism signal at all**; it measures "does a resample of an
> empty-return cell succeed", and its 4.1% UNDER-detects relative to
> §6.2's unbiased 9.5%, consistent with the selection event (an empty
> return) marking hard cells. The selected-on-outcome caveat below stands
> with its direction now measured: under-estimate, not the argued
> over-estimate. `scripts/flip_free_bound.py`; results in
> `notebooks/deduction/results/flip_free_bound_2026-08-18.json`.
>
> **[Corrected 2026-08-21 — the DIRECTION CLAIM IS RETRACTED. The bias
> direction returns to [UNVERIFIED].]** The two clauses immediately above are
> mutually exclusive: a sample stated to carry *no token-level nondeterminism
> signal at all* cannot be compared, in either direction, against §6.2's
> measurement *of* token-level nondeterminism. That is a validity defect, not a
> power problem, so no increase in n repairs it. The numbers agree: the 2×2
> [[3, 71], [19, 181]] gives **Fisher exact two-sided p = 0.209** (χ² p = 0.222),
> and against a fixed 9.5% the one-sided binomial gives **p = 0.070** — n.s. on
> the most generous framing; §6.3's own Clopper-Pearson CI [0.8%, 11.4%]
> contains 9.5%. And the estimands differ: **74 of 74** pairs had an empty first
> surviving attempt, **0** pairs hold two non-empty generations, and all 3 flips
> are `['lean_error','success']` with `n_nonempty_attempts = 1`. What survives:
> §6.3 re-measures at **3/74 (4.1%, exact 95% CI [0.8%, 11.4%])**, all fail→pass,
> and it measures *whether a resample of an empty-return cell succeeds*. No
> comparison with §6.2 in either direction is supportable, and the original
> caveat below — **[UNVERIFIED — bias direction argued, not measured]** — is
> restored as the authoritative statement. Commit `48c08fb8`'s "confirms
> outcome-selection UNDER-detects" is retracted on the same grounds.

The resampling bug left **74 cells with more than one surviving attempt**
(`ministral-3-3b` 63, `qwen3.5-27b` 6, `gemma-4-31b` 5 — inventory §"pass@1
verification"). Those are **paired draws of the same cell from different serving
processes, already collected, at zero marginal cost.** One `ministral-3-3b` cell has
proof lengths `[0, 0, 0, 65]`.

**Caveat that prevents using it as the headline:** the sample is selected on *cell
outcome* — specifically, "the first attempt was empty" — so the flip rate it yields
is **not an unbiased estimate**. Conditioning on one arm of the pair taking a
particular value invites regression to the mean on the second draw, which argues the
figure is an **over**-estimate; that direction is reasoned, not measured
**[UNVERIFIED — bias direction argued, not measured]**. Treat it as a free sanity
check on §6.2's design, not as a bound to quote. Compute it, report it with this
caveat attached, and do not let it substitute for the measurement.

---

## 7. What NOT to do, and why

### 7.1 Do not re-collect the twenty multi-box lanes

The argument, which **survives the §0 correction**:

1. **Per-process variation is noise, not bias.** Every lane runs on its own boxes
   by construction, and the study compares models *across* lanes. The process a
   cell was generated on is assigned by spot capacity — which is independent of
   the model axis. A term that does not correlate with the comparison axis inflates
   variance; it does not move a point estimate.
   **[Corrected 2026-08-21 — this premise is WITHDRAWN as stated.]** Spot
   capacity is independent of model *size*, not of model *identity*. Process
   identity is aliased with lane identity: each lane draws one process
   realization, so that lane's realized offset is indistinguishable from bias in
   its own point estimate and enters every between-model contrast. §7.2 below
   concedes the mechanism without correcting this premise. The §6.2 recompute
   bounds the per-pair mean shift at **+3.5 pts, 95% CI [−0.74, +7.74]**.
   §7.1's conclusion survives on premises 2 and 3 alone.
2. **No re-run can restore original outputs anyway.** A re-run necessarily happens
   in a new process. It can only make a lane internally homogeneous *going forward*.
3. **The cost is absurd relative to the gain.** Twenty-plus lanes, weeks of compute,
   to remove a term that does not bias the comparison.
4. **§0 makes the case stronger, not weaker.** If cross-process agreement were
   uniformly 0/8, one might worry that "process" is a large latent factor. The 8/8
   pairing shows processes can be *exactly* equivalent — the space of regimes is
   small and discrete, not a continuum of unique per-box behaviours.
   **[Corrected 2026-08-21 — premise 4 is WITHDRAWN; it points the other way.]**
   §7.2, eighteen lines below, uses the identical fact as the live worry
   ("Bimodality makes that assumption testable… a lane's expected score would
   depend on how many boxes it used"), and §7.2 is right. Discreteness makes
   within-lane averaging *worse*: a single-box lane sits entirely in one regime
   and its offset never averages down, whereas a continuum of small per-box
   perturbations would average toward zero. Withdrawn, not deleted, so the
   original reasoning stays visible. **§7.1's conclusion — do not re-collect —
   survives on premises 2 and 3 alone.** Note also that premise 3 prices only
   re-collect-vs-accept; the option that would actually shrink the term
   (serving each lane from several processes and averaging) is priced nowhere
   in §7.

### 7.2 The one gap in that argument, stated honestly

Noise-not-bias assumes the discrete regimes are **exchangeable with the same mean
score**. Bimodality makes that assumption *testable*, and it has not been tested.
If the two regimes differed systematically in mean score, then a lane's expected
score would depend on **how many boxes it used** — and box counts vary enormously
(`gemma-4-12b` ×21, `ministral-3-14b` ×48, versus single-box lanes). A lane that
sampled 48 processes would sit nearer the regime-average; a single-box lane could
sit on one regime.

I want to be precise about how much this is worth worrying about: it is a
**bounded, unmeasured caveat, not a reason to re-collect.** It requires regimes to
differ in *mean*, not merely in output; nothing observed suggests that, and the
§6.2 measurement resolves it directly for **$10–17**. **Run §6.2 before the
write-up; do not run twenty lanes.**

> **[Corrected 2026-08-21 — §6.2 RAN, and it bounds this loosely rather than
> resolving it.]** The imperative above is spent: §6.2 was measured 2026-08-18.
> What it delivers is weaker than "resolves it directly". As run it compares
> **one** study process against **one** rerun process on **one** lane; its
> mean-shift estimate is (c−b)/n = **+3.5 pts, SE 2.17, 95% CI [−0.7, +7.7]**,
> exact McNemar p = 0.167, with an **MDE at 80% power of ≈6.1 pts**. Against
> that lane's pass@1 of 8.5%, the interval admits a shift comparable to the
> whole score and several times the ≈±1.1 pt SD the analysis propagates. Even
> at infinite n the design estimates a two-process contrast, not a regime-level
> mean difference — §0 identifies at least three groups among four processes.
> Read §7.2 as: the regime-mean question **remains open**, and the bound now
> available is wider than any ladder contrast the study reports.

> **[MEASURED 2026-08-21 — n extended 200 → 311 (user-approved, $5.35 of a $20
> cap): still no significant regime-mean shift, and the bound tightens.]** A
> second, disjoint `Random(0)` draw of 200 cells from the same 711-cell
> population ran under the identical stock reconstruction (same build dev122,
> image digest, weights digest, HF revision, tp=1, seed 0 — provenance in the
> run dir); 111 of the 200 completed both generation and verification (three
> spot reclaims took the rest; the 88 losses are listed, cut by reclaim time,
> not by outcome). Pooled over 311 cells / 160 theorems: rerun-vs-original
> mean shift **+3.2 pts, cluster-bootstrap 95% CI [−0.3, +6.9]** (naive
> [−0.1, +6.5]), exact McNemar p = 0.087, b/c = 9/19; **MDE at 80% power
> ≈4.7–5.1 pts** (the ~3-pt target needed the full 400). The per-cell flip
> rate **replicates on fresh cells: 8.1%** [3.8, 14.8] vs leg 1's 9.5%,
> pooled 9.0% [5.5, 12.9] cluster; the two legs are statistically
> indistinguishable (shift difference 0.8 pt, z = 0.22). Verifier drift was
> **511/511 exact** across both legs' gates, and the drift gate paid for
> itself again: leg 2's first grading pass returned 58/58 `replay_failed`
> because `~/.elan/bin` was missing from PATH — the same
> infrastructure-masquerading-as-data class as the 2026-08-18 dead-token
> fault, caught at $0 before any box launched. Standing conclusion: shifts
> ≳7 pts are excluded; a shift of the observed +3 pts — consistently
> rerun-HIGHER in both legs — remains neither confirmed nor excluded, and is
> still a two-process contrast, not a regime-level mean. Data:
> `notebooks/deduction/results/runs/regime_mean_2026-08-21/`.

> **[FINAL 2026-08-22 — the draw COMPLETED at n=399; the shift ATTENUATED and
> the sign is process-unstable.]** The 88 reclaim-lost cells were finished
> ($3.55, box reattached mid-flight; one cell is deterministically
> unmeasurable — 2/2-reproducible `DojoCrashError` on a 110,920-char runaway
> candidate — so the full draw is 399 of 400). Pooled 399 cells / 189
> theorems: mean shift **+2.01 pt, cluster 95% CI [−1.01, +5.19]**, exact
> McNemar p = 0.243, b/c = 14/22; flip rate 9.0% [6.1, 12.3], stable across
> every extension. The estimate moved DOWN with more data (+3.5 at n=200 →
> +3.22 at n=311 → +2.01 at n=399), and MDE80 = 4.40 pt still exceeds the
> point estimate: this draw **bounds** the process term at ≈±5 pt, it does
> not establish one. Most informative single fact: the four serving-process
> strata are +3.50 / 0.00 / +4.35 / **−2.30** pt — boxes 3 and 4 are the
> same instance type in the same AZ on the same day under the same pinned
> reconstruction and differ by 6.65 pt with opposite signs (homogeneity
> Q p = 0.40, but per-stratum SEs are 3–4 pt: "undetectably different," not
> "agreeing"). Conclusion: the rerun-higher trend is NOT a stable regime
> property; §7.1's noise-not-bias stance stands, now with a measured ±5 pt
> bound and a demonstrated sign flip between nominally identical processes.
> Full-draw data: `regime_mean_report_full.json`, `by_process_full.json`,
> `REPORT_full_draw.md` in the same run dir (the n=311 report is kept as the
> interim record). Tooling defects found en route, RECORDED NOT YET FIXED:
> (a) `verify_run` cannot grade a second generation pass over a run dir
> (seeds outputs from the prior `verified_rows` but indexes pending against
> the new `all_rows` → IndexError; loud, no damage); (b) more serious,
> `resume_done_groups` marks a (theorem, k) group done if ANY cell in it has
> a verdict, so a second pass can silently leave a cell unverified — the
> full-draw run caught one such cell and verified it in isolation; (c) the
> teardown sweep scripts filter tag key `Experiment` while the harness tags
> `smolbench:experiment`, making the sweep a no-op (teardown was confirmed
> by direct instance-id describe instead).

### 7.3 Do not "fix" this by lowering temperature or dropping the seed

Temperature 0.7 with a fixed seed is the study's regime and is reproducible given
identical logits (§2). Lowering it would mask divergence rather than remove its
cause, and would change what the study measures. Dropping the seed to dodge an
error is already a standing prohibition in this project.

### 7.4 Do not treat the archived 0/8 as "the" cross-process rate

Two of three measured pairings gave 0/8; the third gave 8/8 (§0). Any statement of
the form "vLLM never reproduces across processes" is contradicted by this study's
own archive. n = 8 prompts, one model.

### 7.5 Do not re-run `ministral-3-3b` on the current evidence

The inventory declines to re-run it, and that decision is correct — but for a
**narrower reason than stated**. The right formulation is *"not reproducible under
the one configuration tested, and one of its eight baseline rows was a transport
fault"* — not *"the model is nondeterministic, so nothing can be measured."* §3
arm C settles it for a few dollars. **Do that before re-running anything.**

> **[Corrected 2026-08-21 — §3 arm C RAN on 2026-08-16; this section's premise
> is superseded.]** Arm C returned **8/8**: `ministral-3-3b` **is** reproducible
> under the determinism config, and its archived 0/8 was the *configuration*,
> not the model. So the standing reason not to re-collect it is no longer
> unmeasurability — it is **comparability**: cross-config agreement is **0/8 on
> both hinge models** (§3), so anything re-collected under the determinism
> default cannot be pooled with the twenty stock-config lanes. (The grounds text
> committed at `d571f39f` edited only `CONTAMINATION_INVENTORY_2026-08-15.md`
> and was never propagated into this document; that omission is closed here.)

---

## 8. Summary of changes this document asks the inventory to make

| inventory location | change |
|---|---|
| lines 40–41, "reproducible within one process and not across processes" | **Retract the second clause.** Cross-process agreement reaches 8/8 in one measured pairing, across two *different instance types in different regions* (§0). Four processes fall into **three** groups, not two |
| lines 43–44, "both reported `vllm 0.27.2rc1.dev110+gacb0f1dcd`" | **Do not read as covering the probe.** Probe-1's own log records `dev77`. Five builds spanning `0.26.1`→`0.27.2` served this study (§1.4) |
| lines 29–30 and line 86, "`ministral-3-3b`... nothing can be measured for it" | **Narrow.** Not reproducible *under the one configuration tested*; 1 of its 8 baseline rows is a transport fault (§1.3). §3 arm C tests it for <$10 — [Corrected 2026-08-21: arm C RAN 2026-08-16 and returned **8/8**, so this row is superseded: the model IS reproducible under the determinism config, and the standing reason not to re-collect is 0/8 cross-config incomparability. See §7.5] |
| line 25, "this model IS deterministic at a fixed seed" | **Add the limit.** With prefix caching on and identical prompts, the second pass replays the first pass's KV. The baseline may measure the cache (§1.1) — [Corrected 2026-08-21: superseded by §3 arm A, which read 0 cache queries / 0 hits and still scored 8/8. The "may be measuring the cache" limit is RESOLVED (it was not), so this row should no longer be asked of the inventory. The residual scope caveat is different: arm A changed four flags together and ran at tp=1 on one L40S] |
| lines 121–122, "state this as a known noise term with its measured size (0/8 / 8/8)" | **Replace with a score-level term** (§6). Byte-agreement overstates the problem and is bimodal anyway |
| line 241, "unpinned nightly digest drift remains a residual" | **Upgrade from residual to confirmed**, and note it is partly recoverable: 4 distinct digests are in the logs, two within one lane (§1.4) |

---

## Appendix A: the four-process agreement matrix (§0)

Both archived reports record a per-prompt digest for *each side* of their
comparison, and `cross_size.diffs` lists every prompt when agreement is 0/8 — so
between the two files there are digests for four distinct serving processes over
the same eight prompts. Reproduces §0's table:

```python
import json, itertools, pathlib
d = pathlib.Path("notebooks/deduction/results/hwprobe_archive")
p1 = json.load(open(d / "nemotron-3-nano-4b_4xl-vs-2xl.json"))["cross_size"]["diffs"]
p2 = json.load(open(d / "nemotron-3-nano-4b_4xl-vs-4xl-BOX2BOX.json"))["cross_size"]["diffs"]
proc = {"P1A i-09ec 4xl e2b": {r["prompt"]: r["sha_a"] for r in p1},
        "P1B i-039b 2xl w2a": {r["prompt"]: r["sha_b"] for r in p1},
        "P2A i-0d26 4xl e2b": {r["prompt"]: r["sha_a"] for r in p2},
        "P2B i-0845 4xl e2b": {r["prompt"]: r["sha_b"] for r in p2}}
prompts = sorted(proc["P1A i-09ec 4xl e2b"])
for a, b in itertools.combinations(proc, 2):
    n = sum(proc[a][p] == proc[b][p] for p in prompts)
    print(f"{a:22s} vs {b:22s} {n}/8")
```

The prompt sets are identical across both reports because `load_prompts` sorts and
strides S3 keys deterministically (`hardware_equivalence_probe.py:79-80`) — without
that, the cross-report comparison would not be licensed.

**Caveat on scope.** This is one model, one prompt set, n=8, four processes. It is
enough to *refute* "never reproducible across processes" — a single 8/8 pairing
does that — and not enough to characterise the regime structure. Sizing that is
§3's job.

---

## Appendix B: verification status of every load-bearing claim

**[VERIFIED] — checked in this session, with the command or file cited inline**
- The 8/8 cross-process SHA match and its instance IDs/types/regions/timestamps (§0)
- The 1/8 second-regime match on the shortest output (§0) [Corrected 2026-08-21:
  the 1/8 match is VERIFIED; "on the shortest output" is not — that prompt is the
  SECOND-shortest and the shortest one disagreed in that pairing (§0)]
- The probe is strictly sequential and never calls `evaluate()`; concurrency was 1
  in all four passes (§1.6)
- `--enable-prefix-caching` on every roster model; no `--seed`, `--max-num-seqs`,
  `--enforce-eager`, `--gpu-memory-utilization`, or `--revision` anywhere (§1.6)
  **[VERIFIED as of 2026-08-16; every clause reversed by `91cac390` on
  2026-08-18.** At HEAD the spec audit finds 0/22 specs with
  `--enable-prefix-caching` and 22/22 carrying `--revision`,
  `--tokenizer-revision`, an explicit `--gpu-memory-utilization`, `--seed 0`,
  `--max-num-seqs 1` and `--enforce-eager`. §1.6's knob table describes the
  study-era configuration, not the current one.]
- Per-request `seed` is sent (`openai_compat.py:659`) (§1.6)
- `EC2_MAX_PARALLEL_REQUESTS` default 8; lanes use 4 or 8 (§1.6)
- Four distinct image digests in the logs, two within `deepseek-v4-flash` (§1.4)
- `EC2_REQUIRE_GPU` checks instance type against static tables, never `nvidia-smi` (§1.5)
- `server_config()`'s exact recorded field list (§5)
- The transport-fault commits postdate the probe; `len_a: 1` is the separator
  alone, i.e. an empty response (§1.3)
- Character totals: nemotron `A1` ~344k vs ministral `A1` ~314k (§1.1 caveat)
- `g6e.4xlarge` spot price us-east-2, 2026-08-16: $1.39–$1.71/hr (§3.5)

**[UNVERIFIED] — stated as such, not asserted**
- CLI spellings `--no-enable-prefix-caching`, `--max-num-seqs`, `--enforce-eager`,
  `--seed` against build `0.27.2rc1.dev110+gacb0f1dcd`. §3.6 gives the pre-check
  **[RESOLVED 2026-08-21: all four spellings ran successfully at the §3 hinge
  (2026-08-16) and the §4 canary (2026-08-18) on build
  `0.27.2rc1.dev122+g8efa13b70` — which is the pinned build; `dev110` never was.]**
- Whether this build exposes a batch-invariant kernel mode (recipe #9)
- The `--enforce-eager` throughput cost figure (10–30%) — an order-of-magnitude
  expectation, not a measurement on this hardware
- The **direction** of the selection bias in §6.3's free 74-cell sample. The sample
  is definitely biased (selection is on cell outcome); the argument that it
  over-states the flip rate is reasoning, not measurement
  **[STILL [UNVERIFIED] as of 2026-08-21 — this row is correct and stays here.**
  §6.3's 2026-08-18 remeasurement briefly reported the direction as measured
  ("under-estimate"); that claim is retracted (see the §6.3 correction box).
  3/74 vs 19/200 is Fisher two-sided p = 0.209, one-sided binomial against a
  fixed 9.5% p = 0.070, and the two are different estimands — 74/74 first
  attempts were empty and no pair holds two non-empty generations. Neither
  direction is measured.]
- Which image digest each of the probe's four boxes ran: **not recoverable.** Their
  logs contain no digest line and the instances are terminated. This is exactly the
  gap §5 closes going forward

**[NOT DONE — as of 2026-08-16; SUPERSEDED, see the stamp below] — deliberately, per scope**
- No arm of §3 was run. No box was launched. No S3 object was written, moved or
  deleted. No study code, data or config was modified. The live `ministral-3-14b`
  re-collection (babysitter pid 203085) was not touched.

**[Corrected 2026-08-21 — the [NOT DONE] block above describes 2026-08-16 only
and is contradicted by four later sections of this same document.]** Since then:
§3 ran (both arms, 2026-08-16 21:08–23:00Z); §6.2 was MEASURED 2026-08-18 on a
fresh `g6e.2xlarge`; §4 was ADOPTED and live-validated by the qwen2.5-1.5b canary
2026-08-18; §5 was IMPLEMENTED 2026-08-18. Four boxes were launched in total (2
hinge, 1 flip, 1 canary), S3 objects were written under
`deduction/runs/flip_nemotron-3-nano-4b/`, and `ec2.py`, `agent.py.txt`,
`run_fleet.py` and both notebook `keys.env` files were modified by commits
`91cac390`, `57618f26`, `a1cf5033`, `3f6f342f` and `48c08fb8`. Appendix B is the
section a reader consults *for* status; consult each section's dated banner
instead.
