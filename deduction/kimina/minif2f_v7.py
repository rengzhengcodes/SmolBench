"""miniF2F driver using v7's statement-extensional extractor.

Problems are standalone `.lean` files in /tmp/minif2f_test_solved/src/.
Each file is:
    import Mathlib
    import Aesop
    set_option maxHeartbeats 0
    open BigOperators Real Nat Topology Rat

    theorem <name> <binders> : <type> := <body>

For each problem we:
 - Extract the theorem signature text.
 - Run v7's extract_type_deps against the Mathlib corpus to find types/defs
   the statement references (seeded from notation map + file's opens).
 - Build helper blocks from those corpus premises (v7.premise_block),
   verify each standalone against the server, drop broken ones.
 - Emit the pilot file with imports, helpers, opens, then the theorem
   renamed to `example` with `:= by sorry`.
"""
import argparse
import concurrent.futures as futs
import glob
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests
from openai import OpenAI

sys.path.insert(0, "/tmp")
sys.path.insert(0, os.path.expanduser("~/SmolBench"))
# Reuse v7 primitives for extraction and premise-block emission.
from sb_kimina_ext_v7 import (
    _IDENT_RE, _BOUND_VAR_BLACKLIST, _NOTATION_MAP,
    _ATTR_RE, _MODIFIER_RE, _ADAPT_NOTE_RE, _DECL_HEAD_RE,
    _find_body_start, premise_block,
    extract_signature, strip_comments,
)
from deduction.inspect import BENCHMARK_DIR, load_corpus

MINIF2F_DIR = "/tmp/minif2f_test_solved/src"
SERVER_DEFAULT = "http://localhost:9000"
VLLM_DEFAULT = "http://localhost:8010/v1"
MODEL_DEFAULT = "AI-MO/Kimina-Prover-72B"
SYSTEM = ("You are an expert programmer and mathematician who helps "
          "formalizing mathematical problems in Lean 4.")
USER_PREFIX = ("Think about and solve the following problems step by "
               "step in Lean 4.\n\n")
_FENCE_RE = re.compile(r'```lean4?\s*\n(.*?)\n```', re.DOTALL)
_THEOREM_RE = re.compile(r'^\s*theorem\s+([A-Za-z0-9_\']+)', re.MULTILINE)


@dataclass
class MF2FProblem:
    name: str          # "mathd_algebra_304"
    file_path: str     # absolute path to .lean file
    file_text: str     # full file contents
    theorem_src: str   # "theorem foo (args) : type := body"
    theorem_line: int  # 1-indexed line where `theorem` starts
    opens: List[str]   # namespaces opened at file scope


def load_problems(dir_path: str = MINIF2F_DIR) -> List[MF2FProblem]:
    probs = []
    for path in sorted(glob.glob(os.path.join(dir_path, "*.lean"))):
        text = open(path).read()
        m = _THEOREM_RE.search(text)
        if m is None:
            continue
        name = m.group(1)
        # Find theorem start line (1-indexed)
        line = text[:m.start()].count("\n") + 1
        # The theorem source spans from the match to (a) the next top-level
        # declaration or (b) end of file. Simple heuristic: take everything
        # from the `theorem` start to end of file (miniF2F has one theorem
        # per file).
        thm_src = text[m.start():].rstrip()
        opens = []
        for ln in text.splitlines()[:line - 1]:
            s = ln.strip()
            if s.startswith("open scoped "):
                opens.extend(s[len("open scoped "):].split())
            elif s.startswith("open "):
                opens.extend(s[len("open "):].split())
        probs.append(MF2FProblem(
            name=name, file_path=path, file_text=text,
            theorem_src=thm_src, theorem_line=line, opens=opens,
        ))
    return probs


def mf2f_type_deps(prob: MF2FProblem, corpus) -> List[str]:
    """Like v7.extract_type_deps, but operates on a miniF2F problem
    (no MATHLIB_DIR relative path) and uses prob.opens directly."""
    sig = extract_signature(prob.theorem_src)
    m = _DECL_HEAD_RE.search(sig)
    if m:
        sig = sig[m.end():]

    hits: List[str] = []
    seen: set = set()

    def _add(name: str):
        if name in corpus and name not in seen:
            hits.append(name)
            seen.add(name)

    # 1. Textual identifiers in signature
    for n in _IDENT_RE.findall(sig):
        if n in _BOUND_VAR_BLACKLIST:
            continue
        _add(n)
        parts = n.split(".")
        for k in range(len(parts) - 1, 0, -1):
            _add(".".join(parts[:k]))

    # 2. Target name segments. miniF2F names don't have Mathlib namespaces
    # (they're `mathd_algebra_304`, `aime_1983_p1`), so this rarely hits.
    # Skip.

    # 3. Notation map
    for glyph, mathlib_name in _NOTATION_MAP.items():
        if glyph in sig:
            _add(mathlib_name)

    # 4. File-level opens
    for ns in prob.opens:
        _add(ns)

    return hits


def _replace_theorem_with_example_sorry(thm_src: str) -> str:
    """Rename the leading `theorem <name>` to `example` and replace the
    body with `:= by sorry`."""
    # Strip decorators first so the rename regex sees a clean head
    src = _ATTR_RE.sub("", thm_src)
    src = _MODIFIER_RE.sub("", src)
    src = _ADAPT_NOTE_RE.sub("", src)
    # Strip comments so doc strings don't leak; but keep the theorem body intact
    # (we'll overwrite it anyway).
    src = strip_comments(src)
    # Rename `theorem <name>` to `example`
    src = re.sub(r'^\s*theorem\s+[A-Za-z0-9_\']+', 'example', src, count=1,
                 flags=re.MULTILINE)
    # Replace body
    idx = _find_body_start(src)
    if idx == -1:
        return src.rstrip() + "\n"
    return src[:idx].rstrip() + " := by sorry\n"


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


def build_mf2f_file(prob: MF2FProblem, corpus, condition: str,
                    with_doc: bool = False, depth: int = 1,
                    server_url: Optional[str] = None,
                    stats: Optional[dict] = None) -> Tuple[str, int, int]:
    """Build the prompt file for a miniF2F problem under a given condition.
    Returns (file_text, n_kept, n_considered)."""
    helper_blocks = []
    n_considered = n_kept = 0
    if condition != "intensional":
        seen: set = set()
        frontier: List[str] = mf2f_type_deps(prob, corpus)
        cum: List[str] = []
        for _ in range(depth):
            next_frontier = []
            for name in frontier:
                if name in seen:
                    continue
                seen.add(name)
                cum.append(name)
                pp = corpus.get(name)
                if pp is None:
                    continue
                # Expand further via the corpus premise's own type-deps.
                from sb_kimina_ext_v7 import extract_type_deps as v7_deps
                next_frontier.extend(v7_deps(pp, corpus))
            frontier = next_frontier
            if not frontier:
                break
        for name in cum:
            pp = corpus.get(name)
            if pp is None:
                continue
            block = premise_block(pp, with_doc=with_doc)
            if not block:
                continue
            n_considered += 1
            if server_url is not None and not _block_parses(block, server_url):
                continue
            helper_blocks.append(block)
            n_kept += 1

    if stats is not None:
        stats[prob.name] = (n_kept, n_considered)

    opens_line = ""
    if prob.opens:
        opens_line = "open " + " ".join(prob.opens) + "\n"

    theorem_example = _replace_theorem_with_example_sorry(prob.theorem_src)
    return (
        "import Mathlib\nimport Aesop\n\nset_option maxHeartbeats 0\n\n"
        + "\n".join(helper_blocks)
        + "\n\n"
        + opens_line
        + "\n"
        + theorem_example
        + "\n",
        n_kept, n_considered,
    )


def extract_kimina_proof(text: str) -> str:
    blocks = _FENCE_RE.findall(text)
    valid = [b for b in blocks
             if all(k in b for k in ("by", ":=", "import"))
             and ("theorem" in b or "example" in b)]
    return valid[-1] if valid else ""


def generate(client, model, user_msg, max_tokens=14000, temperature=0.1):
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


def process(prob, corpus, condition, with_doc, depth, client, model,
            server_url, k, log_path):
    stats: dict = {}
    code, kept, considered = build_mf2f_file(
        prob, corpus, condition, with_doc=with_doc, depth=depth,
        server_url=server_url, stats=stats,
    )
    user_msg = USER_PREFIX + code
    attempts, any_pass = [], False
    for i in range(k):
        t0 = time.perf_counter()
        try:
            raw, tok = generate(client, model, user_msg)
        except Exception as e:
            attempts.append({"k": i, "error": f"gen:{str(e)[:80]}"}); continue
        proof = extract_kimina_proof(raw)
        if not proof:
            attempts.append({"k": i, "extract_failed": True, "tokens_out": tok})
            continue
        try:
            ok, errs = verify(server_url, proof)
        except Exception as e:
            attempts.append({"k": i, "error": f"ver:{str(e)[:80]}"}); continue
        attempts.append({
            "k": i, "ok": ok, "tokens_out": tok,
            "first_err": (str(errs[0].get("data"))[:200] if errs else None),
            "wall_ms": int((time.perf_counter() - t0) * 1000),
        })
        if ok:
            any_pass = True
            break
    rec = {
        "target": prob.name, "condition": condition, "k_tried": len(attempts),
        "pass": any_pass, "attempts": attempts, "file_chars": len(code),
        "premises_kept": kept, "premises_considered": considered,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return prob.name, any_pass, len(attempts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--n", type=int, default=0,
                    help="Limit to first N problems (0 = all)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--vllm-url", default=VLLM_DEFAULT)
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    cond = args.condition
    with_doc = False
    depth = 1
    if cond == "intensional":
        pass
    elif cond.startswith("ext-nodoc-d"):
        depth = int(cond.split("-d")[-1])
    elif cond.startswith("ext-doc-d"):
        with_doc = True
        depth = int(cond.split("-d")[-1])
    else:
        sys.exit(f"bad condition: {cond}")

    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    problems = load_problems()
    if args.n > 0:
        problems = problems[:args.n]
    print(f"condition={cond}  pool={len(problems)}  k={args.k}  "
          f"workers={args.workers}")
    print(f"log={args.log}")
    open(args.log, "w").close()
    client = OpenAI(base_url=args.vllm_url, api_key="EMPTY")

    t0 = time.time()
    passed = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {ex.submit(process, p, corpus, cond, with_doc, depth,
                        client, args.model, args.server_url, args.k,
                        args.log): p
              for p in problems}
        for fut in futs.as_completed(fm):
            name, ok, kt = fut.result()
            done = sum(1 for f in fm if f.done())
            n = len(problems)
            tag = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            print(f"  [{done:3d}/{n}] {tag}  {name[:55]:55s}  k={kt}  "
                  f"(running {passed}/{done})", flush=True)

    print(f"\n{cond}  Done in {(time.time()-t0)/60:.1f} min.  "
          f"pass@{args.k}: {passed}/{len(problems)} = "
          f"{100*passed/max(len(problems),1):.1f}%")


if __name__ == "__main__":
    main()
