## Current goal
```
⊢ PullbackCone.IsLimit.lift t (pullback.fst ≫ MonoOver.arrow a) pullback.snd ⋯ ≫ g = pullback.snd
```

## Full tactic state
```
case h.a.g.refine'_2
C : Type u₁
inst✝⁴ : Category.{v₁, u₁} C
X✝ Y✝ Z✝ : C
D : Type u₂
inst✝³ : Category.{v₂, u₂} D
inst✝² : HasPullbacks C
X Y Z W : C
f : X ⟶ Y
g : X ⟶ Z
h : Y ⟶ W
k : Z ⟶ W
inst✝¹ : Mono h
inst✝ : Mono g
comm : f ≫ h = g ≫ k
t : IsLimit (PullbackCone.mk f g comm)
a : MonoOver Y
⊢ PullbackCone.IsLimit.lift t (pullback.fst ≫ MonoOver.arrow a) pullback.snd ⋯ ≫ g = pullback.snd
```
