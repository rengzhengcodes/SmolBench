## Current goal
```
⊢ ∃ t, ↑t = f✝
```

## Full tactic state
```
case h.mpr
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
D : Type u₂
inst✝ : Category.{v₂, u₂} D
F : C ⥤ D
X Y Z : C
f : Y ⟶ X
S R : Sieve X
Y✝ : C
f✝ : Y✝ ⟶ X
hf : S.arrows f✝
⊢ ∃ t, ↑t = f✝
```
