## Current goal
```
⊢ succ a = succ b ↔ a = b
```

## Full tactic state
```
α : Type u_1
β : Type u_2
inst✝¹ : PartialOrder α
inst✝ : SuccOrder α
a b : α
ha : ¬IsMax a
hb : ¬IsMax b
⊢ succ a = succ b ↔ a = b
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Order.succ_eq_succ_iff_of_not_isMax` in `Mathlib/Order/SuccPred/Basic.lean`

## Premises used in the next tactic
- `eq_iff_le_not_lt`
- `eq_iff_le_not_lt`
- `Order.succ_le_succ_iff_of_not_isMax`
- `Order.succ_lt_succ_iff_of_not_isMax`

## Premise signatures
### `eq_iff_le_not_lt` (commanddeclaration)
```lean
theorem eq_iff_le_not_lt [PartialOrder α] {a b : α} : a = b ↔ a ≤ b ∧ ¬a < b
```

### `eq_iff_le_not_lt` (commanddeclaration)
```lean
theorem eq_iff_le_not_lt [PartialOrder α] {a b : α} : a = b ↔ a ≤ b ∧ ¬a < b
```

### `Order.succ_le_succ_iff_of_not_isMax` (commanddeclaration)
```lean
theorem succ_le_succ_iff_of_not_isMax (ha : ¬IsMax a) (hb : ¬IsMax b) :
    succ a ≤ succ b ↔ a ≤ b
```

### `Order.succ_lt_succ_iff_of_not_isMax` (commanddeclaration)
```lean
theorem succ_lt_succ_iff_of_not_isMax (ha : ¬IsMax a) (hb : ¬IsMax b) :
    succ a < succ b ↔ a < b
```

## Premise full source (with proof)
### `eq_iff_le_not_lt` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
theorem eq_iff_le_not_lt [PartialOrder α] {a b : α} : a = b ↔ a ≤ b ∧ ¬a < b :=
  haveI := Classical.dec
  Decidable.eq_iff_le_not_lt
```

### `eq_iff_le_not_lt` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
theorem eq_iff_le_not_lt [PartialOrder α] {a b : α} : a = b ↔ a ≤ b ∧ ¬a < b :=
  haveI := Classical.dec
  Decidable.eq_iff_le_not_lt
```

### `Order.succ_le_succ_iff_of_not_isMax` (commanddeclaration) at `Mathlib/Order/SuccPred/Basic.lean`
```lean
theorem succ_le_succ_iff_of_not_isMax (ha : ¬IsMax a) (hb : ¬IsMax b) :
    succ a ≤ succ b ↔ a ≤ b := by
  rw [succ_le_iff_of_not_isMax ha, lt_succ_iff_of_not_isMax hb]
```

### `Order.succ_lt_succ_iff_of_not_isMax` (commanddeclaration) at `Mathlib/Order/SuccPred/Basic.lean`
```lean
theorem succ_lt_succ_iff_of_not_isMax (ha : ¬IsMax a) (hb : ¬IsMax b) :
    succ a < succ b ↔ a < b := by
  rw [lt_succ_iff_of_not_isMax hb, succ_le_iff_of_not_isMax ha]
```

## Transitive premise context (1-hop, 7/7 premises, ≈685 tokens)
### `PartialOrder` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
/-- A partial order is a reflexive, transitive, antisymmetric relation `≤`. -/
class PartialOrder (α : Type u) extends Preorder α where
  le_antisymm : ∀ a b : α, a ≤ b → b ≤ a → a = b
```

### `Lean.Parser.Term.haveI` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
/-- `haveI` behaves like `have`, but inlines the value instead of producing a `let_fun` term. -/
@[builtin_term_parser] def «haveI» := leading_parser
  withPosition ("haveI " >> haveDecl) >> optSemicolon termParser
/-- `letI` behaves like `let`, but inlines the value instead of producing a `let_fun` term. -/
```

### `Classical.dec` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
/-- Any prop `p` is decidable classically. A shorthand for `Classical.propDecidable`. -/
noncomputable def dec (p : Prop) : Decidable p := by infer_instance
```

### `Decidable.eq_iff_le_not_lt` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
protected theorem Decidable.eq_iff_le_not_lt [PartialOrder α] [@DecidableRel α (· ≤ ·)] {a b : α} :
    a = b ↔ a ≤ b ∧ ¬a < b :=
  ⟨fun h ↦ ⟨h.le, h ▸ lt_irrefl _⟩, fun ⟨h₁, h₂⟩ ↦
    h₁.antisymm <| Decidable.by_contradiction fun h₃ ↦ h₂ (h₁.lt_of_not_le h₃)⟩
```

### `IsMax` (commanddeclaration) at `Mathlib/Order/Max.lean`
```lean
/-- `a` is a maximal element of `α` if no element is strictly greater than it. We spell it without
`<` to avoid having to convert between `≤` and `<`. Instead, `isMax_iff_forall_not_lt` does the
conversion. -/
def IsMax (a : α) : Prop :=
  ∀ ⦃b⦄, a ≤ b → b ≤ a
```

### `Order.succ_le_iff_of_not_isMax` (commanddeclaration) at `Mathlib/Order/SuccPred/Basic.lean`
```lean
theorem succ_le_iff_of_not_isMax (ha : ¬IsMax a) : succ a ≤ b ↔ a < b :=
  ⟨(lt_succ_of_not_isMax ha).trans_le, succ_le_of_lt⟩
```

### `Order.lt_succ_iff_of_not_isMax` (commanddeclaration) at `Mathlib/Order/SuccPred/Basic.lean`
```lean
theorem lt_succ_iff_of_not_isMax (ha : ¬IsMax a) : b < succ a ↔ b ≤ a :=
  ⟨le_of_lt_succ, fun h => h.trans_lt <| lt_succ_of_not_isMax ha⟩
```
