## Current goal
```
⊢ sInf {a | ∀ x ∈ s, x ≤ a} = sSup s
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Type u_4
ι' : Type u_5
inst✝ : ConditionallyCompleteLattice α
s : Set α
h : BddAbove s
hs : Set.Nonempty s
⊢ sInf {a | ∀ x ∈ s, x ≤ a} = sSup s
```
