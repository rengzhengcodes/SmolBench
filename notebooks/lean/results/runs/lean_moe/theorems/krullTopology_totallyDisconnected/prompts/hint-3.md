## Current goal
```
⊢ σ⁻¹ * τ ≠ 1
```

## Full tactic state
```
K : Type u_1
L : Type u_2
inst✝² : Field K
inst✝¹ : Field L
inst✝ : Algebra K L
h_int : Algebra.IsIntegral K L
σ τ : L ≃ₐ[K] L
h_diff : σ ≠ τ
⊢ σ⁻¹ * τ ≠ 1
```

## Proof so far (9 tactics)
```lean
apply isTotallyDisconnected_of_isClopen_set
intro σ τ h_diff
have hστ : σ⁻¹ * τ ≠ 1 := by rwa [Ne.def, inv_mul_eq_one]
rcases DFunLike.exists_ne hστ with ⟨x, hx : (σ⁻¹ * τ) x ≠ x⟩
let E := IntermediateField.adjoin K ({x} : Set L)
haveI := IntermediateField.adjoin.finiteDimensional (h_int x)
refine' ⟨σ • E.fixingSubgroup,
  ⟨E.fixingSubgroup_isClosed.leftCoset σ, E.fixingSubgroup_isOpen.leftCoset σ⟩,
  ⟨1, E.fixingSubgroup.one_mem', mul_one σ⟩, _⟩
simp only [mem_leftCoset_iff, SetLike.mem_coe, IntermediateField.mem_fixingSubgroup_iff,
  not_forall]
exact ⟨x, IntermediateField.mem_adjoin_simple_self K x, hx⟩
```

## Theorem
`krullTopology_totallyDisconnected` in `Mathlib/FieldTheory/KrullTopology.lean`

## Premises used in the next tactic
- `Ne.def`
- `inv_mul_eq_one`

## Premise signatures
### `Ne.def` (commanddeclaration)
```lean
theorem Ne.def {α : Sort u} (a b : α) : (a ≠ b) = ¬ (a = b)
```

### `inv_mul_eq_one` (commanddeclaration)
```lean
@[to_additive]
theorem inv_mul_eq_one : a⁻¹ * b = 1 ↔ a = b
```

## Premise full source (with proof)
### `Ne.def` (commanddeclaration) at `Mathlib/Init/Logic.lean`
```lean
theorem Ne.def {α : Sort u} (a b : α) : (a ≠ b) = ¬ (a = b) := rfl
```

### `inv_mul_eq_one` (commanddeclaration) at `Mathlib/Algebra/Group/Basic.lean`
```lean
@[to_additive]
theorem inv_mul_eq_one : a⁻¹ * b = 1 ↔ a = b := by rw [mul_eq_one_iff_eq_inv, inv_inj]
```

## Transitive premise context (1-hop, 2/2 premises, ≈146 tokens)
### `mul_eq_one_iff_eq_inv` (commanddeclaration) at `Mathlib/Algebra/Group/Basic.lean`
```lean
@[to_additive]
theorem mul_eq_one_iff_eq_inv : a * b = 1 ↔ a = b⁻¹ :=
  ⟨eq_inv_of_mul_eq_one_left, fun h ↦ by rw [h, mul_left_inv]⟩
```

### `inv_inj` (commanddeclaration) at `Mathlib/Algebra/Group/Basic.lean`
```lean
@[to_additive (attr := simp)]
theorem inv_inj : a⁻¹ = b⁻¹ ↔ a = b :=
  inv_injective.eq_iff
```
