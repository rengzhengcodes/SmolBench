## Current goal
```
⊢ set l n a = take n l ++ a :: drop (n + 1) l
```

## Full tactic state
```
α : Type u_1
a : α
n : Nat
l : List α
h : n < length l
⊢ set l n a = take n l ++ a :: drop (n + 1) l
```
