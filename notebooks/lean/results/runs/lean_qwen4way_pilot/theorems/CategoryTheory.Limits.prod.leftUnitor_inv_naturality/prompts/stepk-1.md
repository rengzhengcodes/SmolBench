## Current goal
```
⊢ (leftUnitor X).inv ≫ map (𝟙 (⊤_ C)) f = f ≫ (leftUnitor Y).inv
```

## Full tactic state
```
C : Type u
inst✝² : Category.{v, u} C
X Y : C
inst✝¹ : HasTerminal C
inst✝ : HasBinaryProducts C
f : X ⟶ Y
⊢ (leftUnitor X).inv ≫ map (𝟙 (⊤_ C)) f = f ≫ (leftUnitor Y).inv
```
