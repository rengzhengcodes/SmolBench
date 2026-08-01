## Current goal
```
⊢ (∀ t ∈ lb, ∃ i, pa i ∧ sa i ⊆ f ⁻¹' t) ↔ ∀ t ∈ lb, ∃ i, pa i ∧ MapsTo f (sa i) t
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
ι' : Sort u_5
la : Filter α
pa : ι → Prop
sa : ι → Set α
lb : Filter β
pb : ι' → Prop
sb : ι' → Set β
f : α → β
hla : HasBasis la pa sa
⊢ (∀ t ∈ lb, ∃ i, pa i ∧ sa i ⊆ f ⁻¹' t) ↔ ∀ t ∈ lb, ∃ i, pa i ∧ MapsTo f (sa i) t
```
