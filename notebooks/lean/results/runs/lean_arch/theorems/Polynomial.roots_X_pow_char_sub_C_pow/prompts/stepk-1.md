## Current goal
```
⊢ roots ((X ^ p - C y) ^ m) = (m * p) • {(RingEquiv.symm (frobeniusEquiv R p)) y}
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
y : R
m : ℕ
H : roots ((X ^ p ^ 1 - C y) ^ m) = (m * p ^ 1) • {(RingEquiv.symm (iterateFrobeniusEquiv R p 1)) y}
⊢ roots ((X ^ p - C y) ^ m) = (m * p) • {(RingEquiv.symm (frobeniusEquiv R p)) y}
```
