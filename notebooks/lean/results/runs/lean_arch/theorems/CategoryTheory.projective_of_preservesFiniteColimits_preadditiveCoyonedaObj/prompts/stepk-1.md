## Current goal
```
⊢ Functor.PreservesEpimorphisms (preadditiveCoyonedaObj (op P) ⋙ forget₂ (ModuleCat (End (op P))) AddCommGroupCat)
```

## Full tactic state
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : Abelian C
P : C
hP : PreservesFiniteColimits (preadditiveCoyonedaObj (op P))
⊢ Functor.PreservesEpimorphisms (preadditiveCoyonedaObj (op P) ⋙ forget₂ (ModuleCat (End (op P))) AddCommGroupCat)
```
