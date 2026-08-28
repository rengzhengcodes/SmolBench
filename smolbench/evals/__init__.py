"""Evaluation harness for OpenAI-compatible inference providers.

The package is laid out as follows:

* ``quiz.py`` -- the datamodel every eval is expressed in: the
  question/answer structs (``QnA``, ``ToF``, ``Numeric``), the ``Quiz``
  type alias, and the ``Mark``/``Marks`` records of one graded quiz
  (including their YAML round trip). Its public names are re-exported
  below, so ``from smolbench.evals import Marks`` keeps working and the
  legacy YAML tag ``!!python/object:smolbench.evals.Marks`` still
  resolves.
* ``openai_compat.py`` -- the shared engine: retry loop, response
  parsing (content/reasoning channels, ``<think>`` splitting, token
  guard), parallel quiz evaluation, and metadata GETs. Every backend is
  a thin configuration over it, so it is deliberately NOT one of the
  registered providers.
* ``provider.py`` -- the registry and call-time dispatch. Pick a backend
  with ``INFERENCE_PROVIDER``, or resolve one explicitly with
  ``provider_module(name)``.
* ``providers/`` -- one module per inference backend (``openrouter``,
  ``primeintellect``, ``aws`` for Bedrock/SageMaker, ``ec2`` for a
  self-provisioned EC2 Spot box running vLLM).
* ``_aws.py`` -- AWS provisioning primitives shared by ``providers/aws``,
  ``providers/ec2`` and ``results_store``; it stays at this level
  because it is not itself a backend.
* ``parsing.py``, ``tokenization.py``, ``replicates.py``,
  ``results_store.py`` -- answer extraction, tokenizer loading for
  token-matched prompts, the replicate harness, and the local/S3
  results backends.
* ``payloads/`` -- byte-exact on-instance assets (cloud-init template,
  control agent, watchdog) used by ``providers/ec2``.

See ``smolbench/evals/README.md`` for the design rationale behind this
split.
"""

from smolbench.evals.quiz import Answer, QnA, ToF, Numeric, Quiz, Mark, Marks

__all__ = [
    "Answer",
    "QnA",
    "ToF",
    "Numeric",
    "Quiz",
    "Mark",
    "Marks",
]
