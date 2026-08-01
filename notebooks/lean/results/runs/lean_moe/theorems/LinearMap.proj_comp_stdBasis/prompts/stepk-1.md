## Current goal
```
⊢ proj i ∘ₗ stdBasis R φ j = diag j i
```

## Full tactic state
```
R : Type u_1
ι : Type u_2
inst✝³ : Semiring R
φ : ι → Type u_3
inst✝² : (i : ι) → AddCommMonoid (φ i)
inst✝¹ : (i : ι) → Module R (φ i)
inst✝ : DecidableEq ι
i j : ι
⊢ proj i ∘ₗ stdBasis R φ j = diag j i
```
