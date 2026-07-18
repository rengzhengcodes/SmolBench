## Current goal
```
⊢ ￢∂ a = ⊤
```

## Full tactic state
```
α : Type u_1
inst✝ : CoheytingAlgebra α
a✝ b a : α
⊢ ￢∂ a = ⊤
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Coheyting.hnot_boundary` in `Mathlib/Order/Heyting/Boundary.lean`

## Premises used in the next tactic
- `Coheyting.boundary`
- `hnot_inf_distrib`
- `sup_hnot_self`

## Premise signatures
### `Coheyting.boundary` (commanddeclaration)
```lean
def boundary (a : α) : α
```

### `hnot_inf_distrib` (commanddeclaration)
```lean
theorem hnot_inf_distrib (a b : α) : ￢(a ⊓ b) = ￢a ⊔ ￢b
```

### `sup_hnot_self` (commanddeclaration)
```lean
@[simp]
theorem sup_hnot_self (a : α) : a ⊔ ￢a = ⊤
```

## Premise full source (with proof)
### `Coheyting.boundary` (commanddeclaration) at `Mathlib/Order/Heyting/Boundary.lean`
```lean
/-- The boundary of an element of a co-Heyting algebra is the intersection of its Heyting negation
with itself. Note that this is always `⊥` for a boolean algebra. -/
def boundary (a : α) : α :=
  a ⊓ ￢a
```

### `hnot_inf_distrib` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
theorem hnot_inf_distrib (a b : α) : ￢(a ⊓ b) = ￢a ⊔ ￢b := by
  simp_rw [← top_sdiff', sdiff_inf_distrib]
```

### `sup_hnot_self` (commanddeclaration) at `Mathlib/Order/Heyting/Basic.lean`
```lean
@[simp]
theorem sup_hnot_self (a : α) : a ⊔ ￢a = ⊤ :=
  Codisjoint.eq_top codisjoint_hnot_right
```
