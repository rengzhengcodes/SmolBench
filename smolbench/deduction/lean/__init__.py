"""Lean 4 theorem-proving eval: progressive-context tactic completion over LeanDojo/Mathlib4.

Measures how tactic-completion accuracy moves as a model is given progressively
more context ("rungs") about a theorem, along two cumulative chains:
``stepk:0..2`` (proof-state detail, answer-agnostic) and ``hint:0..4`` (premise
detail, answer-conditional). The ``noise:N`` control arm pads ``hint:(N-1)``
with whitespace to ``hint:N``'s exact token count, isolating real content from
prompt length alone.

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

Dependency split: ``corpus``/``premises``/``context``/``prompt`` are the
generation and analysis side and need no Lean toolchain; ``verify`` also needs
``lean_dojo`` (the ``lean`` extra, ``uv sync --all-extras``), elan, and a
traced-repo cache at runtime. This ``__init__`` therefore carries no imports --
neither ``tiktoken`` (via ``context``) nor ``lean_dojo`` should load merely
because a caller wrote ``import smolbench.deduction.lean``.
"""
