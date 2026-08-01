## Current goal
```
⊢ Multiset.Nodup (aroots f K) ↔ Separable f
```

## Full tactic state
```
F : Type u
inst✝² : Field F
K : Type v
inst✝¹ : Field K
inst✝ : Algebra F K
f : F[X]
hf : f ≠ 0
h : Splits (RingHom.id K) (map (algebraMap F K) f)
⊢ Multiset.Nodup (aroots f K) ↔ Separable f
```

## Proof so far (1 tactic)
```lean
rw [← (algebraMap F K).id_comp, ← splits_map_iff] at h
```

## Theorem
`Polynomial.nodup_aroots_iff_of_splits` in `Mathlib/FieldTheory/Separable.lean`

## Premises used in the next tactic
- `Polynomial.nodup_roots_iff_of_splits`
- `Polynomial.map_ne_zero`
- `Polynomial.separable_map`

## Premise signatures
### `Polynomial.nodup_roots_iff_of_splits` (commanddeclaration)
```lean
theorem nodup_roots_iff_of_splits {f : F[X]} (hf : f ≠ 0) (h : f.Splits (RingHom.id F)) :
    f.roots.Nodup ↔ f.Separable
```

### `Polynomial.map_ne_zero` (commanddeclaration)
```lean
theorem map_ne_zero [Semiring S] [Nontrivial S] {f : R →+* S} (hp : p ≠ 0) : p.map f ≠ 0
```

### `Polynomial.separable_map` (commanddeclaration)
```lean
theorem separable_map {S} [CommRing S] [Nontrivial S] (f : F →+* S) {p : F[X]} :
    (p.map f).Separable ↔ p.Separable
```

## Premise full source (with proof)
### `Polynomial.nodup_roots_iff_of_splits` (commanddeclaration) at `Mathlib/FieldTheory/Separable.lean`
```lean
/-- If a non-zero polynomial splits, then it has no repeated roots on that field
if and only if it is separable. -/
theorem nodup_roots_iff_of_splits {f : F[X]} (hf : f ≠ 0) (h : f.Splits (RingHom.id F)) :
    f.roots.Nodup ↔ f.Separable := by
  refine ⟨(fun hnsep ↦ ?_).mtr, nodup_roots⟩
  rw [Separable, ← gcd_isUnit_iff, isUnit_iff_degree_eq_zero] at hnsep
  obtain ⟨x, hx⟩ := exists_root_of_splits _
    (splits_of_splits_of_dvd _ hf h (gcd_dvd_left f _)) hnsep
  simp_rw [Multiset.nodup_iff_count_le_one, not_forall, not_le]
  exact ⟨x, ((one_lt_rootMultiplicity_iff_isRoot_gcd hf).2 hx).trans_eq f.count_roots.symm⟩

/-- If a non-zero polynomial over `F` splits in `K`, then it has no repeated roots on `K`
if and only if it is separable. -/
```

### `Polynomial.map_ne_zero` (commanddeclaration) at `Mathlib/Data/Polynomial/FieldDivision.lean`
```lean
theorem map_ne_zero [Semiring S] [Nontrivial S] {f : R →+* S} (hp : p ≠ 0) : p.map f ≠ 0 :=
  mt (map_eq_zero f).1 hp
```

### `Polynomial.separable_map` (commanddeclaration) at `Mathlib/FieldTheory/Separable.lean`
```lean
theorem separable_map {S} [CommRing S] [Nontrivial S] (f : F →+* S) {p : F[X]} :
    (p.map f).Separable ↔ p.Separable := by
  refine ⟨fun H ↦ ?_, fun H ↦ H.map⟩
  obtain ⟨m, hm⟩ := Ideal.exists_maximal S
  have := Separable.map H (f := Ideal.Quotient.mk m)
  rwa [map_map, separable_def, derivative_map, isCoprime_map] at this
```

## Transitive premise context (1-hop, 22/22 premises, ≈2293 tokens)
### `CategoryTheory.ShortComplex.RightHomologyData.IsPreservedBy.hf` (commanddeclaration) at `Mathlib/Algebra/Homology/ShortComplex/PreservesHomology.lean`
```lean
/-- When a right homology data is preserved by a functor `F`, this functor
preserves the cokernel of `S.f : S.X₁ ⟶ S.X₂`. -/
def IsPreservedBy.hf : PreservesColimit (parallelPair S.f 0) F :=
  @IsPreservedBy.f _ _ _ _ _ _ _ h F _ _

/-- When a right homology data `h` is preserved by a functor `F`, this functor
preserves the kernel of `h.g' : h.Q ⟶ S.X₃`. -/
```

### `RingHom.id` (commanddeclaration) at `Mathlib/Algebra/Ring/Hom/Defs.lean`
```lean
/-- The identity ring homomorphism from a semiring to itself. -/
def id (α : Type*) [NonAssocSemiring α] : α →+* α := by
  refine' { toFun := _root_.id.. } <;> intros <;> rfl
```

### `Polynomial.nodup_roots` (commanddeclaration) at `Mathlib/FieldTheory/Separable.lean`
```lean
theorem nodup_roots {p : R[X]} (hsep : Separable p) : p.roots.Nodup :=
  Multiset.nodup_iff_count_le_one.mpr (count_roots_le_one hsep)
```

### `Polynomial.Separable` (commanddeclaration) at `Mathlib/FieldTheory/Separable.lean`
```lean
/-- A polynomial is separable iff it is coprime with its derivative. -/
def Separable (f : R[X]) : Prop :=
  IsCoprime f (derivative f)
```

### `gcd_isUnit_iff` (commanddeclaration) at `Mathlib/RingTheory/PrincipalIdealDomain.lean`
```lean
theorem gcd_isUnit_iff (x y : R) : IsUnit (gcd x y) ↔ IsCoprime x y := by
  rw [IsCoprime, ← Ideal.mem_span_pair, ← span_gcd, ← span_singleton_eq_top, eq_top_iff_one]
```

### `Polynomial.isUnit_iff_degree_eq_zero` (commanddeclaration) at `Mathlib/Data/Polynomial/FieldDivision.lean`
```lean
theorem isUnit_iff_degree_eq_zero : IsUnit p ↔ degree p = 0 :=
  ⟨degree_eq_zero_of_isUnit, fun h =>
    have : degree p ≤ 0 := by simp [*, le_refl]
    have hc : coeff p 0 ≠ 0 := fun hc => by
      rw [eq_C_of_degree_le_zero this, hc] at h; simp only [map_zero] at h; contradiction
    isUnit_iff_dvd_one.2
      ⟨C (coeff p 0)⁻¹, by
        conv in p => rw [eq_C_of_degree_le_zero this]
        rw [← C_mul, _root_.mul_inv_cancel hc, C_1]⟩⟩
```

### `Polynomial.exists_root_of_splits` (commanddeclaration) at `Mathlib/Data/Polynomial/Splits.lean`
```lean
theorem exists_root_of_splits {f : K[X]} (hs : Splits i f) (hf0 : degree f ≠ 0) :
    ∃ x, eval₂ i x f = 0 :=
  exists_root_of_splits' i hs ((f.degree_map i).symm ▸ hf0)
```

### `Polynomial.splits_of_splits_of_dvd` (commanddeclaration) at `Mathlib/Data/Polynomial/Splits.lean`
```lean
theorem splits_of_splits_of_dvd {f g : K[X]} (hf0 : f ≠ 0) (hf : Splits i f) (hgf : g ∣ f) :
    Splits i g := by
  obtain ⟨f, rfl⟩ := hgf
  exact (splits_of_splits_mul i hf0 hf).1
```

### `Multiset.nodup_iff_count_le_one` (commanddeclaration) at `Mathlib/Data/Multiset/Nodup.lean`
```lean
theorem nodup_iff_count_le_one [DecidableEq α] {s : Multiset α} : Nodup s ↔ ∀ a, count a s ≤ 1 :=
  Quot.induction_on s fun _l => by
    simp only [quot_mk_to_coe'', coe_nodup, mem_coe, coe_count]
    exact List.nodup_iff_count_le_one
```

### `not_le` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
@[simp]
theorem not_le {a b : α} : ¬a ≤ b ↔ b < a :=
  (lt_iff_not_ge _ _).symm
```

### `Polynomial.one_lt_rootMultiplicity_iff_isRoot_gcd` (commanddeclaration) at `Mathlib/Data/Polynomial/FieldDivision.lean`
```lean
theorem one_lt_rootMultiplicity_iff_isRoot_gcd
    [GCDMonoid R[X]] {p : R[X]} {t : R} (h : p ≠ 0) :
    1 < p.rootMultiplicity t ↔ (gcd p (derivative p)).IsRoot t := by
  simp_rw [one_lt_rootMultiplicity_iff_isRoot h, ← dvd_iff_isRoot, dvd_gcd_iff]
```

### `map_ne_zero` (commanddeclaration) at `Mathlib/Algebra/GroupWithZero/Units/Lemmas.lean`
```lean
theorem map_ne_zero : f a ≠ 0 ↔ a ≠ 0 :=
  ⟨fun hfa ha => hfa <| ha.symm ▸ map_zero f, fun ha => ((IsUnit.mk0 a ha).map f).ne_zero⟩
```

### `Semiring` (commanddeclaration) at `Mathlib/Algebra/Ring/Defs.lean`
```lean
/-- A `Semiring` is a type with addition, multiplication, a `0` and a `1` where addition is
commutative and associative, multiplication is associative and left and right distributive over
addition, and `0` and `1` are additive and multiplicative identities. -/
class Semiring (α : Type u) extends NonUnitalSemiring α, NonAssocSemiring α, MonoidWithZero α
```

### `Nontrivial` (commanddeclaration) at `Mathlib/Logic/Nontrivial/Defs.lean`
```lean
/-- Predicate typeclass for expressing that a type is not reduced to a single element. In rings,
this is equivalent to `0 ≠ 1`. In vector spaces, this is equivalent to positive dimension. -/
class Nontrivial (α : Type*) : Prop where
  /-- In a nontrivial type, there exists a pair of distinct terms. -/
  exists_pair_ne : ∃ x y : α, x ≠ y
```

### `mt` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem mt {a b : Prop} (h₁ : a → b) (h₂ : ¬b) : ¬a :=
  fun ha => h₂ (h₁ ha)
```

### `map_eq_zero` (commanddeclaration) at `Mathlib/Algebra/GroupWithZero/Units/Lemmas.lean`
```lean
@[simp]
theorem map_eq_zero : f a = 0 ↔ a = 0 :=
  not_iff_not.1 (map_ne_zero f)
```

### `CommRing` (commanddeclaration) at `Mathlib/Algebra/Ring/Defs.lean`
```lean
class CommRing (α : Type u) extends Ring α, CommMonoid α
```

### `Ideal.exists_maximal` (commanddeclaration) at `Mathlib/RingTheory/Ideal/Basic.lean`
```lean
/-- Krull's theorem: a nontrivial ring has a maximal ideal. -/
theorem exists_maximal [Nontrivial α] : ∃ M : Ideal α, M.IsMaximal :=
  let ⟨I, ⟨hI, _⟩⟩ := exists_le_maximal (⊥ : Ideal α) bot_ne_top
  ⟨I, hI⟩
```

### `Ideal.Quotient.mk` (commanddeclaration) at `Mathlib/RingTheory/Ideal/Quotient.lean`
```lean
/-- The ring homomorphism from a ring `R` to a quotient ring `R/I`. -/
def mk (I : Ideal R) : R →+* R ⧸ I where
  toFun a := Submodule.Quotient.mk a
  map_zero' := rfl
  map_one' := rfl
  map_mul' _ _ := rfl
  map_add' _ _ := rfl
```

### `Polynomial.separable_def` (commanddeclaration) at `Mathlib/FieldTheory/Separable.lean`
```lean
theorem separable_def (f : R[X]) : f.Separable ↔ IsCoprime f (derivative f) :=
  Iff.rfl
```

### `Polynomial.derivative_map` (commanddeclaration) at `Mathlib/Data/Polynomial/Derivative.lean`
```lean
@[simp]
theorem derivative_map [Semiring S] (p : R[X]) (f : R →+* S) :
    derivative (p.map f) = p.derivative.map f := by
  let n := max p.natDegree (map f p).natDegree
  rw [derivative_apply, derivative_apply]
  rw [sum_over_range' _ _ (n + 1) ((le_max_left _ _).trans_lt (lt_add_one _))]
  rw [sum_over_range' _ _ (n + 1) ((le_max_right _ _).trans_lt (lt_add_one _))]
  simp only [Polynomial.map_sum, Polynomial.map_mul, Polynomial.map_C, map_mul, coeff_map,
    map_natCast, Polynomial.map_nat_cast, Polynomial.map_pow, map_X]
  all_goals intro n; rw [zero_mul, C_0, zero_mul]
```

### `Polynomial.isCoprime_map` (commanddeclaration) at `Mathlib/Data/Polynomial/FieldDivision.lean`
```lean
theorem isCoprime_map [Field k] (f : R →+* k) : IsCoprime (p.map f) (q.map f) ↔ IsCoprime p q := by
  classical
  rw [← EuclideanDomain.gcd_isUnit_iff, ← EuclideanDomain.gcd_isUnit_iff, gcd_map, isUnit_map]
```
