## Current goal
```
⊢ ∃ a ∈ Finset.erase s i, eval (v j) (basisDivisor (v i) (v a)) = 0
```

## Full tactic state
```
F : Type u_1
inst✝¹ : Field F
ι : Type u_2
inst✝ : DecidableEq ι
s : Finset ι
v : ι → F
i j : ι
hij : i ≠ j
hj : j ∈ s
⊢ ∃ a ∈ Finset.erase s i, eval (v j) (basisDivisor (v i) (v a)) = 0
```
