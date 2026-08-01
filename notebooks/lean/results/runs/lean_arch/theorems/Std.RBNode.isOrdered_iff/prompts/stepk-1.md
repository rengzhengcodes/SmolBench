## Current goal
```
⊢ isOrdered cmp t none = true ↔ Ordered cmp t
```

## Full tactic state
```
α : Type u_1
cmp : α → α → Ordering
inst✝ : TransCmp cmp
t : RBNode α
⊢ isOrdered cmp t none = true ↔ Ordered cmp t
```
