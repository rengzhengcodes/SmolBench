## Current goal
```
⊢ {α} ⊆ ↑⊥ ↔ α ∈ ⊥
```

## Full tactic state
```
F : Type u_1
inst✝² : Field F
E : Type u_2
inst✝¹ : Field E
inst✝ : Algebra F E
α : E
S : Set E
K L : IntermediateField F E
⊢ {α} ⊆ ↑⊥ ↔ α ∈ ⊥
```

## Proof so far (1 tactic)
```lean
rw [finrank_adjoin_eq_one_iff]
```

## Theorem
`IntermediateField.finrank_adjoin_simple_eq_one_iff` in `Mathlib/FieldTheory/Adjoin.lean`

## Premises used in the next tactic
- `Set.singleton_subset_iff`

## Premise signatures
### `Set.singleton_subset_iff` (commanddeclaration)
```lean
@[simp]
theorem singleton_subset_iff {a : α} {s : Set α} : {a} ⊆ s ↔ a ∈ s
```

## Premise full source (with proof)
### `Set.singleton_subset_iff` (commanddeclaration) at `Mathlib/Data/Set/Basic.lean`
```lean
@[simp]
theorem singleton_subset_iff {a : α} {s : Set α} : {a} ⊆ s ↔ a ∈ s :=
  forall_eq
```
