## Current goal
```
⊢ (liftAux φ) (r • (z + y)) = r • (liftAux φ) (z + y)
```

## Full tactic state
```
case refine'_2
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝⁷ : CommSemiring R
R₁ : Type u_5
R₂ : Type u_6
s : ι → Type u_7
inst✝⁶ : (i : ι) → AddCommMonoid (s i)
inst✝⁵ : (i : ι) → Module R (s i)
M : Type u_8
inst✝⁴ : AddCommMonoid M
inst✝³ : Module R M
E : Type u_9
inst✝² : AddCommMonoid E
inst✝¹ : Module R E
F : Type u_10
inst✝ : AddCommMonoid F
φ : MultilinearMap R s E
r : R
x z y : ⨂[R] (i : ι), s i
ihz : (liftAux φ) (r • z) = r • (liftAux φ) z
ihy : (liftAux φ) (r • y) = r • (liftAux φ) y
⊢ (liftAux φ) (r • (z + y)) = r • (liftAux φ) (z + y)
```

## Proof so far (4 tactics)
```lean
refine' PiTensorProduct.induction_on' x _ _
intro z f
rw [smul_tprodCoeff' r z f, liftAux_tprodCoeff, liftAux_tprodCoeff, smul_assoc]
intro z y ihz ihy
```

## Theorem
`PiTensorProduct.liftAux.smul` in `Mathlib/LinearAlgebra/PiTensorProduct.lean`

## Premises used in the next tactic
- `smul_add`
- `PiTensorProduct.liftAux`
- `AddMonoidHom.map_add`
- `PiTensorProduct.liftAux`
- `AddMonoidHom.map_add`
- `smul_add`

## Premise signatures
### `smul_add` (commanddeclaration)
```lean
theorem smul_add (a : M) (b₁ b₂ : A) : a • (b₁ + b₂) = a • b₁ + a • b₂
```

### `PiTensorProduct.liftAux` (commanddeclaration)
```lean
def liftAux (φ : MultilinearMap R s E) : (⨂[R] i, s i) →+ E
```

### `AddMonoidHom.map_add`
_(not found in premise corpus)_

### `PiTensorProduct.liftAux` (commanddeclaration)
```lean
def liftAux (φ : MultilinearMap R s E) : (⨂[R] i, s i) →+ E
```

### `AddMonoidHom.map_add`
_(not found in premise corpus)_

### `smul_add` (commanddeclaration)
```lean
theorem smul_add (a : M) (b₁ b₂ : A) : a • (b₁ + b₂) = a • b₁ + a • b₂
```

## Premise full source (with proof)
### `smul_add` (commanddeclaration) at `Mathlib/GroupTheory/GroupAction/Defs.lean`
```lean
theorem smul_add (a : M) (b₁ b₂ : A) : a • (b₁ + b₂) = a • b₁ + a • b₂ :=
  DistribSMul.smul_add _ _ _
```

### `PiTensorProduct.liftAux` (commanddeclaration) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
/-- Auxiliary function to constructing a linear map `(⨂[R] i, s i) → E` given a
`MultilinearMap R s E` with the property that its composition with the canonical
`MultilinearMap R s (⨂[R] i, s i)` is the given multilinear map. -/
def liftAux (φ : MultilinearMap R s E) : (⨂[R] i, s i) →+ E :=
  liftAddHom (fun p : R × Π i, s i ↦ p.1 • φ p.2)
    (fun z f i hf ↦ by simp_rw [map_coord_zero φ i hf, smul_zero])
    (fun f ↦ by simp_rw [zero_smul])
    (fun z f i m₁ m₂ ↦ by simp_rw [← smul_add, φ.map_add])
    (fun z₁ z₂ f ↦ by rw [← add_smul])
    fun z f i r ↦ by simp [φ.map_smul, smul_smul, mul_comm]
```

### `AddMonoidHom.map_add`
_(not found in premise corpus)_

### `PiTensorProduct.liftAux` (commanddeclaration) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
/-- Auxiliary function to constructing a linear map `(⨂[R] i, s i) → E` given a
`MultilinearMap R s E` with the property that its composition with the canonical
`MultilinearMap R s (⨂[R] i, s i)` is the given multilinear map. -/
def liftAux (φ : MultilinearMap R s E) : (⨂[R] i, s i) →+ E :=
  liftAddHom (fun p : R × Π i, s i ↦ p.1 • φ p.2)
    (fun z f i hf ↦ by simp_rw [map_coord_zero φ i hf, smul_zero])
    (fun f ↦ by simp_rw [zero_smul])
    (fun z f i m₁ m₂ ↦ by simp_rw [← smul_add, φ.map_add])
    (fun z₁ z₂ f ↦ by rw [← add_smul])
    fun z f i r ↦ by simp [φ.map_smul, smul_smul, mul_comm]
```

### `AddMonoidHom.map_add`
_(not found in premise corpus)_

### `smul_add` (commanddeclaration) at `Mathlib/GroupTheory/GroupAction/Defs.lean`
```lean
theorem smul_add (a : M) (b₁ b₂ : A) : a • (b₁ + b₂) = a • b₁ + a • b₂ :=
  DistribSMul.smul_add _ _ _
```

## Transitive premise context (1-hop, 9/9 premises, ≈1003 tokens)
### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
```

### `MultilinearMap` (commanddeclaration) at `Mathlib/LinearAlgebra/Multilinear/Basic.lean`
```lean
/-- Multilinear maps over the ring `R`, from `∀ i, M₁ i` to `M₂` where `M₁ i` and `M₂` are modules
over `R`. -/
structure MultilinearMap (R : Type uR) {ι : Type uι} (M₁ : ι → Type v₁) (M₂ : Type v₂) [Semiring R]
  [∀ i, AddCommMonoid (M₁ i)] [AddCommMonoid M₂] [∀ i, Module R (M₁ i)] [Module R M₂] where
  /-- The underlying multivariate function of a multilinear map. -/
  toFun : (∀ i, M₁ i) → M₂
  /-- A multilinear map is additive in every argument. -/
  map_add' :
    ∀ [DecidableEq ι] (m : ∀ i, M₁ i) (i : ι) (x y : M₁ i),
      toFun (update m i (x + y)) = toFun (update m i x) + toFun (update m i y)
  /-- A multilinear map is compatible with scalar multiplication in every argument. -/
  map_smul' :
    ∀ [DecidableEq ι] (m : ∀ i, M₁ i) (i : ι) (c : R) (x : M₁ i),
      toFun (update m i (c • x)) = c • toFun (update m i x)
```

### `Stream'.composition` (commanddeclaration) at `Mathlib/Data/Stream/Init.lean`
```lean
theorem composition (g : Stream' (β → δ)) (f : Stream' (α → β)) (s : Stream' α) :
    pure comp ⊛ g ⊛ f ⊛ s = g ⊛ (f ⊛ s) :=
  rfl
```

### `CategoryTheory.ShortComplex.RightHomologyData.IsPreservedBy.hf` (commanddeclaration) at `Mathlib/Algebra/Homology/ShortComplex/PreservesHomology.lean`
```lean
/-- When a right homology data is preserved by a functor `F`, this functor
preserves the cokernel of `S.f : S.X₁ ⟶ S.X₂`. -/
def IsPreservedBy.hf : PreservesColimit (parallelPair S.f 0) F :=
  @IsPreservedBy.f _ _ _ _ _ _ _ h F _ _

/-- When a right homology data `h` is preserved by a functor `F`, this functor
preserves the kernel of `h.g' : h.Q ⟶ S.X₃`. -/
```

### `smul_zero` (commanddeclaration) at `Mathlib/GroupTheory/GroupAction/Defs.lean`
```lean
@[simp]
theorem smul_zero (a : M) : a • (0 : A) = 0 :=
  SMulZeroClass.smul_zero _
```

### `zero_smul` (commanddeclaration) at `Mathlib/Algebra/SMulWithZero.lean`
```lean
@[simp]
theorem zero_smul (m : M) : (0 : R) • m = 0 :=
  SMulWithZero.zero_smul m
```

### `add_smul` (commanddeclaration) at `Mathlib/Algebra/Module/Basic.lean`
```lean
theorem add_smul : (r + s) • x = r • x + s • x :=
  Module.add_smul r s x
```

### `smul_smul` (commanddeclaration) at `Mathlib/GroupTheory/GroupAction/Defs.lean`
```lean
@[to_additive]
theorem smul_smul (a₁ a₂ : M) (b : α) : a₁ • a₂ • b = (a₁ * a₂) • b :=
  (mul_smul _ _ _).symm
```

### `mul_comm` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive]
theorem mul_comm : ∀ a b : G, a * b = b * a := CommMagma.mul_comm
```
