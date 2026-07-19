## Current goal
```
⊢ ((toDual b) (b i)) x✝ = (coord b i) x✝
```

## Full tactic state
```
case h
R : Type uR
M : Type uM
K : Type uK
V : Type uV
ι : Type uι
inst✝³ : CommSemiring R
inst✝² : AddCommMonoid M
inst✝¹ : Module R M
inst✝ : DecidableEq ι
b : Basis ι R M
i : ι
x✝ : M
⊢ ((toDual b) (b i)) x✝ = (coord b i) x✝
```

## Proof so far (1 tactic)
```lean
ext
```

## Theorem
`Basis.coe_toDual_self` in `Mathlib/LinearAlgebra/Dual.lean`

## Premises used in the next tactic
- `Basis.toDual_apply_right`

## Premise signatures
### `Basis.toDual_apply_right` (commanddeclaration)
```lean
theorem toDual_apply_right (i : ι) (m : M) : b.toDual (b i) m = b.repr m i
```

## Premise full source (with proof)
### `Basis.toDual_apply_right` (commanddeclaration) at `Mathlib/LinearAlgebra/Dual.lean`
```lean
theorem toDual_apply_right (i : ι) (m : M) : b.toDual (b i) m = b.repr m i := by
  rw [← b.toDual_total_right, b.total_repr]
```
