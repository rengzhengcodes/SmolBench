# Lean 4 theorem proving with positive-information context pollution

Evaluate LLM ability to complete Lean 4 proofs as a function of how much context
is supplied about the proof. Given an intermediate state at step `k` of a known
theorem, the eval varies context and measures pass rate.

## Two ways of varying context

**`stepk` — progressively more *step-k* information** with no answer-conditional
content.

| Rung | Adds |
|---|---|
| `stepk:0` | Bare goal expression at step k (hypotheses stripped) |
| `stepk:1` | + local hypotheses (full tactic state) |
| `stepk:2` | + tactics applied so far (steps 0..k-1) + theorem identity (name, file) |

**`hint` — the next-step hint, described in progressively more detail** about the premises
used in the true next tactic. 

| Rung | Adds (cumulative) |
|---|---|
| `hint:0` | `stepk:2` + names of premises used in the true next tactic |
| `hint:1` | + type signatures of those premises |
| `hint:2` | + full bodies of those premises (Lean source) |
| `hint:3` | + 1-hop transitive closure of premise dependencies |
| `hint:4` | + 2-hop transitive closure (BFS, ≤50k token cap) |

**`noise` — control arm for `hint:3` / `hint:4`.** Same baseline as `hint:2`
plus lorem-ipsum filler sized to match the corresponding hint rung's token
count (per-theorem). Isolates *answer-conditional content* from *raw context
length*: comparing `hint:N` vs `noise:N` answers "is the degradation due to
volume alone, or to the specific premise content being injected?"

| Rung | Adds (cumulative) |
|---|---|
| `noise:3` | `hint:2` + lorem padding sized to match `hint:3`'s token count |
| `noise:4` | `hint:2` + lorem padding sized to match `hint:4`'s token count |

## Status of implemented rungs

All 10 rungs are implemented (`stepk:0..2`, `hint:0..4`, `noise:3..4`).

- `hint:1` (signatures) — splits each premise's `code` at the first top-level
  `:=` (bracket-aware so attribute syntax doesn't trip it).
- `hint:2` (full source incl. proof) — slices the cached mathlib4 source file
  from the premise's `start` to the next top-level declaration. Captures real
  proof bodies for theorems, not just the signature stored in `code`.
- `hint:3` / `hint:4` — file-level transitive closure: BFS over the corpus's
  per-file `imports` from the seed files (the files containing the true
  premises), depth 1 / 2. Premises in those reachable files are included in
  signature form, BFS-ordered (closest first) and truncated to a 50k token
  budget. This is the *cheap* variant of transitive closure — coarser than
  per-premise dep-graph scanning but tractable and aligned with the "more
  context-shaped padding" framing.

### Trivial-rung skip (default on)

A rung is *trivial* when it adds no informational content beyond the previous
rung in its chain — e.g. `stepk:2` at `k=0` (no prior tactics), `hint:0`
when no premises are recorded, `hint:1` when none of the true premises are
in the corpus, `hint:2` when no premise's body differs from its signature,
`hint:3`/`hint:4` when seed files have no imports at the requested depth.
The sweep filters trivial rungs *before* the LLM call, so per-rung pass
rates only count theorems where the rung-up actually changed the context.
Disable with `skip_trivial: false` in the sweep config (a `notebooks/lean/
lean_eval.ipynb` config dict, or the equivalent key in a YAML file passed to
`run-sweep`).


## Dataset

[LeanDojo Benchmark 4](https://zenodo.org/records/10929138) (Zenodo
`10929138`, mathlib4 commit `fe4454af`, March 2024). The 64 MB JSON ships
under `data/`; the ~2.4 GB *traced* corpus is pulled lazily from LeanDojo's
S3 cache to `~/.cache/lean_dojo/` on the first `Dojo` call.

data/replay_passing_random_val.jsonl logs which proofs trace in random split

### Pool size

| kind | split | total | w/ traced tactics |
|---|---|---:|---:|
| random | train | 112,729 | 56,140 |
| random | val | 2,000 | 1,035 |
| random | test | 2,000 | 991 |
| novel_premises | train | 112,729 | 55,932 |
| novel_premises | val | 2,000 | 1,104 |
| novel_premises | test | 2,000 | 1,130 |

* We only look at traced tactics (because we can chunk them and replay them)

### What we eval on

- **Source of truth:** the LeanDojo Benchmark JSON. We do not extract our own
  theorems; the trace coverage and premise annotations are what they are.
- **Default working slice:** `random/val` (1,035 tactic-mode theorems) — small
  enough for fast iteration, big enough for variance to matter.
- **Headline slice for the final sweep:** `novel_premises/test` (1,130) — same
  shape as `random/val` but tests generalization to unseen premises, which is
  the more honest signal when the `hint` chain leaks premise identity.
- **Pre-flight replay filter:** before a theorem enters the eval set, we replay
  its ground-truth tactics through Dojo and require `ProofFinished`. Theorems
  that fail this gate are dropped — "the LLM beat the ground truth" isn't a
  meaningful comparison when we can't reproduce the ground truth ourselves. On
  a random `random/val` sample the gate passes ~80%; the failures are mostly
  term-style proofs with embedded `by` blocks that the trace records as a
  single tactic but isn't directly replayable from the theorem entry-point.
- **Step-k choice:** for each kept theorem we pick the intermediate step `k`
  the cell evaluates. Early experiments default to `k = len(traced_tactics) − 1`
  (LLM emits only the final tactic) for high signal-to-cost. Later sweeps
  stratify across early / mid / late `k`.
- **Smoke biasing:** the `replay` smoke samples theorems with
  `1 ≤ len(traced_tactics) ≤ 5` (configurable via `--max-tactics`) to keep
  cold-path tests fast and bias toward likely-replay-passing proofs.

### Premise corpus

`data/leandojo_benchmark_4/corpus.jsonl` — 5,192 records, one per Lean source
file in the traced repo, with its imports and the list of premises it defines
(name + position span). This is the data backing the `hint:1+` rungs (premise
signatures, bodies, and transitive closure).

### What's not in scope

- Theorems outside the traced mathlib4 commit (current Mathlib HEAD,
  downstream libraries).
- Term-mode proofs without traced tactics.
- Theorems that fail the pre-flight replay.


## Backend

[LeanDojo](https://leandojo.org) `Dojo` interactive sessions over the prebuilt
LeanDojo Benchmark 4 corpus, for verification. Generation goes through
`smolbench`'s shared provider stack (`smolbench/evals/`, dispatched per-model
via each model config's `provider` field — `openrouter`, `primeintellect`,
`aws` (Bedrock/SageMaker), or `ec2` (a self-provisioned vLLM spot instance,
for open-weight models with no hosted route)) rather than the standalone
OpenAI-compatible / Anthropic SDK clients the original standalone `lean/`
project used. Every request now carries an explicit decoding seed: the sweep
config's base `seed` plus the cell's `rollout_idx`, so every rollout of every
cell is independently reproducible.

## Project layout

The eval was folded into `smolbench` from a standalone `lean/` project (see
git history for the pre-fold layout). It now spans two directories:

```
smolbench/deduction/lean/            # installed package: generation + verification
├── corpus.py               # load benchmark; iterate (theorem, k, traced_tactic)
├── premises.py              # premise lookup → (signature, body, file)
├── context.py               # render rungs along stepk + hint chains
├── prompt.py                 # message assembly + LLM-response parsing
├── verify.py                  # Dojo replay + tail submission (.venv-lean only)
├── runner.py                   # sweep engine → JSONL (resumable, session reuse)
├── cli.py                       # `python -m smolbench.deduction.lean.cli ...`
└── figures.py                    # shared helpers for the figure scripts below

notebooks/lean/             # experiment surface (this directory)
├── README.md                # this file
├── lean_eval.ipynb           # canonical run notebook (.venv-lean kernel)
├── keys.env                   # gitignored: provider keys + optional EC2 config
├── data/                        # (gitignored except the two files below)
│   └── leandojo_benchmark_4/     # Zenodo download (see Bring-up)
├── results/                   # COMMITTED — run outputs (see Results policy)
│   └── runs/<run_name>/
│       ├── manifest.json        # config + run_id + start/finish timestamps
│       ├── all_rows.jsonl       # source of truth, append-only across resumes
│       ├── analysis.txt         # `analyze`/`report` output
│       └── theorems/<slug>/     # per-theorem prompts, outputs, summary.md
└── figures/                   # publication-figure scripts (see below)
```

Every `smolbench.deduction.lean` module except `verify.py` — including `runner.py`
and `cli.py` — imports cleanly on any Python ≥ 3.12 (the repo's main
`.venv` included): the runner reaches `verify.py` lazily, at call time,
through its `verifier=` injection seam (`runner._default_verifier`), never
at import time. What needs the dedicated `.venv-lean` environment is
*executing* the verification path — `sweep`/`run_cell` with the default
verifier, and the `replay`/`filter`/`run-cell`/`run-sweep` CLI
subcommands — because `lean_dojo` pins `Requires-Python <3.13` upstream.
Importing `smolbench.deduction.lean.verify` on 3.14 raises an actionable
`ImportError` pointing at the `.venv-lean` one-liner.

The four YAML configs that used to live under the standalone project's
`configs/` directory (`smoke.yaml`, `main_v3.yaml`, `main_v3_2.yaml`,
`noise_iso_3way.yaml`) are now `SMOKE_CONFIG` / `MAIN_V3_CONFIG` /
`MAIN_V3_2_CONFIG` / `NOISE_ISO_3WAY_CONFIG` dicts in `lean_eval.ipynb`'s
config cell instead of files. The other, already-retired configs
(`main.yaml`, `main_v2.yaml`, `noise_iso.yaml`, `noise_iso_deepseek.yaml`,
`noise_iso_gpt55.yaml`, `noise_iso_r1.yaml`, `smoke_main_v3.yaml`) were
single-model or superseded variants that were never migrated forward; they
remain visible in git history (`git log --follow -- lean/configs/`) but are
not notebook cells.

## Bring-up

This eval spans two Python environments:

- **Main `.venv` (repo root, Python 3.14).** Covers generation and analysis:
  `corpus`, `premises`, `context`, `prompt`, `figures`, and the figure
  scripts. Bring up per the repo root's own instructions (`uv sync
  --all-extras` or equivalent); no lean-specific step is needed beyond the
  `lean`/`notebook` extras being included.
- **`.venv-lean` (Python 3.12, dedicated).** Additionally covers
  *executing* verification (`verify.py`, i.e. running `sweep`/`run_cell`/
  `replay`/`filter`) via `lean-dojo`, which pins `Requires-Python <3.13`
  upstream and so cannot be installed into the main 3.14 environment.
  Build it from the repo root:

  ```sh
  UV_PROJECT_ENVIRONMENT=.venv-lean uv sync --python 3.12 --extra lean --extra notebook --extra dev
  ```

  Use `.venv-lean/bin/python` (or the `.venv-lean` Jupyter kernel) for
  anything that runs a sweep, replays proofs, or opens a `Dojo` session.

Additional prerequisites, both environments:

- elan + Lean 4 installed (`elan --version`, `lean --version`) — Dojo
  manages its own toolchain per traced repo, but `elan` itself must be on
  `PATH`.
- A `GITHUB_ACCESS_TOKEN` — optional in practice for this eval's paths:
  `replay`/`verify` against the prebuilt benchmark pull the traced corpus
  anonymously from LeanDojo's S3 cache (verified working without a token).
  Heavier LeanDojo use (fresh tracing, many GitHub API calls) may still hit
  anonymous rate limits — see `keys.env` below.

### Data bootstrap

Download the [LeanDojo Benchmark 4](https://zenodo.org/records/10929138)
release (Zenodo record `10929138`) and unpack it so that
`notebooks/lean/data/leandojo_benchmark_4/` contains `metadata.json`,
`corpus.jsonl`, and the `random/` / `novel_premises/` split directories
(matching the "Dataset" section above). This directory is gitignored (it's
a ~700 MB external download, not a generated artifact); the
`replay_passing_<kind>_<split>.jsonl` sidecars that `filter` writes to
`notebooks/lean/data/` (one level up from `leandojo_benchmark_4/`) get
committed once generated — they're comparatively small and expensive to
regenerate. **None are checked in yet**: the sweep configs use
`theorems.source: replay_passing`, so before the first sweep over a given
(kind, split) run the pre-flight filter once (~70 min for random/val):

```sh
.venv-lean/bin/python -m smolbench.deduction.lean.cli filter --kind random --split val
```

then `git add` the sidecar. Until it exists the runner fails fast with a
`FileNotFoundError` naming that command.
The ~2.4 GB *traced* corpus itself is not part of this download — it's
pulled lazily from LeanDojo's S3 cache to `~/.cache/lean_dojo/` on the first
`Dojo` call (cold start: a few minutes).

`SMOLBENCH_LEAN_DATA` overrides the data root if you'd rather keep the
dataset outside the repo tree (see `smolbench.deduction.lean.corpus.data_root`).

### keys.env

`notebooks/lean/keys.env` (gitignored — `*.env` is repo-wide gitignored) is
loaded by `lean_eval.ipynb`'s setup cell via `load_dotenv`. Required/optional
variables:

- `PRIME_INTELLECT_API_KEY` — Prime Intellect passthrough (most models in
  the four configs route here, including the `anthropic/...` and
  `openai/...` ids — Prime Intellect proxies both labs).
- `PRIME_INTELLECT_TEAM_ID` — optional, only needed for team-scoped PI
  accounts.
- `OPENROUTER_API_KEY` — alternative route for any model config with
  `provider: "openrouter"` instead of `"primeintellect"`.
- `GITHUB_ACCESS_TOKEN` — optional; only needed if LeanDojo hits anonymous
  GitHub rate limits (the benchmark's traced corpus itself downloads
  anonymously from S3 — see Bring-up above). Unrelated to model inference.
- `EC2_EXPERIMENT_TAG` / `EC2_STATE_FILE` (optional) — only needed when
  serving an open-weight model yourself via `provider: "ec2"`
  (`smolbench/evals/ec2.py`). Give this experiment its own tag (isolating
  its instance from `notebooks/periodic`/`notebooks/chromatic`) and anchor
  `EC2_STATE_FILE` to a repo-root path (e.g. `<repo root>/.ec2_state_lean.
  json`), not a cwd-relative one — notebook kernels can run with a temp-dir
  cwd.

## How to run

`lean_eval.ipynb` is the canonical way to run this eval: it defines the four
live sweep configs and a run + analyze cell pair for each. Open it with the
`.venv-lean` kernel (see Bring-up).

The `smolbench.deduction.lean.cli` (`python -m smolbench.deduction.lean.cli <subcommand>`)
remains the scriptable/headless entry point and CI/ad-hoc-debugging escape
hatch. Venv split by subcommand:

```sh
# Main .venv (3.14) — no Dojo session, generation/analysis only:
.venv/bin/python -m smolbench.deduction.lean.cli metadata
.venv/bin/python -m smolbench.deduction.lean.cli list --limit 10
.venv/bin/python -m smolbench.deduction.lean.cli analyze notebooks/lean/results/runs/<run>/all_rows.jsonl
.venv/bin/python -m smolbench.deduction.lean.cli report notebooks/lean/results/runs/<run>
.venv/bin/python -m smolbench.deduction.lean.cli show notebooks/lean/results/runs/<run>
.venv/bin/python -m smolbench.deduction.lean.cli compare notebooks/lean/results/runs/<run> <model> <rung_a> <rung_b>
.venv/bin/python -m smolbench.deduction.lean.cli prompt-stats --limit 50

# .venv-lean (3.12) — opens a Dojo session:
.venv-lean/bin/python -m smolbench.deduction.lean.cli replay -n 5 --seed 0   # cold start: ~3min for the 2.4GB traced-corpus pull
.venv-lean/bin/python -m smolbench.deduction.lean.cli filter --kind random --split val   # pre-flight replay filter; ~70min for random/val
.venv-lean/bin/python -m smolbench.deduction.lean.cli run-cell --full-name "MvPolynomial.totalDegree_zero" --k 1 --rung stepk:1 --n-rollouts 3 --model "anthropic/claude-haiku-4.5"
.venv-lean/bin/python -m smolbench.deduction.lean.cli run-sweep --config path/to/config.yaml   # headless equivalent of a notebook run cell
```

In Python: `from smolbench.deduction.lean.corpus import iter_replay_passing` yields
the `BenchmarkTheorem`s whose ground-truth replay was recorded as `success`.

## Fine-tuning (LoRA SFT)

The trio bases (`meta-llama/Llama-3.1-405B-Instruct`,
`nvidia/Llama-3_1-Nemotron-Ultra-253B-v1`, `Qwen/Qwen3-235B-A22B`) are
QLoRA-tuned to this eval's exact task shape and wire format, then served
via the EC2 vLLM provider and swept like any other model.

### Datasets (all under `data/sft/`; JSONLs gitignored, manifests committed)

| builder | output | contents |
|---|---|---|
| `scripts/build_lean_sft.py` | `novel_premises_train_stepk1.jsonl` | REAL: LeanDojo `novel_premises/train` rendered at `stepk:1`, eval theorems held out by `full_name` |
| `scripts/build_lean_synth_sft.py --arm real` | `novel_premises_train_stepk1_decontam.jsonl` | the real set re-filtered through the content-level keys below (stage-2 anneal set) |
| `scripts/build_lean_synth_sft.py --arm goedel` | `synth_goedel_v2_24k.jsonl` | SYNTHETIC arm A: 24k seeded-sampled rows of `Goedel-LM/SFT_dataset_v2` (autoformalized competition problems, compiler-verified proofs; statements mathlib-independent), declarations converted to pseudo initial tactic states, CoT stripped |
| `scripts/build_lean_synth_sft.py --arm leannavigator` | `synth_leannavigator_24k.jsonl` | SYNTHETIC arm B: 24k seeded-sampled `(state, tactic)` pairs of LeanNavigator (Zenodo `13989482`; mathlib state-graph traversal -- mathlib-derived by construction, the high-leak-risk arm) |

Raw synthetic corpora download to `data/synth/` (gitignored): the Goedel-V2
HF snapshot (~6 GB parquet) and the LeanNavigator Zenodo tar (~2.7 GB
unpacked JSON).

### Decontamination

Name-based holdout cannot work on an external corpus (no shared naming),
so `smolbench.deduction.lean.decontam.HoldoutIndex` fingerprints every
`novel_premises/{val,test}` theorem's *content* -- everything the eval's
positive-information rungs can expose:

- **K1 name** -- `full_name` (the original holdout, kept).
- **K2 statement** -- normalized step-0 tactic state, exact + MinHash/LSH
  near-duplicate (catches alpha-renamed restatements). Goal-only variants
  are indexed only when long enough to be identifying (short generic goals
  like `⊢ False` recur everywhere and identify nothing).
- **K3 goal states** -- exact match of the state at EVERY proof step
  (sweeps stratify `k`).
- **K4 tactic chains** -- full chain + any 3-consecutive-tactic window
  (>= 3-tactic proofs), plus `(state, next-tactic)` answer pairs, which
  cover 1-2-tactic proofs where a bare `simp`/`rfl` match would be noise.

A row is dropped on any hit; rows merely *invoking* an eval theorem as a
premise are counted in the manifest but kept (premise usage reveals no
answer content). Every build ends with a zero-leak re-scan gate that
re-derives each emitted row's facets from the written JSONL and fails the
build on any hit. Deterministic throughout (seeded MinHash, no model
calls); manifests record per-key drop counts and the holdout fingerprint.

The holdout is `novel_premises/{val,test}` — the eval slices these
fine-tunes are scored on. The `random` and `novel_premises` kinds
repartition one theorem pool, so a `random/val` theorem can sit in
`novel_premises/train`: **if a sweep is ever scored on a `random` split,
add it to the holdout** (`--eval-spec random:val`, repeatable) or its
theorems are not decontaminated.

### Training (staged, per base model)

`scripts/lean_lora_sft.py` (QLoRA; dedicated GPU box via
`scripts/lean_train_ec2.py` -- see its docstring for the provision/setup/
train/teardown flow):

1. **Stage 1 (synthetic pretrain):** train a fresh adapter on
   `synth_goedel_v2_24k.jsonl` (arm A) or `synth_leannavigator_24k.jsonl`
   (arm B).
2. **Stage 2 (real anneal):** continue that adapter on the decontaminated
   real set with `--init-adapter <stage-1 adapter> --dataset
   novel_premises_train_stepk1_decontam.jsonl --cap 8000`.

Nemotron-Ultra uses the same HF pipeline (bnb int32 guard);
`scripts/nemo_convert_data.py` remains the NeMo fallback and consumes the
same JSONLs. The resulting sweep compares four arms per base: base /
real-only / goedel+real / leannavigator+real.

### Capacity Blocks (interruption-free windows for long runs)

Spot p5 boxes get reclaimed mid-stage (twice in one day, 2026-07-10). For
stages that shouldn't race spot reclaims — the multi-day Nemotron-253B and
Llama-405B runs — reserve an EC2 Capacity Block for ML and launch the same
training box into it:

```bash
# 1. Find offerings (read-only; prints price + window + offering id):
python scripts/lean_train_ec2.py cb-search --duration-hours 72 --start-after +6h

# 2. Validate, then buy (UPFRONT + NON-REFUNDABLE; blocks cannot be cancelled):
python scripts/lean_train_ec2.py cb-purchase --region us-east-2 --offering-id cbo-...        # DryRun only
python scripts/lean_train_ec2.py cb-purchase --region us-east-2 --offering-id cbo-... --yes  # real purchase

# 3. Watch it go scheduled -> active, then launch into it:
python scripts/lean_train_ec2.py cb-status
python scripts/lean_train_ec2.py provision --capacity-reservation auto
```

If a live spot box is still recorded in the state file, `provision
--capacity-reservation` **refuses** rather than silently reattaching to the
interruptible box (the flag would otherwise be dropped and the prepaid block
would burn idle) — `teardown` the spot box first, or wait for its stage to
finish. `cb-purchase --yes` runs on a no-retry client: PurchaseCapacityBlock
has no idempotency token, so botocore's default auto-retry could buy the
same block several times on a flaky connection.

Purchases are recorded in `.ec2_state_lean_train_cb.json` (gitignored, next
to the instance state file); `provision --capacity-reservation` pins the
launch to the reservation's region/AZ/instance type and sizes the OS-halt
backstop to the block's **end** (+60 min) instead of the 48h spot default —
the block is prepaid, so an idle tail costs nothing, while the spot default
would halt a 7-day run mid-block. Inside the window there are no spot
interruptions; AWS still reclaims the box at the block's end (~30 min
warning), which the per-stage S3 checkpoint sync already covers. Everything
downstream (`setup` / `attach-s3` / `train` / the 4-way orchestrator) is
unchanged.

## CoT recipe (round 1)

The real-only/synthetic-pretrain trio above (`base` / `real-only` /
`goedel+real` / `leannav+real`) scored no better than chance: the best arm,
`qwen3-lean-leannav`, beat 17/77 vs base's 15/77, McNemar insignificant. The
2026-07-12 deep-research report
(`notebooks/lean/research/2026-07-12_sft_recipe_deep_research.md`) diagnoses
why — bare tactic-tail SFT targets with assistant-only loss train away the
base models' chain-of-thought (output length collapsed ~5k → ~15 tokens
during training) — and ranks CoT-augmented targets as the highest-evidence
fix, ahead of expert iteration, higher LoRA rank, and curation. This section
is the runbook for that recipe's round-1 (smoke-gated) rollout.

### 8k smoke chain

De-risks the recipe on Qwen alone (the trio's least-favorable base — see the
plan's "Gate asymmetry" decision) before annotating or training the other
two. Each step is a separate spend/go decision; stop and read the previous
step's output before starting the next.

1. **Annotate.** A Bedrock Claude call per row writes a retrospective
   rationale around each row's byte-identical ground-truth tail (see
   `scripts/annotate_lean_cot.py`'s module docstring); boto3 SigV4 needs no
   bearer minting, just a profile:

   ```bash
   # Preview composed prompts/targets first -- no AWS client, no network:
   .venv/bin/python scripts/annotate_lean_cot.py --style think --limit 5 --dry-run

   # The smoke annotation (~$15 at Haiku-tier pricing, temperature 0):
   AWS_PROFILE=rengz .venv/bin/python scripts/annotate_lean_cot.py --style think --limit 8000
   ```

   Writes `notebooks/lean/data/sft/cot_stepk1_think_8k.jsonl` plus
   `cot_stepk1_think_8k.manifest.json` and `cot_stepk1_think_8k.qc.json`.

2. **QC report check** — read the `.qc.json` (and skim 20 rows by hand,
   per the plan's live-gate list) before spending anything on GPUs:
   `rationale_length_chars` percentiles look like prose, not a one-liner;
   `distinct_5gram_ratio` isn't near-zero (boilerplate rationale);
   `grounding_rate` is well above zero (rationales actually cite goal/hyp
   symbols); `holdout_name_mentions.total == 0`. The `.manifest.json`'s
   `decontamination.preflight_bare_facet_rescan` must read `"passed"`.

3. **Provision the training box + attach S3:**

   ```bash
   set -a; source notebooks/periodic/keys.env; set +a   # HF_TOKEN + AWS creds
   .venv/bin/python scripts/lean_train_ec2.py provision
   .venv/bin/python scripts/lean_train_ec2.py setup      # uploads DATASETS, present OPTIONAL_DATASETS
                                                          # (warns + skips missing CoT jsonls), both orchestrators
   .venv/bin/python scripts/lean_train_ec2.py attach-s3
   ```

4. **Launch the orchestrator** (SSH in; it self-halts when done, so a plain
   `nohup … &` is enough):

   ```bash
   ssh -i .ec2_lean_train_key.pem ubuntu@<public_ip>   # public_ip from step 3's output, or `status`
   nohup bash /opt/train/lean_cot_recipe.sh > /opt/train/out/cot-recipe.stdout.log 2>&1 &
   exit
   ```

   Runs `bare8k-r128` (control) then `cot8k-r128` (treatment), same
   rank/schedule, so a gate win is attributable to the CoT format and not
   the rank bump alone. Poll with `.venv/bin/python scripts/lean_train_ec2.py
   status` (tails the most recent on-box log); the orchestrator's own
   step log is `/opt/train/out/cot-recipe.orch.log`
   (START/RESUME/SKIP/END per stage). Off-box, `DRYRUN=1 bash
   scripts/lean_cot_recipe.sh` prints every stage's fully-resolved command
   with no AWS/GPU touch — the plumbing check `tests/test_lean_cot_recipe.py`
   runs offline.

5. **Gate eval**, pre-registered before spend:

   ```bash
   # Pick n_theorems off the RECOMMEND line (defaults: pass@8, mid delta):
   .venv/bin/python scripts/lean_gate_power.py --sims 2000

   set -a; source notebooks/periodic/keys.env; set +a
   .venv-lean/bin/python scripts/lean_ec2_sweep.py --phase cot-gate --cot-smoke \
     --limit <RECOMMEND n_theorems> --n-rollouts 8
   ```

   `--cot-smoke` serves the four paired arms (`base` / `real-only` /
   `bare8k-r128` / `cot8k-r128`, `COT_SMOKE_ARMS` in `lean_ec2_sweep.py`) on
   the SAME cells (`--phase cot-gate`'s theorem sample), `--lora-rank`
   auto-resolves to 128. `.venv/bin/python -m smolbench.deduction.lean.cli
   analyze notebooks/lean/results/runs/lean_cot_gate/all_rows.jsonl` prints
   the per-(model, rung) pass@N tables. **IMPROVEMENT GATE**: `cot8k-r128`
   must beat BOTH `bare8k-r128` and base on paired (theorem, k, rung) cells
   — McNemar's exact test on each pair's discordant counts (reuse
   `lean_gate_power.mcnemar_exact_p(b, c)`; there's no CLI wrapper for this
   cross-arm pairing yet, so read the discordant counts off `all_rows.jsonl`
   by hand/notebook) at `p < 0.05` each, reporting effect size
   `(b - c) / n_cells` and a CI, not just the p-value. Green → prune + full
   annotation + trio commitment (below). Red → the plan's fallback is a
   cheap dense fenced micro-smoke (a few hundred fenced rows, tiny
   train+serve) before any abandon decision — not decisive on Qwen alone
   given the gate-asymmetry caveat.

### Sizing

Effective batch = `--batch-size 1 × --grad-accum 16` = 16; steps =
`ceil(rows / 16) × --epochs`; ~40s/step observed for a trio-class QLoRA
step:

| stage | rows | epochs | steps | wall time |
|---|---:|---:|---:|---|
| 8k smoke arm (`bare8k-r128` / `cot8k-r128`, each) | 8,000 | 2 | 1,000 | ≈11h/arm |
| 56k full (`cot-full-r128`, per trio model, **pre-prune**) | 56,000 | 2 | 7,000 | ≈78h/model |

The 56k figure spans the 48h spot horizon — capacity-block territory (see
below); the round-1.5 curation prune (below) is expected to cut both the
row count and this wall time by ~30–40%.

### Capacity blocks for the full-trio run

Reuses the general `cb-search` / `cb-purchase` / `cb-status` /
`provision --capacity-reservation` flow documented above; `setup` /
`attach-s3` are unchanged. The CoT-specific piece is the launch command
(`FULL=1` runs one `cot-full-r128` stage per trio model, cap 0 = all rows,
on the FULL annotated pool — only after the smoke gate above is green):

```bash
ssh -i .ec2_lean_train_key.pem ubuntu@<public_ip>
FULL=1 nohup bash /opt/train/lean_cot_recipe.sh > /opt/train/out/cot-recipe-full.stdout.log 2>&1 &
```

**Two-block spanning is a MANUAL flow** — one 72h-class block will not
cover a ~78h/model (pre-prune) sequential trio run:

1. Block A ends; AWS reclaims the box (~30 min warning). The orchestrator's
   90s S3 sync + `--save-steps 100` checkpoints already cover this — nothing
   to do here but let it happen.
2. Have block B `cb-purchase`d and `cb-status`-confirmed active ahead of
   time, so there's no idle gap between blocks.
3. `provision --capacity-reservation <block B id>` (or `auto`) re-launches
   into block B. Confirm block A's box reads terminated via `status` first
   — `provision --capacity-reservation` refuses if a live box is still
   recorded in the state file.
4. `setup` again (a fresh box has a fresh NVMe — datasets, trainer, and
   both orchestrators need re-uploading) and `attach-s3` again (fresh
   instance profile attachment).
5. Relaunch `FULL=1 nohup bash /opt/train/lean_cot_recipe.sh &`. Per-stage
   S3 completion-check + `--resume-from-checkpoint auto` picks back up from
   the last checkpoint synced before the reclaim — continuity crosses the
   block boundary automatically; only the box-level orchestration above is
   manual.

### Curation prune — TODO round-1.5

Before annotating the remaining pool for the full run, research finding #8
(MPS-Prover: pruning ~40% of redundant training rows loses nothing, and
improves results) calls for a near-dup self-prune over
`novel_premises_train_stepk1_decontam.jsonl`, reusing
`smolbench.deduction.lean.decontam`'s MinHash/LSH machinery (its K2
near-duplicate index) in SELF-dedup mode — one pool row against another,
not against the eval holdout. Expected cut ~30–40%, shrinking both the
remaining annotation spend and the Sizing table's 56k-row wall time
proportionally. **Not implemented in round 1** — no prune script exists yet;
do this before the `--limit 0` full annotation pass below.

Full annotation, once pruned (or, if the prune is skipped, run as-is against
the full pre-prune pool):

```bash
AWS_PROFILE=rengz .venv/bin/python scripts/annotate_lean_cot.py --style think  --limit 0  # Qwen
AWS_PROFILE=rengz .venv/bin/python scripts/annotate_lean_cot.py --style fenced --limit 0  # both dense bases
```

`--limit 0` selects every row in `--dataset` (no priority ranking, unlike a
capped run), which trivially superset-includes the smoke's 8,000 rows by
`(full_name, k)` identity. Resume keys off `--out`, and the full run's
default `--out` (`cot_stepk1_think_full.jsonl`) differs from the smoke's
(`cot_stepk1_think_8k.jsonl`) — `cp` the smoke output to the full run's
default path first if you want resume to skip (and not re-pay for) those
8,000 rows; otherwise the ~$15 duplicate spend is small relative to the
full run's ~$75–200 and it's fine to just let it re-annotate.

### Deferred to round 2

- **Compiler-feedback self-correction / DPO-on-errors** (research finding
  #3): retrain on the model's own FAILED rollouts paired with the Lean
  compiler's error message, either as SFT self-correction turns or a DPO
  preference pair (successful vs. failed proof of the same cell). Needs a
  harvest pass over `verdict != "success"` rows — the inverse filter of
  `harvest_expert_iter.py`'s success-only gate. Not built.
- **Lean-STaR-style rationale-reproduction filtering**: keep a rationale
  only if re-feeding it to the trainee model, without the ground-truth
  tail, reproduces (or nearly reproduces) the same tail — a
  faithfulness-by-reconstruction filter, distinct from the judge pass
  below. Not built.
- **`annotate_lean_cot.py --judge-sample N`**: parsed but reserved
  (`default=0`, prints "not implemented in round 1" and exits 1 if set) —
  an LLM-judge faithfulness pass over `N` sampled rationales.

### Expert iteration

Gated on the smoke: closing the self-generated-proof loop is only worth the
spend once the CoT format itself is confirmed to help.

```bash
set -a; source notebooks/periodic/keys.env; set +a
.venv-lean/bin/python scripts/lean_ec2_sweep.py --phase expert-iter --cot-smoke \
  --only qwen3-lean-cot-r128
# -> notebooks/lean/results/runs/lean_expert_iter/all_rows.jsonl
#    (pass@8, temperature 1.0, novel_premises/train, stepk:1, source=with_proof)

.venv/bin/python scripts/harvest_expert_iter.py \
  --run-dir notebooks/lean/results/runs/lean_expert_iter --style think \
  --out notebooks/lean/data/sft/expert_iter_r1_think.jsonl \
  --easy-at 0.75 --min-successes 1 --max-per-theorem 2
```

`--cot-smoke --only qwen3-lean-cot-r128` restricts the sweep to the one arm
worth harvesting from (serving the `cot8k-r128` adapter at rank 128).
`harvest_expert_iter.py` keeps verified successes below the `--easy-at`
difficulty ceiling, dedups per theorem, decontaminates from the VERIFIED
proof (never the rationale), and writes rows in the trained wire shape. Feed
the output into a round-2 anneal — e.g. `lean_lora_sft.py --init-adapter
<cot8k-r128 adapter> --dataset expert_iter_r1_think.jsonl` — which is not
yet wired into `lean_cot_recipe.sh` as its own stage; run it as a manual
`lean_train_ec2.py train` invocation until a round-2 orchestrator stage
exists.

## Results policy

`notebooks/lean/results/` is **committed** to the repo, per this repo's
convention for eval results (matching `notebooks/periodic/results/` and
`notebooks/chromatic/results/`) — run outputs are data, not build artifacts,
and reviewing a diff against them is how a sweep's effect gets checked in.
The tree is currently empty: the historical `main_v3`/`main_v3_2` outputs
predate this policy (the old standalone project gitignored its `results/`)
and were not preserved, so the figure scripts have nothing to plot until
those sweeps are re-run (or their outputs recovered) and committed here.
`notebooks/lean/data/leandojo_benchmark_4/` is the one exception under this
directory (see Data bootstrap above): it's a large third-party download,
not something this eval generates.
