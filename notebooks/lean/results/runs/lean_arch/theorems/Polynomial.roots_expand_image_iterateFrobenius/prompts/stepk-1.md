## Current goal
```
⊢ Finset.image (⇑(iterateFrobenius R p n)) (toFinset (roots ((expand R (p ^ n)) f))) = toFinset (roots f)
```

## Full tactic state
```
R : Type u_1
inst✝⁴ : CommRing R
inst✝³ : IsDomain R
p n : ℕ
inst✝² : ExpChar R p
f : R[X]
inst✝¹ : PerfectRing R p
inst✝ : DecidableEq R
⊢ Finset.image (⇑(iterateFrobenius R p n)) (toFinset (roots ((expand R (p ^ n)) f))) = toFinset (roots f)
```
