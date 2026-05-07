"""miniF2F driver using v9: chained `abbrev` helpers.

Difference from v8:
  - v8 inlines each name's body directly into the theorem signature
    (verbose, repetitive when names appear multiple times, breaks
    parseability when bodies contain elided subterms).
  - v9 emits each name's body as a top-level `abbrev sb_X := <body>`
    and rewrites the theorem to use `sb_X`. Each `sb_X`'s body uses
    `sb_Y` for sub-terms ONE LEVEL deeper, so depth d gives a chain
    of d named abbreviations terminating at original Mathlib names.

Structure at depth d for name `Foo` referenced in theorem:
  abbrev sb_Bar := <body of Bar (deepest), original Mathlib names>
  abbrev sb_Foo := <body of Foo, with sub-name `Bar` rewritten to `sb_Bar`>
  example (... : sb_Foo ...) := by sorry

`abbrev` is definitionally transparent — Lean unfolds `sb_Foo` to `Foo`
during elaboration, so Mathlib lemmas about `Foo` still apply via
defeq. The theorem stays solvable; the model must engage with the
abbreviations to understand what's being asked.

Notes:
  - We expand all kinds with a `:=` body (def, abbrev, theorem, lemma,
    instance). For `structure` / `class` / `inductive` (no `:=` body),
    we emit `abbrev sb_Foo := Foo` as a pure alias — informational
    but content-free. Skip if alias is the only thing.
  - Topological order: deepest level emitted first.
  - Skip Lean core names (Nat, Eq, dite, etc.) — only expand corpus
    entries.
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
from typing import List, Optional, Tuple

import requests
from openai import OpenAI

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import BENCHMARK_DIR, load_corpus
from deduction.kimina.lean_query import print_decl, extract_def_body

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
_NAME_RE = re.compile(
    r'[A-Za-z_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]'
    r'[a-zA-Z0-9_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]*'
    r'(?:\.[A-Za-z0-9_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]+)*'
)


def _sb(name: str) -> str:
    """Sanitize Mathlib full name to a valid Lean identifier."""
    return "sb_" + re.sub(r'\W', '_', name)


def _names_in(text: str, corpus) -> List[str]:
    """Return distinct corpus-resolvable names in `text`, in order. Tries
    longest-dotted match first, then progressively trims (to capture
    `Set.image.foo` → `Set.image` → `Set`)."""
    seen: set = set()
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


def _substitute_name(text: str, name: str, replacement: str) -> str:
    """Replace whole-word occurrences of `name` with `replacement`. Avoids
    matching when `name` is a prefix/suffix of a longer dotted name."""
    pat = re.compile(
        r'(?<![A-Za-z0-9_.])' + re.escape(name) + r'(?![A-Za-z0-9_.])'
    )
    return pat.sub(replacement, text)


@dataclass
class MF2FProblem:
    name: str
    file_path: str
    theorem_src: str
    sig_text: str
    theorem_line: int
    opens: List[str]


def _split_signature(thm_src: str) -> str:
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
    return head.strip()


def load_problems(dir_path: str = MINIF2F_DIR) -> List[MF2FProblem]:
    probs = []
    for path in sorted(glob.glob(os.path.join(dir_path, "*.lean"))):
        text = open(path).read()
        m = _THEOREM_RE.search(text)
        if m is None: continue
        name = m.group(1)
        line = text[:m.start()].count("\n") + 1
        thm_src = text[m.start():].rstrip()
        sig_text = _split_signature(thm_src)
        opens = []
        for ln in text.splitlines()[:line - 1]:
            s = ln.strip()
            if s.startswith("open scoped "):
                opens.extend(s[len("open scoped "):].split())
            elif s.startswith("open "):
                opens.extend(s[len("open "):].split())
        probs.append(MF2FProblem(
            name=name, file_path=path,
            theorem_src=thm_src, sig_text=sig_text,
            theorem_line=line, opens=opens,
        ))
    return probs


def _abbrev_parses(abbrev_block: str, server_url: str,
                   timeout: int = 60) -> bool:
    """Verify a single `noncomputable abbrev sb_X := <body>` block parses
    standalone (against `import Mathlib` only). Used to decide whether
    to keep the abbrev in the chain or fall back to the original name."""
    synthetic = ("import Mathlib\n\n" + abbrev_block + "\n"
                 "example : True := trivial\n")
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


def build_chain(theorem_sig: str, corpus, depth: int,
                server_url: str) -> Tuple[List[str], str]:
    """Build the helper-abbrev chain for the theorem signature.

    Returns (abbrev_blocks, rewritten_sig). Each abbrev is verified
    standalone — if it doesn't parse, we keep the original Mathlib
    name in any parent body that referenced it (and don't emit it).
    """
    if depth <= 0:
        return [], theorem_sig

    levels: List[List[str]] = []
    seen: set = set()
    bodies: dict = {}

    level0 = _names_in(theorem_sig, corpus)
    seen.update(level0)
    levels.append(level0)

    for k in range(1, depth):
        next_level = []
        for name in levels[-1]:
            if name not in bodies:
                bodies[name] = extract_def_body(print_decl(name, server_url))
            body = bodies[name]
            if body is None: continue
            for n in _names_in(body, corpus):
                if n not in seen:
                    seen.add(n)
                    next_level.append(n)
        if not next_level: break
        levels.append(next_level)

    for name in levels[-1]:
        if name not in bodies:
            bodies[name] = extract_def_body(print_decl(name, server_url))

    sb_map = {n: _sb(n)
              for level in levels for n in level if bodies.get(n)}

    # Walk deepest → shallowest, verifying each abbrev. If it fails,
    # remove it from sb_map so parent bodies keep the original name.
    blocks: List[str] = []
    for k in range(len(levels) - 1, -1, -1):
        for name in levels[k]:
            body = bodies.get(name)
            if body is None: continue
            if name not in sb_map: continue
            # Substitute names that are still in sb_map (deeper levels
            # we kept) with their sb_* form
            current = body
            for deeper_name in [n for j in range(k + 1, len(levels))
                                  for n in levels[j] if n in sb_map]:
                current = _substitute_name(current, deeper_name, sb_map[deeper_name])
            current = current.replace("⋯", "sorry")
            block = f"noncomputable abbrev {sb_map[name]} := {current}"
            if _abbrev_parses(block, server_url):
                blocks.append(block)
            else:
                # Drop this abbrev — keep the original Mathlib name
                # everywhere else.
                del sb_map[name]

    # Rewrite theorem signature: only substitute names that survived.
    rewritten = theorem_sig
    for name in levels[0]:
        if name in sb_map:
            rewritten = _substitute_name(rewritten, name, sb_map[name])

    return blocks, rewritten


def build_mf2f_v9_file(prob: MF2FProblem, corpus, condition: str,
                       depth: int = 1,
                       server_url: str = SERVER_DEFAULT) -> str:
    if condition == "intensional":
        blocks, sig = [], prob.sig_text
    else:
        blocks, sig = build_chain(prob.sig_text, corpus, depth, server_url)

    opens_line = ""
    if prob.opens:
        opens_line = "open " + " ".join(prob.opens) + "\n"

    helpers = ("\n\n".join(blocks) + "\n\n") if blocks else ""

    return (
        "import Mathlib\nimport Aesop\n\nset_option maxHeartbeats 0\n\n"
        + opens_line
        + "\n"
        + helpers
        + f"example {sig} := by sorry\n"
    )


def extract_kimina_proof(text: str) -> str:
    blocks = _FENCE_RE.findall(text)
    valid = [
        b for b in blocks
        if all(k in b for k in ("by", ":=", "import"))
        and ("theorem" in b or "example" in b)
    ]
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


def process(prob, corpus, condition, depth, client, model, server_url,
            k, log_path):
    code = build_mf2f_v9_file(prob, corpus, condition, depth=depth,
                              server_url=server_url)
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
    rec = {
        "target": prob.name, "condition": condition, "k_tried": len(attempts),
        "pass": any_pass, "attempts": attempts, "file_chars": len(code),
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return prob.name, any_pass, len(attempts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--vllm-url", default=VLLM_DEFAULT)
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--model", default=MODEL_DEFAULT)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    cond = args.condition
    if cond == "intensional":
        depth = 0
    elif cond.startswith("ext-nodoc-d"):
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
        fm = {ex.submit(process, p, corpus, cond, depth,
                        client, args.model, args.server_url, args.k,
                        args.log): p
              for p in problems}
        for fut in futs.as_completed(fm):
            name, ok, kt = fut.result()
            done = sum(1 for f in fm if f.done())
            n = len(problems)
            tag = "PASS" if ok else "FAIL"
            if ok: passed += 1
            print(f"  [{done:3d}/{n}] {tag}  {name[:55]:55s}  k={kt}  "
                  f"(running {passed}/{done})", flush=True)

    print(f"\n{cond}  Done in {(time.time()-t0)/60:.1f} min.  "
          f"pass@{args.k}: {passed}/{len(problems)} = "
          f"{100*passed/max(len(problems),1):.1f}%")


if __name__ == "__main__":
    main()
