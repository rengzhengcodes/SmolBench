## Current goal
```
⊢ False
```

## Full tactic state
```
case a
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
b : α
h : ¬b ∈ l₁
h' : b ∈ l₁
h'' : (a == b) = true
⊢ False
```
