## Current goal
```
⊢ IsLocalizedEquivalence Φ
```

## Full tactic state
```
C₁ : Type u₁
C₂ : Type u₂
C₃ : Type u₃
D₁ : Type u₄
D₂ : Type u₅
D₃ : Type u₆
inst✝⁸ : Category.{v₁, u₁} C₁
inst✝⁷ : Category.{v₂, u₂} C₂
inst✝⁶ : Category.{v₃, u₃} C₃
inst✝⁵ : Category.{v₄, u₄} D₁
inst✝⁴ : Category.{v₅, u₅} D₂
inst✝³ : Category.{v₆, u₅} D₂
W₁ : MorphismProperty C₁
W₂ : MorphismProperty C₂
W₃ : MorphismProperty C₃
Φ : LocalizerMorphism W₁ W₂
L₁ : C₁ ⥤ D₁
inst✝² : Functor.IsLocalization L₁ W₁
L₂ : C₂ ⥤ D₂
inst✝¹ : Functor.IsLocalization L₂ W₂
G : D₁ ⥤ D₂
inst✝ : Functor.IsLocalization (Φ.functor ⋙ L₂) W₁
this : CatCommSq Φ.functor (Φ.functor ⋙ L₂) L₂ (𝟭 D₂)
⊢ IsLocalizedEquivalence Φ
```
