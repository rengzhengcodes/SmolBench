# Horn bench scripts

`smolbench/deduction/horn/README.md` specifies the experiment; its section 9 walks through
reproducing the ICLR 2027 results.

| script | what it does |
|---|---|
| `demo.py` | End-to-end check with no model: renders a small rung, serves the designed proofs from a local stub server, runs `sweep.py`, prints the report. |
| `sweep.py` | Sends every cell (arm x seed x replicate) of a rung to an OpenAI-compatible endpoint (vLLM) and scores the answer. Rows go to a JSONL file; rerunning resumes. |
| `bedrock_sweep.py` | The same over the AWS Bedrock Converse API, with the caller's AWS credentials (`uv sync --extra aws`). |
| `calibrate_m.py` | Searches the ladder of lem-only calibration rungs for the chain length where a model's pass rate reaches the target. |
| `calibration_pick.py` | Fits a logistic curve in log m to the calibration levels and reports the level nearest the target crossing. |

`python -m smolbench.deduction.horn.repro command --model <model> --rung <dir> --out <rows>`
prints a model's sweep command with the ICLR settings.

`sweep.py` options worth knowing:

- `--spec-key` selects the roster model's thinking arguments; `--thinking on|off`
  overrides them.
- `exception` rows (transport failures) are retried on the next run. A second sweep on
  the same output file is refused.
