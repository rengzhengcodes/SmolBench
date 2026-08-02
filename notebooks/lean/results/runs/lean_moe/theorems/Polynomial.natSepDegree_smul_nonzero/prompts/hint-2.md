## Current goal
```
⊢ natSepDegree (x • f) = natSepDegree f
```

## Full tactic state
```
F : Type u
E : Type v
inst✝⁴ : Field F
inst✝³ : Field E
inst✝² : Algebra F E
K : Type w
inst✝¹ : Field K
inst✝ : Algebra F K
f : F[X]
x : F
hx : x ≠ 0
⊢ natSepDegree (x • f) = natSepDegree f
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Polynomial.natSepDegree_smul_nonzero` in `Mathlib/FieldTheory/SeparableDegree.lean`

## Premises used in the next tactic
- `Polynomial.natSepDegree_eq_of_isAlgClosed`
- `AlgebraicClosure`
- `Polynomial.aroots_smul_nonzero`

## Premise signatures
### `Polynomial.natSepDegree_eq_of_isAlgClosed` (commanddeclaration)
```lean
theorem natSepDegree_eq_of_isAlgClosed [IsAlgClosed E] :
    f.natSepDegree = (f.aroots E).toFinset.card
```

### `AlgebraicClosure` (commanddeclaration)
```lean
def AlgebraicClosure : Type u
```

### `Polynomial.aroots_smul_nonzero` (commanddeclaration)
```lean
@[simp]
theorem aroots_smul_nonzero [CommRing S] [IsDomain S] [Algebra T S]
    [NoZeroSMulDivisors T S] {a : T} (p : T[X]) (ha : a ≠ 0) :
    (a • p).aroots S = p.aroots S
```

## Premise full source (with proof)
### `Polynomial.natSepDegree_eq_of_isAlgClosed` (commanddeclaration) at `Mathlib/FieldTheory/SeparableDegree.lean`
```lean
/-- The separable degree of a polynomial is equal to
the number of distinct roots of it over any algebraically closed field. -/
theorem natSepDegree_eq_of_isAlgClosed [IsAlgClosed E] :
    f.natSepDegree = (f.aroots E).toFinset.card :=
  natSepDegree_eq_of_splits f (IsAlgClosed.splits_codomain f)
```

### `AlgebraicClosure` (commanddeclaration) at `Mathlib/FieldTheory/IsAlgClosed/AlgebraicClosure.lean`
```lean
/-- The canonical algebraic closure of a field, the direct limit of adding roots to the field for
each polynomial over the field. -/
def AlgebraicClosure : Type u :=
  MvPolynomial (AlgebraicClosureAux k) k ⧸
    RingHom.ker (MvPolynomial.aeval (R := k) id).toRingHom
```

### `Polynomial.aroots_smul_nonzero` (commanddeclaration) at `Mathlib/Data/Polynomial/RingDivision.lean`
```lean
@[simp]
theorem aroots_smul_nonzero [CommRing S] [IsDomain S] [Algebra T S]
    [NoZeroSMulDivisors T S] {a : T} (p : T[X]) (ha : a ≠ 0) :
    (a • p).aroots S = p.aroots S := by
  rw [smul_eq_C_mul, aroots_C_mul _ ha]
```
