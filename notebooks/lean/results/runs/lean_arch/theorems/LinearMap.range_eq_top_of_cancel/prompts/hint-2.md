## Current goal
```
⊢ ker 0 = ⊤
```

## Full tactic state
```
R : Type u_1
M : Type u_2
R₂ : Type u_3
M₂ : Type u_4
R₃ : Type u_5
M₃ : Type u_6
inst✝¹⁰ : Ring R
inst✝⁹ : Ring R₂
inst✝⁸ : Ring R₃
inst✝⁷ : AddCommMonoid M
inst✝⁶ : AddCommGroup M₂
inst✝⁵ : AddCommMonoid M₃
inst✝⁴ : Module R M
inst✝³ : Module R₂ M₂
inst✝² : Module R₃ M₃
τ₁₂ : R →+* R₂
τ₂₃ : R₂ →+* R₃
τ₁₃ : R →+* R₃
inst✝¹ : RingHomCompTriple τ₁₂ τ₂₃ τ₁₃
inst✝ : RingHomSurjective τ₁₂
f : M →ₛₗ[τ₁₂] M₂
h : ∀ (u v : M₂ →ₗ[R₂] M₂ ⧸ range f), comp u f = comp v f → u = v
h₁ : comp 0 f = 0
⊢ ker 0 = ⊤
```

## Proof so far (2 tactics)
```lean
have h₁ : (0 : M₂ →ₗ[R₂] M₂ ⧸ (range f)).comp f = 0 := zero_comp _
rw [← Submodule.ker_mkQ (range f), ← h 0 f.range.mkQ (Eq.trans h₁ (range_mkQ_comp _).symm)]
```

## Theorem
`LinearMap.range_eq_top_of_cancel` in `Mathlib/LinearAlgebra/Quotient.lean`

## Premises used in the next tactic
- `LinearMap.ker_zero`

## Premise signatures
### `LinearMap.ker_zero` (commanddeclaration)
```lean
@[simp]
theorem ker_zero : ker (0 : M →ₛₗ[τ₁₂] M₂) = ⊤
```

## Premise full source (with proof)
### `LinearMap.ker_zero` (commanddeclaration) at `Mathlib/Algebra/Module/Submodule/Ker.lean`
```lean
@[simp]
theorem ker_zero : ker (0 : M →ₛₗ[τ₁₂] M₂) = ⊤ :=
  eq_top_iff'.2 fun x => by simp
```
