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

## Filler (hint:2 → hint:3 token-match, ≈72 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occ
