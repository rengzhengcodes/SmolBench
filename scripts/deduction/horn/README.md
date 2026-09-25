# Horn bench harness

Pipeline for one rung:

1. `render_rung.sh <out> <lemma_tokens> <unfold_tokens>` writes `<out>/s000N/<arm>/prompt.md`.
   Arms: `lem`, `both`, `pad` (lorem), `junk` (rule-shaped irrelevant lines), `disc`
   (trees with leaves renamed, cannot be entered), `deep` / `dpad` (derivation trees below the
   given facts, needs `--fact-height`; `--fact-tokens` fits the chain length; `--match-library`
   reuses another rung's libraries), `ax`, `unf:j`, `both:j`, `pad:j`, `bothm`, `padm`.
   (env: `NC` constants, `OF` open fraction, `M` chain length, `H` tree depth, `ARMS`, `CAPX` step cap multiple).
2. `solve_arms.workflow.js` is a Claude Code workflow script: one Read-only Haiku agent (`.claude/agents/horn-solver.md`, no grep or shell) per
   seed x sample x arm; each returns `{status, answer}`. Args: `{dir, seeds, samples, arms, only?}`.
3. `collect_rung.py <journal.jsonl> <out>` writes `answer.s<i>.md` per cell and scores the rung
   (`smolbench.deduction.horn.score`) into `<out>/scores.jsonl`.
4. Analysis: `pilot_analysis.py <out>` (pass rates, paired contrasts, step budgets),
   `route_analysis.py <out>` (route of every attempt, failure reasons),
   `intended_route.py <out>...` (route from the written heads, pass by route),
   `transcript_search.py` also lists cells that used any tool other than Read (a grep of the file is a search, not a read; exclude or refill them),
   `transcript_search.py <out> <workflow_dir>` (what the solver explored in its reasoning).

Results and design notes: `notebooks/deduction/HORN_BOTH_VS_PAD.md`.

`grep_excluded.py <out> <workflow_dir>...` recomputes per-arm pass rates with and without the
cells whose solver used a tool other than Read. The `horn-solver` agent type is registered when
a Claude Code session starts, so it is available in sessions started after the file exists.

## Served-model sweeps (no tools)

`sweep.py --endpoint <base_url> --model <served name> --spec-key <roster key> --rung-dir <rung>
--arms lem both pad --replicates 3 --out <rows.jsonl>` sends each cell as one chat completion
(system.md + prompt.md) with a 32k output cap, temperature 0.7 and the roster model's thinking
arguments, and scores the last block of `derive` lines. Rows are keyed by (model, arm, seed,
replicate); rerunning resumes. `render_rung.sh` takes `REPO=<checkout>` and `PYTHON=<interpreter>`
when run from outside a checkout. The roster study plan: `notebooks/deduction/HORN_ROSTER_PLAN.md`.
