## Current goal
```
⊢ FiniteDimensional 𝕜 M
```

## Full tactic state
```
R : Type u_1
inst✝¹¹ : CommRing R
M : Type u_2
inst✝¹⁰ : AddCommGroup M
inst✝⁹ : Module R M
M' : Type u_3
inst✝⁸ : AddCommGroup M'
inst✝⁷ : Module R M'
ι : Type u_4
inst✝⁶ : DecidableEq ι
inst✝⁵ : Fintype ι
e : Basis ι R M
A : Type u_5
inst✝⁴ : CommRing A
inst✝³ : Module A M
κ : Type u_6
inst✝² : Fintype κ
𝕜 : Type u_7
inst✝¹ : Field 𝕜
inst✝ : Module 𝕜 M
f : M →ₗ[𝕜] M
hf : LinearMap.det f = 0
⊢ FiniteDimensional 𝕜 M
```
