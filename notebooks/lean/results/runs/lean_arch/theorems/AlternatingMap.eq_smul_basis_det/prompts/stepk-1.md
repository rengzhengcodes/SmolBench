## Current goal
```
⊢ f (⇑e ∘ ⇑σ) = (f ⇑e • Basis.det e) (⇑e ∘ ⇑σ)
```

## Full tactic state
```
R : Type u_1
inst✝⁶ : CommRing R
M : Type u_2
inst✝⁵ : AddCommGroup M
inst✝⁴ : Module R M
M' : Type u_3
inst✝³ : AddCommGroup M'
inst✝² : Module R M'
ι : Type u_4
inst✝¹ : DecidableEq ι
inst✝ : Fintype ι
e : Basis ι R M
f : M [⋀^ι]→ₗ[R] R
i : ι → ι
h : Injective i
σ : Equiv.Perm ι := Equiv.ofBijective i ⋯
⊢ f (⇑e ∘ ⇑σ) = (f ⇑e • Basis.det e) (⇑e ∘ ⇑σ)
```
