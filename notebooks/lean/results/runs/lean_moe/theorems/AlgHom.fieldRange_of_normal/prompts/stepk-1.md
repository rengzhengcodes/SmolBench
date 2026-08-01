## Current goal
```
⊢ fieldRange f = E
```

## Full tactic state
```
F : Type u_1
K : Type u_2
inst✝¹⁹ : Field F
inst✝¹⁸ : Field K
inst✝¹⁷ : Algebra F K
K₁ : Type u_3
K₂ : Type u_4
K₃ : Type u_5
inst✝¹⁶ : Field F
inst✝¹⁵ : Field K₁
inst✝¹⁴ : Field K₂
inst✝¹³ : Field K₃
inst✝¹² : Algebra F K₁
inst✝¹¹ : Algebra F K₂
inst✝¹⁰ : Algebra F K₃
ϕ : K₁ →ₐ[F] K₂
χ : K₁ ≃ₐ[F] K₂
ψ : K₂ →ₐ[F] K₃
ω : K₂ ≃ₐ[F] K₃
E✝ : Type u_6
inst✝⁹ : Field E✝
inst✝⁸ : Algebra F E✝
inst✝⁷ : Algebra E✝ K₁
inst✝⁶ : Algebra E✝ K₂
inst✝⁵ : Algebra E✝ K₃
inst✝⁴ : IsScalarTower F E✝ K₁
inst✝³ : IsScalarTower F E✝ K₂
inst✝² : IsScalarTower F E✝ K₃
inst✝¹ : Algebra F K
E : IntermediateField F K
inst✝ : Normal F ↥E
f : ↥E →ₐ[F] K
this : Algebra ↥E ↥E := Algebra.id ↥E
g : ↥E ≃ₐ[F] ↥E := restrictNormal' f ↥E
⊢ fieldRange f = E
```
