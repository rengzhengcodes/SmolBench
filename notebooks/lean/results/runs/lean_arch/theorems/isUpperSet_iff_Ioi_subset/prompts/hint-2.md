## Current goal
```
⊢ IsUpperSet s ↔ ∀ ⦃a : α⦄, a ∈ s → Ioi a ⊆ s
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
κ : ι → Sort u_5
inst✝ : PartialOrder α
s : Set α
⊢ IsUpperSet s ↔ ∀ ⦃a : α⦄, a ∈ s → Ioi a ⊆ s
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`isUpperSet_iff_Ioi_subset` in `Mathlib/Order/UpperLower/Basic.lean`

## Premises used in the next tactic
- `isUpperSet_iff_forall_lt`
- `Set.subset_def`
- `forall_swap`

## Premise signatures
### `isUpperSet_iff_forall_lt` (commanddeclaration)
```lean
theorem isUpperSet_iff_forall_lt : IsUpperSet s ↔ ∀ ⦃a b : α⦄, a < b → a ∈ s → b ∈ s
```

### `Set.subset_def` (commanddeclaration)
```lean
theorem subset_def : (s ⊆ t) = ∀ x, x ∈ s → x ∈ t
```

### `forall_swap` (commanddeclaration)
```lean
theorem forall_swap {p : α → β → Prop} : (∀ x y, p x y) ↔ ∀ y x, p x y
```

## Premise full source (with proof)
### `isUpperSet_iff_forall_lt` (commanddeclaration) at `Mathlib/Order/UpperLower/Basic.lean`
```lean
theorem isUpperSet_iff_forall_lt : IsUpperSet s ↔ ∀ ⦃a b : α⦄, a < b → a ∈ s → b ∈ s :=
  forall_congr' fun a => by simp [le_iff_eq_or_lt, or_imp, forall_and]
```

### `Set.subset_def` (commanddeclaration) at `Mathlib/Data/Set/Basic.lean`
```lean
theorem subset_def : (s ⊆ t) = ∀ x, x ∈ s → x ∈ t :=
  rfl
```

### `forall_swap` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
theorem forall_swap {p : α → β → Prop} : (∀ x y, p x y) ↔ ∀ y x, p x y := ⟨swap, swap⟩
```
