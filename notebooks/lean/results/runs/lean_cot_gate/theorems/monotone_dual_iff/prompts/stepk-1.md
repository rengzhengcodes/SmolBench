## Current goal
```
⊢ Monotone (⇑toDual ∘ f ∘ ⇑ofDual) ↔ Monotone f
```

## Full tactic state
```
ι : Type u_1
α : Type u
β : Type v
γ : Type w
δ : Type u_2
π : ι → Type u_3
r : α → α → Prop
inst✝¹ : Preorder α
inst✝ : Preorder β
f : α → β
s : Set α
⊢ Monotone (⇑toDual ∘ f ∘ ⇑ofDual) ↔ Monotone f
```
