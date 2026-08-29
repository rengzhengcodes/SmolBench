"""Test offline round trips through the shared client via each provider module.

These are the "offline stub tests" the provider modules reference. They
verify the unified query, complete, and evaluate behavior: reasoning
channels, <think> splitting, the tolerant usage guard, per-model system
prompts, per-call system prompts, token usage (ChatResult), the
max_retries cap, and grading. All of it runs against a local stub
server, with no credentials and no network.
"""

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


def test_ec2_query_reasoning_content(ec2_env):
    from smolbench.evals.providers import ec2

    ec2_env.queue_response(chat_completion("7", reasoning_content="thought"))
    content, reasoning = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert (content, reasoning) == ("7", "thought")


def test_ec2_query_think_split(ec2_env):
    from smolbench.evals.providers import ec2

    ec2_env.queue_response(chat_completion("<think>step by step</think>\n7"))
    content, reasoning = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert content == "7"
    assert reasoning == "step by step"


def test_ec2_query_missing_usage_tolerated(ec2_env):
    from smolbench.evals.providers import ec2

    ec2_env.queue_response(chat_completion("7", usage=None))
    content, _ = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert content == "7"


# ---------------------------------------------------------------------------
# Opt-in streaming transport (EC2_STREAM_COMPLETIONS)
# ---------------------------------------------------------------------------
# A non-streaming completion is silent on the wire for the whole
# generation. On 2026-08-16 that silence was measured to be fatal for
# cap-length ministral-3-14b responses. The server finished them, but
# the client's sockets stayed ESTABLISHED with empty receive queues for
# 57 minutes, and every one hit its read timeout. An A/B on the same
# box in the same window, identical sampling parameters, differing only
# in `stream`, delivered 19,856,415 bytes streamed against nothing at
# all non-streamed. These tests pin the resulting transport: same
# parsed result, off unless asked for.


def test_ec2_stream_is_off_by_default(ec2_env):
    """No opt-in, no `stream` key.

    Every row already collected in this study came over the non-streamed
    path, so the default must not move.
    """
    from smolbench.evals.providers import ec2

    ec2_env.queue_response(chat_completion("7"))
    ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert "stream" not in ec2_env.requests[-1]["body"]


def test_ec2_stream_round_trip_matches_non_streamed(ec2_env, monkeypatch):
    """The SAME response object, delivered both ways, parses identically.

    This is the property that makes a streamed lane comparable with a
    non-streamed one: transport changes, data does not.
    """
    from smolbench.evals.providers import ec2

    response = chat_completion("7", reasoning_content="thought")
    ec2_env.queue_response(response)
    plain = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)

    monkeypatch.setenv("EC2_STREAM_COMPLETIONS", "1")
    ec2_env.queue_response(response)
    streamed = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)

    assert streamed == plain == ("7", "thought")
    body = ec2_env.requests[-1]["body"]
    assert body["stream"] is True
    # Without include_usage the final chunk carries no counters and a streamed
    # row would silently lose its token counts.
    assert body["stream_options"] == {"include_usage": True}


def test_ec2_stream_preserves_usage_and_finish_reason(ec2_env, monkeypatch):
    from smolbench.evals.providers import ec2

    monkeypatch.setenv("EC2_STREAM_COMPLETIONS", "1")
    ec2_env.queue_response({
        "choices": [{"message": {"content": "7"}, "finish_reason": "length"}],
        "usage": {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33},
    })
    result = ec2.complete("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert (result.content, result.finish_reason) == ("7", "length")
    assert (result.prompt_tokens, result.completion_tokens) == (11, 22)
    assert result.total_tokens == 33


def test_ec2_stream_think_split_still_applies(ec2_env, monkeypatch):
    """Reassembly happens BEFORE parsing.

    So a plain-text think block that arrives split across deltas is
    still split into channels.
    """
    from smolbench.evals.providers import ec2

    monkeypatch.setenv("EC2_STREAM_COMPLETIONS", "1")
    ec2_env.queue_response(chat_completion("<think>step by step</think>\n7"))
    content, reasoning = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert (content, reasoning) == ("7", "step by step")


def test_ec2_stream_matches_non_streamed_when_content_is_null(ec2_env, monkeypatch):
    """A reasoning-only generation must parse the same over both transports.

    vLLM sends ``"content": null`` when the whole budget went to the
    reasoning channel. This was measured live on ministral-3-14b:
    content=None with 1,553 characters of reasoning. If the streamed
    path reassembled that as ``""``, it would skip the branch and
    record reasoning where the non-streamed path records something
    else. That would be a difference in the DATA from a change that is
    only supposed to touch the transport. This is the cap-length case
    the lane is missing, so it is the case most likely to occur.

    2026-08-23 (defect D3): the pinned value moved from ``("", None)``
    to ``("", "long thought")``. The early-return used to hardcode
    ``reasoning=None``, DISCARDING a reasoning-only cap-hit. It now
    returns the reasoning channel faithfully. The INVARIANT this test
    exists for, that both transports parse the same body identically,
    is unchanged. The assertion is now strictly stronger: it pins both
    parity AND retention.
    """
    from smolbench.evals.providers import ec2

    reasoning_only = {
        "choices": [{"message": {"content": None, "reasoning": "long thought"},
                     "finish_reason": "length"}],
        "usage": {"total_tokens": 10},
    }
    ec2_env.queue_response(reasoning_only)
    plain = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)

    monkeypatch.setenv("EC2_STREAM_COMPLETIONS", "1")
    ec2_env.queue_response(reasoning_only)
    streamed = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)

    assert streamed == plain == ("", "long thought")


# ---------------------------------------------------------------------------
# D3 (2026-08-23): the null-content early return must not discard reasoning
# ---------------------------------------------------------------------------
# A reasoning-only cap-hit (content=None, finish_reason="length") used
# to surface as a fully EMPTY row. The early-return hardcoded
# reasoning=None, while the normal branch read the reasoning key. In
# the determinism probes, that manufactured rows of length <= 1: an
# "empty" row that was really a 106,545-character generation. One such
# row was mis-scored as "excluded (empty)" in a published positive
# control. What must NOT move is the study-side semantics: content
# stays "", so a reasoning-only cap-hit is still an empty or failed
# candidate, and can never be graded as a proof.


def test_ec2_null_content_retains_reasoning_and_keeps_content_empty(ec2_env):
    """content=None + reasoning_content -> reasoning kept, content STILL "".

    The ``content == ""`` assertion is the load-bearing one. Every
    scorer in the repo reads content only
    (``extract_tactic_block(rsp.content)``, ``parse_for(q, raw)``). So
    it is what proves retaining the reasoning channel cannot promote a
    cap-hit into a graded answer or a Lean proof.
    """
    from smolbench.evals.providers import ec2

    ec2_env.queue_response({
        "choices": [{"message": {"content": None,
                                 "reasoning_content": "a long reasoning-only cap hit"},
                     "finish_reason": "length"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 32768, "total_tokens": 50},
    })
    result = ec2.complete("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert result.content == ""                      # study-side semantics UNCHANGED
    assert result.reasoning == "a long reasoning-only cap hit"
    assert result.finish_reason == "length"
    assert result.completion_tokens == 32768


def test_ec2_null_content_retains_legacy_reasoning_key(ec2_env):
    """The early return must use the NORMAL branch's key handling.

    Some servers spell the channel ``reasoning`` rather than
    ``reasoning_content``. ``collect_stream`` already folds both
    spellings into ``reasoning_content``. So reading only
    ``reasoning_content`` here would make the non-streamed path disagree
    with the streamed one on exactly this body. This was measured, not
    guessed. This test is the discriminator between the two readings.
    """
    from smolbench.evals.providers import ec2

    ec2_env.queue_response({
        "choices": [{"message": {"content": None, "reasoning": "legacy key"},
                     "finish_reason": "length"}],
        "usage": {"total_tokens": 10},
    })
    result = ec2.complete("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert result.content == ""
    assert result.reasoning == "legacy key"


def test_ec2_null_content_and_no_reasoning_stays_none(ec2_env):
    """A genuinely empty response is still (content="", reasoning=None).

    Without this, "retain the reasoning" could be implemented as
    `or ""`, and a truly empty row would become indistinguishable from
    a cap-hit.
    """
    from smolbench.evals.providers import ec2

    ec2_env.queue_response({
        "choices": [{"message": {"content": None}, "finish_reason": "stop"}],
        "usage": {"total_tokens": 10},
    })
    result = ec2.complete("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert result.content == ""
    assert result.reasoning is None


def test_collect_stream_survives_usage_only_chunk():
    """The include_usage final chunk has an EMPTY choices list.

    This is the shape a naive choices[0] reader crashes on.
    """
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
    # Nothing after [DONE] is consumed.
    assert "IGNORED" not in body["choices"][0]["message"]["content"]
    # No reasoning deltas arrived, so the key is absent -- exactly as it is
    # absent from a non-streamed body with no reasoning channel.
    assert "reasoning_content" not in body["choices"][0]["message"]


def test_ec2_query_context_guard(ec2_env):
    from smolbench.evals.providers import ec2

    ec2_env.queue_response(chat_completion("7", usage={"total_tokens": 999}))
    with pytest.raises(ValueError):
        ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)


def test_ec2_system_prompt_injected_from_deploy_spec(ec2_env):
    from smolbench.evals.providers import ec2

    # ministral's spec carries the [THINK]-protocol default system message.
    from smolbench.evals.providers.ec2 import MINISTRAL_THINK_SYSTEM
    ec2.query("user prompt", "ministral-3-14b", seed=1, context_length=200000)
    body = ec2_env.requests[-1]["body"]
    assert body["messages"][0] == {"role": "system", "content": MINISTRAL_THINK_SYSTEM}
    assert body["messages"][1] == {"role": "user", "content": "user prompt"}
    assert body["seed"] == 1  # repo rule: the decoding seed always ships


def test_ec2_evaluate_grades_and_orders(ec2_env):
    from smolbench.evals.providers import ec2

    quiz = (
        Numeric(prompt="q1", answer=7),
        Numeric(prompt="q2", answer=7),
        Numeric(prompt="q3", answer=7),
    )
    # Correct, wrong, and unparseable -> scores 1, 0, None. Responses may
    # arrive out of order; grading must restore quiz order.
    ec2_env.default_response = chat_completion("7")
    ec2_env.queue_response(chat_completion("7"))
    ec2_env.queue_response(chat_completion("8"))
    ec2_env.queue_response(chat_completion("no digits here"))
    marks = ec2.evaluate(quiz, "qwen2.5-1.5b", seed=1, max_parallel=1, show_progress=False)
    assert [m.score for m in marks.marks] == [1, 0, None]
    assert (marks.correct, marks.incorrect, marks.invalid) == (1, 1, 1)


def test_openrouter_reasoning_fallback(stub_server, monkeypatch):
    from smolbench.evals.providers import openrouter

    monkeypatch.setenv("OPENROUTER_BASE_URL", stub_server.base_url)
    stub_server.queue_response(chat_completion("True", reasoning="hmm"))
    content, reasoning = openrouter.query("p", "m", seed=1, context_length=100)
    assert (content, reasoning) == ("True", "hmm")


def test_openrouter_evaluate_via_provider_dispatch(stub_server, monkeypatch):
    """evaluate() tuning kwargs work under EVERY provider (substitutability)."""
    monkeypatch.setenv("OPENROUTER_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("INFERENCE_PROVIDER", "openrouter")
    from smolbench.evals import provider

    stub_server.default_response = chat_completion("True")
    quiz = (ToF(prompt="q", answer=True),)
    # A unique model name per test avoids get_model_context_length's lru_cache.
    marks = provider.evaluate(
        quiz, "m-dispatch-test", seed=1,
        max_parallel=2, request_timeout=30, show_progress=False,
    )
    assert marks.correct == 1


def test_primeintellect_query_and_context_length(stub_server, monkeypatch):
    """Mirrors the openrouter/aws round trips above, for the Prime Intellect provider.

    PRIME_INTELLECT_BASE_URL points at the stub, and
    get_model_context_length resolves via the stub's
    Prime-Intellect-style GET /models/{model} shape. conftest's do_GET
    already serves {"context_length": 100000} for any path containing
    "/models/".
    """
    from smolbench.evals.providers import primeintellect

    monkeypatch.setenv("PRIME_INTELLECT_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("PRIME_INTELLECT_API_KEY", "stub-key")

    # Unique model name per test avoids get_model_context_length's
    # module-level lru_cache bleeding a stale value in from another test.
    assert primeintellect.get_model_context_length("m-primeintellect-ctxlen") == 100000
    assert stub_server.requests[-1]["path"] == "/v1/models/m-primeintellect-ctxlen"

    stub_server.queue_response(chat_completion("True"))
    content, _ = primeintellect.query("p", "m-primeintellect-ctxlen", seed=1, context_length=100)
    assert content == "True"
    body = stub_server.requests[-1]["body"]
    assert body["model"] == "m-primeintellect-ctxlen"  # identity body_model, sent verbatim
    assert body["seed"] == 1


def test_primeintellect_team_id_header(stub_server, monkeypatch):
    """The optional X-Prime-Team-ID billing header rides on every request.

    It rides along when PRIME_INTELLECT_TEAM_ID is set, and is absent
    otherwise. This resolves at call time via ChatClient.extra_headers,
    so no re-import is needed between the two requests. Authorization
    must survive alongside it: the extra-headers merge cannot clobber
    auth.
    """
    from smolbench.evals.providers import primeintellect

    monkeypatch.setenv("PRIME_INTELLECT_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("PRIME_INTELLECT_API_KEY", "stub-key")

    monkeypatch.setenv("PRIME_INTELLECT_TEAM_ID", "team-42")
    stub_server.queue_response(chat_completion("True"))
    primeintellect.query("p", "m-pi-team-header", seed=1, context_length=100)
    headers = stub_server.requests[-1]["headers"]
    assert headers["X-Prime-Team-ID"] == "team-42"
    assert headers["Authorization"] == "Bearer stub-key"

    monkeypatch.delenv("PRIME_INTELLECT_TEAM_ID")
    stub_server.queue_response(chat_completion("True"))
    primeintellect.query("p", "m-pi-team-header", seed=1, context_length=100)
    assert "X-Prime-Team-ID" not in stub_server.requests[-1]["headers"]


def test_primeintellect_evaluate_via_provider_dispatch(stub_server, monkeypatch):
    """evaluate() tuning kwargs work under primeintellect too.

    This is the same substitutability check
    test_openrouter_evaluate_via_provider_dispatch performs for
    openrouter.
    """
    from smolbench.evals import provider

    monkeypatch.setenv("PRIME_INTELLECT_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("PRIME_INTELLECT_API_KEY", "stub-key")
    monkeypatch.setenv("INFERENCE_PROVIDER", "primeintellect")

    stub_server.default_response = chat_completion("True")
    quiz = (ToF(prompt="q", answer=True),)
    marks = provider.evaluate(
        quiz, "m-primeintellect-dispatch-test", seed=1,
        max_parallel=2, request_timeout=30, show_progress=False,
    )
    assert marks.correct == 1


def test_aws_body_model_and_key_resolution(stub_server, monkeypatch):
    from smolbench.evals.providers import aws

    monkeypatch.setenv("AWS_INFERENCE_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "bedrock-key")
    stub_server.queue_response(chat_completion("7"))
    content, _ = aws.query("p", "qwen.qwen3-32b", seed=5, context_length=100)
    assert content == "7"
    body = stub_server.requests[-1]["body"]
    assert body["model"] == "qwen.qwen3-32b"  # Bedrock: model id sent verbatim
    # AWS_INFERENCE_API_KEY (call-time) outranks the Bedrock key without
    # any module reload. This is the provision_endpoint token-refresh
    # contract.
    monkeypatch.setenv("AWS_INFERENCE_API_KEY", "minted")
    assert aws._api_key() == "minted"


# ---------------------------------------------------------------------------
# ChatClient.complete() / ChatResult: token usage, model, finish_reason
# ---------------------------------------------------------------------------


def test_complete_returns_chat_result_with_usage(ec2_env):
    """ChatResult.cached_prompt_tokens holds usage.prompt_tokens_details.cached_tokens.

    This is how OpenRouter and OpenAI report Anthropic and OpenAI
    prompt-cache hits. It lands alongside the other usage fields, the
    server-reported model id, and finish_reason.
    """
    from smolbench.evals.providers import ec2

    ec2_env.queue_response(
        {
            "choices": [{"message": {"content": "7"}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 3,
                "total_tokens": 15,
                "prompt_tokens_details": {"cached_tokens": 5},
            },
            "model": "qwen2.5-1.5b-served",
        }
    )
    result = ec2.complete("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert result.content == "7"
    assert result.reasoning is None
    assert result.prompt_tokens == 12
    assert result.completion_tokens == 3
    assert result.cached_prompt_tokens == 5
    assert result.total_tokens == 15
    assert result.model == "qwen2.5-1.5b-served"
    assert result.finish_reason == "stop"


def test_complete_usage_absent_defaults_to_zero_and_none(ec2_env):
    """No usage, model, or finish_reason is reported at all.

    The documented absent-value defaults apply: 0 for counts, None for
    total_tokens and finish_reason, the requested model id as a
    fallback. Never a KeyError.
    """
    from smolbench.evals.providers import ec2

    ec2_env.queue_response(chat_completion("7", usage=None))
    result = ec2.complete("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert result.prompt_tokens == 0
    assert result.completion_tokens == 0
    assert result.cached_prompt_tokens == 0
    assert result.total_tokens is None
    assert result.model == "qwen2.5-1.5b"  # falls back to the requested id
    assert result.finish_reason is None


# ---------------------------------------------------------------------------
# Per-call `system`: message ordering
# ---------------------------------------------------------------------------


def test_complete_system_message_ordering_with_provider_prompt(ec2_env):
    """[provider system, per-call system, user] in that order.

    The provider's deploy-spec toggle, ministral's [THINK]-protocol
    default system message, must survive ahead of a caller-supplied
    system message, per complete()'s ``system`` parameter doc.
    """
    from smolbench.evals.providers import ec2
    from smolbench.evals.providers.ec2 import MINISTRAL_THINK_SYSTEM

    ec2.complete(
        "user prompt", "ministral-3-14b", seed=1, context_length=200000,
        system="extra context",
    )
    body = ec2_env.requests[-1]["body"]
    assert body["messages"] == [
        {"role": "system", "content": MINISTRAL_THINK_SYSTEM},
        {"role": "system", "content": "extra context"},
        {"role": "user", "content": "user prompt"},
    ]
    assert body["seed"] == 1  # repo rule: the decoding seed always ships


def test_complete_system_message_without_provider_prompt(ec2_env):
    """No provider-level system_prompt for this model -> [system, user]."""
    from smolbench.evals.providers import ec2

    ec2.complete("user prompt", "qwen2.5-1.5b", seed=1, context_length=100, system="extra context")
    body = ec2_env.requests[-1]["body"]
    assert body["messages"] == [
        {"role": "system", "content": "extra context"},
        {"role": "user", "content": "user prompt"},
    ]


# ---------------------------------------------------------------------------
# query() stays a thin 2-tuple wrapper, forwarding the new kwargs
# ---------------------------------------------------------------------------


def test_query_still_returns_tuple_and_forwards_system(ec2_env):
    """query()'s positional signature and 2-tuple return are unchanged.

    ``system``, a new keyword-only argument, passes through to the same
    message ordering complete() produces.
    """
    from smolbench.evals.providers import ec2

    from smolbench.evals.providers.ec2 import MINISTRAL_THINK_SYSTEM

    ec2_env.queue_response(chat_completion("7"))
    content, reasoning = ec2.query(
        "user prompt", "ministral-3-14b", context_length=200000, seed=1,
        system="extra context",
    )
    assert content == "7"
    assert reasoning is None
    body = ec2_env.requests[-1]["body"]
    assert body["messages"] == [
        {"role": "system", "content": MINISTRAL_THINK_SYSTEM},
        {"role": "system", "content": "extra context"},
        {"role": "user", "content": "user prompt"},
    ]


def test_openrouter_complete_via_provider_dispatch(stub_server, monkeypatch):
    """The module-level provider.complete() dispatcher mirrors provider.query()."""
    monkeypatch.setenv("OPENROUTER_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("INFERENCE_PROVIDER", "openrouter")
    from smolbench.evals import provider

    stub_server.queue_response(chat_completion("True"))
    result = provider.complete("p", "m-complete-dispatch-test", seed=1, context_length=100)
    assert result.content == "True"
    assert result.total_tokens == 10  # conftest's chat_completion default usage


# ---------------------------------------------------------------------------
# max_retries: bounded retry loop
# ---------------------------------------------------------------------------
#
# tests/conftest.py's shared StubServer always replies 200 (see its _reply),
# so it cannot emit the 500s these tests need. Rather than change that
# shared fixture (other test modules depend on its current behavior
# unchanged), this is a small LOCAL status-code-capable server, used only
# here, built the same way (http.server + a request-recording handler).


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
        length = int(self.headers.get("Content-Length", "0") or "0")
        self.rfile.read(length)  # drain the body; the retry tests don't need it
        code, body = self.server.next_response()
        self._reply(body, code)

    def do_GET(self):
        # Same scripted queue for GETs (metadata_get error-status tests).
        code, body = self.server.next_response()
        self._reply(body, code)

    def log_message(self, *args):
        pass  # keep pytest output clean


class _FlakyServer(ThreadingHTTPServer):
    """Queue of scripted (status_code, body) responses, for max_retries tests."""

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


def _flaky_client(flaky_server) -> ChatClient:
    """A bespoke ChatClient pointed at ``flaky_server``.

    ``retry_backoff_s=0`` so a test that deliberately retries doesn't
    actually sleep -- these tests are about the retry COUNT, not timing.
    """
    return ChatClient(
        name="flaky-test",
        env_prefix="FLAKY_TEST",
        connection=lambda model: (f"{flaky_server.base_url}/chat/completions", "stub-key"),
        context_length=lambda model: 100,
        retry_backoff_s=0,
    )


def test_complete_max_retries_raises_on_nth_failure(flaky_server):
    """Two queued 500s under max_retries=2.

    The 2nd failure is the Nth, and must raise HTTPError instead of
    sleeping and retrying again.
    """
    flaky_server.queue(500, {"error": "boom 1"})
    flaky_server.queue(500, {"error": "boom 2"})
    client = _flaky_client(flaky_server)
    with pytest.raises(requests.exceptions.HTTPError):
        client.complete("p", "m", seed=1, max_retries=2)


def test_complete_max_retries_succeeds_before_cap(flaky_server):
    """One 500 followed by a 200, under max_retries=2.

    Only 1 failure is seen before the retry succeeds, so it must NOT
    raise.
    """
    flaky_server.queue(500, {"error": "boom"})
    flaky_server.queue(200, chat_completion("7"))
    client = _flaky_client(flaky_server)
    result = client.complete("p", "m", seed=1, context_length=100, max_retries=2)
    assert result.content == "7"


def test_query_forwards_max_retries_to_complete(flaky_server):
    """query()'s wrapper passes max_retries through to complete().

    A single queued 500 under max_retries=1 must raise on that first
    (== Nth) failure rather than retrying, exactly as calling
    complete() directly would.
    """
    flaky_server.queue(500, {"error": "boom"})
    client = _flaky_client(flaky_server)
    with pytest.raises(requests.exceptions.HTTPError):
        client.query("p", "m", seed=1, context_length=100, max_retries=1)


# ---------------------------------------------------------------------------
# Error body survives into the raised HTTPError
# ---------------------------------------------------------------------------


def test_complete_error_body_survives_in_httperror(flaky_server):
    """The raised HTTPError must carry the API's error-BODY text.

    It is not enough to keep just the bare status line: `err.response`
    must stay attached too, with the right status code. Both matter
    downstream. `is_retryable_request_error` classifies retryability by
    reading `err.response.status_code`. Callers persist `str(err)` into
    durable artifacts, for example the Lean sweep's exception rows,
    where the body's actionable detail (context too long, invalid
    model id, billing) is the whole point of keeping it. If either one
    were lost, it would silently blind both consumers.
    """
    marker = "context_length_exceeded"
    flaky_server.queue(400, {"error": {"message": marker, "code": marker}})
    client = _flaky_client(flaky_server)
    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        client.complete("p", "m", seed=1)
    err = excinfo.value
    assert marker in str(err)
    assert "400" in str(err)
    assert err.response is not None
    assert err.response.status_code == 400


# ---------------------------------------------------------------------------
# on_unreachable: connection-level failures route through the diagnosis
# hook at max_retries exhaustion, even when max_connection_failures hasn't
# tripped; HTTP-level failure exhaustion never calls the hook at all.
# ---------------------------------------------------------------------------


def test_on_unreachable_fires_before_max_retries_exhaustion():
    """`max_connection_failures` (here 10) need not trip first.

    The `on_unreachable` diagnosis hook can still fire without it. A
    caller-supplied `max_retries` SMALLER than `max_connection_failures`
    (the Lean sweep's pattern: its default 4 vs EC2's 10, per
    `ChatClient.complete`'s docstring) must still route the terminal
    connection-level failure through the hook before re-raising.
    Without this, a self-managed endpoint that vanished
    (spot reclaim, caller-IP drift) would surface as a bare
    ConnectionError instead of the actionable diagnosis.

    This test uses a closed TCP port, bound then immediately closed so
    nothing listens there, rather than an unroutable address. So every
    connection attempt fails fast with ECONNREFUSED, instead of hanging
    on a connect timeout.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    closed_port = sock.getsockname()[1]
    sock.close()  # nothing listens here -> every connection attempt is refused

    def _diagnose(exc):
        raise RuntimeError("DIAGNOSED")

    client = ChatClient(
        name="closed-port-test",
        env_prefix="CLOSEDPORT_TEST",
        connection=lambda model: (
            f"http://127.0.0.1:{closed_port}/v1/chat/completions", "stub-key",
        ),
        context_length=lambda model: 100,
        retry_backoff_s=0,
        max_connection_failures=10,
        on_unreachable=_diagnose,
    )
    with pytest.raises(RuntimeError, match="DIAGNOSED"):
        client.complete("p", "m", seed=1, max_retries=2)


def test_on_unreachable_not_called_on_http_500_exhaustion(flaky_server):
    """The `on_unreachable` hook is scoped to CONNECTION-level failures only.

    An HTTP 500 exhausting `max_retries` must raise the plain HTTPError
    WITHOUT ever invoking the hook. `complete()`'s except block only
    increments `connection_failures`, the counter the hook-firing
    branch checks via `connection_failures > 0`, for non-HTTP
    RequestExceptions. So a managed API returning sustained 5xx must
    never be misdiagnosed as an unreachable self-managed endpoint.
    """
    diagnosed: list = []
    client = ChatClient(
        name="http500-test",
        env_prefix="HTTP500_TEST",
        connection=lambda model: (f"{flaky_server.base_url}/chat/completions", "stub-key"),
        context_length=lambda model: 100,
        retry_backoff_s=0,
        max_connection_failures=10,
        on_unreachable=diagnosed.append,
    )
    flaky_server.queue(500, {"error": "boom1"})
    flaky_server.queue(500, {"error": "boom2"})
    with pytest.raises(requests.exceptions.HTTPError):
        client.complete("p", "m", seed=1, max_retries=2)
    assert diagnosed == []


# ---------------------------------------------------------------------------
# metadata_get -- the shared bearer-authenticated metadata GET
# ---------------------------------------------------------------------------


def test_metadata_get_round_trip_sends_bearer_auth(stub_server):
    body = metadata_get(
        f"{stub_server.base_url}/models", "sekret-key", check_status=False
    )
    assert body == {"data": [{"id": "stub-model"}]}
    request = stub_server.requests[-1]
    assert request["path"] == "/v1/models"
    assert request["headers"]["Authorization"] == "Bearer sekret-key"


def test_metadata_get_check_status_true_raises_on_500(flaky_server):
    """The list_models call sites (aws, ec2) check status before parsing."""
    flaky_server.queue(500, {"error": "boom"})
    with pytest.raises(requests.exceptions.HTTPError):
        metadata_get(f"{flaky_server.base_url}/models", "k", check_status=True)


def test_metadata_get_check_status_false_passes_error_body_through(flaky_server):
    """The context-length call sites (openrouter, primeintellect) parse the body.

    They do this regardless of status. An error-shaped JSON body must
    flow through unraised. This is the FIDELITY contract in
    metadata_get's docstring.
    """
    flaky_server.queue(500, {"error": {"message": "denied"}})
    body = metadata_get(f"{flaky_server.base_url}/models", "k", check_status=False)
    assert body == {"error": {"message": "denied"}}
