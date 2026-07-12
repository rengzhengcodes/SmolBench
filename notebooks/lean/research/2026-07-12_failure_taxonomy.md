# Failure taxonomy: why base and SFT models miss on the Lean deduction eval

*Generated 2026-07-12 by classifying every failed cell's verbatim Lean error
message in the two pilot runs. Answers: "was it compilation errors, tactic
errors, or logic errors?"*

## Question and data

Both pilot runs score a model on producing the **single remaining ground-truth
tactic** of a Mathlib proof (k strategy `"last"`: the prefix is replayed in
LeanDojo, the model must close the final goal — any tail that reaches
`ProofFinished` counts). Data:

- `notebooks/lean/results/runs/lean_trio_pilot/all_rows.jsonl` — 462 cells;
  llama-31-405b, nemotron-ultra-253b, qwen3-235b-a22b; base + r=16 LoRA each.
- `notebooks/lean/results/runs/lean_qwen4way_pilot/all_rows.jsonl` — 308
  cells; qwen3-235b-a22b base + 3 SFT arms (real Mathlib tails / Goedel-V2
  synthetic / LeanNavigator synthetic).

Each row carries a `verdict` from the 6-value taxonomy in
`smolbench/deduction/lean/verify.py` (`success` / `lean_error` / `incomplete`
/ `given_up` / `exception` / `replay_failed`) plus the verbatim Lean message
in `lean_error`. The run-level `analysis.txt` only buckets at verdict level
(`lerr`/`incp`/…); this report classifies the messages themselves.

Both runs' 2 sanity-gate failures are `DojoInitError: cannot find *.ast.json`
on two Std-side theorems (`String.extract.go₁_add_right_cancel`,
`List.modifyNth_eq_modifyNthTR`) — trace-cache infra, not model failures, and
those theorems produced no cells.

## Classification rules

Substring/regex classifier over `lean_error` (verdict-level buckets pass
through unchanged):

| class | trigger in the Lean message | user-facing bucket |
|---|---|---|
| syntax/parse | `<stdin>:L:C: expected token / end of input`, `unknown tactic` | **compilation error** (unparseable) |
| hallucinated-name | `unknown identifier/constant`, `environment does not contain '…'`, `failed to rewrite using equation theorems` | **compilation error**, root cause: invented lemma names |
| type-error | `type mismatch`, `invalid constructor`, `invalid field notation`, `typeclass instance problem`, `function expected` | **compilation/elaboration error** |
| tactic-misapplication | `tactic 'X' failed`, `rewrite … did not find instance of the pattern`, `simp made no progress`, `motive is not type correct` | **tactic error** (legal tactic, wrong for this goal — root cause is planning) |
| incomplete | verdict `incomplete`: every tactic ran, goal still open | **logic error** (proof insufficient) |
| timeout/infra | verdict `exception` (`DojoTacticTimeoutError` etc.) | infra/resource, excluded from model-blame shares |
| other | ambiguous-name, no-ext-theorem-found, `internal exception #7` | <2% residue |

## Reproducibility snippet

Run from the repo root (any venv; reads JSONL only):

```python
import collections
import json
import pathlib
import re

RUNS = pathlib.Path("notebooks/lean/results/runs")


def classify(err: str) -> str:
    if "DojoTacticTimeoutError" in err or "DojoInitError" in err:
        return "timeout/infra"
    if "empty tail" in err:
        return "empty-output"
    if re.search(r"<stdin>:\d+:\d+", err) or "unknown tactic" in err:
        return "syntax/parse"
    if ("unknown identifier" in err or "unknown constant" in err
            or "the environment does not contain" in err
            or "failed to rewrite using equation theorems" in err):
        return "hallucinated-name"
    if ("type mismatch" in err or "invalid constructor" in err
            or "invalid field notation" in err or "typeclass instance problem" in err
            or "function expected" in err):
        return "type-error"
    if "failed" in err or "made no progress" in err or "tactic '" in err:
        return "tactic-misapplication"
    return "other"


CATS = ["success", "syntax/parse", "hallucinated-name", "type-error",
        "tactic-misapplication", "incomplete", "gave-up", "timeout/infra",
        "empty-output", "other"]
# short column labels, same order as CATS
HDRS = ["pass", "syntax", "hallucname", "type-err", "tactic-mis", "incompl",
        "gaveup", "infra", "empty", "other"]

for run in ("lean_trio_pilot", "lean_qwen4way_pilot"):
    cells = [r for r in map(json.loads, open(RUNS / run / "all_rows.jsonl"))
             if r.get("kind") == "cell"]
    table = collections.defaultdict(collections.Counter)
    step1 = collections.Counter()
    for r in cells:
        v = r["verdict"]
        cat = ("success" if v == "success" else
               "incomplete" if v == "incomplete" else
               "gave-up" if v == "given_up" else
               "timeout/infra" if v == "exception" else
               classify(r.get("lean_error") or ""))
        table[r["model"]][cat] += 1
        if v == "lean_error":
            m = re.match(r"tail step (\d+)/", r.get("lean_error") or "")
            step1["first" if (m and m.group(1) == "1") else "later"] += 1
    print(f"\n## {run} ({len(cells)} cells)")
    print(f"{'model':30s}" + "".join(f"{h:>11s}" for h in HDRS) + "  total")
    for model in sorted(table):
        n = sum(table[model].values())
        print(f"{model:30s}" + "".join(f"{table[model][c]:11d}" for c in CATS)
              + f"{n:7d}")
    tot = step1["first"] + step1["later"]
    print(f"lean_error rows dying on FIRST generated tactic: "
          f"{step1['first']}/{tot} ({step1['first'] / tot:.0%})")
```

## Per-model taxonomy (snippet output, verified 2026-07-12)

```
## lean_trio_pilot (462 cells)
model                                pass     syntax hallucname   type-err tactic-mis    incompl     gaveup      infra      empty      other  total
llama-31-405b-base                      6         14          4         16         34          0          0          2          0          1     77
llama-31-405b-lean-lora                22          7          3         25         18          2          0          0          0          0     77
nemotron-ultra-253b-base                5         11          7         19         27          2          0          4          0          2     77
nemotron-ultra-253b-lean-lora           6          7         10         15         33          2          0          4          0          0     77
qwen3-235b-a22b-base                    9         17          5         16         22          4          0          4          0          0     77
qwen3-235b-a22b-lean-lora              12          6          6         16         16         21          0          0          0          0     77
lean_error rows dying on FIRST generated tactic: 305/357 (85%)

## lean_qwen4way_pilot (308 cells)
model                                pass     syntax hallucname   type-err tactic-mis    incompl     gaveup      infra      empty      other  total
qwen3-235b-a22b-base                   15         16          4         11         25          4          0          0          0          2     77
qwen3-lean-goedel                      15          5         11         15          9         21          0          0          0          1     77
qwen3-lean-leannav                     17          8         10         12         12         18          0          0          0          0     77
qwen3-lean-real                        14          6          9         13         10         25          0          0          0          0     77
lean_error rows dying on FIRST generated tactic: 171/179 (96%)
```

Pass counts match `analysis.txt` per-model totals for both runs
(6/22/5/6/9/12 and 15/15/17/14).

## Findings

### 1. Base models fail at the compilation/tactic level — and a signature slice is Lean 3 leakage

Qwen3 base (qwen4way run): of 62 failures, 25 are misapplied-but-legal
tactics, 16 are unparseable, 11 are type errors, 4 hallucinated names — and
only 4 are "ran fine but didn't finish". The base models almost never produce
a tail that runs to the end without an error.

A distinctive chunk of the syntax bucket is **Lean 3 / mathlib3 syntax from
pretraining**, which Lean 4 cannot parse:

```
tail step 1/1 ('refl'): <stdin>:1:1: unknown tactic            # Lean 4: rfl
tail step 1/2 ('existsi ⟨f✝, hf⟩'): <stdin>:1:10: expected token
tail step 1/7 ('apply supr_le,'): <stdin>:1:13: expected end of input
                                   # trailing comma + snake_case supr_le (Lean 4: iSup_le)
```

Base models also emit `λ f, …` (Lean 3 lambda comma) and lowercase Lean 3
namespaces (`iso.inv_comp_eq`). Some cells also copy the goal's inaccessible
hypotheses (`f✝`) verbatim, which can never parse.

### 2. SFT shifts the failure mass instead of shrinking it: simp-myopia and name hallucination

Across the three qwen4way SFT arms, syntax errors drop (16 → 5–8) and
tactic-misapplication drops sharply (25 → 9–12) — the models learned to emit
one clean, well-formed, usually-applicable Lean 4 tactic. But two buckets
grow:

- **incomplete balloons (4 → 18–25 per arm, 64 total).** 35 of the 64 are the
  literal single token `simp`, and nearly all the rest are `simp [...]` /
  `simp only [...]` variants: a safe tactic that runs, makes partial
  progress, and leaves the goal open. This is single-step myopia — the SFT
  target was one bare tactic tail, so the model plays a generic move and
  stops.
- **hallucinated names go UP (4 → 9–11 per arm).** The SFT models produce
  plausible-but-nonexistent Mathlib identifiers with perfect naming style:

  ```
  'exact ⟨z, sq_eq_mul_self⟩'  → unknown identifier 'sq_eq_mul_self'
  'exact h.isCompl_of_proj'    → environment does not contain 'LinearMap.IsProj.isCompl_of_proj'
  'simp [… Function.diag_apply]' → unknown identifier 'Function.diag_apply'
  ```

  Naming conventions were learned; which lemmas actually exist was not.

The trio run's r=16 LoRAs show the same direction for qwen (incomplete
4 → 21) and llama (syntax 14 → 7, +16pp pass), while the nemotron LoRA
barely moved its distribution and emitted degenerate multi-tactic blobs (avg
19.4 tactics/cell) — consistent with that adapter not having taken properly.

### 3. Failures are immediate, and every success was a 1-step close

85% (trio) and 96% (qwen4way) of all `lean_error` rows die on the **first
generated tactic**; for the qwen4way SFT arms it is 121/121 = 100%. Since the
eval leaves exactly one ground-truth tactic remaining, all 121 successes in
both runs closed the goal in effectively one step. There is no evidence of
multi-step recovery anywhere: models either nail the step or fail instantly.

### 4. Output-length collapse ties the taxonomy to the known SFT-recipe defect

Base qwen3 spends ~4.5–6k completion tokens per cell (long CoT, never
truncated at the 32k cap); every SFT/LoRA arm spends ~15 tokens and emits a
single tactic in 91–97% of cells. The taxonomy above is the per-error-message
fingerprint of the bare-tactic-target defect identified in
`2026-07-12_sft_recipe_deep_research.md`: training on bare tails removed the
reasoning that would (a) reject non-existent lemma names and (b) keep going
when `simp` doesn't close the goal.

### Infra footnote

The trio run's 14 `exception` rows are all `DojoTacticTimeoutError`, and the
candidate texts show they are **elaboration/unification hangs on
metavariable-heavy `apply` steps** (`apply iSup_mono` / `IsLimit.mk _ _`
families), clustered on 1–2 theorems and hit by several models — a
Lean-side resource limit, not a distinct model failure mode. The qwen4way run
had none.

## Answer: compilation vs tactic vs logic

**Base models:** ~50% of failures are compilation-class (unparseable syntax —
much of it Lean 3 leakage — plus type errors and a few invented names), ~40%
are tactic errors (legal tactics that don't apply to the goal), and under
10% are logic errors in the "ran but didn't finish" sense. (Trio base pooled:
109/211 compilation-class, 83/211 tactic, 6/211 incomplete, 10 timeouts.)

**SFT models (qwen4way arms pooled):** ~48% compilation-class — but now
dominated by **hallucinated lemma names** rather than syntax — ~17% tactic
errors, and ~35% logic errors (64/185 incomplete, mostly bare `simp`).

Two caveats on the labels: tactic-misapplication is *surfaced* by the
compiler but *caused* by planning (the model picked a step that doesn't fit
the goal state), and hallucinated names are knowledge failures wearing a
compilation-error costume. Read as root causes: base models fail on **format
(Lean 3/4 confusion) + planning**; SFT models fail on **library knowledge +
single-step myopia**.

## Implications

The taxonomy independently confirms the fix ordering from the SFT-recipe
report: (1) CoT-style targets (round-1 infra already built:
`cot_stepk1_think_*`) attack both dominant SFT failure modes — reasoning
before answering suppresses invented names and pushes past
`simp`-and-stop; (2) expert iteration with compiler feedback directly trains
on exactly the error messages classified here; (3) none of the failure mass
suggests a capacity/scale problem — the base models' Lean 3 leakage and the
SFT models' myopia are both data-distribution defects.

*Follow-up (same day): the Lean 3 leakage slice now has a dedicated
intervention — deterministic corruption→repair SFT rows built from the
traced mathlib4's `#align` map, mixed into training arms via
`lean_cot_recipe.sh`'s `L3R` env, measured by the `l3` column the analyzer
now emits (see `notebooks/lean/README.md`, "Anti-Lean3 repair mix-in
(L3R)"). The pilot analyses in `results/runs/*/analysis.txt` have been
regenerated with that column.*
