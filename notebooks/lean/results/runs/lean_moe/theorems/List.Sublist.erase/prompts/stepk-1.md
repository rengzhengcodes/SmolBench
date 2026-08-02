## Current goal
```
⊢ List.eraseP (fun x => a == x) l₁ <+ List.eraseP (fun x => a == x) l₂
```

## Full tactic state
```
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
h : l₁ <+ l₂
⊢ List.eraseP (fun x => a == x) l₁ <+ List.eraseP (fun x => a == x) l₂
```
