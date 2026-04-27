"""OpenAI-compatible client for the local vLLM server + extraction of the
model's proof body from a chat-completion response.

The extractor returns a ProofBody dataclass (body text + the path used to
extract it, for diagnostics). DESIGN.md's logging schema records
`extraction_path` for every cell.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple

from openai import OpenAI

from deduction.prompt import SYSTEM


VLLM_BASE_URL_DEFAULT = "http://localhost:8010/v1"
VLLM_API_KEY = "EMPTY"
MODEL_DEFAULT = "Qwen/Qwen2.5-Math-1.5B-Instruct"


@dataclass(frozen=True, slots=True)
class GenerationResult:
    raw: str
    completion_tokens: Optional[int]


@dataclass(frozen=True, slots=True)
class ProofBody:
    body: Optional[str]            # already-indented text to splice; None on failure
    extraction_path: str           # "fenced_with_local", "fenced_last_by", "raw_last_by", "parse_error"


def make_client(base_url: str = VLLM_BASE_URL_DEFAULT) -> OpenAI:
    return OpenAI(base_url=base_url, api_key=VLLM_API_KEY)


def generate(
    client: OpenAI,
    user_message: str,
    *,
    model: str = MODEL_DEFAULT,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    seed: Optional[int] = None,
) -> GenerationResult:
    """Single chat completion. Returns raw model text + completion_tokens."""
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if seed is not None:
        kwargs["seed"] = seed
    r = client.chat.completions.create(**kwargs)
    raw = r.choices[0].message.content or ""
    tok = r.usage.completion_tokens if r.usage else None
    return GenerationResult(raw=raw, completion_tokens=tok)


# ---------- proof body extraction ----------

_FENCE_RE = re.compile(r"```lean4?\s*\n(.*?)\n```", re.DOTALL)
_BY_RE = re.compile(r":=\s*by\s*\n")  # multi-line tactic block opening
_BY_INLINE_RE = re.compile(r":=\s*by\s+")  # single-line `:= by tac`


def _last_by_split(text: str) -> Optional[str]:
    """Return everything after the last `:= by\\n` in `text`. Falls back to
    `:= by ` (inline) if no multi-line opening is found. Returns None when
    neither pattern matches."""
    last = None
    for m in _BY_RE.finditer(text):
        last = m
    if last is not None:
        return text[last.end():]
    last = None
    for m in _BY_INLINE_RE.finditer(text):
        last = m
    if last is not None:
        return text[last.end():]
    return None


def _last_decl_block(block: str, local_name: str) -> Tuple[Optional[str], str]:
    """Within a fenced block, locate the last `theorem <local_name>` (or
    `example`) and return the proof body that follows. Returns (body,
    path)."""
    # Prefer matching by local_name (handles the case where the model emits
    # several theorems but ours is unambiguous).
    pattern = re.compile(
        r"(?:^|\n)(?:theorem|lemma|example)\s+" + re.escape(local_name) + r"\b"
    )
    matches = list(pattern.finditer(block))
    if matches:
        tail = block[matches[-1].end():]
        body = _last_by_split(tail)
        if body is not None:
            return body, "fenced_with_local"
    # Fallback: any theorem or example, last `:= by` in the whole block
    body = _last_by_split(block)
    if body is not None:
        return body, "fenced_last_by"
    return None, "parse_error"


def extract_proof_body(model_output: str, local_name: str) -> ProofBody:
    """Locate the proof body of `theorem <local_name>` in the model output.

    Strategy:
      1. Find all fenced ```lean ... ``` blocks; iterate latest-first.
         For each, try to find a declaration head matching local_name and
         take the proof body after its `:= by`.
      2. If no fenced block produces a body, fall back to the entire raw
         output (some models emit Lean without fences).
    """
    fences = _FENCE_RE.findall(model_output)
    for block in reversed(fences):
        body, path = _last_decl_block(block, local_name)
        if body is not None:
            return ProofBody(body=_normalize_body(body), extraction_path=path)
    # No fence-found body — try raw output
    body = _last_by_split(model_output)
    if body is not None:
        return ProofBody(body=_normalize_body(body), extraction_path="raw_last_by")
    return ProofBody(body=None, extraction_path="parse_error")


def _normalize_body(body: str) -> str:
    """Trim trailing fence remnants and trailing whitespace. Keeps internal
    indentation intact."""
    # If a trailing ``` slipped through, drop it
    body = re.sub(r"\n```\s*$", "", body)
    return body.rstrip()
