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
