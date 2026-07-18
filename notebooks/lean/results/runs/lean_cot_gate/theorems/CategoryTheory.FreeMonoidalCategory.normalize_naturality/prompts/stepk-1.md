## Current goal
```
⊢ ∀ (n : NormalMonoidalObject C),
    inclusionObj n ◁ (ρ_ X✝).inv ≫ (normalizeIsoApp' C (X✝ ⊗ 𝟙_ (F C)) n).hom =
      (normalizeIsoApp' C X✝ n).hom ≫ inclusion.map (eqToHom ⋯)
```

## Full tactic state
```
case ρ_inv
C : Type u
X Y X✝ : F C
⊢ ∀ (n : NormalMonoidalObject C),
    inclusionObj n ◁ (ρ_ X✝).inv ≫ (normalizeIsoApp' C (X✝ ⊗ 𝟙_ (F C)) n).hom =
      (normalizeIsoApp' C X✝ n).hom ≫ inclusion.map (eqToHom ⋯)
```
