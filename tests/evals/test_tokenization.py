"""Test `smolbench.evals.tokenization`.

This resolves the tokenizer of the model under test. The induction
noise arm is sized in tokens, and the only tokenizer whose counts
describe what a served model actually sees is that model's own. This
file covers the resolution path, eval model alias to deploy spec to HF
repo id, and the live-server cross-check. Neither touches the network:
the HF download is monkeypatched, and the vLLM endpoint is the offline
stub server the rest of the suite already uses.
"""

import pytest

from smolbench.evals import tokenization


@pytest.fixture(autouse=True)
def _clear_for_model_cache():
    """`for_model` is `lru_cache`d; keep entries from leaking between tests."""
    tokenization.for_model.cache_clear()
    yield
    tokenization.for_model.cache_clear()


@pytest.fixture
def record_repo(monkeypatch):
    """Captures the repo id `for_model` resolves, without downloading it."""
    seen: list = []

    def fake_from_repo(repo_id: str):
        seen.append(repo_id)
        return f"tokenizer<{repo_id}>"

    monkeypatch.setattr(tokenization.HFTokenizer, "from_repo", fake_from_repo)
    return seen


def test_for_model_resolves_the_specs_hf_model_id(record_repo):
    """The alias the notebooks evaluate maps to that checkpoint's repo."""
    assert tokenization.for_model("gemma-4-31b") == "tokenizer<google/gemma-4-31B-it>"
    assert record_repo == ["google/gemma-4-31B-it"]


def test_for_model_prefers_the_tokenizer_hf_id_override(record_repo, monkeypatch):
    """``tokenizer_hf_id`` wins over ``hf_model_id`` when a spec sets it.

    This is the escape hatch for weights-only quantized
    redistributions. The tokenizer is identical to the base model's, so
    a spec can point at a repo that actually ships ``tokenizer.json``,
    without changing what gets served.
    """
    from smolbench.evals import ec2

    monkeypatch.setitem(
        ec2.EC2_DEPLOY_SPECS,
        "weights-only-model",
        {
            "hf_model_id": "someone/Weights-Only-FP8",
            "tokenizer_hf_id": "someone/Base-Model",
            "tp": 8,
        },
    )
    assert tokenization.for_model("weights-only-model") == "tokenizer<someone/Base-Model>"
    assert record_repo == ["someone/Base-Model"]


def test_for_model_rejects_models_with_no_spec(record_repo):
    """An unknown alias is a caller bug, surfaced immediately.

    If it fell back to some default tokenizer, it would silently size
    the length control against the wrong model. That is exactly the
    failure the noise arm exists to rule out, so there is no fallback.
    """
    with pytest.raises(KeyError, match="no EC2_DEPLOY_SPECS entry"):
        tokenization.for_model("model-that-does-not-exist")
    assert record_repo == []


def test_for_model_is_cached_per_alias(record_repo):
    """Repeated lookups reuse one loaded tokenizer (a parse, per replicate)."""
    tokenization.for_model("gemma-4-31b")
    tokenization.for_model("gemma-4-31b")
    assert record_repo == ["google/gemma-4-31B-it"]


def test_hf_tokenizer_wraps_an_existing_tokenizer_object():
    """The constructor adapts any object with the ``tokenizers`` API.

    This keeps the class usable from a local checkout or a test double,
    without a hub round trip. It also pins the
    ``add_special_tokens=False`` contract. The counts being compared
    are of two prompts that get wrapped identically by the chat
    template downstream, so per-prompt special tokens are noise.
    """
    calls: list = []

    class FakeEncoding:
        ids = (1, 2, 3)

    class FakeTokenizer:
        def encode(self, text, add_special_tokens=True):
            calls.append((text, add_special_tokens))
            return FakeEncoding()

    tokenizer = tokenization.HFTokenizer("fake/repo", FakeTokenizer())
    assert tokenizer.count("hello") == 3
    assert tokenizer.name == "fake/repo"
    assert calls == [("hello", False)]


def test_from_repo_disables_truncation_and_padding(monkeypatch, tmp_path):
    """A ``truncation`` stanza in tokenizer.json must not cap ``count``.

    Found live: ``nvidia/Llama-3_1-Nemotron-Ultra-253B-v1-FP8`` ships
    ``truncation: {max_length: 512}``, and ``tokenizers`` honors it on
    every encode. So a ~26,000-token induction prompt counted as 512.
    Both the extensional prompt and its noise pad would saturate at
    512, the padding search would declare them matched, and the length
    control would be silently wrong by a factor of fifty. That is the
    failure mode the whole token-matching change exists to remove. So
    the loader must switch truncation, and padding, off, and this test
    must keep it off.
    """
    calls: list = []

    class FakeTokenizer:
        def no_truncation(self):
            calls.append("no_truncation")

        def no_padding(self):
            calls.append("no_padding")

    monkeypatch.setattr(
        tokenization, "HFTokenizer", tokenization.HFTokenizer
    )  # explicit: we exercise the real classmethod
    monkeypatch.setitem(
        __import__("sys").modules,
        "huggingface_hub",
        type("M", (), {"hf_hub_download": staticmethod(lambda **kw: str(tmp_path / "t.json"))}),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "tokenizers",
        type("M", (), {"Tokenizer": type("T", (), {"from_file": staticmethod(lambda p: FakeTokenizer())})}),
    )

    tokenizer = tokenization.HFTokenizer.from_repo("fake/repo")
    assert calls == ["no_truncation", "no_padding"]
    assert tokenizer.name == "fake/repo"


def test_vllm_tokenizer_calls_the_server_root_endpoint(stub_server):
    """``/tokenize`` lives at the SERVER root, not under ``/v1``.

    This is the cross-check that a locally loaded tokenizer matches the
    one the served model is actually using. So it has to reach the
    right URL, and ask the same question the local path asks: no
    special tokens.
    """
    stub_server.queue_response({"count": 17})
    tokenizer = tokenization.VLLMTokenizer(stub_server.base_url, "stub-model", "key")

    assert tokenizer.count("some prompt") == 17
    request = stub_server.requests[-1]
    assert request["path"] == "/tokenize"
    assert request["body"] == {
        "model": "stub-model",
        "prompt": "some prompt",
        "add_special_tokens": False,
    }
    assert request["headers"]["Authorization"] == "Bearer key"
