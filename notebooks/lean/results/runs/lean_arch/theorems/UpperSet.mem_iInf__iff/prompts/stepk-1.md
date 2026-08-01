## Current goal
```
⊢ a ∈ ⨅ i, ⨅ j, f i j ↔ ∃ i j, a ∈ f i j
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
κ : ι → Sort u_5
inst✝ : LE α
S : Set (UpperSet α)
s t : UpperSet α
a : α
f : (i : ι) → κ i → UpperSet α
⊢ a ∈ ⨅ i, ⨅ j, f i j ↔ ∃ i j, a ∈ f i j
```
