## Current goal
```
⊢ L.map f ≫ L.map g = 0
```

## Full tactic state
```
C : Type u₁
inst✝⁷ : Category.{v₁, u₁} C
inst✝⁶ : Abelian C
A : Type u₁
B : Type u₂
inst✝⁵ : Category.{v₁, u₁} A
inst✝⁴ : Category.{v₂, u₂} B
inst✝³ : Abelian A
inst✝² : Abelian B
L : A ⥤ B
inst✝¹ : PreservesFiniteLimits L
inst✝ : PreservesFiniteColimits L
X Y Z : A
f : X ⟶ Y
g : Y ⟶ Z
e1 : Exact f g
hcoker : IsColimit (Cofork.ofπ (L.map (cokernel.π f)) ⋯) := isColimitOfHasCokernelOfPreservesColimit L f
hker : IsLimit (Fork.ofι (L.map (kernel.ι g)) ⋯) := isLimitOfHasKernelOfPreservesLimit L g
⊢ L.map f ≫ L.map g = 0
```
