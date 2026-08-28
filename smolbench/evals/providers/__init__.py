"""One module per inference backend.

``openrouter``, ``primeintellect``, ``aws`` (Bedrock/SageMaker) and
``ec2`` (a self-provisioned EC2 Spot box running vLLM) each configure
the shared engine in ``smolbench.evals.openai_compat`` for one service.
Name-to-module dispatch lives one level up, in
``smolbench.evals.provider``.

This file deliberately holds no module-level statements at all -- only
this docstring. Provider resolution therefore stays a call-time act
(nothing is pulled in merely by naming this subpackage), the
env-capture-at-first-load contract of ``ec2`` is not tripped by an
unrelated backend, and no cycle can form back through
``smolbench.evals``.
"""
