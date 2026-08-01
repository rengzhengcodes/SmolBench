## Current goal
```
⊢ Tendsto m l (Filter.lift' f h) ↔ ∀ s ∈ f, ∀ᶠ (a : γ) in l, m a ∈ h s
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
f f₁ f₂ : Filter α
h h₁ h₂ : Set α → Set β
m : γ → β
l : Filter γ
⊢ Tendsto m l (Filter.lift' f h) ↔ ∀ s ∈ f, ∀ᶠ (a : γ) in l, m a ∈ h s
```
