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

## Transitive premise context (1-hop, 9/9 premises, ≈724 tokens)
### `Lean.Parser.Category.attr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Notation.lean`
```lean
/-- `attr` is a builtin syntax category for attributes.
Declarations can be annotated with attributes using the `@[...]` notation. -/
def attr : Category := {}

/-- `stx` is a builtin syntax category for syntax. This is the abbreviated
parser notation used inside `syntax` and `macro` declarations. -/
```

### `one_nsmul` (commanddeclaration) at `Mathlib/Algebra/GroupPower/Basic.lean`
```lean
@[simp]
theorem one_nsmul (a : A) : 1 • a = a := by rw [succ_nsmul, zero_nsmul, add_zero]
```

### `pow_succ` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive succ_nsmul]
theorem pow_succ (a : M) (n : ℕ) : a ^ (n + 1) = a * a ^ n :=
  Monoid.npow_succ n a
```

### `pow_zero` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive zero_nsmul, simp]
theorem pow_zero (a : M) : a ^ 0 = 1 :=
  Monoid.npow_zero _
```

### `mul_one` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive (attr := simp)]
theorem mul_one : ∀ a : M, a * 1 = a :=
  MulOneClass.mul_one
```

### `iterateFrobeniusEquiv` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
/-- The iterated Frobenius automorphism for a perfect ring. -/
@[simps! apply]
noncomputable def iterateFrobeniusEquiv : R ≃+* R :=
  RingEquiv.ofBijective (iterateFrobenius R p n) (bijective_iterateFrobenius R p n)
```

### `frobeniusEquiv` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
/-- The Frobenius automorphism for a perfect ring. -/
@[simps! apply]
noncomputable def frobeniusEquiv : R ≃+* R :=
  RingEquiv.ofBijective (frobenius R p) PerfectRing.bijective_frobenius
```

### `RingEquiv.ext` (commanddeclaration) at `Mathlib/Algebra/Ring/Equiv.lean`
```lean
/-- Two ring isomorphisms agree if they are defined by the
    same underlying function. -/
@[ext]
theorem ext {f g : R ≃+* S} (h : ∀ x, f x = g x) : f = g :=
  DFunLike.ext f g h
```

### `iterateFrobeniusEquiv_one_apply` (commanddeclaration) at `Mathlib/FieldTheory/Perfect.lean`
```lean
theorem iterateFrobeniusEquiv_one_apply (x : R) : iterateFrobeniusEquiv R p 1 x = x ^ p := by
  rw [iterateFrobeniusEquiv_def, pow_one]
```
