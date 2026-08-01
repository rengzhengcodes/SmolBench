## Current goal
```
⊢ ofComponents (biprod.inl ≫ f ≫ biprod.fst) (biprod.inl ≫ f ≫ biprod.snd) (biprod.inr ≫ f ≫ biprod.fst)
      (biprod.inr ≫ f ≫ biprod.snd) =
    f
```

## Full tactic state
```
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : Preadditive C
inst✝ : HasBinaryBiproducts C
X₁ X₂ Y₁ Y₂ : C
f₁₁ : X₁ ⟶ Y₁
f₁₂ : X₁ ⟶ Y₂
f₂₁ : X₂ ⟶ Y₁
f₂₂ : X₂ ⟶ Y₂
f : X₁ ⊞ X₂ ⟶ Y₁ ⊞ Y₂
⊢ ofComponents (biprod.inl ≫ f ≫ biprod.fst) (biprod.inl ≫ f ≫ biprod.snd) (biprod.inr ≫ f ≫ biprod.fst)
      (biprod.inr ≫ f ≫ biprod.snd) =
    f
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Biprod.ofComponents_eq` in `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`

## Premises used in the next tactic
- `CategoryTheory.Category.comp_id`
- `CategoryTheory.Limits.biprod.inr_fst`
- `CategoryTheory.Limits.biprod.inr_snd`
- `CategoryTheory.Limits.biprod.inl_snd`
- `add_zero`
- `zero_add`
- `CategoryTheory.Biprod.inl_ofComponents`
- `CategoryTheory.Biprod.inr_ofComponents`
- `eq_self_iff_true`
- `CategoryTheory.Category.assoc`
- `CategoryTheory.Limits.comp_zero`
- `CategoryTheory.Limits.biprod.inl_fst`
- `CategoryTheory.Preadditive.add_comp`

## Premise signatures
### `CategoryTheory.Category.comp_id`
_(not found in premise corpus)_

### `CategoryTheory.Limits.biprod.inr_fst` (commanddeclaration)
```lean
@[reassoc] theorem biprod.inr_fst {X Y : C} [HasBinaryBiproduct X Y] :
    (biprod.inr : Y ⟶ X ⊞ Y) ≫ (biprod.fst : X ⊞ Y ⟶ X) = 0
```

### `CategoryTheory.Limits.biprod.inr_snd` (commanddeclaration)
```lean
@[reassoc] theorem biprod.inr_snd {X Y : C} [HasBinaryBiproduct X Y] :
    (biprod.inr : Y ⟶ X ⊞ Y) ≫ (biprod.snd : X ⊞ Y ⟶ Y) = 𝟙 Y
```

### `CategoryTheory.Limits.biprod.inl_snd` (commanddeclaration)
```lean
@[reassoc] theorem biprod.inl_snd {X Y : C} [HasBinaryBiproduct X Y] :
    (biprod.inl : X ⟶ X ⊞ Y) ≫ (biprod.snd : X ⊞ Y ⟶ Y) = 0
```

### `add_zero`
_(not found in premise corpus)_

### `zero_add`
_(not found in premise corpus)_

### `CategoryTheory.Biprod.inl_ofComponents` (commanddeclaration)
```lean
@[simp]
theorem Biprod.inl_ofComponents :
    biprod.inl ≫ Biprod.ofComponents f₁₁ f₁₂ f₂₁ f₂₂ = f₁₁ ≫ biprod.inl + f₁₂ ≫ biprod.inr
```

### `CategoryTheory.Biprod.inr_ofComponents` (commanddeclaration)
```lean
@[simp]
theorem Biprod.inr_ofComponents :
    biprod.inr ≫ Biprod.ofComponents f₁₁ f₁₂ f₂₁ f₂₂ = f₂₁ ≫ biprod.inl + f₂₂ ≫ biprod.inr
```

### `eq_self_iff_true` (commanddeclaration)
```lean
theorem eq_self_iff_true (a : α)  : a = a ↔ True
```

### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.comp_zero` (commanddeclaration)
```lean
@[simp]
theorem comp_zero [HasZeroMorphisms C] {X Y : C} {f : X ⟶ Y} {Z : C} :
    f ≫ (0 : Y ⟶ Z) = (0 : X ⟶ Z)
```

### `CategoryTheory.Limits.biprod.inl_fst` (commanddeclaration)
```lean
@[reassoc] theorem biprod.inl_fst {X Y : C} [HasBinaryBiproduct X Y] :
    (biprod.inl : X ⟶ X ⊞ Y) ≫ (biprod.fst : X ⊞ Y ⟶ X) = 𝟙 X
```

### `CategoryTheory.Preadditive.add_comp`
_(not found in premise corpus)_

## Premise full source (with proof)
### `CategoryTheory.Category.comp_id`
_(not found in premise corpus)_

### `CategoryTheory.Limits.biprod.inr_fst` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
@[reassoc] -- Porting note: simp can solve both versions
theorem biprod.inr_fst {X Y : C} [HasBinaryBiproduct X Y] :
    (biprod.inr : Y ⟶ X ⊞ Y) ≫ (biprod.fst : X ⊞ Y ⟶ X) = 0 :=
  (BinaryBiproduct.bicone X Y).inr_fst
```

### `CategoryTheory.Limits.biprod.inr_snd` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
@[reassoc] -- Porting note: simp can solve both versions
theorem biprod.inr_snd {X Y : C} [HasBinaryBiproduct X Y] :
    (biprod.inr : Y ⟶ X ⊞ Y) ≫ (biprod.snd : X ⊞ Y ⟶ Y) = 𝟙 Y :=
  (BinaryBiproduct.bicone X Y).inr_snd
```

### `CategoryTheory.Limits.biprod.inl_snd` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
@[reassoc] -- Porting note: simp can solve both versions
theorem biprod.inl_snd {X Y : C} [HasBinaryBiproduct X Y] :
    (biprod.inl : X ⟶ X ⊞ Y) ≫ (biprod.snd : X ⊞ Y ⟶ Y) = 0 :=
  (BinaryBiproduct.bicone X Y).inl_snd
```

### `add_zero`
_(not found in premise corpus)_

### `zero_add`
_(not found in premise corpus)_

### `CategoryTheory.Biprod.inl_ofComponents` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`
```lean
@[simp]
theorem Biprod.inl_ofComponents :
    biprod.inl ≫ Biprod.ofComponents f₁₁ f₁₂ f₂₁ f₂₂ = f₁₁ ≫ biprod.inl + f₁₂ ≫ biprod.inr := by
  simp [Biprod.ofComponents]
```

### `CategoryTheory.Biprod.inr_ofComponents` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`
```lean
@[simp]
theorem Biprod.inr_ofComponents :
    biprod.inr ≫ Biprod.ofComponents f₁₁ f₁₂ f₂₁ f₂₂ = f₂₁ ≫ biprod.inl + f₂₂ ≫ biprod.inr := by
  simp [Biprod.ofComponents]
```

### `eq_self_iff_true` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem eq_self_iff_true (a : α)  : a = a ↔ True  := iff_true_intro rfl
```

### `CategoryTheory.Category.assoc`
_(not found in premise corpus)_

### `CategoryTheory.Limits.comp_zero` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
@[simp]
theorem comp_zero [HasZeroMorphisms C] {X Y : C} {f : X ⟶ Y} {Z : C} :
    f ≫ (0 : Y ⟶ Z) = (0 : X ⟶ Z) :=
  HasZeroMorphisms.comp_zero f Z
```

### `CategoryTheory.Limits.biprod.inl_fst` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
@[reassoc] -- Porting note: simp can solve both versions
theorem biprod.inl_fst {X Y : C} [HasBinaryBiproduct X Y] :
    (biprod.inl : X ⟶ X ⊞ Y) ≫ (biprod.fst : X ⊞ Y ⟶ X) = 𝟙 X :=
  (BinaryBiproduct.bicone X Y).inl_fst
```

### `CategoryTheory.Preadditive.add_comp`
_(not found in premise corpus)_

## Transitive premise context (1-hop, 4/4 premises, ≈592 tokens)
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

### `CategoryTheory.Limits.HasBinaryBiproduct` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Biproducts.lean`
```lean
/-- `HasBinaryBiproduct P Q` expresses the mere existence of a bicone which is
simultaneously a limit and a colimit of the diagram `pair P Q`.
-/
class HasBinaryBiproduct (P Q : C) : Prop where mk' ::
  exists_binary_biproduct : Nonempty (BinaryBiproductData P Q)
```

### `iff_true_intro` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem iff_true_intro (h : a) : a ↔ True := iff_of_true h trivial
```

### `CategoryTheory.Limits.HasZeroMorphisms` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
/-- A category "has zero morphisms" if there is a designated "zero morphism" in each morphism space,
and compositions of zero morphisms with anything give the zero morphism. -/
class HasZeroMorphisms where
  /-- Every morphism space has zero -/
  [zero : ∀ X Y : C, Zero (X ⟶ Y)]
  /-- `f` composed with `0` is `0` -/
  comp_zero : ∀ {X Y : C} (f : X ⟶ Y) (Z : C), f ≫ (0 : Y ⟶ Z) = (0 : X ⟶ Z) := by aesop_cat
  /-- `0` composed with `f` is `0` -/
  zero_comp : ∀ (X : C) {Y Z : C} (f : Y ⟶ Z), (0 : X ⟶ Y) ≫ f = (0 : X ⟶ Z) := by aesop_cat
```
