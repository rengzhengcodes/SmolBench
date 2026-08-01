## Current goal
```
⊢ {i, j} ⊆ s
```

## Full tactic state
```
F : Type u_1
inst✝¹ : Field F
ι : Type u_2
inst✝ : DecidableEq ι
s t : Finset ι
i j : ι
v r r' : ι → F
hvs : Set.InjOn v ↑s
hi : i ∈ s
hj : j ∈ s
hij : i ≠ j
⊢ {i, j} ⊆ s
```
