## Current goal
```
⊢ Epi f
```

## Full tactic state
```
C : Type u₁
D : Type u₂
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
F : C ⥤ D
X Y : C
f : X ⟶ Y
inst✝¹ : ReflectsColimit (span f f) F
inst✝ : Epi (F.map f)
this : IsColimit (PushoutCocone.mk (F.map (𝟙 Y)) (F.map (𝟙 Y)) ⋯)
⊢ Epi f
```

## Proof so far (2 tactics)
```lean
have := PushoutCocone.isColimitMkIdId (F.map f)
simp_rw [← F.map_id] at this
```

## Theorem
`CategoryTheory.reflects_epi_of_reflectsColimit` in `Mathlib/CategoryTheory/Limits/Constructions/EpiMono.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.PushoutCocone.epi_of_isColimitMkIdId`
- `CategoryTheory.Limits.isColimitOfIsColimitPushoutCoconeMap`

## Premise signatures
### `CategoryTheory.Limits.PushoutCocone.epi_of_isColimitMkIdId` (commanddeclaration)
```lean
theorem epi_of_isColimitMkIdId (f : X ⟶ Y)
    (t : IsColimit (mk (𝟙 Y) (𝟙 Y) rfl : PushoutCocone f f)) : Epi f
```

### `CategoryTheory.Limits.isColimitOfIsColimitPushoutCoconeMap` (commanddeclaration)
```lean
def isColimitOfIsColimitPushoutCoconeMap [ReflectsColimit (span f g) G]
    (l : IsColimit (PushoutCocone.mk (G.map h) (G.map k) (show G.map f ≫ G.map h =
      G.map g ≫ G.map k from by simp only [← G.map_comp,comm]))) :
    IsColimit (PushoutCocone.mk h k comm)
```

## Premise full source (with proof)
### `CategoryTheory.Limits.PushoutCocone.epi_of_isColimitMkIdId` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- `f` is an epi if the pushout cocone `(𝟙 X, 𝟙 X)` is a colimit for the pair `(f, f)`.
The converse is given in `PushoutCocone.isColimitMkIdId`.
-/
theorem epi_of_isColimitMkIdId (f : X ⟶ Y)
    (t : IsColimit (mk (𝟙 Y) (𝟙 Y) rfl : PushoutCocone f f)) : Epi f :=
  ⟨fun {Z} g h eq => by
    rcases PushoutCocone.IsColimit.desc' t _ _ eq with ⟨_, rfl, rfl⟩
    rfl⟩
```

### `CategoryTheory.Limits.isColimitOfIsColimitPushoutCoconeMap` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Preserves/Shapes/Pullbacks.lean`
```lean
/-- The property of reflecting pushouts expressed in terms of binary cofans. -/
def isColimitOfIsColimitPushoutCoconeMap [ReflectsColimit (span f g) G]
    (l : IsColimit (PushoutCocone.mk (G.map h) (G.map k) (show G.map f ≫ G.map h =
      G.map g ≫ G.map k from by simp only [← G.map_comp,comm]))) :
    IsColimit (PushoutCocone.mk h k comm) :=
  ReflectsColimit.reflects ((isColimitMapCoconePushoutCoconeEquiv G comm).symm l)
```
