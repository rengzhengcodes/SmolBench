#!/usr/bin/env python3
"""Verify hand-crafted "unrelated" Lean 4 instances end to end.

Each row of the input JSONL is a self-contained Lean 4 instance: a fresh
namespace holding a *provided* block (axioms / definitions / helper lemmas),
a target theorem whose proof must follow from that provided material, and a
recorded reasoning chain destined for the ``<think>`` block of an SFT
target. This script is the single mechanical source of truth for whether a
row is acceptable; drafting agents, the merge step, and the final auditors
all run the same gates through it.

Gates, per row (in order; the first failure is recorded in ``verify``):

1.  schema        -- required authoring fields present and well-formed.
2.  ban scan      -- comment-stripped ``theorem_src + proof`` contains none
                     of the 13 banned tactic heads (the simp/rw/exact/apply/
                     rfl families that dominate the existing SmolBench
                     traces). Over-approximate token scan: also catches
                     ``<;> simp``, ``all_goals``, and nested ``by`` forms.
3.  compile       -- ``lake env lean --stdin`` against the traced mathlib4
                     checkout compiles with zero errors and no `sorry`.
4.  axiom audit   -- ``#print axioms`` output parsed; used axioms must be a
                     subset of declared + core (propext, Classical.choice,
                     Quot.sound), never ``sorryAx``; rows declaring axioms
                     must actually use at least one.
5.  provenance    -- the theorem must reference the provided material
                     (declared axiom / def / lemma name, or, for
                     hypothesis-style rows, pass the negative control).
6.  consistency   -- axiom-style rows: a throwaway probe tries to prove
                     ``False`` from the declared axioms with a solver
                     battery; if it *succeeds* the axiom set is
                     inconsistent and the row fails.
7.  neg. control  -- hypothesis-style rows: recompiling with the key
                     hypothesis removed (``negative_control_src``) must
                     FAIL, proving the hypothesis is load-bearing.
8.  chain QC      -- vendored `_qc_gate` from scripts/annotate_lean_cot.py
                     (empty / forbidden markup / too long / restatement /
                     hedging), plus grounding (chain must cite provided
                     names) and a prose ban (chain must not prescribe
                     banned tactics).
9.  decontam      -- `smolbench.deduction.lean.decontam.HoldoutIndex` over
                     the eval holdout: zero hits required; eval-name
                     mentions counted for the manifest.
10. dedupe        -- pairwise 3-gram Jaccard across all rows' theorem
                     statements must stay below 0.8.

Outputs (siblings of the input JSONL, rewritten every run):

- the input JSONL itself, enriched with the audit fields;
- ``<stem>.manifest.json``  -- config / stats / decontamination / soundness;
- ``<stem>.qc.json``        -- reasoning-chain QC report;
- ``<stem>_sft.jsonl``      -- training-ready chat rows whose assistant is
  ``<think>\\n{reasoning_chain}\\n</think>\\n\\n{proof}`` (think style,
  mirroring cot_stepk1_think_8k.jsonl), emitted for passing rows only.

Exit status 0 iff every row passes every gate.

Usage
-----
    .venv/bin/python scripts/verify_handcrafted_lean.py \\
        notebooks/lean/data/handcrafted/unrelated_100.jsonl [--jobs 8] \\
        [--skip-decontam] [--timeout 60]

``--skip-decontam`` is for drafting-agent shard self-gates (the holdout
index build costs ~a minute); the canonical merge run must not use it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ---------------------------------------------------------------------------
# Constants (mirrored in the manifest so a future reader can re-derive runs)
# ---------------------------------------------------------------------------

#: Fixed preamble for every instance. ``autoImplicit false`` is mandatory:
#: with it on, a typo'd identifier silently auto-binds as an implicit and
#: the "proof" compiles against a vacuously generalized statement.
PREAMBLE = (
    "import Mathlib.Tactic\n"
    "set_option autoImplicit false\n"
    "set_option relaxedAutoImplicit false"
)

#: The 13 banned tactic heads: the simp/rw/exact/apply/rfl families that
#: make up ~85% of tactic mass in the existing SmolBench Lean traces.
BANNED_HEADS = (
    "simp", "simp_all", "simp_rw", "simpa", "dsimp",
    "rw", "rwa", "erw",
    "exact", "exacts", "exact_mod_cast",
    "apply", "rfl",
)

#: Token scan over comment-stripped source. The lookbehind stops matches
#: inside dotted/primed identifiers (``Iff.rfl``, ``Nat.rfl``, ``h'rw``);
#: the lookahead stops prefix matches (``rw`` inside ``rwa``) while still
#: firing on interrogative forms (``exact?``, ``simp?``).
BAN_RE = re.compile(
    r"(?<![\w.'])(?:" + "|".join(sorted(BANNED_HEADS, key=len, reverse=True)) + r")(?![\w'])"
)

#: Core axioms any classical Mathlib proof may pull in.
CORE_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})

#: Declaration keywords whose names count as "provided material".
_AXIOM_DECL_RE = re.compile(r"^\s*axiom\s+([A-Za-z_][\w'.]*)", re.MULTILINE)
_DEF_DECL_RE = re.compile(
    r"^\s*(?:noncomputable\s+)?(?:def|abbrev|inductive|structure|instance)\s+([A-Za-z_][\w'.]*)",
    re.MULTILINE,
)
_LEMMA_DECL_RE = re.compile(r"^\s*(?:theorem|lemma)\s+([A-Za-z_][\w'.]*)", re.MULTILINE)

#: Constructs that must never appear in a provided block or proof: escape
#: hatches (`sorry`/`admit`), kernel-bypasses (`native_decide`), soundness
#: hazards in provided code (`partial`/`unsafe`/`opaque`/`unsound macros`).
FORBIDDEN_SRC_RE = re.compile(
    r"(?<![\w.'])(?:sorry|admit|native_decide|partial|unsafe|opaque|macro|elab|notation)(?![\w'])"
)

#: `Type*`/`Sort*` in provided blocks (universe-polymorphism trap) is
#: flagged for review rather than hard-failed.
UNIVERSE_STAR_RE = re.compile(r"(?:Type|Sort)\s*\*")

#: `#print axioms` output, both shapes. The axiom list wraps across lines
#: once it exceeds the pretty-printer width (~7+ axioms), so the bracket
#: body is matched with a newline-tolerant negated class, not `.*$`.
_AXIOMS_DEPENDS_RE = re.compile(r"'([^']+)' depends on axioms: \[([^\]]*)\]")
_AXIOMS_NONE_RE = re.compile(r"^'([^']+)' does not depend on any axioms$", re.MULTILINE)

#: Binder names in a theorem signature: ``(h1 : P -> Q)`` etc.
_BINDER_RE = re.compile(r"[(\[{⦃]\s*([A-Za-z_][\w']*(?:\s+[A-Za-z_][\w']*)*)\s*:")

#: Category slugs, 10 instances each, U0xx block per category.
CATEGORIES = (
    "prop_logic", "custom_inductive", "rec_arithmetic", "algebra_ineq",
    "finite_case", "classical", "existential", "equational_calc",
    "extensionality", "order_mono",
)

MAX_RATIONALE_CHARS = 2500
DEDUPE_FAIL_JACCARD = 0.8
DEDUPE_WARN_JACCARD = 0.6

MATHLIB_COMMIT = "fe4454af900584467d21f4fd4fe951d29d9332a7"
TOOLCHAIN = "leanprover/lean4:v4.7.0-rc2"

_LAKE = Path.home() / ".elan" / "bin" / "lake"
_MATHLIB_DIR = Path(
    os.environ.get(
        "SMOLBENCH_MATHLIB_DIR",
        Path.home() / ".cache" / "lean_dojo"
        / f"leanprover-community-mathlib4-{MATHLIB_COMMIT}" / "mathlib4",
    )
)

#: System prompt for the SFT projection. Deliberately close in register to
#: `smolbench.deduction.lean.prompt.SYSTEM` (same "output only the tactic
#: block" contract, so `prompt.extract_tactic_block` round-trips the
#: assistant after stripping the leading ``<think>`` block).
SFT_SYSTEM = (
    "You are an expert in the Lean 4 theorem prover and the Mathlib4 library.\n"
    "\n"
    "You will be shown a self-contained block of axioms, definitions, and\n"
    "lemmas, followed by a theorem statement ending in `by`. Prove the theorem\n"
    "from the provided material. Respond with **only** the Lean 4 tactic block\n"
    "that completes the proof, with no surrounding markdown or commentary. Use\n"
    "newline-separated tactics exactly as they would appear in a Lean source\n"
    "file.\n"
    "\n"
    "Do not include the theorem statement or the `by` keyword — output only\n"
    "the tactic lines that prove the goal."
)

# ---------------------------------------------------------------------------
# Vendored from scripts/annotate_lean_cot.py (source of truth) -- copied, not
# imported, so this tool stays free of that driver's Bedrock client stack.
# tests/test_lean_handcrafted.py asserts parity with the originals.
# ---------------------------------------------------------------------------

_RESTATEMENT_LINE_FRACTION = 0.5


def _is_restatement(rationale: str, tail: str) -> bool:
    """True if `rationale` looks like it just restates `tail` verbatim."""
    tail_lines = [ln.strip() for ln in tail.splitlines() if ln.strip()]
    if len(tail_lines) < 2:
        return rationale.strip() == tail.strip()
    hits = sum(1 for ln in tail_lines if ln in rationale)
    return (hits / len(tail_lines)) >= _RESTATEMENT_LINE_FRACTION


_HEDGING_RE = re.compile(
    r"\b(?:or similar|likely|probably|presumably|perhaps|maybe|"
    r"i think|not sure|some form of|something like)\b",
    re.IGNORECASE,
)


def _qc_gate(rationale: str, tail: str, *, max_rationale_chars: int) -> Optional[str]:
    """First failing QC reason for a reasoning chain, or None if it passes."""
    rationale = rationale.strip()
    if not rationale:
        return "empty_rationale"
    if "```" in rationale or "<think>" in rationale or "</think>" in rationale:
        return "forbidden_markup"
    if len(rationale) > max_rationale_chars:
        return "too_long"
    if _is_restatement(rationale, tail):
        return "restatement"
    if _HEDGING_RE.search(rationale):
        return "hedging"
    return None


def _distinct_5gram_ratio(rationales: Sequence[str]) -> tuple[int, float]:
    """Word-level distinct-5-gram diversity ratio pooled over a sample."""
    total = 0
    distinct: set[tuple[str, ...]] = set()
    for r in rationales:
        words = r.split()
        for i in range(max(0, len(words) - 4)):
            distinct.add(tuple(words[i : i + 5]))
            total += 1
    return total, (len(distinct) / total if total else 0.0)


# ---------------------------------------------------------------------------
# Source handling
# ---------------------------------------------------------------------------


def strip_comments(src: str) -> str:
    """Remove ``--`` line comments and (nested) ``/- ... -/`` block comments."""
    out: list[str] = []
    i, n, depth = 0, len(src), 0
    while i < n:
        two = src[i : i + 2]
        if depth == 0 and two == "--":
            j = src.find("\n", i)
            i = n if j == -1 else j
            continue
        if two == "/-":
            depth += 1
            i += 2
            continue
        if depth > 0 and two == "-/":
            depth -= 1
            i += 2
            continue
        if depth == 0:
            out.append(src[i])
        i += 1
    return "".join(out)


def ban_scan(src: str) -> list[str]:
    """Banned heads found in comment-stripped source (sorted, deduped)."""
    return sorted(set(BAN_RE.findall(strip_comments(src))))


def tactic_heads(proof: str) -> list[str]:
    """Informational head-token list: first identifier of each tactic segment.

    Splits on newlines, ``<;>`` and top-level ``;``, strips focus bullets
    (``·``, ``|``, ``case ... =>``); purely for the manifest histogram --
    the *gate* is `ban_scan`, not this.
    """
    heads: list[str] = []
    text = strip_comments(proof)
    for line in text.splitlines():
        for seg in re.split(r"<;>|(?<![;]);(?![;])", line):
            seg = seg.strip()
            seg = re.sub(r"^(?:·|\||\.\s)\s*", "", seg)
            m = re.match(r"(?:case\s+[^=]*|[A-Za-z_][\w' ]*)=>\s*(.*)", seg)
            if m:
                seg = m.group(1).strip()
            m = re.match(r"[A-Za-z_][\w'!?]*", seg)
            if m and m.group(0) != "_":
                heads.append(m.group(0))
    return heads


def materialize(row: dict) -> str:
    """Reassemble the exact Lean source for a row (what gets compiled)."""
    parts = [PREAMBLE, "", f"namespace {row['ns']}", ""]
    provided = row.get("provided_src", "").rstrip()
    if provided:
        parts += [provided, ""]
    parts += [
        row["theorem_src"].rstrip("\n") + "\n" + row["proof"].rstrip("\n"),
        "",
        f"#print axioms {row['thm_name']}",
        "",
        f"end {row['ns']}",
        "",
    ]
    return "\n".join(parts)


def parse_axioms(stdout: str) -> dict[str, list[str]]:
    """Parse every ``#print axioms`` line in compiler stdout."""
    out: dict[str, list[str]] = {}
    for m in _AXIOMS_DEPENDS_RE.finditer(stdout):
        out[m.group(1)] = [a.strip() for a in m.group(2).split(",") if a.strip()]

    for m in _AXIOMS_NONE_RE.finditer(stdout):
        out[m.group(1)] = []
    return out


def compile_lean(source: str, timeout: float) -> dict:
    """Compile `source` via ``lake env lean --stdin`` in the mathlib4 dir.

    Returns ``{ok, errors, sorry, stdout, stderr, wall_ms, timed_out}``;
    ``ok`` means exit 0, no ``error:`` diagnostics, and no sorry warning.
    """
    env = dict(os.environ)
    env["PATH"] = f"{_LAKE.parent}:{env.get('PATH', '')}"
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            [str(_LAKE), "env", "lean", "--stdin"],
            input=source,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=_MATHLIB_DIR,
            env=env,
            timeout=timeout,
        )
        stdout, stderr, rc, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        rc, timed_out = -1, True
    wall_ms = int((time.monotonic() - t0) * 1000)
    combined = stdout + "\n" + stderr
    errors = re.findall(r"^.*: error: .*$", combined, re.MULTILINE)
    has_sorry = "declaration uses 'sorry'" in combined
    unused = re.findall(r"^.*unused variable.*$", combined, re.MULTILINE)
    return {
        "ok": rc == 0 and not errors and not has_sorry and not timed_out,
        "errors": errors,
        "sorry": has_sorry,
        "unused": unused,
        "stdout": stdout,
        "stderr": stderr,
        "wall_ms": wall_ms,
        "timed_out": timed_out,
    }


def consistency_probe_source(row: dict) -> str:
    """Throwaway file that tries to refute the row's axiom set.

    Every declared axiom is pulled into the local context with ``have`` so
    context-driven solvers (omega, linarith, simp_all, tauto, aesop) can
    actually see it -- global axioms are not in the local context
    otherwise. The banned-tactic list does NOT apply here: this file is
    tooling and is never recorded.
    """
    haves = "".join(
        f"  have hax{i} := {name}\n"
        for i, name in enumerate(_AXIOM_DECL_RE.findall(row.get("provided_src", "")))
    )
    probe = (
        "theorem inconProbe : False := by\n"
        + haves
        + "  first\n"
        "  | omega\n"
        "  | simp_all\n"
        "  | tauto\n"
        "  | (exfalso; nlinarith)\n"
        "  | (exfalso; linarith)\n"
        "  | decide\n"
        "  | aesop\n"
    )
    parts = [PREAMBLE, "", f"namespace {row['ns']}", ""]
    provided = row.get("provided_src", "").rstrip()
    if provided:
        parts += [provided, ""]
    parts += [probe, f"end {row['ns']}", ""]
    return "\n".join(parts)


def negative_control_source(row: dict) -> str:
    """The row with `negative_control_src` in place of the real signature."""
    parts = [PREAMBLE, "", f"namespace {row['ns']}", ""]
    provided = row.get("provided_src", "").rstrip()
    if provided:
        parts += [provided, ""]
    parts += [
        row["negative_control_src"].rstrip("\n") + "\n" + row["proof"].rstrip("\n"),
        "",
        f"end {row['ns']}",
        "",
    ]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Dedupe
# ---------------------------------------------------------------------------


def _statement_shingles(theorem_src: str) -> frozenset[tuple[str, ...]]:
    """Word 3-gram shingles of a theorem signature, name stripped."""
    text = re.sub(r"^\s*theorem\s+[A-Za-z_][\w'.]*", "theorem", theorem_src.strip())
    words = re.findall(r"[^\s]+", text)
    return frozenset(tuple(words[i : i + 3]) for i in range(max(0, len(words) - 2)))


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------------------
# Per-row verification
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = (
    "id", "category", "provision_style", "ns", "thm_name",
    "theorem_src", "proof", "reasoning_chain",
)


def _schema_check(row: dict) -> Optional[str]:
    """First schema violation, or None."""
    for f in _REQUIRED_FIELDS:
        if not isinstance(row.get(f), str) or not row[f].strip():
            return f"schema:missing_{f}"
    if row["category"] not in CATEGORIES:
        return "schema:unknown_category"
    if row["provision_style"] not in ("axiom", "hypothesis", "definition"):
        return "schema:unknown_provision_style"
    if not re.fullmatch(r"U\d{3}", row["id"]) or row["ns"] != row["id"]:
        return "schema:bad_id_or_ns"
    m = re.match(r"^theorem\s+([A-Za-z_][\w']*)", row["theorem_src"].strip())
    if not m or m.group(1) != row["thm_name"]:
        return "schema:theorem_src_name_mismatch"
    if not row["theorem_src"].rstrip().endswith(":= by"):
        return "schema:theorem_src_must_end_with_by"
    if row["provision_style"] == "hypothesis" and not str(row.get("negative_control_src", "")).strip():
        return "schema:missing_negative_control_src"
    return None


def verify_row(row: dict, *, timeout: float) -> dict:
    """Run gates 1-8 on one row; fill audit fields; return the enriched row.

    Decontam (gate 9) and dedupe (gate 10) are corpus-level and run in
    `main` after the per-row pass.
    """
    row = dict(row)
    provided = row.get("provided_src", "")
    row.setdefault("imports", PREAMBLE)
    declared_axioms = [f"{row.get('ns', '?')}.{n}" for n in _AXIOM_DECL_RE.findall(provided)]
    declared_defs = _DEF_DECL_RE.findall(provided)
    declared_lemmas = _LEMMA_DECL_RE.findall(provided)
    row["declared_axioms"] = declared_axioms
    row["tactic_heads"] = tactic_heads(row.get("proof", ""))
    row["banned_heads_found"] = []
    row["axioms_used"] = []
    row["consistency_probe"] = "n/a"
    row["negative_control"] = "n/a"
    row["universe_star_flag"] = False
    row["wall_ms"] = 0

    def fail(reason: str) -> dict:
        row["verify"] = f"fail:{reason}"
        return row

    # 1. schema
    reason = _schema_check(row)
    if reason:
        return fail(reason)
    if row["imports"] != PREAMBLE:
        return fail("schema:nonstandard_preamble")

    # forbidden constructs anywhere in authored source
    for field_name in ("provided_src", "theorem_src", "proof"):
        found = FORBIDDEN_SRC_RE.findall(strip_comments(row.get(field_name, "")))
        if found:
            return fail(f"forbidden_construct:{field_name}:{','.join(sorted(set(found)))}")
    row["universe_star_flag"] = bool(UNIVERSE_STAR_RE.search(provided))

    # 2. ban scan (theorem_src + proof; provided helper-lemma proofs too --
    # the whole instance must live outside the banned families)
    banned = ban_scan(row["theorem_src"] + "\n" + row["proof"] + "\n" + provided)
    row["banned_heads_found"] = banned
    if banned:
        return fail("banned_heads:" + ",".join(banned))

    # 3. compile
    source = materialize(row)
    row["lean_source_sha256"] = hashlib.sha256(source.encode()).hexdigest()
    res = compile_lean(source, timeout)
    row["wall_ms"] = res["wall_ms"]
    if res["timed_out"]:
        return fail("compile_timeout")
    if res["sorry"]:
        return fail("sorry")
    if not res["ok"]:
        first = res["errors"][0] if res["errors"] else (res["stderr"].strip().splitlines() or ["unknown"])[-1]
        return fail("compile_error:" + first[:200])
    if res["unused"]:
        # Dead haves/binders compile, but they are exactly the proof text a
        # reasoning chain ends up rationalizing falsely (audit-found class).
        return fail("unused_variable:" + res["unused"][0][:200])

    # 4. axiom audit
    printed = parse_axioms(res["stdout"])
    full_name = f"{row['ns']}.{row['thm_name']}"
    row["full_thm_name"] = full_name
    if full_name not in printed:
        return fail("axiom_audit:print_axioms_missing")
    used = printed[full_name]
    row["axioms_used"] = used
    if any(a == "sorryAx" or a.endswith(".sorryAx") for a in used):
        return fail("sorry")
    allowed = set(declared_axioms) | CORE_AXIOMS
    extra = [a for a in used if a not in allowed]
    if extra:
        return fail("axiom_audit:undeclared_axioms:" + ",".join(extra))
    if declared_axioms and not (set(used) & set(declared_axioms)):
        return fail("axiom_audit:no_declared_axiom_used")

    # 5. provenance: theorem must engage the provided material
    provided_names = set(
        n.split(".")[-1] for n in declared_axioms
    ) | set(declared_defs) | set(declared_lemmas)
    thm_and_proof = row["theorem_src"] + "\n" + row["proof"]
    if row["provision_style"] in ("axiom", "definition"):
        if not provided_names:
            return fail("provenance:no_provided_declarations")
        mentioned = [
            n for n in provided_names
            if re.search(rf"(?<![\w.']){re.escape(n)}(?![\w'])", thm_and_proof)
        ]
        if not mentioned:
            return fail("provenance:provided_material_unreferenced")
    if row["provision_style"] == "axiom":
        # The STATEMENT itself must name provided material -- a goal that is
        # pure ambient arithmetic (e.g. `∃ m, n < m`) is provable with the
        # axioms deleted, making the provision decorative (audit-found class).
        stated = [
            n for n in provided_names
            if re.search(rf"(?<![\w.']){re.escape(n)}(?![\w'])", row["theorem_src"])
        ]
        if not stated:
            return fail("provenance:statement_ignores_axioms")

    # 6. consistency probe (any row that declares axioms)
    if declared_axioms:
        probe = compile_lean(consistency_probe_source(row), timeout)
        row["consistency_probe"] = "inconsistent" if probe["ok"] else "clean"
        if probe["ok"]:
            return fail("inconsistent_axioms")

    # 7. negative control (hypothesis-style)
    if row["provision_style"] == "hypothesis":
        nc = compile_lean(negative_control_source(row), timeout)
        row["negative_control"] = "still_compiles" if nc["ok"] else "failed_as_required"
        if nc["ok"]:
            return fail("negative_control_still_compiles")

    # 8. reasoning-chain QC
    chain = row["reasoning_chain"]
    reason = _qc_gate(chain, row["proof"], max_rationale_chars=MAX_RATIONALE_CHARS)
    if reason:
        return fail(f"chain_qc:{reason}")
    grounding_names = set(provided_names)
    if row["provision_style"] == "hypothesis":
        for m in _BINDER_RE.finditer(row["theorem_src"]):
            grounding_names.update(m.group(1).split())
    grounded = [
        n for n in grounding_names
        if re.search(rf"(?<![\w.']){re.escape(n)}(?![\w'])", chain)
    ]
    row["chain_grounding_names"] = sorted(grounded)
    if not grounded:
        return fail("chain_qc:ungrounded")
    chain_banned = ban_scan(chain)
    if chain_banned:
        return fail("chain_qc:prescribes_banned:" + ",".join(chain_banned))

    row["verify"] = "pass"
    return row


# ---------------------------------------------------------------------------
# SFT projection
# ---------------------------------------------------------------------------


def build_sft_row(row: dict) -> dict:
    """Project one passing instance row into a training-ready chat row."""
    provided = row.get("provided_src", "").rstrip()
    provided_block = (
        f"## Provided axioms and lemmas\n```lean\n{provided}\n```\n\n" if provided else ""
    )
    user = (
        provided_block
        + "## Theorem to prove\n```lean\n"
        + row["theorem_src"].rstrip()
        + "\n```\n\n"
        + "Produce the Lean 4 tactic block that proves the theorem from the\n"
        + "provided material. Output only the tactic lines, nothing else."
    )
    assistant = f"<think>\n{row['reasoning_chain'].strip()}\n</think>\n\n{row['proof'].rstrip()}"
    return {
        "system": SFT_SYSTEM,
        "user": user,
        "assistant": assistant,
        "meta": {
            "id": row["id"],
            "category": row["category"],
            "provision_style": row["provision_style"],
            "tactic_heads": row["tactic_heads"],
            "cot_style": "think",
        },
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _percentiles(values: list[int | float]) -> dict:
    if not values:
        return {"p50": 0, "p90": 0, "max": 0}
    vs = sorted(values)
    return {
        "p50": vs[len(vs) // 2],
        "p90": vs[min(len(vs) - 1, int(len(vs) * 0.9))],
        "max": vs[-1],
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("jsonl", type=Path)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--skip-decontam", action="store_true")
    args = ap.parse_args(argv)

    if not _MATHLIB_DIR.is_dir():
        print(f"error: mathlib4 checkout not found at {_MATHLIB_DIR}", file=sys.stderr)
        return 2

    rows = [json.loads(ln) for ln in args.jsonl.read_text().splitlines() if ln.strip()]
    if not rows:
        print("error: no rows", file=sys.stderr)
        return 2

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        rows = list(pool.map(lambda r: verify_row(r, timeout=args.timeout), rows))

    # gate 9: decontam (corpus-level)
    decontam_block: dict = {"skipped": True}
    if not args.skip_decontam:
        from smolbench.deduction.lean import decontam as dc

        idx = dc.HoldoutIndex.build()
        total_mentions = 0
        for row in rows:
            proof_lines = [ln.strip() for ln in row.get("proof", "").splitlines() if ln.strip()]
            hits = idx.check(
                name=row.get("full_thm_name") or f"{row.get('ns')}.{row.get('thm_name')}",
                statement=row.get("theorem_src", ""),
                tactics=proof_lines,
                pairs=[(row.get("theorem_src", ""), proof_lines[0])] if proof_lines else [],
            )
            row["decontam_hits"] = [
                {"key": h.key, "theorem": h.theorem, "detail": h.detail} for h in hits
            ]
            mentions = idx.count_name_mentions(
                row.get("provided_src", "") + row.get("theorem_src", "") + row.get("proof", "")
            )
            row["eval_name_mentions"] = mentions
            total_mentions += mentions
            if hits and row.get("verify") == "pass":
                row["verify"] = "fail:decontam_hit"
        decontam_block = {
            "skipped": False,
            "eval_specs": [["novel_premises", "val"], ["novel_premises", "test"]],
            "index": idx.stats(),
            "holdout_names_sha256": hashlib.sha256(
                "\n".join(sorted(idx.names)).encode()
            ).hexdigest(),
            "hits_total": sum(len(r.get("decontam_hits", [])) for r in rows),
            "eval_name_mentions_total": total_mentions,
        }

    # gate 10: dedupe (corpus-level)
    shingles = {r["id"]: _statement_shingles(r.get("theorem_src", "")) for r in rows}
    dup_fail_pairs, dup_warn_pairs = [], []
    ids = [r["id"] for r in rows]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            jac = _jaccard(shingles[ids[i]], shingles[ids[j]])
            if jac >= DEDUPE_FAIL_JACCARD:
                dup_fail_pairs.append([ids[i], ids[j], round(jac, 3)])
            elif jac >= DEDUPE_WARN_JACCARD:
                dup_warn_pairs.append([ids[i], ids[j], round(jac, 3)])
    flagged = {p[0] for p in dup_fail_pairs} | {p[1] for p in dup_fail_pairs}
    for row in rows:
        if row["id"] in flagged and row.get("verify") == "pass":
            row["verify"] = "fail:near_duplicate"

    # rewrite enriched rows
    args.jsonl.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))

    passing = [r for r in rows if r.get("verify") == "pass"]
    failing = [r for r in rows if r.get("verify") != "pass"]

    # SFT projection (passing rows only)
    sft_path = args.jsonl.with_name(args.jsonl.stem + "_sft.jsonl")
    sft_path.write_text(
        "".join(json.dumps(build_sft_row(r), ensure_ascii=False) + "\n" for r in passing)
    )

    # manifest
    head_hist: dict[str, int] = {}
    for r in passing:
        for h in r["tactic_heads"]:
            head_hist[h] = head_hist.get(h, 0) + 1
    cat_counts: dict[str, int] = {}
    for r in passing:
        cat_counts[r["category"]] = cat_counts.get(r["category"], 0) + 1
    manifest = {
        "config": {
            "mathlib_commit": MATHLIB_COMMIT,
            "toolchain": TOOLCHAIN,
            "preamble": PREAMBLE,
            "preamble_sha256": hashlib.sha256(PREAMBLE.encode()).hexdigest(),
            "ban_list": list(BANNED_HEADS),
            "core_axiom_allowlist": sorted(CORE_AXIOMS),
            "compile_timeout_s": args.timeout,
            "jobs": args.jobs,
            "max_rationale_chars": MAX_RATIONALE_CHARS,
            "dedupe_fail_jaccard": DEDUPE_FAIL_JACCARD,
        },
        "stats": {
            "rows": len(rows),
            "verified_pass": len(passing),
            "verify_failures": {
                r["id"]: r["verify"] for r in failing
            },
            "provision_style": {
                s: sum(1 for r in passing if r["provision_style"] == s)
                for s in ("axiom", "hypothesis", "definition")
            },
            "category_counts": cat_counts,
            "tactic_head_histogram": dict(
                sorted(head_hist.items(), key=lambda kv: -kv[1])
            ),
            "wall_ms": _percentiles([r.get("wall_ms", 0) for r in rows]),
            "universe_star_flags": [r["id"] for r in rows if r.get("universe_star_flag")],
        },
        "decontamination": decontam_block,
        "soundness": {
            "consistency_probe": {
                "clean": sum(1 for r in rows if r.get("consistency_probe") == "clean"),
                "inconsistent": sum(1 for r in rows if r.get("consistency_probe") == "inconsistent"),
                "n/a": sum(1 for r in rows if r.get("consistency_probe") == "n/a"),
            },
            "negative_control": {
                "failed_as_required": sum(
                    1 for r in rows if r.get("negative_control") == "failed_as_required"
                ),
                "still_compiles": sum(
                    1 for r in rows if r.get("negative_control") == "still_compiles"
                ),
            },
        },
        "dedupe": {
            "fail_pairs_ge_0.8": dup_fail_pairs,
            "warn_pairs_0.6_0.8": dup_warn_pairs,
        },
        "output_jsonl": args.jsonl.name,
        "sft_jsonl": sft_path.name,
    }
    args.jsonl.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # qc report
    chains = [r["reasoning_chain"].strip() for r in passing]
    n5, ratio5 = _distinct_5gram_ratio(chains)
    qc = {
        "rows": len(rows),
        "passing": len(passing),
        "rationale_chars": _percentiles([len(c) for c in chains]),
        "distinct_5gram": {"n": n5, "ratio": round(ratio5, 4)},
        "grounding_rate": (
            sum(1 for r in passing if r.get("chain_grounding_names")) / len(passing)
            if passing else 0.0
        ),
        "drop_histogram": {},
    }
    for r in failing:
        key = r["verify"].split(":", 2)[1] if ":" in r["verify"] else r["verify"]
        qc["drop_histogram"][key] = qc["drop_histogram"].get(key, 0) + 1
    args.jsonl.with_suffix(".qc.json").write_text(json.dumps(qc, indent=2) + "\n")

    wall = statistics.mean([r.get("wall_ms", 0) for r in rows]) if rows else 0
    print(
        f"{len(passing)}/{len(rows)} pass | mean compile {wall:.0f} ms | "
        f"sft rows: {len(passing)} -> {sft_path.name}"
    )
    for r in failing:
        print(f"  FAIL {r['id']} ({r.get('category', '?')}): {r['verify']}")
    return 0 if not failing else 1


if __name__ == "__main__":
    raise SystemExit(main())
