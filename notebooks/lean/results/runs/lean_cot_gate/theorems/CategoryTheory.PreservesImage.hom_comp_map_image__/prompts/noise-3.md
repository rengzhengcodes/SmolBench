## Current goal
```
⊢ (iso L f).hom ≫ L.map (image.ι f) = image.ι (L.map f)
```

## Full tactic state
```
A : Type u₁
B : Type u₂
inst✝⁷ : Category.{v₁, u₁} A
inst✝⁶ : Category.{v₂, u₂} B
inst✝⁵ : HasEqualizers A
inst✝⁴ : HasImages A
inst✝³ : StrongEpiCategory B
inst✝² : HasImages B
L : A ⥤ B
inst✝¹ : {X Y Z : A} → (f : X ⟶ Z) → (g : Y ⟶ Z) → PreservesLimit (cospan f g) L
inst✝ : {X Y Z : A} → (f : X ⟶ Y) → (g : X ⟶ Z) → PreservesColimit (span f g) L
X Y : A
f : X ⟶ Y
⊢ (iso L f).hom ≫ L.map (image.ι f) = image.ι (L.map f)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.PreservesImage.hom_comp_map_image_ι` in `Mathlib/CategoryTheory/Limits/Preserves/Shapes/Images.lean`

## Premises used in the next tactic
- `CategoryTheory.PreservesImage.iso_hom`
- `CategoryTheory.Limits.image.lift_fac`

## Premise signatures
### `CategoryTheory.PreservesImage.iso_hom`
_(not found in premise corpus)_

### `CategoryTheory.Limits.image.lift_fac` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem image.lift_fac (F' : MonoFactorisation f) : image.lift F' ≫ F'.m = image.ι f
```

## Premise full source (with proof)
### `CategoryTheory.PreservesImage.iso_hom`
_(not found in premise corpus)_

### `CategoryTheory.Limits.image.lift_fac` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Images.lean`
```lean
@[reassoc (attr := simp)]
theorem image.lift_fac (F' : MonoFactorisation f) : image.lift F' ≫ F'.m = image.ι f :=
  (Image.isImage f).lift_fac F'
```

## Filler (hint:2 → hint:3 token-match, ≈252 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum
