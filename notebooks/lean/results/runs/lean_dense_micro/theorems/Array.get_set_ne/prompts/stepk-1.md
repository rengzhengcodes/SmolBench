## Current goal
```
⊢ (set a i v)[j] = a[j]
```

## Full tactic state
```
α : Type u_1
a : Array α
i : Fin (size a)
j : Nat
v : α
hj : j < size a
h : ↑i ≠ j
⊢ (set a i v)[j] = a[j]
```
