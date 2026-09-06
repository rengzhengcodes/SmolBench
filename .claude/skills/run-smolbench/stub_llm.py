"""Two local OpenAI-compatible stub LLM servers for driving a REAL lean sweep.

Used by `lean_smoke.sh --e2e`: fake models, real Lean verification.

Port A (model "stub-good-model", provider `primeintellect`) answers every chat
completion with the CORRECT ground-truth tail for Lagrange.eval_nodal_at_node
at k=1, fenced as ```lean, so the sweep row must come back `verdict: success`.
Port B (model "stub-bad-model", provider `openrouter`) answers with a bogus
tactic, so the row must be `verdict: lean_error` ("unknown identifier
'nonexistent_lemma_xyz42'").

Both servers also answer the providers' context-length GETs (OpenRouter's
`/endpoints` shape and Prime Intellect's `/models/<id>` shape). Every request
is logged as one JSON line to argv[1] so the caller can assert what the sweep
actually sent (seed / system message / temperature / model). Ports are
OS-assigned and printed once to stdout as {"pi": <port>, "or": <port>}, before
either server starts serving.

Reuses `tests/conftest.py`'s `StubServer`, exactly as `driver.py` beside this
file does, so the stub DIALECT -- response shapes, the SSE re-emission, the two
context-length GET routes -- has one source of truth instead of a second
hand-rolled copy that can drift from the one the offline test suite exercises.
This file therefore needs pytest importable (the `dev` extra), not just the
standard library.
"""

import json
import sys
import threading
from pathlib import Path

# Same repo-root bootstrap as `driver.py` beside this file: this script lives
# three directories below the repo root (.claude/skills/run-smolbench/), and is
# run by path rather than as a package, so `tests.conftest` is importable only
# once the root is on sys.path.
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

try:
    # Reused from the offline test suite so the stub dialect has one source of
    # truth (needs pytest importable -- it's in the dev extra).
    from tests.conftest import StubServer, chat_completion
except ImportError as err:
    # stderr, not stdout: `lean_smoke.sh` redirects this process's stdout into
    # ports.json and parses it as JSON, so anything printed there is corruption.
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

#: The two answers, byte-identical to what this file served before it was
#: rewritten onto `StubServer`. GOOD is the real ground-truth tail of
#: Lagrange.eval_nodal_at_node at k=1; BAD names a lemma that does not exist,
#: which is what makes real Lean return `lean_error` rather than a failed goal.
GOOD = "Here is the proof:\n```lean\nexact s.prod_eq_zero hi (sub_self (v i))\n```"
BAD = "```lean\nexact nonexistent_lemma_xyz42\n```"

#: One lock for both servers' log writes. `StubServer` is a
#: `ThreadingHTTPServer`, so handlers run concurrently and two interleaved
#: writes would produce a torn JSON line.
LOG_LOCK = threading.Lock()


class _LoggingRequestList(list):
    """A `StubServer.requests` list that also appends each request to a file.

    `StubServer` records every request -- POSTs and GETs alike -- by calling
    ``self.server.requests.append(...)`` from its handler. Subclassing the
    LIST, rather than overriding the handler, is deliberate: the handler is
    where the stub's dialect lives (the chat-completions response shape, the
    SSE re-emission, the OpenRouter vs Prime Intellect GET routes), and that
    dialect must keep exactly one definition in ``tests/conftest.py`` so this
    smoke path and the offline test suite cannot drift apart. The on-disk log
    is the only genuinely skill-specific behaviour here, and `append` is the
    one seam it needs. ``tests/conftest.py`` is not modified.

    Parameters
    ----------
    stub : str
        Which server this list belongs to, ``"PI"`` or ``"OR"``; written into
        every line as the ``stub`` field, as before.
    path : str
        Log file to append to.

    Notes
    -----
    The in-memory element keeps the handler's full ``{path, body, headers}``
    dict, so anything reading ``server.requests`` still sees what conftest
    promises. Only the DISK line is narrowed, to the same three keys
    (``stub``, ``path``, ``body``) this file wrote before, so a log stays
    comparable with an older run's.

    GET lines are logged too, because conftest's handler records GETs as well,
    and they carry ``"body": null``. That is safe for the only consumer:
    `lean_smoke.sh --e2e` filters ``r["path"].endswith("/chat/completions")``
    before reading ``r["body"]["model"]``, so a context-length GET line never
    reaches a subscript of ``None``.

    Thread-safety: `append` runs on `ThreadingHTTPServer` handler threads, so
    the file write is serialized under `LOG_LOCK`. The list append itself is
    already atomic under the GIL, as it was before.
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

    Parameters
    ----------
    stub : str
        Short name for the log's ``stub`` field: ``"PI"`` or ``"OR"``.
    answer : str
        Assistant message content returned for EVERY chat completion.

    Returns
    -------
    StubServer
        Bound to an OS-assigned port on 127.0.0.1, not yet serving.

    Notes
    -----
    The answer is installed as `default_response`, never queued: `StubServer`
    pops queued responses FIFO, which is order-dependent, whereas this sweep
    issues an unknown number of completions (a sanity gate, the cell, plus any
    retries) and every one must get the same answer.

    The usage stanza and ``finish_reason`` reproduce what this file served
    before the rewrite, so the sweep's rows keep the same token counts and stop
    reason. The response no longer ECHOES the request's ``model`` back, as the
    old hand-rolled handler did -- a static `default_response` cannot see the
    request, and a constant would be a claim about who is calling rather than
    an echo. No observable behaviour changes: ``openai_compat.py``'s
    ``reported_model: str = body.get("model") or model`` falls back to the
    REQUEST's model when the body omits one, so ``rsp.model`` -- and hence a
    row's ``api_model`` -- is still ``"stub-good-model"``. That fallback is
    already load-bearing for the offline suite, where
    ``tests/deduction/test_lean_runner.py`` asserts ``r["api_model"] == M1``
    against `chat_completion` bodies that carry no ``model`` key either.
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

# Both ports are printed BEFORE either server starts serving, so the caller can
# never read a port that is not yet bound. `flush` matters: stdout is redirected
# into ports.json here, so without it the line could sit in the buffer while
# lean_smoke.sh polls an empty file and then fails.
print(json.dumps({"pi": srv_pi.server_address[1], "or": srv_or.server_address[1]}), flush=True)

# The PI server runs on a daemon thread and the OR server on the main one, so
# the process blocks here until the parent kills it -- lean_smoke.sh's EXIT trap
# owns that. Serving OR in the foreground, rather than starting a second thread
# and sleeping, keeps the process's lifetime tied to a real server.
threading.Thread(target=srv_pi.serve_forever, daemon=True).start()
srv_or.serve_forever()
