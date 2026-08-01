## Current goal
```
⊢ ¬Irreducible (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ p)
```

## Full tactic state
```
R✝ : Type u_1
p✝ m n : ℕ
inst✝⁶ : CommSemiring R✝
inst✝⁵ : ExpChar R✝ p✝
inst✝⁴ : PerfectRing R✝ p✝
R : Type u_2
p : ℕ
inst✝³ : CommSemiring R
inst✝² : Fact (Nat.Prime p)
inst✝¹ : CharP R p
inst✝ : PerfectRing R p
f : R[X]
⊢ ¬Irreducible (map (↑(RingEquiv.symm (frobeniusEquiv R p))) f ^ p)
```
