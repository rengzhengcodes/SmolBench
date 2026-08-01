## Current goal
```
⊢ p ∣ Fintype.card { x // (eval x) f₁ = 0 ∧ (eval x) f₂ = 0 }
```

## Full tactic state
```
K : Type u_1
σ : Type u_2
ι : Type u_3
inst✝⁵ : Fintype K
inst✝⁴ : Field K
inst✝³ : Fintype σ
inst✝² : DecidableEq σ
inst✝¹ : DecidableEq K
p : ℕ
inst✝ : CharP K p
f₁ f₂ : MvPolynomial σ K
h : totalDegree f₁ + totalDegree f₂ < Fintype.card σ
F : Bool → MvPolynomial σ K := fun b => bif b then f₂ else f₁
this : ∑ b : Bool, totalDegree (F b) < Fintype.card σ
⊢ p ∣ Fintype.card { x // (eval x) f₁ = 0 ∧ (eval x) f₂ = 0 }
```
