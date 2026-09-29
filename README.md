# SmolBench

A benchmark for smol manipulation of language: evaluating how representations of positive
utility information in context can impact LLM performance.

This branch holds the code needed to reproduce the Horn-rule deduction results of the
ICLR 2027 submission: generate the benchmark from seeds, run models on it, score the
answers, and build the tables and figures. The rest of the project (the Lean 4 deduction
study, cloud run tooling, pilot harnesses and design notes) is on the `extras` branch.

## Install

```
uv sync                   # Python 3.12; add --extra aws for AWS Bedrock runs, --extra dev for tests
```

## Build the tables and figures from the released results

The released results folder holds every model output and verdict behind the paper's
Horn table: 16 models x 4 arms x 100 theories x 3 replicates, with full generations.

```
python notebooks/deduction/analysis/make_figures.py --data <results folder> --out results
```

This checks the folder's checksums and writes every Horn table and figure to
`results/iclr/` (scored as submitted) and `results/default/` (the default extractor;
`smolbench/deduction/horn/README.md`, section 5, describes the two scoring modes).

## Check the pipeline without a model

```
python scripts/deduction/horn/demo.py --out /tmp/horn_demo
```

The demo renders a small benchmark, serves correct proofs from a local stub server, runs the
sweep driver under both scoring modes, and prints the report.

## Run the experiments again

```
python -m smolbench.deduction.horn.repro models                                  # models and chain lengths
python -m smolbench.deduction.horn.repro render --model glm-4.7 --out rungs/m48  # prompts, checked against the served ones
python -m smolbench.deduction.horn.repro command --model glm-4.7 --rung rungs/m48 --out rows.jsonl
python -m smolbench.deduction.horn.repro report rows.jsonl                       # compare with the published values
```

Section 9 of `smolbench/deduction/horn/README.md` walks through each step.

## Layout

| path | contents |
|---|---|
| `smolbench/deduction/horn/` | the benchmark: theory generator, the four arms, checker, scoring modes, statistics, reproduction CLI, `iclr.json` (the recorded protocol) |
| `scripts/deduction/horn/` | sweep drivers for vLLM and AWS Bedrock, chain-length calibration, offline demo |
| `notebooks/deduction/analysis/` | tables and figures from the released results |
| `smolbench/evals/`, `smolbench/induction/` | shared model client and serving specs; the induction study |
| `tests/` | `pytest tests/` |
