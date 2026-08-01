## Current goal
```
⊢ IsPurelyInseparable F E ↔ ∀ (x : E), ∃ n, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n
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
q : ℕ
hF : ExpChar F q
⊢ IsPurelyInseparable F E ↔ ∀ (x : E), ∃ n, Polynomial.map (algebraMap F E) (minpoly F x) = (X - C x) ^ q ^ n
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`isPurelyInseparable_iff_minpoly_eq_X_sub_C_pow` in `Mathlib/FieldTheory/PurelyInseparable.lean`

## Premises used in the next tactic
- `isPurelyInseparable_iff_natSepDegree_eq_one`
- `minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow`

## Premise signatures
### `isPurelyInseparable_iff_natSepDegree_eq_one` (commanddeclaration)
```lean
theorem isPurelyInseparable_iff_natSepDegree_eq_one :
    IsPurelyInseparable F E ↔ ∀ x : E, (minpoly F x).natSepDegree = 1
```

### `minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow` (commanddeclaration)
```lean
theorem natSepDegree_eq_one_iff_eq_X_sub_C_pow : (minpoly F x).natSepDegree = 1 ↔
    ∃ n : ℕ, (minpoly F x).map (algebraMap F E) = (X - C x) ^ q ^ n
```

## Premise full source (with proof)
### `isPurelyInseparable_iff_natSepDegree_eq_one` (commanddeclaration) at `Mathlib/FieldTheory/PurelyInseparable.lean`
```lean
/-- A field extension `E / F` is purely inseparable if and only if for every element `x` of `E`,
its minimal polynomial has separable degree one. -/
theorem isPurelyInseparable_iff_natSepDegree_eq_one :
    IsPurelyInseparable F E ↔ ∀ x : E, (minpoly F x).natSepDegree = 1 := by
  obtain ⟨q, _⟩ := ExpChar.exists F
  simp_rw [isPurelyInseparable_iff_pow_mem F q, minpoly.natSepDegree_eq_one_iff_pow_mem q]
```

### `minpoly.natSepDegree_eq_one_iff_eq_X_sub_C_pow` (commanddeclaration) at `Mathlib/FieldTheory/SeparableDegree.lean`
```lean
/-- The minimal polynomial of an element `x` of `E / F` of exponential characteristic `q` has
separable degree one if and only if the minimal polynomial is of the form
`(X - x) ^ (q ^ n)` for some `n : ℕ`. -/
theorem natSepDegree_eq_one_iff_eq_X_sub_C_pow : (minpoly F x).natSepDegree = 1 ↔
    ∃ n : ℕ, (minpoly F x).map (algebraMap F E) = (X - C x) ^ q ^ n := by
  haveI := expChar_of_injective_algebraMap (algebraMap F E).injective q
  haveI := expChar_of_injective_algebraMap (NoZeroSMulDivisors.algebraMap_injective E E[X]) q
  refine ⟨fun h ↦ ?_, fun ⟨n, h⟩ ↦ (natSepDegree_eq_one_iff_pow_mem q).2 ?_⟩
  · obtain ⟨n, y, h⟩ := (natSepDegree_eq_one_iff_eq_X_pow_sub_C q).1 h
    have hx := congr_arg (Polynomial.aeval x) h.symm
    rw [minpoly.aeval, map_sub, map_pow, aeval_X, aeval_C, sub_eq_zero, eq_comm] at hx
    use n
    rw [h, Polynomial.map_sub, Polynomial.map_pow, map_X, map_C, hx, map_pow, ← sub_pow_expChar_pow]
  apply_fun constantCoeff at h
  simp_rw [map_pow, map_sub, constantCoeff_apply, coeff_map, coeff_X_zero, coeff_C_zero] at h
  rw [zero_sub, neg_pow, ExpChar.neg_one_pow_expChar_pow] at h
  exact ⟨n, -(minpoly F x).coeff 0, by rw [map_neg, h]; ring1⟩
```

## Transitive premise context (1-hop, 26/26 premises, ≈3498 tokens)
### `Lean.Xml.Parser.element` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Data/Xml/Parser.lean`
```lean
  /-- https://www.w3.org/TR/xml/#NT-element -/
  partial def element : Parsec Element := do
    let elem ← Parser.elementPrefix
    EmptyElemTag elem <|> STag elem <*> content <* ETag
```

### `IsPurelyInseparable` (commanddeclaration) at `Mathlib/FieldTheory/PurelyInseparable.lean`
```lean
/-- Typeclass for purely inseparable field extensions: an algebraic extension `E / F` is purely
inseparable if and only if the minimal polynomial of every element of `E ∖ F` is not separable. -/
class IsPurelyInseparable : Prop where
  isIntegral' (x : E) : IsIntegral F x
  inseparable' (x : E) : (minpoly F x).Separable → x ∈ (algebraMap F E).range
```

### `minpoly` (commanddeclaration) at `Mathlib/FieldTheory/Minpoly/Basic.lean`
```lean
/-- Suppose `x : B`, where `B` is an `A`-algebra.

The minimal polynomial `minpoly A x` of `x`
is a monic polynomial with coefficients in `A` of smallest degree that has `x` as its root,
if such exists (`IsIntegral A x`) or zero otherwise.

For example, if `V` is a `𝕜`-vector space for some field `𝕜` and `f : V →ₗ[𝕜] V` then
the minimal polynomial of `f` is `minpoly 𝕜 f`.
-/
noncomputable def minpoly (x : B) : A[X] :=
  if hx : IsIntegral A x then degree_lt_wf.min _ hx else 0
```

### `Polynomial.natSepDegree` (commanddeclaration) at `Mathlib/FieldTheory/SeparableDegree.lean`
```lean
/-- The separable degree `Polynomial.natSepDegree` of a polynomial is a natural number,
defined to be the number of distinct roots of it over its splitting field.
This is similar to `Polynomial.natDegree` but not to `Polynomial.degree`, namely, the separable
degree of `0` is `0`, not negative infinity. -/
def natSepDegree : ℕ := (f.aroots f.SplittingField).toFinset.card

/-- The separable degree of a polynomial is smaller than its degree. -/
```

### `ExpChar.exists` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
theorem ExpChar.exists [Ring R] [IsDomain R] : ∃ q, ExpChar R q := by
  obtain _ | ⟨p, ⟨hp⟩, _⟩ := CharP.exists' R
  exacts [⟨1, .zero⟩, ⟨p, .prime hp⟩]
```

### `isPurelyInseparable_iff_pow_mem` (commanddeclaration) at `Mathlib/FieldTheory/PurelyInseparable.lean`
```lean
/-- A field extension `E / F` of exponential characteristic `q` is purely inseparable
if and only if for every element `x` of `E`, there exists a natural number `n` such that
`x ^ (q ^ n)` is contained in `F`. -/
theorem isPurelyInseparable_iff_pow_mem (q : ℕ) [ExpChar F q] :
    IsPurelyInseparable F E ↔ ∀ x : E, ∃ n : ℕ, x ^ q ^ n ∈ (algebraMap F E).range := by
  rw [isPurelyInseparable_iff]
  refine ⟨fun h x ↦ ?_, fun h x ↦ ?_⟩
  · obtain ⟨g, h1, n, h2⟩ := (minpoly.irreducible (h x).1).hasSeparableContraction q
    exact ⟨n, (h _).2 <| h1.of_dvd <| minpoly.dvd F _ <| by
      simpa only [expand_aeval, minpoly.aeval] using congr_arg (aeval x) h2⟩
  have hdeg := (minpoly.natSepDegree_eq_one_iff_pow_mem q).2 (h x)
  have halg : IsIntegral F x := by_contra fun h' ↦ by
    simp only [minpoly.eq_zero h', natSepDegree_zero, zero_ne_one] at hdeg
  refine ⟨halg, fun hsep ↦ ?_⟩
  rw [hsep.natSepDegree_eq_natDegree, ← adjoin.finrank halg,
    IntermediateField.finrank_eq_one_iff] at hdeg
  simpa only [hdeg] using mem_adjoin_simple_self F x
```

### `minpoly.natSepDegree_eq_one_iff_pow_mem` (commanddeclaration) at `Mathlib/FieldTheory/SeparableDegree.lean`
```lean
/-- The minimal polynomial of an element `x` of `E / F` of exponential characteristic `q` has
separable degree one if and only if `x ^ (q ^ n) ∈ F` for some `n : ℕ`. -/
theorem natSepDegree_eq_one_iff_pow_mem : (minpoly F x).natSepDegree = 1 ↔
    ∃ n : ℕ, x ^ q ^ n ∈ (algebraMap F E).range := by
  convert_to _ ↔ ∃ (n : ℕ) (y : F), Polynomial.aeval x (X ^ q ^ n - C y) = 0
  · simp_rw [RingHom.mem_range, map_sub, map_pow, aeval_C, aeval_X, sub_eq_zero, eq_comm]
  refine ⟨fun h ↦ ?_, fun ⟨n, y, h⟩ ↦ ?_⟩
  · obtain ⟨n, y, hx⟩ := (minpoly.natSepDegree_eq_one_iff_eq_X_pow_sub_C q).1 h
    exact ⟨n, y, hx ▸ aeval F x⟩
  have hnezero := X_pow_sub_C_ne_zero (expChar_pow_pos F q n) y
  refine ((natSepDegree_le_of_dvd _ _ (minpoly.dvd F x h) hnezero).trans_eq <|
    natSepDegree_X_pow_char_pow_sub_C q n y).antisymm ?_
  rw [Nat.one_le_iff_ne_zero, natSepDegree_ne_zero_iff, ← Nat.one_le_iff_ne_zero]
  exact minpoly.natDegree_pos <| IsAlgebraic.isIntegral ⟨_, hnezero, h⟩

/-- The minimal polynomial of an element `x` of `E / F` of exponential characteristic `q` has
separable degree one if and only if the minimal polynomial is of the form
`(X - x) ^ (q ^ n)` for some `n : ℕ`. -/
```

### `Subgroup.Centralizer.characteristic` (commanddeclaration) at `Mathlib/GroupTheory/Subgroup/Basic.lean`
```lean
@[to_additive]
instance Centralizer.characteristic [hH : H.Characteristic] :
    (centralizer (H : Set G)).Characteristic := by
  refine' Subgroup.characteristic_iff_comap_le.mpr fun ϕ g hg h hh => ϕ.injective _
  rw [map_mul, map_mul]
  exact hg (ϕ h) (Subgroup.characteristic_iff_le_comap.mp hH ϕ hh)
```

### `algebraMap` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- Embedding `R →+* A` given by `Algebra` structure. -/
def algebraMap (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] : R →+* A :=
  Algebra.toRingHom
```

### `Lean.Parser.Term.haveI` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Term.lean`
```lean
/-- `haveI` behaves like `have`, but inlines the value instead of producing a `let_fun` term. -/
@[builtin_term_parser] def «haveI» := leading_parser
  withPosition ("haveI " >> haveDecl) >> optSemicolon termParser
/-- `letI` behaves like `let`, but inlines the value instead of producing a `let_fun` term. -/
```

### `expChar_of_injective_algebraMap` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
/-- If the algebra map `R →+* A` is injective then `A` has the same exponential characteristic
as `R`. -/
theorem expChar_of_injective_algebraMap {R A : Type*}
    [CommSemiring R] [Semiring A] [Algebra R A] (h : Function.Injective (algebraMap R A))
    (q : ℕ) [ExpChar R q] : ExpChar A q := expChar_of_injective_ringHom h q
```

### `NoZeroSMulDivisors.algebraMap_injective` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
theorem algebraMap_injective [CommRing R] [Ring A] [Nontrivial A] [Algebra R A]
    [NoZeroSMulDivisors R A] : Function.Injective (algebraMap R A) := by
  simpa only [algebraMap_eq_smul_one'] using smul_left_injective R one_ne_zero
```

### `minpoly.natSepDegree_eq_one_iff_eq_X_pow_sub_C` (commanddeclaration) at `Mathlib/FieldTheory/SeparableDegree.lean`
```lean
/-- The minimal polynomial of an element of `E / F` of exponential characteristic `q` has
separable degree one if and only if the minimal polynomial is of the form
`X ^ (q ^ n) - C y` for some `n : ℕ` and `y : F`. -/
theorem natSepDegree_eq_one_iff_eq_X_pow_sub_C : (minpoly F x).natSepDegree = 1 ↔
    ∃ (n : ℕ) (y : F), minpoly F x = X ^ q ^ n - C y := by
  simp only [minpoly.natSepDegree_eq_one_iff_eq_expand_X_sub_C q, map_sub, expand_X, expand_C]

/-- The minimal polynomial of an element `x` of `E / F` of exponential characteristic `q` has
separable degree one if and only if `x ^ (q ^ n) ∈ F` for some `n : ℕ`. -/
```

### `congr_arg` (stdtacticaliasalias) at `.lake/packages/std/Std/Logic.lean`
```lean
alias congr_arg := congrArg
alias congr_arg₂ := congrArg₂
alias congr_fun := congrFun
alias congr_fun₂ := congrFun₂
alias congr_fun₃ := congrFun₃
```

### `Polynomial.aeval` (commanddeclaration) at `Mathlib/Data/Polynomial/AlgebraMap.lean`
```lean
/-- Given a valuation `x` of the variable in an `R`-algebra `A`, `aeval R A x` is
the unique `R`-algebra homomorphism from `R[X]` to `A` sending `X` to `x`.

This is a stronger variant of the linear map `Polynomial.leval`. -/
def aeval : R[X] →ₐ[R] A :=
  eval₂AlgHom' (Algebra.ofId _ _) x (Algebra.commutes · _)
```

### `minpoly.aeval` (commanddeclaration) at `Mathlib/FieldTheory/Minpoly/Basic.lean`
```lean
/-- An element is a root of its minimal polynomial. -/
@[simp]
theorem aeval : aeval x (minpoly A x) = 0 := by
  delta minpoly
  split_ifs with hx
  · exact (degree_lt_wf.min_mem _ hx).2
  · exact aeval_zero _
```

### `map_pow` (commanddeclaration) at `Mathlib/Algebra/Group/Hom/Defs.lean`
```lean
@[to_additive (attr := simp) (reorder := 9 10)]
theorem map_pow [Monoid G] [Monoid H] [MonoidHomClass F G H] (f : F) (a : G) :
    ∀ n : ℕ, f (a ^ n) = f a ^ n
  | 0 => by rw [pow_zero, pow_zero, map_one]
  | n + 1 => by rw [pow_succ, pow_succ, map_mul, map_pow f a n]
```

### `Int.sub_eq_zero` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem sub_eq_zero {a b : Int} : a - b = 0 ↔ a = b :=
  ⟨Int.eq_of_sub_eq_zero, Int.sub_eq_zero_of_eq⟩
```

### `eq_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem eq_comm {a b : α} : a = b ↔ b = a := Eq.comm
```

### `Polynomial.map_sub` (commanddeclaration) at `Mathlib/Data/Polynomial/Eval.lean`
```lean
@[simp]
protected theorem map_sub {S} [Ring S] (f : R →+* S) : (p - q).map f = p.map f - q.map f :=
  (mapRingHom f).map_sub p q
```

### `Polynomial.map_pow` (commanddeclaration) at `Mathlib/Data/Polynomial/Eval.lean`
```lean
@[simp]
protected theorem map_pow (n : ℕ) : (p ^ n).map f = p.map f ^ n :=
  (mapRingHom f).map_pow _ _
```

### `sub_pow_expChar_pow` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
theorem sub_pow_expChar_pow [CommRing R] {q : ℕ} [hR : ExpChar R q]
    {n : ℕ} (x y : R) : (x - y) ^ q ^ n = x ^ q ^ n - y ^ q ^ n := by
  cases' hR with _ _ hprime _
  · simp only [one_pow, pow_one]
  haveI := Fact.mk hprime; exact sub_pow_char_pow R x y
```

### `Polynomial.coeff_X_zero` (commanddeclaration) at `Mathlib/Data/Polynomial/Basic.lean`
```lean
@[simp]
theorem coeff_X_zero : coeff (X : R[X]) 0 = 0 :=
  coeff_monomial
```

### `Polynomial.coeff_C_zero` (commanddeclaration) at `Mathlib/Data/Polynomial/Basic.lean`
```lean
@[simp]
theorem coeff_C_zero : coeff (C a) 0 = a :=
  coeff_monomial
```

### `neg_pow` (commanddeclaration) at `Mathlib/Algebra/GroupPower/Ring.lean`
```lean
theorem neg_pow (a : R) (n : ℕ) : (-a) ^ n = (-1) ^ n * a ^ n :=
  neg_one_mul a ▸ (Commute.neg_one_left a).mul_pow n
```

### `ExpChar.neg_one_pow_expChar_pow` (commanddeclaration) at `Mathlib/Algebra/CharP/ExpChar.lean`
```lean
theorem ExpChar.neg_one_pow_expChar_pow [Ring R] (q n : ℕ) [hR : ExpChar R q] :
    (-1 : R) ^ q ^ n = -1 := by
  cases' hR with _ _ hprime _
  · simp only [one_pow, pow_one]
  haveI := Fact.mk hprime; exact CharP.neg_one_pow_char_pow R q n
```
