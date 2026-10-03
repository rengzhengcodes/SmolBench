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
- To run the induction study: AWS credentials that can launch GPU spot instances on EC2
  and write to an S3 bucket you own. Rebuilding the induction table needs no credentials.

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

## Rebuild the induction table without a model

The paper's induction accuracy table (`tab:induction-results`) is computed from 1,440
result files: 16 models, 3 conditions, and 30 seeds. They are in the public bucket
`s3://smolbench-public-release`, which anyone can read without AWS credentials.

1. Install the notebook dependencies:

   ```
   uv sync --extra notebook
   ```

1. Run `notebooks/induction/induction_results_table.ipynb` with the `.venv` kernel, or
   headless:

   ```
   uv run --with nbconvert --with ipykernel jupyter nbconvert --to notebook --execute --inplace \
       notebooks/induction/induction_results_table.ipynb
   ```

   This downloads about 1.1 GB and takes about a minute.

The notebook prints the table in LaTeX three times, with the ± as one standard deviation
across seeds (the published table), two standard deviations, and the 95% confidence
interval for the mean. Its last cell checks every published value and prints
`all 80 cells match the published table`.

## Run the induction study on a model

The driver, `notebooks/induction/run_study.py`, runs only on EC2. It launches a GPU spot
instance (`p5e.48xlarge` or `p5.48xlarge` by default), serves each model on it with vLLM,
and writes one result file per model, seed, and condition. It runs the `zero` condition
too, which the table leaves out.

1. Install the dependencies:

   ```
   uv sync --extra notebook
   ```

1. Create an S3 bucket for the results.

1. Write `notebooks/induction/keys.env`. Keep it out of git. To run the table's 16
   models:

   ```
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   AWS_REGION=us-west-2
   SMOLBENCH_RESULTS_S3=s3://<your-bucket>
   INDUCTION_MODELS=gemma-4-e2b,gemma-4-12b,gemma-4-31b,nemotron-3-nano-4b,nemotron-3-nano-30b-a3b,nemotron-3-super-120b-a12b,qwen3.5-27b,qwen3.5-122b-a10b,qwen3.5-397b-a17b,deepseek-v4-flash,deepseek-v3.1,glm-4.7-flash,glm-4.7,ministral-3-3b,ministral-3-8b,ministral-3-14b
   ```

   Give `SMOLBENCH_RESULTS_S3` no path, so the result keys start with `induction/` as
   the notebook expects. Without it, results are written under
   `notebooks/induction/results/` instead, which the notebook does not read. Leave out
   `INDUCTION_MODELS` to run the whole roster in `smolbench/evals/study_config.toml`.
   The module docstring of `run_study.py` lists the other settings.

1. Run the study:

   ```
   python notebooks/induction/run_study.py
   ```

   If it stops, rerun the same command. It runs only the replicates that have no result
   yet.

1. Terminate the instance:

   ```
   python notebooks/induction/run_study.py --teardown
   ```

1. In the first code cell of `notebooks/induction/induction_results_table.ipynb`, set
   `BUCKET` and `REGION` to your bucket, then run the notebook as above. Reads from your
   bucket use your AWS credentials.

Each request carries its replicate's seed, but vLLM does not guarantee identical outputs
across runs, so your table can differ from the published one. The notebook's last cell
then fails and lists the cells that differ.

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
| `smolbench/induction/` | The induction task generator |
| `smolbench/deduction/horn/` | The Horn benchmark: theory generator, arms, checker, scoring modes, statistics, reproduction CLI, and `iclr.json` |
| `scripts/deduction/horn/` | Sweep drivers for vLLM and Bedrock, chain-length calibration, and the demo |
| `notebooks/induction/` | The induction study driver and the induction table notebook |
| `notebooks/deduction/analysis/` | Horn tables and figures |
| `tests/` | The test suite |

The Lean 4 deduction study, the cloud run tooling, and the Horn design notes are not on
this branch. They are on the `extras` branch.
