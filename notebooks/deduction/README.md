# Deduction: family-ladder scaling study (Lean 4 next-tactic success)

`run_study.py` builds each lane from `sweep.yaml`; `lean_eval.ipynb` is for
exploration, not running cells. The driver is a per-lane subprocess launched from a
terminal; see `lean_eval.ipynb`'s "Fleet Launch" section.

## Layout

```
deduction/
  run_study.py           per-lane generation driver
  sweep.yaml             shared sweep settings
  lean_eval.ipynb        exploration notebook
  results/, data/        archived S3 mirrors
  analysis/              report scripts
```

`run_study.py` loads shared settings with `smolbench.deduction.lean.runner.load_sweep_config`,
overlays lane identity, and refuses a `sweep.yaml` that supplies identity keys or omits a knob.
It records the file SHA-256 and `runner.sweep` stores the resulting config in `manifest.json`,
so archived runs retain their settings.

Keep `notebooks/deduction/run_study.py` and `notebooks/deduction/results` at these paths:
`scripts/fleet/run_fleet.py`, `scripts/deduction/merge_lean_shards.py`, and `results_root()`
depend on them. Analysis siblings import by bare name; a process loading both study legs must give
each a unique `sys.modules` name because their module names collide.
Load order does not matter if each load first evicts a cached sibling owned by another
directory, as the `_load` helper in `tests/deduction/test_deduction_analysis_reports.py` does; see `notebooks/README.md`, "Sibling imports".

| File | Purpose |
| --- | --- |
| `rows_source.py` | Shared reader and S3 downloader; maps `<prefix>/scaling_<key>/verified_rows.jsonl` to `<dir>/<model>/verified_rows.jsonl`. |
| `power_analysis.py` | Paired McNemar and bootstrap analysis; uniquely falls back to `all_rows.jsonl`. |
| `error_bars.py` | Published block sign-flip error bars; this, not `power_analysis.py`, produces the published 14/21. The headline pool drops a cell whose every attempt was `exception`/`replay_failed` (an infrastructure fault); `--denominator count-as-failure` scores it 0 instead, and the other rule is always reported as a sensitivity row. `--recovery-dir` stays local-only, though those rows are archived under `<prefix>/dojoinit_recovery_<date>/<lane>/recovered_rows.jsonl`; that layout is neither `scaling_*` nor `verified_rows.jsonl`. |
| `hint_vs_noise.py` | Informative-rung-versus-noise comparison (default `hint:3` vs `noise:3`; `--info-rung`/`--noise-rung` pick another pair). A lane with no cell carrying both rungs exits non-zero rather than printing a null. |

`PILOT_2026-07.md` records the July 2026 pilot: defects found in review, how they were fixed here,
and the re-scored numbers (`pilot_2026-07/`).

## Data layout

The uncommitted corpus is `notebooks/deduction/data/leandojo_benchmark_4/`.
`scripts/deduction/build_postcutoff_corpus.py --out <root>` writes `corpus.jsonl`, provenance
`metadata.json`, `random/{train,val,test}.json`, and `licenses/`.
`replay_passing_<kind>_<split>.jsonl` sidecars contain proofs that replay; this study selects
`corpus.iter_replay_passing`.

Measure the active `random`/`val` pool instead of assuming a count:

```
.venv/bin/python -c "from smolbench.deduction.lean import corpus; print(len(list(corpus.iter_replay_passing('random','val'))))"
```

Build the post-cutoff corpus with `scripts/deduction/build_postcutoff_corpus.py` and set
`SMOLBENCH_LEAN_DATA`. Missing corpus files raise an actionable `FileNotFoundError`; generate
sidecars with `python -m smolbench.deduction.lean.cli filter --kind random --split val`
(about 70 minutes per split). Then write the derivation sidecar,
`python -m smolbench.deduction.lean.cli build-derivation-index`, so `hint:3` closures follow the
traced proofs' premise usage (exact for named usage) instead of a text scan; without it the index
is rebuilt in memory on every process start.

Check the export's premise coverage before building anything on it: the share of traced tactics
with a non-empty `annotated_tactic[1]` should be well above half. lean-dojo-v2 drops any premise
without a definition position, and Lean v4.34 reports none for constants imported from another
module, so an unpatched export keeps only same-file premises (16% of tactics on the first
`2ca39e62` export). `scripts/deduction/trace_mathlib_ec2.sh`'s shim phase patches that; such
premises then carry `def_pos: null`, which `premises.missing_trace_premises` accepts.

The driver requires a post-cutoff corpus because every roster checkpoint's knowledge cutoff postdates the reference trace, so a model may have memorised older theorems' proofs during training.

### Corpus date vs. model cutoffs

`runner._require_all_postcutoff` uses `is_postcutoff_corpus` to refuse an old corpus or row;
`ROSTER_LATEST_RELEASE` separately gates its date, and `build_postcutoff_corpus.py` builds it. `metadata.json` records the old/new commits and dates; each row has
`postcutoff`. A mismatched traced commit raises rather than silently accepting an incoherent corpus.

`runner._select_theorems` rejects a corpus or selected row without post-cutoff status. Before any
AWS call, `run_study.build_config` requires post-cutoff metadata and
`target_date >= ROSTER_LATEST_RELEASE` (`"2026-06-03"`), because weights cannot encode data
published after their release. `runner.sweep` rechecks both at sweep time.

## Results policy: S3-only

Results use `deduction_postcutoff/runs/scaling_<spec-key>/<relative path>`. `spool_to_s3`
verifies every upload by `ContentLength` and prunes only after all pass; it keeps `manifest.json`
so resume can identify a run without downloading the spool. Every lane's results are spooled to
S3, never accumulated locally for the long term: bucket `smolbench-results-414266451290`, region
`us-west-2`, with `smolbench.evals.spool.DEDUCTION_SPOOL_PREFIX` resolved per call by
`smolbench.evals.spool.spool_prefix()` and overridable via `LEAN_SPOOL_PREFIX`.

## Generation and verification

Generation defers Lean work, so its boxes need neither `lean-interact`, elan, nor mathlib.
Verification uses `lean-interact` with the community REPL; Dojo cannot drive Lean >= v4.20, while
this corpus uses Lean v4.34.0-rc2.

Verification requires `elan` on `PATH`, a built mathlib checkout, and `SMOLBENCH_MATHLIB_ROOT`:

```
SMOLBENCH_MATHLIB_ROOT=/path/to/mathlib4 \
  .venv/bin/python scripts/deduction/lean_verify_rows.py --runs 'scaling_glm-4.7*'
```

The variable is read at call time. Verification no longer needs the `~/.cache/lean_dojo/`
traced-corpus download at all. That cache is NOT obsolete repo-wide:
`premises` still uses `~/.cache/lean_dojo/` through `_traced_root` for hint/noise context. Only VERIFICATION has stopped depending on it.

The REPL environment imports the theorem's module, then replays the file's scope commands that
precede the theorem (`namespace`, `section`/`end`, `variable`, `open`, `universe`, `set_option`,
`include`/`omit`, `local` notation and `attribute [local ...]`; `@[expose] public section` becomes
`section`, `... in` forms are dropped) before the renamed stub. Under the module system every
mathlib theorem sits inside such scope, so a bare stub failed on the first unqualified name. The
REPL parses each `ProofStep` without the scoped notation those commands activate, so every tactic
is sent as `open scoped <namespaces> in <tactic>`. Leading attributes are stripped from the stub
(`to_additive` on a renamed lemma fails) and the declared name's dotted prefix is kept
(`IsSuccPrelimit.smolbenchTarget`) because that prefix opens a namespace for the body. A `where`
structure-instance proof has no single proof state and reports `exception`. Private lemmas of the
same file are not reachable through `import`, and Dojo-flattened nested tactics do not replay;
both report `replay_failed`/`exception` and `cli filter` excludes them.

Phase 1 writes `unverified` cells and `skipped` sanity rows through `NullVerifier`; an empty
extracted tactic is `no_answer`, not `lean_error`, because Lean never saw a tactic. Phase 2 writes
sibling `verified_rows.jsonl`; it never modifies `all_rows.jsonl`, so a verification bug cannot
lose paid candidate proofs. `--reverify-all` re-scores every group, including ones that already
carry a verdict, into a fresh `verified_rows.jsonl`; use it after a verifier change.

### Verdicts

| Verdict | Meaning | Scored |
| --- | --- | --- |
| `success` | Tail closed every goal. | 1 |
| `lean_error` | Lean rejected a tactic, or tactics remain after the goals closed. | 0 |
| `incomplete` | Tail ran clean but goals remain. | 0 |
| `given_up` | Tail contains `sorry`/`admit`. | 0 |
| `no_answer` | No tactic could be extracted from the completion. | 0 |
| `timeout` | Lean did not finish the candidate within the request timeout (a model failure: the candidate is too expensive to check). | 0 |
| `exception` | Infrastructure fault (REPL crashed, environment missing); the candidate was never judged. | dropped |
| `replay_failed` | The ground-truth prefix itself did not replay, so no candidate for that cell can be judged. | dropped |

Candidates are scored as whole tactic blocks: an indented continuation line or a leading `|`
belongs to the previous tactic, so a multi-line `calc`, `cases ... with`, or `conv` block is one
step. A REPL killed by a timeout is reopened at the checkpoint before the next candidate, so one
expensive candidate cannot poison the rest of its block.

`max_tokens: 32768` in `sweep.yaml` is the generation budget. A completion cut at that budget
shows in the `trunc` column of `analyze` (from `finish_reason`); it is scored on whatever tactic
it contains, so raise the budget before comparing reasoning models that run long.

### Phase-2 traps, both of which fail SILENTLY

`SMOLBENCH_MATHLIB_ROOT` and `elan` must be valid. A missing root produces an `exception` in
sanity rows but `replay_failed` in cell rows; inspect sanity rows so an environment error does not
condemn ground-truth proofs. `replbackend.open_session` translates `mathlib_root`'s `RuntimeError`
into a `ReplError`, deliberately not a `RuntimeError` subclass, so `verify.verify_proof_tail` cannot catch it; `tests/deduction/test_lean_repl_verifier.py` pins this.

The attached `dojo_failure_hint` is stale: its LeanDojo traced-corpus pull and advice to delete
`~/.cache/lean_dojo` do not apply to this backend. Missing elan fails after retry backoff; under a
non-login shell (`ssh cmd`, SSM `AWS-RunShellScript`, cron), `/root/.elan/bin` is absent from `PATH`. Always:

```
export PATH=/root/.elan/bin:$PATH
```

Resume is keyed by groups, not candidate proofs. Use `--no-resume` after regenerating a lane and
archive its superseded file; compare `all_rows.jsonl` and `verified_rows.jsonl` LastModified values.
Gate on verdicts, not exit status: a broken pass has widespread `replay_failed` with
`verify_ms == 0`. Never analyse unverified `all_rows.jsonl` success rates.

Other broken-pass tells are no live `repl` or `lake` processes, one Python process pinned near
100% CPU rather than the worker count, and implausible throughput. Only an error shaped `prefix tactic ... -> ...` is a genuine ground-truth replay failure; cross-check the unflattened sanity-row verdicts.

## Running one lane

```
LEAN_MODEL=<spec key> .venv/bin/python notebooks/deduction/run_study.py
```

`<spec key>` must be in `run_study.MODELS`. `--no-s3` leaves local rows. Use `--teardown` only
standalone: fleet reuses each box across legs and owns its lifecycle, so teardown would terminate a
box required by the supervisor.

## Replicate terminology

The replication axis is called replicates: `n_replicates` in a sweep config and `replicate_idx`
on a result row. Use that word exclusively in this study's code, notebooks, and documentation.

## Scope

The study uses replay-passing, tactic-traceable theorems and four rungs: `stepk:1`, `hint:2`,
`noise:3`, and `hint:3`. Generation uses `NullVerifier` and never opens a REPL. `results/` and
`data/` are archived; see `notebooks/ARCHIVE.md` for restoration or regeneration.

The documented rung universe is `stepk:0..2` and `hint:0..4`; `context.validate` also accepts
`hint`/`noise` through level 9. The transitive closure is uncapped (no token or premise limit), so
deep levels grow roughly threefold per hop and can exceed a model's context window; choose levels per
model from the measured prompt lengths (`PILOT_2026-07.md`, "Hint ladder length").

### Unflagged library block: `sig`, `proof`, `signoise`, `proofnoise`

The `hint` ladder names the MPI lemmas at the top of the prompt and appends their closure below, so
the model is told which entries matter. The library-block chains do not. `sig:N` and `proof:N`
render the `stepk:2` base plus one `## Library context` block holding the MPI lemmas and their
N-hop closure together, sorted in import order then line (every dependency precedes its
dependents; nothing marks the roots). `sig` shows each declaration's signature; `proof` shows its
full source with proof, so the two forms hold the same set of facts at two token densities.
`signoise:N` pads `sig:0` to `sig:N`'s prompt length (the hops as blank length); `proofnoise:N`
pads `sig:N` to `proof:N`'s (the proof bodies as blank length). `sig:0` versus `hint:1` is the
flagging comparison at near-equal length.
