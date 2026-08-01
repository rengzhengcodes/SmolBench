## Current goal
```
⊢ Monotone (⇑toDual ∘ f ∘ ⇑ofDual) ↔ Monotone f
```

## Full tactic state
```
ι : Type u_1
α : Type u
β : Type v
γ : Type w
δ : Type u_2
π : ι → Type u_3
r : α → α → Prop
inst✝¹ : Preorder α
inst✝ : Preorder β
f : α → β
s : Set α
⊢ Monotone (⇑toDual ∘ f ∘ ⇑ofDual) ↔ Monotone f
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`monotone_dual_iff` in `Mathlib/Order/Monotone/Basic.lean`

## Premises used in the next tactic
- `monotone_toDual_comp_iff`
- `antitone_comp_ofDual_iff`

## Premise signatures
### `monotone_toDual_comp_iff` (commanddeclaration)
```lean
@[simp]
theorem monotone_toDual_comp_iff : Monotone (toDual ∘ f : α → βᵒᵈ) ↔ Antitone f
```

### `antitone_comp_ofDual_iff` (commanddeclaration)
```lean
@[simp]
theorem antitone_comp_ofDual_iff : Antitone (f ∘ ofDual) ↔ Monotone f
```

## Premise full source (with proof)
### `monotone_toDual_comp_iff` (commanddeclaration) at `Mathlib/Order/Monotone/Basic.lean`
```lean
@[simp]
theorem monotone_toDual_comp_iff : Monotone (toDual ∘ f : α → βᵒᵈ) ↔ Antitone f :=
  Iff.rfl
```

### `antitone_comp_ofDual_iff` (commanddeclaration) at `Mathlib/Order/Monotone/Basic.lean`
```lean
@[simp]
theorem antitone_comp_ofDual_iff : Antitone (f ∘ ofDual) ↔ Monotone f :=
  forall_swap
```

## Transitive premise context (1-hop, 4/4 premises, ≈309 tokens)
### `Monotone` (commanddeclaration) at `Mathlib/Order/Monotone/Basic.lean`
```lean
/-- A function `f` is monotone if `a ≤ b` implies `f a ≤ f b`. -/
def Monotone (f : α → β) : Prop :=
  ∀ ⦃a b⦄, a ≤ b → f a ≤ f b
```

### `Antitone` (commanddeclaration) at `Mathlib/Order/Monotone/Basic.lean`
```lean
/-- A function `f` is antitone if `a ≤ b` implies `f b ≤ f a`. -/
def Antitone (f : α → β) : Prop :=
  ∀ ⦃a b⦄, a ≤ b → f b ≤ f a
```

### `Iff.rfl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
protected theorem Iff.rfl {a : Prop} : a ↔ a :=
  Iff.refl a

macro_rules | `(tactic| rfl) => `(tactic| exact Iff.rfl)
```

### `forall_swap` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
theorem forall_swap {p : α → β → Prop} : (∀ x y, p x y) ↔ ∀ y x, p x y := ⟨swap, swap⟩
```
