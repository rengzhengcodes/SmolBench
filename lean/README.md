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
Disable with `skip_trivial: false` in the YAML config.


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
LeanDojo Benchmark 4 corpus. LLM clients: an OpenAI-compatible HTTP client
pointed at Prime Intellect (or any vLLM endpoint), and an Anthropic SDK client.

## Bring-up

Prerequisites:

- elan + Lean 4 installed (`elan --version`, `lean --version`).
- `uv` installed.
- `GITHUB_ACCESS_TOKEN` exported (LeanDojo requirement). Stored in
  `~/.config/secrets.env` (chmod 600), sourced from `~/.zshrc`.
- `PRIME_INTELLECT_API_KEY` + `PRIME_INTELLECT_TEAM_ID`, or `ANTHROPIC_API_KEY`,
  depending on provider.

```sh
cd /home/fisherxue/SmolBench/lean
uv sync                                                    # create .venv, install deps
source ~/.config/secrets.env                               # GITHUB / PRIME secrets
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt    # uv-managed Python needs this
```

The two `export`s are also written into `~/.zshrc`, so fresh interactive shells
pick them up automatically. The `source` is only needed in non-interactive
shells (e.g. inside scripts).

## Smoke

```sh
# benchmark sanity
uv run python -m leaneval.cli metadata
uv run python -m leaneval.cli list --limit 10
uv run python -m leaneval.cli replay -n 5 --seed 0   # cold start: ~3min for the 2.4GB traced-corpus pull

# one (theorem, k, rung) cell with N rollouts
uv run python -m leaneval.cli run-cell \
  --full-name "MvPolynomial.totalDegree_zero" --k 1 \
  --rung stepk:1 --n-rollouts 3 \
  --model "anthropic/claude-haiku-4.5"

# pre-flight replay filter (one-time per slice; ~70min wall-clock for random/val)
# Persists per-theorem verdicts to data/replay_passing_<kind>_<split>.jsonl;
# the run-cell loop and downstream sweeps consume only successes.
uv run python -m leaneval.cli filter --kind random --split val

# multi-cell sweep across (theorem, k, rung, model, rollout). Resumable.
uv run python -m leaneval.cli run-sweep --config configs/smoke.yaml

# aggregate a sweep JSONL into a (rung, model) pass-rate table
uv run python -m leaneval.cli analyze results/runs/smoke_v1.jsonl
```

In Python: `from leaneval.corpus import iter_replay_passing` yields the
`BenchmarkTheorem`s whose ground-truth replay was recorded as `success`.

## Layout

```
lean/
├── pyproject.toml        # uv-managed deps, Python 3.12 pin
├── lean-toolchain        # local Lean pin (Dojo manages its own per traced repo)
├── .python-version       # 3.12
├── configs/              # (todo) YAML run configs
├── data/                 # (gitignored) LeanDojo Benchmark 4 + traced corpus
├── results/              # (gitignored) JSONL run outputs
└── leaneval/             # source
    ├── corpus.py         # load benchmark; iterate (theorem, k, traced_tactic)
    ├── premises.py       # (todo, Phase 3) premise lookup → (signature, body, file)
    ├── context.py        # render rungs along stepk + hint chains
    ├── prompt.py         # message assembly + LLM-response parsing
    ├── llm/              # provider clients behind a thin ABC
    │   ├── base.py
    │   ├── anthropic.py
    │   └── openai_compat.py
    ├── verify.py         # Dojo replay + tail submission
    ├── runner.py         # eval loop → JSONL
    └── cli.py            # `python -m leaneval.cli ...`
```

## Plan

`/home/fisherxue/.claude/plans/do-not-refer-to-wobbly-mitten.md` — note the
plan was written before the chain refactor (still uses the old L0..L7 single
ladder); the chain split is the current canonical design.
