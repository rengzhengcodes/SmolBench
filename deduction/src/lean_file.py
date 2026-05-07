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

from .targets import Target


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


def _build(target: Target, body: str, imports: list[str], prefix: str,
           *, decl_kind: str = "theorem", use_local_name: bool = True) -> str:
    parts: list[str] = []
    parts.extend(imports)
    parts.append("import Aesop")
    parts.append("set_option maxHeartbeats 0")
    parts.append("")

    if prefix.strip():
        parts.append(prefix)
        parts.append("")

    name_part = f" {target.local_name}" if use_local_name else ""
    parts.append(f"{decl_kind}{name_part} {target.sig_text} := by")

    if body:
        parts.append(body.rstrip("\n"))

    return "\n".join(parts) + "\n"


def build_lean_view(target: Target, body: str) -> str:
    """Render the *truncated-imports* verification source: only F's literal
    direct imports are visible. This is the strict criterion — it enforces
    that the model used only what F itself had access to.

    Uses F's full prefix (lemmas declared before T in F) since those aren't
    available via the truncated imports.

    `body` is spliced verbatim as the proof body — the entire content
    after `theorem T sig := by`. The caller is responsible for the body's
    indentation (an extracted model body should already be indented since
    it was produced inside a `:= by` block; replay_continuation returns
    an already-indented string)."""
    return _build(target, body, list(target.imports), target.f_prefix_full)


def build_lean_view_min(target: Target, body: str) -> str:
    """Lean source for the *min_prompt* baseline: `import Mathlib` + F's
    scope-only prefix + `example sig := by\\n<model_body>`. Uses `example`
    (anonymous) to avoid the "T has already been declared" collision
    that happens when our targets are real Mathlib theorems pulled in
    transitively by `import Mathlib`."""
    return _build(target, body, ["import Mathlib"], target.f_prefix_scope_only,
                  decl_kind="example", use_local_name=False)


def build_lean_view_full_mathlib(target: Target, body: str) -> str:
    """Render the *full-Mathlib* verification source: replaces F's literal
    imports with `import Mathlib`, uses only the scope-only prefix
    (namespace/section/variable) — F's lemma declarations are already
    loaded transitively from Mathlib — and emits the proof as `example`
    rather than `theorem T`. Using `example` avoids "T has already been
    declared" since T itself is in Mathlib once we import it all.

    Used as a relaxed second-pass to distinguish "model wrote broken Lean"
    (fails both views) from "model wrote valid Lean using lemmas outside
    F's scope" (passes Mathlib view, fails truncated view).

    Note: `kimina-no-mathlib-collapse.patch` keeps user imports verbatim,
    so writing `import Mathlib` here actually pulls in all of Mathlib."""
    return _build(target, body, ["import Mathlib"], target.f_prefix_scope_only,
                  decl_kind="example", use_local_name=False)
