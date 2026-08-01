## Current goal
```
⊢ U ∈ IsBasis.filter h ↔ ∃ i, p i ∧ s i ⊆ U
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
ι' : Sort u_5
p : ι → Prop
s : ι → Set α
h : IsBasis p s
U : Set α
⊢ U ∈ IsBasis.filter h ↔ ∃ i, p i ∧ s i ⊆ U
```
