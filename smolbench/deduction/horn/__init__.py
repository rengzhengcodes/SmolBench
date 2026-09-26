"""Synthetic Horn-rule deduction bench.

One fixed setup: a theory is a chain of ``m`` lemmas from facts to a goal, plus
open alternatives and a binary derivation tree per lemma. Four token-matched
arms (``lem``, ``pad``, ``disc``, ``both``) show the lemmas alone or with the
trees, lorem or dead trees in the trees' slots. ``checker`` verifies any valid step proof and records which route it
took. ``README.md`` in this package is the specification.
"""
