"""Shared offline OpenAI-stub, tokenizer, and optional S3 fixtures."""

import importlib.util
import json
import math
import os
import re
import sys
import threading
from collections.abc import Iterable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator

import pytest

from tests._paths import NOTEBOOKS
from smolbench.evals.s3_archive import S3Archive as _BaseS3Archive

def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    """Write `rows` with the production JSONL serializer.

    Sharing `runner.jsonl_line` keeps Unicode and record terminators identical
    to files emitted by a real deduction sweep.

    Parameters
    ----------
    path : Path
        Destination file.
    rows : Iterable[dict[str, Any]]
        JSON-compatible records.
    """
    from smolbench.deduction.lean.runner import jsonl_line

    path.write_text("".join(jsonl_line(row) for row in rows))


def cell_row(**overrides: Any) -> dict[str, Any]:
    """Build a full-schema synthetic deduction cell row.

    A shared complete record keeps tests focused on the fields they vary while
    preserving the production schema expected by downstream scripts.

    Parameters
    ----------
    **overrides : Any
        Values replacing the defaults.

    Returns
    -------
    dict[str, Any]
        Synthetic cell row.
    """
    row: dict[str, Any] = {
        "kind": "cell", "theorem_id": "Mini.theoremA", "file_path": "Mini.lean",
        "k": 1, "n_total_tactics": 2, "chain": "stepk", "level": 1,
        "rung": "stepk:1", "replicate_idx": 0, "seed": 0, "model": "model-a",
        "api_model": "model-a", "provider": "stub", "temperature": 0.7,
        "prompt_tokens": 10, "completion_tokens": 5, "cache_read_tokens": 0,
        "cache_creation_tokens": 0, "finish_reason": "stop", "context_chars": 10,
        "gen_ms": 100, "verify_ms": 0, "candidate_proof": "rfl",
        "raw_response": "```lean\nrfl\n```", "reasoning_content": None,
        "verdict": "success", "lean_error": None, "final_state_pp": None,
        "ground_truth_remaining": "rfl", "error": None, "tactics_applied": 0,
        "tactics_total": 1, "ms": 0,
    }
    row.update(overrides)
    return row


def import_run_study(
    name: str, env: dict[str, str] | None = None
) -> tuple[ModuleType | None, BaseException | None, dict[str, str]]:
    """Import the induction driver under an isolated environment.

    Parameters
    ----------
    name : str
        Unique module name.
    env : dict[str, str] or None, optional
        Environment overlay.

    Returns
    -------
    tuple[ModuleType or None, BaseException or None, dict[str, str]]
        Module, import exception, and post-import environment.
    """
    saved = dict(os.environ)
    module: ModuleType | None = None
    exc: BaseException | None = None
    try:
        os.environ.update(env or {})
        spec = importlib.util.spec_from_file_location(
            name, NOTEBOOKS / "induction" / "run_study.py"
        )
        if spec is None or spec.loader is None:
            raise ImportError("could not create run_study module spec")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException as err:
            module, exc = None, err
        env_after = dict(os.environ)
    finally:
        os.environ.clear()
        os.environ.update(saved)
        sys.modules.pop(name, None)
    return module, exc, env_after


class _StubHandler(BaseHTTPRequestHandler):
    """Replay scripted responses and record requests."""

    def _reply(self, obj: Any, code: int = 200) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _reply_sse(self, obj: Any) -> None:
        """Emit character-level SSE frames."""
        message = (obj.get("choices") or [{}])[0].get("message") or {}
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()

        def frame(chunk: Any) -> None:
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

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        payload = json.loads(self.rfile.read(length) or b"{}")
        # Keep headers for authentication and routing checks.
        self.server.requests.append(
            {"path": self.path, "body": payload, "headers": dict(self.headers)}
        )
        response = self.server.next_response()
        if payload.get("stream"):
            self._reply_sse(response)
        else:
            self._reply(response)

    def do_GET(self) -> None:
        self.server.requests.append(
            {"path": self.path, "body": None, "headers": dict(self.headers)}
        )
        if self.path.endswith("/endpoints"):
            self._reply({"data": {"endpoints": [{"context_length": 100000}]}})
        elif "/models/" in self.path:
            self._reply({"context_length": 100000})
        else:
            self._reply({"data": [{"id": "stub-model"}]})

    def log_message(self, *args: Any) -> None:
        pass  # keep pytest output clean


class StubServer(ThreadingHTTPServer):
    """OpenAI-compatible response stub."""

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _StubHandler)
        self.requests: list = []
        self._responses: list = []
        self.default_response = chat_completion("42")

    def queue_response(self, obj: Any) -> None:
        self._responses.append(obj)

    def next_response(self) -> Any:
        return self._responses.pop(0) if self._responses else self.default_response

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}/v1"


def chat_completion(
    content: Any,
    reasoning_content: Any = None,
    reasoning: Any = None,
    usage: Any = ...,
) -> dict[str, Any]:
    """Build a chat-completions response."""
    message = {"content": content}
    if reasoning_content is not None:
        message["reasoning_content"] = reasoning_content
    if reasoning is not None:
        message["reasoning"] = reasoning
    body = {"choices": [{"message": message}]}
    # Ellipsis means default usage; None omits it.
    if usage is ...:
        usage = {"total_tokens": 10}
    if usage is not None:
        body["usage"] = usage
    return body


# Deterministic tokenizer stubs.

_CHUNK_RE = re.compile(r"\s+|\S+")


class StubTokenizer:
    """Tokenizer whose whitespace runs merge for padding tests."""

    name = "stub"

    def count(self, text: str) -> int:
        """Return the stub token count."""
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
    """Tokenizer with a hard cap for saturation tests."""

    name = "truncating-512"

    def __init__(self, cap: int = 512):
        self.cap = cap
        self._inner = StubTokenizer()

    def count(self, text: str) -> int:
        """Return the capped token count."""
        return min(self._inner.count(text), self.cap)


class MergeEverythingTokenizer:
    """Tokenizer with fully merged whitespace for rejection tests."""

    name = "merge-everything"

    def count(self, text: str) -> int:
        """Return the stub token count."""
        return sum(
            1 if chunk.isspace() else math.ceil(len(chunk) / 4)
            for chunk in _CHUNK_RE.findall(text)
        )


@pytest.fixture
def stub_server() -> Iterator[StubServer]:
    server = StubServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture(autouse=True)
def _clear_provider_context_length_caches() -> Iterator[None]:
    """Clear provider context-length caches around each test."""
    def _clear() -> None:
        try:
            from smolbench.evals.providers import openrouter
            openrouter.get_model_context_length.cache_clear()
        except ImportError:
            pass
        try:
            from smolbench.evals.providers import primeintellect
            primeintellect.get_model_context_length.cache_clear()
        except ImportError:
            pass

    _clear()
    yield
    _clear()


class S3Archive(_BaseS3Archive):
    """Read-only S3 archive access.

    Parameters
    ----------
    uri : str
        Archive URI.
    region : str or None
        S3 region.
    """

    def keys(self, rel_prefix: str) -> list[str]:
        """List paths below ``rel_prefix``."""
        full = self._key(rel_prefix).rstrip("/") + "/"
        out: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=full):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                out.append(key[len(self.prefix) + 1:] if self.prefix else key)
        return out

    def exists(self, rel: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=self._key(rel))
            return True
        except self._client.exceptions.ClientError:
            return False

@pytest.fixture(scope="session")
def s3_archive() -> "S3Archive":
    """Return the opt-in S3 archive, or skip."""
    uri = os.environ.get("SMOLBENCH_ARCHIVE_S3", "").strip()
    if not uri:
        pytest.skip("SMOLBENCH_ARCHIVE_S3 not set: archived evidence lives on S3 only")
    pytest.importorskip("boto3")
    region = os.environ.get("SMOLBENCH_RESULTS_S3_REGION") or None
    archive = S3Archive(uri, region)
    try:
        archive.keys("notebooks/deduction/results")
    except Exception as exc:  # noqa: BLE001 -- credentials/network, not a test defect
        pytest.skip(f"S3 archive unreachable: {exc}")
    return archive
