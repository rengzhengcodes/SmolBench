## Current goal
```
⊢ ↑(⨅ i, ⨅ j, f i j) = ⋂ i, ⋂ j, ↑(f i j)
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
δ : Type u_4
ι : Sort u_5
κ : ι → Sort u_6
inst✝¹ : CompleteLattice α
inst✝ : DecidableRel fun x x_1 => x ≤ x_1
f : (i : ι) → κ i → Interval α
⊢ ↑(⨅ i, ⨅ j, f i j) = ⋂ i, ⋂ j, ↑(f i j)
```
