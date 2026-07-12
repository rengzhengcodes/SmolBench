## Current goal
```
⊢ a ⇔ b = ⊥
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : HeytingAlgebra α
a✝ a b : α
h : IsCompl a b
⊢ a ⇔ b = ⊥
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`IsCompl.bihimp_eq_bot` in `Mathlib/Order/SymmDiff.lean`

## Premises used in the next tactic
- `compl_bihimp_self`

## Premise signatures
### `compl_bihimp_self` (commanddeclaration)
```lean
@[simp]
theorem compl_bihimp_self : aᶜ ⇔ a = ⊥
```

## Premise full source (with proof)
### `compl_bihimp_self` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
@[simp]
theorem compl_bihimp_self : aᶜ ⇔ a = ⊥ :=
  @hnot_symmDiff_self αᵒᵈ _ _
```

## Filler (hint:2 → hint:3 token-match, ≈110 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
