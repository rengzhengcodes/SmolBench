## Current goal
```
⊢ PreservesZeroMorphisms L
```

## Full tactic state
```
C : Type u₁
inst✝⁵ : Category.{v₁, u₁} C
inst✝⁴ : Abelian C
A : Type u₁
B : Type u₂
inst✝³ : Category.{v₁, u₁} A
inst✝² : Category.{v₂, u₂} B
inst✝¹ : Abelian A
inst✝ : Abelian B
L : A ⥤ B
h : 𝟙 (L.obj 0) = 0
⊢ PreservesZeroMorphisms L
```

## Proof so far (2 tactics)
```lean
replace h := (h (exact_of_zero (𝟙 0) (𝟙 0))).w
rw [L.map_id, Category.comp_id] at h
```

## Theorem
`CategoryTheory.Functor.preservesZeroMorphisms_of_map_exact` in `Mathlib/CategoryTheory/Abelian/Exact.lean`

## Premises used in the next tactic
- `CategoryTheory.Functor.preservesZeroMorphisms_of_map_zero_object`
- `CategoryTheory.Limits.idZeroEquivIsoZero`

## Premise signatures
### `CategoryTheory.Functor.preservesZeroMorphisms_of_map_zero_object` (commanddeclaration)
```lean
theorem preservesZeroMorphisms_of_map_zero_object (i : F.obj 0 ≅ 0) : PreservesZeroMorphisms F where
```

### `CategoryTheory.Limits.idZeroEquivIsoZero` (commanddeclaration)
```lean
def idZeroEquivIsoZero (X : C) : 𝟙 X = 0 ≃ (X ≅ 0) where
  toFun h
```

## Premise full source (with proof)
### `CategoryTheory.Functor.preservesZeroMorphisms_of_map_zero_object` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Preserves/Shapes/Zero.lean`
```lean
theorem preservesZeroMorphisms_of_map_zero_object (i : F.obj 0 ≅ 0) : PreservesZeroMorphisms F where
  map_zero X Y :=
    calc
      F.map (0 : X ⟶ Y) = F.map (0 : X ⟶ 0) ≫ F.map 0 := by rw [← Functor.map_comp, comp_zero]
      _ = F.map 0 ≫ (i.hom ≫ i.inv) ≫ F.map 0 := by rw [Iso.hom_inv_id, Category.id_comp]
      _ = 0 := by simp only [zero_of_to_zero i.hom, zero_comp, comp_zero]
```

### `CategoryTheory.Limits.idZeroEquivIsoZero` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/ZeroMorphisms.lean`
```lean
/-- An object `X` has `𝟙 X = 0` if and only if it is isomorphic to the zero object.

Because `X ≅ 0` contains data (even if a subsingleton), we express this `↔` as an `≃`.
-/
def idZeroEquivIsoZero (X : C) : 𝟙 X = 0 ≃ (X ≅ 0) where
  toFun h :=
    { hom := 0
      inv := 0 }
  invFun i := zero_of_target_iso_zero (𝟙 X) i
  left_inv := by aesop_cat
  right_inv := by aesop_cat
```

## Filler (hint:2 → hint:3 token-match, ≈359 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint
