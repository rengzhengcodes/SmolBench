"""Builds the LLM-facing user message: what the model sees.

Layout:

    Think about and solve the following problem step by step in Lean 4.
    Provide the complete proof as a single fenced ```lean ... ``` block
    at the end of your response, containing only the theorem and its
    proof body. Do not include `end`, `namespace`, or any wrapping
    declarations.

    [# Relevant premises          -- only when B >= 1
    ```lean
    <premise 1, full declaration, docstring-stripped>
    ```
    ...
    ]

    # Theorem: <T.full_name>      -- header line for unambiguity

    ```lean
    <F's literal direct imports>
    import Aesop
    set_option maxHeartbeats 0

    <scope-only prefix from F>

    theorem <T.local_name> <sig> := by
      [<t_1> ... <t_K>            -- only when K > 0; "first K canonical
                                     tactics shown as a hint"]
      sorry
    ```

Knob K is purely a *hint* in the prompt now: the model sees the first K
canonical tactics (or none, when K=0) and is asked to write the complete
proof. The Lean view assembled at verification time uses the model's full
body, not our K-tactic prefix. K=0 means "no hint"; K=N means "the model
sees the canonical proof in full and is expected to echo it."

The premises section is the only place the LLM and Lean views diverge in
content beyond the LLM-only `# Theorem:` header. Knob B controls the
contents of `premises_blocks`; the elaborator never sees a character of it.
"""
from __future__ import annotations

from typing import Sequence

from deduction.targets import Target


SYSTEM = (
    "You are an expert programmer and mathematician who helps "
    "formalizing mathematical problems in Lean 4."
)
USER_PREFIX = (
    "Think about and solve the following problem step by step in Lean 4.\n"
    "Provide the complete proof as a single fenced ```lean ... ``` block "
    "at the end of your response, containing only `theorem "
    "<theorem-name> <signature> := by` and the body. Do NOT include any "
    "`end`, `namespace`, or other wrapping declarations — they are "
    "already added around your block."
)

_INDENT = "  "


def _indent(text: str) -> str:
    return "\n".join(_INDENT + line if line else line for line in text.splitlines())


def build_user_message(
    target: Target,
    K: int,
    premises_blocks: Sequence[Sequence[str]] = (),
) -> str:
    """Assemble the user-message string.

    `premises_blocks` is a list-of-lists: one inner list per visible tactic,
    each containing already-rendered premise declaration strings (one per
    premise, docstring-stripped, attribute-expanded). The caller — typically
    `elaborate.py` — is responsible for BFS expansion, dedup, and ordering.
    Empty blocks (after dedup) are skipped silently per DESIGN.md.

    K is a hint: the first K canonical tactics are shown to the model as
    a starting point, but the model is asked to write the complete proof.
    """
    if not (0 <= K <= len(target.tactics)):
        raise ValueError(f"K={K} out of range [0, {len(target.tactics)}]")

    parts: list[str] = []
    parts.append(USER_PREFIX)
    parts.append("")

    has_premises = any(block for block in premises_blocks)
    if has_premises:
        parts.append("# Relevant premises")
        parts.append("")
        for block in premises_blocks:
            for premise_decl in block:
                parts.append("```lean")
                parts.append(premise_decl.rstrip("\n"))
                parts.append("```")
                parts.append("")
        # parts already ends with "" from the inner loop

    parts.append(f"# Theorem: {target.full_name}")
    parts.append("")
    parts.append("```lean")
    parts.extend(target.imports)
    parts.append("import Aesop")
    parts.append("set_option maxHeartbeats 0")
    parts.append("")

    if target.f_prefix_scope_only.strip():
        parts.append(target.f_prefix_scope_only.rstrip("\n"))
        parts.append("")

    parts.append(f"theorem {target.local_name} {target.sig_text} := by")
    if K > 0:
        parts.append("  -- first K canonical tactics shown as a hint:")
        for tac in target.tactics[:K]:
            parts.append(_indent(tac))
    parts.append("  sorry")
    parts.append("```")

    return "\n".join(parts) + "\n"
