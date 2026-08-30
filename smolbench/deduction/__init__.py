"""Deduction evals: deriving valid consequences from given premises.

Sibling category to ``smolbench.induction`` (the pattern-completion evals
``chromatic`` and ``periodic``), which instead asks a model to infer a rule
from examples.

Members
-------
lean
    Lean 4 theorem-proving eval over LeanDojo Benchmark 4 / Mathlib4.

Carries no imports deliberately: ``smolbench.deduction.lean`` pulls in heavy
dependencies (``tiktoken``, ``lean_dojo``), so import the specific submodule
you need instead (e.g. ``import smolbench.deduction.lean.corpus``).
"""
