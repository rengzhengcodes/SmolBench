"""Test offline round trips through the shared client via each provider module."""

import importlib
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests

from smolbench.evals import Numeric, ToF
from smolbench.evals.openai_compat import ChatClient, metadata_get
from conftest import chat_completion


@pytest.fixture
def ec2_env(stub_server, monkeypatch):
    """Points the ec2 provider at the stub (bypasses the state file)."""
    monkeypatch.setenv("EC2_INFERENCE_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("EC2_VLLM_API_KEY", "stub-key")
    return stub_server


@pytest.mark.parametrize("body,expected", [
    (chat_completion("7", reasoning_content="thought"), ("7", "thought")),
    (chat_completion("<think>step by step</think>\n7"), ("7", "step by step")),
    (chat_completion("True", reasoning="hmm"), ("True", "hmm")),
])
def test_query_splits_reasoning_channels(ec2_env, body, expected):
    """reasoning_content, an inline <think> block, and the legacy `reasoning` key all split."""
    from smolbench.evals.providers import ec2
    ec2_env.queue_response(body)
    assert ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100) == expected


def _body(message, finish_reason, usage):
    """A chat-completions body with model and finish_reason pinned (the stream echoes both)."""
    return {"choices": [{"message": message, "finish_reason": finish_reason}],
            "usage": usage, "model": "served"}


@pytest.mark.parametrize("body,expected", [
    (_body({"content": "7"}, "length",
           {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33}), ("7", None)),
    (_body({"content": "<think>step by step</think>\n7"}, "stop",
           {"total_tokens": 10}), ("7", "step by step")),
    (_body({"content": None, "reasoning": "long thought"}, "length",
           {"total_tokens": 10}), ("", "long thought")),
])
def test_stream_matches_non_streamed(ec2_env, monkeypatch, body, expected):
    """Transport changes, data does not: the same body parses identically both ways."""
    from smolbench.evals.providers import ec2
    ec2_env.queue_response(body)
    plain = ec2.complete("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert "stream" not in ec2_env.requests[-1]["body"]
    assert (plain.content, plain.reasoning) == expected
    assert plain.total_tokens == body["usage"]["total_tokens"]
    assert plain.finish_reason == body["choices"][0]["finish_reason"]
    monkeypatch.setenv("EC2_STREAM_COMPLETIONS", "1")
    ec2_env.queue_response(body)
    streamed = ec2.complete("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert streamed == plain
    sent = ec2_env.requests[-1]["body"]
    assert sent["stream"] is True
    assert sent["stream_options"] == {"include_usage": True}


def test_collect_stream_survives_usage_only_chunk():
    """The include_usage final chunk has an EMPTY choices list."""
    from smolbench.evals.openai_compat import collect_stream
    frames = [
        'data: {"model": "m", "choices": [{"delta": {"content": "4"}}]}',
        'data: {"choices": [{"delta": {"content": "2"}, "finish_reason": "stop"}]}',
        'data: {"choices": [], "usage": {"total_tokens": 9}}',
        "data: [DONE]",
        'data: {"choices": [{"delta": {"content": "IGNORED"}}]}',
    ]

    class _Resp:
        def iter_lines(self, decode_unicode=False):
            return iter(frames)

    body = collect_stream(_Resp())
    assert body["choices"][0]["message"]["content"] == "42"
    assert body["choices"][0]["finish_reason"] == "stop"
    assert body["usage"] == {"total_tokens": 9}
    assert body["model"] == "m"
    assert "reasoning_content" not in body["choices"][0]["message"]


@pytest.mark.parametrize("message,reasoning", [
    ({"content": None, "reasoning_content": "cap hit"}, "cap hit"),
    ({"content": None, "reasoning": "legacy key"}, "legacy key"),
    ({"content": None}, None),
])
def test_null_content_keeps_content_empty_and_retains_reasoning(ec2_env, message, reasoning):
    """A reasoning-only cap-hit keeps its reasoning but stays content="" for every scorer."""
    from smolbench.evals.providers import ec2
    ec2_env.queue_response({
        "choices": [{"message": message, "finish_reason": "length"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 32768, "total_tokens": 50},
    })
    result = ec2.complete("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert result.content == ""
    assert result.reasoning == reasoning
    assert result.finish_reason == "length"
    assert result.completion_tokens == 32768


def test_query_context_guard(ec2_env):
    """A prompt whose usage exceeds the model's window is an error, not a silent truncation."""
    from smolbench.evals.providers import ec2
    ec2_env.queue_response(chat_completion("7", usage={"total_tokens": 999}))
    with pytest.raises(ValueError):
        ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)


@pytest.mark.parametrize("usage,expected", [
    ({"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15,
      "prompt_tokens_details": {"cached_tokens": 5}}, (12, 3, 5, 15, "served", "stop")),
    (None, (0, 0, 0, None, "qwen2.5-1.5b", None)),
])
def test_complete_chat_result_fields(ec2_env, usage, expected):
    """Usage (incl. cached prompt tokens), server model id, and finish_reason, or their defaults."""
    from smolbench.evals.providers import ec2
    body = {"choices": [{"message": {"content": "7"}}]}
    if usage is not None:
        body["usage"] = usage
        body["choices"][0]["finish_reason"] = "stop"
        body["model"] = "served"
    ec2_env.queue_response(body)
    result = ec2.complete("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert result.content == "7"
    assert result.reasoning is None
    assert (result.prompt_tokens, result.completion_tokens, result.cached_prompt_tokens,
            result.total_tokens, result.model, result.finish_reason) == expected


@pytest.mark.parametrize("model,context_length,system", [
    ("ministral-3-14b", 200000, "extra context"),
    ("qwen2.5-1.5b", 100, "extra context"),
    ("ministral-3-14b", 200000, None),
])
def test_system_message_ordering(ec2_env, model, context_length, system):
    """[provider system, per-call system, user], and query() stays a 2-tuple wrapper."""
    from smolbench.evals.providers import ec2
    from smolbench.evals.providers.ec2 import MINISTRAL_THINK_SYSTEM
    expected = []
    if model == "ministral-3-14b":
        expected.append({"role": "system", "content": MINISTRAL_THINK_SYSTEM})
    if system is not None:
        expected.append({"role": "system", "content": system})
    expected.append({"role": "user", "content": "user prompt"})
    kwargs = {"seed": 1, "context_length": context_length, "system": system}
    ec2.complete("user prompt", model, **kwargs)
    body = ec2_env.requests[-1]["body"]
    assert body["messages"] == expected
    assert body["seed"] == 1  # repo rule: the decoding seed always ships
    ec2_env.queue_response(chat_completion("7"))
    assert ec2.query("user prompt", model, **kwargs) == ("7", None)
    assert ec2_env.requests[-1]["body"]["messages"] == expected


def test_evaluate_grades_and_orders(ec2_env):
    """Correct, wrong, and unparseable -> 1, 0, None, restored to quiz order."""
    from smolbench.evals.providers import ec2
    quiz = tuple(Numeric(prompt=f"q{i}", answer=7) for i in range(3))
    ec2_env.default_response = chat_completion("7")
    for text in ("7", "8", "no digits here"):
        ec2_env.queue_response(chat_completion(text))
    marks = ec2.evaluate(quiz, "qwen2.5-1.5b", seed=1, max_parallel=1, show_progress=False)
    assert [m.score for m in marks.marks] == [1, 0, None]
    assert (marks.correct, marks.incorrect, marks.invalid) == (1, 1, 1)


@pytest.mark.parametrize("name,env,model", [
    ("openrouter", {"OPENROUTER_API_KEY": "stub-key"}, "m-openrouter-shape"),
    ("primeintellect", {"PRIME_INTELLECT_API_KEY": "stub-key",
                        "PRIME_INTELLECT_TEAM_ID": "team-42"}, "m-primeintellect-shape"),
    ("aws", {"AWS_BEARER_TOKEN_BEDROCK": "stub-key"}, "qwen.qwen3-32b"),
])
def test_provider_request_shape(stub_server, monkeypatch, name, env, model):
    """Every provider posts to /v1/chat/completions with a verbatim model id, the seed, and bearer auth."""
    prefix = {"openrouter": "OPENROUTER", "primeintellect": "PRIME_INTELLECT",
              "aws": "AWS_INFERENCE"}[name]
    monkeypatch.setenv(f"{prefix}_BASE_URL", stub_server.base_url)
    monkeypatch.delenv("AWS_INFERENCE_API_KEY", raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    module = importlib.import_module(f"smolbench.evals.providers.{name}")
    if name == "primeintellect":
        assert module.get_model_context_length(model) == 100000
        assert stub_server.requests[-1]["path"] == f"/v1/models/{model}"
    stub_server.queue_response(chat_completion("True"))
    content, _ = module.query("p", model, seed=1, context_length=100)
    assert content == "True"
    request = stub_server.requests[-1]
    assert request["path"] == "/v1/chat/completions"
    assert request["body"]["model"] == model
    assert request["body"]["seed"] == 1
    assert request["headers"]["Authorization"] == "Bearer stub-key"
    if name == "primeintellect":
        assert request["headers"]["X-Prime-Team-ID"] == "team-42"
        monkeypatch.delenv("PRIME_INTELLECT_TEAM_ID")
        stub_server.queue_response(chat_completion("True"))
        module.query("p", model, seed=1, context_length=100)
        assert "X-Prime-Team-ID" not in stub_server.requests[-1]["headers"]


def test_aws_api_key_precedence(monkeypatch):
    """AWS_INFERENCE_API_KEY (call-time, minted) outranks the Bedrock key with no reload."""
    from smolbench.evals.providers import aws
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "bedrock-key")
    monkeypatch.setenv("AWS_INFERENCE_API_KEY", "minted")
    assert aws._api_key() == "minted"


def test_provider_dispatch_complete_and_evaluate(stub_server, monkeypatch):
    """provider.complete/evaluate dispatch to the env-selected provider and forward tuning kwargs."""
    from smolbench.evals import provider
    monkeypatch.setenv("OPENROUTER_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("INFERENCE_PROVIDER", "openrouter")
    stub_server.queue_response(chat_completion("True"))
    result = provider.complete("p", "m-complete-dispatch-test", seed=1, context_length=100)
    assert result.content == "True"
    assert result.total_tokens == 10
    stub_server.default_response = chat_completion("True")
    marks = provider.evaluate(
        (ToF(prompt="q", answer=True),), "m-evaluate-dispatch-test", seed=1,
        max_parallel=2, request_timeout=30, show_progress=False,
    )
    assert marks.correct == 1


class _FlakyHandler(BaseHTTPRequestHandler):
    """Replays a queue of ``(status_code, body)`` pairs, one per request."""

    def _reply(self, obj, code):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
        self.do_GET()

    def do_GET(self):
        code, body = self.server.next_response()
        self._reply(body, code)

    def log_message(self, *args):
        pass


class _FlakyServer(ThreadingHTTPServer):
    """Queue of scripted (status_code, body) responses; the shared stub only replies 200."""

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _FlakyHandler)
        self._responses: list = []

    def queue(self, code: int, body) -> None:
        self._responses.append((code, body))

    def next_response(self):
        return self._responses.pop(0)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}/v1"


@pytest.fixture
def flaky_server():
    server = _FlakyServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join(timeout=5)


def _client(url, **kwargs) -> ChatClient:
    """A ChatClient pointed at a scripted server, with no retry sleep."""
    return ChatClient(
        name="flaky-test", env_prefix="FLAKY_TEST", context_length=lambda model: 100,
        connection=lambda model: (url, "stub-key"), retry_backoff_s=0, **kwargs,
    )


def _chat_url(server) -> str:
    return f"{server.base_url}/chat/completions"


@pytest.mark.parametrize("method,script,max_retries,raises", [
    ("complete", [(500, {"error": "boom 1"}), (500, {"error": "boom 2"})], 2, True),
    ("complete", [(500, {"error": "boom"}), (200, chat_completion("7"))], 2, False),
    ("query", [(500, {"error": "boom"})], 1, True),
])
def test_complete_max_retries(flaky_server, method, script, max_retries, raises):
    """The Nth failure raises instead of retrying again; query() forwards max_retries."""
    for code, body in script:
        flaky_server.queue(code, body)
    call = getattr(_client(_chat_url(flaky_server)), method)
    if raises:
        with pytest.raises(requests.exceptions.HTTPError):
            call("p", "m", seed=1, context_length=100, max_retries=max_retries)
    else:
        result = call("p", "m", seed=1, context_length=100, max_retries=max_retries)
        assert result.content == "7"


def test_complete_error_body_survives_in_httperror(flaky_server):
    """The API's error BODY and the response object both survive into the raised HTTPError."""
    marker = "context_length_exceeded"
    flaky_server.queue(400, {"error": {"message": marker, "code": marker}})
    client = _client(_chat_url(flaky_server))
    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        client.complete("p", "m", seed=1)
    err = excinfo.value
    assert marker in str(err)
    assert "400" in str(err)
    assert err.response is not None
    assert err.response.status_code == 400


def test_on_unreachable_scope(flaky_server):
    """The hook fires at max_retries exhaustion on CONNECTION failures only, never on HTTP 5xx."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    closed_port = sock.getsockname()[1]
    sock.close()

    def _diagnose(exc):
        raise RuntimeError("DIAGNOSED")

    closed = _client(f"http://127.0.0.1:{closed_port}/v1/chat/completions",
                     max_connection_failures=10, on_unreachable=_diagnose)
    with pytest.raises(RuntimeError, match="DIAGNOSED"):
        closed.complete("p", "m", seed=1, max_retries=2)
    diagnosed: list = []
    flaky_server.queue(500, {"error": "boom1"})
    flaky_server.queue(500, {"error": "boom2"})
    http500 = _client(_chat_url(flaky_server), max_connection_failures=10,
                      on_unreachable=diagnosed.append)
    with pytest.raises(requests.exceptions.HTTPError):
        http500.complete("p", "m", seed=1, max_retries=2)
    assert diagnosed == []


def test_metadata_get_round_trip_sends_bearer_auth(stub_server):
    """The shared metadata GET carries bearer auth to the requested path."""
    body = metadata_get(f"{stub_server.base_url}/models", "sekret-key", check_status=False)
    assert body == {"data": [{"id": "stub-model"}]}
    request = stub_server.requests[-1]
    assert request["path"] == "/v1/models"
    assert request["headers"]["Authorization"] == "Bearer sekret-key"


@pytest.mark.parametrize("check_status", [True, False])
def test_metadata_get_check_status(flaky_server, check_status):
    """check_status=True raises (list_models); False passes the error body through (context length)."""
    error = {"error": {"message": "denied"}}
    flaky_server.queue(500, error)
    url = f"{flaky_server.base_url}/models"
    if check_status:
        with pytest.raises(requests.exceptions.HTTPError):
            metadata_get(url, "k", check_status=True)
    else:
        assert metadata_get(url, "k", check_status=False) == error
