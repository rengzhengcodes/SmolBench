## Current goal
```
⊢ a ∈ ⨅ i, ⨅ j, f i j ↔ ∃ i j, a ∈ f i j
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
κ : ι → Sort u_5
inst✝ : LE α
S : Set (UpperSet α)
s t : UpperSet α
a : α
f : (i : ι) → κ i → UpperSet α
⊢ a ∈ ⨅ i, ⨅ j, f i j ↔ ∃ i j, a ∈ f i j
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`UpperSet.mem_iInf₂_iff` in `Mathlib/Order/UpperLower/Basic.lean`

## Premises used in the next tactic
- `UpperSet.mem_iInf_iff`

## Premise signatures
### `UpperSet.mem_iInf_iff` (commanddeclaration)
```lean
@[simp]
theorem mem_iInf_iff {f : ι → UpperSet α} : (a ∈ ⨅ i, f i) ↔ ∃ i, a ∈ f i
```

## Premise full source (with proof)
### `UpperSet.mem_iInf_iff` (commanddeclaration) at `Mathlib/Order/UpperLower/Basic.lean`
```lean
@[simp]
theorem mem_iInf_iff {f : ι → UpperSet α} : (a ∈ ⨅ i, f i) ↔ ∃ i, a ∈ f i := by
  rw [← SetLike.mem_coe, coe_iInf]
  exact mem_iUnion
```

## Filler (hint:2 → hint:3 token-match, ≈178 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
