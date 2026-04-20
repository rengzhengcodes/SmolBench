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
import random
from typing import List, Optional, Tuple

from deduction.harness import LLMFn
from deduction.prompt import extract_proof


def openai_compat_llm(
    base_url: str = "http://localhost:8000/v1",
    base_urls: Optional[List[str]] = None,
    model: str = "Qwen/Qwen2.5-1.5B-Instruct",
    api_key: Optional[str] = None,
    max_tokens: int = 1024,
    extract=None,
) -> LLMFn:
    """Build an `LLMFn` that hits an OpenAI-compatible chat-completions endpoint.

    If `base_urls` is given (list of endpoints), each call picks one at random
    — useful when running several vLLM replicas on separate GPUs to get more
    aggregate throughput. Otherwise `base_url` is used.

    `api_key` falls back to `OPENAI_API_KEY` env var or the string `"dummy"`
    for unauthenticated local servers like vLLM defaults.

    `extract` is a callable `str -> str` applied to the raw completion before
    returning. Defaults to `deduction.prompt.extract_proof` (generic: strips
    code fences + leading `by`). Pass e.g. `extract_proof_dsprover` for the
    DeepSeek-Prover family. Pass `lambda s: s` to disable extraction.
    """
    from openai import OpenAI  # deferred import so the module is light if unused

    if extract is None:
        extract = extract_proof

    if not base_urls:
        base_urls = [base_url]

    key = api_key or os.environ.get("OPENAI_API_KEY", "dummy")
    clients = [OpenAI(base_url=u, api_key=key) for u in base_urls]

    def fn(prompt: str, temperature: float) -> Tuple[str, Optional[int], Optional[int]]:
        client = random.choice(clients)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = resp.choices[0].message.content or ""
        proof_text = extract(content)
        u = resp.usage
        return (
            proof_text,
            u.prompt_tokens if u else None,
            u.completion_tokens if u else None,
        )

    return fn
