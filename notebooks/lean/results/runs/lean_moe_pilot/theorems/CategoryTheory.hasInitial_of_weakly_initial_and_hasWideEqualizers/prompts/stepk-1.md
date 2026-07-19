## Current goal
```
⊢ i ≫ h ≫ e ≫ i = i ≫ 𝟙 T
```

## Full tactic state
```
C : Type u
inst✝¹ : Category.{v, u} C
inst✝ : HasWideEqualizers C
T : C
hT : ∀ (X : C), Nonempty (T ⟶ X)
endos : Type v := T ⟶ T
i : wideEqualizer id ⟶ T := wideEqualizer.ι id
this : Nonempty endos
X : C
a : wideEqualizer id ⟶ X
E : C := equalizer a (i ≫ Classical.choice ⋯)
e : E ⟶ wideEqualizer id := equalizer.ι a (i ≫ Classical.choice ⋯)
h : T ⟶ E := Classical.choice ⋯
⊢ i ≫ h ≫ e ≫ i = i ≫ 𝟙 T
```
