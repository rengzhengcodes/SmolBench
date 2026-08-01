## Current goal
```
⊢ get (set l m a) { val := n, isLt := h✝ } = if m = n then a else get l { val := n, isLt := ⋯ }
```

## Full tactic state
```
α : Type u_1
a : α
m n : Nat
l : List α
h✝ : n < length (set l m a)
h : ¬m = n
⊢ get (set l m a) { val := n, isLt := h✝ } = if m = n then a else get l { val := n, isLt := ⋯ }
```
