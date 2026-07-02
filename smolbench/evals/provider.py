"""
Dispatches to the active inference provider based on INFERENCE_PROVIDER.

Set INFERENCE_PROVIDER=openrouter (default), primeintellect, aws (Amazon
Bedrock by default; set AWS_INFERENCE_BASE_URL to target a SageMaker
endpoint), or ec2 (a self-provisioned EC2 spot instance running vLLM; the
endpoint is resolved at call time from the local state file written by
smolbench.evals.ec2.provision_spot_instance) in keys.env, then import
query/evaluate/get_model_context_length from this module instead of a
provider-specific one.

Dispatch happens at CALL time: INFERENCE_PROVIDER is read (and the provider
module imported) on each call, not when this module is imported. Notebooks
therefore only need their env configured -- e.g. via load_dotenv(keys.env) --
before the first query/evaluate call, not before any import, and switching
providers mid-session is just a matter of changing the env var.
"""

import importlib
import os
from types import ModuleType

#: Provider name -> module implementing query/evaluate/get_model_context_length.
_PROVIDER_MODULES: dict[str, str] = {
    "openrouter": "smolbench.evals.openrouter",
    "primeintellect": "smolbench.evals.primeintellect",
    "aws": "smolbench.evals.aws",
    "bedrock": "smolbench.evals.aws",
    "sagemaker": "smolbench.evals.aws",
    "ec2": "smolbench.evals.ec2",
}


def _provider_module() -> ModuleType:
    """Resolves the active provider module from the environment.

    Raises an actionable error for unknown providers, and for
    INFERENCE_PROVIDER=sagemaker without a base URL: the aws module defaults
    to the Bedrock URL, so selecting sagemaker without one would silently hit
    Bedrock instead. (The ec2 provider needs no such guard -- it raises its
    own actionable error at call time when no instance has been provisioned.)
    """
    name = os.getenv("INFERENCE_PROVIDER", "openrouter").lower()
    if name not in _PROVIDER_MODULES:
        raise ValueError(
            f"Unknown INFERENCE_PROVIDER={name!r}. "
            "Valid options: 'openrouter', 'primeintellect', 'aws'/'bedrock', "
            "'sagemaker', 'ec2'."
        )
    if name == "sagemaker" and not os.getenv("AWS_INFERENCE_BASE_URL"):
        raise ValueError(
            "INFERENCE_PROVIDER=sagemaker requires AWS_INFERENCE_BASE_URL="
            "https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{endpoint}/openai/v1"
        )
    return importlib.import_module(_PROVIDER_MODULES[name])


def query(*args, **kwargs):
    """The active provider's query; see ChatClient.query for parameters."""
    return _provider_module().query(*args, **kwargs)


def evaluate(*args, **kwargs):
    """The active provider's evaluate; see ChatClient.evaluate for parameters.

    Every provider shares one implementation (smolbench.evals.openai_compat),
    so per-call tuning -- extra_args, max_parallel, request_timeout,
    show_progress -- works identically regardless of INFERENCE_PROVIDER.
    """
    return _provider_module().evaluate(*args, **kwargs)


def get_model_context_length(model: str) -> int:
    """The active provider's context-window lookup for ``model``."""
    return _provider_module().get_model_context_length(model)
