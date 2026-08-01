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

## Filler (hint:2 → hint:3 token-match, ≈333 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
