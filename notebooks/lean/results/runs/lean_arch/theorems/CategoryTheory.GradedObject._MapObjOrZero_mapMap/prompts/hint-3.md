## Current goal
```
⊢ ιMapObjOrZero X p i j ≫ mapMap φ p j = φ i ≫ ιMapObjOrZero Y p i j
```

## Full tactic state
```
case neg
I : Type u_1
J : Type u_2
K : Type u_3
C : Type u_4
inst✝⁵ : Category.{u_5, u_4} C
X Y Z : GradedObject I C
φ : X ⟶ Y
e : X ≅ Y
ψ : Y ⟶ Z
p : I → J
j✝ : J
inst✝⁴ : HasMap X p
inst✝³ : HasMap Y p
inst✝² : HasMap Z p
q : J → K
r : I → K
hpqr : ∀ (i : I), q (p i) = r i
inst✝¹ : HasZeroMorphisms C
inst✝ : DecidableEq J
i : I
j : J
h : ¬p i = j
⊢ ιMapObjOrZero X p i j ≫ mapMap φ p j = φ i ≫ ιMapObjOrZero Y p i j
```

## Proof so far (2 tactics)
```lean
by_cases h : p i = j
simp only [ιMapObjOrZero_eq _ _ _ _ h, ι_mapMap]
```

## Theorem
`CategoryTheory.GradedObject.ιMapObjOrZero_mapMap` in `Mathlib/CategoryTheory/GradedObject.lean`

## Premises used in the next tactic
- `CategoryTheory.GradedObject.ιMapObjOrZero_eq_zero`
- `CategoryTheory.Limits.zero_comp`
- `CategoryTheory.Limits.comp_zero`

## Premise signatures
### `CategoryTheory.GradedObject.ιMapObjOrZero_eq_zero` (lemma)
```lean
lemma ιMapObjOrZero_eq_zero (h : p i ≠ j) : X.ιMapObjOrZero p i j = 0
```

### `CategoryTheory.Limits.zero_comp` (commanddeclaration)
```lean
@[simp]
theorem zero_comp [HasZeroMorphisms C] {X : C} {Y Z : C} {f : Y ⟶ Z} :
    (0 : X ⟶ Y) ≫ f = (0 : X ⟶ Z)
```

### `CategoryTheory.Limits.comp_zero` (commanddeclaration)
```lean
@[simp]
theorem comp_zero [HasZeroMorphisms C] {X Y : C} {f : X ⟶ Y} {Z : C} :
    f ≫ (0 : Y ⟶ Z) = (0 : X ⟶ Z)
```

## Premise full source (with proof)
### `CategoryTheory.GradedObject.ιMapObjOrZero_eq_zero` (lemma) at `Mathlib/CategoryTheory/GradedObject.lean`
```lean
lemma ιMapObjOrZero_eq_zero (h : p i ≠ j) : X.ιMapObjOrZero p i j = 0 := dif_neg h
```

### `CategoryTheory.Limits.zero_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
@[simp]
theorem zero_comp [HasZeroMorphisms C] {X : C} {Y Z : C} {f : Y ⟶ Z} :
    (0 : X ⟶ Y) ≫ f = (0 : X ⟶ Z) :=
  HasZeroMorphisms.zero_comp X f
```

### `CategoryTheory.Limits.comp_zero` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
@[simp]
theorem comp_zero [HasZeroMorphisms C] {X Y : C} {f : X ⟶ Y} {Z : C} :
    f ≫ (0 : Y ⟶ Z) = (0 : X ⟶ Z) :=
  HasZeroMorphisms.comp_zero f Z
```

## Transitive premise context (1-hop, 2/2 premises, ≈377 tokens)
### `dif_neg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem dif_neg {c : Prop} {h : Decidable c} (hnc : ¬c) {α : Sort u} {t : c → α} {e : ¬ c → α} : (dite c t e) = e hnc :=
  match h with
  | isTrue hc   => absurd hc hnc
  | isFalse _   => rfl

-- Remark: dite and ite are "defally equal" when we ignore the proofs.
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
