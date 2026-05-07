"""Probe 1: body-availability census on the signature-dep graph.

For each problem in a configurable pool, walks the names appearing in the
problem's canonical (notation-disabled, full-names) signature out to MAX_DEPTH,
classifying every encountered name by `#print` kind. The kind decides whether
the name has a `:=` body that the abbrev-substrate expander could inline:

  has body (unfoldable):   def, abbrev, theorem, lemma, instance, opaque
  no body  (terminal):     structure, class, inductive, axiom

The point of this probe is to characterize, before writing the expander, the
ceiling on achievable expansion depth per problem and the kind-mix of the
graph. If most signatures bottom out at structures/inductives within 1-2 hops,
"depth=4 vs depth=2" is mostly a no-op for that subset.

Output:
  - JSONL: one record per problem with the layered name list + classifications.
  - stdout: per-pool summary table.

Run on a box with kimina-lean-server warm (us-west-2c as of 2026-04-25).
Read-only against the lean-server (only `#check` + `#print`).
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
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Callable, Dict, List, Optional, Tuple

import requests

sys.path.insert(0, os.path.expanduser("~/SmolBench"))
from deduction.inspect import BENCHMARK_DIR, load_corpus
from deduction.kimina.lean_query import print_decl, check_type

SERVER_DEFAULT = "http://localhost:9000"
MINIF2F_DEFAULT_DIR = "/tmp/minif2f_test_solved/src"

# Inlined here (not imported from lean_query) so we can keep kimina/ untouched
# while dropping `pp.structureProjections` which the current Lean toolchain
# rejects as unknown. notation=false + fullNames=true is what makes the
# canonical signature show every operator/coercion as its underlying name.
_PP_OPTS = (
    "set_option pp.notation false\n"
    "set_option pp.fullNames true\n"
    "set_option pp.universes false\n"
    "set_option pp.proofs true\n"
    "set_option pp.deepTerms true\n"
    "set_option pp.maxSteps 1000000\n"
)

_THEOREM_RE = re.compile(r'^\s*theorem\s+([A-Za-z0-9_\']+)', re.MULTILINE)
_NAME_RE = re.compile(
    r'[A-Za-z_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]'
    r'[a-zA-Z0-9_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]*'
    r'(?:\.[A-Za-z0-9_Ͱ-Ͽ℀-⅏ᴀ-ᵿ]+)*'
)
# Modifiers that can prefix a `#print` output before the kind keyword.
_MODIFIERS = {"noncomputable", "protected", "private", "unsafe", "partial",
              "@[reducible]", "@[simp]", "@[inline]"}

HAS_BODY_KINDS = {"def", "abbrev", "theorem", "lemma", "instance", "opaque"}
TERMINAL_KINDS = {"structure", "class", "inductive", "axiom"}
# LeanDojo's corpus indexes these on-disk packages; everything except the demo
# widgets is a real Lean/Mathlib name we can substantively reason about.
# Without this filter, names like single-letter `x` from a JSX demo file get
# matched against binders in user signatures.
CORPUS_PATH_DENY_PREFIXES = (".lake/packages/proofwidgets/",)


@dataclass
class Problem:
    """Target for canonical-signature probing.

    `name` is the Lean identifier to `#check @name`. `setup` is any Lean code
    that must precede the `#check` to make `name` resolvable — empty for names
    already in Mathlib (pilot pool); the temp `theorem name <sig> := by sorry`
    wrapper for unregistered statements (miniF2F). `opens` are the source-file
    `open ...` lines, needed so `setup` parses against the same notation
    environment as the original problem."""
    name: str
    setup: str
    opens: List[str]


@dataclass
class NameInfo:
    name: str
    kind: str            # "def"/"theorem"/.../"unknown"/"error"
    has_body: bool
    body_chars: int
    is_mathlib: bool
    # For terminal kinds (structure/class/inductive/axiom) we walk the
    # constructor/field/type signature for new names rather than a `:=` body.
    # `extension_chars` is the cumulative size of those signatures (one
    # `#check` per ctor, summed) — the analogue of body_chars for terminals.
    # Zero for has-body kinds.
    extension_chars: int = 0
    err: Optional[str] = None


def _split_signature(thm_src: str) -> str:
    """Return everything between `theorem <name>` and the top-level `:=`."""
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


def load_minif2f(dir_path: str = MINIF2F_DEFAULT_DIR) -> List[Problem]:
    out = []
    for path in sorted(glob.glob(os.path.join(dir_path, "*.lean"))):
        text = open(path).read()
        m = _THEOREM_RE.search(text)
        if m is None:
            continue
        name = m.group(1)
        thm_src = text[m.start():].rstrip()
        sig_text = _split_signature(thm_src)
        opens = []
        head_lines = text.splitlines()[: text[:m.start()].count("\n") + 1]
        for ln in head_lines:
            s = ln.strip()
            if s.startswith("open scoped "):
                opens.extend(s[len("open scoped "):].split())
            elif s.startswith("open "):
                opens.extend(s[len("open "):].split())
        out.append(Problem(
            name=name,
            setup=f"theorem {name} {sig_text} := by sorry",
            opens=opens,
        ))
    return out


def load_pilot(max_n: int = 73) -> List[Problem]:
    """LeanDojo Mathlib test split, replay-passing + well-connected subset.
    These are real Mathlib names — no setup needed, `#check @full_name` works
    directly against the Mathlib environment."""
    from deduction.inspect import load_traced_lookup
    from deduction.pool_runner import pilot_pool
    full_corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    traced = load_traced_lookup()
    targets = pilot_pool(full_corpus, traced, max_n=max_n)
    return [Problem(name=t["full_name"], setup="", opens=[]) for t in targets]


POOL_LOADERS: Dict[str, Callable[[], List[Problem]]] = {
    "minif2f": load_minif2f,
    "pilot": load_pilot,
}


def _verify(server_url: str, code: str, timeout: int = 60) -> List[dict]:
    r = requests.post(
        f"{server_url}/verify",
        json={"codes": [{"custom_id": "x", "proof": code}]},
        timeout=timeout,
    )
    return r.json()["results"][0].get("response", {}).get("messages", [])


def canonical_signature(prob: Problem, server_url: str) -> Optional[str]:
    """Ask Lean for `#check @<prob.name>` against the import + opens + setup
    environment. Returns the type text (everything after `<name> :`), or None
    on failure."""
    opens_line = ("open " + " ".join(prob.opens) + "\n") if prob.opens else ""
    setup_line = (prob.setup + "\n") if prob.setup else ""
    code = (
        "import Mathlib\n\n"
        + _PP_OPTS
        + "\n"
        + opens_line + "\n"
        + setup_line
        + f"#check @{prob.name}\n"
    )
    msgs = _verify(server_url, code)
    for m in msgs:
        if m.get("severity") != "info":
            continue
        text = str(m.get("data", ""))
        # `<name> : <type>` or `@<name> : <type>` — Lean keeps the @ prefix
        # when the name has implicit args. Strip both forms before matching.
        idx = text.find(":")
        if idx <= 0:
            continue
        prefix = text[:idx].strip().lstrip("@")
        if prefix == prob.name:
            return text[idx + 1:].strip()
    return None


def classify_kind(print_output: Optional[str]) -> Tuple[str, Optional[str]]:
    """Return (kind, body_text_or_None). kind ∈ HAS_BODY_KINDS ∪ TERMINAL_KINDS
    ∪ {"not_in_lean", "unknown"}. `not_in_lean` = #print returned no info
    (name resolvable in our corpus but not as a queryable Lean decl, e.g.
    `Real.lt` which is supplied via instance, not declaration). `unknown` =
    leading keyword we don't recognize."""
    if not print_output:
        return "not_in_lean", None
    # Skip leading modifiers.
    tokens = print_output.lstrip().split()
    i = 0
    while i < len(tokens) and tokens[i] in _MODIFIERS:
        i += 1
    if i >= len(tokens):
        return "unknown", None
    head = tokens[i]
    # `def`, `abbrev`, ... are bare keywords. Some show as `theorem` etc.
    if head in HAS_BODY_KINDS:
        idx = print_output.find(":=")
        if idx >= 0:
            return head, print_output[idx + 2:].strip()
        return head, None  # has-body kind but no := found (rare)
    if head in TERMINAL_KINDS:
        return head, None
    return "unknown", None


def expand_terminal(name: str, kind: str, server_url: str,
                    corpus) -> Tuple[List[str], int]:
    """Walk a terminal-kind name for new corpus-resolvable names.

    For structure/class/inductive, the `#print` output has a structured layout:
        class Group ...
        parents:
          Group.toDivInvMonoid : DivInvMonoid G
        fields:
          Mul.mul : G → G → G
          ...
        constructor:
          Group.mk ... : Group G
    All three sections (parents, fields, constructor) reference real Mathlib
    names — `parents:` is where `extends` chains live, which is the bulk of
    structurally-meaningful expansion. We just scan the whole `#print` output
    for corpus names rather than trying to parse the sections individually
    (Lean's format varies — structures indent constructor lines by 2 spaces,
    inductives don't indent constructor lines at all).

    For axioms, walk the type via `#check` since `#print axiom Foo : T` just
    gives the type back.

    Returns (new_names, chars_of_walked_text). chars is body_chars's analogue
    for terminals — the cumulative size of the text we scanned.
    """
    if kind == "axiom":
        try:
            tp = check_type(name, server_url)
        except Exception:
            return [], 0
        if not tp:
            return [], 0
        return list(dict.fromkeys(names_in(tp, corpus))), len(tp)

    if kind not in {"structure", "class", "inductive"}:
        return [], 0

    try:
        raw = print_decl(name, server_url)
    except Exception:
        return [], 0
    if raw is None:
        return [], 0
    # Self-reference is unavoidable in the print output ("class Foo : ..."
    # references Foo as the type being declared); dedupe it out.
    names = [n for n in names_in(raw, corpus) if n != name]
    return list(dict.fromkeys(names)), len(raw)


def names_in(text: str, corpus) -> List[str]:
    """Distinct corpus-resolvable names in `text`, in order. Tries longest
    dotted match first, then progressively trims prefixes."""
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


def classify_one(name: str, server_url: str, corpus) -> NameInfo:
    """Single `#print` query + classification."""
    p = corpus.get(name)
    is_mathlib = bool(p and p.file_path.startswith("Mathlib/"))
    try:
        raw = print_decl(name, server_url)
    except Exception as e:
        return NameInfo(name=name, kind="error", has_body=False, body_chars=0,
                        is_mathlib=is_mathlib, err=str(e)[:80])
    kind, body = classify_kind(raw)
    return NameInfo(
        name=name, kind=kind,
        has_body=(body is not None and body != ""),
        body_chars=(len(body) if body else 0),
        is_mathlib=is_mathlib,
    )


def walk_problem(prob: Problem, corpus, server_url: str,
                 max_depth: int, walk_terminals: bool = True) -> dict:
    """Walk the signature-dep graph for one problem out to `max_depth`.
    Returns a serializable record. Each name is queried at most once even if
    it appears at multiple depths (counted at first appearance).

    walk_terminals: if False, structures/classes/inductives/axioms are not
    expanded — their fields/constructors/parents are treated as the leaves
    of the graph. This reproduces the original (pre-extension) behavior."""
    sig = canonical_signature(prob, server_url)
    if sig is None:
        return {
            "problem": prob.name, "ok": False, "err": "canonical_sig_failed",
            "opens": prob.opens,
        }
    layer0 = names_in(sig, corpus)
    layers: List[List[str]] = [layer0]
    seen: set = set(layer0)
    info: Dict[str, NameInfo] = {}

    for n in layer0:
        info[n] = classify_one(n, server_url, corpus)

    for _ in range(1, max_depth + 1):
        next_layer: List[str] = []
        for parent in layers[-1]:
            ni = info.get(parent)
            if ni is None:
                continue
            child_names: List[str] = []
            if ni.has_body:
                # def/abbrev/theorem/lemma/instance/opaque — walk the := body.
                try:
                    raw = print_decl(parent, server_url)
                except Exception:
                    raw = None
                if raw is not None:
                    _, body = classify_kind(raw)
                    if body:
                        child_names = names_in(body, corpus)
            elif walk_terminals and ni.kind in {"structure", "class",
                                                "inductive", "axiom"}:
                # Terminal: walk constructor/field types (or axiom's type).
                child_names, ext_chars = expand_terminal(
                    parent, ni.kind, server_url, corpus
                )
                ni.extension_chars = ext_chars
            for n in child_names:
                if n in seen:
                    continue
                seen.add(n)
                next_layer.append(n)
                info[n] = classify_one(n, server_url, corpus)
        if not next_layer:
            break
        layers.append(next_layer)

    return {
        "problem": prob.name,
        "ok": True,
        "opens": prob.opens,
        "canonical_sig_chars": len(sig),
        "canonical_sig": sig,
        "layers": [
            {
                "depth": d,
                "n_names": len(layer),
                "names": [asdict(info[n]) for n in layer],
            }
            for d, layer in enumerate(layers)
        ],
        "n_unique_names": len(info),
    }


def summarize(records: List[dict], max_depth: int) -> None:
    ok_records = [r for r in records if r.get("ok")]
    n_ok = len(ok_records)
    n_fail = len(records) - n_ok
    print(f"\n{'='*78}")
    print(f"Problems: {len(records)} total, {n_ok} ok, {n_fail} failed")
    if n_fail:
        sample = [r["problem"] for r in records if not r.get("ok")][:5]
        print(f"  fail sample: {sample}")

    if not n_ok:
        return

    print(f"\nNames per depth (mean):")
    print(f"  {'depth':>5s}  {'n_problems':>10s}  {'mean_n':>8s}  {'median_n':>8s}  {'max_n':>6s}")
    for d in range(max_depth + 1):
        sizes = [
            layer["n_names"]
            for r in ok_records
            for layer in r["layers"] if layer["depth"] == d
        ]
        if not sizes:
            continue
        m = sum(sizes) / len(sizes)
        med = sorted(sizes)[len(sizes) // 2]
        print(f"  {d:>5d}  {len(sizes):>10d}  {m:>8.2f}  {med:>8d}  {max(sizes):>6d}")

    print(f"\nKind distribution across all unique names (pool-wide):")
    kinds = Counter()
    for r in ok_records:
        for layer in r["layers"]:
            for n in layer["names"]:
                kinds[n["kind"]] += 1
    total = sum(kinds.values())
    for k, c in sorted(kinds.items(), key=lambda kv: -kv[1]):
        bucket = ("has_body" if k in HAS_BODY_KINDS
                  else "terminal" if k in TERMINAL_KINDS
                  else "other")
        print(f"  {k:14s}  {c:>6d}  ({100*c/total:5.1f}%)  [{bucket}]")

    print(f"\nSaturation depth (where BFS stopped finding new names):")
    sat_depths = []
    for r in ok_records:
        L = len(r["layers"])
        sat_depths.append(L if L <= max_depth else max_depth + 1)
    sat_counts = Counter(sat_depths)
    for d in sorted(sat_counts):
        label = (f"sat at d={d}" if d <= max_depth
                 else f"didn't saturate by d={max_depth}")
        print(f"  {label:30s}  {sat_counts[d]:>4d} problems")

    print(f"\nCanonical sig length (chars):")
    sigs = [r["canonical_sig_chars"] for r in ok_records]
    print(f"  min={min(sigs)} median={sorted(sigs)[len(sigs)//2]} "
          f"mean={sum(sigs)/len(sigs):.0f} max={max(sigs)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", default="minif2f", choices=list(POOL_LOADERS))
    ap.add_argument("--server-url", default=SERVER_DEFAULT)
    ap.add_argument("--max-depth", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--n", type=int, default=0,
                    help="if >0, limit to first n problems (for dev)")
    ap.add_argument("--walk-terminals", default=True,
                    action=argparse.BooleanOptionalAction,
                    help="walk structures/classes/inductives/axioms via "
                         "their constructor/field/parent types "
                         "(--no-walk-terminals reproduces the pre-extension "
                         "def/theorem-only behavior)")
    ap.add_argument("--out", required=True, help="JSONL output path")
    args = ap.parse_args()

    print(f"Loading corpus from {BENCHMARK_DIR / 'corpus.jsonl'} ...")
    full_corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    corpus = {
        n: p for n, p in full_corpus.items()
        if not any(p.file_path.startswith(d) for d in CORPUS_PATH_DENY_PREFIXES)
    }
    print(f"  {len(full_corpus)} premises indexed, "
          f"{len(corpus)} after path filter "
          f"(dropped {len(full_corpus)-len(corpus)} from "
          f"{','.join(CORPUS_PATH_DENY_PREFIXES)})")

    problems = POOL_LOADERS[args.pool]()
    if args.n > 0:
        problems = problems[: args.n]
    print(f"Pool '{args.pool}': {len(problems)} problems")
    print(f"Server: {args.server_url}  max_depth={args.max_depth}  "
          f"workers={args.workers}  walk_terminals={args.walk_terminals}")
    print(f"Out: {args.out}\n")

    open(args.out, "w").close()
    records: List[dict] = []
    t0 = time.time()
    with futs.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fm = {
            ex.submit(walk_problem, p, corpus, args.server_url,
                      args.max_depth, args.walk_terminals): p
            for p in problems
        }
        for fut in futs.as_completed(fm):
            rec = fut.result()
            records.append(rec)
            with open(args.out, "a") as f:
                f.write(json.dumps(rec) + "\n")
            done = len(records)
            n = len(problems)
            tag = "OK " if rec.get("ok") else "ERR"
            extra = (f"layers={len(rec['layers'])} names={rec['n_unique_names']}"
                     if rec.get("ok") else rec.get("err", "?"))
            print(f"  [{done:3d}/{n}] {tag}  {rec['problem'][:50]:50s}  {extra}",
                  flush=True)

    print(f"\nDone in {(time.time()-t0)/60:.1f} min")
    summarize(records, args.max_depth)


if __name__ == "__main__":
    main()
