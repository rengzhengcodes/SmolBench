## Current goal
```
⊢ (lift F M hM).map (Limits.IsInitial.to starInitial (incl.obj x)) = M x
```

## Full tactic state
```
C : Type u
inst✝¹ : Category.{v, u} C
D : Type u_1
inst✝ : Category.{u_2, u_1} D
Z : D
F : C ⥤ D
M : (x : C) → Z ⟶ F.obj x
hM : ∀ (x y : C) (f : x ⟶ y), M x ≫ F.map f = M y
x : C
⊢ (lift F M hM).map (Limits.IsInitial.to starInitial (incl.obj x)) = M x
```
