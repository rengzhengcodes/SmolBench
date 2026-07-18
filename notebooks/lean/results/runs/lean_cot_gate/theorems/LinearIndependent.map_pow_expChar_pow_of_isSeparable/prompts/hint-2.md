## Current goal
```
⊢ LinearIndependent F ((fun x => v x ^ q ^ n) ∘ Subtype.val)
```

## Full tactic state
```
F : Type u
E : Type v
inst✝⁵ : Field F
inst✝⁴ : Field E
inst✝³ : Algebra F E
K : Type w
inst✝² : Field K
inst✝¹ : Algebra F K
q n : ℕ
hF : ExpChar F q
ι : Type u_1
v : ι → E
inst✝ : IsSeparable F E
h : ∀ (s : Finset ι), LinearIndependent F (v ∘ Subtype.val)
halg : Algebra.IsAlgebraic F E
s : Finset ι
E' : IntermediateField F E := adjoin F ↑(Finset.image v s)
this✝ : FiniteDimensional F ↥E'
this : IsSeparable F ↥E'
v' : { x // x ∈ s } → ↥E' := fun i => { val := v ↑i, property := ⋯ }
h' : LinearIndependent F v'
⊢ LinearIndependent F ((fun x => v x ^ q ^ n) ∘ Subtype.val)
```

## Proof so far (9 tactics)
```lean
classical
have halg := IsSeparable.isAlgebraic F E
rw [linearIndependent_iff_finset_linearIndependent] at h ⊢
intro s
let E' := adjoin F (s.image v : Set E)
haveI : FiniteDimensional F E' := finiteDimensional_adjoin fun x _ ↦ (halg x).isIntegral
haveI : IsSeparable F E' := isSeparable_tower_bot_of_isSeparable F E' E
let v' (i : s) : E' := ⟨v i.1, subset_adjoin F _ (Finset.mem_image.2 ⟨i.1, i.2, rfl⟩)⟩
have h' : LinearIndependent F v' := (h s).of_comp E'.val.toLinearMap
exact (h'.map_pow_expChar_pow_of_fd_isSeparable q n).map'
  E'.val.toLinearMap (LinearMap.ker_eq_bot_of_injective E'.val.injective)
have halg := IsSeparable.isAlgebraic F E
rw [linearIndependent_iff_finset_linearIndependent] at h ⊢
intro s
let E' := adjoin F (s.image v : Set E)
haveI : FiniteDimensional F E' := finiteDimensional_adjoin fun x _ ↦ (halg x).isIntegral
haveI : IsSeparable F E' := isSeparable_tower_bot_of_isSeparable F E' E
let v' (i : s) : E' := ⟨v i.1, subset_adjoin F _ (Finset.mem_image.2 ⟨i.1, i.2, rfl⟩)⟩
have h' : LinearIndependent F v' := (h s).of_comp E'.val.toLinearMap
```

## Theorem
`LinearIndependent.map_pow_expChar_pow_of_isSeparable` in `Mathlib/FieldTheory/PurelyInseparable.lean`

## Premises used in the next tactic
- `LinearIndependent.map'`
- `LinearMap.ker_eq_bot_of_injective`

## Premise signatures
### `LinearIndependent.map'` (commanddeclaration)
```lean
theorem LinearIndependent.map' (hv : LinearIndependent R v) (f : M →ₗ[R] M')
    (hf_inj : LinearMap.ker f = ⊥) : LinearIndependent R (f ∘ v)
```

### `LinearMap.ker_eq_bot_of_injective` (commanddeclaration)
```lean
theorem ker_eq_bot_of_injective {f : F} (hf : Injective f) : ker f = ⊥
```

## Premise full source (with proof)
### `LinearIndependent.map'` (commanddeclaration) at `Mathlib/LinearAlgebra/LinearIndependent.lean`
```lean
/-- An injective linear map sends linearly independent families of vectors to linearly independent
families of vectors. See also `LinearIndependent.map` for a more general statement. -/
theorem LinearIndependent.map' (hv : LinearIndependent R v) (f : M →ₗ[R] M')
    (hf_inj : LinearMap.ker f = ⊥) : LinearIndependent R (f ∘ v) :=
  hv.map <| by simp [hf_inj]
```

### `LinearMap.ker_eq_bot_of_injective` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Ker.lean`
```lean
theorem ker_eq_bot_of_injective {f : F} (hf : Injective f) : ker f = ⊥ := by
  have : Disjoint ⊤ (ker f) := by
    -- Porting note: `← map_zero f` should work here, but it needs to be directly applied to H.
    rw [disjoint_ker]
    intros _ _ H
    rw [← map_zero f] at H
    exact hf H
  simpa [disjoint_iff_inf_le]
```
