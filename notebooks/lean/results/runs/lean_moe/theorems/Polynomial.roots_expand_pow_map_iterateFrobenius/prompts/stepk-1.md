## Current goal
```
⊢ Multiset.map (⇑(iterateFrobenius R p n)) (roots ((expand R (p ^ n)) f)) = p ^ n • roots f
```

## Full tactic state
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
inst✝ : PerfectRing R p
⊢ Multiset.map (⇑(iterateFrobenius R p n)) (roots ((expand R (p ^ n)) f)) = p ^ n • roots f
```
