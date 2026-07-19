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

## Transitive premise context (1-hop, 9/9 premises, ≈981 tokens)
### `Subalgebra` (commanddeclaration) at `Mathlib/Algebra/Algebra/Subalgebra/Basic.lean`
```lean
/-- A subalgebra is a sub(semi)ring that includes the range of `algebraMap`. -/
structure Subalgebra (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] extends
  Subsemiring A : Type v where
  /-- The image of `algebraMap` is contained in the underlying set of the subalgebra -/
  algebraMap_mem' : ∀ r, algebraMap R A r ∈ carrier
  zero_mem' := (algebraMap R A).map_zero ▸ algebraMap_mem' 0
  one_mem' := (algebraMap R A).map_one ▸ algebraMap_mem' 1
```

### `integralClosure` (commanddeclaration) at `Mathlib/RingTheory/IntegralClosure.lean`
```lean
/-- The integral closure of R in an R-algebra A. -/
def integralClosure : Subalgebra R A where
  carrier := { r | IsIntegral R r }
  zero_mem' := isIntegral_zero
  one_mem' := isIntegral_one
  add_mem' := IsIntegral.add
  mul_mem' := IsIntegral.mul
  algebraMap_mem' _ := isIntegral_algebraMap
```

### `Algebra.IsIntegral` (commanddeclaration) at `Mathlib/RingTheory/IntegralClosure.lean`
```lean
/-- An algebra is integral if every element of the extension is integral over the base ring -/
protected def Algebra.IsIntegral : Prop :=
  ∀ x : A, IsIntegral R x
```

### `forall_congr'` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
theorem forall_congr' (h : ∀ a, p a ↔ q a) : (∀ a, p a) ↔ ∀ a, q a :=
  ⟨fun H a => (h a).1 (H a), fun H a => (h a).2 (H a)⟩
```

### `IsIntegral` (commanddeclaration) at `Mathlib/RingTheory/IntegralClosure.lean`
```lean
/-- An element `x` of an algebra `A` over a commutative ring `R` is said to be *integral*,
if it is a root of some monic polynomial `p : R[X]`.
Equivalently, the element is integral over `R` with respect to the induced `algebraMap` -/
def IsIntegral (x : A) : Prop :=
  (algebraMap R A).IsIntegralElem x
```

### `algebraMap` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- Embedding `R →+* A` given by `Algebra` structure. -/
def algebraMap (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] : R →+* A :=
  Algebra.toRingHom
```

### `isIntegral_algebraMap_iff` (commanddeclaration) at `Mathlib/RingTheory/IntegralClosure.lean`
```lean
theorem isIntegral_algebraMap_iff [Algebra A B] [IsScalarTower R A B] {x : A}
    (hAB : Function.Injective (algebraMap A B)) :
    IsIntegral R (algebraMap A B x) ↔ IsIntegral R x :=
  isIntegral_algHom_iff (IsScalarTower.toAlgHom R A B) hAB
```

### `Subtype.coe_injective` (commanddeclaration) at `Mathlib/Data/Subtype.lean`
```lean
theorem coe_injective : Injective (fun (a : Subtype p) ↦ (a : α)) := fun _ _ ↦ Subtype.ext
```

### `Algebra.gc` (commanddeclaration) at `Mathlib/Algebra/Algebra/Subalgebra/Basic.lean`
```lean
protected theorem gc : GaloisConnection (adjoin R : Set A → Subalgebra R A) (↑) := fun s S =>
  ⟨fun H => le_trans (le_trans (Set.subset_union_right _ _) Subsemiring.subset_closure) H,
   fun H => show Subsemiring.closure (Set.range (algebraMap R A) ∪ s) ≤ S.toSubsemiring from
      Subsemiring.closure_le.2 <| Set.union_subset S.range_subset H⟩
```
