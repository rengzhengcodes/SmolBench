"""Shared fixtures: a local OpenAI-compatible stub server.

Everything in tests/ runs OFFLINE -- no AWS credentials, no network. The stub
speaks just enough of the Chat Completions dialect to exercise the shared
client in smolbench/evals/openai_compat.py through every provider module.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


class _StubHandler(BaseHTTPRequestHandler):
    """Replays the server's scripted response and records request bodies."""

    def _reply(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        payload = json.loads(self.rfile.read(length) or b"{}")
        # Headers are recorded alongside the body so tests can assert on
        # auth/routing headers (e.g. Prime Intellect's X-Prime-Team-ID).
        self.server.requests.append(
            {"path": self.path, "body": payload, "headers": dict(self.headers)}
        )
        self._reply(self.server.next_response())

    def do_GET(self):
        self.server.requests.append({"path": self.path, "body": None})
        if self.path.endswith("/endpoints"):
            # OpenRouter-style context-length listing.
            self._reply({"data": {"endpoints": [{"context_length": 100000}]}})
        elif "/models/" in self.path:
            # Prime-Intellect-style model info.
            self._reply({"context_length": 100000})
        else:
            # Generic /models listing (aws/ec2 list_models).
            self._reply({"data": [{"id": "stub-model"}]})

    def log_message(self, *args):
        pass  # keep pytest output clean


class StubServer(ThreadingHTTPServer):
    """OpenAI-compatible stub; push responses with ``queue_response``."""

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _StubHandler)
        self.requests: list = []
        self._responses: list = []
        self.default_response = chat_completion("42")

    def queue_response(self, obj) -> None:
        self._responses.append(obj)

    def next_response(self):
        return self._responses.pop(0) if self._responses else self.default_response

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}/v1"


def chat_completion(content, reasoning_content=None, reasoning=None, usage=...):
    """Builds a minimal chat-completions response body."""
    message = {"content": content}
    if reasoning_content is not None:
        message["reasoning_content"] = reasoning_content
    if reasoning is not None:
        message["reasoning"] = reasoning
    body = {"choices": [{"message": message}]}
    if usage is ...:
        usage = {"total_tokens": 10}
    if usage is not None:
        body["usage"] = usage
    return body


@pytest.fixture
def stub_server():
    server = StubServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture(autouse=True)
def _clear_provider_context_length_caches():
    """Autouse: clear the openrouter/primeintellect `get_model_context_length`
    `lru_cache`s before AND after every test.

    Several existing tests work around cross-test cache bleed by picking a
    globally-unique model-name string per test (see the "Unique model name
    per test avoids ... lru_cache" comments sprinkled through
    test_openai_compat.py / test_lean_runner.py) -- a fragile convention
    that silently breaks the moment two tests happen to reuse the same
    model id against two different stub servers. Clearing both caches
    around every test makes that isolation an actual guarantee instead of a
    naming convention every test author has to remember. Guarded by
    ImportError so this fixture degrades gracefully (skips silently) if a
    provider module is ever renamed/removed rather than failing collection
    for the whole suite.
    """
    def _clear() -> None:
        try:
            from smolbench.evals import openrouter
            openrouter.get_model_context_length.cache_clear()
        except ImportError:
            pass
        try:
            from smolbench.evals import primeintellect
            primeintellect.get_model_context_length.cache_clear()
        except ImportError:
            pass

    _clear()   # drop any stale entries left by a previous test
    yield
    _clear()   # leave a clean cache for whatever runs next
