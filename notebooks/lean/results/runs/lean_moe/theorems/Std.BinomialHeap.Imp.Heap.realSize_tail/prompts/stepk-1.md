## Current goal
```
⊢ realSize (Option.getD (some tl) nil) = realSize s - 1
```

## Full tactic state
```
α : Type u_1
le : α → α → Bool
s tl : Heap α
eq : tail? le s = some tl
⊢ realSize (Option.getD (some tl) nil) = realSize s - 1
```
