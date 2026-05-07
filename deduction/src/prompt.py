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

    [# Canonical proof hint       -- only when K > 0
    The Mathlib proof for this theorem begins with these tactics.
    They are advisory: use them, adapt them, or write a different proof.

    ```lean
    <t_1>
    ...
    <t_K>
    ```
    ]

    # Theorem: <T.full_name>      -- header line for unambiguity

    ```lean
    <F's literal direct imports>
    import Aesop
    set_option maxHeartbeats 0

    <scope-only prefix from F>

    theorem <T.local_name> <sig> := by
      sorry
    ```

K is purely a *hint* in the prompt: the model sees the first K canonical
tactics (or none, when K=0) as separate advisory context outside the
proof block, and is asked to write the complete proof from scratch. The
Lean view assembled at verification time uses the model's full body. The
hint sits above the theorem block (not inside `:= by ... sorry`) so the
model isn't biased toward continuation behavior.

K=0 means "no hint"; K=N means "the model is shown the full canonical
proof in the hint section and can echo it back if it wants."

The premises section is the only other place the LLM and Lean views
diverge. Knob B controls `premises_blocks`; the elaborator never sees a
character of it.
"""
from __future__ import annotations

from typing import Sequence

from .targets import Target


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

MIN_SYSTEM = (
    "You are an expert in mathematics and proving theorems in Lean 4."
)
MIN_USER_PREFIX = (
    "Think about and solve the following problem step by step in Lean 4."
)

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

    if K > 0:
        parts.append("# Canonical proof hint")
        parts.append("")
        parts.append("The Mathlib proof for this theorem begins with these tactics. "
                     "They are advisory: use them, adapt them, or write a different proof.")
        parts.append("")
        parts.append("```lean")
        for tac in target.tactics[:K]:
            parts.append(tac.rstrip("\n"))
        parts.append("```")
        parts.append("")

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
    parts.append("  sorry")
    parts.append("```")

    return "\n".join(parts) + "\n"


def build_min_user_message(target: Target, K: int = 0,
                            style: str = "advisory",
                            premises_blocks: Sequence[Sequence[str]] = ()) -> str:
    """MiniF2F-style minimal prompt: full Mathlib in scope, F's opens/scope
    (from f_prefix_scope_only) as preamble, theorem ending in `:= by`.

    `K` controls how many canonical tactics are shown to the model.
    `style` controls *where*:

    - `style="advisory"` (default): K tactics appear in a separate
      `# Canonical proof hint` section ABOVE the theorem block. The
      theorem block ends with `:= by` and `sorry`. The model writes the
      complete proof from scratch; the hint is informational. K=0
      means no hint; K=N means the full canonical proof is shown but
      stays advisory.

    - `style="continuation"` (v10/v11-style): K tactics appear INSIDE
      the theorem's `:= by` block, followed by `sorry` (when K<N) or
      no sorry (when K=N). Structurally biases the model to continue
      from t_K. K=0 means just `sorry`; K=N means the canonical proof
      with no sorry — model just needs to confirm/echo.

    Both styles target the same downstream pipeline: extract the model's
    full proof body, splice into `build_lean_view_min`'s scaffold (which
    owns the imports + scope + `example sig := by`)."""
    if not (0 <= K <= len(target.tactics)):
        raise ValueError(f"K={K} out of range [0, {len(target.tactics)}]")
    if style not in ("advisory", "continuation"):
        raise ValueError(f"style={style!r} not in (advisory, continuation)")

    parts: list[str] = []
    parts.append(MIN_USER_PREFIX)
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

    if style == "advisory" and K > 0:
        parts.append("# Canonical proof hint")
        parts.append("")
        if K == len(target.tactics):
            parts.append("This is the canonical Mathlib proof. "
                         "You may copy it, adapt it, or write a different proof.")
        else:
            parts.append("The Mathlib proof begins with these tactics. "
                         "They are advisory: use them, adapt them, or write a different proof.")
        parts.append("")
        parts.append("```lean")
        for tac in target.tactics[:K]:
            parts.append(tac.rstrip("\n"))
        parts.append("```")
        parts.append("")

    parts.append(f"# Theorem: {target.full_name}")
    parts.append("")
    parts.append("```lean4")
    parts.append("import Mathlib")
    parts.append("import Aesop")
    parts.append("set_option maxHeartbeats 0")
    if target.f_prefix_scope_only.strip():
        parts.append("")
        parts.append(target.f_prefix_scope_only.rstrip("\n"))
    parts.append("")
    parts.append(f"theorem {target.local_name} {target.sig_text} := by")
    if style == "continuation":
        # First K canonical tactics inline, then `sorry` placeholder if
        # there's more proof to write.
        for tac in target.tactics[:K]:
            for line in tac.splitlines():
                if line.strip() and not line.startswith(" "):
                    parts.append("  " + line)
                else:
                    parts.append(line)
        if K < len(target.tactics):
            parts.append("  sorry")
    else:
        parts.append("  sorry")
    parts.append("```")
    return "\n".join(parts) + "\n"
