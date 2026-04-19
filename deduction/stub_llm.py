"""
LLM stubs for end-to-end plumbing tests. Let us exercise the full harness
(prompt → LLM → verify → TrialResult) without a real model or GPU.

`ground_truth_llm` replies with the benchmark's canonical proof regardless of
prompt — useful for checking that a pass-path exists in the pipeline.
`constant_llm` replies with a fixed string — useful for driving known-fail
paths (e.g., `"sorry"`) or syntax errors.
"""

from typing import List, Optional, Tuple

from deduction.harness import LLMFn


def constant_llm(proof_text: str) -> LLMFn:
    """LLMFn that always returns the same text, ignoring prompt and temperature."""
    def fn(prompt: str, temperature: float) -> Tuple[str, Optional[int], Optional[int]]:
        return proof_text, None, None
    return fn


def ground_truth_llm(traced_tactics: List[dict]) -> LLMFn:
    """LLMFn that replies with the benchmark's canonical proof (joined by \\n)."""
    proof = "\n".join(t["tactic"] for t in traced_tactics)
    return constant_llm(proof)
