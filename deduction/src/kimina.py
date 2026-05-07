"""HTTP client for the local kimina-lean-server's `/verify` endpoint.

The server expects POSTs of shape

    {"codes": [{"custom_id": "<any>", "proof": "<lean source>"}]}

and returns

    {"results": [{"custom_id": "...", "response": {"messages": [...]}}]}

where `messages` is a list of dicts with `severity` ("error" | "warning" |
"info") and `data` (the diagnostic text). A submission passes verification iff
no message has severity == "error".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import requests


KIMINA_URL_DEFAULT = "http://localhost:9000"


@dataclass(frozen=True, slots=True)
class VerifyResult:
    ok: bool
    messages: List[dict] = field(default_factory=list)
    raw_response: Optional[dict] = None
    transport_error: Optional[str] = None  # set when the request itself failed


def verify(
    source: str,
    *,
    server_url: str = KIMINA_URL_DEFAULT,
    timeout: int = 180,
    custom_id: str = "x",
) -> VerifyResult:
    """Submit a complete Lean source file for verification.

    `ok` is True iff Kimina returns at least one result and that result has
    no error-severity messages. Transport-level errors (server down, timeout,
    bad JSON) populate `transport_error` and set `ok=False`."""
    try:
        r = requests.post(
            f"{server_url}/verify",
            json={"codes": [{"custom_id": custom_id, "proof": source}]},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        return VerifyResult(ok=False, transport_error=f"request: {e}")
    except ValueError as e:  # JSON decode
        return VerifyResult(ok=False, transport_error=f"json: {e}")

    results = data.get("results", []) if isinstance(data, dict) else []
    if not results:
        return VerifyResult(ok=False, raw_response=data,
                            transport_error="no results returned")

    response = results[0].get("response", {})
    messages = response.get("messages", []) if isinstance(response, dict) else []
    has_error = any(m.get("severity") == "error" for m in messages)
    return VerifyResult(ok=not has_error, messages=messages, raw_response=data)


def is_up(server_url: str = KIMINA_URL_DEFAULT, timeout: int = 5) -> bool:
    """Cheap reachability probe: send the smallest valid verify request and
    check we get a structurally-correct response. Returns False on any kind
    of failure (server down, timeout, bad JSON)."""
    res = verify("example : True := trivial\n", server_url=server_url, timeout=timeout)
    return res.transport_error is None
