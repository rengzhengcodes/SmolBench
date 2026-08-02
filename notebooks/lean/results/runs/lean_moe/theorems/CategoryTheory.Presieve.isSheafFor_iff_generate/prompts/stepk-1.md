## Current goal
```
⊢ FamilyOfElements.IsAmalgamation x t
```

## Full tactic state
```
C : Type u₁
inst✝ : Category.{v₁, u₁} C
P Q U : Cᵒᵖ ⥤ Type w
X Y : C
S : Sieve X
R✝ R : Presieve X
q :
  ∀ (x : FamilyOfElements P (generate R).arrows),
    FamilyOfElements.Compatible x → ∃ t, FamilyOfElements.IsAmalgamation x t
x : FamilyOfElements P R
hx : FamilyOfElements.Compatible x
t : P.obj (op X)
ht : FamilyOfElements.IsAmalgamation (FamilyOfElements.sieveExtend x) t
⊢ FamilyOfElements.IsAmalgamation x t
```
