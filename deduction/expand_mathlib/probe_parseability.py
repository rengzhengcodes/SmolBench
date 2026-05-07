"""Probe 3: parseability census on candidate abbrev helpers.

For each unique has-body name in a probe(1) JSONL, build the candidate
`noncomputable abbrev sb_X := <body>` block (the helper the v9 abbrev
substrate would emit) and verify it elaborates against `import Mathlib` plus
the originating problem's `open` lines. Per-(name, opens) result is shared
across problems that share the same opens so we don't re-verify.

Failure modes to expect:
  - `⋯` elision in body (Lean's pp truncated some sub-term)
  - notation that doesn't roundtrip with notation=false / fullNames=true
  - universe parameter mismatches
  - private/protected name visibility
  - typeclass instance gaps when the body relies on out-of-scope instances

Skips terminal-kind names (structure/class/inductive/axiom) — the helper for
those would be `abbrev sb_X := X`, an alias that trivially parses since X is
already declared in Mathlib.

Run on the box with kimina-lean-server warm. One `/verify` per unique
(name, opens) pair; for miniF2F all 244 problems share the same opens so
dedupe shrinks total work to ~unique-name count.
"""
from __future__ import annotations

import argparse
import concurrent.futures as futs
import json
import os
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import requests

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.kimina.lean_query import print_decl

SERVER_DEFAULT = "http://localhost:9000"
HAS_BODY_KINDS = {"def", "abbrev", "theorem", "lemma", "instance", "opaque"}


def _sb(name: str) -> str:
    return "sb_" + re.sub(r'\W', '_', name)


def _verify(server_url: str, code: str, timeout: int = 60) -> List[dict]:
    r = requests.post(
        f"{server_url}/verify",
        json={"codes": [{"custom_id": "x", "proof": code}]},
        timeout=timeout,
    )
    return r.json()["results"][0].get("response", {}).get("messages", [])


def _extract_body(print_output: Optional[str]) -> Optional[str]:
    """Return the text after the first `:=` in `#print` output, or None."""
    if print_output is None:
        return None
    idx = print_output.find(":=")
    if idx < 0:
        return None
    return print_output[idx + 2:].strip()


def bucket_error(err_data: str) -> str:
    s = err_data.lower()
    if "⋯" in err_data or "elided" in s:
        return "elision"
    if "unexpected token" in s or "expected" in s:
        return "parse"
    if "failed to synthesize" in s:
        return "synth"
    if "unknown identifier" in s or "unknown constant" in s:
        return "unknown_id"
    if "type mismatch" in s:
        return "type_mismatch"
    if "redundant binder" in s:
        return "redundant_binder"
    if "universe" in s:
        return "universe"
    if "private" in s or "protected" in s:
        return "visibility"
    return "other"


@dataclass
class HelperResult:
    name: str
    opens_key: str
    parses: bool
    body_chars: int
    err_bucket: Optional[str] = None
    first_err: Optional[str] = None
    elided: bool = False


def check_helper(name: str, opens: List[str], server_url: str) -> HelperResult:
    """Fetch #print body, build `noncomputable abbrev sb_X := body`, verify
    it parses against `import Mathlib + open <opens>`."""
    opens_key = " ".join(sorted(opens))
    raw = print_decl(name, server_url)
    body = _extract_body(raw)
    if not body:
        return HelperResult(name=name, opens_key=opens_key, parses=False,
                            body_chars=0, err_bucket="no_body",
                            first_err="no := in #print output")

    elided = "⋯" in body
    opens_line = ("open " + " ".join(opens) + "\n") if opens else ""
    helper = f"noncomputable abbrev {_sb(name)} := {body}"
    code = (
        "import Mathlib\n\n"
        + opens_line + "\n"
        + helper + "\n"
        + "example : True := trivial\n"
    )
    try:
        msgs = _verify(server_url, code)
    except Exception as e:
        return HelperResult(name=name, opens_key=opens_key, parses=False,
                            body_chars=len(body), err_bucket="exception",
                            first_err=str(e)[:200], elided=elided)
    errs = [m for m in msgs if m.get("severity") == "error"]
    if not errs:
        return HelperResult(name=name, opens_key=opens_key, parses=True,
                            body_chars=len(body), elided=elided)
    first = str(errs[0].get("data", ""))
    return HelperResult(name=name, opens_key=opens_key, parses=False,
                        body_chars=len(body),
                        err_bucket=bucket_error(first),
                        first_err=first[:200], elided=elided)


def collect_candidates(records: List[dict]) -> List[Tuple[str, Tuple[str, ...]]]:
    """From probe(1) JSONL, return distinct (name, sorted_opens_tuple) pairs
    for every has-body name we'd emit a helper for."""
    seen: set = set()
    out: List[Tuple[str, Tuple[str, ...]]] = []
    for r in records:
        if not r.get("ok"):
            continue
        opens = tuple(sorted(r.get("opens", [])))
        for layer in r["layers"]:
            for n in layer["names"]:
                if n["kind"] in HAS_BODY_KINDS:
                    key = (n["name"], opens)
                    if key not in seen:
                        seen.add(key)
                        out.append(key)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonls", nargs="+",
                    help="probe1 JSONL files to read candidate names from")
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", required=True, help="JSONL output path")
    args = ap.parse_args()

    candidates: List[Tuple[str, Tuple[str, ...]]] = []
    pool_for: Dict[Tuple[str, Tuple[str, ...]], List[str]] = {}
    for path in args.jsonls:
        records = [json.loads(l) for l in open(path)]
        label = os.path.basename(path)
        cands = collect_candidates(records)
        print(f"  {label}: {len(records)} problems → "
              f"{len(cands)} (name, opens) candidates")
        for c in cands:
            if c not in pool_for:
                pool_for[c] = []
                candidates.append(c)
            pool_for[c].append(label)
    print(f"\nTotal unique (name, opens) candidates across all inputs: "
          f"{len(candidates)}")
    print(f"Server: {args.server_url}  workers={args.workers}\n")

    open(args.out, "w").close()
    results: List[HelperResult] = []
    t0 = time.time()
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {
            ex.submit(check_helper, name, list(opens), args.server_url): (name, opens)
            for (name, opens) in candidates
        }
        for fut in futs.as_completed(fm):
            res = fut.result()
            results.append(res)
            row = {**asdict(res), "pools": pool_for[(res.name,
                                                    tuple(res.opens_key.split()))]}
            with open(args.out, "a") as f:
                f.write(json.dumps(row) + "\n")
            done = len(results)
            n = len(candidates)
            if done % 50 == 0 or done == n:
                ok = sum(1 for r in results if r.parses)
                print(f"  [{done:5d}/{n}] running pass={ok}/{done} "
                      f"({100*ok/done:.1f}%)", flush=True)

    print(f"\nDone in {(time.time()-t0)/60:.1f} min")
    n = len(results)
    n_pass = sum(1 for r in results if r.parses)
    n_fail = n - n_pass
    n_elided = sum(1 for r in results if r.elided)
    print(f"\n{'='*78}")
    print(f"Total: {n}  pass: {n_pass} ({100*n_pass/n:.1f}%)  "
          f"fail: {n_fail} ({100*n_fail/n:.1f}%)")
    print(f"Body had `⋯` elision: {n_elided} ({100*n_elided/n:.1f}%)")
    if n_fail:
        b = Counter(r.err_bucket for r in results if not r.parses)
        print(f"\nFailure buckets:")
        for k, c in sorted(b.items(), key=lambda kv: -kv[1]):
            print(f"  {k:16s}  {c:>5d}  ({100*c/n_fail:5.1f}% of failures)")
        print(f"\nSample failures (5 per bucket):")
        for k in b:
            samples = [r for r in results if not r.parses and r.err_bucket == k][:5]
            print(f"  --- {k} ---")
            for r in samples:
                print(f"    {r.name[:50]:50s}  body={r.body_chars}c  "
                      f"err: {(r.first_err or '')[:90]}")


if __name__ == "__main__":
    main()
