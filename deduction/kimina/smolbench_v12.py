"""SmolBench (n_given × depth) grid using v7c-style floating helpers.

Experimental design:
  X axis: % of reference proof shown to model as "premise"
          (first n_given tactics; rest is `sorry` for the model to fill)
  Y axis: completion rate (model writes full proof; we verify)
  Lines:  d = depth to which we expand names found in the premise

Floating-padding design (no sig/tactic rewriting):
  - Theorem signature stays in original Mathlib names.
  - Visible proof prefix stays in original Mathlib names.
  - Helpers (renamed `sb_<name>`) appear above the theorem as floating
    context the model can engage with or ignore. This matches v7c.

Seed mode:
  - "premise" (default): names extracted only from the visible proof
    prefix (first n_given tactics). At n_given=0, no helpers, regardless
    of d. All d-curves coincide at the x=0% baseline.
  - "sig+premise": also includes names from the target signature. At
    n_given=0, only sig-seeded helpers — same as v7c's intensional
    condition.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futs
import json
import os
import re
import sys
import threading
import time
from typing import List

import requests
from openai import OpenAI

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import BENCHMARK_DIR, load_corpus
from deduction.kimina.v7_statement_ext import (
    extract_type_deps, premise_block,
    _IDENT_RE, _BOUND_VAR_BLACKLIST, _NOTATION_MAP,
)
from deduction.kimina.smolbench_v10 import (
    SBTarget, USER_PREFIX, extract_kimina_proof, generate, verify,
    load_smolbench_problems,
)

SERVER_DEFAULT = "http://localhost:9000"
VLLM_DEFAULT = "http://localhost:8010/v1"
MODEL_DEFAULT = "AI-MO/Kimina-Prover-72B"


_UNIV_LINE_RE = re.compile(r'^\s*universes?\s+(.+?)\s*$', re.MULTILINE)


def _dedup_universes(blocks: List[str], existing: set[str]) -> List[str]:
    """Across `blocks`, remove `universe X Y Z` lines that re-declare a
    universe name already in `existing`. Universe declarations are
    module-global in Lean 4, so duplicates cause 'already declared'
    errors. We keep only the first declaration of each name."""
    out = []
    seen = set(existing)
    for block in blocks:
        new_lines = []
        for line in block.splitlines():
            m = _UNIV_LINE_RE.match(line)
            if m:
                names = m.group(1).split()
                fresh = [n for n in names if n not in seen]
                seen.update(names)
                if not fresh:
                    continue  # all already declared, drop the line entirely
                # Emit only the fresh names; preserve indentation
                indent = line[: line.index("universe")]
                new_lines.append(f"{indent}universe {' '.join(fresh)}")
            else:
                new_lines.append(line)
        out.append("\n".join(new_lines))
    return out


def _existing_universes(file_ctx: str) -> set[str]:
    s = set()
    for m in _UNIV_LINE_RE.finditer(file_ctx):
        s.update(m.group(1).split())
    return s


def _block_parses(block: str, server_url: str, timeout: int = 60) -> bool:
    synthetic = "import Mathlib\n\n" + block + "\nexample : True := trivial\n"
    try:
        r = requests.post(
            f"{server_url}/verify",
            json={"codes": [{"custom_id": "x", "proof": synthetic}]},
            timeout=timeout,
        )
        msgs = r.json()["results"][0].get("response", {}).get("messages", [])
        return not any(m.get("severity") == "error" for m in msgs)
    except Exception:
        return False


def _opens_from_file_ctx(file_ctx: str) -> List[str]:
    """Extract namespaces in scope at the target line from the file_ctx
    (which is the result of v7's `collect_target_ctx`). Includes both
    `open <NS>` / `open scoped <NS>` directives and `namespace <NS>`
    blocks (the latter brings <NS>'s declarations into unqualified
    scope inside the namespace body)."""
    opens: List[str] = []
    for line in file_ctx.splitlines():
        s = line.strip()
        if s.startswith("open scoped "):
            opens.extend(s[len("open scoped "):].split())
        elif s.startswith("open "):
            opens.extend(s[len("open "):].split())
        elif s.startswith("namespace "):
            opens.append(s[len("namespace "):].strip())
    return opens


def extract_names_from_text(text: str, corpus, target_name: str | None = None,
                            file_opens: List[str] | None = None) -> List[str]:
    """Sister of v7's `extract_type_deps`, but operates on raw text rather
    than a Premise object. Used to seed name expansion from the visible
    proof prefix (or from sig + prefix). Same regex + corpus filter +
    notation map as v7, plus open-aware resolution: for each unqualified
    identifier, try prefixing each open namespace to find the
    fully-qualified corpus name."""
    hits: List[str] = []
    seen: set = set()

    def _add(name: str):
        if name in corpus and name not in seen:
            hits.append(name)
            seen.add(name)

    # 1. Textual identifiers (filter against corpus + bound-var blacklist).
    for n in _IDENT_RE.findall(text):
        if n in _BOUND_VAR_BLACKLIST:
            continue
        _add(n)
        # Trim dots progressively (A.B.C → A.B → A)
        parts = n.split(".")
        for k in range(len(parts) - 1, 0, -1):
            _add(".".join(parts[:k]))
        # Open-aware resolution: for each opened namespace, try
        # `<ns>.<n>` to catch unqualified references like `rpow_one`
        # (which is `ENNReal.rpow_one` after `open ENNReal`).
        if file_opens:
            for ns in file_opens:
                _add(f"{ns}.{n}")
                # Also try chained: ns prefix on the trimmed-dot variants
                for k in range(len(parts) - 1, 0, -1):
                    _add(f"{ns}.{'.'.join(parts[:k])}")

    # 2. Notation-implied type names (ℝ → Real, ℝ≥0∞ → ENNReal, ...).
    for glyph, mathlib_name in _NOTATION_MAP.items():
        if glyph in text:
            _add(mathlib_name)

    # 3. Target's own namespace ancestors.
    if target_name:
        parts = target_name.split(".")
        for k in range(len(parts) - 1, 0, -1):
            _add(".".join(parts[:k]))

    # 4. File-level opens at the target's source line.
    if file_opens:
        for ns in file_opens:
            _add(ns)

    return hits


def build_v12_file(
    prob: SBTarget, n_given: int, depth: int, corpus,
    server_url: str = SERVER_DEFAULT,
    seed_mode: str = "premise",
) -> str:
    """Build the Lean prompt file at (n_given, depth).

    Parameters
    ----------
    seed_mode : 'premise' (default) or 'sig+premise'
        Controls which names get expanded. 'premise' uses only the visible
        proof prefix; 'sig+premise' also includes the theorem signature.
    """
    n_given = max(0, min(n_given, len(prob.tactics)))

    # Build the text from which we extract names.
    seed_chunks: List[str] = []
    if seed_mode == "sig+premise":
        seed_chunks.append(prob.sig_text)
    elif seed_mode != "premise":
        raise ValueError(f"unknown seed_mode: {seed_mode!r}")
    if n_given > 0:
        seed_chunks.append("\n".join(prob.tactics[:n_given]))
    seed_text = "\n".join(seed_chunks)

    # Extract direct names + BFS depth-d.
    helper_blocks: List[str] = []
    if depth > 0 and seed_text.strip():
        direct = extract_names_from_text(
            seed_text, corpus, prob.name,
            file_opens=_opens_from_file_ctx(prob.file_ctx),
        )
        seen: set = set()
        cum: List[str] = []
        frontier = direct
        for _ in range(depth):
            next_frontier: List[str] = []
            for name in frontier:
                if name in seen:
                    continue
                seen.add(name)
                cum.append(name)
                pp = corpus.get(name)
                if pp is None:
                    continue
                next_frontier.extend(extract_type_deps(pp, corpus))
            frontier = next_frontier
            if not frontier:
                break

        # Emit blocks with v7c's premise_block + per-helper verify+drop.
        for name in cum:
            pp = corpus.get(name)
            if pp is None:
                continue
            block = premise_block(pp, with_doc=False)
            if not block:
                continue
            if not _block_parses(block, server_url):
                continue
            helper_blocks.append(block)

    # Proof section: first n_given tactics, then `sorry` for the rest.
    # (No rewriting — original Mathlib names everywhere; helpers float.)
    if n_given <= 0:
        proof_section = "  sorry"
    elif n_given >= len(prob.tactics):
        proof_section = "\n".join(prob.tactics)
    else:
        proof_section = "\n".join(prob.tactics[:n_given]) + "\n  sorry"

    sb_name = "sb_" + re.sub(r'\W', '_', prob.name)

    # Dedup universe declarations across helpers + file_ctx (Lean's
    # `universe` is module-global; duplicates error).
    existing_universes = _existing_universes(prob.file_ctx)
    deduped_blocks = _dedup_universes(helper_blocks, existing_universes)
    helpers = ("\n\n".join(deduped_blocks) + "\n\n") if deduped_blocks else ""

    return (
        "import Mathlib\nimport Aesop\n\nset_option maxHeartbeats 0\n\n"
        + prob.file_ctx + "\n\n"
        + helpers
        + f"theorem {sb_name} {prob.sig_text} := by\n"
        + proof_section + "\n"
    )


_LOG_LOCK = None


def _resolve_n(spec: str, n_total: int) -> int:
    if spec == "last-1":
        return max(0, n_total - 1)
    if spec.startswith("frac="):
        return int(float(spec[5:]) * n_total)
    n = int(spec)
    return n_total if n < 0 else n


def _run_one(prob, n_given, n_spec_label, depth, seed_mode, corpus, client,
             model, server_url, k):
    code = build_v12_file(prob, n_given, depth, corpus, server_url, seed_mode)
    user_msg = USER_PREFIX + code
    attempts, any_pass = [], False
    for i in range(k):
        t0 = time.perf_counter()
        try:
            raw, tok = generate(client, model, user_msg)
        except Exception as e:
            attempts.append({"k": i, "error": f"gen:{str(e)[:80]}"})
            continue
        proof = extract_kimina_proof(raw)
        if not proof:
            attempts.append({"k": i, "extract_failed": True, "tokens_out": tok})
            continue
        try:
            ok, errs = verify(server_url, proof)
        except Exception as e:
            attempts.append({"k": i, "error": f"ver:{str(e)[:80]}"})
            continue
        attempts.append({
            "k": i, "ok": ok, "tokens_out": tok,
            "first_err": (str(errs[0].get("data"))[:200] if errs else None),
            "wall_ms": int((time.perf_counter() - t0) * 1000),
        })
        if ok:
            any_pass = True
            break
    return {
        "target": prob.name, "n_given": n_given, "n_spec": n_spec_label,
        "depth": depth, "seed_mode": seed_mode,
        "n_total_tactics": len(prob.tactics),
        "k_tried": len(attempts),
        "pass": any_pass, "attempts": attempts, "file_chars": len(code),
    }


def process_grid(prob, cells, seed_mode, corpus, client, model, server_url,
                 k, log_path):
    summary = []
    for n_spec_label, n_given, depth in cells:
        rec = _run_one(prob, n_given, n_spec_label, depth, seed_mode, corpus,
                       client, model, server_url, k)
        with _LOG_LOCK:
            with open(log_path, "a") as f:
                f.write(json.dumps(rec) + "\n")
        summary.append((n_spec_label, depth, rec["pass"]))
    return prob.name, summary


def main():
    global _LOG_LOCK
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-specs", required=True,
                    help="Comma-separated n_given specs.")
    ap.add_argument("--depths", required=True,
                    help="Comma-separated depths.")
    ap.add_argument("--seed-mode", default="premise",
                    choices=["premise", "sig+premise"])
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--vllm-url", default=VLLM_DEFAULT)
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    spec_labels = [s.strip() for s in args.n_specs.split(",") if s.strip()]
    depths = [int(d) for d in args.depths.split(",")]

    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    problems = load_smolbench_problems()
    print(f"n_specs={spec_labels}  depths={depths}  seed={args.seed_mode}  "
          f"pool={len(problems)}  k={args.k}  workers={args.workers}")
    print(f"log={args.log}")
    open(args.log, "w").close()
    client = OpenAI(base_url=args.vllm_url, api_key="EMPTY")
    _LOG_LOCK = threading.Lock()

    t0 = time.time()
    n_done = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {}
        for p in problems:
            cells = [(s, _resolve_n(s, len(p.tactics)), d)
                     for s in spec_labels for d in depths]
            fm[ex.submit(process_grid, p, cells, args.seed_mode, corpus,
                         client, args.model, args.server_url, args.k,
                         args.log)] = p
        for fut in futs.as_completed(fm):
            name, summary = fut.result()
            n_done += 1
            n_pool = len(problems)
            tag = " ".join(f"{s}/d{d}={'P' if ok else 'F'}"
                           for s, d, ok in summary)
            print(f"  [{n_done:3d}/{n_pool}] {name[:45]:45s}  {tag}",
                  flush=True)

    print(f"\nDone in {(time.time()-t0)/60:.1f} min.  "
          f"records: {len(problems) * len(spec_labels) * len(depths)}")


if __name__ == "__main__":
    main()
