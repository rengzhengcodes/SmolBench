## Current goal
```
⊢ eraseP (fun x => a == x) (l₁ ++ l₂) = eraseP (fun x => a == x) l₁ ++ l₂
```

## Full tactic state
```
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
h : a ∈ l₁
⊢ eraseP (fun x => a == x) (l₁ ++ l₂) = eraseP (fun x => a == x) l₁ ++ l₂
```
