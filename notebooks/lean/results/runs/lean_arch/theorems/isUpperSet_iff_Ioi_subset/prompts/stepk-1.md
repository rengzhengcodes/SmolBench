## Current goal
```
⊢ IsUpperSet s ↔ ∀ ⦃a : α⦄, a ∈ s → Ioi a ⊆ s
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
κ : ι → Sort u_5
inst✝ : PartialOrder α
s : Set α
⊢ IsUpperSet s ↔ ∀ ⦃a : α⦄, a ∈ s → Ioi a ⊆ s
```
