## Current goal
```
⊢ (iso L f).hom ≫ L.map (image.ι f) = image.ι (L.map f)
```

## Full tactic state
```
A : Type u₁
B : Type u₂
inst✝⁷ : Category.{v₁, u₁} A
inst✝⁶ : Category.{v₂, u₂} B
inst✝⁵ : HasEqualizers A
inst✝⁴ : HasImages A
inst✝³ : StrongEpiCategory B
inst✝² : HasImages B
L : A ⥤ B
inst✝¹ : {X Y Z : A} → (f : X ⟶ Z) → (g : Y ⟶ Z) → PreservesLimit (cospan f g) L
inst✝ : {X Y Z : A} → (f : X ⟶ Y) → (g : X ⟶ Z) → PreservesColimit (span f g) L
X Y : A
f : X ⟶ Y
⊢ (iso L f).hom ≫ L.map (image.ι f) = image.ι (L.map f)
```
