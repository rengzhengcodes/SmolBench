## Current goal
```
⊢ swapAt! a i v = (a[i], set a { val := i, isLt := h } v)
```

## Full tactic state
```
α : Type u_1
a : Array α
i : Nat
v : α
h : i < size a
⊢ swapAt! a i v = (a[i], set a { val := i, isLt := h } v)
```
