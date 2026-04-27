"""Builds the Lean verification view: the source file submitted to
kimina-lean-server's `/verify` endpoint.

Layout:

    <F's literal direct imports>
    import Aesop
    set_option maxHeartbeats 0

    <F prefix, lines 1..L-1, leading import block stripped>

    theorem <T.local_name> <sig> := by
      <t_1>
      ...
      <t_K>
      <continuation>

The continuation is either (a) the canonical tactics t_{K+1}..t_N for replay
testing, or (b) the proof body extracted from a model completion. Both views
of the experiment use the same builder; the only thing that varies is the
continuation.
"""
from __future__ import annotations

from deduction.targets import Target


_INDENT = "  "


def _indent(text: str) -> str:
    """Indent every non-empty line of `text` by 2 spaces. Empty lines are
    left empty (no trailing whitespace)."""
    return "\n".join(_INDENT + line if line else line for line in text.splitlines())


def replay_continuation(target: Target, K: int) -> str:
    """Continuation for the replay test. When K=0, return the literal
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


def build_lean_view(target: Target, K: int, continuation: str) -> str:
    """Render the verification source file.

    `continuation` is spliced verbatim after the K indented canonical
    tactics. Caller is responsible for the continuation's own indentation
    (use `replay_continuation` for the canonical case; for model output,
    the extracted proof body should already be indented since it was
    produced inside a `:= by\\n  ...` block)."""
    if not (0 <= K <= len(target.tactics)):
        raise ValueError(f"K={K} out of range [0, {len(target.tactics)}]")

    parts: list[str] = []
    parts.extend(target.imports)
    parts.append("import Aesop")
    parts.append("set_option maxHeartbeats 0")
    parts.append("")

    if target.f_prefix_full.strip():
        parts.append(target.f_prefix_full)
        parts.append("")

    parts.append(f"theorem {target.local_name} {target.sig_text} := by")
    for tac in target.tactics[:K]:
        parts.append(_indent(tac))

    if continuation:
        parts.append(continuation.rstrip("\n"))

    return "\n".join(parts) + "\n"
