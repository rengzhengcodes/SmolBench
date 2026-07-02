"""
Interfacing directly with the Prime Intellect inference API.

A thin configuration over :mod:`smolbench.evals.openai_compat`, which holds
the retry loop, response parsing, and parallel evaluation shared by every
provider; only Prime Intellect's endpoint, auth, and context-length lookup
live here.

Setup
-----
    PRIME_INTELLECT_API_KEY=<api key>
    INFERENCE_PROVIDER=primeintellect   # to route smolbench.evals.provider here

Tuning env vars (read at call time): ``PRIME_INTELLECT_MAX_PARALLEL_REQUESTS``
(default 8), ``PRIME_INTELLECT_INFO`` / ``PRIME_INTELLECT_INFO_RESPONSE``
(verbose logging). ``PRIME_INTELLECT_BASE_URL`` overrides the API root
(offline stub tests; see tests/).
"""

import functools
import os
from typing import Any, Dict, Tuple

import requests

from smolbench.evals.openai_compat import ChatClient, METADATA_TIMEOUT_S

PRIME_INTELLECT_RETRY_BACKOFF_SECONDS: int = 60
_DEFAULT_BASE_URL: str = "https://api.pinference.ai/api/v1"


def _base_url() -> str:
    """API root, resolved at call time so env overrides need no re-import."""
    return os.getenv("PRIME_INTELLECT_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")


def _connection(model: str) -> Tuple[str, str]:
    """Returns the chat-completions URL and bearer token."""
    return f"{_base_url()}/chat/completions", os.getenv("PRIME_INTELLECT_API_KEY", "")


@functools.lru_cache(maxsize=None)
def get_model_context_length(model: str) -> int:
    """Fetches the model context window from Prime Intellect.

    A model's window is constant, so the network lookup is cached (see the
    OpenRouter twin of this function for the rationale).
    """
    response: Dict[str, Any] = requests.get(
        url=f"{_base_url()}/models/{model}",
        headers={
            "Authorization": f"Bearer {os.getenv('PRIME_INTELLECT_API_KEY', '')}",
        },
        timeout=METADATA_TIMEOUT_S,
    ).json()

    ctx: int = response["context_length"]
    return ctx


_CLIENT = ChatClient(
    name="Prime Intellect",
    env_prefix="PRIME_INTELLECT",
    connection=_connection,
    context_length=get_model_context_length,
    retry_backoff_s=PRIME_INTELLECT_RETRY_BACKOFF_SECONDS,
)

# The provider-facing API (dispatched via smolbench.evals.provider); full
# parameter docs live on ChatClient.query / ChatClient.evaluate.
query = _CLIENT.query
evaluate = _CLIENT.evaluate
