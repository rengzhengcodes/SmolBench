## Current goal
```
⊢ NoSibling (Option.getD (some tl) nil)
```

## Full tactic state
```
α : Type u_1
le : α → α → Bool
s tl : Heap α
eq : tail? le s = some tl
⊢ NoSibling (Option.getD (some tl) nil)
```
