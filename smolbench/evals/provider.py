"""
Dispatches to the active inference provider based on INFERENCE_PROVIDER env var.

Set INFERENCE_PROVIDER=openrouter (default) or INFERENCE_PROVIDER=primeintellect
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
else:
    raise ValueError(
        f"Unknown INFERENCE_PROVIDER={_PROVIDER!r}. "
        "Valid options: 'openrouter', 'primeintellect'."
    )
