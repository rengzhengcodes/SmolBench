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

## Filler (hint:2 → hint:3 token-match, ≈258 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pari
