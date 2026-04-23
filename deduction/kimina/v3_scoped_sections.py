"""v3 builder: each premise is wrapped in its OWN `section` with its OWN file's
variable/open bindings, preserving implicit args. Emitted at module scope with
a renamed identifier so there's no collision with Mathlib:

    section
    <premise file's variable/open/universe decls>
    theorem sb_<name> <original binders> : <type> := <body>
    end

This restores every file-level `variable [TypeClass α]` and `open NS` the
premise depended on, without leaking those bindings into the rest of the file.
After `end`, `sb_<name>` is callable at top level (or inside the target's
enclosing namespace).

Inside the target proof we use `import Mathlib`; the target's file-level
context stays as-is.
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
from deduction.pool_runner import pilot_pool

SYSTEM = "You are an expert programmer and mathematician who helps formalizing mathematical problems in Lean 4."
USER_PREFIX = "Think about and solve the following problems step by step in Lean 4.\n\n"

_TARGET_RENAME_RE = re.compile(
    r'^(\s*)(?:@\[[^\]]*\]\s*)?(?:theorem|lemma)\s+\S+', re.MULTILINE,
)
_FENCE_RE = re.compile(r'```lean4?\s*\n(.*?)\n```', re.DOTALL)

# File-level scope directives we want to carry.
_CTX_PREFIXES = ("namespace ", "section ", "end ", "end\n", "variable ", "variable{",
                 "variable(", "variable[", "open ", "open scoped ",
                 "universe ", "universes ")

_ADAPT_NOTE_RE = re.compile(r'#adaptation_note\s*/-[-!]?[\s\S]*?-/|#adaptation_note\s*$',
                            re.MULTILINE)
_ATTR_RE = re.compile(r'@\[[^\]]*\]\s*', re.MULTILINE)
_MODIFIER_RE = re.compile(
    r'^(?:\s*(?:noncomputable|private|protected|scoped|partial|mutual|unsafe)\s+)+',
    re.MULTILINE,
)
_DECL_HEAD_RE = re.compile(
    r'\b(theorem|lemma|def|abbrev|instance|structure|class)\s+(\S+)'
)


def strip_comments(text: str) -> str:
    return _base_strip(_ADAPT_NOTE_RE.sub("", text))


def _sanitize(dotted: str) -> str:
    return "sb_" + re.sub(r'\W', '_', dotted)


def _replace_body_with_sorry(decl: str) -> str:
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
    """Pull scope directives from the top of the file up to `theorem_line`."""
    ctx = []
    for i, l in enumerate(file_text.splitlines()):
        if i >= theorem_line_zero_indexed: break
        if l.strip().startswith(_CTX_PREFIXES):
            ctx.append(l)
    return "\n".join(ctx)


def _collect_namespace_chain(ctx_lines: list[str]) -> str:
    """Given the file-level ctx lines, return a minimal `open` string that
    brings the namespaces the premise was declared in into scope — enough for
    notation and relative-name resolution."""
    namespaces = []
    for l in ctx_lines:
        s = l.strip()
        if s.startswith("namespace "):
            namespaces.append(s[len("namespace "):].strip())
    return " ".join(namespaces)


def premise_section(premise, with_doc: bool = False) -> str | None:
    """Return a `section ... end` block that declares a renamed copy of the
    premise with the file-level bindings it needs. Returns None on unhandled
    kinds (instance/structure/class)."""
    src = source_text(premise)
    if src is None: return None
    src_path = MATHLIB_DIR / premise.file_path
    if not src_path.exists(): return None
    file_text = src_path.read_text()
    file_ctx = collect_context(file_text, premise.start[0] - 1).splitlines()

    # Keep only `variable`, `open`, `universe` lines for this scoped section
    # — NOT `namespace` / `end` / `section`, since those create nesting that
    # can conflict between premises. Instead, bring namespace names in via
    # `open` so notation and unqualified names resolve.
    scoped_ctx = []
    seen_ns = set()
    for l in file_ctx:
        s = l.strip()
        if s.startswith(("variable ", "variable{", "variable(", "variable[",
                          "open ", "open scoped ", "universe ", "universes ")):
            scoped_ctx.append(l)
        elif s.startswith("namespace "):
            name = s[len("namespace "):].strip()
            if name not in seen_ns:
                scoped_ctx.append(f"open {name}")
                seen_ns.add(name)

    # Clean + rename the declaration
    src = _ATTR_RE.sub("", src)
    src = _MODIFIER_RE.sub("", src)
    src = _ADAPT_NOTE_RE.sub("", src)
    if not with_doc:
        src = strip_comments(src)
    # Downgrade doc strings so they don't require attaching to a named decl
    src = re.sub(r'/--', '/-', src)
    m = _DECL_HEAD_RE.search(src)
    if not m: return None
    kind, name = m.group(1), m.group(2)
    if kind not in ("theorem", "lemma", "def", "abbrev"):
        return None
    sanitized = _sanitize(name)
    renamed = src.replace(f"{kind} {name}", f"{kind} {sanitized}", 1)

    ctx_block = "\n".join(scoped_ctx)
    return f"section\n{ctx_block}\n{renamed}\nend\n"


def build_target_example(premise) -> str:
    src = source_text(premise)
    if src is None: return ""
    decl = _TARGET_RENAME_RE.sub(r"\1example", src, count=1)
    return _replace_body_with_sorry(decl)


def build_file(target_full_name, corpus, traced_lookup, condition,
               with_doc=False, depth=1):
    p = corpus.get(target_full_name)
    if p is None: return None
    src_path = MATHLIB_DIR / p.file_path
    if not src_path.exists(): return None
    file_text = src_path.read_text()
    target_ctx = collect_context(file_text, p.start[0] - 1)
    target_example = build_target_example(p)

    helper_blocks = []
    if condition != "intensional":
        direct = premise_refs(traced_lookup.get(target_full_name, []))
        layers = expand_by_layer(direct, traced_lookup, depth)
        cum = []
        for l in layers:
            cum.extend(l)
        for name in cum:
            pp = corpus.get(name)
            if pp is None: continue
            section = premise_section(pp, with_doc=with_doc)
            if section:
                helper_blocks.append(section)

    return (
        "import Mathlib\n\n"
        + target_ctx + "\n\n"
        + "\n".join(helper_blocks) + "\n"
        + target_example + "\n"
    )


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
    code = build_file(fn, corpus, traced_lookup, condition,
                      with_doc=with_doc, depth=depth)
    if code is None:
        rec = {"target": fn, "condition": condition, "skip": "build_failed", "pass": False}
        with open(log_path, "a") as f: f.write(json.dumps(rec) + "\n")
        return fn, False, 0, "build"
    # Don't gate on base parseability; just feed Kimina and verify its output.
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
            attempts.append({"k": i, "extract_failed": True, "tokens_out": tok}); continue
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
    rec = {"target": fn, "condition": condition, "k_tried": len(attempts),
           "pass": any_pass, "attempts": attempts, "file_chars": len(code)}
    with open(log_path, "a") as f: f.write(json.dumps(rec) + "\n")
    return fn, any_pass, len(attempts), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--n-targets", type=int, default=73)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--vllm-url", default="http://localhost:8010/v1")
    ap.add_argument("--server-url", default="http://localhost:9000")
    ap.add_argument("--model", default="AI-MO/Kimina-Prover-72B")
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
                skipped += 1; tag = "SKIP"; extra = err[:40]
            elif ok:
                passed += 1; tag = "PASS"; extra = f"k={kt}"
            else:
                tag = "FAIL"; extra = f"k={kt}"
            print(f"  [{done:2d}/{n}] {tag}  {fn[:55]:55s}  {extra}  "
                  f"(running {passed}/{done-skipped}, skipped {skipped})",
                  flush=True)

    print(f"\n{cond}  Done in {(time.time()-t0)/60:.1f} min.  "
          f"pass@{args.k}: {passed}/{len(targets)-skipped} attempted "
          f"= {100*passed/max(len(targets)-skipped,1):.1f}%   "
          f"({skipped} skipped)")


if __name__ == "__main__":
    main()
