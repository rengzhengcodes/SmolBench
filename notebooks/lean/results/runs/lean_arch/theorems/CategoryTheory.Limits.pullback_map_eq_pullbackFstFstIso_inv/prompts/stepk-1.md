## Current goal
```
⊢ map f g f' g' i₁ i₂ i₃ e₁ e₂ = (pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst
```

## Full tactic state
```
C : Type u_1
inst✝² : Category.{u_2, u_1} C
X✝ Y✝ Z : C
inst✝¹ : HasPullbacks C
X Y S X' Y' S' : C
f : X ⟶ S
g : Y ⟶ S
f' : X' ⟶ S'
g' : Y' ⟶ S'
i₁ : X ⟶ X'
i₂ : Y ⟶ Y'
i₃ : S ⟶ S'
e₁ : f ≫ i₃ = i₁ ≫ f'
e₂ : g ≫ i₃ = i₂ ≫ g'
inst✝ : Mono i₃
⊢ map f g f' g' i₁ i₂ i₃ e₁ e₂ = (pullbackFstFstIso f g f' g' i₁ i₂ i₃ e₁ e₂).inv ≫ snd ≫ fst
```
