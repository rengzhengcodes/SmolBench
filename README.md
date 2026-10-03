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
  models (see [Set up AWS](#set-up-aws)).
- The released induction results (1.1 GB), to rebuild the induction table. They are in
  the public bucket `s3://smolbench-public-release`, which needs no AWS credentials.
- To run the induction study: AWS credentials that can launch GPU spot instances on EC2
  and write to an S3 bucket you own (see [Set up AWS](#set-up-aws)).

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

## Set up AWS

The code provisions these resources on first use when your credentials permit it:

- In a launch region, `smolbench-inference` (`EC2_SECURITY_GROUP_NAME`) gets TCP
  ingress on ports 8000 and 9000 from the caller's current public IPv4 `/32`. Existing
  rules on a pre-existing group are not removed.
- Only when `EC2_S3_MODEL_CACHE` is set, the code creates the cache bucket if absent
  and the `smolbench-ec2-role` role/profile (`EC2_INSTANCE_ROLE_NAME`). The role gets
  list/read/write access to that cache bucket and `AmazonSSMManagedInstanceCore`.
- On SageMaker endpoint provisioning, the code creates `smolbench-sm-exec-role`
  (`SAGEMAKER_EXEC_ROLE_NAME`) and attaches `AmazonSageMakerFullAccess`.
- The AMI is resolved from the public Deep Learning AMI SSM parameter configured by
  `EC2_AMI_SSM_PARAM`.

What you set up yourself:

1. **Credentials and IAM.** For EC2 and the results store, boto3's standard credential
   chain is used with fresh sessions/clients, so updated credentials files apply on the
   next operation. First-time role creation needs `iam:CreateRole`,
   `iam:AttachRolePolicy`, `iam:PutRolePolicy`, `iam:CreateInstanceProfile`, and
   `iam:AddRoleToInstanceProfile`; the existing SageMaker-role path also calls
   `iam:GetRole`. For the EC2 model-cache path, `AccessDenied` on `iam:CreateRole`
   makes the code assume the role/profile already exist; that fallback does not apply
   to SageMaker role creation. Allow these EC2 actions:
   `ec2:DescribeInstances`, `ec2:DescribeSecurityGroups`, `ec2:DescribeVpcs`,
   `ec2:DescribeSubnets`, `ec2:DescribeSpotPriceHistory`,
   `ec2:DescribeInstanceTypeOfferings`, `ec2:DescribeInstanceAttribute`,
   `ec2:DescribeImages`, `ec2:DescribeCapacityReservations`, `ec2:RunInstances`,
   `ec2:TerminateInstances`, `ec2:CreateSecurityGroup`,
   `ec2:AuthorizeSecurityGroupIngress`, and `ec2:CreateTags` (`run_instances` uses
   `TagSpecifications`). Also allow `ssm:GetParameter`, `sts:GetCallerIdentity`, and
   `iam:PassRole` on `EC2_INSTANCE_ROLE_NAME` when the model cache is enabled. Results
   storage needs `s3:ListBucket`, `s3:GetObject`, and `s3:PutObject` on your results
   bucket (`ListBucket` on the bucket, `GetObject` and `PutObject` on its objects).
   SageMaker endpoint creation also needs `iam:PassRole` on
   `SAGEMAKER_EXEC_ROLE_NAME`. If the optional cache bucket must be created, the
   caller also needs `s3:CreateBucket`; its `HeadBucket` check uses `s3:ListBucket`.
2. **Networking.** Keep a default VPC with at least one subnet in every region you
   hunt. The provisioner looks up only the default VPC and its subnets; a region without
   either is skipped.
3. **GPU quota.** The default `EC2_INSTANCE_TYPES` are `p5e.48xlarge` and
   `p5.48xlarge`, each using 192 vCPUs. In each hunted region request a Spot P-instance
   vCPU quota of at least 192, or the On-Demand quota when `EC2_MARKET=on-demand`.
   The default regions come from `[fleet].regions` in
   `smolbench/evals/study_config.toml` with `AWS_REGION` prepended; override them with
   `EC2_REGIONS`.
4. **Results bucket.** Create your own S3 bucket with Block Public Access enabled and
   versioning enabled, or run
   `.venv/bin/python scripts/results/provision_results_bucket.py`.
   The script takes no arguments, resolves the bucket from `SMOLBENCH_RESULTS_S3` or
   `[results].bucket`, creates it in `us-west-2` (tolerating an existing bucket), enables
   all four public-access blocks and versioning, and creates or reuses the
   `SmolbenchResultsBucketRW` policy
   (`ListBucket`, `GetObject`, `PutObject`, and `DeleteObject`), and attaches it to the
   existing `smolbench-ec2-operators` IAM group. It needs administrator-scoped
   credentials; it does not create that group. To run the script, allow `s3:CreateBucket`,
   `s3:PutBucketPublicAccessBlock`, `s3:PutBucketVersioning`, `iam:CreatePolicy`,
   `iam:ListPolicies`, and `iam:AttachGroupPolicy`. Alternatively, provision the bucket
   yourself. Point the store at it with `SMOLBENCH_RESULTS_S3=s3://<your-bucket>` and
   `SMOLBENCH_RESULTS_S3_REGION`, or set `[results].bucket` and `[results].region` in
   `smolbench/evals/study_config.toml`.
5. **Optional settings.** `EC2_KEY_NAME` names an existing key pair for SSH;
   `HF_TOKEN` is needed only for gated models; `EC2_S3_MODEL_CACHE` is an `s3://` URI
   for the model-weight cache.
6. **Bedrock.** Enable access in the Bedrock console for the model IDs and regions
   listed in `smolbench/deduction/horn/iclr.json`. `bedrock_sweep.py` loads
   `AWS_BEARER_TOKEN_BEDROCK` (a Bedrock API key) from the repository-root `.env`, or
   uses boto3's standard chain, which needs Bedrock `InvokeModelWithResponseStream`
   access for its `converse_stream` call. For the evals client, set
   `INFERENCE_PROVIDER=aws` and provide `AWS_BEARER_TOKEN_BEDROCK` or
   `AWS_INFERENCE_API_KEY`.

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
   output is one sweep command (see [Set up AWS](#set-up-aws)).

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
| `induction_table.tex` | The paper table (accuracy per arm and the deltas against low density) under each ± |
| `induction_table.md` | The same tables in markdown, with the seeds per model |
| `induction_summary.json` | Every number in the tables |

`induction_table.tex` and `induction_table.md` hold the table three times, with the ± as
one sample standard deviation across seeds, two standard deviations, and the half-width
of the 95% t confidence interval for the mean. The submission's table was improperly
captioned: its ± is one sample standard deviation, as in the first table, and the
outputs open with a note saying so. The three LaTeX tables match the ones the earlier
table notebook printed, byte for byte.

## Run the induction study on a model

`smolbench/induction/iclr.json` records the protocol of the submission's runs: the
seeds, arms, each model's pinned checkpoint, a digest of each seed's published runs, and
the published accuracies. The `repro` commands read it.

The driver, `notebooks/induction/run_study.py`, runs only on EC2. It launches a GPU spot
instance (`p5e.48xlarge` or `p5.48xlarge` by default), serves each model on it with vLLM,
and writes one result file per model, seed, and arm to S3. It runs the `zero` arm too,
which the table leaves out.

1. List the models and their checkpoints:

   ```
   python -m smolbench.induction.repro models
   ```

1. Create an S3 bucket for the results (see [Set up AWS](#set-up-aws)), then write
   `notebooks/induction/keys.env`. Keep it out of git. To run one model:

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
   result yet. `scripts/fleet/run_fleet.py` runs the full roster as a supervised fleet
   instead (see `scripts/README.md`).

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
| `notebooks/induction/` | The induction study driver, its analysis chain, and the induction table |
| `notebooks/statistical_analyses.ipynb` | The induction study's cross-cutting statistics |
| `scripts/fleet/` | Launch and supervise the induction study's EC2 fleet |
| `scripts/results/` | Results-bucket provisioning, completeness audits, and analysis-data snapshots |
| `scripts/arch/` | The model-architecture facts pipeline |
| `notebooks/deduction/analysis/` | Horn tables and figures |
| `tests/` | The test suite |
