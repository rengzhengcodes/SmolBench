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

## Transitive premise context (1-hop, 14/14 premises, ≈1853 tokens)
### `IsAlgClosed` (commanddeclaration) at `Mathlib/FieldTheory/IsAlgClosed/Basic.lean`
```lean
/-- Typeclass for algebraically closed fields.

To show `Polynomial.Splits p f` for an arbitrary ring homomorphism `f`,
see `IsAlgClosed.splits_codomain` and `IsAlgClosed.splits_domain`.
-/
class IsAlgClosed : Prop where
  splits : ∀ p : k[X], p.Splits <| RingHom.id k
```

### `Polynomial.natSepDegree_eq_of_splits` (commanddeclaration) at `Mathlib/FieldTheory/SeparableDegree.lean`
```lean
/-- If a polynomial splits over `E`, then its separable degree is equal to
the number of distinct roots of it over `E`. -/
theorem natSepDegree_eq_of_splits (h : f.Splits (algebraMap F E)) :
    f.natSepDegree = (f.aroots E).toFinset.card := by
  rw [aroots, ← (SplittingField.lift f h).comp_algebraMap, ← map_map,
    roots_map _ ((splits_id_iff_splits _).mpr <| SplittingField.splits f),
    Multiset.toFinset_map, Finset.card_image_of_injective _ (RingHom.injective _), natSepDegree]
```

### `IsAlgClosed.splits_codomain` (commanddeclaration) at `Mathlib/FieldTheory/IsAlgClosed/Basic.lean`
```lean
/-- Every polynomial splits in the field extension `f : K →+* k` if `k` is algebraically closed.

See also `IsAlgClosed.splits_domain` for the case where `K` is algebraically closed.
-/
theorem IsAlgClosed.splits_codomain {k K : Type*} [Field k] [IsAlgClosed k] [Field K] {f : K →+* k}
    (p : K[X]) : p.Splits f := by convert IsAlgClosed.splits (p.map f); simp [splits_map_iff]
```

### `closure` (commanddeclaration) at `Mathlib/Topology/Defs/Basic.lean`
```lean
/-- The closure of `s` is the smallest closed set containing `s`. -/
def closure (s : Set X) : Set X :=
  ⋂₀ { t | IsClosed t ∧ s ⊆ t }
```

### `MvPolynomial` (commanddeclaration) at `Mathlib/Data/MvPolynomial/Basic.lean`
```lean
/-- Multivariate polynomial, where `σ` is the index set of the variables and
  `R` is the coefficient ring -/
def MvPolynomial (σ : Type*) (R : Type*) [CommSemiring R] :=
  AddMonoidAlgebra R (σ →₀ ℕ)
```

### `AlgebraicClosureAux` (commanddeclaration) at `Mathlib/FieldTheory/IsAlgClosed/AlgebraicClosure.lean`
```lean
/-- Auxiliary construction for `AlgebraicClosure`. Although `AlgebraicClosureAux` does define
the algebraic closure of a field, it is redefined at `AlgebraicClosure` in order to make sure
certain instance diamonds commute by definition.
-/
def AlgebraicClosureAux [Field k] : Type u :=
  Ring.DirectLimit (AlgebraicClosure.Step k) fun i j h => AlgebraicClosure.toStepOfLE k i j h
```

### `RingHom.ker` (commanddeclaration) at `Mathlib/RingTheory/Ideal/Operations.lean`
```lean
/-- Kernel of a ring homomorphism as an ideal of the domain. -/
def ker : Ideal R :=
  Ideal.comap f ⊥
```

### `MvPolynomial.aeval` (commanddeclaration) at `Mathlib/Data/MvPolynomial/Basic.lean`
```lean
/-- A map `σ → S₁` where `S₁` is an algebra over `R` generates an `R`-algebra homomorphism
from multivariate polynomials over `σ` to `S₁`. -/
def aeval : MvPolynomial σ R →ₐ[R] S₁ :=
  { eval₂Hom (algebraMap R S₁) f with commutes' := fun _r => eval₂_C _ _ _ }
```

### `CommRing` (commanddeclaration) at `Mathlib/Algebra/Ring/Defs.lean`
```lean
class CommRing (α : Type u) extends Ring α, CommMonoid α
```

### `IsDomain` (commanddeclaration) at `Mathlib/Algebra/Ring/Defs.lean`
```lean
/-- A domain is a nontrivial semiring such multiplication by a non zero element is cancellative,
  on both sides. In other words, a nontrivial semiring `R` satisfying
  `∀ {a b c : R}, a ≠ 0 → a * b = a * c → b = c` and
  `∀ {a b c : R}, b ≠ 0 → a * b = c * b → a = c`.

  This is implemented as a mixin for `Semiring α`.
  To obtain an integral domain use `[CommRing α] [IsDomain α]`. -/
class IsDomain (α : Type u) [Semiring α] extends IsCancelMulZero α, Nontrivial α : Prop
```

### `Algebra` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- An associative unital `R`-algebra is a semiring `A` equipped with a map into its center `R → A`.

See the implementation notes in this file for discussion of the details of this definition.
-/
-- Porting note: unsupported @[nolint has_nonempty_instance]
class Algebra (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] extends SMul R A,
  R →+* A where
  commutes' : ∀ r x, toRingHom r * x = x * toRingHom r
  smul_def' : ∀ r x, r • x = toRingHom r * x
```

### `NoZeroSMulDivisors` (commanddeclaration) at `Mathlib/Algebra/Module/Basic.lean`
```lean
/-- `NoZeroSMulDivisors R M` states that a scalar multiple is `0` only if either argument is `0`.
This is a version of saying that `M` is torsion free, without assuming `R` is zero-divisor free.

The main application of `NoZeroSMulDivisors R M`, when `M` is a module,
is the result `smul_eq_zero`: a scalar multiple is `0` iff either argument is `0`.

It is a generalization of the `NoZeroDivisors` class to heterogeneous multiplication.
-/
@[mk_iff]
class NoZeroSMulDivisors (R M : Type*) [Zero R] [Zero M] [SMul R M] : Prop where
  /-- If scalar multiplication yields zero, either the scalar or the vector was zero. -/
  eq_zero_or_eq_zero_of_smul_eq_zero : ∀ {c : R} {x : M}, c • x = 0 → c = 0 ∨ x = 0
```

### `Polynomial.aroots` (commanddeclaration) at `Mathlib/Data/Polynomial/RingDivision.lean`
```lean
/-- Given a polynomial `p` with coefficients in a ring `T` and a `T`-algebra `S`, `aroots p S` is
the multiset of roots of `p` regarded as a polynomial over `S`. -/
noncomputable abbrev aroots (p : T[X]) (S) [CommRing S] [IsDomain S] [Algebra T S] : Multiset S :=
  (p.map (algebraMap T S)).roots
```

### `Polynomial.aroots_C_mul` (commanddeclaration) at `Mathlib/Data/Polynomial/RingDivision.lean`
```lean
@[simp]
theorem aroots_C_mul [CommRing S] [IsDomain S] [Algebra T S]
    [NoZeroSMulDivisors T S] {a : T} (p : T[X]) (ha : a ≠ 0) :
    (C a * p).aroots S = p.aroots S := by
  rw [aroots_def, Polynomial.map_mul, map_C, roots_C_mul]
  rwa [map_ne_zero_iff]
  exact NoZeroSMulDivisors.algebraMap_injective T S
```
