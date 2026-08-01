## Current goal
```
⊢ ↑s = Interval.pure a ↔ s = pure a
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
δ : Type u_4
ι : Sort u_5
κ : ι → Sort u_6
inst✝ : Preorder α
s : NonemptyInterval α
a : α
⊢ ↑s = Interval.pure a ↔ s = pure a
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`NonemptyInterval.coe_eq_pure` in `Mathlib/Order/Interval.lean`

## Premises used in the next tactic
- `Interval.coe_inj`
- `NonemptyInterval.coe_pure_interval`

## Premise signatures
### `Interval.coe_inj` (commanddeclaration)
```lean
@[norm_cast] theorem coe_inj {s t : NonemptyInterval α} : (s : Interval α) = t ↔ s = t
```

### `NonemptyInterval.coe_pure_interval` (commanddeclaration)
```lean
@[simp, norm_cast]
theorem coe_pure_interval (a : α) : (pure a : Interval α) = Interval.pure a
```

## Premise full source (with proof)
### `Interval.coe_inj` (commanddeclaration) at `Mathlib/Order/Interval.lean`
```lean
@[norm_cast] -- @[simp, norm_cast] -- Porting note: not in simpNF
theorem coe_inj {s t : NonemptyInterval α} : (s : Interval α) = t ↔ s = t :=
  WithBot.coe_inj
```

### `NonemptyInterval.coe_pure_interval` (commanddeclaration) at `Mathlib/Order/Interval.lean`
```lean
@[simp, norm_cast]
theorem coe_pure_interval (a : α) : (pure a : Interval α) = Interval.pure a :=
  rfl
```

## Transitive premise context (1-hop, 6/6 premises, ≈1620 tokens)
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

### `NonemptyInterval` (commanddeclaration) at `Mathlib/Order/Interval.lean`
```lean
/-- The nonempty closed intervals in an order.

We define intervals by the pair of endpoints `fst`, `snd`. To convert intervals to the set of
elements between these endpoints, use the coercion `NonemptyInterval α → Set α`. -/
@[ext (flat := false)]
structure NonemptyInterval (α : Type*) [LE α] extends Prod α α where
  /-- The starting point of an interval is smaller than the endpoint. -/
  fst_le_snd : fst ≤ snd
```

### `Interval` (commanddeclaration) at `Mathlib/Order/Interval.lean`
```lean
/-- The closed intervals in an order.

We represent intervals either as `⊥` or a nonempty interval given by its endpoints `fst`, `snd`.
To convert intervals to the set of elements between these endpoints, use the coercion
`Interval α → Set α`. -/
@[reducible] -- Porting note: added reducible, it seems to help with coercions
def Interval (α : Type*) [LE α] :=
  WithBot (NonemptyInterval α) -- deriving Inhabited, LE, OrderBot
```

### `WithBot.coe_inj` (commanddeclaration) at `Mathlib/Order/WithBot.lean`
```lean
@[simp, norm_cast]
theorem coe_inj : (a : WithBot α) = b ↔ a = b :=
  Option.some_inj
```

### `Interval.pure` (commanddeclaration) at `Mathlib/Order/Interval.lean`
```lean
/-- `{a}` as an interval. -/
def pure (a : α) : Interval α :=
  NonemptyInterval.pure a
```
