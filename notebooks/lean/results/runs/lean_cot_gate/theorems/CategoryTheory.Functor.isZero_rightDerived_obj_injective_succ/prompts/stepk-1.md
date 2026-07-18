## Current goal
```
⊢ IsZero ((InjectiveResolution.self X).cocomplex.X (n + 1))
```

## Full tactic state
```
C : Type u
inst✝⁶ : Category.{v, u} C
D : Type u_1
inst✝⁵ : Category.{u_2, u_1} D
inst✝⁴ : Abelian C
inst✝³ : HasInjectiveResolutions C
inst✝² : Abelian D
F : C ⥤ D
inst✝¹ : Additive F
n : ℕ
X : C
inst✝ : Injective X
⊢ IsZero ((InjectiveResolution.self X).cocomplex.X (n + 1))
```
