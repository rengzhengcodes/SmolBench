"""Proof-completion driver with helper expansion (the d-axis of the 2-way
plot — kimina/minif2f_v10.py covers the n_given axis).

For each problem we already have a reference proof (DeepSeek-Prover-V2's
miniF2F-solutions). The driver:
  1. Loads the problem + parsed-tactic chunks (same loader as v10).
  2. Builds a partial-proof prompt at `n_given` (default = full proof).
  3. **Expands helpers at depth `d`**: walks the dep-graph of names appearing
     in the (theorem signature + given tactic prefix), gathers each name's
     full Mathlib source declaration, and prepends them to the prompt as a
     `/- ... -/` comment block above the theorem.
  4. Asks Kimina-72B to complete and verifies the output.

Why helpers as a comment block, not Lean code: the names are already in
Mathlib via `import Mathlib`, so re-emitting them as live declarations would
collide on duplicate definition when the model echoes them. As comment text
they're visible to the model (the dilution we're testing) but inert at parse
time.

Sanity expectation: success rate at d > 0 should be at least as good as
d = 0 (the helpers can only add positive on-task info; the dilution
hypothesis predicts diminishing returns or harm only at high d).

This module is designed to share its log schema with kimina/minif2f_v10
(adds `d` and `n_helpers` fields) so a single aggregator can plot both axes.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futs
import glob
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import requests
from openai import OpenAI

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import (
    BENCHMARK_DIR, load_corpus, source_text, strip_comments,
)
from deduction.kimina.lean_query import print_decl

PROOFS_DIR_DEFAULT = "/opt/dlami/nvme/test"
SERVER_DEFAULT = "http://localhost:9000"
VLLM_DEFAULT = "http://localhost:8010/v1"
MODEL_DEFAULT = "AI-MO/Kimina-Prover-72B"

SYSTEM = ("You are an expert programmer and mathematician who helps "
          "formalizing mathematical problems in Lean 4.")
USER_PREFIX_FULL = (
    "Complete the following Lean 4 proof. The theorem is stated and a "
    "prefix of the proof has been given for you; write the COMPLETE "
    "theorem (including the given prefix) ending with a closing proof "
    "in a single ```lean4 block.\n\n"
)
USER_PREFIX_SCRATCH = (
    "Think about and solve the following problems step by step in "
    "Lean 4.\n\n"
)

_FENCE_RE = re.compile(r'```lean4?\s*\n(.*?)\n```', re.DOTALL)
_THEOREM_RE = re.compile(r'^\s*theorem\s+([A-Za-z0-9_\']+)', re.MULTILINE)
_NAME_RE = re.compile(
    r'[A-Za-z_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]'
    r'[a-zA-Z0-9_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]*'
    r'(?:\.[A-Za-z0-9_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]+)*'
)
CORPUS_PATH_DENY_PREFIXES = (".lake/packages/proofwidgets/",)


@dataclass
class ProofProblem:
    name: str
    file_path: str
    sig_text: str
    proof_body: str
    tactics: List[str]
    opens: List[str]


# ----- Loader (mirrors v10) -----

def _split_signature(thm_src: str) -> Tuple[str, int]:
    depth = 0
    body_idx = -1
    i = 0
    while i < len(thm_src) - 1:
        c = thm_src[i]
        if c in "[({":
            depth += 1
        elif c in "])}":
            depth -= 1
        elif depth == 0 and c == ":" and thm_src[i + 1] == "=":
            body_idx = i
            break
        i += 1
    head = thm_src if body_idx == -1 else thm_src[:body_idx]
    m = re.match(r'\s*theorem\s+[A-Za-z0-9_\']+\s*', head)
    if m:
        head = head[m.end():]
    return head.strip(), body_idx


def _split_tactics(body: str) -> List[str]:
    """Indent-transition chunking: lines at the base indent start new chunks;
    deeper-indented lines attach to the preceding chunk."""
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines = lines[1:]
    if not lines:
        return []
    base = len(lines[0]) - len(lines[0].lstrip())
    chunks: List[str] = []
    cur: List[str] = []
    for ln in lines:
        if not ln.strip():
            cur.append(ln)
            continue
        ind = len(ln) - len(ln.lstrip())
        has_nonblank = any(l.strip() for l in cur)
        if ind == base and has_nonblank:
            chunks.append("\n".join(cur).rstrip())
            cur = [ln]
        else:
            cur.append(ln)
    if cur and any(l.strip() for l in cur):
        chunks.append("\n".join(cur).rstrip())
    return chunks


def load_problems(dir_path: str = PROOFS_DIR_DEFAULT) -> List[ProofProblem]:
    probs = []
    for path in sorted(glob.glob(os.path.join(dir_path, "*.lean"))):
        text = open(path).read()
        m = _THEOREM_RE.search(text)
        if m is None:
            continue
        name = m.group(1)
        line = text[:m.start()].count("\n") + 1
        thm_src = text[m.start():].rstrip()
        sig, body_start = _split_signature(thm_src)
        if body_start == -1:
            continue
        body_src = thm_src[body_start + 2:].lstrip()
        if body_src.startswith("by"):
            body_src = body_src[2:]
        tactics = _split_tactics(body_src)
        opens = []
        for ln in text.splitlines()[:line - 1]:
            s = ln.strip()
            if s.startswith("open scoped "):
                opens.extend(s[len("open scoped "):].split())
            elif s.startswith("open "):
                opens.extend(s[len("open "):].split())
        probs.append(ProofProblem(
            name=name, file_path=path, sig_text=sig,
            proof_body=body_src, tactics=tactics, opens=opens,
        ))
    return probs


# ----- Helper expansion (the d-axis) -----

def _names_in(text: str, corpus) -> List[str]:
    """Distinct corpus-resolvable names in `text`, in order, longest-prefix
    match first."""
    seen: Set[str] = set()
    out: List[str] = []
    for m in _NAME_RE.finditer(text):
        n = m.group(0)
        parts = n.split(".")
        for k in range(len(parts), 0, -1):
            cand = ".".join(parts[:k])
            if cand in corpus and cand not in seen:
                seen.add(cand)
                out.append(cand)
                break
    return out


def _walk_deps_to_depth(seed_names: List[str], corpus, server_url: str,
                         depth: int, max_per_layer: int) -> List[str]:
    """BFS over `#print` bodies starting from `seed_names`. Returns names
    discovered at layers 0..depth-1 in BFS order (so the rendered helper
    block reads shallow-to-deep). Caps each layer at `max_per_layer` to
    bound prompt size on heavy fanout."""
    if depth <= 0:
        return list(dict.fromkeys(seed_names))[:max_per_layer]
    layers: List[List[str]] = [list(dict.fromkeys(seed_names))[:max_per_layer]]
    seen: Set[str] = set(layers[0])
    for _ in range(depth - 1):
        next_layer: List[str] = []
        for name in layers[-1]:
            try:
                raw = print_decl(name, server_url)
            except Exception:
                continue
            if raw is None:
                continue
            idx = raw.find(":=")
            body = raw[idx + 2:] if idx >= 0 else ""
            if not body:
                continue
            for n in _names_in(body, corpus):
                if n in seen or len(next_layer) >= max_per_layer:
                    continue
                seen.add(n)
                next_layer.append(n)
        if not next_layer:
            break
        layers.append(next_layer)
    out: List[str] = []
    for layer in layers:
        out.extend(layer)
    return out


def _render_helper_block(names: List[str], corpus) -> Tuple[str, int]:
    """Return (comment_block_text, n_rendered). For each name, prefer the
    real Mathlib source declaration (well-formed, was actually compiled).
    Fall back to the corpus signature for premises outside Mathlib4
    (lean4-core, batteries) where we don't have the clone."""
    if not names:
        return "", 0
    parts: List[str] = []
    for n in names:
        p = corpus.get(n)
        if p is None:
            continue
        src = source_text(p)
        if src is None:
            src = p.corpus_code
        parts.append(strip_comments(src))
    if not parts:
        return "", 0
    body = "\n\n".join(parts)
    block = (
        "/- ----- relevant Mathlib declarations (already imported, do not "
        "redefine) -----\n"
        + body
        + "\n----- end of declarations -----/\n"
    )
    return block, len(parts)


def expand_helpers(prob: ProofProblem, n_given: int, depth: int,
                    corpus, server_url: str,
                    max_per_layer: int = 64) -> Tuple[str, int]:
    """Build the helper comment block for (problem, n_given, depth).
    Seeds from names visible in (theorem sig + first n_given tactics).
    Returns (block_text, n_rendered_decls)."""
    if depth <= 0:
        return "", 0
    visible_text = prob.sig_text + "\n"
    if n_given > 0:
        visible_text += "\n".join(prob.tactics[:n_given]) + "\n"
    seeds = _names_in(visible_text, corpus)
    if not seeds:
        return "", 0
    walked = _walk_deps_to_depth(seeds, corpus, server_url, depth,
                                  max_per_layer=max_per_layer)
    return _render_helper_block(walked, corpus)


# ----- Prompt + verify (mirrors v10) -----

def build_completion_file(prob: ProofProblem, n_given: int,
                          helpers_block: str) -> str:
    if n_given <= 0:
        proof_section = "  sorry"
        rationale = "No proof has been given yet. Provide the full proof."
    elif n_given >= len(prob.tactics):
        proof_section = "\n".join(prob.tactics)
        rationale = "The proof is complete; output it back unchanged."
    else:
        prefix = "\n".join(prob.tactics[:n_given])
        proof_section = prefix + "\n  sorry"
        rationale = (
            f"The first {n_given} steps of the proof are given; "
            f"replace the trailing `sorry` with the rest of the proof."
        )
    opens_line = ""
    if prob.opens:
        opens_line = "open " + " ".join(prob.opens) + "\n"
    return (
        "import Mathlib\nimport Aesop\n\nset_option maxHeartbeats 0\n\n"
        + opens_line + "\n"
        + helpers_block
        + f"-- {rationale}\n"
        + f"theorem {prob.name} {prob.sig_text} := by\n"
        + proof_section + "\n"
    )


def extract_kimina_proof(text: str) -> str:
    blocks = _FENCE_RE.findall(text)
    valid = [b for b in blocks
             if all(k in b for k in ("by", ":=", "import"))
             and ("theorem" in b or "example" in b)]
    return valid[-1] if valid else ""


def generate(client, model, user_msg, max_tokens=128000, temperature=0.1):
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": user_msg}],
        temperature=temperature, max_tokens=max_tokens,
    )
    raw = r.choices[0].message.content or ""
    u = r.usage
    return raw, (u.completion_tokens if u else None)


def verify(server_url, code, timeout=180):
    r = requests.post(
        f"{server_url}/verify",
        json={"codes": [{"custom_id": "x", "proof": code}]},
        timeout=timeout,
    )
    msgs = r.json()["results"][0].get("response", {}).get("messages", [])
    errs = [m for m in msgs if m.get("severity") == "error"]
    return len(errs) == 0, errs


def process(prob, n_given, depth, corpus, client, model, server_url, k,
            log_path, max_per_layer):
    helpers, n_helpers = expand_helpers(prob, n_given, depth, corpus,
                                         server_url, max_per_layer)
    code = build_completion_file(prob, n_given, helpers)
    user_prefix = USER_PREFIX_SCRATCH if n_given <= 0 else USER_PREFIX_FULL
    user_msg = user_prefix + code
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
    rec = {
        "target": prob.name, "n_given": n_given, "d": depth,
        "n_total_tactics": len(prob.tactics), "n_helpers": n_helpers,
        "k_tried": len(attempts), "pass": any_pass, "attempts": attempts,
        "file_chars": len(code), "helpers_chars": len(helpers),
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return prob.name, any_pass, len(attempts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-given", type=int, required=True,
                    help="Number of leading tactics to give. -1 = full proof.")
    ap.add_argument("--d", type=int, required=True,
                    help="Helper expansion depth. 0 = no helpers.")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--n-problems", type=int, default=0,
                    help="Limit pool size (0 = all)")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--max-per-layer", type=int, default=64,
                    help="Cap helpers per BFS layer to bound prompt size.")
    ap.add_argument("--proofs-dir", default=PROOFS_DIR_DEFAULT)
    ap.add_argument("--vllm-url", default=VLLM_DEFAULT)
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    print(f"Loading corpus ...")
    full_corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    corpus = {
        n: p for n, p in full_corpus.items()
        if not any(p.file_path.startswith(d) for d in CORPUS_PATH_DENY_PREFIXES)
    }
    print(f"  {len(full_corpus)} indexed, {len(corpus)} after path filter")

    problems = load_problems(args.proofs_dir)
    if args.n_problems > 0:
        problems = problems[:args.n_problems]

    print(f"n_given={args.n_given}  d={args.d}  pool={len(problems)}  "
          f"k={args.k}  workers={args.workers}  "
          f"max_per_layer={args.max_per_layer}")
    print(f"log={args.log}")
    open(args.log, "w").close()
    client = OpenAI(base_url=args.vllm_url, api_key="EMPTY")

    t0 = time.time()
    passed = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {}
        for p in problems:
            n = args.n_given if args.n_given >= 0 else len(p.tactics)
            fm[ex.submit(process, p, n, args.d, corpus, client, args.model,
                         args.server_url, args.k, args.log,
                         args.max_per_layer)] = p
        for fut in futs.as_completed(fm):
            name, ok, kt = fut.result()
            done = sum(1 for f in fm if f.done())
            n = len(problems)
            tag = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            print(f"  [{done:3d}/{n}] {tag}  {name[:55]:55s}  k={kt}  "
                  f"(running {passed}/{done})", flush=True)

    print(f"\nDone in {(time.time()-t0)/60:.1f} min.  "
          f"pass@{args.k}: {passed}/{len(problems)} = "
          f"{100*passed/max(len(problems),1):.1f}%")


if __name__ == "__main__":
    main()
