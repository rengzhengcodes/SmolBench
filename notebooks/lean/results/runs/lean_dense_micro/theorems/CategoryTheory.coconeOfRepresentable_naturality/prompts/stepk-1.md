## Current goal
```
⊢ ((coconeOfRepresentable P₁).ι.app j ≫ α).app T f =
    ((coconeOfRepresentable P₂).ι.app ((CategoryOfElements.map α).op.obj j)).app T f
```

## Full tactic state
```
case w.h.h
C : Type u₁
inst✝¹ : SmallCategory C
ℰ : Type u₂
inst✝ : Category.{u₁, u₂} ℰ
A : C ⥤ ℰ
P₁ P₂ : Cᵒᵖ ⥤ Type u₁
α : P₁ ⟶ P₂
j : (Functor.Elements P₁)ᵒᵖ
T : Cᵒᵖ
f : ((functorToRepresentables P₁).obj j).obj T
⊢ ((coconeOfRepresentable P₁).ι.app j ≫ α).app T f =
    ((coconeOfRepresentable P₂).ι.app ((CategoryOfElements.map α).op.obj j)).app T f
```
