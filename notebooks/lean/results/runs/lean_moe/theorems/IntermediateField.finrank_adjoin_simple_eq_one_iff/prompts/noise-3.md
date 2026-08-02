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

## Filler (hint:2 → hint:3 token-match, ≈114 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et
