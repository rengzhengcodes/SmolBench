## Current goal
```
⊢ ((interpolate s v) fun i => eval (v i) f) = (interpolate s v) r
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
f : F[X]
hvs : Set.InjOn v ↑s
degree_f_lt : degree f < ↑s.card
eval_f : ∀ i ∈ s, eval (v i) f = r i
⊢ ((interpolate s v) fun i => eval (v i) f) = (interpolate s v) r
```
