## Current goal
```
⊢ colimit.ι (parallelPair (M.actRight ▷ N.X) ((α_ M.X Y.X N.X).hom ≫ M.X ◁ N.actLeft)) WalkingParallelPair.one =
    coequalizer.π (M.actRight ▷ N.X) ((α_ M.X Y.X N.X).hom ≫ M.X ◁ N.actLeft) ≫ 𝟙 (TensorBimod.X M N)
```

## Full tactic state
```
case h.h
C : Type u₁
inst✝⁴ : Category.{v₁, u₁} C
inst✝³ : MonoidalCategory C
A B : Mon_ C
M✝ : Bimod A B
inst✝² : HasCoequalizers C
inst✝¹ : (X : C) → PreservesColimitsOfSize.{0, 0, v₁, v₁, u₁, u₁} (tensorLeft X)
inst✝ : (X : C) → PreservesColimitsOfSize.{0, 0, v₁, v₁, u₁, u₁} (tensorRight X)
X Y Z : Mon_ C
M : Bimod X Y
N : Bimod Y Z
⊢ colimit.ι (parallelPair (M.actRight ▷ N.X) ((α_ M.X Y.X N.X).hom ≫ M.X ◁ N.actLeft)) WalkingParallelPair.one =
    coequalizer.π (M.actRight ▷ N.X) ((α_ M.X Y.X N.X).hom ≫ M.X ◁ N.actLeft) ≫ 𝟙 (TensorBimod.X M N)
```
