## Current goal
```
⊢ ∃ a ∈ Finset.erase s i, eval (v j) (basisDivisor (v i) (v a)) = 0
```

## Full tactic state
```
F : Type u_1
inst✝¹ : Field F
ι : Type u_2
inst✝ : DecidableEq ι
s : Finset ι
v : ι → F
i j : ι
hij : i ≠ j
hj : j ∈ s
⊢ ∃ a ∈ Finset.erase s i, eval (v j) (basisDivisor (v i) (v a)) = 0
```

## Proof so far (1 tactic)
```lean
simp_rw [Lagrange.basis, eval_prod, prod_eq_zero_iff]
```

## Theorem
`Lagrange.eval_basis_of_ne` in `Mathlib/LinearAlgebra/Lagrange.lean`

## Premises used in the next tactic
- `Lagrange.eval_basisDivisor_right`

## Premise signatures
### `Lagrange.eval_basisDivisor_right` (commanddeclaration)
```lean
@[simp]
theorem eval_basisDivisor_right : eval y (basisDivisor x y) = 0
```

## Premise full source (with proof)
### `Lagrange.eval_basisDivisor_right` (commanddeclaration) at `Mathlib/LinearAlgebra/Lagrange.lean`
```lean
@[simp]
theorem eval_basisDivisor_right : eval y (basisDivisor x y) = 0 := by
  simp only [basisDivisor, eval_mul, eval_C, eval_sub, eval_X, sub_self, mul_zero]
```

## Filler (hint:2 → hint:3 token-match, ≈154 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
