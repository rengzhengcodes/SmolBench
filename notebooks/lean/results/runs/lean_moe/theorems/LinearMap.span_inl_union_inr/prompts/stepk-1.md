## Current goal
```
⊢ span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = Submodule.prod (span R s) (span R t)
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
inst✝⁸ : Semiring R
inst✝⁷ : AddCommMonoid M
inst✝⁶ : AddCommMonoid M₂
inst✝⁵ : AddCommMonoid M₃
inst✝⁴ : AddCommMonoid M₄
inst✝³ : Module R M
inst✝² : Module R M₂
inst✝¹ : Module R M₃
inst✝ : Module R M₄
s : Set M
t : Set M₂
⊢ span R (⇑(inl R M M₂) '' s ∪ ⇑(inr R M M₂) '' t) = Submodule.prod (span R s) (span R t)
```
