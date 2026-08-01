## Current goal
```
⊢ HasColimit F
```

## Full tactic state
```
J : Type u₁
inst✝³ : Category.{v₁, u₁} J
K : Type u₂
inst✝² : Category.{v₂, u₂} K
C : Type u
inst✝¹ : Category.{v, u} C
F : J ⥤ C
e : K ≌ J
inst✝ : HasColimit (e.functor ⋙ F)
this : HasColimit (e.inverse ⋙ e.functor ⋙ F)
⊢ HasColimit F
```
