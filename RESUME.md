# Resume runbook — coprime & divisor induction studies

Written 2026-08-09 because the machine driving these runs was going down
mid-collection. Everything below is what a fresh session needs to pick up
without re-deriving it.

Branch `periodic-induction`. Last commit before shutdown: `5932137d`.

---

## 1. FIRST: check for billing instances

Do this before anything else, every time. Two p5.48xlarge boxes (~$21/h each)
were live at shutdown:

| instance | region | study |
|---|---|---|
| `i-0e9d2af63354dfb84` | us-east-2 | periodic-divisor-induction |
| `i-06c0a4bce7703f5da` | us-east-2 | periodic-coprime-induction |

They should be **gone**. When the driver process dies the box goes idle and the
on-instance watchdog terminates it after 30 minutes; there is also a hard
`shutdown -h +1440`. Verify rather than assume:

```bash
set -a && . notebooks/ec2-operator.env && set +a
for r in us-east-1 us-east-2 us-west-2; do
  aws ec2 describe-instances --region $r \
    --filters "Name=instance-state-name,Values=pending,running" \
    --query 'Reservations[].Instances[].[InstanceId,InstanceType,LaunchTime,Tags[?Key==`smolbench:experiment`].Value|[0]]' \
    --output text
done
```

If either is still running, a relaunch (step 3) reattaches to it and reuses its
warm model cache — that is better than terminating. Only terminate if you are
not resuming:

```bash
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv('notebooks/periodic_divisor/keys.env')
from smolbench.evals import ec2; ec2.shutdown_instance()"
```

Note the unrelated `pruning-metrics` box in us-east-1 belongs to different
work — do not touch it.

## 2. Where the data stopped

Committed at `5932137d`. Replicates resume-skip on `rep_{seed}.yaml` existence,
so nothing below is re-run or re-paid for.

| study | replicates | gpt-oss | Nemotron-3 | Qwen3.5 |
|---|---|---|---|---|
| `periodic_coprime` | 308/360 | 30/30 | 30/30 | **17/30** |
| `periodic_divisor` | 172/360 | 30/30 | **13/30** | **0/30** |

Target is 360 = 3 models x 4 arms x 30 seeds (1776–1805).

## 3. Resume commands

Run from the repo root, main venv. Each study is a separate process — this is
mandatory, not stylistic: `ec2.py` freezes its `EC2_*` constants from
`os.environ` at import, so two studies cannot share an interpreter.

```bash
set -a && . notebooks/ec2-operator.env && set +a

# coprime: only Qwen is outstanding
COPRIME_N_REPLICATES=30 COPRIME_MODELS=qwen35 \
  nohup .venv/bin/python notebooks/periodic_coprime/run_study.py > /tmp/coprime.log 2>&1 &

# divisor: Nemotron-3 finishes, then Qwen
DIVISOR_N_REPLICATES=30 \
  nohup .venv/bin/python notebooks/periodic_divisor/run_study.py > /tmp/divisor.log 2>&1 &
```

Startup derives each completion budget before provisioning (a minute or two of
CPU, no GPU billing). Expect a log line like:

```
qwen3.5-397b-a17b: worst prompt 59,221 tok (+8,000 reserve) -> completion budget 63,851
```

If that line does not appear, something failed before provisioning — read the
log, do not relaunch blindly.

Rough remaining time at observed rates: coprime ~3–5 h (13 Qwen replicates plus
a ~397 GB load); divisor ~15–20 h (17 Nemotron-3 at ~17 min each, then 30 Qwen).

## 4. When a study reaches 360

```bash
.venv/bin/python scripts/coprime_pilot_gate.py periodic_coprime   # or periodic_divisor
.venv/bin/python scripts/posterior_power.py periodic_coprime --mei 0.05
```

The gate blocks on `compliance=empty` marks (truncation). The posterior power
script sorts every planned contrast into DECIDED / EQUIVALENT / UNDECIDED and
quotes an R only for UNDECIDED ones — it deliberately does not report observed
power, which is just a restatement of the p-value.

Then commit results and figures.

## 5. Hazards already hit — do not rediscover these

Three failures cost roughly 10 hours of collection between them. All are fixed
in committed code; they are listed so the symptoms are recognisable.

1. **600 s read timeout vs a large completion budget** (`c50bb6b0` lineage).
   A read timeout counts toward `EC2_MAX_CONNECTION_FAILURES`, so a long
   generation dies after 10 retries with a misleading "endpoint unreachable"
   when the endpoint is perfectly healthy. Fixed by
   `EC2_REQUEST_TIMEOUT_SECONDS=3600` in both studies' `keys.env`.

2. **Teardown deleting another run's state file** (`3da8b192`). Run A's
   teardown used to unlink state unconditionally, including state run B had
   just written for a *different* box — stranding a live $21/h instance with
   nothing driving it. `_clear_state` now only clears state it owns. Still:
   **do not launch a study while a previous run of the same study is tearing
   down.** Wait for the process to exit.

3. **Completion budget sized from `count()` on one seed** (`c50bb6b0`). Two
   ways wrong: `count()` excludes the server-side chat template (~1,547
   tokens), and one seed is not the worst seed (coprime's worst extens prompt
   is 59,221 at seed 1793 vs 55,526 at seed 1776). A budget one token too large
   gets a vLLM 400, which kills the whole run. Now derived at startup with an
   8,000-token reserve — **do not hardcode it again.**

## 6. Analysis caveats to carry into the write-up

- **Qwen cannot fully fit the coprime task.** Its derived budget there is
  63,851, *below* the 65,536 that already truncated one mark. At ~59k-token
  prompts Qwen3.5 cannot reliably both reason and answer inside a 131,072
  context. Report its invalid rate as a finding about the model at this prompt
  length, not as a misconfiguration.
- **A budget seam inside coprime's Qwen arm.** Replicates collected before the
  shutdown used 65,536; the remaining ones use 63,851. Treat that arm's invalid
  rate as approximate, or re-collect the arm uniformly if the truncation rate
  matters to a claim.
- **`power_analysis.py` in each notebook sizes from a pilot and refuses to read
  completed replicates** — that is deliberate, not a bug. Posterior questions
  go to `scripts/posterior_power.py`.
- **Divisor has 26 questions per replicate, coprime 6**, against the 9 the
  original `power_analysis.py` assumes. Strata differ, so size R from these
  studies' own data rather than inheriting the baseline's numbers.
- **`periodic_moe/keys.env` pins `vllm/vllm-openai:nightly`, a moving tag**,
  and both new studies inherit it. Record the digest per run; pinning it
  overflows the EC2 user-data 16 KB cap (41 bytes of headroom, and the tag form
  needs exactly 41).

## 7. What these studies are for

`periodic_moe` saturated: intens and noise_intens are both at ceiling for all
three models at *every* harmonic, so no harmonic separates them (paired
McNemar p=0.549 for gpt-oss, 1.000 for the others). More harmonics cannot fix
it — `lcm(1..10) == lcm(1..9) == 2520`, and `lcm(1..11)` is 11x, a ~341k-token
listing against a 131,072 context.

The two studies attack the saturation from opposite sides:

- **coprime** `(1,3,4,5,7,11)` → 4,620 positions. Pairwise-coprime, so
  `lcm == prod` and the EXTENSIONAL listing lengthens ~1.6x.
- **divisor** 26 periods all dividing 2,520 → sequence length unmoved, so the
  INTENSIONAL rule list roughly doubles against an unchanged listing.

Noise adds length without adding rules, so it cannot separate a context-length
limit from a rule-tracking one. Together these can.

Early divisor signal (gpt-oss, R=30) is already interesting: extens fails only
at *large* periods (needles in 2,520 lines) while intens fails only at *small*
ones (large-number division) — the two representations break at opposite ends
of the harmonic range.
