## Current goal
```
⊢ f ≫ retraction f = 0
```

## Full tactic state
```
case mpr
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
inst✝¹ : HasZeroMorphisms C
X Y : C
f : X ⟶ Y
inst✝ : IsSplitMono f
h : f = 0
⊢ f ≫ retraction f = 0
```
