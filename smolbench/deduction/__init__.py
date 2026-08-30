"""Deduction evals: deriving valid consequences from given premises.

Sibling category to ``smolbench.induction`` (``chromatic``, ``periodic``), which
instead asks a model to infer a rule from examples.

Members
-------
lean
    Lean 4 theorem-proving eval over LeanDojo Benchmark 4 / Mathlib4.

Deliberately imports nothing; import the specific submodule you need (e.g.
``import smolbench.deduction.lean.corpus``). See ``smolbench.deduction.lean``
for which submodules pull in ``tiktoken`` / ``lean_dojo``.
"""
