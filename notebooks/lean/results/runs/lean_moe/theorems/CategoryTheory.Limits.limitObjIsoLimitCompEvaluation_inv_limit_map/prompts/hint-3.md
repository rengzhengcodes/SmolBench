## Current goal
```
⊢ (limitObjIsoLimitCompEvaluation F i).inv ≫ (limit F).map f =
    limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F j).inv
```

## Full tactic state
```
C : Type u
inst✝⁴ : Category.{v, u} C
D : Type u'
inst✝³ : Category.{v', u'} D
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
inst✝ : HasLimitsOfShape J C
i j : K
F : J ⥤ K ⥤ C
f : i ⟶ j
⊢ (limitObjIsoLimitCompEvaluation F i).inv ≫ (limit F).map f =
    limMap (whiskerLeft F ((evaluation K C).map f)) ≫ (limitObjIsoLimitCompEvaluation F j).inv
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Limits.limitObjIsoLimitCompEvaluation_inv_limit_map` in `Mathlib/CategoryTheory/Limits/FunctorCategory.lean`

## Premises used in the next tactic
- `CategoryTheory.Iso.inv_comp_eq`
- `CategoryTheory.Category.assoc`
- `CategoryTheory.Iso.eq_comp_inv`
- `CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom`

## Premise signatures
### `CategoryTheory.Iso.inv_comp_eq` (commanddeclaration)
```lean
theorem inv_comp_eq (α : X ≅ Y) {f : X ⟶ Z} {g : Y ⟶ Z} : α.inv ≫ f = g ↔ f = α.hom ≫ g
```

### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Iso.eq_comp_inv` (commanddeclaration)
```lean
theorem eq_comp_inv (α : X ≅ Y) {f : Z ⟶ Y} {g : Z ⟶ X} : g = f ≫ α.inv ↔ g ≫ α.hom = f
```

### `CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem limit_map_limitObjIsoLimitCompEvaluation_hom [HasLimitsOfShape J C] {i j : K}
    (F : J ⥤ K ⥤ C) (f : i ⟶ j) : (limit F).map f ≫ (limitObjIsoLimitCompEvaluation _ _).hom =
    (limitObjIsoLimitCompEvaluation _ _).hom ≫ limMap (whiskerLeft _ ((evaluation _ _).map f))
```

## Premise full source (with proof)
### `CategoryTheory.Iso.inv_comp_eq` (commanddeclaration) at `Mathlib/CategoryTheory/Iso.lean`
```lean
theorem inv_comp_eq (α : X ≅ Y) {f : X ⟶ Z} {g : Y ⟶ Z} : α.inv ≫ f = g ↔ f = α.hom ≫ g :=
  ⟨fun H => by simp [H.symm], fun H => by simp [H]⟩
```

### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Iso.eq_comp_inv` (commanddeclaration) at `Mathlib/CategoryTheory/Iso.lean`
```lean
theorem eq_comp_inv (α : X ≅ Y) {f : Z ⟶ Y} {g : Z ⟶ X} : g = f ≫ α.inv ↔ g ≫ α.hom = f :=
  (comp_inv_eq α.symm).symm
```

### `CategoryTheory.Limits.limit_map_limitObjIsoLimitCompEvaluation_hom` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/FunctorCategory.lean`
```lean
@[reassoc (attr := simp)]
theorem limit_map_limitObjIsoLimitCompEvaluation_hom [HasLimitsOfShape J C] {i j : K}
    (F : J ⥤ K ⥤ C) (f : i ⟶ j) : (limit F).map f ≫ (limitObjIsoLimitCompEvaluation _ _).hom =
    (limitObjIsoLimitCompEvaluation _ _).hom ≫ limMap (whiskerLeft _ ((evaluation _ _).map f)) := by
  ext
  dsimp
  simp
```

## Transitive premise context (1-hop, 5/5 premises, ≈576 tokens)
### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```

### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `CategoryTheory.Limits.HasLimitsOfShape` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
/-- `C` has limits of shape `J` if there exists a limit for every functor `F : J ⥤ C`. -/
class HasLimitsOfShape : Prop where
  /-- All functors `F : J ⥤ C` from `J` have limits -/
  has_limit : ∀ F : J ⥤ C, HasLimit F := by infer_instance
```

### `CategoryTheory.Limits.limitObjIsoLimitCompEvaluation` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/FunctorCategory.lean`
```lean
/-- If `F : J ⥤ K ⥤ C` is a functor into a functor category which has a limit,
then the evaluation of that limit at `k` is the limit of the evaluations of `F.obj j` at `k`.
-/
def limitObjIsoLimitCompEvaluation [HasLimitsOfShape J C] (F : J ⥤ K ⥤ C) (k : K) :
    (limit F).obj k ≅ limit (F ⋙ (evaluation K C).obj k) :=
  preservesLimitIso ((evaluation K C).obj k) F
```

### `CategoryTheory.Limits.limMap` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
/-- Functoriality of limits.

Usually this morphism should be accessed through `lim.map`,
but may be needed separately when you have specified limits for the source and target functors,
but not necessarily for all functors of shape `J`.
-/
def limMap {F G : J ⥤ C} [HasLimit F] [HasLimit G] (α : F ⟶ G) : limit F ⟶ limit G :=
  IsLimit.map _ (limit.isLimit G) α
```
