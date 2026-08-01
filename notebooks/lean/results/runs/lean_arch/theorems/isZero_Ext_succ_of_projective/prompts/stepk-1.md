## Current goal
```
⊢ n + 1 ≠ 0
```

## Full tactic state
```
R : Type u_1
inst✝⁵ : Ring R
C : Type u_2
inst✝⁴ : Category.{u_3, u_2} C
inst✝³ : Abelian C
inst✝² : Linear R C
inst✝¹ : EnoughProjectives C
X Y : C
inst✝ : Projective X
n : ℕ
x : ((ChainComplex.single₀ C).obj X).X (n + 1) ⟶ Y
⊢ n + 1 ≠ 0
```
