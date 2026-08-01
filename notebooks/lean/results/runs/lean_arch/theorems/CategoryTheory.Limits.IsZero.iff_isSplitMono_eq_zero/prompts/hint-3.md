## Current goal
```
⊢ f ≫ retraction f = 0
```

## Full tactic state
```
case mpr
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
inst✝¹ : HasZeroMorphisms C
X Y : C
f : X ⟶ Y
inst✝ : IsSplitMono f
h : f = 0
⊢ f ≫ retraction f = 0
```

## Proof so far (6 tactics)
```lean
rw [iff_id_eq_zero]
constructor
intro h
rw [← Category.id_comp f, h, zero_comp]
intro h
rw [← IsSplitMono.id f]
```

## Theorem
`CategoryTheory.Limits.IsZero.iff_isSplitMono_eq_zero` in `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.zero_comp`

## Premise signatures
### `CategoryTheory.Limits.zero_comp` (commanddeclaration)
```lean
@[simp]
theorem zero_comp [HasZeroMorphisms C] {X : C} {Y Z : C} {f : Y ⟶ Z} :
    (0 : X ⟶ Y) ≫ f = (0 : X ⟶ Z)
```

## Premise full source (with proof)
### `CategoryTheory.Limits.zero_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
@[simp]
theorem zero_comp [HasZeroMorphisms C] {X : C} {Y Z : C} {f : Y ⟶ Z} :
    (0 : X ⟶ Y) ≫ f = (0 : X ⟶ Z) :=
  HasZeroMorphisms.zero_comp X f
```

## Transitive premise context (1-hop, 1/1 premises, ≈246 tokens)
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
