"""
Tokenize prompts for the model under test, to size token-matched prompts.

The induction ``noise_intens`` arm pads the intensional (rule) prompt to the
length of the extensional (listing) prompt, so an intens-vs-extens gap cannot
be blamed on prompt length. Length means TOKENS under the tested model's OWN
tokenizer, not characters: at the periodic production config (``n=9``, seed
1776, ``cl100k_base``) a character-matched pad ran 1.62x the extensional
prompt's 26,279 tokens. `for_model` maps an eval model alias (a key of
``ec2.EC2_DEPLOY_SPECS``, also vLLM's ``--served-model-name``) to that
checkpoint's `Tokenizer`.

NO SILENT FALLBACKS: every constructor raises when it cannot load its
tokenizer. A count here fixes PROMPT BYTES, so a fallback would emit a
differently padded prompt under the same seed and break the guarantee that a
replicate's ``rep_{seed}.yaml`` is regenerable byte-for-byte from its filename.
"""

import functools
import logging
from typing import Any, Protocol, runtime_checkable

import requests

from smolbench.evals.openai_compat import METADATA_TIMEOUT_S


@runtime_checkable
class Tokenizer(Protocol):
    """Anything that can count a string's tokens for the model under test.

    Structural, not nominal, so the offline test suite can drive the
    token-matching machinery with a deterministic stub.
    """

    #: Human-readable identity of the tokenizer (repo id, encoding name,
    #: served model...). This is only used in error messages and log
    #: lines, so its exact format is free -- it exists so a token-match
    #: failure names WHICH tokenizer could not reach the target.
    name: str

    def count(self, text: str) -> int:
        """Return the number of tokens `text` encodes to.

        Implementations MUST exclude special/BOS tokens: callers compare two
        prompts the chat template wraps identically downstream, so an
        inconsistently applied offset becomes an off-by-N in the match.
        """
        ...


class HFTokenizer:
    """A model's own tokenizer, loaded from its HuggingFace ``tokenizer.json``.

    Built on ``huggingface_hub`` + ``tokenizers``, not ``transformers``:
    counting needs one file and the Rust BPE that reads it, not torch.
    """

    def __init__(self, name: str, tokenizer: Any) -> None:
        """Wrap an already-constructed ``tokenizers.Tokenizer``.

        Prefer `from_repo`; this stays public so a caller holding a
        local-checkout or test-fixture tokenizer can adapt it without network.

        Parameters
        ----------
        name : str
            Identity for logs/errors, conventionally the HF repo id.
        tokenizer : Any
            Duck-typed on ``encode(text, add_special_tokens=False).ids``.
        """
        self.name = name
        self._tokenizer = tokenizer

    @classmethod
    def from_repo(cls, repo_id: str) -> "HFTokenizer":
        """Download (once, then cached) and load `repo_id`'s tokenizer.

        Fetches only ``tokenizer.json`` (a few MB, not the weights) into the
        ordinary ``~/.cache/huggingface`` hub cache; only the first call needs
        network. Truncation and padding are disabled on load, and that is
        load-bearing: an embedded ``truncation`` stanza is honored on every
        ``encode`` (``nvidia/Llama-3_1-Nemotron-Ultra-253B-v1-FP8`` ships
        ``{"max_length": 512}``, which reported a ~26,000-token induction prompt
        as 512), and a padded batch counts tokens the model never sees.

        Raises
        ------
        ImportError
            ``huggingface_hub`` or ``tokenizers`` is not installed.
        RuntimeError
            The repo ships no ``tokenizer.json`` (common for quantized
            redistributions), or the download/parse failed. The message names
            the ``tokenizer_hf_id`` deploy-spec key that overrides which repo
            the tokenizer comes from.
        """
        try:
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer as HFTokenizerImpl
        except ImportError as exc:  # pragma: no cover -- both are core deps
            raise ImportError(
                "HFTokenizer needs `huggingface_hub` and `tokenizers` "
                f"(pip install smolbench): {exc}"
            ) from exc
        try:
            path = hf_hub_download(repo_id=repo_id, filename="tokenizer.json")
        except Exception as exc:  # noqa: BLE001 -- hub raises a wide family here
            raise RuntimeError(
                f"could not fetch tokenizer.json from {repo_id!r}: "
                f"{type(exc).__name__}: {exc}. If this repo ships weights "
                "only (common for quantized redistributions), point the "
                "deploy spec's `tokenizer_hf_id` key at a repo that has the "
                "tokenizer -- normally the unquantized base model."
            ) from exc
        tokenizer = HFTokenizerImpl.from_file(path)
        tokenizer.no_truncation()
        tokenizer.no_padding()
        return cls(repo_id, tokenizer)

    def count(self, text: str) -> int:
        """Return `text`'s token count under this checkpoint's tokenizer."""
        return len(self._tokenizer.encode(text, add_special_tokens=False).ids)


class TiktokenTokenizer:
    """A fixed ``tiktoken`` encoding, for tests and offline/tokenizer-free work.

    NOT a stand-in for the model under test: ``cl100k_base`` is nobody's
    tokenizer among the served checkpoints. Nothing here falls back to it; a
    caller must select it explicitly.
    """

    def __init__(self, encoding_name: str = "cl100k_base") -> None:
        """Load a ``tiktoken`` encoding by any name ``get_encoding`` accepts.

        Raises
        ------
        ImportError
            ``tiktoken`` (the ``lean`` extra, not a core dependency) is missing.
        """
        try:
            import tiktoken
        except ImportError as exc:  # pragma: no cover -- optional extra
            raise ImportError(
                "TiktokenTokenizer needs `tiktoken` "
                f"(pip install 'smolbench[lean]'): {exc}"
            ) from exc
        self.name = f"tiktoken:{encoding_name}"
        self._encoding = tiktoken.get_encoding(encoding_name)

    def count(self, text: str) -> int:
        """Return `text`'s token count under this encoding."""
        return len(self._encoding.encode(text))


class VLLMTokenizer:
    """Count tokens by asking a LIVE vLLM server's ``/tokenize`` endpoint.

    Ground truth for what the served model sees, so the cross-check that
    `HFTokenizer` loaded the right tokenizer. NOT for the prompt-building hot
    path: sizing one pad takes several ``count`` calls per question, and an HTTP
    round trip on a ~55 KB prompt each time would dwarf the eval.
    """

    def __init__(self, base_url: str, model: str, api_key: str) -> None:
        """Bind to one served model on one vLLM server.

        `base_url` is the OpenAI-compatible base URL (``ec2._base_url()``);
        vLLM serves ``/tokenize`` at the SERVER root, not under ``/v1``, so a
        trailing ``/v1`` is stripped here.
        """
        root = base_url.rstrip("/")
        if root.endswith("/v1"):
            root = root[: -len("/v1")]
        self.name = f"vllm:{model}@{root}"
        self._url = f"{root}/tokenize"
        self._model = model
        self._api_key = api_key

    def count(self, text: str) -> int:
        """Return `text`'s token count as reported by the live server.

        Raises
        ------
        requests.HTTPError
            The endpoint rejected the request. vLLM exposes ``/tokenize`` by
            default, so a 404 means the server predates it or disabled it.
        """
        response = requests.post(
            self._url,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._model, "prompt": text, "add_special_tokens": False},
            timeout=METADATA_TIMEOUT_S,
        )
        response.raise_for_status()
        return int(response.json()["count"])


@functools.lru_cache(maxsize=None)
def for_model(model: str) -> Tokenizer:
    """Return the tokenizer of the checkpoint served under alias `model`.

    `model` is a key of ``ec2.EC2_DEPLOY_SPECS``; the tokenizer comes from that
    spec's ``hf_model_id``, or its ``tokenizer_hf_id`` override for weights-only
    quantized repos. Memoized per alias for the life of the process.

    Raises
    ------
    KeyError
        No deploy spec names `model`; such a caller must build and pass a
        `Tokenizer` itself.

    Notes
    -----
    ``ec2`` is imported INSIDE this function, never at module scope: its
    ``EC2_*`` constants are captured from ``os.environ`` at IMPORT time, so an
    eager import would freeze them for any notebook importing the induction
    stack before its ``load_dotenv(keys.env)`` cell (see
    ``smolbench.induction.experiment``).
    """
    from smolbench.evals.providers import ec2

    spec = ec2.EC2_DEPLOY_SPECS.get(model)
    if spec is None:
        raise KeyError(
            f"no EC2_DEPLOY_SPECS entry for model {model!r}; pass a "
            "Tokenizer explicitly for models outside the spec table"
        )
    repo_id: str = spec.get("tokenizer_hf_id") or spec["hf_model_id"]
    logging.info(f"tokenization.for_model: {model!r} -> {repo_id}")
    return HFTokenizer.from_repo(repo_id)

