## Current goal
```
⊢ b ⊓ b = b ∧ b ⊔ b = b
```

## Full tactic state
```
case refine_2.intro
α : Type u
β : Type v
inst✝ : Lattice α
b d : α
⊢ b ⊓ b = b ∧ b ⊔ b = b
```

## Proof so far (4 tactics)
```lean
refine ⟨fun h ↦ ?_, ?_⟩
obtain rfl := sup_eq_inf.1 (h.2.trans h.1.symm)
simpa using h
rintro ⟨rfl, rfl⟩
```

## Theorem
`inf_eq_and_sup_eq_iff` in `Mathlib/Order/Lattice.lean`

## Premises used in the next tactic
- `inf_idem`
- `sup_idem`

## Premise signatures
### `inf_idem` (commanddeclaration)
```lean
theorem inf_idem (a : α) : a ⊓ a = a
```

### `sup_idem` (commanddeclaration)
```lean
theorem sup_idem (a : α) : a ⊔ a = a
```

## Premise full source (with proof)
### `inf_idem` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
theorem inf_idem (a : α) : a ⊓ a = a := by simp
```

### `sup_idem` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
theorem sup_idem (a : α) : a ⊔ a = a := by simp
```
