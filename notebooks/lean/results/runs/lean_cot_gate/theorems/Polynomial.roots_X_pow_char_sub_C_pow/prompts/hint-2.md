## Current goal
```
⊢ roots ((X ^ p - C y) ^ m) = (m * p) • {(RingEquiv.symm (frobeniusEquiv R p)) y}
```

## Full tactic state
```
R : Type u_1
inst✝³ : CommRing R
inst✝² : IsDomain R
p n : ℕ
inst✝¹ : ExpChar R p
f : R[X]
inst✝ : PerfectRing R p
y : R
m : ℕ
H : roots ((X ^ p ^ 1 - C y) ^ m) = (m * p ^ 1) • {(RingEquiv.symm (iterateFrobeniusEquiv R p 1)) y}
⊢ roots ((X ^ p - C y) ^ m) = (m * p) • {(RingEquiv.symm (frobeniusEquiv R p)) y}
```

## Proof so far (1 tactic)
```lean
have H := roots_X_pow_char_pow_sub_C_pow (p := p) (n := 1) (y := y) (m := m)
```

## Theorem
`Polynomial.roots_X_pow_char_sub_C_pow` in `Mathlib/FieldTheory/Perfect.lean`

## Premises used in the next tactic
- `pow_one`
- `iterateFrobeniusEquiv_one`

## Premise signatures
### `pow_one` (commanddeclaration)
```lean
@[to_additive existing (attr := simp) one_nsmul]
theorem pow_one (a : M) : a ^ 1 = a
```

### `iterateFrobeniusEquiv_one` (commanddeclaration)
```lean
@[simp]
theorem iterateFrobeniusEquiv_one : iterateFrobeniusEquiv R p 1 = frobeniusEquiv R p
```

## Premise full source (with proof)
### `pow_one` (commanddeclaration) at `Mathlib/Algebra/GroupPower/Basic.lean`
```lean
@[to_additive existing (attr := simp) one_nsmul]
theorem pow_one (a : M) : a ^ 1 = a := by rw [pow_succ, pow_zero, mul_one]
```

### `iterateFrobeniusEquiv_one` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
@[simp]
theorem iterateFrobeniusEquiv_one : iterateFrobeniusEquiv R p 1 = frobeniusEquiv R p :=
  RingEquiv.ext (iterateFrobeniusEquiv_one_apply R p)
```
