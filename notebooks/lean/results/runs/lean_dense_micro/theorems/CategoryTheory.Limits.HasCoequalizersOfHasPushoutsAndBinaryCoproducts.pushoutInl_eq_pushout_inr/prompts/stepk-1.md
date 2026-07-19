## Current goal
```
⊢ pushoutInl F = pushout.inr
```

## Full tactic state
```
C : Type u
inst✝³ : Category.{v, u} C
D : Type u'
inst✝² : Category.{v', u'} D
G : C ⥤ D
inst✝¹ : HasBinaryCoproducts C
inst✝ : HasPushouts C
F : WalkingParallelPair ⥤ C
⊢ pushoutInl F = pushout.inr
```
