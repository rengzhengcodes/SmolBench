## Current goal
```
⊢ (singleObjApplyIso j X).inv ≫ (single j).map f j = f ≫ (singleObjApplyIso j Y).inv
```

## Full tactic state
```
J : Type u_1
C : Type u_2
inst✝² : Category.{u_3, u_2} C
inst✝¹ : HasInitial C
inst✝ : DecidableEq J
j : J
X Y : C
f : X ⟶ Y
⊢ (singleObjApplyIso j X).inv ≫ (single j).map f j = f ≫ (singleObjApplyIso j Y).inv
```
