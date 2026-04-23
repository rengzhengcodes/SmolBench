"""v8 builder: Lean-elaborator-driven unfolding of the target signature.

Goal: define the problem itself in terms of unfolded Lean, not just
pad the prompt with helper definitions that the target can ignore.

Approach:
  1. Ask Lean for the target's full signature (`#check @<name>`) with
     notation off and full names on. This gives the type with all
     unqualified/notation refs resolved to Mathlib corpus names.
  2. Find Mathlib corpus names in that signature.
  3. For each such name at depth <= d, ask Lean for its `#print` output
     and substitute the definition body into the signature text (with
     parentheses around the substitution).
  4. At each deeper level, the newly-introduced names are themselves
     unfolded. Recurse until depth `d` or no further Mathlib names.

Caveats:
  - Some substitutions break instance/lemma resolution because typeclass
    resolution on `def`-backed types (semi-reducible) doesn't see through
    the unfolded form the way it sees through the original named type.
    Expect pass rate to drop at higher `d` for reasons beyond pure
    density; this is the "compound effect" the experiment measures.
  - `structure`/`class`/`inductive` have no `:=` body; we fall back to
    leaving the original name in place for those. An empirical question
    is how many deps this affects.
  - Quality of the unfolded text depends on Lean's pretty printer and
    the pp options we set. We use notation=false, fullNames=true so the
    output is deterministic text we can re-substitute.
"""
from __future__ import annotations

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
from deduction.inspect import BENCHMARK_DIR, load_corpus, load_traced_lookup
from deduction.kimina.lean_query import (
    check_type, extract_def_body, print_decl,
)
from deduction.pool_runner import pilot_pool

SYSTEM = (
    "You are an expert programmer and mathematician who helps "
    "formalizing mathematical problems in Lean 4."
)
USER_PREFIX = (
    "Think about and solve the following problems step by step in Lean 4.\n\n"
)

_FENCE_RE = re.compile(r'```lean4?\s*\n(.*?)\n```', re.DOTALL)

# A Lean identifier: ASCII + common math Unicode. Dotted or single.
_NAME_RE = re.compile(
    r'[A-Za-z_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]'
    r'[a-zA-Z0-9_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]*'
    r'(?:\.[A-Za-z0-9_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]+)*'
)


def _names_in(text: str, corpus) -> list[str]:
    """Return distinct corpus-resolvable names appearing in text, in order
    of first occurrence. We try the longest-dotted match first, then
    progressively trim."""
    seen: set = set()
    out: list[str] = []
    for m in _NAME_RE.finditer(text):
        n = m.group(0)
        # Try full match, then shorter prefixes
        candidates = []
        parts = n.split(".")
        for k in range(len(parts), 0, -1):
            candidates.append(".".join(parts[:k]))
        for c in candidates:
            if c in corpus and c not in seen:
                seen.add(c)
                out.append(c)
                break
    return out


def _substitute_name(text: str, name: str, body: str) -> str:
    """Replace whole-word occurrences of `name` in `text` with `(body)`.
    Whole-word means the name is not a prefix/suffix of a longer dotted
    identifier. We use a regex with lookaround for dot/word chars."""
    # Escape the name for regex. The lookbehind ensures the name isn't a
    # suffix of a longer dotted name; lookahead prevents prefix match.
    escaped = re.escape(name)
    pat = re.compile(
        r'(?<![A-Za-z0-9_.])' + escaped + r'(?![A-Za-z0-9_.])'
    )
    return pat.sub(f"({body})", text)


def unfold_signature(sig: str, depth: int, corpus, server_url: str) -> str:
    """Iteratively unfold Mathlib corpus names in `sig` up to `depth`.
    Names whose `#print` output has no `:=` body (structure/class/
    inductive) are left in place."""
    current = sig
    for _ in range(depth):
        names = _names_in(current, corpus)
        if not names:
            break
        any_subbed = False
        for name in names:
            raw = print_decl(name, server_url)
            body = extract_def_body(raw)
            if body:
                current = _substitute_name(current, name, body)
                any_subbed = True
        if not any_subbed:
            break
    return current


def build_file(target_full_name: str, corpus, condition: str,
               depth: int = 1, server_url: str = "http://localhost:9000") -> str | None:
    """Build the Lean file for a target under a condition.

    - intensional: target's signature with notation enabled (original
      Mathlib form).
    - ext-nodoc-d{N}: target's signature unfolded N levels via `#print`.
    """
    p = corpus.get(target_full_name)
    if p is None:
        return None
    # Get the target's full signature from Lean. With notation off +
    # fullNames on, this is a canonical form we can edit.
    sig_text = check_type(target_full_name, server_url)
    if sig_text is None:
        return None
    # `#check @Foo` returns `@Foo : <type>`. Strip the leading `@Foo : `.
    m = re.match(r'^@?[\w.]+\s*:\s*', sig_text)
    if m:
        sig_text = sig_text[m.end():]

    if condition == "intensional":
        body_type = sig_text  # no unfolding
    else:
        # ext-nodoc-d<depth>
        body_type = unfold_signature(sig_text, depth, corpus, server_url)

    return (
        "import Mathlib\n\n"
        "set_option pp.notation true\n\n"
        f"example : {body_type} := by sorry\n"
    )


def extract_kimina_proof(text: str) -> str:
    blocks = _FENCE_RE.findall(text)
    valid = [
        b for b in blocks
        if all(k in b for k in ("by", ":=", "import"))
        and ("theorem" in b or "example" in b)
    ]
    return valid[-1] if valid else ""


def generate(client, model, user_msg, max_tokens=32000, temperature=0.1):
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


def process(target, corpus, condition, depth, client, model, server_url,
            k, log_path):
    fn = target["full_name"]
    code = build_file(fn, corpus, condition, depth=depth, server_url=server_url)
    if code is None:
        rec = {"target": fn, "condition": condition, "skip": "build_failed",
               "pass": False}
        with open(log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        return fn, False, 0, "build"
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
        "target": fn, "condition": condition, "k_tried": len(attempts),
        "pass": any_pass, "attempts": attempts, "file_chars": len(code),
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(rec) + "\n")
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
    depth = 1
    if cond == "intensional":
        depth = 0
    elif cond.startswith("ext-nodoc-d"):
        depth = int(cond.split("-d")[-1])
    else:
        sys.exit(f"bad condition: {cond}")

    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced = load_traced_lookup()
    targets = pilot_pool(corpus, traced, max_n=args.n_targets)
    print(f"condition={cond}  pool={len(targets)}  k={args.k}  "
          f"workers={args.workers}")
    print(f"log={args.log}")
    open(args.log, "w").close()
    client = OpenAI(base_url=args.vllm_url, api_key="EMPTY")

    t0 = time.time()
    passed = skipped = 0
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {
            ex.submit(process, t, corpus, cond, depth, client, args.model,
                      args.server_url, args.k, args.log): t
            for t in targets
        }
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
            print(
                f"  [{done:2d}/{n}] {tag}  {fn[:55]:55s}  {extra}  "
                f"(running {passed}/{done-skipped}, skipped {skipped})",
                flush=True,
            )

    print(f"\n{cond}  Done in {(time.time()-t0)/60:.1f} min.  "
          f"pass@{args.k}: {passed}/{len(targets)-skipped} attempted "
          f"= {100*passed/max(len(targets)-skipped,1):.1f}%   "
          f"({skipped} skipped)")


if __name__ == "__main__":
    main()
