# Evaluations

Evaluation infrastructure for OpenAI-compatible providers, AWS Bedrock/SageMaker, and EC2 vLLM.
Select the call-time provider with `INFERENCE_PROVIDER`; import `query`/`evaluate` from `provider.py`.

## Layout

```
smolbench/evals/
  __init__.py       re-exports quiz.py's datamodel
  quiz.py           QnA / ToF / Numeric / Quiz / Mark / Marks
  openai_compat.py  shared HTTP and parsing engine
  provider.py       call-time provider registry
  providers/        openrouter.py primeintellect.py aws.py ec2.py
  _aws.py           shared AWS primitives
  parsing.py  tokenization.py  replicates.py  results_store.py
  study_config.py   loads study_config.toml
  study_config.toml committed results bucket/fleet/roster config
  payloads/         byte-exact EC2 assets
```

`provider.py` stays outside `providers/` to avoid inverted dependencies. It imports one backend at call time, so importing the package cannot freeze EC2 environment settings. `payloads/` and `study_config.toml` paths are package-data anchors; `.gitattributes` pins `payloads/` to LF bytes.

## Results store

`results_store.py` writes replicate YAMLs locally by default or to S3 when `SMOLBENCH_RESULTS_S3` is set. It reads this setting at call time because notebooks load environment files after imports. S3 falls back to local outside `repo_root()` to keep `tmp_path` tests hermetic.

```
<base-prefix>/<experiment>/<model>/seed=<seed>/<info>--<run_ts>.yaml
induction/gemma-4-12b/seed=0/extens--20260810T193000Z.yaml
```

`run_ts` is shared by one seed collection and sorts chronologically, enabling earliest-wins reads.

### Syncing down for analysis

`ReplicateHarness.sync_down()` translates S3 records to the local analysis layout. Supply model tags outside a notebook:

```
python -m smolbench.evals.results_store notebooks/induction/results --tag gpt-oss-120b=moe
```

`--tag model=tag` is repeatable; `--prefix one_hop_` supplies a harness prefix. Run this before analysis: analysis scripts read local trees. Sync is one-way and overwrites matching local paths.

## Provisioning the bucket

`scripts/results/provision_results_bucket.py` idempotently provisions the configured bucket, public-access blocks, versioning, and `SmolbenchResultsBucketRW`. It requires admin credentials; day-to-day EC2 operator credentials cannot manage S3 or IAM.
