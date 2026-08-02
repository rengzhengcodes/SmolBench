## Current goal
```
⊢ (colimit.cocone (diagram J P X.unop ⋙ F)).ι.app W ≫
      (HasColimit.isoOfNatIso
          (NatIso.ofComponents
            (fun W =>
              IsLimit.conePointUniqueUpToIso
                  (isLimitOfPreserves F (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P))))
                  (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P) ⋙ F)) ≪≫
                HasLimit.isoOfNatIso (Cover.multicospanComp F P W.unop).symm)
            ⋯)).hom =
    ((IsLimit.conePointUniqueUpToIso
            (isLimitOfPreserves F (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P))))
            (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P) ⋙ F))).hom ≫
        (HasLimit.isoOfNatIso (Cover.multicospanComp F P W.unop).symm).hom) ≫
      colimit.ι (diagram J (P ⋙ F) X.unop) W
```

## Full tactic state
```
C : Type u
inst✝⁸ : Category.{v, u} C
J : GrothendieckTopology C
D : Type w₁
inst✝⁷ : Category.{max v u, w₁} D
E : Type w₂
inst✝⁶ : Category.{max v u, w₂} E
F : D ⥤ E
inst✝⁵ : ∀ (α β : Type (max v u)) (fst snd : β → α), HasLimitsOfShape (WalkingMulticospan fst snd) D
inst✝⁴ : ∀ (α β : Type (max v u)) (fst snd : β → α), HasLimitsOfShape (WalkingMulticospan fst snd) E
inst✝³ : (X : C) → (W : Cover J X) → (P : Cᵒᵖ ⥤ D) → PreservesLimit (MulticospanIndex.multicospan (Cover.index W P)) F
P : Cᵒᵖ ⥤ D
inst✝² : ∀ (X : C), HasColimitsOfShape (Cover J X)ᵒᵖ D
inst✝¹ : ∀ (X : C), HasColimitsOfShape (Cover J X)ᵒᵖ E
inst✝ : (X : C) → PreservesColimitsOfShape (Cover J X)ᵒᵖ F
X : Cᵒᵖ
W : (Cover J X.unop)ᵒᵖ
⊢ (colimit.cocone (diagram J P X.unop ⋙ F)).ι.app W ≫
      (HasColimit.isoOfNatIso
          (NatIso.ofComponents
            (fun W =>
              IsLimit.conePointUniqueUpToIso
                  (isLimitOfPreserves F (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P))))
                  (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P) ⋙ F)) ≪≫
                HasLimit.isoOfNatIso (Cover.multicospanComp F P W.unop).symm)
            ⋯)).hom =
    ((IsLimit.conePointUniqueUpToIso
            (isLimitOfPreserves F (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P))))
            (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P) ⋙ F))).hom ≫
        (HasLimit.isoOfNatIso (Cover.multicospanComp F P W.unop).symm).hom) ≫
      colimit.ι (diagram J (P ⋙ F) X.unop) W
```

## Proof so far (3 tactics)
```lean
delta diagramCompIso plusCompIso
simp only [IsColimit.descCoconeMorphism_hom, IsColimit.uniqueUpToIso_hom,
  Cocones.forget_map, Iso.trans_hom, NatIso.ofComponents_hom_app, Functor.mapIso_hom, ←
  Category.assoc]
erw [(isColimitOfPreserves F (colimit.isColimit (J.diagram P (unop X)))).fac]
```

## Theorem
`CategoryTheory.GrothendieckTopology.ι_plusCompIso_hom` in `Mathlib/CategoryTheory/Sites/CompatiblePlus.lean`

## Premises used in the next tactic
- `CategoryTheory.Category.assoc`
- `CategoryTheory.Limits.HasLimit.isoOfNatIso_hom_π`
- `CategoryTheory.Iso.symm_hom`
- `CategoryTheory.GrothendieckTopology.Cover.multicospanComp_hom_inv_left`
- `CategoryTheory.eqToHom_refl`
- `CategoryTheory.Category.comp_id`
- `CategoryTheory.Limits.limit.conePointUniqueUpToIso_hom_comp`
- `CategoryTheory.Functor.mapCone_π_app`
- `CategoryTheory.Limits.Multiequalizer.multifork_π_app_left`
- `CategoryTheory.Limits.Multiequalizer.lift_ι`
- `CategoryTheory.Functor.map_comp`
- `eq_self_iff_true`
- `CategoryTheory.Category.assoc`
- `CategoryTheory.Iso.trans_hom`
- `CategoryTheory.Iso.cancel_iso_hom_left`
- `CategoryTheory.NatIso.ofComponents_hom_app`
- `CategoryTheory.Limits.colimit.cocone_ι`
- `CategoryTheory.Category.assoc`
- `CategoryTheory.Limits.HasColimit.isoOfNatIso_ι_hom`

## Premise signatures
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.HasLimit.isoOfNatIso_hom_π` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem HasLimit.isoOfNatIso_hom_π {F G : J ⥤ C} [HasLimit F] [HasLimit G] (w : F ≅ G) (j : J) :
    (HasLimit.isoOfNatIso w).hom ≫ limit.π G j = limit.π F j ≫ w.hom.app j
```

### `CategoryTheory.Iso.symm_hom` (commanddeclaration)
```lean
@[simp]
theorem symm_hom (α : X ≅ Y) : α.symm.hom = α.inv
```

### `CategoryTheory.GrothendieckTopology.Cover.multicospanComp_hom_inv_left` (commanddeclaration)
```lean
@[simp]
theorem multicospanComp_hom_inv_left (P : Cᵒᵖ ⥤ A) {X : C} (S : J.Cover X) (a) :
    (S.multicospanComp F P).inv.app (WalkingMulticospan.left a) = eqToHom rfl
```

### `CategoryTheory.eqToHom_refl` (commanddeclaration)
```lean
@[simp]
theorem eqToHom_refl (X : C) (p : X = X) : eqToHom p = 𝟙 X
```

### `CategoryTheory.Category.comp_id`
_(not found in premise corpus)_

### `CategoryTheory.Limits.limit.conePointUniqueUpToIso_hom_comp` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem limit.conePointUniqueUpToIso_hom_comp {F : J ⥤ C} [HasLimit F] {c : Cone F} (hc : IsLimit c)
    (j : J) : (IsLimit.conePointUniqueUpToIso hc (limit.isLimit _)).hom ≫ limit.π F j = c.π.app j
```

### `CategoryTheory.Functor.mapCone_π_app`
_(not found in premise corpus)_

### `CategoryTheory.Limits.Multiequalizer.multifork_π_app_left` (commanddeclaration)
```lean
@[simp]
theorem multifork_π_app_left (a) :
    (Multiequalizer.multifork I).π.app (WalkingMulticospan.left a) = Multiequalizer.ι I a
```

### `CategoryTheory.Limits.Multiequalizer.lift_ι` (commanddeclaration)
```lean
@[reassoc] theorem lift_ι (W : C) (k : ∀ a, W ⟶ I.left a)
    (h : ∀ b, k (I.fstTo b) ≫ I.fst b = k (I.sndTo b) ≫ I.snd b) (a) :
    Multiequalizer.lift I _ k h ≫ Multiequalizer.ι I a = k _
```

### `CategoryTheory.Functor.map_comp`
_(not found in premise corpus)_

### `eq_self_iff_true` (commanddeclaration)
```lean
theorem eq_self_iff_true (a : α)  : a = a ↔ True
```

### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Iso.trans_hom`
_(not found in premise corpus)_

### `CategoryTheory.Iso.cancel_iso_hom_left` (commanddeclaration)
```lean
@[simp]
theorem cancel_iso_hom_left {X Y Z : C} (f : X ≅ Y) (g g' : Y ⟶ Z) :
    f.hom ≫ g = f.hom ≫ g' ↔ g = g'
```

### `CategoryTheory.NatIso.ofComponents_hom_app`
_(not found in premise corpus)_

### `CategoryTheory.Limits.colimit.cocone_ι` (commanddeclaration)
```lean
@[simp]
theorem colimit.cocone_ι {F : J ⥤ C} [HasColimit F] (j : J) :
    (colimit.cocone F).ι.app j = colimit.ι _ j
```

### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.HasColimit.isoOfNatIso_ι_hom` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem HasColimit.isoOfNatIso_ι_hom {F G : J ⥤ C} [HasColimit F] [HasColimit G] (w : F ≅ G)
    (j : J) : colimit.ι F j ≫ (HasColimit.isoOfNatIso w).hom = w.hom.app j ≫ colimit.ι G j
```

## Premise full source (with proof)
### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.HasLimit.isoOfNatIso_hom_π` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
@[reassoc (attr := simp)]
theorem HasLimit.isoOfNatIso_hom_π {F G : J ⥤ C} [HasLimit F] [HasLimit G] (w : F ≅ G) (j : J) :
    (HasLimit.isoOfNatIso w).hom ≫ limit.π G j = limit.π F j ≫ w.hom.app j :=
  IsLimit.conePointsIsoOfNatIso_hom_comp _ _ _ _
```

### `CategoryTheory.Iso.symm_hom` (commanddeclaration) at `Mathlib/CategoryTheory/Iso.lean`
```lean
@[simp]
theorem symm_hom (α : X ≅ Y) : α.symm.hom = α.inv :=
  rfl
```

### `CategoryTheory.GrothendieckTopology.Cover.multicospanComp_hom_inv_left` (commanddeclaration) at `Mathlib/CategoryTheory/Sites/Whiskering.lean`
```lean
@[simp]
theorem multicospanComp_hom_inv_left (P : Cᵒᵖ ⥤ A) {X : C} (S : J.Cover X) (a) :
    (S.multicospanComp F P).inv.app (WalkingMulticospan.left a) = eqToHom rfl :=
  rfl
```

### `CategoryTheory.eqToHom_refl` (commanddeclaration) at `Mathlib/CategoryTheory/EqToHom.lean`
```lean
@[simp]
theorem eqToHom_refl (X : C) (p : X = X) : eqToHom p = 𝟙 X :=
  rfl
```

### `CategoryTheory.Category.comp_id`
_(not found in premise corpus)_

### `CategoryTheory.Limits.limit.conePointUniqueUpToIso_hom_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
@[reassoc (attr := simp)]
theorem limit.conePointUniqueUpToIso_hom_comp {F : J ⥤ C} [HasLimit F] {c : Cone F} (hc : IsLimit c)
    (j : J) : (IsLimit.conePointUniqueUpToIso hc (limit.isLimit _)).hom ≫ limit.π F j = c.π.app j :=
  IsLimit.conePointUniqueUpToIso_hom_comp _ _ _
```

### `CategoryTheory.Functor.mapCone_π_app`
_(not found in premise corpus)_

### `CategoryTheory.Limits.Multiequalizer.multifork_π_app_left` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Multiequalizer.lean`
```lean
@[simp]
theorem multifork_π_app_left (a) :
    (Multiequalizer.multifork I).π.app (WalkingMulticospan.left a) = Multiequalizer.ι I a :=
  rfl
```

### `CategoryTheory.Limits.Multiequalizer.lift_ι` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Multiequalizer.lean`
```lean
@[reassoc] -- Porting note (#10618): simp can prove this, removed attribute
theorem lift_ι (W : C) (k : ∀ a, W ⟶ I.left a)
    (h : ∀ b, k (I.fstTo b) ≫ I.fst b = k (I.sndTo b) ≫ I.snd b) (a) :
    Multiequalizer.lift I _ k h ≫ Multiequalizer.ι I a = k _ :=
  limit.lift_π _ _
```

### `CategoryTheory.Functor.map_comp`
_(not found in premise corpus)_

### `eq_self_iff_true` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem eq_self_iff_true (a : α)  : a = a ↔ True  := iff_true_intro rfl
```

### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Iso.trans_hom`
_(not found in premise corpus)_

### `CategoryTheory.Iso.cancel_iso_hom_left` (commanddeclaration) at `Mathlib/CategoryTheory/Iso.lean`
```lean
@[simp]
theorem cancel_iso_hom_left {X Y Z : C} (f : X ≅ Y) (g g' : Y ⟶ Z) :
    f.hom ≫ g = f.hom ≫ g' ↔ g = g' := by
  simp only [cancel_epi]
```

### `CategoryTheory.NatIso.ofComponents_hom_app`
_(not found in premise corpus)_

### `CategoryTheory.Limits.colimit.cocone_ι` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
@[simp]
theorem colimit.cocone_ι {F : J ⥤ C} [HasColimit F] (j : J) :
    (colimit.cocone F).ι.app j = colimit.ι _ j :=
  rfl
```

### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.HasColimit.isoOfNatIso_ι_hom` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
@[reassoc (attr := simp)]
theorem HasColimit.isoOfNatIso_ι_hom {F G : J ⥤ C} [HasColimit F] [HasColimit G] (w : F ≅ G)
    (j : J) : colimit.ι F j ≫ (HasColimit.isoOfNatIso w).hom = w.hom.app j ≫ colimit.ι G j :=
  IsColimit.comp_coconePointsIsoOfNatIso_hom _ _ _ _
```

## Filler (hint:2 → hint:3 token-match, ≈1123 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur
