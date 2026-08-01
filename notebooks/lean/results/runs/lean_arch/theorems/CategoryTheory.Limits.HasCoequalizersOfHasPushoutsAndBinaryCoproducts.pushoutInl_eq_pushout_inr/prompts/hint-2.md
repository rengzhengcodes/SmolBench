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
