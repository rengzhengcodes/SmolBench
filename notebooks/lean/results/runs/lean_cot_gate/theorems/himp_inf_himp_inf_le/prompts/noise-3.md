## Current goal
```
⊢ (b ⇨ c) ⊓ (a ⇨ b) ⊓ a ≤ c
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
inst✝ : GeneralizedHeytingAlgebra α
a b c d : α
⊢ (b ⇨ c) ⊓ (a ⇨ b) ⊓ a ≤ c
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`himp_inf_himp_inf_le` in `Mathlib/Order/Heyting/Basic.lean`

## Premises used in the next tactic
- `himp_le_himp_himp_himp`

## Premise signatures
### `himp_le_himp_himp_himp` (commanddeclaration)
```lean
theorem himp_le_himp_himp_himp : b ⇨ c ≤ (a ⇨ b) ⇨ a ⇨ c
```

## Premise full source (with proof)
### `himp_le_himp_himp_himp` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem himp_le_himp_himp_himp : b ⇨ c ≤ (a ⇨ b) ⇨ a ⇨ c := by
  rw [le_himp_iff, le_himp_iff, inf_assoc, himp_inf_self, ← inf_assoc, himp_inf_self, inf_assoc]
  exact inf_le_left
```

## Filler (hint:2 → hint:3 token-match, ≈280 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt
