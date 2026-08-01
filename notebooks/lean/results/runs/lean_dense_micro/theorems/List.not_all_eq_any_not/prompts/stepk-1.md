## Current goal
```
⊢ (!(p head✝ && all tail✝ p)) = (!p head✝ || any tail✝ fun a => !p a)
```

## Full tactic state
```
case cons
α : Type u_1
p : α → Bool
head✝ : α
tail✝ : List α
ih : (!all tail✝ p) = any tail✝ fun a => !p a
⊢ (!(p head✝ && all tail✝ p)) = (!p head✝ || any tail✝ fun a => !p a)
```
