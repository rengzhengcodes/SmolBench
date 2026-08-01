## Current goal
```
⊢ (shiftComm X i j).symm.hom = (shiftComm X j i).hom
```

## Full tactic state
```
case w
C : Type u
A : Type u_1
inst✝² : Category.{v, u} C
inst✝¹ : AddCommMonoid A
inst✝ : HasShift C A
X Y : C
f : X ⟶ Y
i j : A
⊢ (shiftComm X i j).symm.hom = (shiftComm X j i).hom
```
