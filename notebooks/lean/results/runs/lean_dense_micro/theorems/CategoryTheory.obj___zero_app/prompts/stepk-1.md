## Current goal
```
⊢ (F.μ (𝟙_ M) m₂).app ((F.obj m₁).obj X) ≫
      (F.μ m₁ (𝟙_ M ⊗ m₂)).app X ≫
        (F.map (α_ m₁ (𝟙_ M) m₂).inv).app X ≫ (MonoidalFunctor.μIso F (m₁ ⊗ 𝟙_ M) m₂).inv.app X =
    (F.obj m₂).map ((MonoidalFunctor.εIso F).inv.app ((F.obj m₁).obj X) ≫ (F.map (ρ_ m₁).inv).app X)
```

## Full tactic state
```
C : Type u
inst✝² : Category.{v, u} C
M : Type u_1
inst✝¹ : Category.{u_2, u_1} M
inst✝ : MonoidalCategory M
F : MonoidalFunctor M (C ⥤ C)
m₁ m₂ : M
X : C
⊢ (F.μ (𝟙_ M) m₂).app ((F.obj m₁).obj X) ≫
      (F.μ m₁ (𝟙_ M ⊗ m₂)).app X ≫
        (F.map (α_ m₁ (𝟙_ M) m₂).inv).app X ≫ (MonoidalFunctor.μIso F (m₁ ⊗ 𝟙_ M) m₂).inv.app X =
    (F.obj m₂).map ((MonoidalFunctor.εIso F).inv.app ((F.obj m₁).obj X) ≫ (F.map (ρ_ m₁).inv).app X)
```
