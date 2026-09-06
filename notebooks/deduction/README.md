# Deduction: family-ladder scaling study (Lean 4 next-tactic success)

This is the DEDUCTION side of the family-ladder scaling study. The sweep
configuration lives in `run_study.py` (`build_config`), the roster is
imported from `notebooks/induction/run_study.py` (`MODELS`, `COT_ARGS`),
and the fleet-aware entry point for exploring and validating the study is
`lean_eval.ipynb`. This file documents this directory's layout, the data
layout, the results/verification contracts, and how to run one lane by
hand. There is no run-from-cells workflow: this study's driver is a
per-lane subprocess launched from a terminal (see `lean_eval.ipynb`'s
"Fleet Launch" section).

## Layout

```
deduction/
  run_study.py           the per-lane, generation-only driver  <- pinned here
  lean_eval.ipynb        the exploration notebook
  pinned_theorems.json   the 300 theorems every lane ran  <- see "The pinned 300"
  results/, data/        S3-mirrored; both archived out of the tree
  analysis/              the numbers that got published
```

`run_study.py` stays at this study root because `scripts/fleet/run_fleet.py`
builds each lane's argv from the literal path `notebooks/deduction/run_study.py`
(as does `scripts/deduction/merge_lean_shards.py`), and `results/` stays
directly beneath it because `notebooks/deduction/results` is the path
`results_store.experiment_name` matches -- and what
`smolbench.deduction.lean.runner.results_root()` falls back to.

`analysis/` holds the three read-only report scripts. Each puts its own
directory on `sys.path` and imports its siblings by bare name, so anything
importing them programmatically must register each under a UNIQUE
`sys.modules` name -- the bare names collide with the induction leg's
same-named modules. Load order does not matter (see
`tests/tooling/test_analysis_stats.py`).

| File | What it's for |
| --- | --- |
| `power_analysis.py` | Power analysis for this study: model-vs-model paired McNemar plus block bootstrap. Owns `RESULTS_DIR` and a `--s3` run-file download **for itself only** -- it lands one row file per `scaling_<key>/` run prefix, not the `<model>/verified_rows.jsonl` tree `error_bars.py`/`hint_vs_noise.py` read from `--rows-dir`. |
| `error_bars.py` | Block sign-flip error bars over theorem blocks. **This -- not `power_analysis.py` -- produces the published 14/21**; `--no-count-as-failure` drops cells with no surviving rollout instead of counting them as failures. |
| `hint_vs_noise.py` | Focused test: hint-padded vs noise-padded context, per model. |

Note both legs ship a file named `power_analysis.py`. A process loading
this one and the induction one together must give each a unique
`sys.modules` name -- see `notebooks/README.md`, "Sibling imports".

## Data layout

The corpus lives under `notebooks/deduction/data/leandojo_benchmark_4/` -- a pre-cutoff-era directory name (not committed; see "Data bootstrap" below).
`leandojo_benchmark_4` is a path artifact of the builder's output layout, not itself a claim about which snapshot is checked out: it is both the ORIGINAL pre-cutoff download's directory name and the name `scripts/deduction/build_postcutoff_corpus.py --out <root>` writes its POST-cutoff output under (`<root>/leandojo_benchmark_4`, same pre-cutoff-era name, post-cutoff content):

- `corpus.jsonl` -- every premise (theorem/def/etc.) declared in the traced
  mathlib4 repo, with its source position and containing file
  (`smolbench.deduction.lean.premises`).
- `metadata.json` -- the corpus's provenance: `dataset_name`,
  `creation_time`, `from_repo` (`url`/`commit`), `leandojo_version`, and --
  for a post-cutoff corpus -- an extra `postcutoff` block (see "Corpus date
  vs. model cutoffs" below).
- `novel_premises/{train,val,test}.json` and `random/{train,val,test}.json`
  -- the two split-kind directories `smolbench.deduction.lean.corpus` loads
  via `load_split(kind, split)`. In the PRE-CUTOFF LeanDojo Benchmark 4
  snapshot these are two independent partitions: `"random"` is an i.i.d.
  train/val/test split, `"novel_premises"` is a val/test split chosen so its
  premises are under-represented in train (the harder generalization slice
  that pre-cutoff study's pool was drawn from -- see "History: the
  pre-cutoff study" below). `build_postcutoff_corpus.py` writes both
  directories too (so no loader path 404s), but as real copies of the SAME
  rows: there is no separate generalization-slice curation post-cutoff, so
  this study's driver now reads `random`/`val` by default
  (`LEAN_CORPUS_KIND`/`LEAN_CORPUS_SPLIT`; see `run_study.py`'s module
  docstring, "Environment"). Each file is a JSON array of theorem records
  (`url`, `commit`, `file_path`, `full_name`, `start`, `end`,
  `traced_tactics`).
- `licenses/` -- upstream license files for the traced repo and the tools
  LeanDojo depends on (CMark.lean, LeanInk, ProofWidgets4, aesop, ...).

Alongside the corpus, sidecars record which theorems' GROUND-TRUTH proofs
actually replay successfully against a live Lean session:
`replay_passing_<kind>_<split>.jsonl` -- e.g. `replay_passing_random_val.jsonl`
for this study's default pool. These are produced by
`python -m smolbench.deduction.lean.cli filter --kind <kind> --split <split>`
and are small enough to commit (unlike the multi-hundred-MB raw corpus). A
theorem whose recorded proof does not replay (a tracing artifact, a premise
that no longer resolves, etc.) is excluded from every sweep that draws its
pool via `corpus.iter_replay_passing`, which this study's `build_config`
always does (`theorems.source == "replay_passing"`).

**Pool size** (measured against the checked-out data, not assumed):

```
.venv/bin/python -c "from smolbench.deduction.lean import corpus; print(len(list(corpus.iter_replay_passing('random','val'))))"
```

No number is recorded here: the post-cutoff corpus's `replay_passing`/
`random`/`val` pool depends on which built corpus is checked out, and this
study has not yet fixed a single number for it the way the pre-cutoff study
did (see "History: the pre-cutoff study" below, **805**) -- run the command
above against your own checked-out corpus to find out. Inventing a number
here would be worse than omitting one.

### Data bootstrap

The corpus itself is not shipped in this repo. Build the POST-CUTOFF corpus
with `scripts/deduction/build_postcutoff_corpus.py` (see that script's
module docstring for the full pipeline: a LeanDojo-v2 `generate_benchmark`
export of mathlib4 at a NEW commit, plus
`scripts/deduction/postcutoff_names.py`'s declaration-name-difference JSON
against an OLD commit) and point `SMOLBENCH_LEAN_DATA` at wherever you built
it -- see `smolbench.deduction.lean.corpus.data_root`'s docstring for the
exact resolution order.

**The driver refuses a pre-cutoff corpus.** `notebooks/deduction/run_study.py`'s
`build_config` calls `corpus.postcutoff_metadata()` before any AWS call and
`SystemExit`s if it is `None` (see that function's docstring, "Post-cutoff
corpus gate"): every roster checkpoint's knowledge cutoff postdates the
original LeanDojo Benchmark 4 snapshot's 2024-03-24 trace, so a pre-cutoff
corpus's theorems are not a valid held-out set -- a model may simply have
memorised their proofs during training. (The historical exception is the
ORIGINAL study, which predates this gate and ran directly against that
pre-cutoff snapshot -- see "History: the pre-cutoff study" below.)

Every loader in `smolbench.deduction.lean.corpus` raises an actionable
`FileNotFoundError` naming the exact missing path if the corpus has not been
built. The `replay_passing_*.jsonl` sidecars are generated from the built
corpus (`python -m smolbench.deduction.lean.cli filter --kind random --split
val`, ~70 min per split) and live beside it at `data_root().parent`; they
are not tracked -- see `notebooks/ARCHIVE.md` for the archived pre-cutoff
copies.

### History: the pre-cutoff study

Everything below this point through "The pinned 300" (and the FIRST two
paragraphs of "Corpus date vs. model cutoffs" just after it) describes the
ORIGINAL, COMPLETED, pre-cutoff study: LeanDojo Benchmark 4, pre-cutoff Zenodo record 10929138, traced mathlib4 commit `fe4454af`, `creation_time` 2024-03-24 -- not a live default for new runs. ("Corpus
date vs. model cutoffs"'s own "What the code now enforces" subsection is
NOT historical: it documents the gate the driver enforces today.)
`pinned_theorems.json`'s recorded derivation, the published `deduction/runs`
S3 prefix (see "Results policy: S3-only" below), and
`smolbench.deduction.lean.runner`'s `EXPECTED_THEOREMS` / `EXPECTED_CELLS` /
`EXPECTED_SANITY_ROWS` (300/944/300 -- "the OLD published study's pinned
shape", per that module's own comment) all still describe that pre-cutoff
study; they are retained as the historical record of what was measured,
not as instructions for a new run. New runs draw from the post-cutoff
corpus described above, whose pool size is not yet fixed.

### The pinned 300 (pre-cutoff study)

The PRE-CUTOFF study's `build_config` drew its sample with
`random.Random(0).sample(pool, 300)` over that study's 805-theorem pool (see
"History: the pre-cutoff study" above), so the drawn set was fixed only as
long as that pool was -- and the pool is not stable by construction. It came
from the `replay_passing` sidecars, which are produced by live Dojo replay,
and Dojo init fails nondeterministically. Regenerating a sidecar can add or
drop a theorem, and because `rng.sample` depends on both the membership AND
the order of its population, one changed theorem would have reshuffled the
entire 300. Nothing downstream compared the drawn set against anything, so
that reshuffle would have been silent.

`pinned_theorems.json` therefore records that pre-cutoff study's drawn set
verbatim: the 300 `full_name`s, the corpus provenance, the derivation
recipe, and a sha256 over the sorted names. `tests/deduction/
test_lean_pinning_audit.py` pins that digest, so a reshuffle of the archived
pre-cutoff sidecars would fail a test instead of quietly changing which
theorems the historical record claims that study measured. That file is
also the only in-tree answer to "which theorems did the pre-cutoff study
run": the corpus and both sidecars are archived out of the tree.

`scripts/results/audit_lean_pinning.py` checks that drawn set against what
the pre-cutoff study's 21 lanes actually ran, from the S3 spool -- identical
`theorems` config and seed, identical theorem sets, identical `(theorem,
rung)` cell keys, byte-identical rendered prompts (compared by ETag, so no
spool download), and containment of the recovery and flip side-runs. All 21
lanes ran the same 300 theorems and 944 cells (that pre-cutoff study's
pinned shape, `runner.EXPECTED_THEOREMS`/`EXPECTED_CELLS`) with
byte-identical prompts.

Byte equality is the load-bearing check, not set equality: it proves the
same theorem was asked at the same step `k` under the same rendered context.
It also covers `noise:3`, which is whitespace padded to a token-matched
length -- the induction leg pads under each model's own tokenizer, and had
this leg done the same, that rung would not have been comparable across
models.

This gated the questions ASKED, not the data that came back. Cells can be
present and dead, and that pre-cutoff study's published pools (707/828/833
cells) are smaller than its 944 because dead cells and verdict filtering
shrink it unevenly. Use `scripts/results/audit_run_completeness.py` for
that axis on any run, pre- or post-cutoff.

### Corpus date vs. model cutoffs

`metadata.json` records the trace as mathlib4 at commit `fe4454af`,
`creation_time` 2024-03-24 -- one snapshot, not a date range. Every roster
checkpoint's cutoff postdates it, so 0 of the benchmark's 300 theorems
qualify as post-cutoff by construction, and no sampling, seed, or split
change over this single-commit snapshot can produce one.

Neither of the pre-cutoff study's two holdout mechanisms is a substitute for
a post-cutoff tail, and neither should be cited as if it were one:
`decontam.py` screens a candidate training corpus for content that
reproduces eval theorems, and the pre-cutoff study's `novel_premises` split
selects theorems under-represented in the benchmark's own train split --
both operate entirely within that same 2024-03-24 snapshot.

**What the code now enforces.** A re-collection is underway on a NEW mathlib4
snapshot, restricted by declaration-name set difference against the old
`fe4454af` trace to theorems provably absent from it -- see
`scripts/deduction/build_postcutoff_corpus.py` for how that corpus is built;
this section only covers what consumes it. Such a corpus's `metadata.json`
carries an extra `postcutoff` block (`method`, `old_commit`,
`old_commit_date`, `new_commit`, `new_commit_date`, `target_date`,
`n_old_decls`, `n_new_decls`, `n_postcutoff_decls`), and every theorem row it
emits carries a per-row `postcutoff` boolean flag.
`smolbench.deduction.lean.corpus.is_postcutoff_corpus()` (backed by
`corpus.postcutoff_metadata()`) reports whether the ACTIVE corpus
(`SMOLBENCH_LEAN_DATA`, or the default LeanDojo Benchmark 4 location) carries
that block, and raises rather than silently reporting False if the block's
`new_commit` disagrees with the corpus's own traced commit -- an incoherent
corpus must not be trusted.

The runner enforces this at the point theorems are actually selected:
`smolbench.deduction.lean.runner._select_theorems` accepts a
`theorems.require_postcutoff` config key which, when true, refuses to select
from a corpus that is not `is_postcutoff_corpus()`, and separately refuses
any pool or final selection containing a theorem whose `postcutoff` flag is
unset -- both checks raise `ValueError` rather than silently proceeding.
`notebooks/deduction/run_study.py`'s `build_config` runs a second, earlier
gate, BEFORE any AWS call: it requires `corpus.postcutoff_metadata()` to be
non-`None` (else `SystemExit`, naming the corpus root and its traced commit)
and requires the block's `target_date` to be `>=` `ROSTER_LATEST_RELEASE`
(`"2026-06-03"`, the latest weights-publication date across the 21-model
roster: the last Hugging Face commit touching a weight file at each lane's
pinned revision; weights cannot encode data published after they were
written, so this is the floor a post-cutoff corpus's target date must clear).
`build_config` then sets `theorems.require_postcutoff: True` in the sweep
config it hands to `runner.sweep`, so `_select_theorems` re-checks the same
corpus and every selected theorem at sweep time, independent of the earlier
gate.

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
"goal state" and K4 "tactic chain" key families) to catch a candidate
training corpus that reproduces an eval theorem's states or tactic chains
inside some OTHER, differently-named theorem -- a leak channel a
`full_name`-only holdout cannot see. See that module's own docstring for
the full key-family breakdown (K1 name, K2 statement, K3 goal state, K4
tactic chain).

## Results policy: S3-only

Every lane's results are spooled to S3, never accumulated locally for the
long term. Bucket `smolbench-results-414266451290`, region `us-west-2`,
key layout `deduction/runs/scaling_<spec-key>/<relative path>` (e.g.
`deduction/runs/scaling_glm-4.7/all_rows.jsonl`) -- but that prefix is the
PUBLISHED pre-cutoff study's location and must never be written again. New
runs against the post-cutoff corpus spool under
`deduction_postcutoff/runs/scaling_<spec-key>/<relative path>` instead
(`smolbench.deduction.lean.runner.DEDUCTION_SPOOL_PREFIX`, resolved per call
by `runner.spool_prefix()` and overridable via `LEAN_SPOOL_PREFIX`);
`spool_prefix()` refuses to resolve back to `deduction/runs` unless
`LEAN_ALLOW_LEGACY_PREFIX=1` is set, since overwriting it would silently
destroy the unrecoverable published record. `deduction/runs` itself is
retained read-only, for analysis of the published study only.

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

Lean verification is deliberately deferred to a separate pass: it is a
separate, slow, Lean-touching step that runs later against a downloaded
`all_rows.jsonl`, so generation boxes never need `lean-interact`, elan, or a
built mathlib4 checkout.

The verification backend is the PyPI package `lean-interact`, which drives a
[`leanprover-community/repl`](https://github.com/leanprover-community/repl)
session (`smolbench.deduction.lean.replbackend`). It is not LeanDojo's `Dojo`:
LeanDojo v1's interaction layer is deprecated and cannot drive Lean >= v4.20,
while the post-cutoff corpus is mathlib4 at Lean v4.34.0-rc2, so `Dojo` cannot
reach it at all.

Verification therefore needs three things on the box that runs phase 2:
`elan` on `PATH`, a mathlib4 checkout that has actually been BUILT with
`elan`/`lake`, and `SMOLBENCH_MATHLIB_ROOT` set to that checkout:

```
SMOLBENCH_MATHLIB_ROOT=/path/to/mathlib4 \
  .venv/bin/python scripts/deduction/lean_verify_rows.py --runs 'scaling_glm-4.7*'
```

The variable is read at CALL time (`replbackend.mathlib_root`), never cached at
import, so setting it late still takes effect. Verification no longer needs the
`~/.cache/lean_dojo/` traced-corpus download at all. That cache is NOT obsolete
repo-wide, though: `smolbench.deduction.lean.premises`'s source slicing still
resolves `~/.cache/lean_dojo/leanprover-community-mathlib4-<commit>/mathlib4`
(`premises._traced_root`) to render hint/noise context, and `lean-dojo` remains
a declared dependency of the `lean` extra for corpus tracing and premise
slicing. Only VERIFICATION has stopped depending on it.

**Limitation, stated plainly: the elaboration environment is import-only.**
`replbackend.open_session` builds the environment for a theorem's statement with
a single `import <Module>` of the theorem's own module. That restores the
module's *imports* but NOT its file-level `open` / `variable` / `namespace`
scope, nor any `local notation`. A statement that depends on such scope fails to
elaborate and is reported as `exception` (or `replay_failed` when it happens
under a prefix replay -- and phase 2's cell rows always show `replay_failed`
regardless; see trap 1 below). Re-elaborating the whole file prefix up to the
declaration would be correct but much more expensive; the spec chose cost. See
`replbackend.py`'s module docstring, which also records that no part of the REPL
interaction has been exercised against a real Lean toolchain.

- **Phase 1 (generation)** runs on `.venv`. `notebooks/deduction/run_study.py`
  calls a model, extracts a candidate tactic block, and writes each cell row
  with `verdict == "unverified"` (a placeholder -- nothing has been checked
  against Lean yet) and each per-theorem sanity row with `verdict ==
  "skipped"`. By default it uses `NullVerifier` (`LEAN_VERIFY=defer`), which
  never imports `smolbench.deduction.lean.verify` or its `lean_interact`
  dependency. Once verification (below) assigns a real verdict, a candidate
  that extracted to zero tactic lines (typically a reasoning model truncated
  mid-`<think>`) is graded `no_answer`, not `lean_error`: Lean never saw a
  tactic to reject, so it must not read as "the model wrote a wrong proof."
- **Phase 2 (verification)** also runs on `.venv`, via
  `scripts/deduction/lean_verify_rows.py`. It downloads a run's
  `all_rows.jsonl` from S3, replays every recorded candidate proof against a
  real REPL session, and uploads `verified_rows.jsonl` beside it --
  **the original `all_rows.jsonl` is never modified or re-uploaded**; every
  write goes to the sibling `verified_rows.jsonl` key so a verification bug
  can never corrupt or lose a candidate proof that already cost real
  inference spend to collect. Typical invocation (see that script's own
  module docstring and `--help` for the full flag set):

  ```
  .venv/bin/python scripts/deduction/lean_verify_rows.py --dry-run
  .venv/bin/python scripts/deduction/lean_verify_rows.py --runs 'scaling_glm-4.7*'
  ```

### Two traps in phase 2, both of which fail SILENTLY

**1. `SMOLBENCH_MATHLIB_ROOT` and `elan` must both be right, or the whole pass
"verifies" nothing.**

- **`SMOLBENCH_MATHLIB_ROOT` unset (or pointing at a directory that is missing,
  or has no `lean-toolchain`)** stops every session before a Lean process is
  even started, with a message naming `SMOLBENCH_MATHLIB_ROOT` verbatim -- grep
  the `lean_error` column for that string, it is the fastest positive
  identification of this trap.

  **The verdict differs by row kind, and the cell rows are misleading.** At the
  `smolbench.deduction.lean.verify` boundary this is deliberately an
  `exception`, never a `replay_failed`: `replay_failed` means "the RECORDED
  ground-truth prefix does not replay", a claim about the CORPUS, and a
  forgotten environment variable must not condemn all 300 ground-truth proofs.
  `replbackend.open_session` translates `mathlib_root`'s `RuntimeError` into a
  `ReplError`, which is deliberately NOT a `RuntimeError` subclass, so
  `verify.verify_proof_tail`'s `except RuntimeError` clause cannot catch it
  (pinned by `tests/deduction/test_lean_repl_verifier.py`). The per-theorem
  SANITY rows, which go through `verify.replay_ground_truth`, therefore land on
  `exception` as intended.

  The per-cell rows do NOT. `lean_verify_rows.py` drives a group through
  `verify.open_at_step` directly, and its group-level handler records
  `verdict == "replay_failed"` for every failure that is not a `RuntimeError`
  whose message begins `prefix tactic ` -- so the `ReplError` carrying the
  `SMOLBENCH_MATHLIB_ROOT` message is flattened into `replay_failed` with
  `dojo_failure_hint`'s text attached. That hint text is itself stale (it still
  talks about a LeanDojo traced-corpus pull and advises deleting
  `~/.cache/lean_dojo`, neither of which is relevant to this backend). Both are
  known follow-ups. Until they are fixed: **read the sanity rows, not the cell
  rows, to tell a misconfigured box from a genuinely unreplayable corpus.**
- **`elan` missing from `PATH`** fails later, when the REPL process itself is
  started, and only after `open_session`'s retry backoff has been spent on each
  group -- so the tell is a pass that is slow AND barren rather than fast and
  barren. It reaches the same group-level handler, so it too lands on
  `replay_failed` for cell rows. (Exactly which exception `lean-interact` raises
  for a missing `elan` has not been observed: no box in this project's CI has a
  Lean toolchain.) Under a non-login shell (`ssh cmd`, SSM
  `AWS-RunShellScript`, cron) `/root/.elan/bin` is absent from `PATH`. Always:

  ```
  export PATH=/root/.elan/bin:$PATH
  ```

Other tells of a broken pass, independent of which of the two it is: no `repl`
or `lake` processes alive, one Python process pinned at ~100% CPU (rather than
the worker count), and implausible throughput.

**2. Resume is keyed on GROUPS, not on the proofs inside them.** If phase 1
regenerated a lane after it was verified, every `(theorem_id, k)` group still looks
done while the candidate proofs beneath are completely different, so the pass reports
`0 to process` and leaves `verified_rows.jsonl` describing text that no longer exists.
Use `--no-resume` for any regenerated lane, and archive the superseded file first.
Compare `all_rows.jsonl`'s LastModified against `verified_rows.jsonl`'s to find them.

**Gate on the verdicts, not on the exit status.** A healthy pass writes a mix of
`success` / `lean_error` / `no_answer` (the last for a candidate that split to
zero tactic lines -- a real miss, but not a Lean rejection) with
`verify_ms > 0`. A broken one writes
`replay_failed` almost everywhere with `verify_ms == 0` and a REPL-open error
attached -- read that error rather than the verdict, per trap 1: one naming
`SMOLBENCH_MATHLIB_ROOT` is a misconfigured box, one quoting Lean's own messages
about an unresolved identifier or notation is most likely the import-only
environment limitation described in "Generation -> verification split", and only
one shaped `prefix tactic ... -> ...` is a genuine ground-truth replay failure.
Cross-check against the sanity rows, whose verdicts are not flattened.

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
  supervisor (`scripts/fleet/run_fleet.py`), a lane's box is reused across the
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

## Replicate terminology

The replication axis is called **replicates**: `n_replicates` in a sweep
config, `replicate_idx` on a result row. Use that word exclusively in this
study's code, notebooks, and documentation.

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
- **The `novel_premises` split kind, post-cutoff.** The PRE-CUTOFF study's
  pool selector was fixed to `kind == "novel_premises"` (the harder
  generalization slice; see "History: the pre-cutoff study" above). That is
  now backwards: the re-collection's post-cutoff corpus has a single
  meaningful split family -- `build_postcutoff_corpus.py` writes a
  `novel_premises/` directory too, but as a real copy of `random/`'s rows,
  not an independent curated slice (see "Data layout" above) -- so
  `run_study.build_config` now reads `random`/`val` by default
  (`LEAN_CORPUS_KIND`/`LEAN_CORPUS_SPLIT`), and `random` IS what every sweep
  this study runs draws from.
- **Live REPL interaction during generation.** Everything in this
  study's generation phase (`run_study.py`, and by extension
  `lean_eval.ipynb`'s cells) uses `NullVerifier` by default and therefore
  never imports `smolbench.deduction.lean.verify` or opens a real REPL
  session -- see "Generation -> verification split" above.

## Results and data

`results/` and `data/` are not in this tree; see `notebooks/ARCHIVE.md`
for where they live and how to restore or regenerate each.
