## Current goal
```
⊢ ∀ᶠ (x : α) in l, ∀ y ≤ f x, p y
```

## Full tactic state
```
ι : Type u_1
ι' : Type u_2
α✝ : Type u_3
β✝ : Type u_4
γ : Type u_5
α : Type u_6
β : Type u_7
inst✝ : Preorder β
l : Filter α
p : β → Prop
f : α → β
hf : Tendsto f l atBot
h_evtl : ∀ᶠ (x : β) in atBot, ∀ y ≤ x, p y
⊢ ∀ᶠ (x : α) in l, ∀ y ≤ f x, p y
```
