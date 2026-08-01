## Current goal
```
⊢ coequalizer.π (F.map ((comparison adj).obj B).a) (adj.counit.app (F.obj ((comparison adj).obj B).A)) ≫
      coequalizer.desc ((adj.homEquiv (G.obj B) B).symm (𝟙 (G.obj B))) ⋯ =
    coequalizer.π (F.map ((comparison adj).obj B).a) (adj.counit.app (F.obj ((comparison adj).obj B).A)) ≫
      coequalizer.desc (adj.counit.app B) ⋯
```

## Full tactic state
```
case h
C : Type u₁
D : Type u₂
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₁, u₂} D
G : D ⥤ C
inst✝¹ : IsRightAdjoint G
inst✝ : ∀ (A : Algebra (Adjunction.toMonad adj)), HasCoequalizer (F.map A.a) (adj.counit.app (F.obj A.A))
B : D
⊢ coequalizer.π (F.map ((comparison adj).obj B).a) (adj.counit.app (F.obj ((comparison adj).obj B).A)) ≫
      coequalizer.desc ((adj.homEquiv (G.obj B) B).symm (𝟙 (G.obj B))) ⋯ =
    coequalizer.π (F.map ((comparison adj).obj B).a) (adj.counit.app (F.obj ((comparison adj).obj B).A)) ≫
      coequalizer.desc (adj.counit.app B) ⋯
```
