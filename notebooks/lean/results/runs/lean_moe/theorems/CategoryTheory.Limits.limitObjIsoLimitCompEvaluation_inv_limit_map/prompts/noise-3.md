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

## Filler (hint:2 → hint:3 token-match, ≈601 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
