## Current goal
```
⊢ (∃ᶠ (x : α) in sSup fs, p x) ↔ ∃ f ∈ fs, ∃ᶠ (x : α) in f, p x
```

## Full tactic state
```
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι : Sort x
p : α → Prop
fs : Set (Filter α)
⊢ (∃ᶠ (x : α) in sSup fs, p x) ↔ ∃ f ∈ fs, ∃ᶠ (x : α) in f, p x
```
