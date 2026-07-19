## Current goal
```
⊢ Finset.image (⇑(frobenius R p)) (toFinset (roots ((expand R p) f))) = toFinset (roots f)
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
⊢ Finset.image (⇑(frobenius R p)) (toFinset (roots ((expand R p) f))) = toFinset (roots f)
```
