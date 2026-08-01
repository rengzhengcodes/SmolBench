## Current goal
```
⊢ (∀ {x : α}, root? (zoom cut t.val).fst = some x → cmpEq cmp (f x) x) →
    OnRoot (fun x => cmpEq cmp (f x) x) (zoom cut t.val).fst
```

## Full tactic state
```
α : Type u_1
cmp : α → α → Ordering
cut : α → Ordering
f : α → α
t : RBSet α cmp
⊢ (∀ {x : α}, root? (zoom cut t.val).fst = some x → cmpEq cmp (f x) x) →
    OnRoot (fun x => cmpEq cmp (f x) x) (zoom cut t.val).fst
```
