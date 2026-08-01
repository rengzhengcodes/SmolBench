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

## Filler (hint:2 → hint:3 token-match, ≈399 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
