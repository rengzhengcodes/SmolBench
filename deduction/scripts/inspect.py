"""
Loads LeanDojo Benchmark 4 and measures the context *size sweep* available
when expanding premises out to N hops, using traced_tactics across all splits
as the premise-graph source. Phase 0 sanity check before committing to the
LLM harness.

Terminology: both conditions carry the same positive information (sufficient
to prove the target), so information-per-token density is inversely
proportional to size. A size_ratio of K means the extensional context is K
times the character count of the intensional context, i.e. the extensional
representation has 1/K the density of the intensional representation.

Three conditions per depth D:
  intensional       = direct premises' *signatures* only (fixed, D=1, no proof body)
  extensional-nodoc = full declarations of all premises reachable within D hops,
                      Lean comments/docstrings stripped
  extensional-doc   = same as extensional-nodoc, with docstrings kept as-is

BFS over premises uses traced_tactics when available. Leaf premises (no
traced_tactics) contribute their source declaration but don't expand further —
so depth-D extensional contains the union over all paths through the
traced_tactics graph of length <= D.

The Benchmark 4 corpus `code` field is truncated at `:=` for theorems, so
extensional variants read the real declaration from the Mathlib4 clone.
Premises outside Mathlib4 (lean4 core, batteries, etc.) fall back to the
corpus signature since we haven't cloned those.

Signature split uses `[`-depth tracking so attribute-level `:=` (e.g. inside
`@[to_additive (attr := simp)]`) isn't mistaken for the proof separator.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = ROOT / "data" / "leandojo_benchmark_4"
MATHLIB_DIR = ROOT / "data" / "mathlib4"

MAX_DEPTH = 4  # how deep to walk the premise graph
N_SAMPLES = 30  # targets to evaluate
MIN_DIRECT_PREMS = 3
MAX_DIRECT_PREMS = 8
MIN_MATHLIB_FRAC = 0.8  # direct premises that must live in Mathlib4
MIN_TRACED_COVERAGE = 0.4  # fraction of direct premises with own traced_tactics


@dataclass(frozen=True, slots=True)
class Premise:
    full_name: str
    file_path: str
    corpus_code: str
    kind: str
    start: Tuple[int, int]
    end: Tuple[int, int]


def load_corpus(corpus_path: Path) -> Dict[str, Premise]:
    """full_name -> Premise. Last-write-wins if names collide across files."""
    lookup: Dict[str, Premise] = {}
    with corpus_path.open() as f:
        for line in f:
            entry = json.loads(line)
            for p in entry["premises"]:
                lookup[p["full_name"]] = Premise(
                    full_name=p["full_name"],
                    file_path=entry["path"],
                    corpus_code=p["code"],
                    kind=p["kind"],
                    start=tuple(p["start"]),
                    end=tuple(p["end"]),
                )
    return lookup


def load_traced_lookup() -> Dict[str, list]:
    """Union of traced_tactics across every split we have, keyed by theorem full_name.
    This is our premise-graph source for BFS expansion."""
    out: Dict[str, list] = {}
    for schema in ("random", "novel_premises"):
        for split in ("train", "val", "test"):
            path = BENCHMARK_DIR / schema / f"{split}.json"
            for t in json.load(path.open()):
                tactics = t.get("traced_tactics")
                if tactics and t["full_name"] not in out:
                    out[t["full_name"]] = tactics
    return out


def split_signature(code: str) -> str:
    """Signature = prefix up to the first top-level `:=`, where 'top-level'
    means outside `[...]` (attribute brackets)."""
    depth = 0
    i = 0
    while i < len(code) - 1:
        c = code[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
        elif depth == 0 and c == ":" and code[i + 1] == "=":
            return code[:i].rstrip()
        i += 1
    return code.rstrip()


def source_text(premise: Premise) -> str | None:
    """Full declaration text from Mathlib source at the corpus-recorded
    line range. Returns None if the premise file is outside Mathlib4."""
    if not premise.file_path.startswith("Mathlib/"):
        return None
    src_path = MATHLIB_DIR / premise.file_path
    if not src_path.exists():
        return None
    lines = src_path.read_text().splitlines()
    sl, _ = premise.start
    el, _ = premise.end
    return "\n".join(lines[sl - 1 : el])


_BLOCK_COMMENT = re.compile(r"/-[-!]?[\s\S]*?-/")
_LINE_COMMENT = re.compile(r"(^|\s)--[^\n]*", re.MULTILINE)
_BLANK_LINES = re.compile(r"\n\s*\n\s*\n+")


def strip_comments(text: str) -> str:
    text = _BLOCK_COMMENT.sub("", text)
    text = _LINE_COMMENT.sub(lambda m: m.group(1), text)
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()


def premise_refs(tactics: list) -> List[str]:
    """Unique premise full_names referenced across a tactic list, in first-use order."""
    seen: Dict[str, None] = {}
    for tac in tactics:
        for ref in tac.get("annotated_tactic", [None, []])[1]:
            fname = ref.get("full_name")
            if fname and fname not in seen:
                seen[fname] = None
    return list(seen.keys())


def expand_by_layer(
    direct: List[str], traced_lookup: Dict[str, list], max_depth: int
) -> List[List[str]]:
    """BFS from direct premises through the traced_tactics premise graph.
    Returns layers[0]=direct, layers[d]=premises newly reachable at depth d+1."""
    seen: set = set()
    layers: List[List[str]] = []
    current: List[str] = list(dict.fromkeys(direct))
    for _ in range(max_depth):
        new_layer = [n for n in current if n not in seen]
        seen.update(new_layer)
        layers.append(new_layer)
        next_frontier: List[str] = []
        for name in new_layer:
            for fn in premise_refs(traced_lookup.get(name, [])):
                if fn not in seen:
                    next_frontier.append(fn)
        current = list(dict.fromkeys(next_frontier))
        if not current:
            layers.extend([[] for _ in range(max_depth - len(layers))])
            break
    return layers


def render_premises(
    names: List[str], corpus: Dict[str, Premise]
) -> Tuple[List[str], List[str], dict]:
    """Returns (doc_parts, nodoc_parts, diagnostics). Each *_parts is a list of
    full declarations (one per premise), docstring-bearing vs stripped."""
    doc_parts: List[str] = []
    nodoc_parts: List[str] = []
    resolved_src = 0
    resolved_corpus = 0
    missing: List[str] = []
    for name in names:
        p = corpus.get(name)
        if p is None:
            missing.append(name)
            continue
        src = source_text(p)
        if src is not None:
            doc_parts.append(src)
            nodoc_parts.append(strip_comments(src))
            resolved_src += 1
        else:
            doc_parts.append(p.corpus_code)
            nodoc_parts.append(strip_comments(p.corpus_code))
            resolved_corpus += 1
    return doc_parts, nodoc_parts, {
        "n_requested": len(names),
        "resolved_src": resolved_src,
        "resolved_corpus": resolved_corpus,
        "missing": missing,
    }


def build_all_depths(
    theorem: dict, corpus: Dict[str, Premise], traced_lookup: Dict[str, list], max_depth: int
) -> dict:
    """Build intensional + extensional-nodoc/doc at depths 1..max_depth for one target."""
    direct = premise_refs(theorem.get("traced_tactics", []))
    layers = expand_by_layer(direct, traced_lookup, max_depth)

    # Intensional: signatures of direct premises only, from corpus.
    intens_sigs: List[str] = []
    for name in direct:
        p = corpus.get(name)
        if p is not None:
            intens_sigs.append(split_signature(p.corpus_code))
    intensional = "\n\n".join(intens_sigs)

    # Extensional at each cumulative depth.
    depth_output: Dict[int, dict] = {}
    cumulative: List[str] = []
    for d in range(1, max_depth + 1):
        cumulative.extend(layers[d - 1])
        doc_parts, nodoc_parts, diag = render_premises(cumulative, corpus)
        depth_output[d] = {
            "ext_doc": "\n\n".join(doc_parts),
            "ext_nodoc": "\n\n".join(nodoc_parts),
            "n_premises_cum": len(cumulative),
            "layer_size": len(layers[d - 1]),
            "diag": diag,
        }
    return {
        "intensional": intensional,
        "depth": depth_output,
        "n_direct": len(direct),
        "n_direct_with_traces": sum(1 for n in direct if n in traced_lookup),
    }


def pick_well_connected(
    theorems: List[dict],
    corpus: Dict[str, Premise],
    traced_lookup: Dict[str, list],
    n: int,
) -> List[dict]:
    """Filter: prem-count in range, >=min_mathlib_frac in Mathlib, >=min_traced_coverage
    of direct premises have their own traced_tactics (needed for multi-hop walking)."""
    out: List[dict] = []
    for t in theorems:
        prems = premise_refs(t.get("traced_tactics", []))
        if not (MIN_DIRECT_PREMS <= len(prems) <= MAX_DIRECT_PREMS):
            continue
        in_ml = sum(
            1 for n in prems if (p := corpus.get(n)) and p.file_path.startswith("Mathlib/")
        )
        if in_ml / len(prems) < MIN_MATHLIB_FRAC:
            continue
        with_traces = sum(1 for n in prems if n in traced_lookup)
        if with_traces / len(prems) < MIN_TRACED_COVERAGE:
            continue
        out.append(t)
        if len(out) == n:
            break
    return out


def main() -> None:
    print(f"Loading corpus ({BENCHMARK_DIR / 'corpus.jsonl'}) ...")
    corpus = load_corpus(BENCHMARK_DIR / "corpus.jsonl")
    print(f"  {len(corpus)} premises indexed")

    print("Loading traced_tactics across all splits ...")
    traced_lookup = load_traced_lookup()
    print(f"  {len(traced_lookup)} theorems with traced_tactics")

    test_theorems = json.load((BENCHMARK_DIR / "random" / "test.json").open())
    picks = pick_well_connected(test_theorems, corpus, traced_lookup, N_SAMPLES)
    print(
        f"Picked {len(picks)} samples "
        f"(prems in [{MIN_DIRECT_PREMS},{MAX_DIRECT_PREMS}], "
        f">={int(MIN_MATHLIB_FRAC*100)}% mathlib, "
        f">={int(MIN_TRACED_COVERAGE*100)}% have traces)\n"
    )

    # Per-sample results for aggregation.
    per_sample: List[dict] = []
    for thm in picks:
        r = build_all_depths(thm, corpus, traced_lookup, MAX_DEPTH)
        intens_chars = len(r["intensional"])
        row = {
            "name": thm["full_name"],
            "n_direct": r["n_direct"],
            "cov": r["n_direct_with_traces"] / max(r["n_direct"], 1),
            "intens_chars": intens_chars,
        }
        for d in range(1, MAX_DEPTH + 1):
            ext_nodoc_chars = len(r["depth"][d]["ext_nodoc"])
            ext_doc_chars = len(r["depth"][d]["ext_doc"])
            row[f"d{d}_n"] = r["depth"][d]["n_premises_cum"]
            row[f"d{d}_nodoc_c"] = ext_nodoc_chars
            row[f"d{d}_doc_c"] = ext_doc_chars
            row[f"d{d}_nodoc_size"] = ext_nodoc_chars / max(intens_chars, 1)
            row[f"d{d}_doc_size"] = ext_doc_chars / max(intens_chars, 1)
        per_sample.append(row)

    # Eyeball: show first sample's intensional + d1 + d3 extensional-nodoc.
    ex = per_sample[0]
    print("=" * 80)
    print(f"Eyeball sample: {ex['name']}")
    print(f"  direct premises={ex['n_direct']}  coverage={ex['cov']:.0%}  intens={ex['intens_chars']} chars")
    print(
        f"  d1: {ex['d1_n']} prems, nodoc={ex['d1_nodoc_c']} ({ex['d1_nodoc_size']:.2f}x), "
        f"doc={ex['d1_doc_c']} ({ex['d1_doc_size']:.2f}x)"
    )
    print(
        f"  d3: {ex['d3_n']} prems, nodoc={ex['d3_nodoc_c']} ({ex['d3_nodoc_size']:.2f}x), "
        f"doc={ex['d3_doc_c']} ({ex['d3_doc_size']:.2f}x)"
    )
    first_result = build_all_depths(picks[0], corpus, traced_lookup, MAX_DEPTH)
    print("\n--- INTENSIONAL ---")
    print(first_result["intensional"][:1500])
    print("\n--- EXTENSIONAL-NODOC @ depth 3 (first 2000 chars) ---")
    print(first_result["depth"][3]["ext_nodoc"][:2000])
    if len(first_result["depth"][3]["ext_nodoc"]) > 2000:
        print(f"... (truncated, full length {len(first_result['depth'][3]['ext_nodoc'])} chars)")

    # Per-sample compact table.
    print("\n" + "=" * 80)
    print("Per-sample size ratios (extensional-nodoc chars / intensional chars):")
    print("  Higher = more verbose = lower density per the proposal's definition.")
    print(f"  {'name':50s}  {'cov':>5s}  {'intens':>6s}  {'d1':>6s}  {'d2':>6s}  {'d3':>6s}  {'d4':>6s}")
    for row in per_sample:
        name = row["name"][:50]
        print(
            f"  {name:50s}  {row['cov']:>5.0%}  {row['intens_chars']:>6d}  "
            f"{row['d1_nodoc_size']:>5.2f}x  {row['d2_nodoc_size']:>5.2f}x  "
            f"{row['d3_nodoc_size']:>5.2f}x  {row['d4_nodoc_size']:>5.2f}x"
        )

    # Distribution summary across samples.
    print("\n" + "=" * 80)
    print("Size-ratio distribution across samples (extensional-nodoc / intensional):")
    print("  Implied extensional density = 1 / size_ratio (same information, more tokens).")
    print(f"  {'depth':>5s}  {'min':>6s}  {'median':>6s}  {'mean':>6s}  {'max':>6s}  {'n_prem_mean':>11s}")
    for d in range(1, MAX_DEPTH + 1):
        rs = [r[f"d{d}_nodoc_size"] for r in per_sample]
        ps = [r[f"d{d}_n"] for r in per_sample]
        print(
            f"  {d:>5d}  {min(rs):>5.2f}x  {median(rs):>5.2f}x  {mean(rs):>5.2f}x  "
            f"{max(rs):>5.2f}x  {mean(ps):>11.1f}"
        )

    # Docstring premium at depth 3 (representative).
    print("\nDocstring premium at depth 3 (extensional-doc / extensional-nodoc):")
    doc_prems = [r["d3_doc_c"] / max(r["d3_nodoc_c"], 1) for r in per_sample]
    print(f"  min={min(doc_prems):.2f}x  median={median(doc_prems):.2f}x  "
          f"mean={mean(doc_prems):.2f}x  max={max(doc_prems):.2f}x")


if __name__ == "__main__":
    main()
