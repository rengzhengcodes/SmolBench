## Current goal
```
⊢ (eqToIso h).hom ≫ ι 0 = 0
```

## Full tactic state
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u'
inst✝⁴ : Category.{v', u'} D
inst✝³ : HasZeroMorphisms C
inst✝² : HasZeroObject C
inst✝¹ : HasEqualizers C
X Y : C
f : X ⟶ Y
h : f = 0
inst✝ : HasImage f
⊢ (eqToIso h).hom ≫ ι 0 = 0
```
