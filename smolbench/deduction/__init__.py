"""Deduction evals: deriving valid consequences from given premises.

Sibling category to ``smolbench.induction`` (``chromatic``, ``periodic``), which
instead asks a model to infer a rule from examples.

Members
-------
lean
    Lean 4 theorem-proving eval over LeanDojo Benchmark 4 / Mathlib4.

Carries no imports deliberately: ``smolbench.deduction.lean`` pulls in
``tiktoken`` and ``lean_dojo``, so import the specific submodule you need
(e.g. ``import smolbench.deduction.lean.corpus``).
"""
