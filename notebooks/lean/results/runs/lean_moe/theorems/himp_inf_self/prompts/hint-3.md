## Current goal
```
⊢ (a ⇨ b) ⊓ a = b ⊓ a
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
inst✝ : GeneralizedHeytingAlgebra α
a✝ b✝ c d a b : α
⊢ (a ⇨ b) ⊓ a = b ⊓ a
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`himp_inf_self` in `Mathlib/Order/Heyting/Basic.lean`

## Premises used in the next tactic
- `inf_comm`
- `inf_himp`
- `inf_comm`

## Premise signatures
### `inf_comm` (commanddeclaration)
```lean
theorem inf_comm (a b : α) : a ⊓ b = b ⊓ a
```

### `inf_himp` (commanddeclaration)
```lean
@[simp]
theorem inf_himp (a b : α) : a ⊓ (a ⇨ b) = a ⊓ b
```

### `inf_comm` (commanddeclaration)
```lean
theorem inf_comm (a b : α) : a ⊓ b = b ⊓ a
```

## Premise full source (with proof)
### `inf_comm` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
theorem inf_comm (a b : α) : a ⊓ b = b ⊓ a := @sup_comm αᵒᵈ _ _ _
```

### `inf_himp` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem inf_himp (a b : α) : a ⊓ (a ⇨ b) = a ⊓ b :=
  le_antisymm (le_inf inf_le_left <| by rw [inf_comm, ← le_himp_iff]) <| inf_le_inf_left _ le_himp
```

### `inf_comm` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
theorem inf_comm (a b : α) : a ⊓ b = b ⊓ a := @sup_comm αᵒᵈ _ _ _
```

## Transitive premise context (1-hop, 7/7 premises, ≈413 tokens)
### `sup_comm` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
theorem sup_comm (a b : α) : a ⊔ b = b ⊔ a := by apply le_antisymm <;> simp
```

### `le_antisymm` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
theorem le_antisymm : ∀ {a b : α}, a ≤ b → b ≤ a → a = b :=
  PartialOrder.le_antisymm _ _
```

### `le_inf` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
theorem le_inf : a ≤ b → a ≤ c → a ≤ b ⊓ c :=
  SemilatticeInf.le_inf a b c
```

### `inf_le_left` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
@[simp]
theorem inf_le_left : a ⊓ b ≤ a :=
  SemilatticeInf.inf_le_left a b
```

### `le_himp_iff` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem le_himp_iff : a ≤ b ⇨ c ↔ a ⊓ b ≤ c :=
  GeneralizedHeytingAlgebra.le_himp_iff _ _ _
```

### `inf_le_inf_left` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
@[gcongr]
theorem inf_le_inf_left (a : α) {b c : α} (h : b ≤ c) : a ⊓ b ≤ a ⊓ c :=
  inf_le_inf le_rfl h
```

### `le_himp` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem le_himp : a ≤ b ⇨ a :=
  le_himp_iff.2 inf_le_left
```
