## Current goal
```
⊢ (lift j i p) ((lift i j p) x) = x
```

## Full tactic state
```
K : Type u_1
L : Type u_2
M : Type u_3
N : Type u_4
inst✝¹² : CommRing K
inst✝¹¹ : CommRing L
inst✝¹⁰ : CommRing M
inst✝⁹ : CommRing N
i : K →+* L
j : K →+* M
k : K →+* N
f : L →+* M
g : L →+* N
p : ℕ
inst✝⁸ : ExpChar K p
inst✝⁷ : ExpChar L p
inst✝⁶ : ExpChar M p
inst✝⁵ : ExpChar N p
inst✝⁴ : PerfectRing M p
inst✝³ : IsPRadical i p
inst✝² : PerfectRing N p
inst✝¹ : IsPRadical j p
inst✝ : PerfectRing L p
x : L
⊢ (lift j i p) ((lift i j p) x) = x
```
