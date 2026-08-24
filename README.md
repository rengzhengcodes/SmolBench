# SmolBench

SmolBench is a benchmark suite for smol manipulation of language. It
measures how the representation of positive utility information in a
prompt's context affects LLM performance. Two families of benchmarks live
in this repository:

- **Induction** (`smolbench/induction/`): asks a model to infer a rule
  from examples. The `periodic` benchmark uses a generalized FizzBuzz
  sequence; the `chromatic` benchmark uses interval "sceptre handoff"
  sequences. Both compare an intensional (compact rule) representation
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

- `smolbench/induction/` -- the periodic and chromatic benchmarks, their
  shared generation machinery (`_common.py`), the replicated-evaluation and
  EC2-lifecycle facade (`experiment.py`), and analysis plotting helpers
  (`figures.py`).
- `smolbench/deduction/lean/` -- the Lean 4 theorem-proving benchmark:
  corpus loading, prompt rendering, the sweep runner, and verification
  against `lean-dojo`.
- `smolbench/evals/` -- shared evaluation infrastructure: inference
  providers (OpenRouter, Prime Intellect, AWS Bedrock/SageMaker, a
  self-provisioned EC2 spot instance running vLLM), response parsing,
  replicated-quiz orchestration, and the results store. See
  `smolbench/evals/README.md` for details.
- `notebooks/` -- experiment drivers and analysis notebooks/scripts for
  each study, plus their `results/` trees and `keys.env` provider
  credentials.
- `scripts/` -- standalone operational scripts: fleet provisioning and
  teardown, run-completeness audits, and other one-off tooling that does
  not belong inside the `smolbench` package.
- `tests/` -- the offline pytest suite: provider round trips against a
  local stub server, golden quiz regressions, EC2 payload checks, and more.
  None of it needs AWS credentials.

## Install

SmolBench uses `uv` for dependency management. Install the main
environment (`.venv`, Python 3.14) with:

```bash
uv sync --all-extras
```

The Lean verification path depends on `lean-dojo`, which pins
`Requires-Python <3.13` upstream, so it needs its own Python 3.12
environment (`.venv-lean`):

```bash
UV_PROJECT_ENVIRONMENT=.venv-lean uv sync --python 3.12 --extra lean --extra notebook --extra dev
```

`pyproject.toml` declares four optional extras: `dev` (pytest, linters),
`aws` (boto3/botocore, for the EC2 and SageMaker/Bedrock providers),
`lean` (the Lean theorem-proving stack), and `notebook` (matplotlib,
python-dotenv, and other notebook-only dependencies). `smolbench` itself
requires only Python 3.12+, `joblib`, `numpy`, `ordered-set`, `requests`,
`huggingface-hub`, and `tokenizers`.

## Run the tests

```bash
.venv/bin/python -m pytest tests/ -q          # offline suite, zero credentials
.venv-lean/bin/python -m pytest tests/ -q     # same suite on Python 3.12
```

The suite needs no AWS credentials or network access: it drives the real
quiz-generation, provider-dispatch, and grading code paths against a local
OpenAI-compatible stub server.
