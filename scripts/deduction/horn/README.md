# Horn bench scripts

`smolbench/deduction/horn/README.md` specifies the experiment. Section 9 of that file
walks through reproducing the ICLR 2027 results. This directory holds the scripts that
run a rung on a model and calibrate a model's chain length.

## Run a rung on a model

| script | what it does |
|---|---|
| `demo.py` | End-to-end check with no model: renders a small rung, serves the designed proofs from a local stub server, runs `sweep.py` under both scoring modes, prints the report. |
| `sweep.py` | Sends every cell (arm x seed x replicate) to an OpenAI-compatible endpoint (vLLM) and scores the answer. Rows go to a JSONL file; rerunning resumes. |
| `bedrock_sweep.py` | The same over the AWS Bedrock Converse API, with the caller's AWS credentials. |
| `rows_contrast.py` | Pass rates per arm and seed-paired contrasts for any rows files. |
| `render_rung.sh` | Renders a rung's seeds in parallel (`M=12 SEED0=100 NSEEDS=100 render_rung.sh <out>`). |

`python -m smolbench.deduction.horn.repro command --model <key> --rung <dir> --out <rows>`
prints a model's `sweep.py` or `bedrock_sweep.py` command with the ICLR settings.

Typical `sweep.py` run against a vLLM server:

```
python scripts/deduction/horn/sweep.py --endpoint http://127.0.0.1:8000/v1 \
    --model qwen3.5-27b --spec-key qwen3.5-27b --rung-dir rungs/m64 --seeds 100-199 \
    --replicates 3 --max-tokens 131072 --context-length 131072 --scoring iclr --out rows.jsonl
```

- `--spec-key` selects the roster model's thinking arguments; `--thinking on|off`
  overrides them.
- `--scoring iclr|default` selects the proof extraction rule (default `default`).
- `--order reverse` and `--skip-from <rows>...` let a second worker fill a rung from the
  other end without repeating cells that another file already holds.
- Rows are keyed by (model, rung, arm, seed, replicate). `exception` rows (transport
  failures) are retried on the next run. A second sweep on the same output file is refused.

## Calibrate a model's chain length

`calibrate_m.py` searches the ladder of lem-only calibration rungs (`<root>/calib_m<m>`,
seeds 200-209) for the chain length where the model's lem pass rate reaches the target,
and writes `<out_dir>/<spec_key>_calibration.json`. `calibration_pick.py` fits a logistic
curve in log m to the levels run and reports the level nearest the target crossing.
Render a calibration rung with `ARMS=lem render_rung.sh` or
`python -m smolbench.deduction.horn.cli render --arms lem --seeds 200-209 --m <m>`.

## Record of the ICLR runs

`build_iclr_protocol.py` wrote `smolbench/deduction/horn/iclr.json` from the served rungs
and the results summaries. It does not need to run again.

## Haiku harness (`haiku/`)

The pilot runs used Claude Haiku 4.5 as Claude Code subagents.

| script | what it does |
|---|---|
| `solve_arms.workflow.js` | Claude Code workflow: one Read-only Haiku agent (`.claude/agents/horn-solver.md`, no search or shell) per seed x sample x arm, returning `{status, answer}`. Args: `{dir, seeds, samples, arms, only?}`; `only` lists cells to refill. |
| `collect_rung.py` | `collect_rung.py <journal.jsonl> <rung>` writes `answer.s<i>.md` per cell and scores the rung with `python -m smolbench.deduction.horn.score` into `<rung>/scores.jsonl`. |
| `grep_excluded.py` | Pass rates without the cells whose solver used a tool other than Read. |
| `pilot_analysis.py`, `route_analysis.py`, `intended_route.py`, `transcript_search.py` | Pilot analysis: contrasts, proof routes, tree-rule use, what the solver explored. |

A cell whose answer holds no `derive` line, or whose status is `confused`, is contamination
(the agent acted on the parent session's chat instead of the file): refill it with
`only`. The `horn-solver` agent type is registered when a Claude Code session starts.

Results and design history: `notebooks/deduction/HORN_BOTH_VS_PAD.md`. The roster study
plan: `notebooks/deduction/HORN_ROSTER_PLAN.md`.
