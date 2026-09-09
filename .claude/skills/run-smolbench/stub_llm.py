"""Run local OpenAI-compatible stubs for a real Lean sweep.

The good fixture proof must verify and the bogus one must return `lean_error`.
Port A serves model "stub-good-model" and Port B serves "stub-bad-model"; OS-assigned
ports print once to stdout as {"pi": <port>, "or": <port>} before serving.
Reuse `tests.conftest.StubServer` so the stub dialect has one source of truth.
"""

import json
import sys
import threading
from pathlib import Path

# Run by path, so `tests.conftest` needs the repository root on sys.path.
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

try:
    from tests.conftest import StubServer, chat_completion
except ImportError as err:
    # stdout is ports.json, so diagnostics there would corrupt JSON.
    print(
        f"FAIL: cannot import tests.conftest ({err}).\n"
        f"Expected tests/conftest.py under {REPO_ROOT} and pytest installed "
        "-- run `uv sync --all-extras` from the repo root.",
        file=sys.stderr,
    )
    sys.exit(2)

#: Request log path, supplied by `lean_smoke.sh --e2e`.
REQLOG = sys.argv[1]

#: GOOD proves `Mini.theoremA`; BAD names a lemma that does not exist, so Lean returns `lean_error`.
GOOD = "Here is the proof:\n```lean\nexact Mini.premiseA h (Mini.premiseB n)\n```"
BAD = "```lean\nexact nonexistent_lemma_xyz42\n```"

#: Handlers are concurrent, so this prevents torn JSON log lines.
LOG_LOCK = threading.Lock()


class _LoggingRequestList(list):
    """Request list that appends `{stub, path, body}` JSON lines under `LOG_LOCK`.

    Subclass the list so the stub dialect stays defined once in `tests/conftest.py`.
    GET requests are logged too, with `body: null`, and filtered by path before body access.
    """

    def __init__(self, stub: str, path: str) -> None:
        super().__init__()
        self._stub = stub
        self._path = path

    def append(self, request: dict) -> None:
        """Record `request` in memory and as one JSON line in the log file."""
        super().append(request)
        line = json.dumps(
            {"stub": self._stub, "path": request.get("path"), "body": request.get("body")}
        )
        with LOG_LOCK, open(self._path, "a") as fh:
            fh.write(line + "\n")


def make_server(stub: str, answer: str) -> StubServer:
    """Build a logging server with one response for an unknown number of completions.

    `default_response` is required because queued responses are FIFO; model fallback keeps `rsp.model` correct.

    Parameters
    ----------
    stub : str
        Logged request label.
    answer : str
        Completion response.

    Returns
    -------
    StubServer
        Logging server.
    """
    server = StubServer()
    server.requests = _LoggingRequestList(stub, REQLOG)
    body = chat_completion(
        answer, usage={"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
    )
    body["choices"][0]["finish_reason"] = "stop"
    server.default_response = body
    return server


srv_pi = make_server("PI", GOOD)
srv_or = make_server("OR", BAD)

# Print and flush ports before serving so `ports.json` never exposes an unbound port.
print(json.dumps({"pi": srv_pi.server_address[1], "or": srv_or.server_address[1]}), flush=True)

# The main server keeps the process alive until `lean_smoke.sh` kills it.
threading.Thread(target=srv_pi.serve_forever, daemon=True).start()
srv_or.serve_forever()
