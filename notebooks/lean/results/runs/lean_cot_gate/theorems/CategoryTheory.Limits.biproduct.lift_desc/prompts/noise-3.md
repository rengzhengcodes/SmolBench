## Current goal
```
⊢ lift g ≫ desc h = ∑ j : J, g j ≫ h j
```

## Full tactic state
```
C : Type u
inst✝³ : Category.{v, u} C
inst✝² : Preadditive C
J : Type
inst✝¹ : Fintype J
f : J → C
inst✝ : HasBiproduct f
T U : C
g : (j : J) → T ⟶ f j
h : (j : J) → f j ⟶ U
⊢ lift g ≫ desc h = ∑ j : J, g j ≫ h j
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Limits.biproduct.lift_desc` in `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.biproduct.lift_eq`
- `CategoryTheory.Limits.biproduct.desc_eq`
- `CategoryTheory.Preadditive.comp_sum`
- `CategoryTheory.Preadditive.sum_comp`
- `CategoryTheory.Limits.biproduct.ι_π_assoc`
- `CategoryTheory.comp_dite`
- `CategoryTheory.dite_comp`

## Premise signatures
### `CategoryTheory.Limits.biproduct.lift_eq` (commanddeclaration)
```lean
theorem biproduct.lift_eq {T : C} {g : ∀ j, T ⟶ f j} :
    biproduct.lift g = ∑ j, g j ≫ biproduct.ι f j
```

### `CategoryTheory.Limits.biproduct.desc_eq` (commanddeclaration)
```lean
theorem biproduct.desc_eq {T : C} {g : ∀ j, f j ⟶ T} :
    biproduct.desc g = ∑ j, biproduct.π f j ≫ g j
```

### `CategoryTheory.Preadditive.comp_sum` (commanddeclaration)
```lean
@[reassoc]
theorem comp_sum {P Q R : C} {J : Type*} (s : Finset J) (f : P ⟶ Q) (g : J → (Q ⟶ R)) :
    (f ≫ ∑ j in s, g j) = ∑ j in s, f ≫ g j
```

### `CategoryTheory.Preadditive.sum_comp` (commanddeclaration)
```lean
@[reassoc]
theorem sum_comp {P Q R : C} {J : Type*} (s : Finset J) (f : J → (P ⟶ Q)) (g : Q ⟶ R) :
    (∑ j in s, f j) ≫ g = ∑ j in s, f j ≫ g
```

### `CategoryTheory.Limits.biproduct.ι_π_assoc`
_(not found in premise corpus)_

### `CategoryTheory.comp_dite` (commanddeclaration)
```lean
theorem comp_dite {P : Prop} [Decidable P]
    {X Y Z : C} (f : X ⟶ Y) (g : P → (Y ⟶ Z)) (g' : ¬P → (Y ⟶ Z)) :
    (f ≫ if h : P then g h else g' h) = if h : P then f ≫ g h else f ≫ g' h
```

### `CategoryTheory.dite_comp` (commanddeclaration)
```lean
theorem dite_comp {P : Prop} [Decidable P]
    {X Y Z : C} (f : P → (X ⟶ Y)) (f' : ¬P → (X ⟶ Y)) (g : Y ⟶ Z) :
    (if h : P then f h else f' h) ≫ g = if h : P then f h ≫ g else f' h ≫ g
```

## Premise full source (with proof)
### `CategoryTheory.Limits.biproduct.lift_eq` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`
```lean
theorem biproduct.lift_eq {T : C} {g : ∀ j, T ⟶ f j} :
    biproduct.lift g = ∑ j, g j ≫ biproduct.ι f j := by
  ext j
  simp only [sum_comp, biproduct.ι_π, comp_dite, biproduct.lift_π, Category.assoc, comp_zero,
    Finset.sum_dite_eq', Finset.mem_univ, eqToHom_refl, Category.comp_id, if_true]
```

### `CategoryTheory.Limits.biproduct.desc_eq` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Biproducts.lean`
```lean
theorem biproduct.desc_eq {T : C} {g : ∀ j, f j ⟶ T} :
    biproduct.desc g = ∑ j, biproduct.π f j ≫ g j := by
  ext j
  simp [comp_sum, biproduct.ι_π_assoc, dite_comp]
```

### `CategoryTheory.Preadditive.comp_sum` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Basic.lean`
```lean
@[reassoc]
theorem comp_sum {P Q R : C} {J : Type*} (s : Finset J) (f : P ⟶ Q) (g : J → (Q ⟶ R)) :
    (f ≫ ∑ j in s, g j) = ∑ j in s, f ≫ g j :=
  map_sum (leftComp R f) _ _
```

### `CategoryTheory.Preadditive.sum_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Preadditive/Basic.lean`
```lean
@[reassoc]
theorem sum_comp {P Q R : C} {J : Type*} (s : Finset J) (f : J → (P ⟶ Q)) (g : Q ⟶ R) :
    (∑ j in s, f j) ≫ g = ∑ j in s, f j ≫ g :=
  map_sum (rightComp P g) _ _
```

### `CategoryTheory.Limits.biproduct.ι_π_assoc`
_(not found in premise corpus)_

### `CategoryTheory.comp_dite` (commanddeclaration) at `Mathlib/CategoryTheory/Category/Basic.lean`
```lean
theorem comp_dite {P : Prop} [Decidable P]
    {X Y Z : C} (f : X ⟶ Y) (g : P → (Y ⟶ Z)) (g' : ¬P → (Y ⟶ Z)) :
    (f ≫ if h : P then g h else g' h) = if h : P then f ≫ g h else f ≫ g' h := by aesop
```

### `CategoryTheory.dite_comp` (commanddeclaration) at `Mathlib/CategoryTheory/Category/Basic.lean`
```lean
theorem dite_comp {P : Prop} [Decidable P]
    {X Y Z : C} (f : P → (X ⟶ Y)) (f' : ¬P → (X ⟶ Y)) (g : Y ⟶ Z) :
    (if h : P then f h else f' h) ≫ g = if h : P then f h ≫ g else f' h ≫ g := by aesop
```

## Filler (hint:2 → hint:3 token-match, ≈740 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
