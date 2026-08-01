## Current goal
```
⊢ Adhesive C
```

## Full tactic state
```
J : Type v'
inst✝⁸ : Category.{u', v'} J
C : Type u
inst✝⁷ : Category.{v, u} C
W X Y Z : C
f : W ⟶ X
g : W ⟶ Y
h : X ⟶ Z
i : Y ⟶ Z
D : Type u''
inst✝⁶ : Category.{v'', u''} D
F : C ⥤ D
inst✝⁵ : Adhesive D
inst✝⁴ : HasPullbacks C
inst✝³ : HasPushouts C
inst✝² : PreservesLimitsOfShape WalkingCospan F
inst✝¹ : PreservesColimitsOfShape WalkingSpan F
inst✝ : ReflectsIsomorphisms F
this✝ : ReflectsLimitsOfShape WalkingCospan F
this : ReflectsColimitsOfShape WalkingSpan F
⊢ Adhesive C
```

## Proof so far (2 tactics)
```lean
haveI : ReflectsLimitsOfShape WalkingCospan F :=
  reflectsLimitsOfShapeOfReflectsIsomorphisms
haveI : ReflectsColimitsOfShape WalkingSpan F :=
  reflectsColimitsOfShapeOfReflectsIsomorphisms
```

## Theorem
`CategoryTheory.adhesive_of_preserves_and_reflects_isomorphism` in `Mathlib/CategoryTheory/Adhesive.lean`

## Premises used in the next tactic
- `CategoryTheory.adhesive_of_preserves_and_reflects`

## Premise signatures
### `CategoryTheory.adhesive_of_preserves_and_reflects` (commanddeclaration)
```lean
theorem adhesive_of_preserves_and_reflects (F : C ⥤ D) [Adhesive D]
    [H₁ : ∀ {X Y S : C} (f : X ⟶ S) (g : Y ⟶ S) [Mono f], HasPullback f g]
    [H₂ : ∀ {X Y S : C} (f : S ⟶ X) (g : S ⟶ Y) [Mono f], HasPushout f g]
    [PreservesLimitsOfShape WalkingCospan F]
    [ReflectsLimitsOfShape WalkingCospan F]
    [PreservesColimitsOfShape WalkingSpan F]
    [ReflectsColimitsOfShape WalkingSpan F] :
    Adhesive C
```

## Premise full source (with proof)
### `CategoryTheory.adhesive_of_preserves_and_reflects` (commanddeclaration) at `Mathlib/CategoryTheory/Adhesive.lean`
```lean
theorem adhesive_of_preserves_and_reflects (F : C ⥤ D) [Adhesive D]
    [H₁ : ∀ {X Y S : C} (f : X ⟶ S) (g : Y ⟶ S) [Mono f], HasPullback f g]
    [H₂ : ∀ {X Y S : C} (f : S ⟶ X) (g : S ⟶ Y) [Mono f], HasPushout f g]
    [PreservesLimitsOfShape WalkingCospan F]
    [ReflectsLimitsOfShape WalkingCospan F]
    [PreservesColimitsOfShape WalkingSpan F]
    [ReflectsColimitsOfShape WalkingSpan F] :
    Adhesive C := by
  apply Adhesive.mk (hasPullback_of_mono_left := H₁) (hasPushout_of_mono_left := H₂)
  intros W X Y Z f g h i hf H
  rw [IsPushout.isVanKampen_iff]
  refine IsVanKampenColimit.of_mapCocone F ?_
  refine (IsVanKampenColimit.precompose_isIso_iff (diagramIsoSpan _).inv).mp ?_
  refine IsVanKampenColimit.of_iso ?_ (PushoutCocone.isoMk _).symm
  refine (IsPushout.isVanKampen_iff (H.map F)).mp ?_
  apply Adhesive.van_kampen
```
