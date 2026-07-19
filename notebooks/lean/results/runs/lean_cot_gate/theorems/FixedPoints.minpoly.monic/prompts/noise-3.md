## Current goal
```
⊢ Polynomial.Monic (prodXSubSMul G F x)
```

## Full tactic state
```
M : Type u
inst✝⁵ : Monoid M
G : Type u
inst✝⁴ : Group G
F : Type v
inst✝³ : Field F
inst✝² : MulSemiringAction M F
inst✝¹ : MulSemiringAction G F
m : M
inst✝ : Fintype G
x : F
⊢ Polynomial.Monic (prodXSubSMul G F x)
```

## Proof so far (1 tactic)
```lean
simp only [minpoly, Polynomial.monic_toSubring]
```

## Theorem
`FixedPoints.minpoly.monic` in `Mathlib/FieldTheory/Fixed.lean`

## Premises used in the next tactic
- `prodXSubSMul.monic`

## Premise signatures
### `prodXSubSMul.monic` (commanddeclaration)
```lean
theorem prodXSubSMul.monic (x : R) : (prodXSubSMul G R x).Monic
```

## Premise full source (with proof)
### `prodXSubSMul.monic` (commanddeclaration) at `Mathlib/Algebra/Polynomial/GroupRingAction.lean`
```lean
theorem prodXSubSMul.monic (x : R) : (prodXSubSMul G R x).Monic :=
  Polynomial.monic_prod_of_monic _ _ fun _ _ ↦ Polynomial.monic_X_sub_C _
```

## Filler (hint:2 → hint:3 token-match, ≈391 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur
