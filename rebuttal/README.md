# Rebuttal: SmolBench on Amazon Bedrock

`bedrock_trio.ipynb` runs both studies on Amazon Bedrock with reasoning switched on: periodic
induction (arms `intens`, `noise_intens`, `extens` and the review arm `related_intens`) and Horn-rule deduction (eight arms: the
paper arms `lem`, `pad`, `disc`, `both` and the review arms `fwd`, `tjunk`, `rep`,
`marked-lemma`). It runs them for three ladder models from three labs:

| roster key | lab | parameters | Horn `m` |
|---|---|---|---|
| `gemma-4-31b` | Google | 30.7B dense | 64 |
| `nemotron-3-super-120b-a12b` | NVIDIA | 120B MoE, 12B active | 20 |
| `deepseek-v3.1` | DeepSeek | 685B MoE, 37B active | 64 |

The notebook's first cell explains the choice and lists how these runs differ from the
ICLR runs: the induction temperature default and seeding. The output budgets are the ICLR
ones.

| File | Contents |
|---|---|
| `bedrock_trio.ipynb` | The notebook: authenticate, force reasoning, check prompts, run, report |
| `bedrock_trio.py` | Roster, endpoint switch, results store and reasoning checks over the existing run code |
| `cap_probe.py` | Probes whether an endpoint honours an output cap above the model-card cap |
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
| `probes/cap-probe--<label>--<stamp>.jsonl` | Rows of one output-cap probe (`cap_probe.py`) |
| `attention-v2/induction/<model>/seed=<s>/<arm>--<stamp>/q<i>.r<rank>.{npz,json}` | Attention summary of one induction mark, one object pair per tensor-parallel rank |
| `attention-v2/induction/<model>/seed=<s>/<arm>--<stamp>/manifest--<ts>.json` | What one replay captured for that run |

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
- **Output budgets.** Both studies send the ICLR budgets: for Horn a 131,072-token cap cut
  to fit a 131,072-token context, for induction `run_study.completion_budget`.
  bedrock-mantle honours them. `cap_probe.py` checked this on 2026-11-13 on mantle in
  `us-east-1` and `us-east-2` and on the Converse API in `us-east-2`: all three returned
  completions above the output caps on the model cards (8K for DeepSeek V3.1, 32K for
  Nemotron Super), up to the full 131,072 tokens. Its rows are in the bucket as
  `probes/cap-probe--<label>--<stamp>.jsonl`. The first smoke sent the model-card caps, so
  most of its Horn answers were truncated; that is one more reason `bedrock-trio/smoke/`
  is not read.
- **Answers in the reasoning channel.** Bedrock sometimes returns an induction answer as
  the whole reasoning text with an empty response (seen for Nemotron Super on `extens`: 3 of
  18 marks in the smoke, each 4 completion tokens long and each the correct number). Such a
  mark is graded as wrong, as an empty answer was at ICLR, and the notebook counts it as
  `empty_response`. It passes the reasoning check, which only tests for reasoning text.
- **Horn reference.** The published DeepSeek and Nemotron Horn rows ran through the Bedrock
  Converse API in `us-east-2` without a seed. The notebook prints their pass rates and
  answer lengths (`bedrock_trio.horn_reference`, from
  `notebooks/deduction/review/bedrock_cells.csv`) next to its own seeded mantle runs.
- **`related_intens`.** The review arm for induction: the rules, then irrelevant rules of the
  same form (one of the replicate's periods with a fresh label that no question asks about),
  filled to the token count of `extens` under the model's tokenizer, with a few whitespace
  tokens to make the count exact (about 3,500 to 4,700 added lines). The added lines are
  one stream per seed, the same for every model. The four paper conditions are unchanged.
  It is the induction counterpart of the Horn arm `tjunk`: padding that is irrelevant but
  has the structure of the relevant information.
- **`extens`.** On this branch the `extens` context is the intensional rules followed by the
  listing. The published `extens` and `noise_intens` values come from the earlier arm, which
  carried the listing only, so only `intens` is like-for-like with the published values. The
  notebook's prompt check compares each arm with the released prompts in the way that
  matches this.

## Attention

Bedrock returns no attention weights. `attention_replay.py` replays each stored induction
mark (prompt, returned reasoning, answer) through the matching open-weights checkpoint on a
self-hosted vLLM server on EC2, teacher-forced, with a capture plugin. For each response
token, layer and head it stores:

- the prompt entropy: the Shannon entropy, in nats, of the attention weights on the input
  prompt after they are renormalized to sum to 1;
- the entropy of the whole attention row;
- the attention mass on four classes of earlier tokens: the informative prompt, the
  padding (the whitespace of `noise_intens`, the added rule lines of `related_intens`),
  template tokens, and the response so far.

`read_captures` averages the prompt entropy over one response and then over responses, and
reports global-attention and sliding-window layers apart. A response token with no prompt
token in reach (late tokens in a sliding-window layer) has no prompt entropy and is left
out. `pull_captures` mirrors the stored captures for it. Only captures that a manifest
records as verified are read.

The captures measure the open checkpoint reading Bedrock's text, not Bedrock's own serving.
`attention_replay.APPROXIMATIONS` lists the differences: token ids are encoded again from
text, the chat template is the open repository's, and newlines around the thinking
delimiters are not restored.

The notebook section is off by default and has three switches:

- `ATTENTION = True` plans the replay offline (jobs, tokens, errors, storage estimate) and
  reports the captures already stored. Planning makes no AWS call.
- `ATTENTION_APPROVED = True` launches. `replay_model` provisions one billed EC2 spot GPU
  instance, serves the checkpoint, captures, audits every stored array against the model's
  shape and terminates the instance. It refuses anything but the literal `True` before
  any AWS client is built.
- `ATTENTION_ALLOW_UNVERIFIED = True` is also needed for `deepseek-v3.1`.

Safeguards: a mark with mis-decoded text is listed as an error and never sent; jobs already
in the bucket are skipped; uploads use `If-None-Match: *`, so they cannot replace an
object; a job with only some of its rank objects is reported as partial.

The instance serves from the fleet's weight mirror (`EC2_S3_MODEL_CACHE`, set in the
notebook's first cell). `replay_model` refuses to launch without it: on 2026-11-16 an
instance without the mirror was billed for 15 minutes and vLLM failed at startup.

`deepseek-v3.1`: vLLM serves it with multi-head latent attention. The plugin captures that
layer by rebuilding per-head keys and values with the layer's own projection, as vLLM's
prefill path does. This is tested against a stub and has never run on a live server. Serving
is unverified too: the pinned vLLM image failed to start this model on 2026-09-19 with a
tokenizer error whose cause is unknown. For capture it is served with a 49,152-token
context, because startup memory at 131,072 tokens is unmeasured.

What has run live: the Gemma 4 31B pilot of 2026-11-16 on the second smoke (54 jobs, all
verified; captures under `bedrock-trio/smoke-2/attention/`). It predates the prompt entropy
and the `related_intens` arm, so new captures go under `attention-v2/`. Nemotron Super and
DeepSeek V3.1 have no captures.

The offline tests are in `tests/rebuttal/test_attention_replay.py` and
`tests/evals/test_attention*.py`. The capture plugin tests need torch and are skipped by
the default suite. In an environment with torch, run
`python -m pytest tests/evals/test_attention_capture_plugin.py`.

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
