## Current goal
```
⊢ f.left ≫ Z₁.hom ≫ g = 𝟙 Z₂.left ≫ Z₂.hom ≫ g
```

## Full tactic state
```
C : Type u
inst✝¹ : Category.{v, u} C
J : GrothendieckTopology C
A : Type u'
inst✝ : Category.{v', u'} A
F G : Cᵒᵖ ⥤ A
X : C
S : Sieve X
hG : ⦃Y : C⦄ → (f : Y ⟶ X) → IsLimit (G.mapCone (Cocone.op (Presieve.cocone (Sieve.pullback f S).arrows)))
x : Presieve.FamilyOfElements (presheafHom F G) S.arrows
hx : Presieve.FamilyOfElements.Compatible x
Y : C
g : Y ⟶ X
Z₁ : Over Y
hZ₁ : (Sieve.pullback g S).arrows Z₁.hom
Z₂ : Over Y
hZ₂ : (Sieve.pullback g S).arrows Z₂.hom
f : Z₂ ⟶ Z₁
⊢ f.left ≫ Z₁.hom ≫ g = 𝟙 Z₂.left ≫ Z₂.hom ≫ g
```
