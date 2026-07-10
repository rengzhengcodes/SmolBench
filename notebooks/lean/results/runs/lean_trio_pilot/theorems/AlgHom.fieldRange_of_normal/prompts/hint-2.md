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
