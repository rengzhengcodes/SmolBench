## Current goal
```
⊢ ofComponents (biprod.inl ≫ f ≫ biprod.fst) (biprod.inl ≫ f ≫ biprod.snd) (biprod.inr ≫ f ≫ biprod.fst)
      (biprod.inr ≫ f ≫ biprod.snd) =
    f
```

## Full tactic state
```
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : Preadditive C
inst✝ : HasBinaryBiproducts C
X₁ X₂ Y₁ Y₂ : C
f₁₁ : X₁ ⟶ Y₁
f₁₂ : X₁ ⟶ Y₂
f₂₁ : X₂ ⟶ Y₁
f₂₂ : X₂ ⟶ Y₂
f : X₁ ⊞ X₂ ⟶ Y₁ ⊞ Y₂
⊢ ofComponents (biprod.inl ≫ f ≫ biprod.fst) (biprod.inl ≫ f ≫ biprod.snd) (biprod.inr ≫ f ≫ biprod.fst)
      (biprod.inr ≫ f ≫ biprod.snd) =
    f
```
