## Current goal
```
⊢ IsPushout 0 0 b.inl b.inr
```

## Full tactic state
```
C : Type u₁
inst✝² : Category.{v₁, u₁} C
Z X Y P : C
f : Z ⟶ X
g : Z ⟶ Y
inl : X ⟶ P
inr : Y ⟶ P
inst✝¹ : HasZeroObject C
inst✝ : HasZeroMorphisms C
b : BinaryBicone X Y
h : BinaryBicone.IsBilimit b
⊢ IsPushout 0 0 b.inl b.inr
```
