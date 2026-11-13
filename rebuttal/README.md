# Rebuttal: SmolBench on Amazon Bedrock

`bedrock_trio.ipynb` runs both studies on Amazon Bedrock with reasoning switched on: periodic
induction (arms `intens`, `noise_intens`, `extens`) and Horn-rule deduction (eight arms: the
paper arms `lem`, `pad`, `disc`, `both` and the review arms `fwd`, `tjunk`, `rep`,
`marked-lemma`). It runs them for three ladder models from three labs:

| roster key | lab | parameters | Horn `m` |
|---|---|---|---|
| `gemma-4-31b` | Google | 30.7B dense | 64 |
| `nemotron-3-super-120b-a12b` | NVIDIA | 120B MoE, 12B active | 20 |
| `deepseek-v3.1` | DeepSeek | 685B MoE, 37B active | 64 |

The notebook's first cell explains the choice and lists how these runs differ from the
ICLR runs: Bedrock's output caps, the induction temperature default, and seeding.

| File | Contents |
|---|---|
| `bedrock_trio.ipynb` | The notebook: authenticate, force reasoning, check prompts, run, report |
| `bedrock_trio.py` | Roster, endpoint switch, results store and reasoning checks over the existing run code |
| `results/` | Local mirror of the bucket (not committed), described below |
| `rungs/` | Rendered Horn rungs (not committed) |

## Results

The private bucket `s3://smolbench-rebuttals-414266451290/bedrock-trio` (`us-west-2`; Bedrock
inference stays in `us-east-1`) is the store of record. Objects are append-only: nothing is
overwritten or deleted, and a rerun adds new stamped keys.

| Key below the prefix | Contents |
|---|---|
| `induction/<model>/seed=<s>/<arm>--<stamp>.yaml` | One induction replicate, in the released-results layout |
| `deduction/horn/<model>/rows--<stamp>.jsonl` | A part of Horn rows: the rows one push added |
| `probes/probes--<stamp>.json` | Model ids and the reasoning fields each model accepted |

`results/` is a mirror that the report cells read: `results/induction/induction/<model>/seed=<s>/...`
(what `smolbench.induction.repro` reads), `results/horn/<model>.jsonl` (what
`smolbench.deduction.horn.repro report` reads) and `results/probes.json`. The notebook mirrors
at the end of a run and again before it reports, so a fresh checkout can report from the
bucket alone.

A run resumes from the bucket, not from the local files: a Horn run pulls the bucket's rows
before it picks the cells to run, and induction asks the bucket whether a replicate exists.
A run on a second machine therefore continues where the first stopped, without re-billing
finished work. Horn rows are pushed every 200 new rows and when the run ends; on an
interrupt the cells already running finish and their rows are kept and pushed.
`RESULTS_S3 = None` in the notebook keeps everything local.

A smoke run (`SMOKE = True`) writes under `bedrock-trio/smoke-2/` with the same layout and
mirrors to `results/smoke-2/`, so the protocol prefix only ever holds protocol runs.
`bedrock-trio/smoke/` holds the first smoke (2026-11-13). Its scores are valid, but the
non-ASCII characters of its stored reasoning and responses are mis-decoded (UTF-8 read as
ISO-8859-1; the stream reader is fixed since). Nothing reads that prefix.

## Caveats

- **Horn arms.** `horn_repro.report` gives contrasts for the four paper arms only; the four
  review arms appear in its per-arm pass rates and in the notebook's per-arm breakdown.
- **`extens`.** On this branch the `extens` context is the intensional rules followed by the
  listing. The published `extens` and `noise_intens` values come from the earlier arm, which
  carried the listing only, so only `intens` is like-for-like with the published values. The
  notebook's prompt check compares each arm with the released prompts in the way that
  matches this.

## Run

You need:
- AWS credentials that can call Bedrock in `us-east-1` and read and write the results
  bucket in `us-west-2`. A short-term bearer token is minted from them; an
  `AWS_BEARER_TOKEN_BEDROCK` already set is used instead.
- Access to the three models.
- The Hugging Face tokenizers. `google/gemma-4-31B-it` is gated, so set `HF_TOKEN` unless
  it is already cached.

```
uv sync --all-extras
.venv/bin/python -m ipykernel install --user --name smolbench
```

Open `rebuttal/bedrock_trio.ipynb` with the `smolbench` kernel, set `SMOKE`, and run all
cells. `SMOKE = True` runs 2 induction seeds and 2 Horn seeds × 1 replicate per model;
`SMOKE = False` runs the full protocol. A rerun skips finished replicates and rows.

Score the local mirror without the notebook (the notebook's report cells pull it first):

```
python -m smolbench.induction.repro report rebuttal/results/induction
python -m smolbench.deduction.horn.repro report rebuttal/results/horn/*.jsonl
```

The offline tests are in `tests/rebuttal/test_bedrock_trio.py`.
