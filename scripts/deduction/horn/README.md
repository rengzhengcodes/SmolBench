# Horn bench harness

The experimental setup is fixed; `smolbench/deduction/horn/README.md` specifies it. This
directory holds the scripts that render a rung, run it on Haiku (Claude Code subagents) or on
a served model, and analyse the results.

## Pipeline for one rung

1. `M=12 SEED0=100 NSEEDS=30 render_rung.sh <out>` writes `<out>/s<seed>/<arm>/prompt.md` for
   the four arms (`lem`, `pad`, `disc`, `both`). `M` is the chain length, the one
   parameter of a rung: `M` chain lemmas, `5 M` open alternatives, depth-2 trees, so prompt
   size follows `M` (about 80 tokens per chain lemma in `lem`, four times that in the other arms).
   `ARMS=lem` renders a calibration rung.
2. Haiku: `solve_arms.workflow.js` is a Claude Code workflow script: one Read-only Haiku agent
   (`.claude/agents/horn-solver.md`, no grep or shell) per seed x sample x arm; each returns
   `{status, answer}`. Args: `{dir, seeds, samples, arms, only?}`; `only` lists the cells to
   refill. `collect_rung.py <journal.jsonl> <out>` writes `answer.s<i>.md` per cell and scores
   the rung (`smolbench.deduction.horn.score`) into `<out>/scores.jsonl`. A cell whose answer
   holds no `derive` line, or whose status is `confused`, is contamination (the agent acted on
   the parent session's chat instead of the file): refill it with `only`.
3. Served models: `sweep.py --endpoint <base_url> --model <served name> --spec-key <roster key>
   --rung-dir <rung> --replicates 3 --out <rows.jsonl>` sends each cell as one chat completion
   (system.md + prompt.md) with a 32k output cap, temperature 0.7 and the roster model's
   thinking arguments, and scores the last block of `derive` lines. Rows are keyed by (model,
   rung, arm, seed, replicate); rerunning resumes; `length` finish reasons score as failures.
   Tested against a stub server in `tests/deduction/test_horn_sweep.py`.
   AWS Bedrock: `bedrock_sweep.py --model <bedrock id> --spec-key <roster key> --region us-east-2
   --rung-dir <rung> --out <rows.jsonl>` does the same over the Converse API with the caller's AWS
   credentials (`--extra-fields '{"reasoning_effort":"high"}'` switches thinking on for GLM-4.7 and
   Nemotron-3). `calibrate_m.py --calib-root <root> --out-dir <dir> --model ... --spec-key ...`
   walks lem-only calibration rungs `<root>/calib_m<m>` (seeds 200-229) up or down the ladder
   m in {3, 6, 12, 24, 48, 96, 192} until the model's lem pass rate lies in [60%, 80%], and records the
   level closest to 70% in `<dir>/<spec_key>_calibration.json`.
4. Analysis: `pilot_analysis.py <out>` (pass rates, seed-paired contrasts with bootstrap CIs and
   exact sign-flip p-values, proof lengths), `route_analysis.py <out>` (route of every attempt,
   failure reasons, tree-rule use), `intended_route.py <out>...` (route from the written heads).
   Haiku only: `grep_excluded.py <out> <workflow_dir>...` recomputes pass rates without the
   cells whose solver used a tool other than Read (a search of the file is not a read), and
   `transcript_search.py <out> <workflow_dir>` summarises what the solver explored.

The `horn-solver` agent type is registered when a Claude Code session starts, so it is available
in sessions started after the file exists.

Results and design history: `notebooks/deduction/HORN_BOTH_VS_PAD.md`. The roster study plan:
`notebooks/deduction/HORN_ROSTER_PLAN.md`.
