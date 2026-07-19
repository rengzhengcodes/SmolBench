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

## Transitive premise context (1-hop, 7/7 premises, ≈1100 tokens)
### `CategoryTheory.Limits.IsColimit` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/IsLimit.lean`
```lean
/-- A cocone `t` on `F` is a colimit cocone if each cocone on `F` admits a unique
cocone morphism from `t`.

See <https://stacks.math.columbia.edu/tag/002F>.
-/
-- Porting note: remove @[nolint has_nonempty_instance]
structure IsColimit (t : Cocone F) where
  /-- `t.pt` maps to all other cocone covertices -/
  desc : ∀ s : Cocone F, t.pt ⟶ s.pt
  /-- The map `desc` makes the diagram with the natural transformations commute -/
  fac : ∀ (s : Cocone F) (j : J), t.ι.app j ≫ desc s = s.ι.app j := by aesop_cat
  /-- `desc` is the unique such map -/
  uniq :
    ∀ (s : Cocone F) (m : t.pt ⟶ s.pt) (_ : ∀ j : J, t.ι.app j ≫ m = s.ι.app j), m = desc s := by
    aesop_cat
```

### `CategoryTheory.Limits.PushoutCocone` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Pullbacks.lean`
```lean
/-- A pushout cocone is just a cocone on the span formed by two morphisms `f : X ⟶ Y` and
    `g : X ⟶ Z`.-/
abbrev PushoutCocone (f : X ⟶ Y) (g : X ⟶ Z) :=
  Cocone (span f g)
```

### `CategoryTheory.Epi` (commanddeclaration) at `Mathlib/CategoryTheory/Category/Basic.lean`
```lean
/-- A morphism `f` is an epimorphism if it can be cancelled when precomposed:
`f ≫ g = f ≫ h` implies `g = h`.

See <https://stacks.math.columbia.edu/tag/003B>.
-/
class Epi (f : X ⟶ Y) : Prop where
  /-- A morphism `f` is an epimorphism if it can be cancelled when precomposed. -/
  left_cancellation : ∀ {Z : C} (g h : Y ⟶ Z), f ≫ g = f ≫ h → g = h
```

### `CategoryTheory.Limits.ReflectsColimit` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Preserves/Basic.lean`
```lean
/-- A functor `F : C ⥤ D` reflects colimits for `K : J ⥤ C` if
whenever the image of a cocone over `K` under `F` is a colimit cocone in `D`,
the cocone was already a colimit cocone in `C`.
Note that we do not assume a priori that `D` actually has any colimits.
-/
class ReflectsColimit (K : J ⥤ C) (F : C ⥤ D) where
  reflects : ∀ {c : Cocone K}, IsColimit (F.mapCocone c) → IsColimit c
```

### `comm` (commanddeclaration) at `Mathlib/Order/RelClasses.lean`
```lean
theorem comm [IsSymm α r] {a b : α} : r a b ↔ r b a :=
  ⟨symm, symm⟩
```

### `CategoryTheory.Limits.isColimitMapCoconePushoutCoconeEquiv` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Preserves/Shapes/Pullbacks.lean`
```lean
/-- The map of a pushout cocone is a colimit iff the cofork consisting of the mapped morphisms is a
colimit. This essentially lets us commute `PushoutCocone.mk` with `Functor.mapCocone`. -/
def isColimitMapCoconePushoutCoconeEquiv :
    IsColimit (mapCocone G (PushoutCocone.mk h k comm)) ≃
      IsColimit
        (PushoutCocone.mk (G.map h) (G.map k) (by simp only [← G.map_comp, comm]) :
          PushoutCocone (G.map f) (G.map g)) :=
  (IsColimit.precomposeHomEquiv (diagramIsoSpan.{v₂} _).symm _).symm.trans <|
    IsColimit.equivIsoColimit <|
      Cocones.ext (Iso.refl _) <| by
        rintro (_ | _ | _) <;> dsimp <;>
          simp only [Category.comp_id, Category.id_comp, ← G.map_comp]
```

### `symm` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem symm [IsSymm α r] {a b : α} : a ≺ b → b ≺ a :=
  IsSymm.symm _ _
```
