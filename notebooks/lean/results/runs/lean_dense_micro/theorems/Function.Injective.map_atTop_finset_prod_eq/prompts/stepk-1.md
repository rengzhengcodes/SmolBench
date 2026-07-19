## Current goal
```
⊢ ∃ u', s ⊆ u' ∧ ∏ x in u', f (g x) = ∏ x in Finset.preimage t g ⋯, f (g x)
```

## Full tactic state
```
case a
ι : Type u_1
ι' : Type u_2
α : Type u_3
β : Type u_4
γ : Type u_5
inst✝ : CommMonoid α
g : γ → β
hg : Injective g
f : β → α
hf : ∀ x ∉ Set.range g, f x = 1
this : DecidableEq β
s : Finset γ
t : Finset β
ht : Finset.image g s ⊆ t
⊢ ∃ u', s ⊆ u' ∧ ∏ x in u', f (g x) = ∏ x in Finset.preimage t g ⋯, f (g x)
```
