## Current goal
```
⊢ IsPurelyInseparable F E ↔ ∀ (x : E), ∃ n, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n
```

## Full tactic state
```
F : Type u
E : Type v
inst✝⁴ : Field F
inst✝³ : Field E
inst✝² : Algebra F E
K : Type w
inst✝¹ : Field K
inst✝ : Algebra F K
q : ℕ
hF : ExpChar F q
⊢ IsPurelyInseparable F E ↔ ∀ (x : E), ∃ n, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n
```
