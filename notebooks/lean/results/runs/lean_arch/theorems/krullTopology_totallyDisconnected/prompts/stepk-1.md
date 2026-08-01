## Current goal
```
⊢ σ⁻¹ * τ ≠ 1
```

## Full tactic state
```
K : Type u_1
L : Type u_2
inst✝² : Field K
inst✝¹ : Field L
inst✝ : Algebra K L
h_int : Algebra.IsIntegral K L
σ τ : L ≃ₐ[K] L
h_diff : σ ≠ τ
⊢ σ⁻¹ * τ ≠ 1
```
