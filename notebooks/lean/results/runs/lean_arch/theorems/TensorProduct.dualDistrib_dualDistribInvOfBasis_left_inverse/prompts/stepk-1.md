## Current goal
```
⊢ ∑ x : κ, (Finsupp.single i 1) i * (Finsupp.single x 1) j * ((Finsupp.single i' 1) i * (Finsupp.single j' 1) x) = 0
```

## Full tactic state
```
case mk.mk.h₁
R : Type u_1
A : Type u_2
M : Type u_3
N : Type u_4
ι : Type u_5
κ : Type u_6
inst✝⁸ : DecidableEq ι
inst✝⁷ : DecidableEq κ
inst✝⁶ : Fintype ι
inst✝⁵ : Fintype κ
inst✝⁴ : CommRing R
inst✝³ : AddCommGroup M
inst✝² : AddCommGroup N
inst✝¹ : Module R M
inst✝ : Module R N
b : Basis ι R M
c : Basis κ R N
i : ι
j : κ
i' : ι
j' : κ
a✝ : i ∉ Finset.univ
⊢ ∑ x : κ, (Finsupp.single i 1) i * (Finsupp.single x 1) j * ((Finsupp.single i' 1) i * (Finsupp.single j' 1) x) = 0
```
