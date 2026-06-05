"""
Dispatches to the active inference provider based on INFERENCE_PROVIDER env var.

Set INFERENCE_PROVIDER=openrouter (default), primeintellect, or aws (Amazon
Bedrock by default; set AWS_INFERENCE_BASE_URL to target a SageMaker endpoint)
in keys.env, then import from this module instead of a provider-specific one.
"""

import os
from typing import Any, Optional

from smolbench.evals import Quiz, Marks

_PROVIDER = os.getenv("INFERENCE_PROVIDER", "openrouter").lower()

if _PROVIDER == "primeintellect":
    from smolbench.evals.primeintellect import query, evaluate, get_model_context_length
elif _PROVIDER == "openrouter":
    from smolbench.evals.openrouter import query, evaluate, get_model_context_length
elif _PROVIDER in ("aws", "bedrock"):
    from smolbench.evals.aws import query, evaluate, get_model_context_length
elif _PROVIDER == "sagemaker":
    # The aws module defaults to the Bedrock URL; selecting sagemaker without a
    # base URL would silently hit Bedrock instead, so require it explicitly.
    if not os.getenv("AWS_INFERENCE_BASE_URL"):
        raise ValueError(
            "INFERENCE_PROVIDER=sagemaker requires AWS_INFERENCE_BASE_URL="
            "https://runtime.sagemaker.{region}.amazonaws.com/endpoints/{endpoint}/openai/v1"
        )
    from smolbench.evals.aws import query, evaluate, get_model_context_length
else:
    raise ValueError(
        f"Unknown INFERENCE_PROVIDER={_PROVIDER!r}. "
        "Valid options: 'openrouter', 'primeintellect', 'aws'/'bedrock', 'sagemaker'."
    )
