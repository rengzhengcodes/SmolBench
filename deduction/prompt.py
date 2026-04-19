"""
Prompt template for deduction trials and a lightweight extractor for the
model's output. One template for now; iterate if a specific model misbehaves.

The instruction asks the model for just the tactic sequence (no `theorem`,
no `:= by`, no prose) so the output is directly feedable to
`deduction.verifier.verify`. `extract_proof` tolerates a few common deviations
(markdown code fences, a leading `by`) without trying to be a full parser.
"""

import re

_FENCE_RE = re.compile(r"```(?:lean4?)?\s*\n(.*?)\n```", re.DOTALL)


def tactics_only_prompt(target_sig: str, context_text: str) -> str:
    """Build a prompt asking the model to emit tactics only."""
    return (
        "You are completing a Lean 4 proof.\n"
        "\n"
        "Available declarations (you may use any of these in the proof):\n"
        f"{context_text}\n"
        "\n"
        "Target theorem:\n"
        f"{target_sig}\n"
        "\n"
        "Write the proof using Lean 4 tactics. Output one tactic per line. "
        "Do not include `theorem`, `:= by`, or any explanation — output only "
        "the tactic sequence.\n"
        "\n"
        "Proof:\n"
    )


def extract_proof(raw: str) -> str:
    """Pull a proof out of a raw LLM response.

    - If the output is wrapped in a ```lean ... ``` fence, take the fence body.
    - Strip a leading `by` token if the model emitted one despite the instruction.
    - Strip leading/trailing whitespace.
    """
    match = _FENCE_RE.search(raw)
    if match:
        raw = match.group(1)
    raw = raw.strip()
    if raw.startswith("by\n"):
        raw = raw[3:].lstrip("\n")
    elif raw.startswith("by "):
        raw = raw[3:]
    return raw.strip()
