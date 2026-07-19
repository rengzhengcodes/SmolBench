## Current goal
```
⊢ a ∆ b \ a = b \ a
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
⊢ a ∆ b \ a = b \ a
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`symmDiff_sdiff_left` in `Mathlib/Order/SymmDiff.lean`

## Premises used in the next tactic
- `symmDiff_def`
- `sup_sdiff`
- `sdiff_idem`
- `sdiff_sdiff_self`
- `bot_sup_eq`

## Premise signatures
### `symmDiff_def` (commanddeclaration)
```lean
theorem symmDiff_def [Sup α] [SDiff α] (a b : α) : a ∆ b = a \ b ⊔ b \ a
```

### `sup_sdiff` (commanddeclaration)
```lean
theorem sup_sdiff : (a ⊔ b) \ c = a \ c ⊔ b \ c
```

### `sdiff_idem` (commanddeclaration)
```lean
@[simp]
theorem sdiff_idem : (a \ b) \ b = a \ b
```

### `sdiff_sdiff_self` (commanddeclaration)
```lean
@[simp]
theorem sdiff_sdiff_self : (a \ b) \ a = ⊥
```

### `bot_sup_eq` (commanddeclaration)
```lean
theorem bot_sup_eq (a : α) : ⊥ ⊔ a = a
```

## Premise full source (with proof)
### `symmDiff_def` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
theorem symmDiff_def [Sup α] [SDiff α] (a b : α) : a ∆ b = a \ b ⊔ b \ a :=
  rfl
```

### `sup_sdiff` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem sup_sdiff : (a ⊔ b) \ c = a \ c ⊔ b \ c :=
  sup_sdiff_distrib _ _ _
```

### `sdiff_idem` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem sdiff_idem : (a \ b) \ b = a \ b := by rw [sdiff_sdiff_left, sup_idem]
```

### `sdiff_sdiff_self` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem sdiff_sdiff_self : (a \ b) \ a = ⊥ := by rw [sdiff_sdiff_comm, sdiff_self, bot_sdiff]
```

### `bot_sup_eq` (commanddeclaration) at `Mathlib/Order/BoundedOrder.lean`
```lean
theorem bot_sup_eq (a : α) : ⊥ ⊔ a = a :=
  sup_of_le_right bot_le
```
