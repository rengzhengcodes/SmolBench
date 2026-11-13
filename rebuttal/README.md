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
| `attention_replay.py` | Replays stored induction transcripts through self-hosted checkpoints to capture attention (see below) |
| `attention_state/` | EC2 state of a replay in progress (not committed) |
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
| `attention/induction/<model>/seed=<s>/<arm>--<stamp>/q<i>.r<rank>.{npz,json}` | Attention summary of one induction mark, one object pair per tensor-parallel rank |
| `attention/induction/<model>/seed=<s>/<arm>--<stamp>/manifest--<ts>.json` | What one replay captured for that run |

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
- **Horn output caps.** The published DeepSeek and Nemotron Horn rows ran through the
  Bedrock Converse API in `us-east-2` with a 131,072-token output cap. This notebook sends
  the model-card caps (8K and 32K) to bedrock-mantle, and most generations need more: in
  the published cells every DeepSeek success is longer than 8K. Horn pass rates from this
  notebook are therefore not comparable with the published ones until the cap is raised.
  The report prints the published rates next to what they would be under the caps here
  (`bedrock_trio.horn_reference`, from `notebooks/deduction/review/bedrock_cells.csv`).
- **`extens`.** On this branch the `extens` context is the intensional rules followed by the
  listing. The published `extens` and `noise_intens` values come from the earlier arm, which
  carried the listing only, so only `intens` is like-for-like with the published values. The
  notebook's prompt check compares each arm with the released prompts in the way that
  matches this.

## Attention

Bedrock returns no attention weights. `attention_replay.py` replays each stored induction
mark (prompt, returned reasoning, answer) through the matching open-weights checkpoint on a
self-hosted vLLM server on EC2, teacher-forced, with a capture plugin. For each response
token, layer and head it stores the attention mass on four classes of earlier tokens (the
informative prompt, the whitespace padding of `noise_intens`, template tokens, the response
so far) and the entropy. The captures measure the open checkpoint reading Bedrock's text,
not Bedrock's own serving. `attention_replay.APPROXIMATIONS` lists the differences: token
ids are encoded again from text, the chat template is the open repository's, and newlines
around the thinking delimiters are not restored.

The notebook section is off by default and has two switches:

- `ATTENTION = True` plans the replay offline (jobs, tokens, errors, storage estimate). It
  makes no AWS call.
- `ATTENTION_APPROVED = True` launches. `replay_model` provisions one billed EC2 spot GPU
  instance, serves the checkpoint, captures, audits every stored array against the model's
  shape and terminates the instance. It refuses anything but the literal `True` before
  any AWS client is built.

Safeguards: a mark with mis-decoded text is listed as an error and never sent; jobs already
in the bucket are skipped; uploads use `If-None-Match: *`, so they cannot replace an
object; a job with only some of its rank objects is reported as partial.
The offline reader `read_captures` reads only captures that a manifest records as verified.

`deepseek-v3.1` is refused. vLLM serves it with multi-head latent attention (a separate
MLA layer), which the capture hook does not reach, so a run would store nothing.

The replay has never run against a live instance. Its offline tests are in
`tests/rebuttal/test_attention_replay.py` and `tests/evals/test_attention*.py`. The capture
plugin tests need torch and are skipped by the default suite. In an environment with torch,
run `python -m pytest tests/evals/test_attention_capture_plugin.py`.

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
