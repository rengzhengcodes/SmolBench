## Current goal
```
⊢ (b ⇨ c) ⊓ (a ⇨ b) ⊓ a ≤ c
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
inst✝ : GeneralizedHeytingAlgebra α
a b c d : α
⊢ (b ⇨ c) ⊓ (a ⇨ b) ⊓ a ≤ c
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`himp_inf_himp_inf_le` in `Mathlib/Order/Heyting/Basic.lean`

## Premises used in the next tactic
- `himp_le_himp_himp_himp`

## Premise signatures
### `himp_le_himp_himp_himp` (commanddeclaration)
```lean
theorem himp_le_himp_himp_himp : b ⇨ c ≤ (a ⇨ b) ⇨ a ⇨ c
```

## Premise full source (with proof)
### `himp_le_himp_himp_himp` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem himp_le_himp_himp_himp : b ⇨ c ≤ (a ⇨ b) ⇨ a ⇨ c := by
  rw [le_himp_iff, le_himp_iff, inf_assoc, himp_inf_self, ← inf_assoc, himp_inf_self, inf_assoc]
  exact inf_le_left
```

## Transitive premise context (1-hop, 4/4 premises, ≈256 tokens)
### `le_himp_iff` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem le_himp_iff : a ≤ b ⇨ c ↔ a ⊓ b ≤ c :=
  GeneralizedHeytingAlgebra.le_himp_iff _ _ _
```

### `inf_assoc` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
theorem inf_assoc (a b c : α) : a ⊓ b ⊓ c = a ⊓ (b ⊓ c) := @sup_assoc αᵒᵈ _ _ _ _
```

### `himp_inf_self` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem himp_inf_self (a b : α) : (a ⇨ b) ⊓ a = b ⊓ a := by rw [inf_comm, inf_himp, inf_comm]
```

### `inf_le_left` (commanddeclaration) at `Mathlib/Order/Lattice.lean`
```lean
@[simp]
theorem inf_le_left : a ⊓ b ≤ a :=
  SemilatticeInf.inf_le_left a b
```
