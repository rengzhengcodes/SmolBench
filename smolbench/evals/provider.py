"""
Dispatch to the active inference provider, based on INFERENCE_PROVIDER.

Set INFERENCE_PROVIDER in keys.env to openrouter (the default),
primeintellect, aws (Amazon Bedrock by default; set AWS_INFERENCE_BASE_URL to
target a SageMaker endpoint instead), or ec2 (a self-provisioned vLLM spot
instance, whose endpoint is resolved at call time from the state file written
by smolbench.evals.providers.ec2.provision_spot_instance). Then import
query/complete/evaluate/get_model_context_length from here rather than from a
provider-specific module.

Dispatch happens at CALL time -- the env var is read and the provider module
imported on each call -- so a notebook only needs its env configured before the
first query/evaluate call, not before any import.

To mix providers per model in one process (one env var cannot express that),
resolve explicitly with provider_module("ec2"), which bypasses the environment;
smolbench.deduction.lean uses that pattern, everything else uses env dispatch.

This module only dispatches. The AWS provisioning primitives shared by aws.py
and ec2.py live in smolbench.evals._aws.
"""

import importlib
import os
from types import ModuleType
from typing import Optional

#: Provider name -> module implementing query/complete/evaluate/get_model_context_length.
_PROVIDER_MODULES: dict[str, str] = {
    "openrouter": "smolbench.evals.providers.openrouter",
    "primeintellect": "smolbench.evals.providers.primeintellect",
    "aws": "smolbench.evals.providers.aws",
    "bedrock": "smolbench.evals.providers.aws",
    "sagemaker": "smolbench.evals.providers.aws",
    "ec2": "smolbench.evals.providers.ec2",
}


def provider_module(name: Optional[str] = None) -> ModuleType:
    """Resolve a provider module, either explicitly or from the environment.

    ``name=None`` (the default) dispatches from ``INFERENCE_PROVIDER``
    ("openrouter" when unset); an explicit `name` bypasses the environment
    entirely.

    Raises
    ------
    ValueError
        The resolved name is not a recognized provider, or it resolves to
        "sagemaker" with no AWS_INFERENCE_BASE_URL set -- the aws module
        defaults to the Bedrock URL, so it would otherwise silently hit
        Bedrock. (ec2 needs no such guard: it raises at call time when it
        finds no provisioned instance.)
    """
    # Design: an explicit `name` bypasses the environment lookup entirely
    # rather than merely overriding it, so a caller resolving "ec2" here
    # is unaffected by whatever INFERENCE_PROVIDER happens to be set to
    # elsewhere in the process (needed for mixed-provider sweeps).
    resolved = (name if name is not None else os.getenv("INFERENCE_PROVIDER", "openrouter")).lower()
    if resolved not in _PROVIDER_MODULES:
        # Error text says INFERENCE_PROVIDER for the env-dispatch case,
        # which tests match on; explicit-name lookups get a generic
        # "provider" label instead.
        label = "INFERENCE_PROVIDER" if name is None else "provider"
        raise ValueError(
            f"Unknown {label}={resolved!r}. "
            "Valid options: 'openrouter', 'primeintellect', 'aws'/'bedrock', "
            "'sagemaker', 'ec2'."
        )
    if resolved == "sagemaker" and not os.getenv("AWS_INFERENCE_BASE_URL"):
        raise ValueError(
            "INFERENCE_PROVIDER=sagemaker requires AWS_INFERENCE_BASE_URL="
            "https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{endpoint}/openai/v1"
        )
    return importlib.import_module(_PROVIDER_MODULES[resolved])


def query(*args, **kwargs):
    """Query the active provider; see ChatClient.query for the parameters."""
    return provider_module().query(*args, **kwargs)


def complete(*args, **kwargs):
    """Query the active provider, returning the full ``ChatResult`` (content,
    reasoning, token usage, server-reported model, finish_reason) instead of
    query's narrowed ``(content, reasoning)`` 2-tuple; see ChatClient.complete."""
    return provider_module().complete(*args, **kwargs)


def evaluate(*args, **kwargs):
    """Evaluate a quiz on the active provider; see ChatClient.evaluate.

    All providers share one implementation (smolbench.evals.openai_compat), so
    per-call tuning behaves identically regardless of INFERENCE_PROVIDER.
    """
    return provider_module().evaluate(*args, **kwargs)


def get_model_context_length(model: str) -> int:
    """Look up the active provider's context window for `model`."""
    return provider_module().get_model_context_length(model)
