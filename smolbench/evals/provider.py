"""
Dispatch to the active inference provider, based on INFERENCE_PROVIDER.

Set INFERENCE_PROVIDER in keys.env to one of the keys below (default
"openrouter"), then import query/complete/evaluate/get_model_context_length
from here. "aws" is Bedrock unless AWS_INFERENCE_BASE_URL targets a SageMaker
endpoint; "ec2" is a self-provisioned vLLM spot instance whose endpoint is
resolved at call time from the state file written by
smolbench.evals.providers.ec2.provision_spot_instance.

Dispatch happens at CALL time -- the env var is read and the module imported on
each call -- so a notebook only needs its env configured before the first
query/evaluate call, not before any import. To mix providers per model in one
process (one env var cannot express that), resolve explicitly with
provider_module("ec2"), which bypasses the environment; smolbench.deduction.lean
uses that pattern. This module only dispatches: the AWS provisioning primitives
shared by aws.py and ec2.py live in smolbench.evals._aws.
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

    Parameters
    ----------
    name : str, optional
        Explicit provider name, bypassing the environment entirely (so a
        mixed-provider sweep is unaffected by INFERENCE_PROVIDER); None (the
        default) dispatches from ``INFERENCE_PROVIDER`` ("openrouter" unset).

    Raises
    ------
    ValueError
        Unrecognized provider name, or "sagemaker" with no
        AWS_INFERENCE_BASE_URL set -- the aws module defaults to the Bedrock
        URL, so it would otherwise silently hit Bedrock. (ec2 needs no such
        guard: it raises at call time when it finds no provisioned instance.)
    """
    resolved = (name if name is not None else os.getenv("INFERENCE_PROVIDER", "openrouter")).lower()
    if resolved not in _PROVIDER_MODULES:
        # Says INFERENCE_PROVIDER for env dispatch, which tests match on.
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
    """Query the active provider, returning the full ``ChatResult`` (usage,
    server-reported model, finish_reason) instead of query's narrowed
    ``(content, reasoning)`` 2-tuple; see ChatClient.complete."""
    return provider_module().complete(*args, **kwargs)


def evaluate(*args, **kwargs):
    """Evaluate a quiz on the active provider; see ChatClient.evaluate."""
    return provider_module().evaluate(*args, **kwargs)


def get_model_context_length(model: str) -> int:
    """Look up the active provider's context window for `model`."""
    return provider_module().get_model_context_length(model)
