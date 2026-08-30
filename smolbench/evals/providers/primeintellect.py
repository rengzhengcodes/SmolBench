"""
Interface directly with the Prime Intellect inference API.

A thin configuration over :mod:`smolbench.evals.openai_compat` (the shared
retry/parsing/evaluation core); only Prime Intellect's endpoint, auth and
context-length lookup live here.

Env, all read at call time: ``PRIME_INTELLECT_API_KEY``,
``INFERENCE_PROVIDER=primeintellect`` (routes smolbench.evals.provider here),
``PRIME_INTELLECT_MAX_PARALLEL_REQUESTS`` (default 8),
``PRIME_INTELLECT_INFO`` / ``PRIME_INTELLECT_INFO_RESPONSE`` (verbose
logging), ``PRIME_INTELLECT_TEAM_ID`` (team billing; see ``_extra_headers``),
``PRIME_INTELLECT_BASE_URL`` (overrides the API root; offline stub tests).
"""

import functools
import os
from typing import Any, Dict, Tuple

from smolbench.evals.openai_compat import ChatClient, metadata_get

PRIME_INTELLECT_RETRY_BACKOFF_SECONDS: int = 60
_DEFAULT_BASE_URL: str = "https://api.pinference.ai/api/v1"


def _base_url() -> str:
    """Return the API root, resolved at call time so an override needs no re-import."""
    return os.getenv("PRIME_INTELLECT_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")


def _connection(model: str) -> Tuple[str, str]:
    """Return the chat-completions URL and bearer token."""
    return f"{_base_url()}/chat/completions", os.getenv("PRIME_INTELLECT_API_KEY", "")


def _extra_headers(model: str) -> Dict[str, str]:
    """Return the ``X-Prime-Team-ID`` billing header, or ``{}`` for a personal account.

    ``PRIME_INTELLECT_TEAM_ID`` is read on every request attempt, so setting it
    in keys.env alongside the API key needs no re-import.
    """
    team_id = os.getenv("PRIME_INTELLECT_TEAM_ID", "")
    return {"X-Prime-Team-ID": team_id} if team_id else {}


@functools.lru_cache(maxsize=None)
def get_model_context_length(model: str) -> int:
    """Get `model`'s context window from Prime Intellect.

    A model's window is constant, so the lookup is cached, keyed on `model`
    alone; see the OpenRouter twin of this function for the rationale and for
    what that key omits.
    """
    response: Dict[str, Any] = metadata_get(
        f"{_base_url()}/models/{model}",
        os.getenv("PRIME_INTELLECT_API_KEY", ""),
        check_status=False,  # unchecked -- see metadata_get's check_status doc
    )

    ctx: int = response["context_length"]
    return ctx


_CLIENT = ChatClient(
    name="Prime Intellect",
    env_prefix="PRIME_INTELLECT",
    connection=_connection,
    context_length=get_model_context_length,
    extra_headers=_extra_headers,
    retry_backoff_s=PRIME_INTELLECT_RETRY_BACKOFF_SECONDS,
)

# The provider-facing API; see ChatClient.query/complete/evaluate.
query = _CLIENT.query
complete = _CLIENT.complete
evaluate = _CLIENT.evaluate
