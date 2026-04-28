"""OpenAI-compatible client for the local vLLM server + extraction of the
model's proof body from a chat-completion response.

The extractor returns a ProofBody dataclass (body text + the path used to
extract it, for diagnostics). DESIGN.md's logging schema records
`extraction_path` for every cell.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

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


def _take_body_at_indent(text: str, *, after_offset: int) -> Optional[str]:
    """Starting just past `:= by` at `after_offset`, take the proof body
    and stop at a column-0 dedent.

    Two cases for the byte at `after_offset`:
      - newline (multi-line `:= by\\n`): skip it, then collect lines whose
        indent is > 0 (tactics) or which are empty. The first column-0
        non-empty line ends the body.
      - any other char (inline `:= by tac`): take the rest of that line as
        the first body line (with synthetic 2-space indent), then continue
        with multi-line behavior on the line after it.
    """
    if after_offset >= len(text):
        return None

    body_lines: list[str] = []

    sep_char = text[after_offset]
    if sep_char == "\n":
        cursor = after_offset + 1
    else:
        # Inline body — take to end-of-line, then continue.
        eol = text.find("\n", after_offset)
        first = text[after_offset:eol] if eol != -1 else text[after_offset:]
        first = first.lstrip()
        if first:
            body_lines.append("  " + first)
        cursor = eol + 1 if eol != -1 else len(text)

    remaining = text[cursor:]
    for line in remaining.split("\n"):
        if line.strip() == "":
            body_lines.append("")
            continue
        # Drop ```-fence terminators that occasionally land in raw output.
        if line.strip().startswith("```"):
            break
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent == 0:
            break
        body_lines.append(line)

    # Drop trailing empty lines.
    while body_lines and body_lines[-1] == "":
        body_lines.pop()

    if not body_lines:
        return None
    return "\n".join(body_lines)


def _extract_named(text: str, local_name: str) -> Optional[str]:
    """Find the LAST `theorem <local_name>` head in `text`, locate its
    `:= by`, and return the body up to the first column-0 dedent. None on
    miss."""
    head_re = re.compile(
        r"(?:^|\n)(?:theorem|lemma|example)\s+" + re.escape(local_name) + r"\b"
    )
    matches = list(head_re.finditer(text))
    if not matches:
        return None
    head_end = matches[-1].end()
    by_re = re.compile(r":=\s*by\b")
    by_match = by_re.search(text, head_end)
    if not by_match:
        return None
    return _take_body_at_indent(text, after_offset=by_match.end())


def _extract_last_by(text: str) -> Optional[str]:
    """Fallback: take the body of the LAST `:= by` in `text`, with the
    same column-0 stop rule. Imprecise (may grab an inner have-block) but
    useful when the model emits Lean without a recognizable theorem head."""
    by_re = re.compile(r":=\s*by\b")
    last = None
    for m in by_re.finditer(text):
        last = m
    if last is None:
        return None
    return _take_body_at_indent(text, after_offset=last.end())


def extract_proof_body(model_output: str, local_name: str) -> ProofBody:
    """Locate the proof body of `theorem <local_name>` in the model output.

    Strategy:
      1. Iterate fenced ```lean ... ``` blocks latest-first; for each, try
         the named-anchor extractor (`theorem <local_name> ... := by`).
      2. Fall back to the same named-anchor extractor against the entire
         raw response (handles models that don't fence).
      3. Last resort: last `:= by` in the raw response.
    """
    fences = _FENCE_RE.findall(model_output)
    for block in reversed(fences):
        body = _extract_named(block, local_name)
        if body is not None:
            return ProofBody(body=_normalize_body(body),
                             extraction_path="fenced_with_local")
        # Even a fenced block w/o the local_name head can sometimes give
        # a usable body via last-`:= by`.
        body = _extract_last_by(block)
        if body is not None:
            return ProofBody(body=_normalize_body(body),
                             extraction_path="fenced_last_by")
    # No fenced block worked — try raw output.
    body = _extract_named(model_output, local_name)
    if body is not None:
        return ProofBody(body=_normalize_body(body),
                         extraction_path="raw_with_local")
    body = _extract_last_by(model_output)
    if body is not None:
        return ProofBody(body=_normalize_body(body),
                         extraction_path="raw_last_by")
    return ProofBody(body=None, extraction_path="parse_error")


def _normalize_body(body: str) -> str:
    """Trim trailing fence remnants and trailing whitespace. Keeps internal
    indentation intact."""
    body = re.sub(r"\n```\s*$", "", body)
    return body.rstrip()
