## Current goal
```
⊢ (trace R M) ((dualTensorHom R M M) x) = (contractLeft R M) x
```

## Full tactic state
```
R : Type u_1
inst✝¹² : CommRing R
M : Type u_2
inst✝¹¹ : AddCommGroup M
inst✝¹⁰ : Module R M
N : Type u_3
P : Type u_4
inst✝⁹ : AddCommGroup N
inst✝⁸ : Module R N
inst✝⁷ : AddCommGroup P
inst✝⁶ : Module R P
ι : Type u_5
inst✝⁵ : Module.Free R M
inst✝⁴ : Module.Finite R M
inst✝³ : Module.Free R N
inst✝² : Module.Finite R N
inst✝¹ : Module.Free R P
inst✝ : Module.Finite R P
x : Module.Dual R M ⊗[R] M
⊢ (trace R M) ((dualTensorHom R M M) x) = (contractLeft R M) x
```
