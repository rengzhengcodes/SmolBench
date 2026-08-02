## Current goal
```
⊢ (coord R M x h) { val := x, property := ⋯ } = 1
```

## Full tactic state
```
R : Type u_1
R₂ : Type u_2
K : Type u_3
M : Type u_4
M₂ : Type u_5
V : Type u_6
S : Type u_7
inst✝³ : Ring R
inst✝² : AddCommGroup M
inst✝¹ : Module R M
inst✝ : NoZeroSMulDivisors R M
x : M
h : x ≠ 0
⊢ (coord R M x h) { val := x, property := ⋯ } = 1
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`LinearEquiv.coord_self` in `Mathlib/LinearAlgebra/Span.lean`

## Premises used in the next tactic
- `LinearEquiv.toSpanNonzeroSingleton_one`
- `LinearEquiv.symm_apply_apply`

## Premise signatures
### `LinearEquiv.toSpanNonzeroSingleton_one` (commanddeclaration)
```lean
theorem toSpanNonzeroSingleton_one :
    LinearEquiv.toSpanNonzeroSingleton R M x h 1 =
      (⟨x, Submodule.mem_span_singleton_self x⟩ : R ∙ x)
```

### `LinearEquiv.symm_apply_apply` (commanddeclaration)
```lean
@[simp]
theorem symm_apply_apply (b : M) : e.symm (e b) = b
```

## Premise full source (with proof)
### `LinearEquiv.toSpanNonzeroSingleton_one` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
theorem toSpanNonzeroSingleton_one :
    LinearEquiv.toSpanNonzeroSingleton R M x h 1 =
      (⟨x, Submodule.mem_span_singleton_self x⟩ : R ∙ x) := by simp
```

### `LinearEquiv.symm_apply_apply` (commanddeclaration) at `Mathlib/Algebra/Module/Equiv.lean`
```lean
@[simp]
theorem symm_apply_apply (b : M) : e.symm (e b) = b :=
  e.left_inv b
```

## Transitive premise context (1-hop, 2/2 premises, ≈236 tokens)
### `LinearEquiv.toSpanNonzeroSingleton` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
/-- Given a nonzero element `x` of a torsion-free module `M` over a ring `R`, the natural
isomorphism from `R` to the span of `x` given by $r \mapsto r \cdot x$. -/
noncomputable
def toSpanNonzeroSingleton : R ≃ₗ[R] R ∙ x :=
  LinearEquiv.trans
    (LinearEquiv.ofInjective (LinearMap.toSpanSingleton R M x)
      (ker_eq_bot.1 <| ker_toSpanSingleton R M h))
    (LinearEquiv.ofEq (range <| toSpanSingleton R M x) (R ∙ x) (span_singleton_eq_range R M x).symm)
```

### `Submodule.mem_span_singleton_self` (commanddeclaration) at `Mathlib/LinearAlgebra/Span.lean`
```lean
theorem mem_span_singleton_self (x : M) : x ∈ R ∙ x :=
  subset_span rfl
```
