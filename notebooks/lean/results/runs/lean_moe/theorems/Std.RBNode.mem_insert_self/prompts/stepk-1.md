## Current goal
```
⊢ ∃ s t_1, toList (insert cmp t v) = s ++ v :: t_1
```

## Full tactic state
```
α : Type u_1
c : RBColor
n : Nat
v : α
cmp : α → α → Ordering
t : RBNode α
ht : Balanced t c n
⊢ ∃ s t_1, toList (insert cmp t v) = s ++ v :: t_1
```
