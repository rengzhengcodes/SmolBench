## Current goal
```
⊢ IsIso 0
```

## Full tactic state
```
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
inst✝¹ : HasZeroMorphisms C
inst✝ : HasZeroObject C
X Y : C
f : X ⟶ Y
i : X ≅ 0
j : Y ≅ 0
⊢ IsIso 0
```
