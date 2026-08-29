"""
Dispatch to the active inference provider, based on INFERENCE_PROVIDER.

Set INFERENCE_PROVIDER in keys.env to one of: openrouter (the default),
primeintellect, aws (Amazon Bedrock by default; set AWS_INFERENCE_BASE_URL
to target a SageMaker endpoint instead), or ec2 (a self-provisioned EC2
spot instance running vLLM). For ec2, the endpoint is resolved at call
time from the local state file written by
smolbench.evals.providers.ec2.provision_spot_instance. Then import
query/complete/evaluate/get_model_context_length from this module, instead
of from a provider-specific one.

Dispatch happens at CALL time: this module reads INFERENCE_PROVIDER, and
imports the provider module, on each call -- not when this module itself
is imported. A notebook therefore only needs its env configured (e.g. via
load_dotenv(keys.env)) before the first query/evaluate call, not before
any import. Switching providers mid-session is just a matter of changing
the env var.

A caller that needs to mix providers per model within one process -- e.g.
a Lean sweep runner iterating over models that live on different
providers, where a single INFERENCE_PROVIDER env var cannot express "this
model via ec2, that one via openrouter" at the same time -- can resolve a
provider module explicitly via provider_module("ec2"). That call bypasses
the environment entirely, instead of going through the env-dispatched
query/evaluate/complete/get_model_context_length functions below.
smolbench.deduction.lean uses exactly this explicit-name pattern;
everything else uses env dispatch.

This module only dispatches; it holds no provisioning logic of its own.
The AWS-specific provisioning primitives shared by aws.py (SageMaker) and
ec2.py (EC2 Spot) -- fresh-Session clients, IAM role setup, the generic
poll loop, teardown -- live in smolbench.evals._aws. Each provider builds
its own deploy/serve/teardown lifecycle on top of those primitives, in
aws.py/ec2.py respectively; see _aws.py's module docstring for the
lifecycle-correspondence table between the two.
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

    ``name=None`` (the default) reproduces the original env-dispatch
    behavior: this function reads INFERENCE_PROVIDER from the environment
    (default "openrouter" when unset). Passing an explicit `name` bypasses
    the environment entirely and resolves that provider directly. See the
    module docstring for why a caller (e.g. a Lean sweep runner mixing
    providers per model) would want that, instead of the env-dispatched
    query/evaluate/complete/get_model_context_length functions below.

    This function raises an actionable error for an unknown provider name
    (explicit or from INFERENCE_PROVIDER). It also raises when the
    resolved name is "sagemaker" with no base URL set: the aws module
    defaults to the Bedrock URL, so selecting sagemaker with no base URL
    would silently hit Bedrock instead. This guard applies the same way
    whether "sagemaker" came from the environment or was passed explicitly
    as `name`. The ec2 provider needs no such guard -- it raises its own
    actionable error at call time when it finds no provisioned instance.

    Parameters
    ----------
    name : str, optional
        Provider name (e.g. "openrouter", "aws", "bedrock", "sagemaker",
        "ec2"), or None to dispatch from INFERENCE_PROVIDER instead.

    Returns
    -------
    ModuleType
        The imported provider module. It exposes ``query``/``complete``/
        ``evaluate``/``get_model_context_length``.

    Raises
    ------
    ValueError
        The resolved name is not a recognized provider, or it resolves to
        "sagemaker" with no AWS_INFERENCE_BASE_URL set.
    """
    # Design: an explicit `name` bypasses the environment lookup entirely
    # rather than merely overriding it, so a caller resolving "ec2" here
    # is unaffected by whatever INFERENCE_PROVIDER happens to be set to
    # elsewhere in the process (needed for mixed-provider sweeps).
    resolved = (name if name is not None else os.getenv("INFERENCE_PROVIDER", "openrouter")).lower()
    if resolved not in _PROVIDER_MODULES:
        # Error text keeps saying "INFERENCE_PROVIDER" for the env-dispatch
        # case (name=None) so it stays byte-identical to the pre-rename
        # message notebooks/tests may already match on; explicit-name
        # lookups get a generic "provider" label instead.
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
    """Query the active provider; see ChatClient.complete for the parameters.

    Returns the full ``ChatResult`` (content, reasoning, token usage,
    server-reported model, finish_reason), instead of query's narrowed
    ``(content, reasoning)`` 2-tuple.
    """
    return provider_module().complete(*args, **kwargs)


def evaluate(*args, **kwargs):
    """Evaluate a quiz on the active provider; see ChatClient.evaluate.

    Every provider shares one implementation
    (smolbench.evals.openai_compat), so per-call tuning -- extra_args,
    max_parallel, request_timeout, show_progress -- works the same way
    regardless of INFERENCE_PROVIDER.
    """
    return provider_module().evaluate(*args, **kwargs)


def get_model_context_length(model: str) -> int:
    """Look up the active provider's context window for `model`."""
    return provider_module().get_model_context_length(model)
