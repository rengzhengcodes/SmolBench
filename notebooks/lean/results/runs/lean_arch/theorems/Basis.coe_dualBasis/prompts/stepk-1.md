## Current goal
```
⊢ ((dualBasis b) i) x = (coord b i) x
```

## Full tactic state
```
case h.h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
inst✝⁴ : CommRing R
inst✝³ : AddCommGroup M
inst✝² : Module R M
inst✝¹ : DecidableEq ι
b : Basis ι R M
inst✝ : _root_.Finite ι
i : ι
x : M
⊢ ((dualBasis b) i) x = (coord b i) x
```
