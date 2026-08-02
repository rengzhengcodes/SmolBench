## Current goal
```
⊢ (unitCompPartialBijective A hB') (f ≫ h) = (unitCompPartialBijective A hB) f ≫ h
```

## Full tactic state
```
C : Type u₁
D : Type u₂
E : Type u₃
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
inst✝¹ : Category.{v₃, u₃} E
i : D ⥤ C
inst✝ : Reflective i
A B B' : C
h : B ⟶ B'
hB : B ∈ Functor.essImage i
hB' : B' ∈ Functor.essImage i
f : A ⟶ B
⊢ (unitCompPartialBijective A hB') (f ≫ h) = (unitCompPartialBijective A hB) f ≫ h
```
