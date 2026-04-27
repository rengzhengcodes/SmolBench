# Deduction track — design

Source of truth for the rewrite. Anything in `deduction/` that contradicts this
doc is wrong.

## Goal

Measure whether positive-information density (same closure, more tokens)
degrades small-model proof-completion accuracy on Mathlib theorems. Two knobs
are exercised over a target pool drawn from LeanDojo Benchmark 4:

- **K** — number of canonical-proof tactics shown to the model as scaffold
  (knob A: depth of progress).
- **B** — BFS depth of premise elaboration shown alongside (knob B: density
  manipulation).

Intensional baseline = (K, B=0). Extensional = (K, B≥1). At fixed K, B varies
displayed token count without changing the closure of mathematical content
available to the model. The verifier is a local kimina-lean-server pinned to
the LeanDojo Mathlib commit (`29dcec074de168ac2bf835a77ef68bbe069194c5`).

## The proof boundary

A proof of T legitimately uses **exactly the lemmas that existed in Mathlib's
dependency graph before T was added**. Concretely, for T declared at line `L`
in source file `F`:

- F's **literal direct `import` lines** (the contiguous import block at the
  top of F) define the import scope. Lean's import resolution is transitive,
  so these few lines pull in F's full upstream Mathlib. Because import edges
  go upstream only, neither F itself nor any file downstream of F is reached.
- `F` lines `1..L-1` is the legitimate prelude (opens, variables, namespace
  stack, helper lemmas declared above T in the same file).

This rules out, by construction:

- T itself — no name collision, no `sb_<name>` rename, no `example` workaround.
- T's trivial corollaries declared after T in F — cannot be looked up.
- Any declaration in files downstream of F.

The verification path never uses `import Mathlib`. The boundary is structural,
not audit-after-the-fact. The full transitive closure is never enumerated —
Lean does the work, given F's first few `import` lines verbatim.

## Dual view

Every target is presented in two parallel forms. They diverge in exactly two
places: (1) the LLM view's prefix is **scope-only** (no helper-lemma
declarations); the Lean view's prefix is **full** (helpers needed for
canonical replay are visible to the elaborator). (2) The LLM view carries a
`# Relevant premises` section; the Lean view does not.

The imports section is **identical** in both views — F's literal direct
`import` lines verbatim.

### LLM view (the user message — what the model sees)

Natural Lean format. The model has been trained on files that look like this;
deviating from the format trades real surface tokens for off-distribution
parsing risk.

```
Think about and solve the following problem step by step in Lean 4.

[# Relevant premises          -- only when B ≥ 1
```lean
<premise 1, full declaration, docstring-stripped>
```
... per-tactic blocks, each block reverse-BFS, deduped across blocks ...
]

# Theorem: <T.full_name>     -- header line for unambiguity

```lean
<F's literal direct imports>
import Aesop
set_option maxHeartbeats 0

<scope-only prefix from F>   -- namespace stack, opens, variables, local notation; NO helper lemmas

theorem <T.local_name> <sig> := by
  <t_1>
  ...
  <t_K>
  -- complete the proof
```
```

The theorem is shown in F's local form (e.g., `theorem map_unop_mul` inside
`namespace Submodule`). The fully-qualified path appears as a header above the
Lean block, so the model sees both.

### Lean view (sent to kimina-lean-server — never seen by the model)

```
<F's literal direct imports>
import Aesop
set_option maxHeartbeats 0

<F prefix, lines 1..L-1, with leading import block stripped>

theorem <T.local_name> <sig> := by
  <t_1>
  ...
  <t_K>
  <model continuation>
```

F's leading import block (the contiguous `import` lines at the top of F, after
the copyright comment) is stripped from the prefix when emitted: those imports
are already emitted as the standalone import block above. F prefix begins at
the first non-import, non-blank, non-pure-comment line.

The LLM view's prefix additionally drops all `theorem`/`lemma`/`def`/`instance`/
`structure`/`inductive`/`class`/`abbrev` declarations from F's prefix —
keeping only `namespace`/`open`/`variable`/`universe`/`section`/`set_option`/
`local notation` lines. This is the **scope-only** prefix. Helper lemmas
declared above T in F are visible to the Lean elaborator (via the full prefix
in the Lean view) but not to the model — the model relies on `import`
resolution, not on F's same-file helpers, which keeps the density measurement
uncluttered by 100s of lines of in-file boilerplate.

The premises section is **never** in the Lean view. The model's premises are
purely informational; they don't change what the elaborator can prove. That is
the point: B is pure density manipulation.

## Knob semantics

Let target T have canonical tactics `[t_1, ..., t_N]` (LeanDojo
`traced_tactics`).

### Knob A: K ∈ {0, ..., N}

The first K tactics are pre-pended to the proof body in **both** views. The
model fills the rest. K=0 ⇒ no scaffold; K=N ⇒ full proof shown.

### Knob B: B ∈ {0, 1, 2, ...}

BFS depth of the premise section in the LLM view.

- `P_0` = direct premises referenced in `t_1..t_K`, taken from
  `traced_tactics[i].annotated_tactic[1].full_name`.
- `P_b` = `P_{b-1} ∪ {premises referenced in declarations of P_{b-1}}`.
- B=0 ⇒ no premise section.
- B≥1 ⇒ rendered declarations of `P_B`.

Termination: hard depth cap = B; Mathlib-only filter (premises in
Init/Batteries skipped).

Premise resolution. For each premise reference, look up its **`full_name`** in
the corpus index — *not* the `def_pos`/`def_end_pos` carried in
`annotated_tactic[1]` (those mark the identifier-name span, not the
declaration range). The corpus entry's `start`/`end` is the declaration range.
References whose `full_name` has no corpus entry (typically `def`s, structure
projections, or alias-introduced declarations not indexed by LeanDojo) are
**skipped and counted**; the per-target counter is recorded in the replay log.

Rendering:

- Each premise rendered as its full source declaration. The corpus is
  inconsistent about whether `[start, end]` includes preceding `@[...]`
  attribute lines — we always **expand backward** through any contiguous
  `@[...]` lines so attribute decoration is uniform across premises.
- Docstring-stripped: `/-- ... -/` blocks removed. Non-doc `--` and `/- ... -/`
  comments kept.
- **No provenance comments.** Each premise is rendered as the declaration text
  only. (Names are recoverable from the declaration head.)
- Order: per-tactic block (one block per `t_i` in order). Within a block:
  reverse-BFS — deepest premises first, the direct premise of the tactic last.
  Sibling premises at the same depth are emitted in **first-seen order**
  (standard BFS); a premise reachable via two parents is attributed to the
  branch where it was first discovered.
- Dedup across blocks: a premise that appears in multiple tactics is emitted
  only in the block of its first occurrence. If a tactic's block becomes empty
  after dedup, **emit nothing** — no header, no marker, no fence.

## Replay-test contract

Before any model evaluation, every candidate target is replay-tested:

1. Build the **Lean view** with `<model continuation>` = the canonical tactics
   `t_1..t_N` (i.e., the full canonical proof, K=0 form).
2. Submit to local Kimina.
3. Pass ⇒ admit T to the pool.
4. Fail ⇒ log + drop. Record the error class.

The K split does not change the total proof, only the prefix/continuation
boundary. One replay per target is sufficient. Targets that fail replay are
excluded from all (K, B) cells — we refuse to measure the model against a
ceiling our verifier cannot reach.

`data/replay_filter.json` is **discarded**. It was built against a different
toolchain and import scope. The pool is rebuilt against our exact Lean view.

## Module layout

```
deduction/
├── corpus.py        # LeanDojo corpus loader, source-range reader, F-imports parser, full + scope-only prefix extractors, nested-namespace local-name resolver.
├── targets.py       # Target dataclass + pool builder.
├── elaborate.py     # Knob B: BFS premise expansion, body retrieval, docstring strip.
├── prompt.py        # Knobs A+B → LLM user message (string assembly only).
├── lean_file.py     # Builds the Lean verification view.
├── kimina.py        # HTTP client to local kimina-lean-server /verify.
├── vllm_client.py   # OpenAI-compatible client + extraction of model's proof body.
├── errors.py        # Parse Kimina error messages into a typed schema.
├── runner.py        # Orchestrate (target × K × B × seed) grid + replay sweep + JSONL log.
├── filter.py        # One-off: build replay-pool by running canonical proofs through Kimina.
├── DESIGN.md        # This file.
└── tests/
    └── test_smoke.py
```

CLI entry point lives in `runner.py`. No legacy modules from the prior
scaffolding survive.

The smoke suite (`tests/test_smoke.py`) must include at least one target with
a **nested namespace** stack (e.g., `namespace A; namespace B; theorem foo`)
to exercise local-name extraction — the corpus only records `full_name`, so
the implementation must walk `namespace`/`end` directives from line 1 to L to
compute the stack and strip the deepest matching prefix.

### Target dataclass

```
Target:
  full_name             # "Submodule.map_unop_mul"
  local_name            # "map_unop_mul" (as written in F, given its namespace stack)
  sig_text              # binders + return type
  tactics               # list[str], from LeanDojo traced_tactics
  premise_refs_per_tactic  # list[list[full_name]] — direct premises per tactic
  file_path             # F, e.g., "Mathlib/Algebra/Module/Submodule/.../Foo.lean"
  start_line            # L (1-indexed)
  imports               # F's literal direct `import` lines (F's import block verbatim)
  f_prefix_full         # F lines 1..L-1, with leading import block stripped (Lean view)
  f_prefix_scope_only   # subset of f_prefix_full keeping only scope-affecting lines (LLM view)
```

## Extraction of model output

The model emits a Lean file in the natural format the prompt taught it. To
build the Lean view we splice its proof body in:

1. Locate the last fenced ```lean ... ``` block in the model output.
2. Within that block, find the *first* `theorem ` or `example ` keyword. Take
   everything from there to end-of-block as the candidate.
3. Within the candidate, locate the *first* `:= by\n` (or `:= by ` followed by
   indentation). Take everything after it as the proof body.
4. The Lean verification view is built as
   `<F's literal imports> + <F prefix full, leading-imports-stripped> +
   theorem <T.local_name> <sig> := by\n <K canonical tactics> +
   <extracted proof body>`.

If the model includes the K canonical tactics in its output, the spliced view
has them duplicated. Lean accepts this — duplicated identical tactics are
no-ops at the goal-state level. If the model omits them, the K we splice
provides them. Either way, the verifier sees the K-prefix once.

If extraction fails at any step (no fenced block, no theorem keyword, no
`:= by`), the cell is logged as a `parse_error` (model output malformed) and
no Kimina request is made.

## Error classification

`errors.py` parses Kimina's `messages` array into a typed schema. Every error
is mapped to one of:

- `identifier_not_found` — with the specific identifier name extracted.
- `type_mismatch` — with the expected and got types when extractable.
- `timeout` — Kimina returned a timeout/heartbeat-exceeded.
- `parse_error` — Lean failed to parse the source.
- `other` — didn't match any of the above; full text preserved.

A separate flag `lookup_leak_attempt` is set when:

- The error is `identifier_not_found` AND the missing identifier is
  - exactly `T.full_name`, or
  - prefixed by `T.full_name`, or
  - in the set of identifiers declared in F at lines ≥ L (downstream of T in F),
    or
  - in the precomputed set of declarations in files downstream of F.

The model has training-time familiarity with T's full Mathlib name. Even with
both views restricted to F's upstream (so T is not in either prompt-scope), the
model may still attempt to call T or its downstream from training memory. Lean
rejects, we flag. This isolates "recall-from-training cheat attempts" from
genuine proof failures.

## Logging schema

JSONL. One record per `(target, K, B, seed)` cell:

```json
{
  "target_id": "Submodule.map_unop_mul",
  "K": 0,
  "B": 0,
  "seed": 0,
  "prompt_chars": 1234,
  "prompt_premise_chars": 0,
  "completion_tokens": 256,
  "extracted_proof_chars": 312,
  "extraction_path": "fenced_block_with_theorem",
  "verify_pass": true,
  "error_class": null,
  "error_detail": null,
  "lookup_leak_attempt": false,
  "wall_ms": 4823
}
```

Replay log (`filter.py` output) uses the same schema with `K=N`, no model run,
just the verifier outcome.

## Decoder defaults

- Model: `Qwen/Qwen2.5-Math-1.5B-Instruct` for the local pilot smoke test.
- vLLM, OpenAI-compatible endpoint at `http://localhost:8010/v1`.
- `temperature=0.7`, `max_tokens=4096`.
- `k=4` decoding seeds per `(target, K, B)` cell.
- Cell verdict = any-of-k pass.

System prompt and user prefix:

```
SYSTEM = "You are an expert programmer and mathematician who helps "
         "formalizing mathematical problems in Lean 4."
USER_PREFIX = "Think about and solve the following problem step by step "
              "in Lean 4.\n\n"
```

## Reused assets

These are not rewritten:

- `data/leandojo_benchmark_4/` — corpus + traced_tactics splits.
- `data/mathlib4/` — shallow Mathlib clone at the pinned SHA, used to read
  declaration source ranges.
- `data/lean_dojo_cache/.../mathlib4/.lake/` — pre-built oleans (5,680 files)
  that kimina-lean-server resolves imports against.
- Pinned Lean toolchain `leanprover/lean4:v4.10.0-rc1`.

## Out of scope

- Promotion to DeepSeek-Prover-V2-7B-FP8 on us-west-2c. Separate task; only
  the model id and base URL change.
- Mathematical model fitting density → accuracy. Downstream analysis on
  pilot output.
- Inductive (chromatic intervals) track. Lives in `induction/`, untouched.
