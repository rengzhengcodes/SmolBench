## Current goal
```
⊢ fieldRange f = E
```

## Full tactic state
```
F : Type u_1
K : Type u_2
inst✝¹⁹ : Field F
inst✝¹⁸ : Field K
inst✝¹⁷ : Algebra F K
K₁ : Type u_3
K₂ : Type u_4
K₃ : Type u_5
inst✝¹⁶ : Field F
inst✝¹⁵ : Field K₁
inst✝¹⁴ : Field K₂
inst✝¹³ : Field K₃
inst✝¹² : Algebra F K₁
inst✝¹¹ : Algebra F K₂
inst✝¹⁰ : Algebra F K₃
ϕ : K₁ →ₐ[F] K₂
χ : K₁ ≃ₐ[F] K₂
ψ : K₂ →ₐ[F] K₃
ω : K₂ ≃ₐ[F] K₃
E✝ : Type u_6
inst✝⁹ : Field E✝
inst✝⁸ : Algebra F E✝
inst✝⁷ : Algebra E✝ K₁
inst✝⁶ : Algebra E✝ K₂
inst✝⁵ : Algebra E✝ K₃
inst✝⁴ : IsScalarTower F E✝ K₁
inst✝³ : IsScalarTower F E✝ K₂
inst✝² : IsScalarTower F E✝ K₃
inst✝¹ : Algebra F K
E : IntermediateField F K
inst✝ : Normal F ↥E
f : ↥E →ₐ[F] K
this : Algebra ↥E ↥E := Algebra.id ↥E
g : ↥E ≃ₐ[F] ↥E := restrictNormal' f ↥E
⊢ fieldRange f = E
```

## Proof so far (2 tactics)
```lean
letI : Algebra E E := Algebra.id E
let g := f.restrictNormal' E
```

## Theorem
`AlgHom.fieldRange_of_normal` in `Mathlib/FieldTheory/Normal.lean`

## Premises used in the next tactic
- `AlgHom.map_fieldRange`
- `AlgEquiv.fieldRange_eq_top`
- `AlgHom.fieldRange_eq_map`
- `IntermediateField.fieldRange_val`

## Premise signatures
### `AlgHom.map_fieldRange` (commanddeclaration)
```lean
theorem _root_.AlgHom.map_fieldRange {L : Type*} [Field L] [Algebra F L]
    (f : E →ₐ[F] K) (g : K →ₐ[F] L) : f.fieldRange.map g = (g.comp f).fieldRange
```

### `AlgEquiv.fieldRange_eq_top` (commanddeclaration)
```lean
@[simp]
theorem _root_.AlgEquiv.fieldRange_eq_top (f : E ≃ₐ[F] K) :
    (f : E →ₐ[F] K).fieldRange = ⊤
```

### `AlgHom.fieldRange_eq_map` (commanddeclaration)
```lean
theorem _root_.AlgHom.fieldRange_eq_map (f : E →ₐ[F] K) :
    f.fieldRange = IntermediateField.map f ⊤
```

### `IntermediateField.fieldRange_val` (commanddeclaration)
```lean
@[simp]
theorem fieldRange_val : S.val.fieldRange = S
```

## Premise full source (with proof)
### `AlgHom.map_fieldRange` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
theorem _root_.AlgHom.map_fieldRange {L : Type*} [Field L] [Algebra F L]
    (f : E →ₐ[F] K) (g : K →ₐ[F] L) : f.fieldRange.map g = (g.comp f).fieldRange :=
  SetLike.ext' (Set.range_comp g f).symm
```

### `AlgEquiv.fieldRange_eq_top` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
@[simp]
theorem _root_.AlgEquiv.fieldRange_eq_top (f : E ≃ₐ[F] K) :
    (f : E →ₐ[F] K).fieldRange = ⊤ :=
  AlgHom.fieldRange_eq_top.mpr f.surjective
```

### `AlgHom.fieldRange_eq_map` (commanddeclaration) at `Mathlib/FieldTheory/Adjoin.lean`
```lean
theorem _root_.AlgHom.fieldRange_eq_map (f : E →ₐ[F] K) :
    f.fieldRange = IntermediateField.map f ⊤ :=
  SetLike.ext' Set.image_univ.symm
```

### `IntermediateField.fieldRange_val` (commanddeclaration) at `Mathlib/FieldTheory/IntermediateField.lean`
```lean
@[simp]
theorem fieldRange_val : S.val.fieldRange = S :=
  SetLike.ext' Subtype.range_val
```

## Transitive premise context (1-hop, 7/7 premises, ≈792 tokens)
### `Field` (commanddeclaration) at `Mathlib/Algebra/Field/Defs.lean`
```lean
/-- A `Field` is a `CommRing` with multiplicative inverses for nonzero elements.

An instance of `Field K` includes maps `ratCast : ℚ → K` and `qsmul : ℚ → K → K`.
Those two fields are needed to implement the `DivisionRing K → Algebra ℚ K` instance since we need
to control the specific definitions for some special cases of `K` (in particular `K = ℚ` itself).
See also note [forgetful inheritance].

If the field has positive characteristic `p`, our division by zero convention forces
`ratCast (1 / p) = 1 / 0 = 0`. -/
class Field (K : Type u) extends CommRing K, DivisionRing K
```

### `Algebra` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- An associative unital `R`-algebra is a semiring `A` equipped with a map into its center `R → A`.

See the implementation notes in this file for discussion of the details of this definition.
-/
-- Porting note: unsupported @[nolint has_nonempty_instance]
class Algebra (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] extends SMul R A,
  R →+* A where
  commutes' : ∀ r x, toRingHom r * x = x * toRingHom r
  smul_def' : ∀ r x, r • x = toRingHom r * x
```

### `SetLike.ext'` (commanddeclaration) at `Mathlib/Data/SetLike/Basic.lean`
```lean
theorem ext' (h : (p : Set B) = q) : p = q :=
  coe_injective h
```

### `Set.range_comp` (commanddeclaration) at `Mathlib/Data/Set/Image.lean`
```lean
theorem range_comp (g : α → β) (f : ι → α) : range (g ∘ f) = g '' range f := by aesop
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `IntermediateField.map` (commanddeclaration) at `Mathlib/FieldTheory/IntermediateField.lean`
```lean
/-- Given `f : L →ₐ[K] L'`, `S.map f` is the intermediate field between `K` and `L'`
such that `x ∈ S ↔ f x ∈ S.map f`. -/
def map (f : L →ₐ[K] L') (S : IntermediateField K L) : IntermediateField K L' where
  __ := S.toSubalgebra.map f
  inv_mem' := by
    rintro _ ⟨x, hx, rfl⟩
    exact ⟨x⁻¹, S.inv_mem hx, map_inv₀ f x⟩
```

### `Subtype.range_val` (commanddeclaration) at `Mathlib/Data/Set/Image.lean`
```lean
/-- A variant of `range_coe`. Try to use `range_coe` if possible.
  This version is useful when defining a new type that is defined as the subtype of something.
  In that case, the coercion doesn't fire anymore. -/
theorem range_val {s : Set α} : range (Subtype.val : s → α) = s :=
  range_coe
```
