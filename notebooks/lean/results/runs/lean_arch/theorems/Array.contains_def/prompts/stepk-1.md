## Current goal
```
⊢ (∃ x, x ∈ as.data ∧ (a == x) = true) ↔ a ∈ as.data
```

## Full tactic state
```
α : Type u_1
inst✝ : DecidableEq α
a : α
as : Array α
⊢ (∃ x, x ∈ as.data ∧ (a == x) = true) ↔ a ∈ as.data
```
