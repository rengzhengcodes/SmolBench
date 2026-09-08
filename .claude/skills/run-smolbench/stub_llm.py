"""Two local OpenAI-compatible stub LLM servers for driving a real Lean sweep.

Used by `lean_smoke.sh --e2e`: fake models, real Lean verification. Port A
(model "stub-good-model") always answers with the correct ground-truth tactic
for the post-cutoff fixture's `Mini.theoremA`, so the row must verify. Port B
(model "stub-bad-model") answers with a bogus tactic, so the row must come
back `lean_error`. Both also answer the providers' context-length GETs
(OpenRouter's `/endpoints`, Prime Intellect's `/models/<id>`). Every request
is logged as one JSON line to argv[1]. Ports are OS-assigned and printed once
to stdout as {"pi": <port>, "or": <port>}, before either server starts serving.

Reuses `tests/conftest.py`'s `StubServer`, like `driver.py` beside this file,
so the stub dialect has one source of truth instead of a second hand-rolled
copy that can drift from the offline suite.
"""

import json
import sys
import threading
from pathlib import Path

# Same repo-root bootstrap as `driver.py`: run by path rather than as a
# package, so `tests.conftest` needs the root on sys.path first.
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

try:
    from tests.conftest import StubServer, chat_completion
except ImportError as err:
    # stderr, not stdout: lean_smoke.sh redirects stdout into ports.json and
    # parses it as JSON, so anything printed there is corruption.
    print(
        f"FAIL: cannot import tests.conftest ({err}).\n"
        f"Expected tests/conftest.py under {REPO_ROOT} and pytest installed "
        "-- run `uv sync --all-extras` from the repo root.",
        file=sys.stderr,
    )
    sys.exit(2)

#: Where every request is logged, one JSON line each. `lean_smoke.sh --e2e`
#: passes a path inside its mktemp working directory.
REQLOG = sys.argv[1]

#: GOOD is the real final proof step for `Mini.theoremA`; BAD
#: names a lemma that does not exist, so real Lean returns `lean_error`.
GOOD = "Here is the proof:\n```lean\nexact Mini.premiseA h (Mini.premiseB n)\n```"
BAD = "```lean\nexact nonexistent_lemma_xyz42\n```"

#: `StubServer` is a `ThreadingHTTPServer`, so handlers run concurrently;
#: this serializes log writes to avoid a torn JSON line.
LOG_LOCK = threading.Lock()


class _LoggingRequestList(list):
    """A `StubServer.requests` list that also appends each request to a file.

    Subclassing the list, rather than overriding the handler, is deliberate:
    the handler is where the stub dialect lives (response shapes, SSE
    re-emission, the OpenRouter vs Prime Intellect GET routes), and that has
    to stay defined once in `tests/conftest.py`. The disk line narrows each
    request to `{stub, path, body}`; `stub` is `"PI"` or `"OR"`. GET requests
    are logged too, with `body: null` -- safe, since `lean_smoke.sh --e2e`
    only reads `body["model"]` after filtering to `/chat/completions` paths.
    `append` runs on `ThreadingHTTPServer` handler threads, so the file write
    is serialized under `LOG_LOCK`.
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
    """Build a logging `StubServer` that answers every completion with `answer`.

    `answer` is installed as `default_response`, never queued: `StubServer`
    pops queued responses FIFO, but this sweep issues an unknown number of
    completions (sanity gate, cell, retries), all needing the same answer.
    The response does not echo the request's `model` back -- a static
    `default_response` can't see the request -- but `openai_compat.py` falls
    back to the request's model when the body omits one, so `rsp.model` (and
    a row's `api_model`) is still correct; `test_lean_runner.py` already
    relies on that same fallback with model-less `chat_completion` bodies.

    Parameters
    ----------
    stub : str
        Label written with each logged request.
    answer : str
        Response body for every completion.

    Returns
    -------
    StubServer
        Configured logging server.
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

# Ports print before either server serves, so the caller never reads an
# unbound port. `flush` matters: stdout feeds ports.json, and an unflushed
# line could sit in the buffer while lean_smoke.sh polls an empty file.
print(json.dumps({"pi": srv_pi.server_address[1], "or": srv_or.server_address[1]}), flush=True)

# PI runs on a daemon thread, OR on the main thread, so the process blocks
# here until lean_smoke.sh's EXIT trap kills it -- ties the process's
# lifetime to a real server rather than a sleep loop.
threading.Thread(target=srv_pi.serve_forever, daemon=True).start()
srv_or.serve_forever()
