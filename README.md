# SmolBench

SmolBench is a benchmark suite for smol manipulation of language. It
measures how the representation of positive utility information in a
prompt's context affects LLM performance. Two families of benchmarks live
in this repository:

- **Induction** (`smolbench/induction/`): asks a model to infer a rule
  from examples. The `periodic` benchmark uses a generalized FizzBuzz
  sequence, comparing an intensional (compact rule) representation
  against an extensional (fully enumerated) one, plus a token-matched
  noise-padded control. See `smolbench/induction/README.md` for the full
  task design.
- **Deduction** (`smolbench/deduction/lean/`): asks a model to derive a
  valid consequence from given premises, under fixed rules of inference.
  Its one experiment to date, the Lean 4 theorem-proving eval, measures
  next-tactic completion accuracy over LeanDojo Benchmark 4 / Mathlib4
  theorems as the model gets progressively more proof-state and premise
  context. See `notebooks/deduction/README.md` for the current study.

## Package layout

An annotated tree of the whole repository. Each subsystem has its own
README with the full detail; this section is the map.

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
    figures.py                 analysis plotting helpers
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
  induction/                 golden quiz regressions, figures, token-matching
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

SmolBench uses `uv` for dependency management. Install the environment
(`.venv`, Python 3.12, pinned by `.python-version` because `lean-dojo`
pins `Requires-Python <3.13`) with:

```bash
uv sync --all-extras
```

This builds a single `.venv` holding every extra, including the Lean
verification path's `lean-interact` dependency. `lean-dojo` is still
installed too, but for corpus tracing and premise slicing, not verification.

`pyproject.toml` declares four optional extras: `dev` (pytest, linters),
`aws` (boto3/botocore, for the EC2 and SageMaker/Bedrock providers),
`lean` (the Lean theorem-proving stack), and `notebook` (matplotlib,
python-dotenv, and other notebook-only dependencies). `smolbench` itself
requires only Python 3.12, `joblib`, `numpy`, `ordered-set`, `requests`,
`huggingface-hub`, and `tokenizers`.

## Run the tests

```bash
.venv/bin/python -m pytest tests/ -q          # offline suite, zero credentials
```

The suite needs no AWS credentials or network access: it drives the real
quiz-generation, provider-dispatch, and grading code paths against a local
OpenAI-compatible stub server. This prints `1204 passed, 5 skipped`.

All 5 skips are the same opt-in gate: `tests/deduction/test_s3_archive.py`
pins archived evidence that lives only on S3, so it skips unless
`SMOLBENCH_ARCHIVE_S3` is set. See `notebooks/ARCHIVE.md` under `## S3` for
the worked invocation, and its `## GitHub releases` section for the archive
sha256s.
