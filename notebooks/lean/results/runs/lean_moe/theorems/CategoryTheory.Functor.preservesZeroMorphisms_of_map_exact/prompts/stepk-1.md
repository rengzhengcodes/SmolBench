## Current goal
```
⊢ PreservesZeroMorphisms L
```

## Full tactic state
```
C : Type u₁
inst✝⁵ : Category.{v₁, u₁} C
inst✝⁴ : Abelian C
A : Type u₁
B : Type u₂
inst✝³ : Category.{v₁, u₁} A
inst✝² : Category.{v₂, u₂} B
inst✝¹ : Abelian A
inst✝ : Abelian B
L : A ⥤ B
h : 𝟙 (L.obj 0) = 0
⊢ PreservesZeroMorphisms L
```
