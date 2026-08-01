## Current goal
```
⊢ (colimitCocone F).ι.app j xj =
    (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).toEquiv (t.ι.app j xj)
```

## Full tactic state
```
case h.e'_2.h.e'_3.h
J : Type v
inst✝² : Category.{w, v} J
F : J ⥤ Type u
inst✝¹ : HasColimit F
inst✝ : IsFilteredOrEmpty J
t : Cocone F
ht : IsColimit t
i j : J
xi : F.obj i
xj : F.obj j
e_1✝ : ((Functor.const J).obj (colimitCocone F).pt).obj i = (colimitCocone F).pt
⊢ (colimitCocone F).ι.app j xj =
    (IsColimit.coconePointUniqueUpToIso ht (colimitCoconeIsColimit F)).toEquiv (t.ι.app j xj)
```
