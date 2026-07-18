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

## Transitive premise context (1-hop, 13/13 premises, ≈1859 tokens)
### `CategoryTheory.Adhesive` (commanddeclaration) at `Mathlib/CategoryTheory/Adhesive.lean`
```lean
/-- A category is adhesive if it has pushouts and pullbacks along monomorphisms,
and such pushouts are van Kampen. -/
class Adhesive (C : Type u) [Category.{v} C] : Prop where
  [hasPullback_of_mono_left : ∀ {X Y S : C} (f : X ⟶ S) (g : Y ⟶ S) [Mono f], HasPullback f g]
  [hasPushout_of_mono_left : ∀ {X Y S : C} (f : S ⟶ X) (g : S ⟶ Y) [Mono f], HasPushout f g]
  van_kampen : ∀ {W X Y Z : C} {f : W ⟶ X} {g : W ⟶ Y} {h : X ⟶ Z} {i : Y ⟶ Z} [Mono f]
    (H : IsPushout f g h i), H.IsVanKampen
```

### `CategoryTheory.Mono` (commanddeclaration) at `Mathlib/CategoryTheory/Category/Basic.lean`
```lean
/-- A morphism `f` is a monomorphism if it can be cancelled when postcomposed:
`g ≫ f = h ≫ f` implies `g = h`.

See <https://stacks.math.columbia.edu/tag/003B>.
-/
class Mono (f : X ⟶ Y) : Prop where
  /-- A morphism `f` is a monomorphism if it can be cancelled when postcomposed. -/
  right_cancellation : ∀ {Z : C} (g h : Z ⟶ X), g ≫ f = h ≫ f → g = h
```

### `CategoryTheory.Limits.HasPullback` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- `HasPullback f g` represents a particular choice of limiting cone
for the pair of morphisms `f : X ⟶ Z` and `g : Y ⟶ Z`.
-/
abbrev HasPullback {X Y Z : C} (f : X ⟶ Z) (g : Y ⟶ Z) :=
  HasLimit (cospan f g)
```

### `CategoryTheory.Limits.HasPushout` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- `HasPushout f g` represents a particular choice of colimiting cocone
for the pair of morphisms `f : X ⟶ Y` and `g : X ⟶ Z`.
-/
abbrev HasPushout {X Y Z : C} (f : X ⟶ Y) (g : X ⟶ Z) :=
  HasColimit (span f g)
```

### `CategoryTheory.Limits.PreservesLimitsOfShape` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Preserves/Basic.lean`
```lean
/-- We say that `F` preserves limits of shape `J` if `F` preserves limits for every diagram
    `K : J ⥤ C`, i.e., `F` maps limit cones over `K` to limit cones. -/
class PreservesLimitsOfShape (J : Type w) [Category.{w'} J] (F : C ⥤ D) where
  preservesLimit : ∀ {K : J ⥤ C}, PreservesLimit K F := by infer_instance
```

### `CategoryTheory.Limits.WalkingCospan` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- The type of objects for the diagram indexing a pullback, defined as a special case of
`WidePullbackShape`. -/
abbrev WalkingCospan : Type :=
  WidePullbackShape WalkingPair
```

### `CategoryTheory.Limits.ReflectsLimitsOfShape` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Preserves/Basic.lean`
```lean
/-- A functor `F : C ⥤ D` reflects limits of shape `J` if
whenever the image of a cone over some `K : J ⥤ C` under `F` is a limit cone in `D`,
the cone was already a limit cone in `C`.
Note that we do not assume a priori that `D` actually has any limits.
-/
class ReflectsLimitsOfShape (J : Type w) [Category.{w'} J] (F : C ⥤ D) where
  reflectsLimit : ∀ {K : J ⥤ C}, ReflectsLimit K F := by infer_instance
```

### `CategoryTheory.Limits.PreservesColimitsOfShape` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Preserves/Basic.lean`
```lean
/-- We say that `F` preserves colimits of shape `J` if `F` preserves colimits for every diagram
    `K : J ⥤ C`, i.e., `F` maps colimit cocones over `K` to colimit cocones. -/
class PreservesColimitsOfShape (J : Type w) [Category.{w'} J] (F : C ⥤ D) where
  preservesColimit : ∀ {K : J ⥤ C}, PreservesColimit K F := by infer_instance
```

### `CategoryTheory.Limits.WalkingSpan` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- The type of objects for the diagram indexing a pushout, defined as a special case of
`WidePushoutShape`.
-/
abbrev WalkingSpan : Type :=
  WidePushoutShape WalkingPair
```

### `CategoryTheory.Limits.ReflectsColimitsOfShape` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Preserves/Basic.lean`
```lean
/-- A functor `F : C ⥤ D` reflects colimits of shape `J` if
whenever the image of a cocone over some `K : J ⥤ C` under `F` is a colimit cocone in `D`,
the cocone was already a colimit cocone in `C`.
Note that we do not assume a priori that `D` actually has any colimits.
-/
class ReflectsColimitsOfShape (J : Type w) [Category.{w'} J] (F : C ⥤ D) where
  reflectsColimit : ∀ {K : J ⥤ C}, ReflectsColimit K F := by infer_instance
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

### `CategoryTheory.Limits.diagramIsoSpan` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- Every diagram indexing a pushout is naturally isomorphic (actually, equal) to a `span` -/
-- @[simps (config := { rhsMd := semireducible })]  Porting note: no semireducible
@[simps!]
def diagramIsoSpan (F : WalkingSpan ⥤ C) : F ≅ span (F.map fst) (F.map snd) :=
  NatIso.ofComponents
  (fun j => eqToIso (by rcases j with (⟨⟩ | ⟨⟨⟩⟩) <;> rfl))
  (by rintro (⟨⟩ | ⟨⟨⟩⟩) (⟨⟩ | ⟨⟨⟩⟩) f <;> cases f <;> dsimp <;> simp)
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```
