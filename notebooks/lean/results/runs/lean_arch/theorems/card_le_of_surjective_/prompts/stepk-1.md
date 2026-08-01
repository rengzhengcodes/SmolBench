## Current goal
```
⊢ Fintype.card β ≤ Fintype.card α
```

## Full tactic state
```
R : Type u
inst✝³ : Semiring R
inst✝² : RankCondition R
α : Type u_1
β : Type u_2
inst✝¹ : Fintype α
inst✝ : Fintype β
f : (α →₀ R) →ₗ[R] β →₀ R
i : Surjective ⇑f
P : (β →₀ R) ≃ₗ[R] β → R := Finsupp.linearEquivFunOnFinite R R β
Q : (α → R) ≃ₗ[R] α →₀ R := LinearEquiv.symm (Finsupp.linearEquivFunOnFinite R R α)
⊢ Fintype.card β ≤ Fintype.card α
```
