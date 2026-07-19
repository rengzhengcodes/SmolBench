## Current goal
```
⊢ map (Embedding.subtype p) (Finset.subtype p (Ioi ↑a)) = Ioi ↑a
```

## Full tactic state
```
α : Type u_1
β : Type u_2
inst✝² : Preorder α
p : α → Prop
inst✝¹ : DecidablePred p
inst✝ : LocallyFiniteOrderTop α
a : Subtype p
hp : ∀ ⦃a x : α⦄, a ≤ x → p a → p x
⊢ map (Embedding.subtype p) (Finset.subtype p (Ioi ↑a)) = Ioi ↑a
```
