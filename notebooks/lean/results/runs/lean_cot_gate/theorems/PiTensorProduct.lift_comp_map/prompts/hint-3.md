## Current goal
```
⊢ (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ =
    (LinearMap.compMultilinearMap (lift (compLinearMap h f)) (tprod R)) x✝
```

## Full tactic state
```
case H.H
ι : Type u_1
ι₂ : Type u_2
ι₃ : Type u_3
R : Type u_4
inst✝¹¹ : CommSemiring R
R₁ : Type u_5
R₂ : Type u_6
s : ι → Type u_7
inst✝¹⁰ : (i : ι) → AddCommMonoid (s i)
inst✝⁹ : (i : ι) → Module R (s i)
M : Type u_8
inst✝⁸ : AddCommMonoid M
inst✝⁷ : Module R M
E : Type u_9
inst✝⁶ : AddCommMonoid E
inst✝⁵ : Module R E
F : Type u_10
inst✝⁴ : AddCommMonoid F
t : ι → Type u_11
t' : ι → Type u_12
inst✝³ : (i : ι) → AddCommMonoid (t i)
inst✝² : (i : ι) → Module R (t i)
inst✝¹ : (i : ι) → AddCommMonoid (t' i)
inst✝ : (i : ι) → Module R (t' i)
g : (i : ι) → t i →ₗ[R] t' i
f : (i : ι) → s i →ₗ[R] t i
h : MultilinearMap R t E
x✝ : (i : ι) → s i
⊢ (LinearMap.compMultilinearMap (lift h ∘ₗ map f) (tprod R)) x✝ =
    (LinearMap.compMultilinearMap (lift (compLinearMap h f)) (tprod R)) x✝
```

## Proof so far (1 tactic)
```lean
ext
```

## Theorem
`PiTensorProduct.lift_comp_map` in `Mathlib/LinearAlgebra/PiTensorProduct.lean`

## Premises used in the next tactic
- `LinearMap.compMultilinearMap_apply`
- `LinearMap.coe_comp`
- `Function.comp_apply`
- `PiTensorProduct.map_tprod`
- `PiTensorProduct.lift.tprod`
- `MultilinearMap.compLinearMap_apply`

## Premise signatures
### `LinearMap.compMultilinearMap_apply` (commanddeclaration)
```lean
@[simp]
theorem compMultilinearMap_apply (g : M₂ →ₗ[R] M₃) (f : MultilinearMap R M₁ M₂) (m : ∀ i, M₁ i) :
    g.compMultilinearMap f m = g (f m)
```

### `LinearMap.coe_comp` (commanddeclaration)
```lean
@[simp, norm_cast]
theorem coe_comp : (f.comp g : M₁ → M₃) = f ∘ g
```

### `Function.comp_apply` (commanddeclaration)
```lean
@[simp] theorem Function.comp_apply {f : β → δ} {g : α → β} {x : α} : comp f g x = f (g x)
```

### `PiTensorProduct.map_tprod` (lemma)
```lean
@[simp] lemma map_tprod (x : Π i, s i) :
    map f (tprod R x) = tprod R fun i ↦ f i (x i)
```

### `PiTensorProduct.lift.tprod` (commanddeclaration)
```lean
@[simp]
theorem lift.tprod (f : Π i, s i) : lift φ (tprod R f) = φ f
```

### `MultilinearMap.compLinearMap_apply` (commanddeclaration)
```lean
@[simp]
theorem compLinearMap_apply (g : MultilinearMap R M₁' M₂) (f : ∀ i, M₁ i →ₗ[R] M₁' i)
    (m : ∀ i, M₁ i) : g.compLinearMap f m = g fun i => f i (m i)
```

## Premise full source (with proof)
### `LinearMap.compMultilinearMap_apply` (commanddeclaration) at `Mathlib/LinearAlgebra/Multilinear/Basic.lean`
```lean
@[simp]
theorem compMultilinearMap_apply (g : M₂ →ₗ[R] M₃) (f : MultilinearMap R M₁ M₂) (m : ∀ i, M₁ i) :
    g.compMultilinearMap f m = g (f m) :=
  rfl
```

### `LinearMap.coe_comp` (commanddeclaration) at `Mathlib/Algebra/Module/LinearMap/Basic.lean`
```lean
@[simp, norm_cast]
theorem coe_comp : (f.comp g : M₁ → M₃) = f ∘ g :=
  rfl
```

### `Function.comp_apply` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
@[simp] theorem Function.comp_apply {f : β → δ} {g : α → β} {x : α} : comp f g x = f (g x) := rfl
```

### `PiTensorProduct.map_tprod` (lemma) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
@[simp] lemma map_tprod (x : Π i, s i) :
    map f (tprod R x) = tprod R fun i ↦ f i (x i) :=
  lift.tprod _

-- No lemmas about associativity, because we don't have associativity of `PiTensorProduct` yet.
```

### `PiTensorProduct.lift.tprod` (commanddeclaration) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
@[simp]
theorem lift.tprod (f : Π i, s i) : lift φ (tprod R f) = φ f :=
  liftAux_tprod φ f
```

### `MultilinearMap.compLinearMap_apply` (commanddeclaration) at `Mathlib/LinearAlgebra/Multilinear/Basic.lean`
```lean
@[simp]
theorem compLinearMap_apply (g : MultilinearMap R M₁' M₂) (f : ∀ i, M₁ i →ₗ[R] M₁' i)
    (m : ∀ i, M₁ i) : g.compLinearMap f m = g fun i => f i (m i) :=
  rfl
```

## Transitive premise context (1-hop, 3/3 premises, ≈722 tokens)
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

### `PiTensorProduct` (commanddeclaration) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
/-- `PiTensorProduct R s` with `R` a commutative semiring and `s : ι → Type*` is the tensor
  product of all the `s i`'s. This is denoted by `⨂[R] i, s i`. -/
def PiTensorProduct : Type _ :=
  (addConGen (PiTensorProduct.Eqv R s)).Quotient
```

### `PiTensorProduct.liftAux_tprod` (commanddeclaration) at `Mathlib/LinearAlgebra/PiTensorProduct.lean`
```lean
theorem liftAux_tprod (φ : MultilinearMap R s E) (f : Π i, s i) : liftAux φ (tprod R f) = φ f := by
  simp only [liftAux, liftAddHom, tprod_eq_tprodCoeff_one, tprodCoeff, AddCon.coe_mk']
  -- The end of this proof was very different before leanprover/lean4#2644:
  -- rw [FreeAddMonoid.of, FreeAddMonoid.ofList, Equiv.refl_apply, AddCon.lift_coe]
  -- dsimp [FreeAddMonoid.lift, FreeAddMonoid.sumAux]
  -- show _ • _ = _
  -- rw [one_smul]
  erw [AddCon.lift_coe]
  erw [FreeAddMonoid.of]
  dsimp [FreeAddMonoid.ofList]
  rw [← one_smul R (φ f)]
  erw [Equiv.refl_apply]
  convert one_smul R (φ f)
  simp
```
