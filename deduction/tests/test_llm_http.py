"""
Smoke test for the OpenAI-compatible LLMFn.

Requires a vLLM (or other OpenAI-compatible) server at `localhost:8000` with
the specified model loaded. Start a local vLLM against our default model with:

    uv run vllm serve Qwen/Qwen2.5-1.5B-Instruct --port 8000 --max-model-len 8192

and then run this test. We don't launch the server inside the test because
model loading takes 30-60 s on a warm-cache GPU, so keeping it separate keeps
the test loop fast.
"""

import time

from deduction.llm_http import openai_compat_llm


def test_basic_roundtrip() -> None:
    llm = openai_compat_llm(max_tokens=200)
    t0 = time.perf_counter()
    proof, tin, tout = llm("Say hello in exactly one word.", temperature=0.0)
    dt = time.perf_counter() - t0
    print(f"response ({dt*1000:.0f} ms): {proof!r}")
    print(f"tokens: in={tin}  out={tout}")
    assert len(proof) > 0, "empty response"


def test_proof_shaped_prompt() -> None:
    """Send a prompt shaped like what run_trial would send, confirm we get tactic-like output."""
    from deduction.prompt import tactics_only_prompt
    prompt = tactics_only_prompt(
        target_sig="theorem add_zero_add (a : Nat) : a + 0 + 0 = a",
        context_text="theorem Nat.add_zero (n : Nat) : n + 0 = n",
    )
    llm = openai_compat_llm(max_tokens=300)
    proof, tin, tout = llm(prompt, temperature=0.3)
    print(f"\nproof-shaped response (in={tin} tok, out={tout} tok):")
    print(proof)


def main() -> None:
    test_basic_roundtrip()
    test_proof_shaped_prompt()
    print("\nllm_http smoke test passed.")


if __name__ == "__main__":
    main()
