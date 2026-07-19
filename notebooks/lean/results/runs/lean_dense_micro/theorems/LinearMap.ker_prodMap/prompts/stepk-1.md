## Current goal
```
⊢ Submodule.comap (prodMap f g) ⊥ = Submodule.prod (Submodule.comap f ⊥) (Submodule.comap g ⊥)
```

## Full tactic state
```
R : Type u
K : Type u'
M : Type v
V : Type v'
M₂ : Type w
V₂ : Type w'
M₃ : Type y
V₃ : Type y'
M₄ : Type z
ι : Type x
M₅ : Type u_1
M₆ : Type u_2
S : Type u_3
inst✝¹³ : Semiring R
inst✝¹² : Semiring S
inst✝¹¹ : AddCommMonoid M
inst✝¹⁰ : AddCommMonoid M₂
inst✝⁹ : AddCommMonoid M₃
inst✝⁸ : AddCommMonoid M₄
inst✝⁷ : AddCommMonoid M₅
inst✝⁶ : AddCommMonoid M₆
inst✝⁵ : Module R M
inst✝⁴ : Module R M₂
inst✝³ : Module R M₃
inst✝² : Module R M₄
inst✝¹ : Module R M₅
inst✝ : Module R M₆
f✝ f : M →ₗ[R] M₂
g : M₃ →ₗ[R] M₄
⊢ Submodule.comap (prodMap f g) ⊥ = Submodule.prod (Submodule.comap f ⊥) (Submodule.comap g ⊥)
```
