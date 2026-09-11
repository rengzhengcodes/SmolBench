"""Test `smolbench.evals.tokenization`: alias -> HF repo resolution and the vLLM cross-check."""

# pylint: disable=missing-function-docstring,missing-class-docstring

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from smolbench.evals import tokenization
from smolbench.evals.providers import ec2


@pytest.fixture(autouse=True)
def _clear_for_model_cache() -> Iterator[None]:
    """`for_model` is `lru_cache`d; keep entries from leaking between tests."""
    tokenization.for_model.cache_clear()
    yield
    tokenization.for_model.cache_clear()


@pytest.fixture
def record_repo(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str | None]]:
    """Captures the repo id `for_model` resolves, without downloading it."""
    seen: list[tuple[str, str | None]] = []

    def fake_from_repo(repo_id: str, revision: str | None = None) -> str:
        seen.append((repo_id, revision))
        return f"tokenizer<{repo_id}>"

    monkeypatch.setattr(tokenization.HFTokenizer, "from_repo", fake_from_repo)
    return seen


def test_for_model_resolution(
    record_repo: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """hf_model_id resolves, tokenizer_hf_id overrides it, unknown aliases raise, and it caches."""
    override = {
        "hf_model_id": "someone/FP8",
        "tokenizer_hf_id": "someone/Override",
        "tp": 8,
        "vllm_args": ["--tokenizer-revision", "ignored"],
    }
    monkeypatch.setitem(
        ec2.EC2_DEPLOY_SPECS,
        "plain-model",
        {"hf_model_id": "Org/M", "vllm_args": ["--tokenizer-revision", "abc"]},
    )
    monkeypatch.setitem(
        ec2.EC2_DEPLOY_SPECS,
        "no-revision-model",
        {"hf_model_id": "someone/Base"},
    )
    monkeypatch.setitem(ec2.EC2_DEPLOY_SPECS, "weights-only-model", override)
    assert tokenization.for_model("plain-model") == "tokenizer<Org/M>"
    assert tokenization.for_model("weights-only-model") == "tokenizer<someone/Override>"
    assert tokenization.for_model("no-revision-model") == "tokenizer<someone/Base>"
    assert record_repo == [
        ("Org/M", "abc"),
        ("someone/Override", None),
        ("someone/Base", None),
    ]
    with pytest.raises(KeyError):
        tokenization.for_model("model-that-does-not-exist")
    assert record_repo == [
        ("Org/M", "abc"),
        ("someone/Override", None),
        ("someone/Base", None),
    ]

    record_repo.clear()
    tokenization.for_model("no-revision-model")
    tokenization.for_model("no-revision-model")
    assert record_repo == []


def test_hf_tokenizer_wraps_an_existing_tokenizer_object() -> None:
    """The constructor adapts any tokenizers-API object and encodes without special tokens."""
    calls: list = []

    class FakeEncoding:
        ids = (1, 2, 3)

    class FakeTokenizer:
        def encode(self, text: str, add_special_tokens: bool = True) -> FakeEncoding:
            calls.append((text, add_special_tokens))
            return FakeEncoding()

    tokenizer = tokenization.HFTokenizer("fake/repo", FakeTokenizer())
    assert tokenizer.count("hello") == 3
    assert tokenizer.name == "fake/repo"
    assert calls == [("hello", False)]


def test_from_repo_disables_truncation_and_padding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A `truncation` stanza in tokenizer.json must not cap `count`."""
    calls: list = []
    download_calls: list[dict] = []

    class FakeTokenizer:
        def no_truncation(self) -> None:
            calls.append("no_truncation")

        def no_padding(self) -> None:
            calls.append("no_padding")

    # pylint: disable-next=unnecessary-lambda-assignment
    mod = lambda **kw: type("M", (), kw)  # noqa: E731

    def fake_download(**kwargs: object) -> str:
        download_calls.append(kwargs)
        return str(tmp_path / "t.json")

    download = mod(hf_hub_download=staticmethod(fake_download))
    loader = mod(Tokenizer=mod(from_file=staticmethod(lambda p: FakeTokenizer())))
    monkeypatch.setitem(sys.modules, "huggingface_hub", download)
    monkeypatch.setitem(sys.modules, "tokenizers", loader)
    tokenizer = tokenization.HFTokenizer.from_repo("fake/repo", revision="abc")
    assert calls == ["no_truncation", "no_padding"]
    assert tokenizer.name == "fake/repo"
    assert download_calls == [
        {
            "repo_id": "fake/repo",
            "filename": "tokenizer.json",
            "revision": "abc",
        }
    ]


# ---------------------------------------------------------------------------
# The token-matched noise pad: public API of this module, not of induction
# ---------------------------------------------------------------------------


def test_the_pad_search_is_public_here() -> None:
    """`tokenization` owns the pad primitives."""
    for name in (
        "WHITESPACE_UNITS",
        "choose_whitespace_unit",
        "token_matched_noise_prompt",
    ):
        assert hasattr(tokenization, name), name
    assert isinstance(tokenization.WHITESPACE_UNITS, tuple)
    assert tokenization.WHITESPACE_UNITS[0] == " \t"


def test_a_merging_tokenizer_has_no_qualifying_unit() -> None:
    """No whitespace unit survives the probes when every run merges to 1 token."""

    class Merging:
        """A tokenizer that merges every whitespace run, so no unit qualifies."""

        name = "merging"

        def count(self, text: str) -> int:
            return 1

    with pytest.raises(ValueError):
        tokenization.choose_whitespace_unit(Merging())
