## Current goal
```
⊢ ((dualBasis b) i) x = (coord b i) x
```

## Full tactic state
```
case h.h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
inst✝⁴ : CommRing R
inst✝³ : AddCommGroup M
inst✝² : Module R M
inst✝¹ : DecidableEq ι
b : Basis ι R M
inst✝ : _root_.Finite ι
i : ι
x : M
⊢ ((dualBasis b) i) x = (coord b i) x
```

## Proof so far (1 tactic)
```lean
ext i x
```

## Theorem
`Basis.coe_dualBasis` in `Mathlib/LinearAlgebra/Dual.lean`

## Premises used in the next tactic
- `Basis.dualBasis_apply`

## Premise signatures
### `Basis.dualBasis_apply` (commanddeclaration)
```lean
theorem dualBasis_apply (i : ι) (m : M) : b.dualBasis i m = b.repr m i
```

## Premise full source (with proof)
### `Basis.dualBasis_apply` (commanddeclaration) at `Mathlib/LinearAlgebra/Dual.lean`
```lean
theorem dualBasis_apply (i : ι) (m : M) : b.dualBasis i m = b.repr m i :=
  b.toDual_apply_right i m
```
