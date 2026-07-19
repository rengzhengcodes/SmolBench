## Current goal
```
⊢ IsLeast s (argminOn id ⋯ s hs)
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
inst✝¹ : ConditionallyCompleteLinearOrder α
s t : Set α
a b : α
inst✝ : IsWellOrder α fun x x_1 => x < x_1
hs : Set.Nonempty s
⊢ IsLeast s (argminOn id ⋯ s hs)
```
