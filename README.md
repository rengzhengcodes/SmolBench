# SmolBench

SmolBench measures how the way information is presented in a prompt affects a language
model's reasoning. It holds two studies:

- **Induction.** Models infer periodic patterns from either a compact rule or a list of
  examples. See `smolbench/induction/README.md`.
- **Horn-rule deduction.** Models prove a goal from a library of Horn rules. The library
  is shown compactly (high density), with every lemma's full derivation tree (low
  density), with length-matched irrelevant text, or with dead trees that can't be used.
  This is the deduction benchmark of the ICLR 2027 submission. See
  `smolbench/deduction/horn/README.md`.

This page explains how to install the code, rebuild the Horn and induction tables from the
released results, and run the benchmarks yourself.

## Before you begin

You need the following:

- Linux with Python 3.12.
- [uv](https://docs.astral.sh/uv/) to install the dependencies.
- The released Horn results folder, `smolbench-horn-data-v1` (2.1 GB), to rebuild the
  tables and figures without running any model.
- To run models yourself: a GPU server with [vLLM](https://docs.vllm.ai/) for
  self-hosted models, or AWS credentials with Amazon Bedrock access for Bedrock-hosted
  models.
- The released induction results (1.1 GB), to rebuild the induction table. They are in
  the public bucket `s3://smolbench-public-release`, which needs no AWS credentials.
- To run the induction study: AWS credentials that can launch GPU spot instances on EC2
  and write to an S3 bucket you own.

## Install

1. Clone the repository and change into it.
1. Install the dependencies:

   ```
   uv sync
   ```

   To run Bedrock-hosted models, add the `aws` extra. To run the tests, add the `dev`
   extra:

   ```
   uv sync --extra aws --extra dev
   ```

The commands on this page assume the virtual environment is active
(`source .venv/bin/activate`), or that you prefix them with `uv run`.

## Rebuild the Horn tables and figures

The results folder holds every prompt, model output, and verdict behind the paper's Horn
table: 16 models, 4 arms, 100 theories, and 3 replicates, with full generations. It also
holds the calibration runs that chose each model's chain length. The folder's
`README.md` describes its layout and fields.

1. Check the folder against its manifest of checksums:

   ```
   python -m smolbench.deduction.horn.repro check-data path/to/smolbench-horn-data-v1
   ```

   The command prints `OK` when every file matches.

1. Build the tables and figures:

   ```
   python notebooks/deduction/analysis/make_figures.py \
       --data path/to/smolbench-horn-data-v1 --out results
   ```

   This takes about four minutes. It writes the outputs twice, once per scoring mode:

   - `results/iclr/`: scored as in the submission.
   - `results/default/`: scored with the default proof extractor, which also reads
     proofs that have prose between their steps.

The main outputs in each directory are:

| File | Contents |
|---|---|
| `horn_table.tex` | The paper table: pass rates per arm and the deltas against low density |
| `horn_table_full.tex`, `horn_table.md` | The full table, grouped by family, with every arm |
| `horn_summary.json` | Every number in the tables |
| `horn_ladder_arms.pdf`, `horn_ladder_deltas.pdf` | Pass rates and deltas per model family |
| `horn_routes.pdf`, `horn_route_outcomes*.pdf` | How proofs used the derivation trees |
| `reasoning_length_increase.pdf` | Output length relative to the high-density arm |

The outputs match the submitted ones byte for byte, except for the creation date
embedded in each PDF.

## Check the pipeline without a model

The demo runs the whole Horn pipeline on your machine in a few seconds. It renders a
small benchmark, answers every prompt with a correct proof from a local stub server, runs
the sweep driver under both scoring modes, and prints the results:

```
python scripts/deduction/horn/demo.py --out /tmp/horn_demo
```

Every cell passes. To see how the two scoring modes differ, write a line of prose between
proof steps:

```
python scripts/deduction/horn/demo.py --out /tmp/horn_demo --style interleaved
```

The answers then fail under `iclr` scoring and pass under `default` scoring.

## Run the Horn benchmark on a model

`smolbench/deduction/horn/iclr.json` records the protocol of the submission's runs: the
seeds, replicates, sampling settings, each model's chain length and serving settings,
and the published pass rates. The `repro` commands read it.

1. List the models and their chain lengths:

   ```
   python -m smolbench.deduction.horn.repro models
   ```

1. Get the model's prompts. The results folder holds the served prompts in
   `horn/prompts/m<m>/`, where `m` is the chain length. To regenerate them from their
   seeds instead, render them; the command checks every file against the prompts the
   model was served:

   ```
   python -m smolbench.deduction.horn.repro render --model glm-4.7 --out rungs/m48
   ```

1. Print the commands that run the model with the submission's settings:

   ```
   python -m smolbench.deduction.horn.repro command \
       --model qwen3.5-27b --rung rungs/m64 --out rows.jsonl
   ```

   For a self-hosted model, the output has two commands. The first serves the pinned
   checkpoint with vLLM; the second runs the sweep against it. For a Bedrock model, the
   output is one sweep command, which uses your AWS credentials.

1. Run the printed commands. The sweep writes one JSONL row per cell. If it stops,
   rerun the same command to resume.

1. Compare your results with the published values:

   ```
   python -m smolbench.deduction.horn.repro report rows.jsonl
   ```

Sampling runs at temperature 0.7, so a rerun matches the published numbers up to
sampling noise, not row for row.

### Run a model outside the roster

Render a rung at any chain length, then point the sweep driver at any
OpenAI-compatible endpoint:

```
python -m smolbench.deduction.horn.cli render --seeds 100-199 --m 12 --out rungs/m12
python scripts/deduction/horn/sweep.py --endpoint http://localhost:8000/v1 \
    --model my-model --thinking on --rung-dir rungs/m12 --replicates 3 --out rows.jsonl
```

`scripts/deduction/horn/README.md` lists the sweep driver's options.

## Rebuild the induction table

The results folder holds every result file behind the paper's induction table: 16
models, 3 arms, and 30 seeds, one YAML file of 9 graded answers per replicate. Install
the dependencies with `uv sync --extra notebook` first.

1. Download the folder from the public bucket:

   ```
   python -m smolbench.induction.repro fetch --out path/to/smolbench-induction-data
   ```

   This downloads 1,440 files (about 1.1 GB). If it stops, rerun the same command.

1. Check the folder against the published runs:

   ```
   python -m smolbench.induction.repro check-data path/to/smolbench-induction-data
   ```

   The command prints `OK` when every replicate matches.

1. Build the table:

   ```
   python notebooks/induction/analysis/induction_results.py \
       --data path/to/smolbench-induction-data --out results/induction
   ```

   This takes about ten seconds. It checks the folder again, writes the outputs, and
   prints how many cells match the published table.

| File | Contents |
|---|---|
| `induction_table.tex` | The paper table: accuracy per arm and the deltas against low density |
| `induction_table.md` | The same table in markdown, with the seeds per model |
| `induction_summary.json` | Every number in the tables |

The ± is one sample standard deviation across seeds, as published. Pass `--spread 2sd`
for two standard deviations or `--spread ci` for the half-width of the 95% confidence
interval for the mean. `induction_table.tex` matches the submitted table byte for byte.

## Run the induction study on a model

`smolbench/induction/iclr.json` records the protocol of the submission's runs: the
seeds, arms, each model's pinned checkpoint, a digest of every published replicate, and
the published accuracies. The `repro` commands read it.

The driver, `notebooks/induction/run_study.py`, runs only on EC2. It launches a GPU spot
instance (`p5e.48xlarge` or `p5.48xlarge` by default), serves each model on it with vLLM,
and writes one result file per model, seed, and arm to S3. It runs the `zero` arm too,
which the table leaves out.

1. List the models and their checkpoints:

   ```
   python -m smolbench.induction.repro models
   ```

1. Create an S3 bucket for the results, then write `notebooks/induction/keys.env`. Keep
   it out of git. To run one model:

   ```
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   AWS_REGION=us-west-2
   SMOLBENCH_RESULTS_S3=s3://<your-bucket>
   INDUCTION_MODELS=glm-4.7
   ```

   `INDUCTION_MODELS` takes a comma-separated list. Leave it out to run the whole roster
   in `smolbench/evals/study_config.toml`, which also holds models outside the table.
   The module docstring of `run_study.py` lists the other settings.

1. Run the study, then terminate the instance:

   ```
   python notebooks/induction/run_study.py
   python notebooks/induction/run_study.py --teardown
   ```

   If the study stops, rerun the first command. It runs only the replicates that have no
   result yet.

1. Download your results. If `SMOLBENCH_RESULTS_S3` has a path, pass it as `--prefix`:

   ```
   python -m smolbench.induction.repro fetch --bucket <your-bucket> --out myrun
   ```

   Reads from your bucket use your AWS credentials.

1. Compare your results with the published values:

   ```
   python -m smolbench.induction.repro report myrun
   ```

   To build the table from them, run `induction_results.py --data myrun --skip-check`.

vLLM does not guarantee identical outputs across runs, so a rerun matches the published
numbers up to sampling noise, not replicate for replicate.

## Run the tests

```
uv sync --extra dev
python -m pytest tests/
```

The tests run offline. They use stub model servers and need no credentials.

## Repository layout

| Path | Contents |
|---|---|
| `smolbench/evals/` | Shared model client, serving specs, results storage, and tokenizers |
| `smolbench/induction/` | The induction task generator, reproduction CLI, and `iclr.json` |
| `smolbench/deduction/horn/` | The Horn benchmark: theory generator, arms, checker, scoring modes, statistics, reproduction CLI, and `iclr.json` |
| `scripts/deduction/horn/` | Sweep drivers for vLLM and Bedrock, chain-length calibration, and the demo |
| `notebooks/induction/` | The induction study driver |
| `notebooks/induction/analysis/` | The induction table |
| `notebooks/deduction/analysis/` | Horn tables and figures |
| `tests/` | The test suite |

The Lean 4 deduction study, the cloud run tooling, and the Horn design notes are not on
this branch. They are on the `extras` branch.
