"""Builds the Lean verification view: the source file submitted to
kimina-lean-server's `/verify` endpoint.

Layout:

    <F's literal direct imports>
    import Aesop
    set_option maxHeartbeats 0

    <F prefix, lines 1..L-1, leading import block stripped>

    theorem <T.local_name> <sig> := by
      <body>

The body is either (a) the canonical proof body for the replay test or
(b) the full proof body the model wrote. Under the "K as informational
hint" design, K controls only what the prompt SHOWS the model — at
verification time the model produces the entire body from scratch and we
splice it in directly.
"""
from __future__ import annotations

from deduction.targets import Target


_INDENT = "  "


def _indent(text: str) -> str:
    """Indent every non-empty line of `text` by 2 spaces. Empty lines are
    left empty (no trailing whitespace)."""
    return "\n".join(_INDENT + line if line else line for line in text.splitlines())


def replay_continuation(target: Target, K: int) -> str:
    """Canonical proof body for replay tests. When K=0, return the literal
    proof body source from F — preserves bullets, `<;>` combinators, and
    inner-`by` blocks exactly as Lean originally accepted them.

    For K > 0, fall back to joining `target.tactics[K:]`. (LeanDojo's
    flat traced_tactics may misrepresent multi-goal/bullet structure for
    some targets; correct slicing for non-K=0 cases is downstream work.)"""
    if K == 0 and target.proof_body_source:
        return target.proof_body_source
    rest = target.tactics[K:]
    if not rest:
        return ""
    return "\n".join(_indent(t) for t in rest)


def build_lean_view(target: Target, body: str) -> str:
    """Render the verification source file.

    `body` is spliced verbatim as the proof body — the entire content
    after `theorem T sig := by`. The caller is responsible for the body's
    indentation (an extracted model body should already be indented since
    it was produced inside a `:= by` block; replay_continuation returns
    an already-indented string)."""
    parts: list[str] = []
    parts.extend(target.imports)
    parts.append("import Aesop")
    parts.append("set_option maxHeartbeats 0")
    parts.append("")

    if target.f_prefix_full.strip():
        parts.append(target.f_prefix_full)
        parts.append("")

    parts.append(f"theorem {target.local_name} {target.sig_text} := by")

    if body:
        parts.append(body.rstrip("\n"))

    return "\n".join(parts) + "\n"
