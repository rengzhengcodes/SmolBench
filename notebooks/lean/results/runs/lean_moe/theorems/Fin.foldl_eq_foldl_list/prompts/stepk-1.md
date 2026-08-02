## Current goal
```
⊢ foldl (n + 1) f x = List.foldl f x (list (n + 1))
```

## Full tactic state
```
case succ
α : Type u_1
n : Nat
ih : ∀ (f : α → Fin n → α) (x : α), foldl n f x = List.foldl f x (list n)
f : α → Fin (n + 1) → α
x : α
⊢ foldl (n + 1) f x = List.foldl f x (list (n + 1))
```
