## Current goal
```
⊢ a ∆ b ∆ (c ∆ d) = a ∆ c ∆ (b ∆ d)
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : GeneralizedBooleanAlgebra α
a b c d : α
⊢ a ∆ b ∆ (c ∆ d) = a ∆ c ∆ (b ∆ d)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`symmDiff_symmDiff_symmDiff_comm` in `Mathlib/Order/SymmDiff.lean`

## Premises used in the next tactic
- `symmDiff_assoc`
- `symmDiff_left_comm`

## Premise signatures
### `symmDiff_assoc` (commanddeclaration)
```lean
theorem symmDiff_assoc : a ∆ b ∆ c = a ∆ (b ∆ c)
```

### `symmDiff_left_comm` (commanddeclaration)
```lean
theorem symmDiff_left_comm : a ∆ (b ∆ c) = b ∆ (a ∆ c)
```

## Premise full source (with proof)
### `symmDiff_assoc` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
theorem symmDiff_assoc : a ∆ b ∆ c = a ∆ (b ∆ c) := by
  rw [symmDiff_symmDiff_left, symmDiff_symmDiff_right]
```

### `symmDiff_left_comm` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
theorem symmDiff_left_comm : a ∆ (b ∆ c) = b ∆ (a ∆ c) := by
  simp_rw [← symmDiff_assoc, symmDiff_comm]
```

## Transitive premise context (1-hop, 3/3 premises, ≈533 tokens)
### `symmDiff_symmDiff_left` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
theorem symmDiff_symmDiff_left :
    a ∆ b ∆ c = a \ (b ⊔ c) ⊔ b \ (a ⊔ c) ⊔ c \ (a ⊔ b) ⊔ a ⊓ b ⊓ c :=
  calc
    a ∆ b ∆ c = a ∆ b \ c ⊔ c \ a ∆ b := symmDiff_def _ _
    _ = a \ (b ⊔ c) ⊔ b \ (a ⊔ c) ⊔ (c \ (a ⊔ b) ⊔ c ⊓ a ⊓ b) := by
        { rw [sdiff_symmDiff', sup_comm (c ⊓ a ⊓ b), symmDiff_sdiff] }
    _ = a \ (b ⊔ c) ⊔ b \ (a ⊔ c) ⊔ c \ (a ⊔ b) ⊔ a ⊓ b ⊓ c := by ac_rfl
```

### `symmDiff_symmDiff_right` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
theorem symmDiff_symmDiff_right :
    a ∆ (b ∆ c) = a \ (b ⊔ c) ⊔ b \ (a ⊔ c) ⊔ c \ (a ⊔ b) ⊔ a ⊓ b ⊓ c :=
  calc
    a ∆ (b ∆ c) = a \ b ∆ c ⊔ b ∆ c \ a := symmDiff_def _ _
    _ = a \ (b ⊔ c) ⊔ a ⊓ b ⊓ c ⊔ (b \ (c ⊔ a) ⊔ c \ (b ⊔ a)) := by
        { rw [sdiff_symmDiff', sup_comm (a ⊓ b ⊓ c), symmDiff_sdiff] }
    _ = a \ (b ⊔ c) ⊔ b \ (a ⊔ c) ⊔ c \ (a ⊔ b) ⊔ a ⊓ b ⊓ c := by ac_rfl
```

### `symmDiff_comm` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
theorem symmDiff_comm : a ∆ b = b ∆ a := by simp only [symmDiff, sup_comm]
```
