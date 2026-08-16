"""Shared fixtures: a local OpenAI-compatible stub server + stub tokenizers.

Everything in tests/ runs OFFLINE -- no AWS credentials, no network. The stub
server speaks just enough of the Chat Completions dialect to exercise the
shared client in smolbench/evals/openai_compat.py through every provider
module, and `StubTokenizer` stands in for the model tokenizers the induction
generators would otherwise download.
"""

import json
import math
import re
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

    def _reply_sse(self, obj):
        """Re-emits a chat-completions body as an SSE stream.

        Chunked deliberately -- one character per delta for both channels --
        so a test exercises real REASSEMBLY rather than a single-frame
        passthrough that would pass even if the client dropped everything
        but the last chunk. The frame ORDER mirrors vLLM: content/reasoning
        deltas, then a chunk carrying only ``finish_reason``, then (for
        ``stream_options: {"include_usage": true}``) a usage-only chunk whose
        ``choices`` list is EMPTY -- the shape most likely to crash a naive
        ``choices[0]`` reader -- and finally ``[DONE]``.
        """
        message = (obj.get("choices") or [{}])[0].get("message") or {}
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()

        def frame(chunk):
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())

        for key in ("reasoning_content", "reasoning"):
            for ch in message.get(key) or "":
                frame({"model": obj.get("model", "stub-model"),
                       "choices": [{"delta": {key: ch}}]})
        for ch in message.get("content") or "":
            frame({"model": obj.get("model", "stub-model"),
                   "choices": [{"delta": {"content": ch}}]})
        finish = (obj.get("choices") or [{}])[0].get("finish_reason", "stop")
        frame({"choices": [{"delta": {}, "finish_reason": finish}]})
        if obj.get("usage") is not None:
            frame({"choices": [], "usage": obj["usage"]})
        self.wfile.write(b"data: [DONE]\n\n")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        payload = json.loads(self.rfile.read(length) or b"{}")
        # Headers are recorded alongside the body so tests can assert on
        # auth/routing headers (e.g. Prime Intellect's X-Prime-Team-ID).
        self.server.requests.append(
            {"path": self.path, "body": payload, "headers": dict(self.headers)}
        )
        response = self.server.next_response()
        # The stub answers in whichever transport the CLIENT asked for, so a
        # streaming test and a non-streaming test can queue the exact same
        # response object and assert the parsed results match.
        if payload.get("stream"):
            self._reply_sse(response)
        else:
            self._reply(response)

    def do_GET(self):
        # Headers recorded for the same reason as in do_POST (e.g. asserting
        # metadata_get's Authorization bearer header).
        self.server.requests.append(
            {"path": self.path, "body": None, "headers": dict(self.headers)}
        )
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


# ---------------------------------------------------------------------------
# Stub tokenizers (smolbench.evals.tokenization.Tokenizer implementations)
# ---------------------------------------------------------------------------
# The induction generators need a tokenizer to size their token-matched noise
# arm. Driving the offline suite with a REAL one would mean either a network
# download (`HFTokenizer`) or a tiktoken BPE file that may or may not be in the
# local cache -- neither acceptable for tests whose whole contract is that they
# run offline and deterministically. These stubs are pure Python, exact, and
# stable forever, which also makes them what the golden-hash fixture is
# recorded against.

_CHUNK_RE = re.compile(r"\s+|\S+")


class StubTokenizer:
    """Deterministic tokenizer that imitates the BPE behaviour that matters.

    Two real-tokenizer properties drive the noise-padding machinery, and this
    stub reproduces both so tests exercise the same code paths a served model
    would:

    1. **Whitespace runs merge.** A long run of ONE repeated whitespace
       character collapses to a single token (``" " * 128`` really is one
       token in ``cl100k_base``), which is why a naive space pad cannot reach
       a large token target and why `choose_whitespace_unit` exists.
    2. **Mixed whitespace does not.** Alternating characters defeat the run
       merge, so ``" \\t" * n`` costs ~n tokens -- the property the pad atom
       is selected for.

    Everything else is a coarse length model (a token per 2 whitespace
    characters, per 4 other characters). Boundary effects are real here too:
    the pad fuses with adjacent whitespace in the template, so the count of a
    padded prompt is NOT the sum of its parts -- exactly the second-order
    behaviour the padding search has to absorb.
    """

    name = "stub"

    def count(self, text: str) -> int:
        """Returns the stub token count of `text`."""
        total = 0
        for chunk in _CHUNK_RE.findall(text):
            if chunk.isspace():
                if len(set(chunk)) == 1 and len(chunk) > 8:
                    total += 1  # BPE-style run merge
                else:
                    total += math.ceil(len(chunk) / 2)
            else:
                total += math.ceil(len(chunk) / 4)
        return total


class TruncatingTokenizer:
    """`StubTokenizer` with a hard cap, like a tokenizer.json truncation stanza.

    Models the live failure found in
    ``nvidia/Llama-3_1-Nemotron-Ultra-253B-v1-FP8``: its ``tokenizer.json``
    embeds ``truncation: {max_length: 512}``, so every count above the cap
    comes back AS the cap. A capped tokenizer looks perfectly linear right up
    to the cap, which is why the pad-atom probe has to reach past any
    plausible one -- a saturating counter would otherwise report a
    26,000-token prompt and its pad as equal at 512.
    """

    name = "truncating-512"

    def __init__(self, cap: int = 512):
        self.cap = cap
        self._inner = StubTokenizer()

    def count(self, text: str) -> int:
        """Returns the stub count, capped like a truncating tokenizer."""
        return min(self._inner.count(text), self.cap)


class MergeEverythingTokenizer:
    """Pathological tokenizer: ANY whitespace run is one token.

    No repeating whitespace atom can grow the count under it, so it is the
    case `choose_whitespace_unit` must refuse rather than silently return a
    pad that saturates far below its target.
    """

    name = "merge-everything"

    def count(self, text: str) -> int:
        """Returns the stub token count of `text`."""
        return sum(
            1 if chunk.isspace() else math.ceil(len(chunk) / 4)
            for chunk in _CHUNK_RE.findall(text)
        )


@pytest.fixture
def stub_tokenizer():
    """A `StubTokenizer` instance (see that class for what it models)."""
    return StubTokenizer()


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
