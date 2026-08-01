## Current goal
```
⊢ Antitone (⇑toDual ∘ f ∘ ⇑ofDual) ↔ Antitone f
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
⊢ Antitone (⇑toDual ∘ f ∘ ⇑ofDual) ↔ Antitone f
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`antitone_dual_iff` in `Mathlib/Order/Monotone/Basic.lean`

## Premises used in the next tactic
- `antitone_toDual_comp_iff`
- `monotone_comp_ofDual_iff`

## Premise signatures
### `antitone_toDual_comp_iff` (commanddeclaration)
```lean
@[simp]
theorem antitone_toDual_comp_iff : Antitone (toDual ∘ f : α → βᵒᵈ) ↔ Monotone f
```

### `monotone_comp_ofDual_iff` (commanddeclaration)
```lean
@[simp]
theorem monotone_comp_ofDual_iff : Monotone (f ∘ ofDual) ↔ Antitone f
```

## Premise full source (with proof)
### `antitone_toDual_comp_iff` (commanddeclaration) at `Mathlib/Order/Monotone/Basic.lean`
```lean
@[simp]
theorem antitone_toDual_comp_iff : Antitone (toDual ∘ f : α → βᵒᵈ) ↔ Monotone f :=
  Iff.rfl
```

### `monotone_comp_ofDual_iff` (commanddeclaration) at `Mathlib/Order/Monotone/Basic.lean`
```lean
@[simp]
theorem monotone_comp_ofDual_iff : Monotone (f ∘ ofDual) ↔ Antitone f :=
  forall_swap
```

## Filler (hint:2 → hint:3 token-match, ≈333 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
