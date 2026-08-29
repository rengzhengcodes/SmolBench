"""Test `smolbench.evals.tokenization`: alias -> HF repo resolution and the vLLM cross-check."""

import sys

import pytest

from smolbench.evals import tokenization
from smolbench.evals.providers import ec2


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


def test_for_model_resolution(record_repo, monkeypatch):
    """hf_model_id resolves, tokenizer_hf_id overrides it, unknown aliases raise, and it caches."""
    override = {"hf_model_id": "someone/FP8", "tokenizer_hf_id": "someone/Override", "tp": 8}
    monkeypatch.setitem(ec2.EC2_DEPLOY_SPECS, "plain-model", {"hf_model_id": "someone/Base"})
    monkeypatch.setitem(ec2.EC2_DEPLOY_SPECS, "weights-only-model", override)
    assert tokenization.for_model("plain-model") == "tokenizer<someone/Base>"
    assert tokenization.for_model("weights-only-model") == "tokenizer<someone/Override>"
    assert record_repo == ["someone/Base", "someone/Override"]
    with pytest.raises(KeyError):
        tokenization.for_model("model-that-does-not-exist")
    assert record_repo == ["someone/Base", "someone/Override"]

    record_repo.clear()
    tokenization.for_model("plain-model")
    tokenization.for_model("plain-model")
    assert record_repo == []


def test_hf_tokenizer_wraps_an_existing_tokenizer_object():
    """The constructor adapts any tokenizers-API object and encodes without special tokens."""
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
    """A `truncation` stanza in tokenizer.json must not cap `count`."""
    calls: list = []

    class FakeTokenizer:
        def no_truncation(self):
            calls.append("no_truncation")

        def no_padding(self):
            calls.append("no_padding")

    mod = lambda **kw: type("M", (), kw)  # noqa: E731
    download = mod(hf_hub_download=staticmethod(lambda **kw: str(tmp_path / "t.json")))
    loader = mod(Tokenizer=mod(from_file=staticmethod(lambda p: FakeTokenizer())))
    monkeypatch.setitem(sys.modules, "huggingface_hub", download)
    monkeypatch.setitem(sys.modules, "tokenizers", loader)
    tokenizer = tokenization.HFTokenizer.from_repo("fake/repo")
    assert calls == ["no_truncation", "no_padding"]
    assert tokenizer.name == "fake/repo"


def test_vllm_tokenizer_calls_the_server_root_endpoint(stub_server):
    """`/tokenize` lives at the SERVER root, not under `/v1`, and asks for no special tokens."""
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
