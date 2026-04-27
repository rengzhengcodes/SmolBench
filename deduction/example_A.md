# example_A.md — Worked example of knob A/B expansion

This document validates the design in [`DESIGN.md`](DESIGN.md) by walking one
real LeanDojo target through the full pipeline (corpus lookup → premise BFS →
LLM view + Lean view) entirely in text. Read this end-to-end and you should
believe the rewrite is concretely realizable.

A second small contrast example is in the appendix.

---

## Picked target: `Real.log_sqrt`

Found in `data/leandojo_benchmark_4/random/test.json`. First reasonable
candidate that satisfies all selection criteria.

### Target metadata

| field                 | value                                                         |
| --------------------- | ------------------------------------------------------------- |
| `full_name`           | `Real.log_sqrt`                                               |
| `local_name`          | `log_sqrt` (declared inside `namespace Real`, see below)      |
| `file_path` (F)       | `Mathlib/Analysis/SpecialFunctions/Log/Basic.lean`            |
| `start` (corpus)      | `[315, 1]`                                                    |
| `end` (corpus)        | `[317, 20]`                                                   |
| line range L          | `315`                                                         |
| `traced_tactics`      | 2                                                             |
| direct premises       | 6 distinct full_names across both tactics                     |
| Mathlib-only premises | 6 / 6 (none in Init/Batteries)                                |
| B=2 expandable        | 5 / 6 premises have direct corpus entries; 2 have sub-tactics |

### Canonical proof (concatenation of `traced_tactics[].tactic`)

```
rw [eq_div_iff, mul_comm, ← Nat.cast_two, ← log_pow, sq_sqrt hx]   -- t_1
exact two_ne_zero                                                  -- t_2
```

`N = 2`, so K ∈ {0, 1, 2}. State transitions: `t_1` reduces `⊢ log √x =
log x / 2` to `⊢ 2 ≠ 0`; `t_2` closes it.

### F's `import` lines (head of F)

Read from `data/mathlib4/Mathlib/Analysis/SpecialFunctions/Log/Basic.lean`,
lines 1–10:

```lean
/-
Copyright (c) 2018 Chris Hughes. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Chris Hughes, Abhimanyu Pallavi Sudhir, Jean Lo, Calle Sönne
-/
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Data.Nat.Factorization.Basic
import Mathlib.Analysis.NormedSpace.Real

#align_import analysis.special_functions.log.basic from "..."
```

So F directly imports three Mathlib modules. The transitive closure adds
everything those three pull in.

### Transitive-import closure (sketch, one level deeper)

`Mathlib.Analysis.SpecialFunctions.Exp` (head):

```lean
import Mathlib.Analysis.Complex.Asymptotics
import Mathlib.Analysis.SpecificLimits.Normed
```

`Mathlib.Data.Nat.Factorization.Basic` (head):

```lean
import Mathlib.Data.Finsupp.Multiset
import Mathlib.Data.Nat.GCD.BigOperators
import Mathlib.Data.Nat.PrimeFin
import Mathlib.NumberTheory.Padics.PadicVal
import Mathlib.Order.Interval.Finset.Nat
```

`Mathlib.Analysis.NormedSpace.Real` (head):

```lean
import Mathlib.Analysis.NormedSpace.Basic
import Mathlib.Topology.Algebra.Module.Basic
```

So at level 2 the closure already contains
`{ Exp, NormedSpace.Real, Nat.Factorization.Basic,
   Complex.Asymptotics, SpecificLimits.Normed,
   Finsupp.Multiset, Nat.GCD.BigOperators, Nat.PrimeFin,
   Padics.PadicVal, Interval.Finset.Nat,
   NormedSpace.Basic, Topology.Algebra.Module.Basic, ... }`.

Each of those imports more, and so on. The resolver walks this graph
breadth-first, deduplicating by module path, **excluding F itself**
(`Mathlib.Analysis.SpecialFunctions.Log.Basic`). For Mathlib-Basic-style
files this typically expands to a few hundred modules. We do not enumerate
the full set here; the resolver in `corpus.py` is responsible for that. The
point demonstrated: starting from F's three direct imports, recursion is
unambiguous (each `.lean` file's leading `import …` lines parse trivially).

### F prefix (lines 1..L-1 = lines 1..314)

The full prefix is 314 lines, included verbatim in **both** views. Skeleton:

```lean
/- Copyright ... -/
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Data.Nat.Factorization.Basic
import Mathlib.Analysis.NormedSpace.Real

/-! # Real logarithm ... -/
open Set Filter Function
open Topology
noncomputable section

namespace Real                              -- line 32 (live namespace)
variable {x y : ℝ}                          -- line 34

@[pp_nodot]
noncomputable def log (x : ℝ) : ℝ := ...    -- line 41
theorem log_of_ne_zero ...                  -- line 45
... (lines 45..297: dozens of helpers — log_of_pos, exp_log, log_mul,
     log_div, log_inv, log_le_log_iff, etc., all inside `namespace Real`.) ...

@[simp]
theorem log_pow (x : ℝ) (n : ℕ) : log (x ^ n) = n * log x := by   -- line 300
  induction' n with n ih
  · simp
  rcases eq_or_ne x 0 with (rfl | hx)
  · simp
  rw [pow_succ, log_mul (pow_ne_zero _ hx) hx, ih, Nat.cast_succ, add_mul, one_mul]

@[simp]
theorem log_zpow ...                        -- line 308
-- (line 314 ends; line 315 is the target log_sqrt)
```

Two observations:

1. The namespace stack at line 315 is just `namespace Real` (opened 32,
   closed 429). Target is written `theorem log_sqrt ...`; thus
   `full_name = Real.log_sqrt`, `local_name = log_sqrt`.
2. `log_pow` is declared at line 300 — *above* the target. It's in F's
   prefix, hence in scope. The canonical proof refers to it unqualified;
   the elaborator resolves it via the live `namespace Real`.

### Direct premises per tactic (P_0)

From `traced_tactics[i].annotated_tactic[1]`:

`t_1` = `rw [eq_div_iff, mul_comm, ← Nat.cast_two, ← log_pow, sq_sqrt hx]`

| full_name      | def_path                                              |
| -------------- | ----------------------------------------------------- |
| `eq_div_iff`   | `Mathlib/Algebra/GroupWithZero/Units/Basic.lean`      |
| `mul_comm`     | `Mathlib/Algebra/Group/Defs.lean`                     |
| `Nat.cast_two` | `Mathlib/Data/Nat/Cast/Defs.lean`                     |
| `Real.log_pow` | `Mathlib/Analysis/SpecialFunctions/Log/Basic.lean` ← **same as F** |
| `Real.sq_sqrt` | `Mathlib/Data/Real/Sqrt.lean`                         |

`t_2` = `exact two_ne_zero`

| full_name     | def_path                       |
| ------------- | ------------------------------ |
| `two_ne_zero` | `Mathlib/Algebra/NeZero.lean`  |

All six premises live in `Mathlib/...` so none are filtered by the
"Mathlib-only" rule. `Real.log_pow` is in F itself (`def_path == F.file_path`)
but at line 300 < 315 = L, so it is captured by F's prefix and is a
legitimate reference. Whether to render it in the **premises section** is a
judgment call — see *Judgment calls*. The default chosen here is to render
it like any other Mathlib premise; this is harmless because the premises
section is purely informational and never reaches the verifier.

### B=1 expansion (per-tactic blocks, reverse-BFS, deduped)

At B=1, each block is just the direct premises of that tactic. "Reverse-BFS"
within a block means deepest-first, direct premise of the tactic last; at
B=1 the depth is uniformly 1, so within each block, premise order matches
appearance order in the tactic text from last-mentioned to first-mentioned.
Each premise is rendered as its **full source declaration** read from
`data/mathlib4/<file>` at the corpus-recorded `[start, end]` range,
docstring-stripped (`/-- ... -/` blocks removed; non-doc comments preserved).

Premises pulled in by `t_1` are emitted in `t_1`'s block; the `t_2` premise
in `t_2`'s block. Dedup is across blocks: a premise that appeared earlier is
omitted from later blocks. (None of the t_1 premises overlap with t_2 here,
so dedup makes no visible difference — it's exercised in the synthetic
illustration below.)

Rendered output (this is what would appear under `# Relevant premises` in
the LLM view at B=1; Lean syntax, docstring-stripped):

#### Block for `t_1` (5 declarations, deepest-of-depth-1 ordering)

```lean
-- Real.sq_sqrt — Mathlib/Data/Real/Sqrt.lean lines 201..201
@[simp]
theorem sq_sqrt (h : 0 ≤ x) : √x ^ 2 = x := by rw [sq, mul_self_sqrt h]

-- Real.log_pow — Mathlib/Analysis/SpecialFunctions/Log/Basic.lean lines 300..305
@[simp]
theorem log_pow (x : ℝ) (n : ℕ) : log (x ^ n) = n * log x := by
  induction' n with n ih
  · simp
  rcases eq_or_ne x 0 with (rfl | hx)
  · simp
  rw [pow_succ, log_mul (pow_ne_zero _ hx) hx, ih, Nat.cast_succ, add_mul, one_mul]

-- Nat.cast_two — Mathlib/Data/Nat/Cast/Defs.lean lines 208..208
theorem cast_two [AddMonoidWithOne R] : ((2 : ℕ) : R) = (2 : R) := rfl

-- mul_comm — Mathlib/Algebra/Group/Defs.lean lines 332..332
theorem mul_comm : ∀ a b : G, a * b = b * a := CommMagma.mul_comm

-- eq_div_iff — Mathlib/Algebra/GroupWithZero/Units/Basic.lean lines 357..357
@[field_simps] lemma eq_div_iff (hb : b ≠ 0) : c = a / b ↔ c * b = a := hb.isUnit.eq_div_iff
```

The leading `--` lines are provenance comments I add for readability in this
doc; the production renderer may or may not include them — `DESIGN.md` is
silent. See *Judgment calls*.

#### Block for `t_2` (1 declaration)

```lean
-- two_ne_zero — Mathlib/Algebra/NeZero.lean lines 64..65
@[field_simps]
lemma two_ne_zero [OfNat α 2] [NeZero (2 : α)] : (2 : α) ≠ 0 := NeZero.ne (2 : α)
```

(Note that `two_ne_zero`'s corpus `[start, end] = [64, 1] -> [65, 82]`
includes the preceding `@[field_simps]` attribute line, while
`Real.sq_sqrt`'s range `[201, 1] -> [201, 72]` *excludes* its `@[simp]`
line. The corpus is inconsistent about attribute inclusion — flagged
below.)

### B=2 expansion (where applicable)

For each premise `p ∈ P_0`, look up `p.full_name` in the corpus index
(union of train/val/test). If `p` has its own `traced_tactics`, harvest
their premise refs, filter to Mathlib-only, and add to `P_1`.

From `Real.log_pow` (`traced_tactics` has 5 entries — the inductive proof
above):

| sub-premise         | def_path                                         | corpus entry?                               |
| ------------------- | ------------------------------------------------ | ------------------------------------------- |
| `eq_or_ne`          | `Mathlib/Logic/Basic.lean`                       | yes, `[212,1]→[212,70]`                     |
| `pow_succ`          | `Mathlib/Algebra/Group/Defs.lean`                | yes, `[657,1]→[658,23]`                     |
| `Real.log_mul`      | `Mathlib/Analysis/SpecialFunctions/Log/Basic.lean` (= F) | yes, `[126,1]→[128,100]`             |
| `pow_ne_zero`       | `Mathlib/Algebra/GroupWithZero/Basic.lean`       | yes, `[199,1]→[200,70]`                     |
| `Nat.cast_succ`     | `Mathlib/Data/Nat/Cast/Defs.lean`                | yes, `[135,1]→[136,34]`                     |
| `add_mul`           | `Mathlib/Algebra/Ring/Defs.lean`                 | **no corpus entry** (not a `theorem`/`lemma`?) |
| `one_mul`           | `Mathlib/Algebra/Group/Defs.lean`                | yes, `[477,1]→[478,22]`                     |

From `Real.sq_sqrt` (`traced_tactics` has 1 entry — its by-rfl proof):

| sub-premise         | def_path                                         | corpus entry?                       |
| ------------------- | ------------------------------------------------ | ----------------------------------- |
| `sq`                | `Mathlib/Algebra/Group/Defs.lean`                | **no corpus entry** (likely a `def`) |
| `Real.mul_self_sqrt`| `Mathlib/Data/Real/Sqrt.lean`                    | yes, `[166,1]→[167,80]`             |

The other four direct premises (`eq_div_iff`, `mul_comm`, `Nat.cast_two`,
`two_ne_zero`) have corpus entries with `traced_tactics = []` — they are
proved by direct term-mode (`:= ...` rather than `:= by ...`), so there is
nothing further to expand. They contribute no new sub-premises.

So at B=2, P_2 = P_1 ∪ the seven new full_names that resolve to corpus
entries: `eq_or_ne, pow_succ, Real.log_mul, pow_ne_zero, Nat.cast_succ,
one_mul, Real.mul_self_sqrt`.

(`add_mul` and `sq` are referenced in some declaration body but do not have
corpus entries indexed by `full_name`. The implementation must skip them.
This is a real ambiguity — see *Judgment calls*.)

#### Per-tactic blocks at B=2

**Block for `t_1`** — reverse-BFS over the seven sub-premises (depth 2)
followed by the five direct premises (depth 1). All depth-2 premises that
were discovered through `Real.log_pow` and `Real.sq_sqrt` are emitted before
those direct premises, in the order they were enqueued (here I've ordered
by enqueue order: `Real.log_pow`'s subs first, then `Real.sq_sqrt`'s).

```lean
-- one_mul — depth 2, via Real.log_pow
@[to_additive (attr := simp)]
theorem one_mul : ∀ a : M, 1 * a = a :=
  MulOneClass.one_mul

-- Nat.cast_succ — depth 2, via Real.log_pow
@[norm_cast 500]
theorem cast_succ (n : ℕ) : ((succ n : ℕ) : R) = n + 1 :=
  AddMonoidWithOne.natCast_succ _

-- pow_ne_zero — depth 2, via Real.log_pow
@[field_simps]
lemma pow_ne_zero (n : ℕ) (h : a ≠ 0) : a ^ n ≠ 0 := mt pow_eq_zero h

-- Real.log_mul — depth 2, via Real.log_pow
theorem log_mul (hx : x ≠ 0) (hy : y ≠ 0) : log (x * y) = log x + log y :=
  exp_injective <| by
    rw [exp_log_eq_abs (mul_ne_zero hx hy), exp_add, exp_log_eq_abs hx, exp_log_eq_abs hy, abs_mul]

-- pow_succ — depth 2, via Real.log_pow
@[to_additive succ_nsmul]
theorem pow_succ (a : M) (n : ℕ) : a ^ (n + 1) = a ^ n * a :=
  Monoid.npow_succ n a

-- eq_or_ne — depth 2, via Real.log_pow
theorem eq_or_ne {α : Sort*} (x y : α) : x = y ∨ x ≠ y := em <| x = y

-- Real.mul_self_sqrt — depth 2, via Real.sq_sqrt
@[simp]
theorem mul_self_sqrt (h : 0 ≤ x) : √x * √x = x := by
  rw [Real.sqrt, ← NNReal.coe_mul, NNReal.mul_self_sqrt, Real.coe_toNNReal _ h]

-- Real.sq_sqrt — depth 1
@[simp]
theorem sq_sqrt (h : 0 ≤ x) : √x ^ 2 = x := by rw [sq, mul_self_sqrt h]

-- Real.log_pow — depth 1
@[simp]
theorem log_pow (x : ℝ) (n : ℕ) : log (x ^ n) = n * log x := by
  induction' n with n ih
  · simp
  rcases eq_or_ne x 0 with (rfl | hx)
  · simp
  rw [pow_succ, log_mul (pow_ne_zero _ hx) hx, ih, Nat.cast_succ, add_mul, one_mul]

-- Nat.cast_two — depth 1
theorem cast_two [AddMonoidWithOne R] : ((2 : ℕ) : R) = (2 : R) := rfl

-- mul_comm — depth 1
theorem mul_comm : ∀ a b : G, a * b = b * a := CommMagma.mul_comm

-- eq_div_iff — depth 1
@[field_simps] lemma eq_div_iff (hb : b ≠ 0) : c = a / b ↔ c * b = a := hb.isUnit.eq_div_iff
```

**Block for `t_2`** — direct premises plus any new depth-2 expansion.
`two_ne_zero` has 0 traced_tactics so contributes no children.

```lean
-- two_ne_zero — depth 1
@[field_simps]
lemma two_ne_zero [OfNat α 2] [NeZero (2 : α)] : (2 : α) ≠ 0 := NeZero.ne (2 : α)
```

Token cost (rough character counts) for each B at fixed K:

| B value | premises chars | observed declarations |
| ------- | -------------- | --------------------- |
| 0       | 0              | 0                     |
| 1       | ~700           | 6                     |
| 2       | ~1700          | 13 (6 + 7 new)        |

These are exactly the kind of monotone-growth points (same closure, more
tokens) the experiment is designed to probe.

---

## LLM view at (K=1, B=1)

The full user message. (The system message and `USER_PREFIX` come from
`vllm_client.py` defaults.) K=1 means `t_1` is spliced as the first proof
step; the model must continue.

````
Think about and solve the following problem step by step in Lean 4.

# Relevant premises

```lean
@[simp]
theorem sq_sqrt (h : 0 ≤ x) : √x ^ 2 = x := by rw [sq, mul_self_sqrt h]
```

```lean
@[simp]
theorem log_pow (x : ℝ) (n : ℕ) : log (x ^ n) = n * log x := by
  induction' n with n ih
  · simp
  rcases eq_or_ne x 0 with (rfl | hx)
  · simp
  rw [pow_succ, log_mul (pow_ne_zero _ hx) hx, ih, Nat.cast_succ, add_mul, one_mul]
```

```lean
theorem cast_two [AddMonoidWithOne R] : ((2 : ℕ) : R) = (2 : R) := rfl
```

```lean
theorem mul_comm : ∀ a b : G, a * b = b * a := CommMagma.mul_comm
```

```lean
@[field_simps] lemma eq_div_iff (hb : b ≠ 0) : c = a / b ↔ c * b = a := hb.isUnit.eq_div_iff
```

# Theorem: Real.log_sqrt

```lean
import Mathlib
import Aesop
set_option maxHeartbeats 0

... (F prefix lines 1..314, exactly as shown earlier) ...

theorem log_sqrt {x : ℝ} (hx : 0 ≤ x) : log (√x) = log x / 2 := by
  rw [eq_div_iff, mul_comm, ← Nat.cast_two, ← log_pow, sq_sqrt hx]
  -- complete the proof
```
````

The `# Theorem: Real.log_sqrt` header gives the model the fully-qualified
name; the Lean block shows the theorem in **F's local form**
(`theorem log_sqrt`) because that's how Lean parses it inside `namespace
Real` and matches the model's pre-training distribution. `t_2` is not
shown — the model must discover `exact two_ne_zero` (or any equivalent).

---

## Lean view at (K=1, B=1)

What `kimina-lean-server` actually verifies. **Never seen by the model.**
The four differences from the LLM view above:

1. `# Relevant premises` section: **completely removed**. B has no effect on
   the verifier — that is the design's load-bearing claim.
2. `# Theorem: …` header line: removed (Lean has no use for it).
3. `import Mathlib`: replaced by F's transitive-import closure, **with F
   itself excluded**.
4. Trailing `-- complete the proof` is replaced by `<model continuation>`
   (or, in replay, by the canonical `t_2`).

```lean
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Data.Nat.Factorization.Basic
import Mathlib.Analysis.NormedSpace.Real
import Mathlib.Analysis.Complex.Asymptotics
import Mathlib.Analysis.SpecificLimits.Normed
... (rest of F's transitive-import closure, deduplicated, ~hundreds of
     modules; explicitly **excludes**
     Mathlib.Analysis.SpecialFunctions.Log.Basic.) ...
import Aesop
set_option maxHeartbeats 0

... (F prefix lines 1..314 — IDENTICAL to the LLM view; F's own
     `import Mathlib.Analysis.SpecialFunctions.Exp` etc. on lines 6–8
     re-appear here as duplicates, which Lean accepts as no-ops) ...

theorem log_sqrt {x : ℝ} (hx : 0 ≤ x) : log (√x) = log x / 2 := by
  rw [eq_div_iff, mul_comm, ← Nat.cast_two, ← log_pow, sq_sqrt hx]
  <model continuation>          -- or, for replay, `exact two_ne_zero`
```

If Kimina accepts the canonical `t_2` continuation in replay mode (K=N,
B=0), `Real.log_sqrt` enters the pool. Otherwise it's dropped.

---

## Diff between the two views

The architectural payoff. At identical (K, B) = (1, 1) the views differ in
exactly two places:

1. **Premises section**: present in LLM view (~700 chars at B=1, ~1700 at
   B=2), absent in Lean view. The model gets the density signal; the
   elaborator never sees a character of it. B cannot change what's
   provable, only what the model can attend to. That is the experiment's
   identification strategy.

2. **Imports**: `import Mathlib` in LLM view; F's transitive-import
   closure with F excluded in Lean view. The model sees the on-distribution
   surface form; Lean is given a strictly smaller scope that structurally
   cannot resolve `Real.log_sqrt` (F is not imported, and F's content is
   inlined as prefix where T is only the currently-being-proved
   declaration). Kills both name-collision and lookup-leak: the verifier
   cannot write `exact Real.log_sqrt` because that identifier does not
   resolve.

Everything else — F prefix, K canonical tactics, `import Aesop`,
`set_option maxHeartbeats 0`, theorem signature in local form, namespace
stack, opens, variables — is byte-identical across the two views.

---

## Per-tactic reverse-BFS + dedup behaviour

`Real.log_sqrt`'s `t_1`/`t_2` premise sets don't overlap, so dedup makes
no visible difference there. Synthetic three-tactic illustration:

```
t_1 = rw [foo, bar]      -- premises: {foo, bar}
t_2 = exact bar.symm     -- premises: {bar}
t_3 = simp [foo, baz]    -- premises: {foo, baz}
```

At B=1, the per-tactic emission with reverse-BFS + cross-block dedup:

```
Block 1 (t_1):
  bar     ← last-mentioned in t_1's text (reverse order)
  foo     ← first-mentioned in t_1
Block 2 (t_2):
  -- bar already emitted in block 1 (DEDUPED)
  (block is empty — see Judgment call #7)
Block 3 (t_3):
  -- foo already emitted in block 1 (DEDUPED)
  baz
```

`bar` and `foo` appear exactly once even though referenced twice. Within
each block, order is reverse-BFS: at B≥2, depth-`B` nodes first, …, depth-1
last; at B=1, depth-1 only, in reverse-of-mention order. Reading bottom-up
gives "general/abstract building blocks introduced before the lemmas that
compose them."

---

## Judgment calls / ambiguities surfaced

DESIGN.md does not explicitly resolve these. None block the rewrite, but
each should be settled before code lands.

1. **`def_pos` vs. corpus `start`/`end`.** Premise refs in
   `annotated_tactic[1]` carry `def_pos`/`def_end_pos`, but those mark just
   the *identifier name span* (e.g., col 22–32 for `eq_div_iff`), not the
   declaration. The full range lives in the *corpus entry* keyed by
   `full_name`. DESIGN.md says "corpus-recorded `[start, end]`" — I read
   that as the corpus entry. Confirmed empirically. Document in `corpus.py`.

2. **Premises with no corpus entry.** Two B=2 sub-premises here (`add_mul`
   from `Real.log_pow`'s body, `sq` from `Real.sq_sqrt`'s body) have
   `def_path` in `Mathlib/...` but no corpus entry indexed by `full_name`
   in any split. They are presumably `def`s, structure projections, or
   declarations introduced via `instance`/`alias` not picked up by
   LeanDojo's theorem index. Implementation must either skip them or fall
   back to a `def_path`/`def_pos` source read. Pick one.

3. **Attribute lines.** Some corpus ranges include the preceding `@[…]`
   line (`two_ne_zero` `[64,1]→[65,82]`, `pow_ne_zero`, `pow_succ`); others
   don't (`Real.sq_sqrt` `[201,1]→[201,72]` excludes the `@[simp]` on line
   200; same for `Real.log_pow`, `Nat.cast_succ`). The inconsistency shows
   up in the rendered output above. Either trust the corpus as-is or
   always expand backward through `@[…]` lines — pick one.

4. **Same-file premises.** `Real.log_pow` is in F at line 300 (above L=315),
   so it's already in the prefix and already in scope. Should it still be
   rendered in the LLM-view premises section? I rendered it because the
   premises section is informational and redacting same-file premises
   would create a B-dependent asymmetry. Worth confirming.

5. **Local name extraction for nested namespaces.** Easy here: stack is
   `namespace Real`, so `local_name = log_sqrt`. For nested stacks
   (`namespace A; namespace B; theorem foo` with `full_name = A.B.foo`),
   the implementation must walk `namespace`/`end` from line 1 to compute
   the stack at line L, then strip the deepest matching prefix. The corpus
   does not record the stack. Add a regression test with a nested target.

6. **Duplicate imports between closure and F prefix.** The closure prepends
   F's three direct imports; F's prefix then re-emits them on lines 6–8.
   Lean treats duplicate imports as no-ops, so this is harmless. Stripping
   them would require detecting the end of F's import block. DESIGN.md
   says "F lines 1..L-1, raw text" — leave them.

7. **Empty per-tactic block.** When dedup empties a tactic's block, emit
   nothing? An empty fence? A comment marker? DESIGN.md is silent. I
   defaulted to "nothing at all".

8. **Provenance comments in premise blocks.** The `-- <name> — <file>
   lines …` comments I added in this doc are a readability aid. The
   production prompt may include or omit them; whichever is chosen must
   be held constant across (K, B) cells (otherwise it's a confound on B).

9. **Reverse-BFS sibling redundancy.** When a depth-2 premise is reached
   through two depth-1 premises, does it appear at first-seen or at the
   deepest position? I used first-seen (standard BFS). Within a single
   block the dedup rule already eliminates duplicates so this only matters
   for traversal order, not multiplicity.

---

## Appendix — contrast example: `Convex.thickening`

Picked from the same scan: `Mathlib/Analysis/Convex/Normed.lean`, 2
tactics (`rw [← cthickening_eq_thickening_of_isClosed h.isClosed_iff]`
then `exact h.cthickening`), 2 Mathlib-only direct premises. Same
construction applies with smaller numbers. The point of sketching this
contrast: the architecture's only data-dependent variable is the *number*
of rendered declarations at each B. The LLM view layout, Lean view
layout, view diff, and dedup rule are identical regardless of target —
the design does not require target-specific code paths.
