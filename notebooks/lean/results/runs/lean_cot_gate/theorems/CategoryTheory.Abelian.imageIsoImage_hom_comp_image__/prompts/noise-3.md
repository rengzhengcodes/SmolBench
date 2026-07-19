## Current goal
```
⊢ (imageIsoImage f).hom ≫ Limits.image.ι f = kernel.ι (cokernel.π f)
```

## Full tactic state
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : Abelian C
X Y : C
f : X ⟶ Y
⊢ (imageIsoImage f).hom ≫ Limits.image.ι f = kernel.ι (cokernel.π f)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.Abelian.imageIsoImage_hom_comp_image_ι` in `Mathlib/CategoryTheory/Abelian/Basic.lean`

## Premises used in the next tactic
- `CategoryTheory.Limits.IsImage.isoExt_hom`
- `CategoryTheory.Limits.IsImage.lift_ι`
- `CategoryTheory.Abelian.imageStrongEpiMonoFactorisation_m`

## Premise signatures
### `CategoryTheory.Limits.IsImage.isoExt_hom`
_(not found in premise corpus)_

### `CategoryTheory.Limits.IsImage.lift_ι` (commanddeclaration)
```lean
@[reassoc (attr := simp)]
theorem IsImage.lift_ι {F : MonoFactorisation f} (hF : IsImage F) :
    hF.lift (Image.monoFactorisation f) ≫ image.ι f = F.m
```

### `CategoryTheory.Abelian.imageStrongEpiMonoFactorisation_m`
_(not found in premise corpus)_

## Premise full source (with proof)
### `CategoryTheory.Limits.IsImage.isoExt_hom`
_(not found in premise corpus)_

### `CategoryTheory.Limits.IsImage.lift_ι` (commanddeclaration) at `Mathlib/CategoryTheory/Limits/Shapes/Images.lean`
```lean
@[reassoc (attr := simp)]
theorem IsImage.lift_ι {F : MonoFactorisation f} (hF : IsImage F) :
    hF.lift (Image.monoFactorisation f) ≫ image.ι f = F.m :=
  hF.lift_fac _
```

### `CategoryTheory.Abelian.imageStrongEpiMonoFactorisation_m`
_(not found in premise corpus)_

## Filler (hint:2 → hint:3 token-match, ≈252 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum
