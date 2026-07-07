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
