## Current goal
```
⊢ dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = map e (dualCoannihilator p)
```

## Full tactic state
```
R : Type u_1
M : Type u_2
N : Type u_3
inst✝⁵ : CommRing R
inst✝⁴ : AddCommGroup M
inst✝³ : Module R M
inst✝² : AddCommGroup N
inst✝¹ : Module R N
inst✝ : IsReflexive R M
e : N ≃ₗ[R] Dual R M
p : Submodule R (Dual R N)
this : IsReflexive R N
⊢ dualAnnihilator (map (LinearEquiv.symm (LinearEquiv.flip e)) p) = map e (dualCoannihilator p)
```
