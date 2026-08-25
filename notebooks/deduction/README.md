# Deduction: family-ladder scaling study (Lean 4 next-tactic success)

This is the DEDUCTION side of the family-ladder scaling study. The sweep
configuration lives in `run_study.py` (`build_config`), the roster is
imported from `notebooks/induction/run_study.py` (`MODELS`, `COT_ARGS`),
and the fleet-aware entry point for exploring and validating the study is
`lean_eval.ipynb`. This file is intentionally small: it documents the data
layout, the results/verification contracts, and how to run one lane by
hand. It does not document a run-from-cells workflow -- the retired
`notebooks/lean/README.md` documented that older design for a different
(pre-fleet) driver; this study's driver is a per-lane subprocess launched
from a terminal, not from notebook cells (see `lean_eval.ipynb`'s "Fleet
Launch" section).

## Data layout

The traced corpus lives under `notebooks/deduction/data/leandojo_benchmark_4/`
(not committed -- see "Data bootstrap" below):

- `corpus.jsonl` -- every premise (theorem/def/etc.) declared in the traced
  mathlib4 repo, with its source position and containing file
  (`smolbench.deduction.lean.premises`).
- `metadata.json` -- the benchmark's provenance: `dataset_name`,
  `creation_time`, `from_repo` (`url`/`commit`), `leandojo_version`.
- `novel_premises/{train,val,test}.json` and `random/{train,val,test}.json`
  -- the two independent split axes `smolbench.deduction.lean.corpus`
  loads via `load_split(kind, split)`: `"random"` is an i.i.d. train/val/test
  split, `"novel_premises"` is a val/test split chosen so its premises are
  under-represented in train (the harder generalization slice). Each file
  is a JSON array of theorem records (`url`, `commit`, `file_path`,
  `full_name`, `start`, `end`, `traced_tactics`).
- `licenses/` -- upstream license files for the traced repo and the tools
  LeanDojo depends on (CMark.lean, LeanInk, ProofWidgets4, aesop, ...).

Alongside `leandojo_benchmark_4/`, two sidecars record which theorems'
GROUND-TRUTH proofs actually replay successfully against a live Dojo
session: `replay_passing_novel_premises_val.jsonl` and
`replay_passing_novel_premises_test.jsonl`. These are produced by
`python -m smolbench.deduction.lean.cli filter --kind <kind> --split <split>`
and are small enough to commit (unlike the ~700 MB raw dataset). A theorem
whose recorded proof does not replay (a LeanDojo tracing artifact, a
premise that no longer resolves, etc.) is excluded from every sweep that
draws its pool via `corpus.iter_replay_passing`, which this study's
`build_config` always does (`theorems.source == "replay_passing"`).

**Pool size** (measured against the checked-out data, not assumed):

```
.venv/bin/python -c "from smolbench.deduction.lean import corpus; print(len(list(corpus.iter_replay_passing('novel_premises','val'))))"
```

returns **805** -- the `replay_passing`/`novel_premises`/`val` pool this
study draws its 300-theorem sample from (`build_config`'s
`theorems.limit`, seeded `0`).

### Data bootstrap

The dataset itself (`leandojo_benchmark_4/`) is not shipped in this repo:
download the LeanDojo Benchmark 4 archive from
[Zenodo](https://zenodo.org/records/10929138) and unpack it so that
`corpus.jsonl`, `metadata.json`, `novel_premises/`, `random/`, and
`licenses/` land directly under `notebooks/deduction/data/leandojo_benchmark_4/`
(or point `SMOLBENCH_LEAN_DATA` at wherever you unpacked it -- see
`smolbench.deduction.lean.corpus.data_root`'s docstring for the exact
resolution order). Every loader in `smolbench.deduction.lean.corpus` raises
an actionable `FileNotFoundError` naming the exact missing path if this
step has not been done. The `replay_passing_*.jsonl` sidecars are generated
from the bootstrapped dataset (`python -m smolbench.deduction.lean.cli
filter --kind novel_premises --split val`) and are committed once
generated, so a normal clone of this repo already has them without needing
to regenerate.

## What the eval exposes per theorem

Each `BenchmarkTheorem` carries a `traced_tactics` list: one `TracedTactic`
per proof step, with the pretty-printed Lean tactic state immediately
BEFORE the tactic (`state_before`), the tactic text itself, and the state
immediately AFTER (`state_after`). `smolbench.deduction.lean.context.render`
turns step `k` of a theorem into a prompt: at minimum the current goal
(`stepk:0`), and at higher rungs the full tactic state, the proof-so-far,
and premise information (`hint:0..4` -- this study runs `stepk:1`,
`hint:2`, `noise:3`, and `hint:3`; see `lean_eval.ipynb`'s framing cell for
what each is for and why exactly these four). A sweep row then pairs that
rendered context with the theorem's GROUND-TRUTH next tactic
(`traced_tactics[k].tactic`) as the target a model's candidate is compared
against.

So, per theorem, the eval exposes: its goal states at every step `k`
(`state_before` for each traced tactic), its tactic PREFIX (every tactic
before step `k`, surfaced at `stepk:2` and above as "proof so far"), and
its ground-truth tactic TAIL (the tactic actually asked for at each `k`,
plus -- implicitly, by construction -- everything after it in the
recorded proof). This is exactly the content
`smolbench.deduction.lean.decontam.HoldoutIndex` fingerprints (its K3
"goal state" and K4 "tactic chain" key families) to catch a synthetic
training corpus that reproduces an eval theorem's states or tactic chains
inside some OTHER, differently-named theorem -- a leak channel a
`full_name`-only holdout cannot see. See that module's own docstring for
the full key-family breakdown (K1 name, K2 statement, K3 goal state, K4
tactic chain).

## Results policy: S3-only

Every lane's results are spooled to S3, never accumulated locally for the
long term. Bucket `smolbench-results-414266451290`, region `us-west-2`,
key layout `deduction/runs/scaling_<spec-key>/<relative path>` (e.g.
`deduction/runs/scaling_glm-4.7/all_rows.jsonl`).

`run_study.py`'s `spool_to_s3` runs exactly once, after the sweep returns:
it uploads every file under the run directory, verifies each upload
against S3's own `ContentLength` (raising, and leaving local data intact,
on any mismatch), and only once every file has passed verification does it
prune the local run directory -- deleting everything EXCEPT
`manifest.json`. The manifest is deliberately kept: it is the run's
config/run-id record, and keeping it lets a later resume of the same run
recognise that it already exists without first re-downloading the whole
spool from S3 just to check.

## Generation -> verification split

Lean verification is deliberately deferred to a separate pass, because the
two halves need incompatible Python environments:

- **Phase 1 (generation)** runs on the main `.venv` (Python 3.14).
  `notebooks/deduction/run_study.py` calls a model, extracts a candidate
  tactic block, and writes each cell row with `verdict == "unverified"`
  (a placeholder -- nothing has been checked against Lean yet) and each
  per-theorem sanity row with `verdict == "skipped"`. This venv cannot
  import the real verifier at all: `smolbench.deduction.lean.verify`
  requires `lean_dojo`, which pins `python<3.13`.
- **Phase 2 (verification)** runs on the dedicated `.venv-lean` (Python
  3.12, which has `lean_dojo` installed) via `scripts/lean_verify_rows.py`.
  It downloads a run's `all_rows.jsonl` from S3, replays every recorded
  candidate proof against a real Dojo session, and uploads
  `verified_rows.jsonl` beside it -- **the original `all_rows.jsonl` is
  never modified or re-uploaded**; every write goes to the sibling
  `verified_rows.jsonl` key so a verification bug can never corrupt or
  lose a candidate proof that already cost real inference spend to
  collect. Typical invocation (see that script's own module docstring and
  `--help` for the full flag set):

  ```
  .venv-lean/bin/python scripts/lean_verify_rows.py --dry-run
  .venv-lean/bin/python scripts/lean_verify_rows.py --runs 'scaling_glm-4.7*'
  ```

### Two traps in phase 2, both of which fail SILENTLY

**1. `elan` must be on `PATH`, or every group "verifies" as `replay_failed`.**
Under a non-login shell (`ssh cmd`, SSM `AWS-RunShellScript`, cron) `/root/.elan/bin`
is absent from `PATH`, `lean_dojo` cannot spawn Lean, and every Dojo open fails with
`ExceptionPexpect: The command was not found`. The pass does not crash -- it marks
group after group `replay_failed` at high speed and uploads them as if they were
findings. Tells: no `repl`/`lake` processes, one Python process pinned at ~100% CPU
(not the worker count), and implausible throughput. Always:

```
export PATH=/root/.elan/bin:$PATH
```

**2. Resume is keyed on GROUPS, not on the proofs inside them.** If phase 1
regenerated a lane after it was verified, every `(theorem_id, k)` group still looks
done while the candidate proofs beneath are completely different, so the pass reports
`0 to process` and leaves `verified_rows.jsonl` describing text that no longer exists.
Use `--no-resume` for any regenerated lane, and archive the superseded file first.
Compare `all_rows.jsonl`'s LastModified against `verified_rows.jsonl`'s to find them.

**Gate on the verdicts, not on the exit status.** A healthy pass writes a mix of
`success` / `lean_error` with `verify_ms > 0`; a broken one writes `replay_failed`
almost everywhere with a Dojo-open error attached.

**Analysing `all_rows.jsonl` before phase 2 has run shows all-zero success
rates.** That is an artifact of every cell still carrying the `unverified`
placeholder, not a finding about any model -- always check for a
`verified_rows.jsonl` sibling before drawing conclusions from a run's
results.

## Running one lane standalone

```
LEAN_MODEL=<spec key> .venv/bin/python notebooks/deduction/run_study.py
```

`<spec key>` must name a key of `run_study.MODELS` (imported from
`notebooks/induction/run_study.py`; the driver's `SystemExit` message on an
unset or unknown key lists every valid key). Useful flags:

- `--no-s3` -- skip the end-of-run S3 spool sync and leave this lane's
  replicate rows on local disk only.
- `--teardown` -- terminate this lane's EC2 instance after the sweep (or
  after a failure) and exit. **STANDALONE USE ONLY.** Under the fleet
  supervisor (`scripts/run_fleet.py`), a lane's box is reused across the
  induction and deduction phases (same `EC2_EXPERIMENT_TAG`, same state
  file) and the supervisor owns that box's lifecycle end-to-end,
  terminating it itself once every phase scheduled for the lane has
  finished. Passing `--teardown` from fleet-driven automation would
  terminate the instance out from under that bookkeeping -- it exists
  purely for a solo smoke test of this file with nothing else depending on
  the box.

`LEAN_STATE_FILE` and `LEAN_RUN_NAME` are also read from the environment
(see `run_study.py`'s module docstring, "Environment," for the full list);
neither needs to be set for an ad hoc standalone run against a fresh box.

## Replicate terminology note

The replication axis is called **replicates** throughout this study:
`n_replicates` in a sweep config, `replicate_idx` on a result row. An
earlier, now-retired synonym for this same axis must not reappear in this
study's code, notebooks, or documentation -- use "replicate"/"replicates"
exclusively.

## What's not in scope

- **Term-mode (or otherwise untraceable) theorems.** LeanDojo's tactic-mode
  tracer only records `traced_tactics` for theorems it can trace
  tactic-by-tactic; a theorem proved entirely in term mode (or one
  LeanDojo's tracer otherwise could not step through) has an empty
  `traced_tactics` list (`BenchmarkTheorem.has_proof` is `False`) and is
  excluded by every loader in this package that iterates "theorems with a
  proof" (`corpus.iter_with_proof`). This study only ever draws from
  `iter_replay_passing`, which is already a subset of traced theorems, so
  this exclusion is inherited rather than applied again.
- **Levels beyond this study's four rungs.** The full rung universe this
  README documents is `stepk:0..2` / `hint:0..4` (`context.render` accepts
  any of them); `run_study.build_config` runs exactly four of
  those rungs (`stepk:1`, `hint:2`, `noise:3`, `hint:3` -- see
  `lean_eval.ipynb`'s framing cell for what each is for and why). The
  renderer's own range check (`context.validate`) additionally accepts
  `hint`/`noise` levels up to 9 -- deeper transitive premise-dependency-
  closure hops (`hint:5..9`, `noise` mirroring the same range) -- but those
  are neither part of this documented rung universe nor exercised by any
  sweep this study runs; nothing in the renderer breaks past `hint:4`, but
  a deeper hop count is progressively more likely to hit the renderer's own
  50k-token cap before its expanded content actually reaches a rendered
  prompt.
- **The `random` split kind.** This study's pool selector is fixed to
  `kind == "novel_premises"` (the harder generalization slice); the
  `random` split is present in the bootstrapped dataset and loadable via
  `corpus.load_split("random", ...)`, but no sweep this study runs draws
  from it.
- **Live Dojo interaction from the main venv.** Everything in this
  study's generation phase (`run_study.py`, and by extension
  `lean_eval.ipynb`'s cells) runs on the main `.venv` and therefore never
  imports `smolbench.deduction.lean.verify` or opens a real Dojo session --
  see "Generation -> verification split" above.

## Results and data archived (2026-08-25)

`results/` and `data/` were removed from the tree and attached to PR #4 as
`pr4_evidence_and_data_2026-08-25.zip`; see `notebooks/README.md` for the
contents, hashes, and how to restore or regenerate each file.
