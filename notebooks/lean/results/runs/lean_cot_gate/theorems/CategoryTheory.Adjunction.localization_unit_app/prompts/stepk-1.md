## Current goal
```
⊢ (localization adj L₁ W₁ L₂ W₂ G' F').unit.app (L₁.obj X₁) =
    L₁.map (adj.unit.app X₁) ≫
      (CatCommSq.iso F L₂ L₁ F').hom.app (G.obj X₁) ≫ F'.map ((CatCommSq.iso G L₁ L₂ G').hom.app X₁)
```

## Full tactic state
```
C₁ : Type u_1
C₂ : Type u_2
D₁ : Type u_3
D₂ : Type u_4
inst✝⁷ : Category.{u_6, u_1} C₁
inst✝⁶ : Category.{u_8, u_2} C₂
inst✝⁵ : Category.{u_5, u_3} D₁
inst✝⁴ : Category.{u_7, u_4} D₂
G : C₁ ⥤ C₂
F : C₂ ⥤ C₁
adj : G ⊣ F
L₁ : C₁ ⥤ D₁
W₁ : MorphismProperty C₁
inst✝³ : Functor.IsLocalization L₁ W₁
L₂ : C₂ ⥤ D₂
W₂ : MorphismProperty C₂
inst✝² : Functor.IsLocalization L₂ W₂
G' : D₁ ⥤ D₂
F' : D₂ ⥤ D₁
inst✝¹ : CatCommSq G L₁ L₂ G'
inst✝ : CatCommSq F L₂ L₁ F'
X₁ : C₁
⊢ (localization adj L₁ W₁ L₂ W₂ G' F').unit.app (L₁.obj X₁) =
    L₁.map (adj.unit.app X₁) ≫
      (CatCommSq.iso F L₂ L₁ F').hom.app (G.obj X₁) ≫ F'.map ((CatCommSq.iso G L₁ L₂ G').hom.app X₁)
```
