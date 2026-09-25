"""Synthetic Horn-rule deduction bench.

A theory is a chain of ``m`` lemmas from facts to a goal. Each lemma has a
binary derivation tree of depth ``H`` over two-body axioms. Arms show the
lemmas, a cut of their trees, both, or the lemmas padded to the length of
both. `checker` verifies any valid step proof and records which route it took.
"""
