## Current goal
```
⊢ Monic (annIdealGenerator 𝕜 a)
```

## Full tactic state
```
𝕜 : Type u_1
A : Type u_2
inst✝² : Field 𝕜
inst✝¹ : Ring A
inst✝ : Algebra 𝕜 A
a : A
p : 𝕜[X]
p_monic : Monic p
p_gen : Associated p (annIdealGenerator 𝕜 a)
h : ¬p = 0
⊢ Monic (annIdealGenerator 𝕜 a)
```

## Proof so far (5 tactics)
```lean
by_cases h : p = 0
rwa [h, annIdealGenerator_eq_zero_iff, ← p_gen, Ideal.span_singleton_eq_bot.mpr]
rw [← span_singleton_annIdealGenerator, Ideal.span_singleton_eq_span_singleton] at p_gen
rw [eq_comm]
apply eq_of_monic_of_associated p_monic _ p_gen
```

## Theorem
`Polynomial.monic_generator_eq_minpoly` in `Mathlib/LinearAlgebra/AnnihilatingPolynomial.lean`

## Premises used in the next tactic
- `Polynomial.monic_annIdealGenerator`
- `Associated.ne_zero_iff`
- `Iff.mp`

## Premise signatures
### `Polynomial.monic_annIdealGenerator` (commanddeclaration)
```lean
theorem monic_annIdealGenerator (a : A) (hg : annIdealGenerator 𝕜 a ≠ 0) :
    Monic (annIdealGenerator 𝕜 a)
```

### `Associated.ne_zero_iff` (commanddeclaration)
```lean
theorem Associated.ne_zero_iff [MonoidWithZero α] {a b : α} (h : a ~ᵤ b) : a ≠ 0 ↔ b ≠ 0
```

### `Iff.mp`
_(not found in premise corpus)_

## Premise full source (with proof)
### `Polynomial.monic_annIdealGenerator` (commanddeclaration) at `Mathlib/LinearAlgebra/AnnihilatingPolynomial.lean`
```lean
/-- The generator we chose for the annihilating ideal is monic when the ideal is non-zero. -/
theorem monic_annIdealGenerator (a : A) (hg : annIdealGenerator 𝕜 a ≠ 0) :
    Monic (annIdealGenerator 𝕜 a) :=
  monic_mul_leadingCoeff_inv (mul_ne_zero_iff.mp hg).1
```

### `Associated.ne_zero_iff` (commanddeclaration) at `Mathlib/Algebra/Associated.lean`
```lean
theorem Associated.ne_zero_iff [MonoidWithZero α] {a b : α} (h : a ~ᵤ b) : a ≠ 0 ↔ b ≠ 0 :=
  not_congr h.eq_zero_iff
```

### `Iff.mp`
_(not found in premise corpus)_

## Transitive premise context (1-hop, 8/8 premises, ≈826 tokens)
### `Submodule.IsPrincipal.generator` (commanddeclaration) at `Mathlib/RingTheory/PrincipalIdealDomain.lean`
```lean
/-- `generator I`, if `I` is a principal submodule, is an `x ∈ M` such that `span R {x} = I` -/
noncomputable def generator (S : Submodule R M) [S.IsPrincipal] : M :=
  Classical.choose (principal S)
```

### `when` (commanddeclaration) at `Mathlib/Init/Control/Combinators.lean`
```lean
def when {m : Type → Type} [Monad m] (c : Prop) [Decidable c] (t : m Unit) : m Unit :=
  ite c t (pure ())
```

### `CategoryTheory.ShortComplex.LeftHomologyData.IsPreservedBy.hg` (commanddeclaration) at `Mathlib/Algebra/Homology/ShortComplex/PreservesHomology.lean`
```lean
/-- When a left homology data is preserved by a functor `F`, this functor
preserves the kernel of `S.g : S.X₂ ⟶ S.X₃`. -/
def IsPreservedBy.hg : PreservesLimit (parallelPair S.g 0) F :=
  @IsPreservedBy.g _ _ _ _ _ _ _ h F _ _

/-- When a left homology data `h` is preserved by a functor `F`, this functor
preserves the cokernel of `h.f' : S.X₁ ⟶ h.K`. -/
```

### `Polynomial.annIdealGenerator` (commanddeclaration) at `Mathlib/LinearAlgebra/AnnihilatingPolynomial.lean`
```lean
/-- `annIdealGenerator 𝕜 a` is the monic generator of `annIdeal 𝕜 a`
if one exists, otherwise `0`.

Since `𝕜[X]` is a principal ideal domain there is a polynomial `g` such that
 `span 𝕜 {g} = annIdeal a`. This picks some generator.
 We prefer the monic generator of the ideal. -/
noncomputable def annIdealGenerator (a : A) : 𝕜[X] :=
  let g := IsPrincipal.generator <| annIdeal 𝕜 a
  g * C g.leadingCoeff⁻¹
```

### `Polynomial.Monic` (commanddeclaration) at `Mathlib/Data/Polynomial/Degree/Definitions.lean`
```lean
/-- a polynomial is `Monic` if its leading coefficient is 1 -/
def Monic (p : R[X]) :=
  leadingCoeff p = (1 : R)
```

### `Polynomial.monic_mul_leadingCoeff_inv` (commanddeclaration) at `Mathlib/Data/Polynomial/Degree/Lemmas.lean`
```lean
theorem monic_mul_leadingCoeff_inv {p : K[X]} (h : p ≠ 0) : Monic (p * C (leadingCoeff p)⁻¹) := by
  rw [Monic, leadingCoeff_mul, leadingCoeff_C,
    mul_inv_cancel (show leadingCoeff p ≠ 0 from mt leadingCoeff_eq_zero.1 h)]
```

### `MonoidWithZero` (commanddeclaration) at `Mathlib/Algebra/GroupWithZero/Defs.lean`
```lean
/-- A type `M₀` is a “monoid with zero” if it is a monoid with zero element, and `0` is left
and right absorbing. -/
class MonoidWithZero (M₀ : Type u) extends Monoid M₀, MulZeroOneClass M₀, SemigroupWithZero M₀
```

### `not_congr` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem not_congr (h : a ↔ b) : ¬a ↔ ¬b := ⟨mt h.2, mt h.1⟩
```
