## Current goal
```
⊢ coprodComparison F A B ≫ F.map (coprod.map f g) = coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B'
```

## Full tactic state
```
C : Type u
inst✝⁵ : Category.{v, u} C
X Y : C
D : Type u₂
inst✝⁴ : Category.{w, u₂} D
F : C ⥤ D
A A' B B' : C
inst✝³ : HasBinaryCoproduct A B
inst✝² : HasBinaryCoproduct A' B'
inst✝¹ : HasBinaryCoproduct (F.obj A) (F.obj B)
inst✝ : HasBinaryCoproduct (F.obj A') (F.obj B')
f : A ⟶ A'
g : B ⟶ B'
⊢ coprodComparison F A B ≫ F.map (coprod.map f g) = coprod.map (F.map f) (F.map g) ≫ coprodComparison F A' B'
```
