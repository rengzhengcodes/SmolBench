## Current goal
```
⊢ (pullbackIsoUnopPushout f g).hom ≫ pushout.inl.unop = pullback.fst
```

## Full tactic state
```
case a
C : Type u₁
inst✝³ : Category.{v₁, u₁} C
J : Type u₂
inst✝² : Category.{v₂, u₂} J
X✝ : Type v₂
X Y Z : C
f : X ⟶ Z
g : Y ⟶ Z
inst✝¹ : HasPullback f g
inst✝ : HasPushout f.op g.op
⊢ (pullbackIsoUnopPushout f g).hom ≫ pushout.inl.unop = pullback.fst
```

## Proof so far (2 tactics)
```lean
apply Quiver.Hom.unop_inj
dsimp
```

## Theorem
`CategoryTheory.Limits.pullbackIsoUnopPushout_hom_inl` in `Mathlib/CategoryTheory/Limits/Opposites.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst`
- `CategoryTheory.Iso.hom_inv_id_assoc`

## Premise signatures
### `CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem pullbackIsoUnopPushout_inv_fst {X Y Z : C} (f : X ⟶ Z) (g : Y ⟶ Z) [HasPullback f g]
    [HasPushout f.op g.op] :
    (pullbackIsoUnopPushout f g).inv ≫ pullback.fst = (pushout.inl : _ ⟶ pushout f.op g.op).unop
```

### `CategoryTheory.Iso.hom_inv_id_assoc`
_(not found in premise corpus)_

## Premise full source (with proof)
### `CategoryTheory.Limits.pullbackIsoUnopPushout_inv_fst` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Opposites.lean`
```lean
@[reassoc (attr := simp)]
theorem pullbackIsoUnopPushout_inv_fst {X Y Z : C} (f : X ⟶ Z) (g : Y ⟶ Z) [HasPullback f g]
    [HasPushout f.op g.op] :
    (pullbackIsoUnopPushout f g).inv ≫ pullback.fst = (pushout.inl : _ ⟶ pushout f.op g.op).unop :=
  (IsLimit.conePointUniqueUpToIso_inv_comp _ _ _).trans (by simp [unop_id (X := { unop := X })])
```

### `CategoryTheory.Iso.hom_inv_id_assoc`
_(not found in premise corpus)_

## Transitive premise context (1-hop, 5/5 premises, ≈596 tokens)
### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
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

### `CategoryTheory.Limits.pullbackIsoUnopPushout` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Opposites.lean`
```lean
/-- The pullback of `f` and `g` in `C` is isomorphic to the pushout of
`f.op` and `g.op` in `Cᵒᵖ`. -/
noncomputable def pullbackIsoUnopPushout {X Y Z : C} (f : X ⟶ Z) (g : Y ⟶ Z) [h : HasPullback f g]
    [HasPushout f.op g.op] : pullback f g ≅ unop (pushout f.op g.op) :=
  IsLimit.conePointUniqueUpToIso (@limit.isLimit _ _ _ _ _ h)
    ((PushoutCocone.isColimitEquivIsLimitUnop _) (colimit.isColimit (span f.op g.op)))
```

### `trans` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem trans [IsTrans α r] {a b c : α} : a ≺ b → b ≺ c → a ≺ c :=
  IsTrans.trans _ _ _
```
