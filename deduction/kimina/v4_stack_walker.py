"""v4 builder: stack-aware premise scope reconstruction.

For each premise, walk its source file top-to-bottom keeping a stack of
`namespace` / `section` frames. At each frame we accumulate only the
`variable` / `universe` / `open` lines declared in THAT frame. When a frame
closes (`end` [name]), we pop. When we reach the premise's line, the stack
represents exactly the scopes the premise was declared under, and the
`open`s / `universe`s / `variable`s on each frame are exactly those in
effect there.

We then emit:

    section                               -- outer wrapper per premise
    <module-frame universes/opens/vars>   -- from the file's module scope
    namespace NS1
    <NS1 frame universes/opens/vars>
      section S1
      <S1 frame ...>
        ... (deeper)
          theorem sb_<name> <binders> : <type> := <body>
        end [deeper]
      end S1
    end NS1
    end

Each premise lives inside its own outer wrapper section, so module-scope
`universe u` / `variable`s from the premise's file do NOT leak into
subsequent premises or the target.
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


class Frame:
    __slots__ = ("kind", "name", "lines")

    def __init__(self, kind, name):
        self.kind = kind  # "module" | "namespace" | "section"
        self.name = name
        self.lines = []  # scope-local variable/universe/open lines


def walk_scopes(file_text: str, target_line_zero_indexed: int) -> list[Frame]:
    """Walk file up to target_line and return the stack of active frames
    (module-first). Each frame carries the variable/universe/open lines
    declared in that frame."""
    module = Frame("module", "")
    stack = [module]
    for i, line in enumerate(file_text.splitlines()):
        if i >= target_line_zero_indexed:
            break
        s = line.strip()
        if not s:
            continue
        if s.startswith("namespace "):
            name = s[len("namespace "):].split("--", 1)[0].strip()
            stack.append(Frame("namespace", name))
        elif s == "section" or s.startswith("section "):
            name = s[len("section"):].split("--", 1)[0].strip()
            stack.append(Frame("section", name))
        elif s == "end" or s.startswith("end "):
            # Pop the most-recent section/namespace frame
            if len(stack) > 1:
                stack.pop()
        elif s.startswith(("variable ", "variable{", "variable(", "variable[",
                            "open ", "open scoped ", "universe ", "universes ")):
            stack[-1].lines.append(line)
    return stack


def premise_block(premise, with_doc: bool = False) -> str | None:
    """Return a top-level `section ... end` block containing the premise
    under exactly its file's active scopes, with the declaration renamed."""
    src = source_text(premise)
    if src is None: return None
    src_path = MATHLIB_DIR / premise.file_path
    if not src_path.exists(): return None
    file_text = src_path.read_text()
    frames = walk_scopes(file_text, premise.start[0] - 1)

    # Clean + rename the declaration
    src = _ATTR_RE.sub("", src)
    src = _MODIFIER_RE.sub("", src)
    src = _ADAPT_NOTE_RE.sub("", src)
    if not with_doc:
        src = strip_comments(src)
    # Downgrade doc strings; without a named decl to attach to they're errors.
    src = re.sub(r'/--', '/-', src)
    m = _DECL_HEAD_RE.search(src)
    if not m: return None
    kind, name = m.group(1), m.group(2)
    if kind not in ("theorem", "lemma", "def", "abbrev"):
        return None
    sanitized = _sanitize(name)
    renamed = src.replace(f"{kind} {name}", f"{kind} {sanitized}", 1)

    # Emit: outer section, then for each frame (module first): its lines,
    # then `namespace/section` openers (nested), then the renamed decl,
    # then matching closers, then outer `end`.
    out = ["section"]

    # Module frame's lines first (universes/opens/vars at file top-level).
    out.extend(frames[0].lines)

    # Then nested frames (namespace/section) with their local lines.
    for fr in frames[1:]:
        if fr.kind == "namespace":
            out.append(f"namespace {fr.name}")
        else:
            out.append("section" + (f" {fr.name}" if fr.name else ""))
        out.extend(fr.lines)

    out.append(renamed.rstrip())

    # Close all nested frames in reverse.
    for fr in reversed(frames[1:]):
        if fr.kind == "namespace":
            out.append(f"end {fr.name}")
        else:
            out.append("end" + (f" {fr.name}" if fr.name else ""))

    out.append("end")  # close outer wrapper
    return "\n".join(out) + "\n"


def build_target_example(premise) -> str:
    src = source_text(premise)
    if src is None: return ""
    decl = _TARGET_RENAME_RE.sub(r"\1example", src, count=1)
    return _replace_body_with_sorry(decl)


def collect_target_ctx(file_text: str, target_line_zero_indexed: int) -> str:
    """For the TARGET declaration we want the reader to actually see the
    example with its file's scope. Emit the active frames as an opening
    stanza (no closers; the example comes at the end of the file)."""
    frames = walk_scopes(file_text, target_line_zero_indexed)
    out = list(frames[0].lines)
    for fr in frames[1:]:
        if fr.kind == "namespace":
            out.append(f"namespace {fr.name}")
        else:
            out.append("section" + (f" {fr.name}" if fr.name else ""))
        out.extend(fr.lines)
    return "\n".join(out)


def build_file(target_full_name, corpus, traced_lookup, condition,
               with_doc=False, depth=1):
    p = corpus.get(target_full_name)
    if p is None: return None
    src_path = MATHLIB_DIR / p.file_path
    if not src_path.exists(): return None
    file_text = src_path.read_text()
    target_ctx = collect_target_ctx(file_text, p.start[0] - 1)
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
            block = premise_block(pp, with_doc=with_doc)
            if block:
                helper_blocks.append(block)

    return (
        "import Mathlib\n\n"
        + "\n".join(helper_blocks)
        + "\n\n"
        + target_ctx + "\n\n"
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
