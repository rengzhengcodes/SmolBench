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
