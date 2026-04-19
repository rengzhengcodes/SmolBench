"""
OpenAI-compatible HTTP `LLMFn` — works against any OpenAI-spec endpoint: local
vLLM, EC2 vLLM, OpenAI, DeepSeek, etc. Server-mode keeps the LLM process
decoupled from the experiment runner and keeps one client abstraction across
local dev and EC2.

To run a local vLLM server against a small model (fits in 8 GB VRAM):

    steam-run bash -c 'LD_LIBRARY_PATH=/run/opengl-driver/lib \\
        uv run vllm serve Qwen/Qwen2.5-1.5B-Instruct \\
            --port 8000 \\
            --max-model-len 8192 \\
            --gpu-memory-utilization 0.85 \\
            --enforce-eager'

NixOS notes (not needed on EC2 / other distros):
- `steam-run` provides an FHS sandbox with `/sbin/ldconfig` available — torch
  and vLLM both shell out to it during CUDA init and fail hard without it.
- `LD_LIBRARY_PATH=/run/opengl-driver/lib` exposes libcuda.so from the Nix
  nvidia-driver package.
- `--enforce-eager` disables torch.compile, which invokes another subprocess
  chain that tends to trip over host-FS assumptions. Eager is slower per
  token but dodges the issue entirely.

Then from Python:

    from deduction.llm_http import openai_compat_llm
    llm = openai_compat_llm(model="Qwen/Qwen2.5-1.5B-Instruct")
    proof, tokens_in, tokens_out = llm(prompt, temperature=0.7)
"""

import os
from typing import Optional, Tuple

from deduction.harness import LLMFn
from deduction.prompt import extract_proof


def openai_compat_llm(
    base_url: str = "http://localhost:8000/v1",
    model: str = "Qwen/Qwen2.5-1.5B-Instruct",
    api_key: Optional[str] = None,
    max_tokens: int = 1024,
    extract: bool = True,
) -> LLMFn:
    """Build an `LLMFn` that hits `base_url` with OpenAI chat-completions.

    `api_key` falls back to `OPENAI_API_KEY` env var or the string `"dummy"`
    for unauthenticated local servers like vLLM defaults. When `extract` is
    True the returned proof text is pre-processed by `deduction.prompt.extract_proof`
    (strips markdown fences, leading `by`); set False for debugging raw
    model output.
    """
    from openai import OpenAI  # deferred import so the module is light if unused

    key = api_key or os.environ.get("OPENAI_API_KEY", "dummy")
    client = OpenAI(base_url=base_url, api_key=key)

    def fn(prompt: str, temperature: float) -> Tuple[str, Optional[int], Optional[int]]:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = resp.choices[0].message.content or ""
        proof_text = extract_proof(content) if extract else content
        u = resp.usage
        return (
            proof_text,
            u.prompt_tokens if u else None,
            u.completion_tokens if u else None,
        )

    return fn
