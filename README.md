# SmolBench

SmolBench measures how positive-utility context representation affects LLM performance.

- **Induction** (`smolbench/induction/`): generalized FizzBuzz rule inference comparing an intensional (compact rule) representation with an extensional (fully enumerated) one and token-matched noise contexts.
- **Horn** (`smolbench/deduction/horn/`): the `lem`, `pad`, `disc`, and `both` arms test whether adding relevant context harms a prover more than the same amount of irrelevant text.

## Package layout

Each subsystem has its own README with full detail.

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
    parsing.py, replicates.py, results_store.py
  induction/                the periodic benchmark (see smolbench/induction/README.md)
    _common.py                generation machinery
    periodic.py                the benchmark family
    experiment.py              thin InductionExperiment(Experiment) subclass
  deduction/horn/           the Horn-clause benchmark
    checker.py, cli.py, extract.py, render.py
    repro.py, score.py, stats.py, theory.py

notebooks/                 experiment drivers and analysis, one directory per study (see notebooks/README.md)
  induction/                family-ladder induction study (see notebooks/induction/README.md)
    run_study.py, induction_eval.ipynb   the driver and its notebook
    analysis/                  power, paired, significance, extens-vs-noise, all run by run_all.py
  deduction/                Horn benchmark
    horn_results.ipynb
    HORN_BOTH_VS_PAD.md, HORN_RELEVANCE_DESIGNS.md, HORN_ROSTER_PLAN.md
    analysis/horn_reasoning_figure.py, horn_results.py, horn_routes.py
  statistical_analyses.ipynb  this study's cross-cutting statistics
  notebook_stats.py           induction posterior-power and bootstrap estimators
  _power_common.py           shared induction power-analysis scaffolding
  ARCHIVE.md                 where historical artifacts live, and what is regenerable

scripts/                   operational scripts, grouped by job (see scripts/README.md)
  fleet/                     launch and babysit the 21-lane EC2 fleet
    run_fleet.py                 the CLI entry point
    _config.py                   fleet-wide constants and the shared by-path loader
    lane_env.py                  roster tables, and one lane's environment and argv
    supervisor.py                the launch/monitor/restart/gate/shutdown loop
    policy.py                    the shared restart vocabulary
    shards.py                    one supervised shard of a direct driver run
    run_shards.py                babysits supervisor-less shard fleets
    fleet_status.py              read-only fleet listing
    fleet_teardown.py            lists, and with --terminate ends, the instances
  deduction/horn/             Horn sweep, calibration, and repro drivers
    sweep.py, bedrock_sweep.py, calibrate_m.py, calibration_pick.py
    build_iclr_protocol.py, demo.py, render_rung.sh, rows_contrast.py
  results/                   results-store admin: provisioning, audits, manifests
  smoke/                     live-AWS smoke tests (spend real money -- opt-in only)
  arch/                      the model-architecture facts pipeline (see scripts/arch/README.md)

tests/                     the offline pytest suite (see tests/README.md), zero AWS credentials needed
  analysis/                  synthetic result trees driving the analysis report scripts
  evals/                     provider round trips against a local stub server
  induction/                 golden quiz regressions, token-matching
  deduction/                 Horn benchmark tests
    test_horn_bench.py, test_horn_extract.py, test_horn_repro.py, test_horn_sweep.py
  tooling/                   fleet/evidence/bucket/arch cross-study contracts
  fixtures/                  shared fixtures (golden quizzes, roster configs)
```

### Where do I go?

| I want to... | Go to |
| --- | --- |
| Run a study | `notebooks/<study>/run_study.py` |
| Reproduce a published number | Induction: `notebooks/induction/analysis/run_all.py`. Horn: `python -m smolbench.deduction.horn.repro models` |
| Operate the EC2 fleet | `scripts/fleet/` |
| Verify, merge, or audit results | `scripts/results/` (bucket admin, regrade, completeness, evidence manifest) |
| Add or change an inference provider | `smolbench/evals/providers/` |
| Find or add a test | `tests/<group>/` (`evals`, `induction`, `deduction`, `tooling`) |

## Install

`.python-version` pins Python 3.12.

```bash
uv sync --all-extras
```

The optional extras defined in `pyproject.toml` are `dev`, `aws`, `lean`, and `notebook`.

## Run the tests

```bash
.venv/bin/python -m pytest tests/ -q          # offline suite, zero credentials
```

The suite uses a local OpenAI-compatible stub and needs no AWS credentials.
