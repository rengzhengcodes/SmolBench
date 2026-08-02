## Current goal
```
⊢ kernel.ι g ≫ cokernel.π f = 0
```

## Full tactic state
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
inst✝ : Abelian C
X Y Z : C
f : X ⟶ Y
g : Y ⟶ Z
w : f ≫ g = 0
h : IsColimit (CokernelCofork.ofπ g w)
this : g ≫ h.desc (CokernelCofork.ofπ (cokernel.π f) ⋯) = cokernel.π f
⊢ kernel.ι g ≫ cokernel.π f = 0
```
