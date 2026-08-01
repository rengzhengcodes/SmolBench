## Current goal
```
⊢ pure a * pure b = 1
```

## Full tactic state
```
case refine'_2.intro.intro.intro.intro
F : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
δ : Type u_5
ε : Type u_6
inst✝ : DivisionMonoid α
a b : α
h : a * b = 1
⊢ pure a * pure b = 1
```

## Proof so far (9 tactics)
```lean
refine' ⟨fun hfg => _, _⟩
obtain ⟨t₁, h₁, t₂, h₂, h⟩ : (1 : Set α) ∈ f * g := hfg.symm.subst one_mem_one
have hfg : (f * g).NeBot := hfg.symm.subst one_neBot
rw [(hfg.nonempty_of_mem <| mul_mem_mul h₁ h₂).subset_one_iff, Set.mul_eq_one_iff] at h
obtain ⟨a, b, rfl, rfl, h⟩ := h
refine' ⟨a, b, _, _, h⟩
rwa [← hfg.of_mul_left.le_pure_iff, le_pure_iff]
rwa [← hfg.of_mul_right.le_pure_iff, le_pure_iff]
rintro ⟨a, b, rfl, rfl, h⟩
```

## Theorem
`Filter.mul_eq_one_iff` in `Mathlib/Order/Filter/Pointwise.lean`

## Premises used in the next tactic
- `Filter.pure_mul_pure`
- `Filter.pure_one`

## Premise signatures
### `Filter.pure_mul_pure` (commanddeclaration)
```lean
@[to_additive]
theorem pure_mul_pure : (pure a : Filter α) * pure b = pure (a * b)
```

### `Filter.pure_one` (commanddeclaration)
```lean
@[to_additive (attr := simp)]
theorem pure_one : pure 1 = (1 : Filter α)
```

## Premise full source (with proof)
### `Filter.pure_mul_pure` (commanddeclaration) at `Mathlib/Order/Filter/Pointwise.lean`
```lean
@[to_additive]
-- Porting note (#11119): removed `simp` attribute because `simpNF` says it can prove it.
theorem pure_mul_pure : (pure a : Filter α) * pure b = pure (a * b) :=
  map₂_pure
```

### `Filter.pure_one` (commanddeclaration) at `Mathlib/Order/Filter/Pointwise.lean`
```lean
@[to_additive (attr := simp)]
theorem pure_one : pure 1 = (1 : Filter α) :=
  rfl
```

## Transitive premise context (1-hop, 5/5 premises, ≈1783 tokens)
### `Lean.MVarId.note` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Meta/Tactic/Assert.lean`
```lean
/-- Add the hypothesis `h : t`, given `v : t`, and return the new `FVarId`. -/
def _root_.Lean.MVarId.note (g : MVarId) (h : Name) (v : Expr) (t? : Option Expr := .none) :
    MetaM (FVarId × MVarId) := do
  (← g.assert h (← match t? with | some t => pure t | none => inferType v) v).intro1P

/--
  Convert the given goal `Ctx |- target` into `Ctx |- let name : type := val; target`.
  It assumes `val` has type `type` -/
```

### `Std.Tactic.Lint.simpNF` (commanddeclaration) at `.lake/packages/std/Std/Tactic/Lint/Simp.lean`
```lean
/-- A linter for simp lemmas whose lhs is not in simp-normal form, and which hence never fire. -/
@[std_linter] def simpNF : Linter where
  noErrorsFound := "All left-hand sides of simp lemmas are in simp-normal form."
  errorsFound := "SOME SIMP LEMMAS ARE NOT IN SIMP-NORMAL FORM.
see note [simp-normal form] for tips how to debug this.
https://leanprover-community.github.io/mathlib_docs/notes.html#simp-normal%20form"
  test := fun declName => do
    unless ← isSimpTheorem declName do return none
    let ctx := { ← Simp.Context.mkDefault with config.decide := false }
    checkAllSimpTheoremInfos (← getConstInfo declName).type fun {lhs, rhs, isConditional, ..} => do
      let ({ expr := lhs', proof? := prf1, .. }, prf1Lems) ←
        decorateError "simplify fails on left-hand side:" <| simp lhs ctx
      if prf1Lems.contains (.decl declName) then return none
      let ({ expr := rhs', .. }, used_lemmas) ←
        decorateError "simplify fails on right-hand side:" <| simp rhs ctx (usedSimps := prf1Lems)
      let lhs'EqRhs' ← isSimpEq lhs' rhs' (whnfFirst := false)
      let lhsInNF ← isSimpEq lhs' lhs
      if lhs'EqRhs' then
        if prf1.isNone then return none -- TODO: FP rewriting foo.eq_2 using `simp only [foo]`
        return m!"simp can prove this:
  by {← formatLemmas used_lemmas}
One of the lemmas above could be a duplicate.
If that's not the case try reordering lemmas or adding @[priority].
"
      else if ¬ lhsInNF then
        return m!"Left-hand side simplifies from
  {lhs}
to
  {lhs'}
using
  {← formatLemmas prf1Lems}
Try to change the left-hand side to the simplified term!
"
      else if !isConditional && lhs == lhs' then
        return m!"Left-hand side does not simplify, when using the simp lemma on itself.
This usually means that it will never apply.
"
      else
        return none

library_note "simp-normal form" /--
This note gives you some tips to debug any errors that the simp-normal form linter raises.

The reason that a lemma was considered faulty is because its left-hand side is not in simp-normal
form.
These lemmas are hence never used by the simplifier.

This linter gives you a list of other simp lemmas: look at them!

Here are some tips depending on the error raised by the linter:

  1. 'the left-hand side reduces to XYZ':
     you should probably use XYZ as the left-hand side.

  2. 'simp can prove this':
     This typically means that lemma is a duplicate, or is shadowed by another lemma:

     2a. Always put more general lemmas after specific ones:
      ```
      @[simp] lemma zero_add_zero : 0 + 0 = 0 := rfl
      @[simp] lemma add_zero : x + 0 = x := rfl
      ```

      And not the other way around!  The simplifier always picks the last matching lemma.

     2b. You can also use `@[priority]` instead of moving simp-lemmas around in the file.

      Tip: the default priority is 1000.
      Use `@[priority 1100]` instead of moving a lemma down,
      and `@[priority 900]` instead of moving a lemma up.

     2c. Conditional simp lemmas are tried last. If they are shadowed
         just remove the `simp` attribute.

     2d. If two lemmas are duplicates, the linter will complain about the first one.
         Try to fix the second one instead!
         (You can find it among the other simp lemmas the linter prints out!)

  3. 'try_for tactic failed, timeout':
     This typically means that there is a loop of simp lemmas.
     Try to apply squeeze_simp to the right-hand side (removing this lemma from the simp set) to see
     what lemmas might be causing the loop.

     Another trick is to `set_option trace.simplify.rewrite true` and
     then apply `try_for 10000 { simp }` to the right-hand side.  You will
     see a periodic sequence of lemma applications in the trace message.
-/

/--
A linter for simp lemmas whose lhs has a variable as head symbol,
and which hence never fire.
-/
```

### `Lean.Elab.Tactic.NormCast.prove` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Elab/Tactic/NormCast.lean`
```lean
/--
Discharging function used during simplification in the "squash" step.
-/
-- TODO: normCast takes a list of expressions to use as lemmas for the discharger
-- TODO: a tactic to print the results the discharger fails to prove
def prove (e : Expr) : SimpM (Option Expr) := do
  withTraceNode `Tactic.norm_cast (return m!"{exceptOptionEmoji ·} discharging: {e}") do
  return (← findLocalDeclWithType? e).map mkFVar

/--
Core rewriting function used in the "squash" step, which moves casts upwards
and eliminates them.

It tries to rewrite an expression using the elim and move lemmas.
On failure, it calls the splitting procedure heuristic.
-/
```

### `Filter` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
/-- A filter `F` on a type `α` is a collection of sets of `α` which contains the whole `α`,
is upwards-closed, and is stable under intersection. We do not forbid this collection to be
all sets of `α`. -/
structure Filter (α : Type*) where
  /-- The set of sets that belong to the filter. -/
  sets : Set (Set α)
  /-- The set `Set.univ` belongs to any filter. -/
  univ_sets : Set.univ ∈ sets
  /-- If a set belongs to a filter, then its superset belongs to the filter as well. -/
  sets_of_superset {x y} : x ∈ sets → x ⊆ y → y ∈ sets
  /-- If two sets belong to a filter, then their intersection belongs to the filter as well. -/
  inter_sets {x y} : x ∈ sets → y ∈ sets → x ∩ y ∈ sets
```

### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```
