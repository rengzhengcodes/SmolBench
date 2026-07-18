## Current goal
```
⊢ prod.lift (𝟙 X) 0 ≫ σ ≫ g = g
```

## Full tactic state
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : NonPreadditiveAbelian C
X Y : C
f : X ⟶ Y
g : (CokernelCofork.ofπ σ ⋯).pt ⟶ Y
hg : Cofork.π (CokernelCofork.ofπ σ ⋯) ≫ g = prod.map f f ≫ σ
⊢ prod.lift (𝟙 X) 0 ≫ σ ≫ g = g
```
