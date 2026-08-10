# Resume runbook — coprime & divisor induction studies

Last updated 2026-08-10. Branch `periodic-induction`.

**Both studies are COMPLETE and written up.** Nothing is collecting, nothing is
billing, and no box is live.

| study | replicates | write-up |
|---|---|---|
| `periodic_coprime` | 360/360 | `notebooks/COPRIME_RESULTS.md` |
| `periodic_divisor` | 360/360 | `notebooks/DIVISOR_RESULTS.md` |

This file is now a **reference**, not a resume checklist. Sections 1, 3 and 6
still apply verbatim to any future run of either study; sections 5 and 7 record
what the results mean and which traps are already paid for.

---

## 1. FIRST: check for billing instances

Do this before anything else, every time — including now, even though the last
session ended clean. Both divisor boxes (`i-0de896205a3f4c5c2`,
`i-0d74add84f68e785f`, p5.48xlarge @ us-east-2c) terminated on schedule when
their drivers finished, verified across all three regions.

One note from the 2026-08-10 relaunch worth keeping: **us-east-1 had no p5 spot
capacity in any of its six AZs.** The provisioner walked all six, fell through
to us-east-2c, and landed both boxes at $20.55/h — slightly under the recorded
us-east-1 rate. That fallthrough is configured behaviour and needs no
intervention, but it means the region a box lands in is not fixed, so a sweep
that only checks us-east-1 will miss live instances.

When a driver dies the box goes idle and its on-instance watchdog terminates it
after 30 minutes (plus a hard `shutdown -h +1440`). That backstop has fired
correctly every time so far — but verify, never assume:

```bash
set -a && . notebooks/ec2-operator.env && set +a
for r in us-east-1 us-east-2 us-west-2; do
  aws ec2 describe-instances --region $r \
    --filters "Name=instance-state-name,Values=pending,running" \
    --query 'Reservations[].Instances[].[InstanceId,InstanceType,LaunchTime,Tags[?Key==`smolbench:experiment`].Value|[0]]' \
    --output text
done
```

**If a box is still alive, relaunch rather than terminate** — the driver
reattaches and reuses its loaded checkpoint, worth ~40 minutes. Caveat learned
the hard way: a box idle for over ~30 min may terminate *during* your reattach,
and the run then dies with "went shutting-down while waiting for its agent".
Just relaunch again; it provisions fresh.

The unrelated `pruning-metrics` box in us-east-1 belongs to different work —
do not touch it.

## 2. Where the data stands

| study | replicates | gpt-oss | Nemotron-3 | Qwen3.5 |
|---|---|---|---|---|
| `periodic_coprime` | **360/360 DONE** | 30/30 | 30/30 | 30/30 |
| `periodic_divisor` | **360/360 DONE** | 30/30 | 30/30 | 30/30 |

Target is 360 = 3 models x 4 arms x 30 seeds (1776–1805). Everything is
committed; replicates resume-skip on `rep_{seed}.yaml` existence, so nothing is
re-run or re-paid for.

## 3. Resume commands

Repo root, main venv. One process per study — mandatory, since `ec2.py` freezes
its `EC2_*` constants at import, so two studies cannot share an interpreter.
Divisor's two outstanding models run on separate boxes:

```bash
set -a && . notebooks/ec2-operator.env && set +a

# Nemotron-3 leg (default tag/state)
DIVISOR_N_REPLICATES=30 DIVISOR_MODELS=nemotron3 \
  nohup .venv/bin/python notebooks/periodic_divisor/run_study.py > /tmp/dn.log 2>&1 &

# Qwen leg -- distinct tag AND state file, or it reattaches to the sibling's box
DIVISOR_N_REPLICATES=30 DIVISOR_MODELS=qwen35 \
  DIVISOR_STATE_FILE=.ec2_state_periodic_divisor_qwen.json \
  EC2_EXPERIMENT_TAG=periodic-divisor-qwen \
  nohup .venv/bin/python notebooks/periodic_divisor/run_study.py > /tmp/dq.log 2>&1 &
```

Startup derives each completion budget before provisioning (CPU only, nothing
billing). Expect:

```
qwen3.5-397b-a17b: worst prompt 36,321 tok (+8,000 reserve) -> completion budget 86,751
```

If that line does not appear, something failed before provisioning — read the
log rather than relaunching blindly.

Remaining at observed rates: Nemotron-3 ~10 replicates at ~17 min each (~3 h),
Qwen ~12 at ~15 min (~3 h), running concurrently.

## 3b. Parallelising further (optional, costs money)

**By model** — already in use above. `EC2_STATE_FILE` alone does NOT work:
`InductionExperiment` writes its configured `state_file` into that variable
(experiment.py), clobbering the shell value, and the second process then
reattaches to the first's box and swaps the served model out from under it.
Use `{COPRIME,DIVISOR}_STATE_FILE`.

**By replicate** — `{COPRIME,DIVISOR}_SHARD=index/count` runs every `count`-th
replicate starting at `index`. One process per shard, same MODELS:

```bash
for i in 0 1 2; do
  DIVISOR_N_REPLICATES=30 DIVISOR_MODELS=qwen35 DIVISOR_SHARD=$i/3 \
    nohup .venv/bin/python notebooks/periodic_divisor/run_study.py > /tmp/dq$i.log 2>&1 &
done
```

Each shard derives its own AWS tag and state file (`...-qwen35-s0of3`), so
shards cannot collide. Shards stride, so 30 over 4 splits 8/8/7/7 and the
slowest shard stays balanced. Seeds keep their identity across shards.
Unsharded runs are byte-identical to before the flag existed.

**Do not** run two processes with the same (MODELS, SHARD) — the one
combination that races on the same `rep_{seed}.yaml`. Sharding costs real
money: each extra box re-loads its checkpoint (~40 min) before useful work, so
shallow shards spend much of their life loading.

## 4. Post-collection analysis (already run for both studies)

```bash
.venv/bin/python scripts/coprime_pilot_gate.py <study>
.venv/bin/python scripts/posterior_power.py <study> --mei 0.05
```

The gate blocks on `compliance=empty` marks. **It blocks on the signature, not
the cause** — as of 2026-08-10 it prints the prompt-length range behind the
empties and the two competing explanations instead of asserting truncation.
Diagnose before acting: empties in the longest-prompt arm mean the budget is
tight; empties on the shortest prompts with the long arm clean mean the model
failed to terminate, which no budget fixes. Divisor is the second kind.

The posterior script sorts all 30 planned contrasts into DECIDED / EQUIVALENT /
UNDECIDED and quotes an R only for UNDECIDED, at a pre-specified MEI. It
deliberately reports no observed power — that is a monotone restatement of the
p-value.

## 5. What divisor found

Full write-up in `notebooks/DIVISOR_RESULTS.md`. The four things a future
session is most likely to get wrong:

1. **The opposite-ends crossover is gpt-oss-specific.** The pilot suggested it
   was a property of the task; with all three models in, it is not.
   Nemotron-3's extensional failure is broad and flat (gap −0.048), Qwen has no
   gradient at all (+0.007). Only gpt-oss crosses over (intens +0.173, extens
   −0.499).
2. **gpt-oss's intens and noise arms score identically (0.9244 both) but agree
   on only 86.7% of marks.** 104 marks flip, ~52 each way, cancelling to zero.
   The aggregate null is real; "padding is inert" is false. Any rate-only
   analysis misses this.
3. **Nemotron-3's extensional marks mix two failure modes.** 90 of 780 are
   runaway position-by-position enumerations (median 112,756 chars vs 28,482
   clean) that never conclude. Its 0.452 -> 0.655 move versus baseline is
   partly a change in failure mode, not competence.
4. **Do not leniently regrade those enumerations.** The expected answer appears
   somewhere in the text for 78 of 80 `multiple-values` marks — because an
   enumeration of positions 1–2520 contains every candidate integer by
   construction. Crediting them scores the model on its scratch work.

A large-period harmonic is EASY intensionally (2520/2520 = 1) and HARD
extensionally, so the two arms average over different difficulty profiles. Do
not report their accuracies as if they faced the same task.

**If the study is extended:** 2,520 has 48 divisors and this study used 26.
More divisors is the concrete route to de-saturating Nemotron-3 and Qwen on
the intensional arm, which 26 was not enough to trouble.

## 6. Hazards already paid for — do not rediscover

Roughly 10 hours of collection went to these. All fixed in committed code;
listed so the symptoms are recognisable.

1. **Read timeout vs a large completion budget.** A read timeout counts toward
   `EC2_MAX_CONNECTION_FAILURES`, so a long generation dies after 10 retries
   with a misleading "endpoint unreachable" on a perfectly healthy endpoint.
   Fixed by `EC2_REQUEST_TIMEOUT_SECONDS=3600` in both studies' `keys.env`.
   (A *genuine* unreachable box says the same thing — check whether requests
   were succeeding moments earlier.)
2. **Teardown deleting another run's state file** (`3da8b192`). `_clear_state`
   now only clears state it owns. Still: do not launch a study while a previous
   run of the same study is tearing down.
3. **Completion budget sized from `count()` on one seed** (`c50bb6b0`).
   `count()` excludes the server-side chat template (~1,547 tokens), and one
   seed is not the worst seed (coprime's worst extens prompt is 59,221 at seed
   1793 vs 55,526 at 1776). A budget one token too large gets a vLLM 400, which
   kills the whole run. Now derived at startup with an 8,000-token reserve —
   **do not hardcode it again.**
4. **Public IP changes after a host restart.** The security group still holds
   the old IP and every request fails to connect. Relaunching re-authorises.

## 7. Analysis caveats that outlive the runs

- **Qwen cannot fully fit the coprime task.** 10 of its 180 coprime extens
  marks are truncation (empty response AND empty reasoning: the `<think>` block
  never closed). At ~59k-token prompts it cannot reliably both reason and
  answer inside a 131,072 window. Report as a finding about the model at that
  prompt length, not a misconfiguration.
- **Budget seam in coprime's Qwen arm.** Replicates before a mid-study host
  restart used 65,536; the rest used the derived 63,851. Its invalid rate is
  approximate. Re-collect uniformly if the truncation rate matters to a claim.
- **Coprime's Nemotron-3 recovery (0.452 -> 0.792) is confounded.**
  Coprimality forbids both 2 and 4, so that listing is longer AND sparser
  (2.02 vs 2.83 labels/position). Length and density moved together.
- **Equivalence at ceiling is weaker than equivalence mid-range.** All ten
  coprime EQUIVALENT verdicts have zero-width intervals because both arms are
  perfect. Say "indistinguishable at this benchmark's resolution".
- **`power_analysis.py` in each notebook sizes from a pilot and refuses to read
  completed replicates** — deliberate. Posterior questions go to
  `scripts/posterior_power.py`.
- **Divisor has 26 questions/replicate, coprime 6**, against the 9 the original
  `power_analysis.py` assumes. Strata differ; size from each study's own data.
- **`vllm/vllm-openai:nightly` is a moving tag** inherited from
  `periodic_moe/keys.env`. Record the digest per run; pinning it overflows the
  EC2 user-data 16 KB cap (41 bytes of headroom, tag form needs exactly 41).

## 8. Why these studies exist

`periodic_moe` saturated: intens and noise both at ceiling for all three models
at *every* harmonic, so no harmonic separated them (paired McNemar p=0.549 for
gpt-oss, 1.000 for the others). More harmonics cannot fix it —
`lcm(1..10) == lcm(1..9) == 2520`, and `lcm(1..11)` is 11x, a ~341k-token
listing against a 131,072 context.

Two studies attack it from opposite sides:

- **coprime** `(1,3,4,5,7,11)` -> 4,620 positions. `lcm == prod`, so the
  EXTENSIONAL listing lengthens ~1.6x. **Done, and it failed its purpose:**
  intensional went to a perfect 1.000, more saturated than the baseline,
  because lengthening the listing never touches a six-line rule list. It did
  sharpen the extensional contrast. See `notebooks/COPRIME_RESULTS.md`.
- **divisor** 26 periods all dividing 2,520 -> sequence length unmoved, so the
  INTENSIONAL rule list roughly doubles against an unchanged listing. **In
  flight, and the one that matters** for the original question.
