# SmolBench

SmolBench measures how the way information is presented in a prompt affects a language
model's reasoning. It holds two studies:

- **Induction.** Models infer periodic patterns from either a compact rule or a list of
  examples. See `smolbench/induction/README.md`.
- **Horn-rule deduction.** Models prove a goal from a library of Horn rules. The library
  is shown compactly (high density), with every lemma's full derivation tree (low
  density), with length-matched irrelevant text, or with dead trees that can't be used. See
  `smolbench/deduction/horn/README.md`.

This page explains how to install the code and rebuild both tables from the released
results.

## Before you begin

You need Linux, Python 3.12, and [uv](https://docs.astral.sh/uv/) to install the
dependencies. Both result folders are in the public bucket
`s3://smolbench-public-release` and can be fetched without credentials:

- Horn: about 2.1 GB and 12,474 files.
- Induction: about 1.1 GB and 1,440 files.

## Install

Install the runtime dependencies with:

```
uv sync
```

To run the test suite, install the development dependencies:

```
uv sync --extra dev
```

The commands below assume the virtual environment is active
(`source .venv/bin/activate`), or that you prefix them with `uv run`.

## Rebuild the Horn tables and figures

1. Fetch the released results. The command writes the results folder directly, including
   `MANIFEST.json`; rerun it to resume an interrupted download.

   ```
   python -m smolbench.deduction.horn.repro fetch \
       --out path/to/smolbench-horn-data-v1
   ```

1. Check every file against the manifest:

   ```
   python -m smolbench.deduction.horn.repro check-data path/to/smolbench-horn-data-v1
   ```

1. Rebuild the tables and figures:

   ```
   python notebooks/deduction/analysis/make_figures.py \
       --data path/to/smolbench-horn-data-v1 --out results
   ```

   This takes about four minutes. The main outputs in `results/` are:

| File | Contents |
|---|---|
| `horn_table.tex` | Paper table: pass rates per arm and deltas against low density |
| `horn_table_full.tex`, `horn_table.md` | Full table, grouped by family |
| `horn_summary.json` | Every number in the tables |
| `horn_ladder_arms.pdf`, `horn_ladder_deltas.pdf` | Pass rates and deltas per model family |
| `horn_routes.pdf`, `horn_route_outcomes*.pdf` | How proofs used the derivation trees |
| `reasoning_length_increase.pdf` | Output length relative to the high-density arm |

The outputs match the submitted ones byte for byte, except for the creation date embedded
in each PDF.

## Rebuild the induction table

The released results hold 16 models, 3 arms, and 30 seeds, with one YAML file of 9 graded
answers per replicate.

1. Fetch the public results. Rerun the command to resume an interrupted download.

   ```
   python -m smolbench.induction.repro fetch --out path/to/smolbench-induction-data
   ```

1. Check the folder against the published runs:

   ```
   python -m smolbench.induction.repro check-data path/to/smolbench-induction-data
   ```

1. Build the table:

   ```
   python notebooks/induction/analysis/induction_results.py \
       --data path/to/smolbench-induction-data --out results/induction
   ```

   This takes about ten seconds, checks the folder again, writes the outputs, and prints
   how many cells match the published table.

| File | Contents |
|---|---|
| `induction_table.tex` | Paper table: accuracy per arm and deltas against low density under each ± |
| `induction_table.md` | The same tables in markdown, with the seeds per model |
| `induction_summary.json` | Every number in the tables |

`induction_table.tex` and `induction_table.md` hold the table three times, with the ± as
one sample standard deviation across seeds, two standard deviations, and the half-width
of the 95% t confidence interval for the mean. The submission's table was improperly
captioned: its ± is one sample standard deviation, as in the first table, and the
outputs open with a note saying so.

## Run the tests

```
uv sync --extra dev
.venv/bin/python -m pytest -q
```

The tests run offline and need no credentials; none of them access the network.

## Repository layout

| Path | Contents |
|---|---|
| `smolbench/public_release.py` | Anonymous fetch of released result files |
| `smolbench/induction/` | Induction protocol and result reproduction |
| `smolbench/deduction/horn/` | Horn theory, checker, scoring, statistics, and result reproduction |
| `notebooks/induction/analysis/` | Induction results table |
| `notebooks/deduction/analysis/` | Horn tables and figures |
| `tests/deduction/`, `tests/induction/` | Analysis and result-reproduction tests |
