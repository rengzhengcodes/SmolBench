"""Provide shared fixtures: a local OpenAI-compatible stub server and stub tokenizers.

All tests in this directory run offline. They use no AWS credentials and no
network access. The stub server implements enough of the Chat Completions
API to exercise the shared client in ``smolbench/evals/openai_compat.py``
through every provider module. ``StubTokenizer`` replaces the real model
tokenizers that the induction generators would otherwise download.
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
        """Re-emit a chat-completions body as an SSE stream.

        The stream sends one character per delta, on both channels. This
        makes a test exercise real reassembly, not a single-frame passthrough
        that would still pass even if the client dropped every chunk but the
        last. The frame order matches vLLM: content and reasoning deltas
        first, then a chunk that carries only ``finish_reason``, then (when
        ``stream_options`` sets ``{"include_usage": true}``) a usage-only
        chunk whose ``choices`` list is empty -- the shape most likely to
        crash a naive ``choices[0]`` reader -- and finally ``[DONE]``.
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
        # Record the headers with the body. Tests can then check auth and
        # routing headers, for example Prime Intellect's X-Prime-Team-ID.
        self.server.requests.append(
            {"path": self.path, "body": payload, "headers": dict(self.headers)}
        )
        response = self.server.next_response()
        # The stub replies in whatever transport the client asks for. A
        # streaming test and a non-streaming test can queue the same
        # response object and check that the parsed results match.
        if payload.get("stream"):
            self._reply_sse(response)
        else:
            self._reply(response)

    def do_GET(self):
        # Record headers for the same reason as in do_POST, for example to
        # check metadata_get's Authorization bearer header.
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
# arm. A real tokenizer would need either a network download (`HFTokenizer`)
# or a tiktoken BPE file that may or may not be in the local cache. Neither
# fits the offline, deterministic contract of this suite. These stubs are
# pure Python. They give exact, stable results, so the golden-hash fixture is
# recorded against them.

_CHUNK_RE = re.compile(r"\s+|\S+")


class StubTokenizer:
    """Deterministic tokenizer that copies the BPE behavior that matters.

    Two properties of real tokenizers drive the noise-padding logic. This
    stub copies both, so tests exercise the same code paths a served model
    would use.

    1. Whitespace runs merge. A long run of one repeated whitespace
       character collapses to a single token (``" " * 128`` really is one
       token in ``cl100k_base``). This is why a plain space pad cannot reach
       a large token target, and why `choose_whitespace_unit` exists.
    2. Mixed whitespace does not merge. Alternating characters defeat the run
       merge, so ``" \\t" * n`` costs about n tokens. This is the property
       the pad atom is chosen for.

    All other text follows a coarse length model: one token per 2 whitespace
    characters, and one token per 4 other characters. Boundary effects are
    real here too. The pad fuses with adjacent whitespace in the template, so
    the token count of a padded prompt is not the sum of its parts. This is
    the same second-order behavior the padding search must handle.
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

    This models a real failure found in
    ``nvidia/Llama-3_1-Nemotron-Ultra-253B-v1-FP8``: its ``tokenizer.json``
    sets ``truncation: {max_length: 512}``, so every count above the cap
    comes back as the cap. A capped tokenizer looks linear right up to the
    cap. This is why the pad-atom probe must reach past any plausible cap --
    otherwise a saturating counter could report a 26,000-token prompt and its
    pad as equal, both at 512.
    """

    name = "truncating-512"

    def __init__(self, cap: int = 512):
        self.cap = cap
        self._inner = StubTokenizer()

    def count(self, text: str) -> int:
        """Returns the stub count, capped like a truncating tokenizer."""
        return min(self._inner.count(text), self.cap)


class MergeEverythingTokenizer:
    """Pathological tokenizer: any whitespace run is one token.

    No repeating whitespace atom can grow the count under this tokenizer.
    This is the case `choose_whitespace_unit` must refuse, instead of
    silently returning a pad that saturates far below its target.
    """

    name = "merge-everything"

    def count(self, text: str) -> int:
        """Returns the stub token count of `text`."""
        return sum(
            1 if chunk.isspace() else math.ceil(len(chunk) / 4)
            for chunk in _CHUNK_RE.findall(text)
        )


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
    """Clear the openrouter and primeintellect `get_model_context_length` caches.

    This fixture is autouse. It clears both `lru_cache` caches before and
    after every test.

    Some tests avoid cross-test cache bleed by picking a globally unique
    model-name string per test (see the "Unique model name per test avoids
    ... lru_cache" comments in test_openai_compat.py and
    test_lean_runner.py). This convention is fragile: it breaks silently the
    moment two tests reuse the same model id against two different stub
    servers. This cache-clearing around every test makes that isolation a
    real guarantee, not a naming convention every test author must remember.

    The clear step is guarded by ImportError, so this fixture degrades
    gracefully (skips silently) if a provider module is ever renamed or
    removed, instead of failing collection for the whole suite.
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
