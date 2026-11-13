# Rebuttal: SmolBench on Amazon Bedrock

`bedrock_trio.ipynb` runs both studies on Amazon Bedrock with reasoning switched on: periodic
induction (arms `intens`, `noise_intens`, `extens`) and Horn-rule deduction (arms `lem`,
`pad`, `disc`, `both`). It runs them for three ladder models from three labs:

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
| `results/probes.json` | Model ids and the reasoning fields each model accepted |
| `results/induction/induction/<model>/seed=<s>/<arm>--<stamp>.yaml` | Induction replicates, in the released-results layout |
| `results/horn/<model>.jsonl` | Horn rows, readable by `smolbench.deduction.horn.repro report` |
| `rungs/` | Rendered Horn rungs (not committed) |

## Run

You need:
- AWS credentials that can call Bedrock in `us-east-1`. A short-term bearer token is
  minted from them; an `AWS_BEARER_TOKEN_BEDROCK` already set is used instead.
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

Score saved results without the notebook:

```
python -m smolbench.induction.repro report rebuttal/results/induction
python -m smolbench.deduction.horn.repro report rebuttal/results/horn/*.jsonl
```

The offline tests are in `tests/rebuttal/test_bedrock_trio.py`.
