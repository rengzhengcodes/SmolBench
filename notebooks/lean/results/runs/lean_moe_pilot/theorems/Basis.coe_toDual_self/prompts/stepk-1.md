## Current goal
```
⊢ ((toDual b) (b i)) x✝ = (coord b i) x✝
```

## Full tactic state
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
inst✝³ : CommSemiring R
inst✝² : AddCommMonoid M
inst✝¹ : Module R M
inst✝ : DecidableEq ι
b : Basis ι R M
i : ι
x✝ : M
⊢ ((toDual b) (b i)) x✝ = (coord b i) x✝
```
