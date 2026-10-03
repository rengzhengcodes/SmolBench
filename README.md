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

This page explains how to install the code and run the benchmarks yourself.

## Before you begin

You need the following:

- Linux with Python 3.12.
- [uv](https://docs.astral.sh/uv/) to install the dependencies.
- To run models yourself: a GPU server with [vLLM](https://docs.vllm.ai/) for
  self-hosted models, or AWS credentials with Amazon Bedrock access for Bedrock-hosted
  models (see [Set up AWS](#set-up-aws)).

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
   versioning enabled. Set `SMOLBENCH_RESULTS_S3=s3://<your-bucket>` and
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
and reference pass rates. The `repro` commands read it.

1. List the models and their chain lengths:

   ```
   python -m smolbench.deduction.horn.repro models
   ```

1. Get the model's prompts by rendering them from their seeds. The command checks every
   file against the prompts the model was served:

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

1. Compare your results with the protocol's recorded values:

   ```
   python -m smolbench.deduction.horn.repro report rows.jsonl
   ```

Sampling runs at temperature 0.7, so a rerun matches the protocol's recorded values up to
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

## Run the induction study

The induction driver is `notebooks/induction/run_study.py`. It provisions and serves
models on EC2 and writes results to S3. See [Set up AWS](#set-up-aws), then
`notebooks/induction/README.md` for how to configure and run it.

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
| `notebooks/induction/` | The induction study driver |
| `notebooks/deduction/analysis/` | Horn tables and figures |
| `tests/` | The test suite |
