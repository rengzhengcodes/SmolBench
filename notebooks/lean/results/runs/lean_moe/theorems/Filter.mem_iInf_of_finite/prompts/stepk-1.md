## Current goal
```
⊢ ⋂ i, t i ∈ ⨅ i, f i
```

## Full tactic state
```
case intro.intro
α✝ : Type u
β : Type v
γ : Type w
δ : Type u_1
ι✝ : Sort x
f✝ g : Filter α✝
s t✝ : Set α✝
ι : Type u_2
inst✝ : Finite ι
α : Type u_3
f : ι → Filter α
t : ι → Set α
ht : ∀ (i : ι), t i ∈ f i
⊢ ⋂ i, t i ∈ ⨅ i, f i
```
