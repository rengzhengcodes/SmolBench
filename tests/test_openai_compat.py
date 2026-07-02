"""Offline round trips through the shared client via each provider module.

These are the "offline stub tests" the provider modules reference: they
verify the unified query/evaluate behavior -- reasoning channels, <think>
splitting, the tolerant usage guard, per-model system prompts, and grading --
against a local stub server, with no credentials and no network.
"""

import pytest

from smolbench.evals import Numeric, ToF
from tests.conftest import chat_completion


@pytest.fixture
def ec2_env(stub_server, monkeypatch):
    """Points the ec2 provider at the stub (bypasses the state file)."""
    monkeypatch.setenv("EC2_INFERENCE_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("EC2_VLLM_API_KEY", "stub-key")
    return stub_server


def test_ec2_query_reasoning_content(ec2_env):
    from smolbench.evals import ec2

    ec2_env.queue_response(chat_completion("7", reasoning_content="thought"))
    content, reasoning = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert (content, reasoning) == ("7", "thought")


def test_ec2_query_think_split(ec2_env):
    from smolbench.evals import ec2

    ec2_env.queue_response(chat_completion("<think>step by step</think>\n7"))
    content, reasoning = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert content == "7"
    assert reasoning == "step by step"


def test_ec2_query_missing_usage_tolerated(ec2_env):
    from smolbench.evals import ec2

    ec2_env.queue_response(chat_completion("7", usage=None))
    content, _ = ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)
    assert content == "7"


def test_ec2_query_context_guard(ec2_env):
    from smolbench.evals import ec2

    ec2_env.queue_response(chat_completion("7", usage={"total_tokens": 999}))
    with pytest.raises(ValueError):
        ec2.query("p", "qwen2.5-1.5b", seed=1, context_length=100)


def test_ec2_system_prompt_injected_from_deploy_spec(ec2_env):
    from smolbench.evals import ec2

    # nemotron's spec carries the "detailed thinking on" CoT toggle.
    ec2.query("user prompt", "nemotron-ultra-253b", seed=1, context_length=200000)
    body = ec2_env.requests[-1]["body"]
    assert body["messages"][0] == {"role": "system", "content": "detailed thinking on"}
    assert body["messages"][1] == {"role": "user", "content": "user prompt"}
    assert body["seed"] == 1  # repo rule: the decoding seed always ships


def test_ec2_evaluate_grades_and_orders(ec2_env):
    from smolbench.evals import ec2

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
    from smolbench.evals import openrouter

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


def test_aws_body_model_and_key_resolution(stub_server, monkeypatch):
    from smolbench.evals import aws

    monkeypatch.setenv("AWS_INFERENCE_BASE_URL", stub_server.base_url)
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "bedrock-key")
    stub_server.queue_response(chat_completion("7"))
    content, _ = aws.query("p", "qwen.qwen3-32b", seed=5, context_length=100)
    assert content == "7"
    body = stub_server.requests[-1]["body"]
    assert body["model"] == "qwen.qwen3-32b"  # Bedrock: model id sent verbatim
    # AWS_INFERENCE_API_KEY (call-time) outranks the Bedrock key without any
    # module reload -- the provision_endpoint token-refresh contract.
    monkeypatch.setenv("AWS_INFERENCE_API_KEY", "minted")
    assert aws._api_key() == "minted"
