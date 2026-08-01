## Current goal
```
⊢ IsIso (Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val))) ↔
    IsIso { val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) }
```

## Full tactic state
```
C : Type u
inst✝² : Category.{v, u} C
J : GrothendieckTopology C
A : Type u'
inst✝¹ : Category.{v', u'} A
inst✝ : ConcreteCategory A
F G : Sheaf J (Type w)
f : F ⟶ G
⊢ IsIso (Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val))) ↔
    IsIso { val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) }
```

## Proof so far (1 tactic)
```lean
rw [imageSheafι, isLocallySurjective_iff_imagePresheaf_sheafify_eq_top',
  Subpresheaf.eq_top_iff_isIso]
```

## Theorem
`CategoryTheory.isLocallySurjective_iff_isIso` in `Mathlib/CategoryTheory/Sites/Surjective.lean`

## Premises used in the next tactic
- `CategoryTheory.isIso_of_reflects_iso`
- `CategoryTheory.GrothendieckTopology.imageSheafι`
- `CategoryTheory.sheafToPresheaf`
- `CategoryTheory.Functor.map_isIso`
- `CategoryTheory.sheafToPresheaf`

## Premise signatures
### `CategoryTheory.isIso_of_reflects_iso` (commanddeclaration)
```lean
theorem isIso_of_reflects_iso {A B : C} (f : A ⟶ B) (F : C ⥤ D) [IsIso (F.map f)]
    [ReflectsIsomorphisms F] : IsIso f
```

### `CategoryTheory.GrothendieckTopology.imageSheafι` (commanddeclaration)
```lean
@[simps]
def imageSheafι {F F' : Sheaf J (Type w)} (f : F ⟶ F') : imageSheaf f ⟶ F'
```

### `CategoryTheory.sheafToPresheaf` (commanddeclaration)
```lean
@[simps]
def sheafToPresheaf : Sheaf J A ⥤ Cᵒᵖ ⥤ A where
  obj
```

### `CategoryTheory.Functor.map_isIso` (commanddeclaration)
```lean
instance map_isIso (F : C ⥤ D) (f : X ⟶ Y) [IsIso f] : IsIso (F.map f)
```

### `CategoryTheory.sheafToPresheaf` (commanddeclaration)
```lean
@[simps]
def sheafToPresheaf : Sheaf J A ⥤ Cᵒᵖ ⥤ A where
  obj
```

## Premise full source (with proof)
### `CategoryTheory.isIso_of_reflects_iso` (commanddeclaration) at `Mathlib/CategoryTheory/Functor/ReflectsIso.lean`
```lean
/-- If `F` reflects isos and `F.map f` is an iso, then `f` is an iso. -/
theorem isIso_of_reflects_iso {A B : C} (f : A ⟶ B) (F : C ⥤ D) [IsIso (F.map f)]
    [ReflectsIsomorphisms F] : IsIso f :=
  ReflectsIsomorphisms.reflects F f
```

### `CategoryTheory.GrothendieckTopology.imageSheafι` (commanddeclaration) at `Mathlib/CategoryTheory/Sites/Subsheaf.lean`
```lean
/-- The inclusion of the image sheaf to the target. -/
@[simps]
def imageSheafι {F F' : Sheaf J (Type w)} (f : F ⟶ F') : imageSheaf f ⟶ F' :=
  ⟨Subpresheaf.ι _⟩
```

### `CategoryTheory.sheafToPresheaf` (commanddeclaration) at `Mathlib/CategoryTheory/Sites/Sheaf.lean`
```lean
/-- The inclusion functor from sheaves to presheaves. -/
@[simps]
def sheafToPresheaf : Sheaf J A ⥤ Cᵒᵖ ⥤ A where
  obj := Sheaf.val
  map f := f.val
  map_id _ := rfl
  map_comp _ _ := rfl
```

### `CategoryTheory.Functor.map_isIso` (commanddeclaration) at `Mathlib/CategoryTheory/Iso.lean`
```lean
instance map_isIso (F : C ⥤ D) (f : X ⟶ Y) [IsIso f] : IsIso (F.map f) :=
  IsIso.of_iso <| F.mapIso (asIso f)
```

### `CategoryTheory.sheafToPresheaf` (commanddeclaration) at `Mathlib/CategoryTheory/Sites/Sheaf.lean`
```lean
/-- The inclusion functor from sheaves to presheaves. -/
@[simps]
def sheafToPresheaf : Sheaf J A ⥤ Cᵒᵖ ⥤ A where
  obj := Sheaf.val
  map f := f.val
  map_id _ := rfl
  map_comp _ _ := rfl
```
