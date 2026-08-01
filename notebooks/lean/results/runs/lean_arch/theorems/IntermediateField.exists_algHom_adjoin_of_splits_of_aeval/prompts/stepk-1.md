## Current goal
```
⊢ ∃ φ, φ { val := x, property := hx } = y
```

## Full tactic state
```
case intro
F : Type u_1
E : Type u_2
K : Type u_3
inst✝⁴ : Field F
inst✝³ : Field E
inst✝² : Field K
inst✝¹ : Algebra F E
inst✝ : Algebra F K
S : Set E
hK : ∀ s ∈ S, IsIntegral F s ∧ Splits (algebraMap F K) (minpoly F s)
hK' : ∀ (s : E), IsIntegral F s ∧ Splits (algebraMap F K) (minpoly F s)
L : IntermediateField F E
f : ↥L →ₐ[F] K
hL : L ≤ adjoin F S
hS : adjoin F S = ⊤
x : E
hx : x ∈ adjoin F S
y : K
hy : (aeval y) (minpoly F x) = 0
ix : IsIntegral F ↑{ val := x, property := hx }
φ : ↥(adjoin F S) →ₐ[F] K
hφ : AlgHom.comp φ (inclusion ⋯) = (algHomAdjoinIntegralEquiv F ix).symm { val := y, property := ⋯ }
⊢ ∃ φ, φ { val := x, property := hx } = y
```
