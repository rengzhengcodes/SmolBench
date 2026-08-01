## Current goal
```
⊢ (RingEquiv.symm (equiv i j p)) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)
```

## Full tactic state
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹¹ : CommRing K
inst✝¹⁰ : CommRing L
inst✝⁹ : CommRing M
inst✝⁸ : CommRing N
i : K →+* L
j : K →+* M
k : K →+* N
f : L →+* M
g : L →+* N
p : ℕ
inst✝⁷ : ExpChar K p
inst✝⁶ : ExpChar L p
inst✝⁵ : ExpChar M p
inst✝⁴ : ExpChar N p
inst✝³ : PerfectRing L p
inst✝² : IsPerfectClosure i p
inst✝¹ : PerfectRing M p
inst✝ : IsPerfectClosure j p
x : M
n : ℕ
y : K
h : j y = x ^ p ^ n
⊢ (RingEquiv.symm (equiv i j p)) x = (RingEquiv.symm (iterateFrobeniusEquiv L p n)) (i y)
```
