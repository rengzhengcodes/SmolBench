## Current goal
```
⊢ (∀ᶠ (x : α) in ↑f, p x → q x) ↔ (∀ᶠ (x : α) in ↑f, p x) → ∀ᶠ (x : α) in ↑f, q x
```

## Full tactic state
```
α : Type u
β : Type v
γ : Type u_1
f g : Ultrafilter α
s t : Set α
p q : α → Prop
⊢ (∀ᶠ (x : α) in ↑f, p x → q x) ↔ (∀ᶠ (x : α) in ↑f, p x) → ∀ᶠ (x : α) in ↑f, q x
```
