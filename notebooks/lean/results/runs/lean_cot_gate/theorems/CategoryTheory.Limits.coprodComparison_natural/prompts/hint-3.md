## Current goal
```
⊢ coprodComparison F A B ≫ F.map (coprod.map f g) = coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B'
```

## Full tactic state
```
C : Type u
inst✝⁵ : Category.{v, u} C
X Y : C
D : Type u₂
inst✝⁴ : Category.{w, u₂} D
F : C ⥤ D
A A' B B' : C
inst✝³ : HasBinaryCoproduct A B
inst✝² : HasBinaryCoproduct A' B'
inst✝¹ : HasBinaryCoproduct (F.obj A) (F.obj B)
inst✝ : HasBinaryCoproduct (F.obj A') (F.obj B')
f : A ⟶ A'
g : B ⟶ B'
⊢ coprodComparison F A B ≫ F.map (coprod.map f g) = coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B'
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Limits.coprodComparison_natural` in `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.coprodComparison`
- `CategoryTheory.Limits.coprodComparison`
- `CategoryTheory.Limits.coprod.map_desc`
- `CategoryTheory.Limits.coprod.desc_comp`
- `CategoryTheory.Limits.coprod.inl_map`
- `CategoryTheory.Limits.coprod.inr_map`

## Premise signatures
### `CategoryTheory.Limits.coprodComparison` (commanddeclaration)
```lean
def coprodComparison (F : C ⥤ D) (A B : C) [HasBinaryCoproduct A B]
    [HasBinaryCoproduct (F.obj A) (F.obj B)] : F.obj A ⨿ F.obj B ⟶ F.obj (A ⨿ B)
```

### `CategoryTheory.Limits.coprodComparison` (commanddeclaration)
```lean
def coprodComparison (F : C ⥤ D) (A B : C) [HasBinaryCoproduct A B]
    [HasBinaryCoproduct (F.obj A) (F.obj B)] : F.obj A ⨿ F.obj B ⟶ F.obj (A ⨿ B)
```

### `CategoryTheory.Limits.coprod.map_desc` (commanddeclaration)
```lean
@[reassoc, simp]
theorem coprod.map_desc {S T U V W : C} [HasBinaryCoproduct U W] [HasBinaryCoproduct T V]
    (f : U ⟶ S) (g : W ⟶ S) (h : T ⟶ U) (k : V ⟶ W) :
    coprod.map h k ≫ coprod.desc f g = coprod.desc (h ≫ f) (k ≫ g)
```

### `CategoryTheory.Limits.coprod.desc_comp` (commanddeclaration)
```lean
@[simp] theorem coprod.desc_comp {V W X Y : C} [HasBinaryCoproduct X Y] (f : V ⟶ W) (g : X ⟶ V)
    (h : Y ⟶ V) : coprod.desc g h ≫ f = coprod.desc (g ≫ f) (h ≫ f)
```

### `CategoryTheory.Limits.coprod.inl_map` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem coprod.inl_map {W X Y Z : C} [HasBinaryCoproduct W X] [HasBinaryCoproduct Y Z] (f : W ⟶ Y)
    (g : X ⟶ Z) : coprod.inl ≫ coprod.map f g = f ≫ coprod.inl
```

### `CategoryTheory.Limits.coprod.inr_map` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem coprod.inr_map {W X Y Z : C} [HasBinaryCoproduct W X] [HasBinaryCoproduct Y Z] (f : W ⟶ Y)
    (g : X ⟶ Z) : coprod.inr ≫ coprod.map f g = g ≫ coprod.inr
```

## Premise full source (with proof)
### `CategoryTheory.Limits.coprodComparison` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
/-- The coproduct comparison morphism.

In `CategoryTheory/Limits/Preserves` we show
this is always an iso iff F preserves binary coproducts.
-/
def coprodComparison (F : C ⥤ D) (A B : C) [HasBinaryCoproduct A B]
    [HasBinaryCoproduct (F.obj A) (F.obj B)] : F.obj A ⨿ F.obj B ⟶ F.obj (A ⨿ B) :=
  coprod.desc (F.map coprod.inl) (F.map coprod.inr)
```

### `CategoryTheory.Limits.coprodComparison` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
/-- The coproduct comparison morphism.

In `CategoryTheory/Limits/Preserves` we show
this is always an iso iff F preserves binary coproducts.
-/
def coprodComparison (F : C ⥤ D) (A B : C) [HasBinaryCoproduct A B]
    [HasBinaryCoproduct (F.obj A) (F.obj B)] : F.obj A ⨿ F.obj B ⟶ F.obj (A ⨿ B) :=
  coprod.desc (F.map coprod.inl) (F.map coprod.inr)
```

### `CategoryTheory.Limits.coprod.map_desc` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
@[reassoc, simp]
theorem coprod.map_desc {S T U V W : C} [HasBinaryCoproduct U W] [HasBinaryCoproduct T V]
    (f : U ⟶ S) (g : W ⟶ S) (h : T ⟶ U) (k : V ⟶ W) :
    coprod.map h k ≫ coprod.desc f g = coprod.desc (h ≫ f) (k ≫ g) := by
  ext <;> simp
```

### `CategoryTheory.Limits.coprod.desc_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
@[simp] -- Porting note: removing reassoc tag since result is not hygienic (two h's)
theorem coprod.desc_comp {V W X Y : C} [HasBinaryCoproduct X Y] (f : V ⟶ W) (g : X ⟶ V)
    (h : Y ⟶ V) : coprod.desc g h ≫ f = coprod.desc (g ≫ f) (h ≫ f) := by
  ext <;> simp
```

### `CategoryTheory.Limits.coprod.inl_map` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
@[reassoc (attr := simp)]
theorem coprod.inl_map {W X Y Z : C} [HasBinaryCoproduct W X] [HasBinaryCoproduct Y Z] (f : W ⟶ Y)
    (g : X ⟶ Z) : coprod.inl ≫ coprod.map f g = f ≫ coprod.inl :=
  ι_colimMap _ _
```

### `CategoryTheory.Limits.coprod.inr_map` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
@[reassoc (attr := simp)]
theorem coprod.inr_map {W X Y Z : C} [HasBinaryCoproduct W X] [HasBinaryCoproduct Y Z] (f : W ⟶ Y)
    (g : X ⟶ Z) : coprod.inr ≫ coprod.map f g = g ≫ coprod.inr :=
  ι_colimMap _ _
```

## Transitive premise context (1-hop, 6/6 premises, ≈839 tokens)
### `AlgebraicGeometry.LocallyRingedSpace.coproduct` (commanddeclaration) at `Mathlib/Geometry/RingedSpace/LocallyRingedSpace/HasColimits.lean`
```lean
/-- The explicit coproduct for `F : discrete ι ⥤ LocallyRingedSpace`. -/
noncomputable def coproduct : LocallyRingedSpace where
  toSheafedSpace := colimit (C := SheafedSpace.{u+1, u, u} CommRingCatMax.{u, u})
    (F ⋙ forgetToSheafedSpace)
  localRing x := by
    obtain ⟨i, y, ⟨⟩⟩ := SheafedSpace.colimit_exists_rep (F ⋙ forgetToSheafedSpace) x
    haveI : LocalRing (((F ⋙ forgetToSheafedSpace).obj i).toPresheafedSpace.stalk y) :=
      (F.obj i).localRing _
    exact
      (asIso (PresheafedSpace.stalkMap
        (colimit.ι (C := SheafedSpace.{u+1, u, u} CommRingCatMax.{u, u})
          (F ⋙ forgetToSheafedSpace) i : _) y)).symm.commRingCatIsoToRingEquiv.localRing
```

### `CategoryTheory.Limits.HasBinaryCoproduct` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean`
```lean
/-- An abbreviation for `HasColimit (pair X Y)`. -/
abbrev HasBinaryCoproduct (X Y : C) :=
  HasColimit (pair X Y)
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

### `Lean.TagDeclarationExtension.tag` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Environment.lean`
```lean
def tag (ext : TagDeclarationExtension) (env : Environment) (declName : Name) : Environment :=
  have : Inhabited Environment := ⟨env⟩
  assert! env.getModuleIdxFor? declName |>.isNone -- See comment at `TagDeclarationExtension`
  ext.addEntry env declName
```

### `IO.Promise.result` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/System/Promise.lean`
```lean
/--
The result task of a `Promise`.

The task blocks until `Promise.resolve` is called.
-/
@[extern "lean_io_promise_result"]
opaque Promise.result (promise : Promise α) : Task α :=
  have : Nonempty α := promise.h
  Classical.choice inferInstance
```

### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```
