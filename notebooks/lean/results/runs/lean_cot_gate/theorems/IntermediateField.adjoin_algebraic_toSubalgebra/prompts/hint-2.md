## Current goal
```
⊢ Algebra.IsIntegral F ↥(Algebra.adjoin F S)
```

## Full tactic state
```
F : Type u_1
inst✝² : Field F
E : Type u_2
inst✝¹ : Field E
inst✝ : Algebra F E
S✝ : Set E
α : E
S : Set E
hS : ∀ x ∈ S, IsIntegral F x
⊢ Algebra.IsIntegral F ↥(Algebra.adjoin F S)
```

## Proof so far (4 tactics)
```lean
simp only [isAlgebraic_iff_isIntegral] at hS
have : Algebra.IsIntegral F (Algebra.adjoin F S) := by
  rwa [← le_integralClosure_iff_isIntegral, Algebra.adjoin_le_iff]
have := isField_of_isIntegral_of_isField' this (Field.toIsField F)
rw [← ((Algebra.adjoin F S).toIntermediateField' this).eq_adjoin_of_eq_algebra_adjoin F S] <;> rfl
```

## Theorem
`IntermediateField.adjoin_algebraic_toSubalgebra` in `Mathlib/FieldTheory/Adjoin.lean`

## Premises used in the next tactic
- `le_integralClosure_iff_isIntegral`
- `Algebra.adjoin_le_iff`

## Premise signatures
### `le_integralClosure_iff_isIntegral` (commanddeclaration)
```lean
theorem le_integralClosure_iff_isIntegral {S : Subalgebra R A} :
    S ≤ integralClosure R A ↔ Algebra.IsIntegral R S
```

### `Algebra.adjoin_le_iff` (commanddeclaration)
```lean
theorem adjoin_le_iff {S : Subalgebra R A} : adjoin R s ≤ S ↔ s ⊆ S
```

## Premise full source (with proof)
### `le_integralClosure_iff_isIntegral` (commanddeclaration) at `Mathlib/RingTheory/IntegralClosure.lean`
```lean
theorem le_integralClosure_iff_isIntegral {S : Subalgebra R A} :
    S ≤ integralClosure R A ↔ Algebra.IsIntegral R S :=
  SetLike.forall.symm.trans
    (forall_congr' fun x =>
      show IsIntegral R (algebraMap S A x) ↔ IsIntegral R x from
        isIntegral_algebraMap_iff Subtype.coe_injective)
```

### `Algebra.adjoin_le_iff` (commanddeclaration) at `Mathlib/RingTheory/Adjoin/Basic.lean`
```lean
theorem adjoin_le_iff {S : Subalgebra R A} : adjoin R s ≤ S ↔ s ⊆ S :=
  Algebra.gc _ _
```
