# SmolBench

SmolBench measures how positive-utility context representation affects LLM performance.

- **Induction** (`smolbench/induction/`): generalized FizzBuzz rule inference with compact, enumerated, and token-matched noise contexts.
- **Deduction** (`smolbench/deduction/lean/`): Lean 4 next-tactic completion as proof-state and premise context grows.

## Package layout

Repository map.

```
smolbench/                 the installable library
  evals/                   shared eval infrastructure (see smolbench/evals/README.md)
    providers/               one module per inference backend
    payloads/                byte-frozen on-instance assets for providers/ec2.py
    experiment.py            the provision/run/agent_status/teardown facade
    study_config.py          loads study_config.toml
    study_config.toml        the one source: results bucket/region, fleet regions, roster
    quiz.py                  the QnA/ToF/Numeric/Quiz/Mark/Marks datamodel
    provider.py              name -> provider module registry
    openai_compat.py         the shared HTTP + response-parsing engine
    _aws.py                  the shared AWS primitives
    tokenization.py          text/token helpers, incl. the noise-pad search
    parsing.py, replicates.py, results_store.py, retired_markers.py, s3_archive.py
  induction/                the periodic benchmark (see smolbench/induction/README.md)
    _common.py                generation machinery
    periodic.py                the benchmark family
    experiment.py              thin InductionExperiment(Experiment) subclass
  deduction/lean/           the Lean 4 theorem-proving benchmark
    corpus.py, premises.py, context.py, prompt.py   corpus loading + prompt rendering
    runner.py, verify.py, replbackend.py            the sweep runner and lean-interact verification
    decontam.py, decontam_config.py                 near-duplicate filtering + its policy loader
    decontam_config.toml                            the MinHash/LSH params and key floor
    lean3.py, nullverify.py, cli.py

notebooks/                 experiment drivers and analysis, one directory per study (see notebooks/README.md)
  induction/                family-ladder induction study (see notebooks/induction/README.md)
    run_study.py, induction_eval.ipynb   the driver and its notebook
    analysis/                  power, paired, significance, extens-vs-noise, all run by run_all.py
  deduction/                family-ladder Lean deduction study (see notebooks/deduction/README.md)
    run_study.py, lean_eval.ipynb        the generation-only driver and its notebook
    sweep.yaml                           the sweep config, sha256-pinned into each run's manifest
    analysis/                  power, error bars, hint-vs-noise; rows_source.py is the shared reader
  statistical_analyses.ipynb  this study's cross-cutting statistics
  _power_common.py           stats helpers both studies' analysis scripts import
  ARCHIVE.md                 where historical artifacts live, and what is regenerable

scripts/                   operational scripts, grouped by job (see scripts/README.md)
  fleet/                     launch and babysit the 21-lane EC2 fleet
    run_fleet.py                 the CLI entry point
    _config.py                   fleet-wide constants and the shared by-path loader
    lane_env.py                  roster tables, and one lane's environment and argv
    supervisor.py                the launch/monitor/restart/gate/spool loop
    policy.py                    the shared restart vocabulary
    shards.py                    one supervised shard of a direct driver run
    run_shards.py                babysits supervisor-less shard fleets
    fleet_status.py              read-only fleet listing
    fleet_teardown.py            lists, and with --terminate ends, the instances
  deduction/                 Lean run sharding, merging, and the deferred verify pass
  results/                   results-store admin: provisioning, audits, manifests, regrade.py
  smoke/                     live-AWS smoke tests (spend real money -- opt-in only)
  arch/                      the model-architecture facts pipeline (see scripts/arch/README.md)

tests/                     the offline pytest suite (see tests/README.md), zero AWS credentials needed
  analysis/                  synthetic result trees driving the analysis report scripts
  evals/                     provider round trips against a local stub server
  induction/                 golden quiz regressions, token-matching
  deduction/                 Lean corpus/context/prompt/runner/verify, S3 archive pins
  tooling/                   fleet/evidence/bucket/arch cross-study contracts
  fixtures/                  shared fixtures (golden quizzes, lean_mini corpus, roster configs)
```

### Where do I go?

| I want to... | Go to |
| --- | --- |
| Run a study | `notebooks/<study>/run_study.py` |
| Reproduce a published number | Induction: `notebooks/induction/analysis/run_all.py`. Deduction: the `notebooks/deduction/analysis/` scripts' `--s3` readers. Or `notebooks/statistical_analyses.ipynb` |
| Operate the EC2 fleet | `scripts/fleet/` |
| Verify, merge, or audit results | `scripts/deduction/` (Lean verify/shard/merge), `scripts/results/` (bucket admin, regrade, completeness, evidence manifest) |
| Add or change an inference provider | `smolbench/evals/providers/` |
| Find or add a test | `tests/<group>/` (`evals`, `induction`, `deduction`, `tooling`) |

## Install

Install the Python 3.12 environment; `lean-dojo` pins `Requires-Python <3.13`.

```bash
uv sync --all-extras
```

This installs `lean-interact` for verification; `lean-dojo` remains for corpus tracing and premise slicing.

Extras: `dev`, `aws`, `lean`, and `notebook`. Base dependencies are Python 3.12, `joblib`, `numpy`, `ordered-set`, `requests`, `huggingface-hub`, and `tokenizers`.

## Run the tests

```bash
.venv/bin/python -m pytest tests/ -q          # offline suite, zero credentials
```

The suite uses a local OpenAI-compatible stub, so it needs no AWS credentials or network access. This prints `1204 passed, 5 skipped`.

All 5 skips are `tests/deduction/test_s3_archive.py`: archived S3 evidence requires `SMOLBENCH_ARCHIVE_S3`. `notebooks/ARCHIVE.md` documents `## S3` and archive sha256s.
