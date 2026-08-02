## Current goal
```
⊢ False
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
inst✝¹ : SemilatticeSup α
b c : α
inst✝ : OrderBot α
s : Finset ι
f : ι → α
ha : SupIrred ⊥
⊢ False
```

## Proof so far (1 tactic)
```lean
rintro rfl
```

## Theorem
`SupIrred.ne_bot` in `Mathlib/Order/Irreducible.lean`

## Premises used in the next tactic
- `not_supIrred_bot`

## Premise signatures
### `not_supIrred_bot` (commanddeclaration)
```lean
@[simp]
theorem not_supIrred_bot : ¬SupIrred (⊥ : α)
```

## Premise full source (with proof)
### `not_supIrred_bot` (commanddeclaration) at `Mathlib/Order/Irreducible.lean`
```lean
@[simp]
theorem not_supIrred_bot : ¬SupIrred (⊥ : α) :=
  isMin_bot.not_supIrred
```

## Filler (hint:2 → hint:3 token-match, ≈117 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua
