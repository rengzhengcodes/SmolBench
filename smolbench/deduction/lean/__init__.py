"""Lean 4 theorem-proving eval: progressive-context induction over LeanDojo/Mathlib4.

This subpackage measures how an LLM's tactic-completion accuracy changes as
it gets progressively more context ("rungs") about a theorem's proof state
and the premises its true next tactic relies on. It uses LeanDojo Benchmark
4 theorems, and two cumulative chains: `stepk:0..2` (proof-state detail,
answer-agnostic) and `hint:0..4` (premise detail, answer-conditional). A
`noise:N` control arm pads `hint:(N-1)` with whitespace to `hint:N`'s exact
token count, so it isolates the effect of real content from the effect of
prompt length alone.

Module map:
  - `corpus` — loads LeanDojo Benchmark 4 theorem splits and locates the
    dataset root (`data_root()`, overridable via `SMOLBENCH_LEAN_DATA`).
  - `premises` — indexes `corpus.jsonl` for premise signature/body lookup
    and per-premise transitive dependency closure (hint:3+).
  - `context` — renders a (theorem, step, chain, level) triple into the
    Markdown context block shown to the model.
  - `prompt` — the fixed system prompt, the user-prompt assembly
    (`build_user_prompt`), and tactic-block extraction from a model
    response.
  - `runner`, `verify`, `cli` — orchestration, Lean-side proof replay, and
    the command-line entry points. These are owned and maintained
    separately from the four generation-side modules above.

Environment split: the four modules above (`corpus`, `premises`, `context`,
`prompt`) handle generation and analysis. They run under any Python >= 3.12,
using this project's regular `.venv`. `verify.py` additionally needs the
`.venv-lean` 3.12 environment, because its `lean_dojo` dependency pins
`python<3.13` for compatibility with the traced-repo tooling it wraps.

This `__init__.py` deliberately carries no imports. Importing
`smolbench.deduction.lean` must stay dependency-light. `context.py` pulls in
`tiktoken` (for token-budget accounting), and `verify.py` pulls in
`lean_dojo` (a heavy, `.venv-lean`-only dependency). Neither should load
merely because a caller wrote `import smolbench.deduction.lean`. Import the
specific submodule you need instead (e.g. `import smolbench.deduction.lean.corpus`).
"""
