"""
Interface directly with the OpenRouter API.

A thin configuration over :mod:`smolbench.evals.openai_compat` (the shared
retry/parsing/evaluation core); only OpenRouter's endpoint, auth and
context-length lookup live here.

Env, all read at call time: ``OPENROUTER_API_KEY``,
``INFERENCE_PROVIDER=openrouter`` (routes smolbench.evals.provider here),
``OPENROUTER_MAX_PARALLEL_REQUESTS`` (default 8), ``OPENROUTER_INFO`` /
``OPENROUTER_INFO_RESPONSE`` (verbose logging), ``OPENROUTER_BASE_URL``
(overrides the API root; offline stub tests).
"""

import functools
import os
from typing import Any, Dict, Tuple

from smolbench.evals.openai_compat import ChatClient, metadata_get

OPENROUTER_RETRY_BACKOFF_SECONDS: int = 60
_DEFAULT_BASE_URL: str = "https://openrouter.ai/api/v1"


def _base_url() -> str:
    """Return the API root, resolved at call time so an override needs no re-import."""
    return os.getenv("OPENROUTER_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")


def _connection(model: str) -> Tuple[str, str]:
    """Return the chat-completions URL and bearer token."""
    return f"{_base_url()}/chat/completions", os.getenv("OPENROUTER_API_KEY", "")


@functools.lru_cache(maxsize=None)
def get_model_context_length(model: str) -> int:
    """Get `model`'s context window from its OpenRouter endpoint listing.

    A model's window is constant, so the lookup is cached: evaluate() calls it
    once per replicate, and re-fetching one integer would cost a round trip
    plus a fresh chance to trip a 429.
    """
    response: Dict[str, Any] = metadata_get(
        f"{_base_url()}/models/{model}/endpoints",
        os.getenv("OPENROUTER_API_KEY", ""),
        check_status=False,  # unchecked -- see metadata_get's check_status doc
    )

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
# parameter docs live on ChatClient.query / ChatClient.complete / ChatClient.evaluate.
query = _CLIENT.query
complete = _CLIENT.complete  # ChatResult-returning superset of query (usage, model, finish_reason)
evaluate = _CLIENT.evaluate
