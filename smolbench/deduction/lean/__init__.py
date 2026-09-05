"""Lean 4 theorem-proving eval: progressive-context tactic completion over LeanDojo/Mathlib4.

Measures how tactic-completion accuracy moves as a model is given progressively
more context ("rungs"), along two cumulative chains: ``stepk:0..2`` (proof-state
detail, answer-agnostic) and ``hint:0..4`` (premise detail, answer-conditional).
The ``noise:N`` control arm pads ``hint:(N-1)`` with whitespace to ``hint:N``'s
exact token count, isolating content from prompt length alone.

Module map
----------
corpus
    Benchmark splits; ``data_root()``, overridable via ``SMOLBENCH_LEAN_DATA``.
premises
    ``corpus.jsonl`` index: premise signature/body and transitive closure (hint:3+).
context
    Renders a (theorem, step, chain, level) triple into the Markdown context block.
prompt
    Fixed system prompt, user-prompt assembly, tactic-block extraction.
runner, verify, cli
    Orchestration, Lean-side proof replay, command-line entry points.
replbackend
    Drives a `lean_interact` REPL session against a mathlib4 checkout
    (``SMOLBENCH_MATHLIB_ROOT``); the Lean-side backend ``verify`` sits on.
nullverify
    ``NullVerifier``: verifies nothing, for phase-1 (generation-only) sweeps
    with no Lean toolchain at all; used by `runner` and
    ``notebooks/deduction/run_study.py``.
sft
    Builds a decontaminated Lean 4 SFT dataset out of the eval's own
    corpus/context/prompt code, for prompt parity with the headline sweep.
    Not called by anything in-tree today outside its own tests.
decontam
    Content-level (name/statement/state/tactic-chain) decontamination for
    `sft`-built data, catching leaks ``sft``'s ``full_name`` holdout misses.
    Likewise only exercised by tests today, not by an in-tree caller.
lean3
    Detects and injects Lean 3 syntax / renamed-lemma relics; `runner`'s
    `write_run_analysis` uses it unconditionally for the ``l3`` leak-rate
    column.

Dependency split: only ``verify`` (and, transitively through it, `run-cell`
and `run-sweep` in `cli`) needs a live Lean toolchain at runtime --
`lean_interact` (the ``lean`` extra, ``uv sync --all-extras``) plus `elan` on
``PATH`` plus a mathlib4 checkout actually BUILT with `elan`/`lake`, pointed
to by the ``SMOLBENCH_MATHLIB_ROOT`` environment variable that
`replbackend.mathlib_root` reads at call time. Everything else in this
package -- generation, prompt rendering, analysis, SFT/decontam dataset
building -- is the non-verifying side and needs none of that. `lean-dojo`
(the old, now-deprecated ``Dojo`` interaction layer, which cannot drive Lean
>= v4.20 and so cannot reach this corpus's mathlib4 at Lean v4.34.0-rc2) is
NOT what `verify` needs any more -- but it has not left the ``lean`` extra:
it remains a declared dependency for corpus TRACING (building
``corpus.jsonl``) and for `premises`' PREMISE SOURCE SLICING, which still
resolves full declaration text out of the traced-repo cache at
``~/.cache/lean_dojo`` (`premises._traced_root`). That cache is therefore not
obsolete repo-wide, only no longer read by verification.

This ``__init__`` therefore imports nothing, so neither ``tiktoken`` (via
``context``) nor ``lean_interact`` (via ``verify``) loads on a bare
``import smolbench.deduction.lean``.
"""
