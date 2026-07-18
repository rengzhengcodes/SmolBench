## Current goal
```
⊢ limit.π (homDiagram X X) j (eqToHom ⋯) = eqToHom ⋯
```

## Full tactic state
```
J : Type v
inst✝ : SmallCategory J
F : J ⥤ Cat
X : limit (F ⋙ objects)
j : J
⊢ limit.π (homDiagram X X) j (eqToHom ⋯) = eqToHom ⋯
```
