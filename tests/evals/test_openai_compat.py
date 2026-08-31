"""Test offline round trips through the shared client via each provider module."""

import importlib
import json
import socket
import threading
import time

import pytest
import requests

from smolbench.evals import Numeric, ToF
from smolbench.evals import openai_compat
from smolbench.evals.openai_compat import ChatClient, collect_stream, metadata_get
from smolbench.evals.providers import ec2
from conftest import StubServer, _StubHandler, chat_completion

CAP = {"prompt_tokens": 5, "completion_tokens": 32768, "total_tokens": 50}
TAIL = (5, 32768, 0, 50, "qwen2.5-1.5b", "length")  # prompt/completion/cached/total, model, finish
CALL = {"seed": 1, "context_length": 100}


@pytest.fixture
def ec2_env(stub_server, monkeypatch):
    """Point the ec2 provider's env at the loopback stub server."""
    monkeypatch.setenv("EC2_INFERENCE_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("EC2_VLLM_API_KEY", "stub-key")
    return stub_server


def _body(content, finish_reason=None, model=None, **kwargs):
    """A chat_completion body with explicit finish_reason and model fields."""
    body = chat_completion(content, **kwargs)
    body["choices"][0]["finish_reason"] = finish_reason
    body["model"] = model
    return body


@pytest.mark.parametrize("body,expected", [
    (_body("7", "stop", "served", usage={"prompt_tokens": 12, "completion_tokens": 3,
     "total_tokens": 15, "prompt_tokens_details": {"cached_tokens": 5}}),
     ("7", None, 12, 3, 5, 15, "served", "stop")),
    (_body("7", usage=None), ("7", None, 0, 0, 0, None, "qwen2.5-1.5b", None)),
    (_body("7", usage=None, reasoning_content="thought"),
     ("7", "thought", 0, 0, 0, None, "qwen2.5-1.5b", None)),
    (_body("True", usage=None, reasoning="hmm"), ("True", "hmm", 0, 0, 0, None, "qwen2.5-1.5b", None)),
    (_body("<think>step by step</think>\n7", "length", usage=CAP), ("7", "step by step") + TAIL),
    (_body(None, "length", reasoning_content="cap hit", usage=CAP), ("", "cap hit") + TAIL),
    (_body(None, "length", reasoning="legacy key", usage=CAP), ("", "legacy key") + TAIL),
    # Usage above the model's window is a loud warning, not an abort: the
    # generation is already billed, so a pooled evaluate() must keep it.
    (_body("7", usage={"total_tokens": 999}),
     ("7", None, 0, 0, 0, 999, "qwen2.5-1.5b", None)),
])
def test_complete_chat_result_fields(ec2_env, monkeypatch, body, expected):
    """Channels split, usage/model/finish_reason, null content, guard -- streamed and not alike."""
    ec2_env.queue_response(body)
    plain = ec2.complete("p", "qwen2.5-1.5b", **CALL)
    assert "stream" not in ec2_env.requests[-1]["body"]
    assert (plain.content, plain.reasoning, plain.prompt_tokens, plain.completion_tokens,
            plain.cached_prompt_tokens, plain.total_tokens, plain.model,
            plain.finish_reason) == expected
    monkeypatch.setenv("EC2_STREAM_COMPLETIONS", "1")  # transport changes, data does not
    ec2_env.queue_response(body)
    assert ec2.complete("p", "qwen2.5-1.5b", **CALL) == plain
    sent = ec2_env.requests[-1]["body"]
    assert sent["stream"] is True and sent["stream_options"] == {"include_usage": True}


def test_collect_stream_survives_usage_only_chunk_and_stops_at_done():
    """The include_usage final chunk has an EMPTY choices list; frames after [DONE] are dead."""
    frames = ['data: {"model": "m", "choices": [{"delta": {"content": "42"}, "finish_reason": "stop"}]}',
              'data: {"choices": [], "usage": {"total_tokens": 9}}', "data: [DONE]",
              'data: {"choices": [{"delta": {"content": "IGNORED"}}]}']
    body = collect_stream(type("_R", (), {"iter_lines": lambda s, decode_unicode=False:
                                          iter(frames)})())
    assert body["choices"][0] == {"message": {"content": "42"}, "finish_reason": "stop"}
    assert (body["usage"], body["model"]) == ({"total_tokens": 9}, "m")


def _stream_of(frames):
    """A minimal requests-response stand-in yielding `frames` from iter_lines."""
    return type("_R", (), {"iter_lines": lambda s, decode_unicode=False: iter(frames)})()


@pytest.mark.parametrize("frames", [
    # Malformed chunk: must surface as the retryable stream-broke class, not
    # a stdlib JSONDecodeError that escapes complete()'s retry loop.
    ['data: {"choices": [{"delta": {"content": "4"}}]}', "data: {truncated"],
    # Clean close before [DONE] with no finish_reason: an incomplete body
    # must be retried, never graded as a finished generation.
    ['data: {"choices": [{"delta": {"content": "4"}}]}'],
])
def test_collect_stream_rejects_malformed_or_truncated_streams(frames):
    """A broken stream raises the retryable transport error, never a partial body."""
    with pytest.raises(requests.exceptions.ChunkedEncodingError):
        collect_stream(_stream_of(frames))


def test_collect_stream_accepts_finish_reason_without_done():
    """Some servers end the stream after the final chunk without a [DONE] sentinel."""
    frames = ['data: {"choices": [{"delta": {"content": "42"}, "finish_reason": "stop"}]}']
    assert collect_stream(_stream_of(frames))["choices"][0]["finish_reason"] == "stop"


@pytest.mark.parametrize("model,context_length,system", [
    ("ministral-3-14b", 200000, "extra context"),
    ("qwen2.5-1.5b", 100, "extra context"),
    ("ministral-3-14b", 200000, None),
])
def test_system_message_ordering(ec2_env, model, context_length, system):
    """[provider system, per-call system, user], and query() stays a 2-tuple wrapper."""
    expected = [{"role": "system", "content": ec2.MINISTRAL_THINK_SYSTEM}] * (model != "qwen2.5-1.5b")
    expected += [{"role": "system", "content": system}] * (system is not None)
    expected += [{"role": "user", "content": "user prompt"}]
    kwargs = {"seed": 1, "context_length": context_length, "system": system}
    ec2.complete("user prompt", model, **kwargs)
    body = ec2_env.requests[-1]["body"]
    assert body["messages"] == expected
    assert body["seed"] == 1  # repo rule: the decoding seed always ships
    ec2_env.queue_response(chat_completion("7"))
    assert ec2.query("user prompt", model, **kwargs) == ("7", None)
    assert ec2_env.requests[-1]["body"]["messages"] == expected
    # extra_args merges FIRST, so no caller sampling argument can drop the seed.
    ec2.complete("user prompt", model, extra_args={"seed": 999, "temperature": 0}, **kwargs)
    body = ec2_env.requests[-1]["body"]
    assert (body["seed"], body["temperature"]) == (1, 0)


@pytest.mark.parametrize("name,prefix,env,model", [
    ("openrouter", "OPENROUTER", {"OPENROUTER_API_KEY": "stub-key"}, "m-openrouter-shape"),
    ("primeintellect", "PRIME_INTELLECT", {"PRIME_INTELLECT_API_KEY": "stub-key",
     "PRIME_INTELLECT_TEAM_ID": "team-42"}, "m-primeintellect-shape"),
    ("aws", "AWS_INFERENCE", {"AWS_BEARER_TOKEN_BEDROCK": "stub-key"}, "qwen.qwen3-32b"),
])
def test_provider_request_shape(stub_server, monkeypatch, name, prefix, env, model):
    """Every provider posts to /v1/chat/completions with a verbatim model id, seed, bearer auth."""
    monkeypatch.setenv(f"{prefix}_BASE_URL", stub_server.base_url)
    monkeypatch.delenv("AWS_INFERENCE_API_KEY", raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    module = importlib.import_module(f"smolbench.evals.providers.{name}")
    if name == "primeintellect":
        assert module.get_model_context_length(model) == 100000
        assert stub_server.requests[-1]["path"] == f"/v1/models/{model}"
    stub_server.queue_response(chat_completion("True"))
    assert module.query("p", model, **CALL)[0] == "True"
    request = stub_server.requests[-1]
    assert (request["path"], request["body"]["model"], request["body"]["seed"]) == (
        "/v1/chat/completions", model, 1)
    assert request["headers"]["Authorization"] == "Bearer stub-key"
    if name == "primeintellect":  # the routing header is present when set, absent when unset
        assert request["headers"]["X-Prime-Team-ID"] == "team-42"
        monkeypatch.delenv("PRIME_INTELLECT_TEAM_ID")
        stub_server.queue_response(chat_completion("True"))
        module.query("p", model, **CALL)
        assert "X-Prime-Team-ID" not in stub_server.requests[-1]["headers"]
    if name == "aws":  # the call-time minted key outranks the Bedrock key, with no reload
        monkeypatch.setenv("AWS_INFERENCE_API_KEY", "minted")
        assert module._api_key() == "minted"


def test_provider_dispatch_grades_and_orders(ec2_env, monkeypatch):
    """provider.* dispatch to the env-selected provider; correct/wrong/unparseable -> 1/0/None."""
    from smolbench.evals import provider
    monkeypatch.setenv("INFERENCE_PROVIDER", "ec2")
    ec2_env.default_response = chat_completion("7")
    result = provider.complete("p", "qwen2.5-1.5b", **CALL)
    assert (result.content, result.total_tokens) == ("7", 10)
    quiz = tuple(Numeric(prompt=f"q{i}", answer=7) for i in range(3)) + (ToF(prompt="q", answer=True),)
    for text in ("7", "8", "no digits here", "True"):
        ec2_env.queue_response(chat_completion(text))
    marks = provider.evaluate(quiz, "qwen2.5-1.5b", seed=1, max_parallel=1, request_timeout=30,
                              show_progress=False)
    assert [m.score for m in marks.marks] == [1, 0, None, 1]
    assert (marks.correct, marks.incorrect, marks.invalid) == (2, 1, 1)


class _FlakyHandler(_StubHandler):
    """Replays a queue of ``(status_code, body)`` pairs, one per request."""

    def do_GET(self):
        code, body = self.server.next_response()
        _StubHandler._reply(self, body, code)

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
        self.do_GET()


@pytest.fixture
def flaky_server():
    """A stub server scripted with (status_code, body) pairs; the shared stub only replies 200."""
    server = StubServer()
    server.RequestHandlerClass = _FlakyHandler
    server.queue = lambda code, body: server._responses.append((code, body))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join(timeout=5)


def _client(target, **kwargs) -> ChatClient:
    url = target if isinstance(target, str) else f"{target.base_url}/chat/completions"
    return ChatClient(name="flaky-test", env_prefix="FLAKY_TEST", retry_backoff_s=0,
                      context_length=lambda m: 100, connection=lambda m: (url, "stub-key"), **kwargs)


@pytest.mark.parametrize("method,script,max_retries,status", [
    ("complete", [(500, "boom 1"), (500, "boom 2")], 2, 500),
    ("complete", [(500, "boom"), (200, chat_completion("7"))], 2, None),
    ("query", [(500, "boom")], 1, 500),
    ("complete", [(400, "context_length_exceeded")], 2, 400),  # non-retryable
])
def test_retry_cap_and_error_surface(flaky_server, method, script, max_retries, status):
    """The Nth failure raises instead of retrying; query() forwards the cap; error body survives."""
    for code, marker in script:
        flaky_server.queue(code, marker if code == 200 else {"error": {"message": marker}})
    call = getattr(_client(flaky_server), method)
    if status is None:
        assert call("p", "m", max_retries=max_retries, **CALL).content == "7"
        return
    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        call("p", "m", max_retries=max_retries, **CALL)
    assert script[-1][1] in str(excinfo.value)  # the API's error BODY survives
    assert excinfo.value.response is not None and excinfo.value.response.status_code == status


def test_on_unreachable_scope(flaky_server):
    """The hook fires at max_retries exhaustion on CONNECTION failures only, never on HTTP 5xx."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        closed_url = f"http://127.0.0.1:{sock.getsockname()[1]}/v1/chat/completions"
    diagnosed: list = []
    closed = _client(closed_url, max_connection_failures=10, on_unreachable=diagnosed.append)
    with pytest.raises(requests.exceptions.ConnectionError):
        closed.complete("p", "m", seed=1, max_retries=2)
    assert len(diagnosed) == 1
    for _ in range(2):
        flaky_server.queue(500, {"error": "boom"})
    http500 = _client(flaky_server, max_connection_failures=10, on_unreachable=diagnosed.append)
    with pytest.raises(requests.exceptions.HTTPError):
        http500.complete("p", "m", seed=1, max_retries=2)
    assert len(diagnosed) == 1  # unchanged: an HTTP 5xx never reaches the hook


def test_read_timeout_is_not_an_unreachable_endpoint(monkeypatch):
    """A server that ANSWERED and then generated slowly never trips the connection cap."""
    def _timeout(**kwargs):
        raise requests.exceptions.ReadTimeout("generation outran the read timeout")

    monkeypatch.setattr(openai_compat.requests, "post", _timeout)
    diagnosed: list = []
    client = _client("http://127.0.0.1:1/v1/chat/completions",
                     max_connection_failures=2, on_unreachable=diagnosed.append)
    with pytest.raises(requests.exceptions.ReadTimeout):
        client.complete("p", "m", seed=1, max_retries=3)
    assert diagnosed == []  # a RuntimeError here would mean "the box is gone"


#: Quiz size for the ordering test; also its thread fan-out, so the reversal is total.
ORDER_N = 6


class _EchoHandler(_StubHandler):
    """Echoes each prompt back as its own content, slowest for the FIRST prompt."""

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0") or "0")))
        prompt = payload["messages"][-1]["content"]
        time.sleep(0.05 * (ORDER_N - int(prompt)))  # invert the completion order
        self.server.requests.append({"body": payload})  # recorded on COMPLETION
        self._reply(chat_completion(prompt))


def test_evaluate_restores_quiz_order_under_parallel_fan_out():
    """Responses land in reverse under max_parallel>1; marks still line up with their questions."""
    server = StubServer()
    server.RequestHandlerClass = _EchoHandler
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    prompts = [str(i) for i in range(ORDER_N)]
    try:
        quiz = tuple(Numeric(prompt=p, answer=int(p)) for p in prompts)
        marks = _client(server).evaluate(quiz, "m", seed=1, max_parallel=ORDER_N,
                                         show_progress=False)
    finally:
        server.shutdown()
        thread.join(timeout=5)
    completed = [r["body"]["messages"][-1]["content"] for r in server.requests]
    assert completed == prompts[::-1], "premise: the wire order really was reversed"
    assert [m.query for m in marks.marks] == prompts
    assert [m.response for m in marks.marks] == prompts
    assert marks.correct == ORDER_N


def test_metadata_get_auth_and_check_status(stub_server, flaky_server):
    """Bearer auth on the GET; check_status=True raises (list_models), False passes the body on."""
    url = f"{stub_server.base_url}/models"
    assert metadata_get(url, "sekret-key", check_status=False) == {"data": [{"id": "stub-model"}]}
    request = stub_server.requests[-1]
    assert (request["path"], request["headers"]["Authorization"]) == ("/v1/models",
                                                                     "Bearer sekret-key")
    error, url = {"error": {"message": "denied"}}, f"{flaky_server.base_url}/models"
    flaky_server.queue(500, error)
    assert metadata_get(url, "k", check_status=False) == error  # context-length probe
    flaky_server.queue(500, error)
    with pytest.raises(requests.exceptions.HTTPError):
        metadata_get(url, "k", check_status=True)
