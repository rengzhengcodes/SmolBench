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
| `run_protocol.py` | The same two studies from the command line, one model and one region per process |
| `cap_probe.py` | Probes whether an endpoint honours an output cap above the model-card cap |
| `attention_replay.py` | Replays stored induction and Horn transcripts through self-hosted checkpoints to capture attention (see below) |
| `run_attention.py` | The replay from the command line: plan, launch (with `--approved`), audit |
| `attention_state/` | EC2 state of a replay in progress (not committed) |
| `results/` | Local mirror of the bucket (not committed), described below |
| `rungs/` | Rendered Horn rungs (not committed) |

## Results

The private bucket `s3://smolbench-rebuttals-414266451290/bedrock-trio` (`us-west-2`) is the
store of record. Bedrock inference runs in `us-east-1` by default; `us-east-2` and
`us-west-2` serve the same three model ids, and the protocol runs of 2026-11-16 used all
three regions. Objects are append-only: nothing is
overwritten or deleted, and a rerun adds new stamped keys.

| Key below the prefix | Contents |
|---|---|
| `induction/<model>/seed=<s>/<arm>--<stamp>.yaml` | One induction replicate, in the released-results layout |
| `deduction/horn/<model>/rows--<stamp>.jsonl` | A part of Horn rows: the rows one push added |
| `probes/probes--<stamp>.json` | Model ids and the reasoning fields each model accepted |
| `probes/cap-probe--<label>--<stamp>.jsonl` | Rows of one output-cap probe (`cap_probe.py`) |
| `attention-v2/induction/<model>/seed=<s>/<arm>--<stamp>/q<i>.r<rank>.{npz,json}` | Attention summary of one induction mark, one object pair per tensor-parallel rank |
| `attention-v2/induction/<model>/seed=<s>/<arm>--<stamp>/manifest--<ts>.json` | What one replay captured for that run |
| `attention-v2/deduction/horn/<model>/<rung>/<arm>/s<seed>.rep<rep>.r<rank>.{npz,json}` | Attention summary of one Horn cell, with manifests beside them |
| `attention-v2-check/` | One Gemma seed captured in both capture modes, to compare them |

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

### Protocol runs of 2026-11-16

Seeded, on bedrock-mantle. Induction: 30 seeds per arm, accuracy over 270 questions, with
95% bootstrap intervals that resample seeds (10,000 draws).

| | high density (`intens`) | with whitespace (`noise_intens`) | with related rules (`related_intens`) | low density (`extens`) |
|---|---|---|---|---|
| Gemma 4 31B | 1.000 [1.000, 1.000] | 0.996 [0.989, 1.000] | 0.981 [0.959, 1.000] | 1.000 [1.000, 1.000] |
| Nemotron 3 Super | 0.993 [0.981, 1.000] | 0.993 [0.981, 1.000] | 0.919 [0.874, 0.956] | 0.956 [0.911, 0.989] |
| DeepSeek V3.1 | 1.000 [1.000, 1.000] | 1.000 [1.000, 1.000] | 0.967 [0.941, 0.989] | 1.000 [1.000, 1.000] |

An arm with 270 of 270 correct has no variance over seeds, so its bootstrap interval is a
point; the exact binomial interval for 270 of 270 is 0.986 to 1.000.

Horn: 100 seeds × 3 replicates per arm (300 cells), pass rate in percent.

| | `lem` | `pad` | `disc` | `both` | `fwd` | `tjunk` | `rep` | `marked-lemma` |
|---|---|---|---|---|---|---|---|---|
| Gemma 4 31B (`m`=64) | 67.3 | 59.3 | 24.7 | 10.7 | 16.0 | 21.3 | 77.7 | 15.7 |
| Nemotron 3 Super (`m`=20) | 66.0 | 49.3 | 7.7 | 8.0 | 12.3 | 33.7 | 64.7 | 14.0 |
| DeepSeek V3.1 (`m`=64) | 65.0 | 45.0 | 12.3 | 12.3 | 29.0 | 32.7 | 72.7 | 33.3 |

`tjunk` minus `both`, seed-paired (`smolbench.deduction.horn.stats.contrast`): Gemma +10.7
points (95% interval +4.7 to +16.7, p = 0.0011), Nemotron +25.7 (+19.3 to +32.0, p < 5e-05),
DeepSeek +20.3 (+15.0 to +26.0, p < 5e-05).

Regions: Gemma 2,027 cells in `us-east-1` and 373 in `us-east-2`; Nemotron 990 in
`us-east-1`, 610 in `us-east-2` and 800 in `us-west-2`; DeepSeek all in `us-east-1`. The
regions ran different replicates, not different arms, and each row records its region in
`provider`.

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
mark or Horn cell (prompt, returned reasoning, answer) through the matching open-weights
checkpoint on a self-hosted vLLM server on EC2, teacher-forced, with a capture plugin. For
each response token, layer and head it measures:

- the prompt entropy: the Shannon entropy, in nats, of the attention weights on the input
  prompt after they are renormalized to sum to 1;
- the entropy of the whole attention row;
- the attention mass on four classes of earlier tokens: the informative prompt, the
  padding (the whitespace of `noise_intens`, the added rule lines of `related_intens`),
  template tokens, and the response so far.

There are two capture modes. `mass` stores one value per response token (float16 arrays,
about 35 MB per induction mark for Gemma 4 31B). `summary` stores, per layer and head, the
sums over the response tokens and the counts they need, which is all the tables below use
(a few kB per mark). The two modes agree: on Gemma seed 0 the per-layer mean prompt entropy
differs by at most 2e-5 nats over 36 marks. Horn cells are captured in `summary` mode only,
because a Horn answer runs to tens of thousands of tokens.

`read_captures` averages the prompt entropy over one response and then over responses, and
reports global-attention and sliding-window layers apart. A response token with no prompt
token in reach (late tokens in a sliding-window layer) has no prompt entropy and is left
out. `read_entropy_table` gives the same statistic for each study and arm. `pull_captures`
mirrors the stored captures for them. Only captures that a manifest records as verified are
read.

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
prefill path does. `replay_model` asks for `allow_unverified_serve` for this model, because
the pinned vLLM image starts it only when the weight mirror holds the repository's metadata
archive (`meta.tar`, with `tokenizer.json`; added 2026-11-16). For capture it is served with
a 49,152-token context by default; `capture_max_model_len` raises it. The longest cell
captured is 82,036 tokens. With a 98,304-token context, cells of 86,900 tokens or more
stopped the vLLM engine on four instances, so the Horn runs that held such cells were
repeated with an 84,000-token context, which leaves them out. vLLM's flash-attention backend for this layer treats a sequence of 512 tokens or fewer
as decode, a path the plugin refuses to capture, so the plugin sets that threshold to 1 when
it loads; short `intens` marks then take the captured prefill path.

### Captures of 2026-11-16 and 2026-11-17

Induction: all 30 seeds, four arms, 9 questions per replicate (270 responses per arm). Horn:
the arms `lem`, `pad`, `both` and `tjunk`, seeds 100 to 189, replicates 0 to 2 (270 responses
per arm, as for induction). Mean prompt entropy in nats; for Gemma
4 31B over its 10 global-attention layers, for the others over all attention layers.

| | Gemma 4 31B | Nemotron 3 Super | DeepSeek V3.1 |
|---|---|---|---|
| induction `intens` | 2.466 [2.462, 2.471] | 2.418 [2.395, 2.439] | 1.309 [1.299, 1.320] |
| induction `noise_intens` | 4.638 [4.625, 4.652] | 3.116 [3.107, 3.124] | 2.118 [2.105, 2.130] |
| induction `extens` | 5.863 [5.851, 5.876] | 3.998 [3.981, 4.015] | 2.584 [2.572, 2.595] |
| induction `related_intens` | 6.212 [6.174, 6.251] | 4.170 [4.064, 4.275] | 2.526 [2.517, 2.536] |
| Horn `lem` | 5.035 [5.030, 5.039] | 3.186 [3.165, 3.207] | 1.941 [1.928, 1.953] |
| Horn `pad` | 5.858 [5.854, 5.862] | 3.822 [3.798, 3.844] | 2.233 [2.216, 2.249] |
| Horn `both` | 6.358 [6.350, 6.367] | 3.789 [3.765, 3.814] | 2.108 [2.083, 2.134] |
| Horn `tjunk` | 6.272 [6.265, 6.279] | 3.694 [3.670, 3.717] | 2.268 [2.244, 2.291] |

The brackets are 95% bootstrap intervals (`attention_replay.entropy_ci`, 10,000 draws).
Responses of one seed share their context, so a draw resamples whole seeds (30 for induction, 90
for Horn) and takes the mean over the responses of the drawn seeds.

Captures missing from these means:

- DeepSeek V3.1 induction: 3 `related_intens` marks longer than the 98,304-token capture
  context.
- DeepSeek V3.1 Horn: 11 `both` cells and 2 `tjunk` cells, so those means are over 259 and
  268 responses. Seven are longer than 98,304 tokens; six `both` cells of 85,000 to 87,800
  tokens are the ones left out after the engine stopped (one of them was stored before the
  engine stopped, but no manifest records it as verified, so it is not read).
- Gemma 4 31B: 7 induction marks and 1 Horn cell lost one rank to the plugin's self-check
  (a relative error of 0.031 to 0.040 against a tolerance of 0.03). They are recorded as
  failed and are not read.
- Nemotron 3 Super: none.

`bedrock-trio/smoke-2/attention/` holds the Gemma pilot on the second smoke (54 jobs). It
predates the prompt entropy and the `related_intens` arm and is not read.

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

The same runs from the command line, one model per process (the Horn options `--region`,
`--rep-indices` and `--rows-label` let several regions run disjoint replicates of one
model):

```
python rebuttal/run_protocol.py induction --model gemma-4-31b --seeds 0-29
python rebuttal/run_protocol.py horn --model gemma-4-31b
python rebuttal/run_attention.py --model gemma-4-31b --study induction --mode summary
python rebuttal/run_attention.py --model gemma-4-31b --study horn --seeds 100-189 --arms lem pad both tjunk --reps 0-2
```

`run_attention.py` prints the plan and stops; it launches only with `--approved`.

Score the local mirror without the notebook (the notebook's report cells pull it first):

```
python -m smolbench.induction.repro report rebuttal/results/induction
python -m smolbench.deduction.horn.repro report rebuttal/results/horn/*.jsonl
```

The offline tests are in `tests/rebuttal/`.
