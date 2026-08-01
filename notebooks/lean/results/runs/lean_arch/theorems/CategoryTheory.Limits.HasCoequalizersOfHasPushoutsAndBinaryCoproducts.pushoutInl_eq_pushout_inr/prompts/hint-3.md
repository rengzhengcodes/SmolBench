## Current goal
```
⊢ pushoutInl F = pushout.inr
```

## Full tactic state
```
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
G : C ⥤ D
inst✝¹ : HasBinaryCoproducts C
inst✝ : HasPushouts C
F : WalkingParallelPair ⥤ C
⊢ pushoutInl F = pushout.inr
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Limits.HasCoequalizersOfHasPushoutsAndBinaryCoproducts.pushoutInl_eq_pushout_inr` in `Mathlib/CategoryTheory/Limits/Constructions/Equalizers.lean`

## Premises used in the next tactic
- `CategoryTheory.whisker_eq`
- `CategoryTheory.Limits.coprod.inl`
- `CategoryTheory.Limits.pushout.condition`
- `CategoryTheory.Limits.HasCoequalizersOfHasPushoutsAndBinaryCoproducts.constructCoequalizer`

## Premise signatures
### `CategoryTheory.whisker_eq` (commanddeclaration)
```lean
theorem whisker_eq (f : X ⟶ Y) {g h : Y ⟶ Z} (w : g = h) : f ≫ g = f ≫ h
```

### `CategoryTheory.Limits.coprod.inl` (commanddeclaration)
```lean
abbrev coprod.inl {X Y : C} [HasBinaryCoproduct X Y] : X ⟶ X ⨿ Y
```

### `CategoryTheory.Limits.pushout.condition` (commanddeclaration)
```lean
@[reassoc]
theorem pushout.condition {X Y Z : C} {f : X ⟶ Y} {g : X ⟶ Z} [HasPushout f g] :
    f ≫ (pushout.inl : Y ⟶ pushout f g) = g ≫ pushout.inr
```

### `CategoryTheory.Limits.HasCoequalizersOfHasPushoutsAndBinaryCoproducts.constructCoequalizer` (commanddeclaration)
```lean
@[reducible]
def constructCoequalizer (F : WalkingParallelPair ⥤ C) : C
```

## Premise full source (with proof)
### `CategoryTheory.whisker_eq` (commanddeclaration) at `Mathlib/CategoryTheory/Category/Basic.lean`
```lean
/-- precompose an equation between morphisms by another morphism -/
theorem whisker_eq (f : X ⟶ Y) {g h : Y ⟶ Z} (w : g = h) : f ≫ g = f ≫ h := by rw [w]
```

### `CategoryTheory.Limits.coprod.inl` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
/-- The inclusion map from the first component of the coproduct. -/
abbrev coprod.inl {X Y : C} [HasBinaryCoproduct X Y] : X ⟶ X ⨿ Y :=
  colimit.ι (pair X Y) ⟨WalkingPair.left⟩
```

### `CategoryTheory.Limits.pushout.condition` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
@[reassoc]
theorem pushout.condition {X Y Z : C} {f : X ⟶ Y} {g : X ⟶ Z} [HasPushout f g] :
    f ≫ (pushout.inl : Y ⟶ pushout f g) = g ≫ pushout.inr :=
  PushoutCocone.condition _
```

### `CategoryTheory.Limits.HasCoequalizersOfHasPushoutsAndBinaryCoproducts.constructCoequalizer` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Constructions/Equalizers.lean`
```lean
/-- Define the equalizing object -/
@[reducible]
def constructCoequalizer (F : WalkingParallelPair ⥤ C) : C :=
  pushout (coprod.desc (𝟙 _) (F.map WalkingParallelPairHom.left))
    (coprod.desc (𝟙 _) (F.map WalkingParallelPairHom.right))
```

## Transitive premise context (1-hop, 6/6 premises, ≈586 tokens)
### `CategoryTheory.Limits.Cocones.precompose` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Cones.lean`
```lean
/-- Functorially precompose a cocone for `F` by a natural transformation `G ⟶ F` to give a cocone
for `G`. -/
@[simps]
def precompose {G : J ⥤ C} (α : G ⟶ F) : Cocone F ⥤ Cocone G where
  obj c :=
    { pt := c.pt
      ι := α ≫ c.ι }
  map f := { hom := f.hom }
```

### `WeierstrassCurve.Affine.equation` (commanddeclaration) at `Mathlib/AlgebraicGeometry/EllipticCurve/Affine.lean`
```lean
/-- The proposition that an affine point $(x, y)$ lies in `W`. In other words, $W(x, y) = 0$. -/
@[pp_dot]
def equation (x y : R) : Prop :=
  (W.polynomial.eval <| C y).eval x = 0
```

### `DirectSum.component` (commanddeclaration) at `Mathlib/Algebra/DirectSum/Module.lean`
```lean
/-- The projection map onto one component, as a linear map. -/
def component (i : ι) : (⨁ i, M i) →ₗ[R] M i :=
  DFinsupp.lapply i
```

### `CategoryTheory.Limits.HasBinaryCoproduct` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
/-- An abbreviation for `HasColimit (pair X Y)`. -/
abbrev HasBinaryCoproduct (X Y : C) :=
  HasColimit (pair X Y)
```

### `CategoryTheory.Limits.HasPushout` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- `HasPushout f g` represents a particular choice of colimiting cocone
for the pair of morphisms `f : X ⟶ Y` and `g : X ⟶ Z`.
-/
abbrev HasPushout {X Y Z : C} (f : X ⟶ Y) (g : X ⟶ Z) :=
  HasColimit (span f g)
```

### `CategoryTheory.Limits.WalkingParallelPair` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Equalizers.lean`
```lean
/-- The type of objects for the diagram indexing a (co)equalizer. -/
inductive WalkingParallelPair : Type
  | zero
  | one
  deriving DecidableEq, Inhabited
```
