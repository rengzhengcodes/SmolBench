## Current goal
```
⊢ x ∈ {a | ∃ i, p i ∧ ∀ ⦃x : ι⦄, x ∈ s i → a ≤ f x} ↔ x ∈ ⋃ j, ⋂ i, Iic (f ↑i)
```

## Full tactic state
```
case e_a.h
α : Type u_1
β : Type u_2
γ : Type u_3
ι✝ : Type u_4
ι'✝ : Type u_5
inst✝ : ConditionallyCompleteLattice α
ι : Type u_6
ι' : Type u_7
f : ι → α
v : Filter ι
p : ι' → Prop
s : ι' → Set ι
hv : HasBasis v p s
x : α
⊢ x ∈ {a | ∃ i, p i ∧ ∀ ⦃x : ι⦄, x ∈ s i → a ≤ f x} ↔ x ∈ ⋃ j, ⋂ i, Iic (f ↑i)
```
