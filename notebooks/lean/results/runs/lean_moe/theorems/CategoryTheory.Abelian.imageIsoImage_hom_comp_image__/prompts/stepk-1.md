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
