## Current goal
```
⊢ braiding' P Q = braiding P Q
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
P✝ Q✝ : C
inst✝ : HasBinaryBiproducts C
P Q : C
⊢ braiding' P Q = braiding P Q
```
