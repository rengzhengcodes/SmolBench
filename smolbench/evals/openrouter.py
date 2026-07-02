"""
Interfacing directly with the OpenRouter API.

A thin configuration over :mod:`smolbench.evals.openai_compat`, which holds
the retry loop, response parsing, and parallel evaluation shared by every
provider; only OpenRouter's endpoint, auth, and context-length lookup live
here.

Setup
-----
    OPENROUTER_API_KEY=<api key>
    INFERENCE_PROVIDER=openrouter   # to route smolbench.evals.provider here

Tuning env vars (read at call time): ``OPENROUTER_MAX_PARALLEL_REQUESTS``
(default 8), ``OPENROUTER_INFO`` / ``OPENROUTER_INFO_RESPONSE`` (verbose
logging). ``OPENROUTER_BASE_URL`` overrides the API root (offline stub
tests; see tests/).
"""

import functools
import os
from typing import Any, Dict, Tuple

import requests

from smolbench.evals.openai_compat import ChatClient

OPENROUTER_RETRY_BACKOFF_SECONDS: int = 60
_DEFAULT_BASE_URL: str = "https://openrouter.ai/api/v1"


def _base_url() -> str:
    """API root, resolved at call time so env overrides need no re-import."""
    return os.getenv("OPENROUTER_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")


def _connection(model: str) -> Tuple[str, str]:
    """Returns the chat-completions URL and bearer token."""
    return f"{_base_url()}/chat/completions", os.getenv("OPENROUTER_API_KEY", "")


@functools.lru_cache(maxsize=None)
def get_model_context_length(model: str) -> int:
    """Fetches the model context window from segments.

    A model's window is constant, so the network lookup is cached: evaluate()
    is called once per replicate and re-fetching one integer per call costs
    a round trip plus a fresh chance to trip a 429.
    """
    response: Dict[str, Any] = requests.get(
        url=f"{_base_url()}/models/{model}/endpoints",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY', '')}",
        },
        timeout=120,
    ).json()

    # pick the first available endpoint
    ctx: int = response["data"]["endpoints"][0]["context_length"]
    return ctx


_CLIENT = ChatClient(
    name="OpenRouter",
    env_prefix="OPENROUTER",
    connection=_connection,
    context_length=get_model_context_length,
    retry_backoff_s=OPENROUTER_RETRY_BACKOFF_SECONDS,
)

# The provider-facing API (dispatched via smolbench.evals.provider); full
# parameter docs live on ChatClient.query / ChatClient.evaluate.
query = _CLIENT.query
evaluate = _CLIENT.evaluate
