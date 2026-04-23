"""SmolBench × Kimina extensional-conditions pilot.

For each target, build multiple file variants and run Kimina on each:
  - intensional (i): bare target, no helpers.
  - ext-nodoc-dN: target + renamed premise helpers at BFS depth N, comments stripped.
  - ext-doc-dN:   same but docstrings preserved.

Renaming strategy: replace each premise's `theorem|lemma <dotted.name>` with
`theorem|lemma sb_<underscored_name>` so the helpers compile alongside the
original Mathlib declarations without collision. References to OTHER premises
inside a body (e.g. `apply Rel.inv_def`) still resolve via Mathlib, which is
fine — same fact, just a different import path.

Uses the same vLLM + kimina-lean-server setup as the intensional runs.
"""
import argparse
import concurrent.futures as futs
import json
import os
import re
import sys
import time
import requests
from openai import OpenAI

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import (
    BENCHMARK_DIR, MATHLIB_DIR, load_corpus, load_traced_lookup,
    source_text, strip_comments as _base_strip, expand_by_layer, premise_refs,
)


# Mathlib files sometimes contain `#adaptation_note /-- ... -/` — a command
# that REQUIRES a following doc comment. Our comment stripper removes the
# doc, leaving a dangling `#adaptation_note` which errors. Drop both.
_ADAPT_NOTE_RE = re.compile(r'#adaptation_note\s*/-[-!]?[\s\S]*?-/|#adaptation_note\s*$',
                            re.MULTILINE)


def strip_comments(text: str) -> str:
    # Remove adaptation_note FIRST (while its doc is still present),
    # then run the base stripper.
    text = _ADAPT_NOTE_RE.sub("", text)
    return _base_strip(text)
from deduction.pool_runner import pilot_pool

SYSTEM = "You are an expert programmer and mathematician who helps formalizing mathematical problems in Lean 4."
USER_PREFIX = "Think about and solve the following problems step by step in Lean 4.\n\n"

# Target line: rename `theorem|lemma <anything>` to `example`.
_TARGET_RENAME_RE = re.compile(
    r'^(\s*)(?:@\[[^\]]*\]\s*)?(?:theorem|lemma)\s+\S+', re.MULTILINE,
)

# Premise rename: `theorem|lemma Foo.Bar.baz` → `theorem|lemma sb_Foo_Bar_baz`
# Anchored at line start (possibly after attributes) so we don't rename
# identifier uses inside bodies.
_PREMISE_DECL_RE = re.compile(
    r'^(\s*)((?:@\[[^\]]*\]\s*)?)(theorem|lemma|def|abbrev)\s+(\S+)',
    re.MULTILINE,
)

_FENCE_RE = re.compile(r'```lean4?\s*\n(.*?)\n```', re.DOTALL)
_CTX_PREFIXES = ("namespace ", "section ", "end ", "end\n", "variable ", "variable{",
                 "variable(", "variable[", "open ", "open scoped ",
                 "universe ", "universes ")


def _sanitize(dotted: str) -> str:
    """Convert a dotted Mathlib name to a flat, unique `sb_`-prefixed one."""
    return "sb_" + re.sub(r'\W', '_', dotted)


def rename_premise_decls(src: str) -> str:
    """Rename all top-level theorem/lemma/def/abbrev in `src` to `sb_*`.
    Preserves attributes and indentation."""
    def _sub(m):
        indent, attrs, kind, name = m.group(1), m.group(2), m.group(3), m.group(4)
        new_name = _sanitize(name)
        return f"{indent}{attrs}{kind} {new_name}"
    return _PREMISE_DECL_RE.sub(_sub, src)


def _replace_body_with_sorry(decl: str) -> str:
    """Find first top-level `:=` (outside `[...]`), replace from there with
    ` := by sorry`."""
    depth = 0
    i = 0
    while i < len(decl) - 1:
        c = decl[i]
        if c == "[": depth += 1
        elif c == "]": depth -= 1
        elif depth == 0 and c == ":" and decl[i + 1] == "=":
            return decl[:i].rstrip() + " := by sorry\n"
        i += 1
    return decl.rstrip() + "\n"


def collect_context(file_text: str, theorem_line_zero_indexed: int) -> str:
    """Preceding namespace/variable/open/section lines from the file."""
    ctx = []
    for i, l in enumerate(file_text.splitlines()):
        if i >= theorem_line_zero_indexed: break
        if l.strip().startswith(_CTX_PREFIXES):
            ctx.append(l)
    return "\n".join(ctx)


def build_target_decl(premise) -> str:
    """Target-as-`example` with body → sorry. Reads the full Mathlib source."""
    src = source_text(premise)
    if src is None: return ""
    decl = _TARGET_RENAME_RE.sub(r"\1example", src, count=1)
    return _replace_body_with_sorry(decl)


def build_file_for_condition(
    target_full_name, corpus, traced_lookup, condition, with_doc=False, depth=1,
):
    """Return the Kimina-style Lean file for this (target, condition).
    condition ∈ {'intensional', 'ext-nodoc-d1..d4', 'ext-doc-d1..d4'}."""
    p = corpus.get(target_full_name)
    if p is None: return None
    src_path = MATHLIB_DIR / p.file_path
    if not src_path.exists(): return None
    file_text = src_path.read_text()
    ctx = collect_context(file_text, p.start[0] - 1)
    target_decl = build_target_decl(p)

    if condition == "intensional":
        helpers = ""
    else:
        # BFS premise expansion to the requested depth.
        direct = premise_refs(traced_lookup.get(target_full_name, []))
        layers = expand_by_layer(direct, traced_lookup, depth)
        cum = []
        for l in layers:
            cum.extend(l)
        parts = []
        for name in cum:
            pp = corpus.get(name)
            if pp is None: continue
            pp_src = source_text(pp)
            if pp_src is None:
                pp_src = pp.corpus_code
            if not with_doc:
                pp_src = strip_comments(pp_src)
            parts.append(rename_premise_decls(pp_src))
        helpers = "\n\n".join(parts)

    return f"import Mathlib\n\n{ctx}\n\n{helpers}\n\n{target_decl}\n"


def extract_kimina_proof(text: str) -> str:
    blocks = _FENCE_RE.findall(text)
    valid = [b for b in blocks if all(k in b for k in ("by", ":=", "import"))
             and ("theorem" in b or "example" in b)]
    return valid[-1] if valid else ""


def generate(client, model, user_msg, max_tokens=14000, temperature=0.1):
    r = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_msg},
        ],
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
    data = r.json()
    resp = data["results"][0].get("response", {})
    errs = [m for m in resp.get("messages", []) if m.get("severity") == "error"]
    return len(errs) == 0, errs


def process(target, corpus, traced_lookup, condition, with_doc, depth,
            client, model, server_url, k, log_path):
    fn = target["full_name"]
    code = build_file_for_condition(fn, corpus, traced_lookup, condition,
                                    with_doc=with_doc, depth=depth)
    if code is None:
        rec = {"target": fn, "condition": condition, "skip": "build_failed", "pass": False}
        with open(log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        return fn, False, 0, "build"

    base_ok, base_errs = verify(server_url, code)
    if not base_ok:
        err_sample = str(base_errs[0].get("data"))[:150] if base_errs else ""
        rec = {"target": fn, "condition": condition, "skip": "base_unparseable",
               "base_err": err_sample, "pass": False}
        with open(log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        return fn, False, 0, f"base:{err_sample[:50]}"

    user_msg = USER_PREFIX + code
    attempts = []
    any_pass = False
    for i in range(k):
        t0 = time.perf_counter()
        try:
            raw, tokens_out = generate(client, model, user_msg)
        except Exception as e:
            attempts.append({"k": i, "error": f"gen:{str(e)[:80]}"})
            continue
        proof = extract_kimina_proof(raw)
        if not proof:
            attempts.append({"k": i, "extract_failed": True, "tokens_out": tokens_out})
            continue
        try:
            ok, errs = verify(server_url, proof)
        except Exception as e:
            attempts.append({"k": i, "error": f"ver:{str(e)[:80]}"})
            continue
        attempts.append({
            "k": i, "ok": ok, "tokens_out": tokens_out,
            "first_err": (str(errs[0].get("data"))[:200] if errs else None),
            "wall_ms": int((time.perf_counter() - t0) * 1000),
        })
        if ok:
            any_pass = True
            break

    rec = {"target": fn, "condition": condition, "k_tried": len(attempts),
           "pass": any_pass, "attempts": attempts,
           "file_chars": len(code)}
    with open(log_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return fn, any_pass, len(attempts), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True,
                    help="intensional | ext-nodoc-d1..d4 | ext-doc-d1..d4")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--n-targets", type=int, default=73)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--vllm-url", default="http://localhost:8010/v1")
    ap.add_argument("--server-url", default="http://localhost:9000")
    ap.add_argument("--model", default="AI-MO/Kimina-Prover-72B")
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    # Parse condition
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
    traced = load_traced_lookup()
    targets = pilot_pool(corpus, traced, max_n=args.n_targets)
    print(f"condition={cond}  pool={len(targets)}  k={args.k}  workers={args.workers}")
    print(f"log={args.log}")
    open(args.log, "w").close()
    client = OpenAI(base_url=args.vllm_url, api_key="EMPTY")

    t0 = time.time()
    passed = skipped = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {ex.submit(process, t, corpus, traced, cond, with_doc, depth,
                        client, args.model, args.server_url, args.k, args.log): t
              for t in targets}
        for fut in futs.as_completed(fm):
            fn, ok, kt, err = fut.result()
            done = sum(1 for f in fm if f.done())
            n = len(targets)
            if err:
                skipped += 1
                tag = "SKIP"
                extra = err[:40]
            elif ok:
                passed += 1
                tag = "PASS"
                extra = f"k={kt}"
            else:
                tag = "FAIL"
                extra = f"k={kt}"
            print(f"  [{done:2d}/{n}] {tag}  {fn[:55]:55s}  {extra}  "
                  f"(running {passed}/{done-skipped}, skipped {skipped})", flush=True)

    print(f"\n{cond}  Done in {(time.time()-t0)/60:.1f} min.  "
          f"pass@{args.k}: {passed}/{len(targets)-skipped} attempted "
          f"= {100*passed/max(len(targets)-skipped,1):.1f}%   "
          f"({skipped} skipped)")


if __name__ == "__main__":
    main()
