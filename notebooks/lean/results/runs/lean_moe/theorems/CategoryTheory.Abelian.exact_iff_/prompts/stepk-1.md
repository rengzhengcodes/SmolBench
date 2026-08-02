## Current goal
```
⊢ ((IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))).hom ≫ kernel.ι g ≫ cokernel.π f) ≫
      (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf).hom =
    0
```

## Full tactic state
```
case mpr
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
inst✝ : Abelian C
X Y Z : C
f : X ⟶ Y
g : Y ⟶ Z
cg : KernelFork g
hg : IsLimit cg
cf : CokernelCofork f
hf : IsColimit cf
h : f ≫ g = 0 ∧ Fork.ι cg ≫ Cofork.π cf = 0
⊢ ((IsLimit.conePointUniqueUpToIso hg (limit.isLimit (parallelPair g 0))).hom ≫ kernel.ι g ≫ cokernel.π f) ≫
      (IsColimit.coconePointUniqueUpToIso (colimit.isColimit (parallelPair f 0)) hf).hom =
    0
```
