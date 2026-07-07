"""Deduction evals: tasks that probe *forward* logical inference.

Sibling category to ``smolbench.induction`` (the pattern-completion evals,
``chromatic`` and ``periodic``). Where induction asks a model to infer a rule
from examples, deduction asks it to derive a valid consequence from given
premises under fixed rules of inference.

Members
-------
lean
    Lean 4 theorem-proving eval over LeanDojo Benchmark 4 / Mathlib4 -- the
    first (and currently only) deduction experiment. See
    ``smolbench.deduction.lean`` for its module map and the main-``.venv`` vs.
    ``.venv-lean`` environment split.

This ``__init__`` deliberately carries no imports: ``smolbench.deduction.lean``
pulls in heavy, environment-specific dependencies (``tiktoken``, ``lean_dojo``),
so importing the category namespace must stay cheap. Import the specific
submodule you need (e.g. ``import smolbench.deduction.lean.corpus``).
"""
