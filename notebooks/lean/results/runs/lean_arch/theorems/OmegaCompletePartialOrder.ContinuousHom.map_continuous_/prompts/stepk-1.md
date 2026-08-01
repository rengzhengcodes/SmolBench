## Current goal
```
⊢ Continuous' fun x => pure ∘ f
```

## Full tactic state
```
α : Type u
α' : Type u_1
β✝ : Type v
β' : Type u_2
γ✝ : Type u_3
φ : Type u_4
inst✝⁵ : OmegaCompletePartialOrder α
inst✝⁴ : OmegaCompletePartialOrder β✝
inst✝³ : OmegaCompletePartialOrder γ✝
inst✝² : OmegaCompletePartialOrder φ
inst✝¹ : OmegaCompletePartialOrder α'
inst✝ : OmegaCompletePartialOrder β'
β γ : Type v
f : β → γ
g : α → Part β
hg : Continuous' g
⊢ Continuous' fun x => pure ∘ f
```
