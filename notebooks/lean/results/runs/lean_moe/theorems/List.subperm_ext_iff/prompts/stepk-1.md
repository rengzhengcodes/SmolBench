## Current goal
```
⊢ List.diff l₂ l₁ ++ l₁ ~ l₂
```

## Full tactic state
```
α : Type u_1
inst✝ : DecidableEq α
l₁ l₂ : List α
h : ∀ (x : α), x ∈ l₁ → count x l₁ ≤ count x l₂
this : l₁ <+~ List.diff l₂ l₁ ++ l₁
⊢ List.diff l₂ l₁ ++ l₁ ~ l₂
```
