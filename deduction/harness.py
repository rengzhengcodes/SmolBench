"""
Per-trial orchestration for deduction experiments. One trial = build prompt,
call LLM once, verify the result in Lean. `run_trial` repeats k times at a
fixed temperature and returns k TrialResult records.

Caller is responsible for building the target signature and context upstream
(see `deduction.inspect.build_all_depths`). The harness itself is
deduction-specific and knows nothing about the induction track — track
unification comes later.
"""

import time
from typing import Callable, List, Optional, Tuple

from deduction.trial import TrialResult, now_iso
from deduction.verifier import verify

# (prompt, temperature) -> (proof_text, tokens_in, tokens_out)
# tokens may be None for stubs / local engines that don't report counts.
LLMFn = Callable[[str, float], Tuple[str, Optional[int], Optional[int]]]

# (target_sig, context_text) -> prompt_string
PromptTemplate = Callable[[str, str], str]


def run_trial(
    target_id: str,
    file_path: str,
    target_sig: str,
    context_text: str,
    condition: str,
    prompt_template: PromptTemplate,
    llm_fn: LLMFn,
    *,
    k: int = 10,
    temperature: float = 0.7,
    model_name: str = "stub",
) -> List[TrialResult]:
    """Run k LLM calls at one (target, condition), verify each."""
    prompt = prompt_template(target_sig, context_text)
    context_chars = len(context_text)
    results: List[TrialResult] = []
    for i in range(k):
        t0 = time.perf_counter()
        proof_text, tokens_in, tokens_out = llm_fn(prompt, temperature)
        v = verify(file_path, target_id, proof_text)
        wall_ms = int((time.perf_counter() - t0) * 1000)
        results.append(
            TrialResult(
                target_id=target_id,
                file_path=file_path,
                condition=condition,
                context_chars=context_chars,
                model=model_name,
                temperature=temperature,
                k_index=i,
                proof_text=proof_text,
                ok=v.ok,
                error=v.error,
                tactics_applied=v.tactics_applied,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                wall_ms=wall_ms,
                timestamp=now_iso(),
            )
        )
    return results
