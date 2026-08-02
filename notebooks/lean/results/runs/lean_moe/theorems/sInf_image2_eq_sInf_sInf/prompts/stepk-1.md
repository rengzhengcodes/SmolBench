## Current goal
```
⊢ sInf (image2 u s t) = u (sInf s) (sInf t)
```

## Full tactic state
```
α : Type u
β : Type v
γ : Type w
ι : Sort x
κ : ι → Sort u_1
a a₁ a₂ : α
b b₁ b₂ : β
inst✝² : CompleteLattice α
inst✝¹ : CompleteLattice β
inst✝ : CompleteLattice γ
f : α → β → γ
s : Set α
t : Set β
l u : α → β → γ
l₁ u₁ : β → γ → α
l₂ u₂ : α → γ → β
h₁ : ∀ (b : β), GaloisConnection (l₁ b) (swap u b)
h₂ : ∀ (a : α), GaloisConnection (l₂ a) (u a)
⊢ sInf (image2 u s t) = u (sInf s) (sInf t)
```
