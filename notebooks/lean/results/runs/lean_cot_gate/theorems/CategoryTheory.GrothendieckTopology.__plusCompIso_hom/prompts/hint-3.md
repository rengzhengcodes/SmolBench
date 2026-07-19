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

## Transitive premise context (1-hop, 8/8 premises, ≈1094 tokens)
### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `CategoryTheory.Limits.HasLimit` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
/-- `HasLimit F` represents the mere existence of a limit for `F`. -/
class HasLimit (F : J ⥤ C) : Prop where mk' ::
  /-- There is some limit cone for `F` -/
  exists_limit : Nonempty (LimitCone F)
```

### `CategoryTheory.Limits.Cone` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Cones.lean`
```lean
/-- A `c : Cone F` is:
* an object `c.pt` and
* a natural transformation `c.π : c.pt ⟶ F` from the constant `c.pt` functor to `F`.

Example: if `J` is a category coming from a poset then the data required to make
a term of type `Cone F` is morphisms `πⱼ : c.pt ⟶ F j` for all `j : J` and,
for all `i ≤ j` in `J`, morphisms `πᵢⱼ : F i ⟶ F j` such that `πᵢ ≫ πᵢⱼ = πᵢ`.

`Cone F` is equivalent, via `cone.equiv` below, to `Σ X, F.cones.obj X`.
-/
structure Cone (F : J ⥤ C) where
  /-- An object of `C` -/
  pt : C
  /-- A natural transformation from the constant functor at `X` to `F` -/
  π : (const J).obj pt ⟶ F
```

### `Lean.MVarId.note` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Meta/Tactic/Assert.lean`
```lean
/-- Add the hypothesis `h : t`, given `v : t`, and return the new `FVarId`. -/
def _root_.Lean.MVarId.note (g : MVarId) (h : Name) (v : Expr) (t? : Option Expr := .none) :
    MetaM (FVarId × MVarId) := do
  (← g.assert h (← match t? with | some t => pure t | none => inferType v) v).intro1P

/--
  Convert the given goal `Ctx |- target` into `Ctx |- let name : type := val; target`.
  It assumes `val` has type `type` -/
```

### `Lean.Elab.Tactic.NormCast.prove` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Elab/Tactic/NormCast.lean`
```lean
/--
Discharging function used during simplification in the "squash" step.
-/
-- TODO: normCast takes a list of expressions to use as lemmas for the discharger
-- TODO: a tactic to print the results the discharger fails to prove
def prove (e : Expr) : SimpM (Option Expr) := do
  withTraceNode `Tactic.norm_cast (return m!"{exceptOptionEmoji ·} discharging: {e}") do
  return (← findLocalDeclWithType? e).map mkFVar

/--
Core rewriting function used in the "squash" step, which moves casts upwards
and eliminates them.

It tries to rewrite an expression using the elim and move lemmas.
On failure, it calls the splitting procedure heuristic.
-/
```

### `iff_true_intro` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem iff_true_intro (h : a) : a ↔ True := iff_of_true h trivial
```

### `CategoryTheory.cancel_epi` (commanddeclaration) at `Mathlib/CategoryTheory/Category/Basic.lean`
```lean
theorem cancel_epi (f : X ⟶ Y) [Epi f] {g h : Y ⟶ Z} : f ≫ g = f ≫ h ↔ g = h :=
  ⟨fun p => Epi.left_cancellation g h p, congr_arg _⟩
```

### `CategoryTheory.Limits.HasColimit` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/HasLimits.lean`
```lean
/-- `HasColimit F` represents the mere existence of a colimit for `F`. -/
class HasColimit (F : J ⥤ C) : Prop where mk' ::
  /-- There exists a colimit for `F` -/
  exists_colimit : Nonempty (ColimitCocone F)
```
