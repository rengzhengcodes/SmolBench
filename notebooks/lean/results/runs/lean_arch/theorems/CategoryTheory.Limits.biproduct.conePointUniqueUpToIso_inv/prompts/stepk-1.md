## Current goal
```
⊢ (ι f j ≫ (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv) ≫ (Bicone.toCone b).π.app j' =
    (ι f j ≫ desc b.ι) ≫ (Bicone.toCone b).π.app j'
```

## Full tactic state
```
J : Type w
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroMorphisms C
D : Type uD
inst✝² : Category.{uD', uD} D
inst✝¹ : HasZeroMorphisms D
f : J → C
inst✝ : HasBiproduct f
b : Bicone f
hb : Bicone.IsBilimit b
j : J
j' : Discrete J
⊢ (ι f j ≫ (IsLimit.conePointUniqueUpToIso hb.isLimit (isLimit f)).inv) ≫ (Bicone.toCone b).π.app j' =
    (ι f j ≫ desc b.ι) ≫ (Bicone.toCone b).π.app j'
```
