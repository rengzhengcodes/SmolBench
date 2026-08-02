## Current goal
```
⊢ restrictScalars F (extendScalars hi) = restrictScalars F (adjoin ↥M ↑E')
```

## Full tactic state
```
F : Type u
E : Type v
inst✝⁷ : Field F
inst✝⁶ : Field E
inst✝⁵ : Algebra F E
K : Type w
inst✝⁴ : Field K
inst✝³ : Algebra F K
inst✝² : Algebra E K
inst✝¹ : IsScalarTower F E K
S : Set K
inst✝ : IsPurelyInseparable F E
M : IntermediateField F K := adjoin F S
halg : Algebra.IsAlgebraic F ↥M
L : IntermediateField E K := adjoin E S
E' : IntermediateField F K := AlgHom.fieldRange (IsScalarTower.toAlgHom F E K)
j : E ≃ₐ[F] ↥E' := AlgEquiv.ofInjectiveField (IsScalarTower.toAlgHom F E K)
hi : M ≤ restrictScalars F L
i : ↥M →+* ↥L := Subsemiring.inclusion hi
this✝¹ : Algebra ↥M ↥L := RingHom.toAlgebra i
this✝ : SMul ↥M ↥L := Algebra.toSMul
this : IsScalarTower F ↥M ↥L
q : ℕ
h✝ : ExpChar F q
⊢ restrictScalars F (extendScalars hi) = restrictScalars F (adjoin ↥M ↑E')
```
