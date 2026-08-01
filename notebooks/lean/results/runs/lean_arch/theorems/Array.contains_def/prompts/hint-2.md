## Current goal
```
⊢ (∃ x, x ∈ as.data ∧ (a == x) = true) ↔ a ∈ as.data
```

## Full tactic state
```
α : Type u_1
inst✝ : DecidableEq α
a : α
as : Array α
⊢ (∃ x, x ∈ as.data ∧ (a == x) = true) ↔ a ∈ as.data
```

## Proof so far (1 tactic)
```lean
rw [mem_def, contains, any_def, List.any_eq_true]
```

## Theorem
`Array.contains_def` in `.lake/packages/std/Std/Data/Array/Lemmas.lean`

## Premises used in the next tactic
- `and_comm`

## Premise signatures
### `and_comm` (commanddeclaration)
```lean
theorem and_comm : a ∧ b ↔ b ∧ a
```

## Premise full source (with proof)
### `and_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem and_comm : a ∧ b ↔ b ∧ a := And.comm
```
