## Current goal
```
⊢ Cocone.extend (colimitCocone h) (homOfCocone h s) = coconeOfHom h (homOfCocone h s)
```

## Full tactic state
```
J : Type u₁
inst✝² : Category.{v₁, u₁} J
K : Type u₂
inst✝¹ : Category.{v₂, u₂} K
C : Type u₃
inst✝ : Category.{v₃, u₃} C
F : J ⥤ C
t : Cocone F
X : C
h : coyoneda.obj (op X) ⋙ uliftFunctor.{u₁, v₃} ≅ Functor.cocones F
s : Cocone F
⊢ Cocone.extend (colimitCocone h) (homOfCocone h s) = coconeOfHom h (homOfCocone h s)
```
