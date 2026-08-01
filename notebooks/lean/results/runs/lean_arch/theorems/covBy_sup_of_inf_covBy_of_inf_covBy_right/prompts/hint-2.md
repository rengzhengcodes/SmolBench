## Current goal
```
⊢ b ⊓ a ⋖ a → b ⊓ a ⋖ b → b ⋖ b ⊔ a
```

## Full tactic state
```
α : Type u_1
inst✝¹ : Lattice α
inst✝ : IsWeakUpperModularLattice α
a b : α
⊢ b ⊓ a ⋖ a → b ⊓ a ⋖ b → b ⋖ b ⊔ a
```

## Proof so far (1 tactic)
```lean
rw [inf_comm, sup_comm]
```

## Theorem
`covBy_sup_of_inf_covBy_of_inf_covBy_right` in `Mathlib/Order/ModularLattice.lean`

## Premises used in the next tactic
- `covBy_sup_of_inf_covBy_of_inf_covBy_left`

## Premise signatures
### `covBy_sup_of_inf_covBy_of_inf_covBy_left` (commanddeclaration)
```lean
theorem covBy_sup_of_inf_covBy_of_inf_covBy_left : a ⊓ b ⋖ a → a ⊓ b ⋖ b → a ⋖ a ⊔ b
```

## Premise full source (with proof)
### `covBy_sup_of_inf_covBy_of_inf_covBy_left` (commanddeclaration) at `Mathlib/Order/ModularLattice.lean`
```lean
theorem covBy_sup_of_inf_covBy_of_inf_covBy_left : a ⊓ b ⋖ a → a ⊓ b ⋖ b → a ⋖ a ⊔ b :=
  IsWeakUpperModularLattice.covBy_sup_of_inf_covBy_covBy
```
