# Review-round experiments

These runs answer the deduction questions from the ICLR 2027 reviews. They add two control
arms, `rep` and `tjunk`, to the paper's Bedrock models, and run all four review arms on
Haiku 4.5. `smolbench/deduction/horn/render.py` defines the arms.

| arm | what each tree slot holds | question |
|---|---|---|
| `rep` | a copy of the slot's own lemma; same proof graph as `lem`, at `both`'s line count | does lower density cost when the proof graph is fixed? |
| `tjunk` | `both`'s tree with leaves and root renamed; same shapes, connected to nothing | does rule structure alone cost? |
| `fwd` | `both`'s tree with the root renamed; it fires from the facts but leads nowhere | does a tree connected only at its leaves cost? |
| `marked-lemma` | `both`, with lemma lines tagged `[lemma]` | does knowing which rules are lemmas remove the cost? |

## Bedrock

- **Models and m.** The eight Bedrock models of the paper table, each at its paper chain
  length m. Theories are seeds 100-199, the same as the paper; the theory files are
  byte-identical.
- **Cells.** `rep` and `tjunk` × 100 seeds × 3 replicates = 600 per model. They ran in
  November 2026. The `lem`, `pad`, `disc` and `both` cells are the September 2026 cells
  behind the paper table.
- **Settings.** The paper's settings: Converse API in us-east-2, `reasoning_effort: high`
  for GLM, Nemotron and DeepSeek, an output cap of 131,072 tokens, temperature 0.7.
- **Scoring.** The `iclr` rule, which scored the paper table (`horn/extract.py`).
- **Errors.** Server errors were retried until every cell had a verdict.

The new arms ran seven weeks after the paper's arms. A change in Bedrock serving between
the two batches would shift every comparison across batches, including `rep` − `lem`.

## Haiku 4.5

- **Calibration.** `lem` on seeds 200-209 at m = 96, 128, 160 and 192, giving 10/10, 10/10,
  5/10 and 0/10. The run uses m = 160.
- **Runs.** All eight arms at m = 160, seeds 100-199, one replicate. Each cell is a
  Read-only Claude Code subagent (`horn-solver`) that reads the prompt and returns a proof.
- **Coverage.** 486 of the 800 cells completed. An API outage stopped 296 cells, and 18
  cells were dropped because the solver answered a chat message instead of the proof.
- **Read coverage.** Transcript audits show that the solvers requested the full prompt
  file in every arm.

## Files

| file | contents |
|---|---|
| `bedrock_cells.csv` | one row per Bedrock cell: model, m, arm, seed, replicate, verdict, route, steps, finish reason, completion tokens, batch |
| `haiku_m160_cells.csv` | one row per completed Haiku cell at m = 160 |
| `haiku_calibration.csv` | the Haiku `lem` calibration cells |
| `review_table.md` | the tables, written by `notebooks/deduction/analysis/horn_review_arms.py` |

The raw rows of the November Bedrock run, with full generations, are in
`s3://smolbench-results-414266451290/deduction_horn/review_2026-11/`. They are not public.

To rebuild the tables, run:

```
python notebooks/deduction/analysis/horn_review_arms.py
```
