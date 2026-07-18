## Current goal
```
⊢ Sigma.ι (functorObjSrcFamily f πX) { i := i, t := t, b := b, w := w } ≫
      functorObjLeft f πX ≫ functorMapTgt f πX πY φ hφ =
    Sigma.ι (functorObjSrcFamily f πX) { i := i, t := t, b := b, w := w } ≫
      functorMapSrc f πX πY φ hφ ≫ functorObjLeft f πY
```

## Full tactic state
```
case h.mk
C : Type u
inst✝⁴ : Category.{v, u} C
I : Type w
A B : I → C
f : (i : I) → A i ⟶ B i
S X Y Z : C
πX : X ⟶ S
πY : Y ⟶ S
φ : X ⟶ Y
hφ : φ ≫ πY = πX
inst✝³ : HasColimitsOfShape (Discrete (FunctorObjIndex f πX)) C
inst✝² : HasColimitsOfShape (Discrete (FunctorObjIndex f πY)) C
inst✝¹ : HasPushout (functorObjTop f πX) (functorObjLeft f πX)
inst✝ : HasPushout (functorObjTop f πY) (functorObjLeft f πY)
i : I
t : A i ⟶ X
b : B i ⟶ S
w : t ≫ πX = f i ≫ b
⊢ Sigma.ι (functorObjSrcFamily f πX) { i := i, t := t, b := b, w := w } ≫
      functorObjLeft f πX ≫ functorMapTgt f πX πY φ hφ =
    Sigma.ι (functorObjSrcFamily f πX) { i := i, t := t, b := b, w := w } ≫
      functorMapSrc f πX πY φ hφ ≫ functorObjLeft f πY
```
