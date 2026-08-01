## Current goal
```
⊢ (MonoidalFunctor.εIso F).inv.app X ≫ (𝟙_ (C ⥤ C)).map f = (MonoidalFunctor.εIso F).inv.app X ≫ f
```

## Full tactic state
```
C : Type u
inst✝² : Category.{v, u} C
M : Type u_1
inst✝¹ : Category.{u_2, u_1} M
inst✝ : MonoidalCategory M
F : MonoidalFunctor M (C ⥤ C)
X Y : C
f : X ⟶ Y
⊢ (MonoidalFunctor.εIso F).inv.app X ≫ (𝟙_ (C ⥤ C)).map f = (MonoidalFunctor.εIso F).inv.app X ≫ f
```
