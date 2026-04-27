"""Builds the LLM-facing user message: what the model sees.

Layout:

    Think about and solve the following problem step by step in Lean 4.

    [# Relevant premises          -- only when B >= 1
    ```lean
    <premise 1, full declaration, docstring-stripped>
    ```

    ```lean
    <premise 2 ...>
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
      <t_1>
      ...
      <t_K>
      -- complete the proof
    ```

The premises section is the *only* place the LLM and Lean views diverge in
content (beyond the LLM-only `# Theorem:` header). Knob B controls the
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
    "Think about and solve the following problem step by step in Lean 4."
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
    for tac in target.tactics[:K]:
        parts.append(_indent(tac))
    parts.append("  -- complete the proof")
    parts.append("```")

    return "\n".join(parts) + "\n"
