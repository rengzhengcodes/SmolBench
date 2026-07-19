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

## Transitive premise context (1-hop, 4/4 premises, ≈367 tokens)
### `prodXSubSMul` (commanddeclaration) at `Mathlib/Algebra/Polynomial/GroupRingAction.lean`
```lean
/-- the product of `(X - g • x)` over distinct `g • x`. -/
noncomputable def prodXSubSMul (x : R) : R[X] :=
  letI := Classical.decEq R
  (Finset.univ : Finset (G ⧸ MulAction.stabilizer G x)).prod fun g ↦
    Polynomial.X - Polynomial.C (ofQuotientStabilizer G x g)
```

### `Polynomial.Monic` (commanddeclaration) at `Mathlib/Data/Polynomial/Degree/Definitions.lean`
```lean
/-- a polynomial is `Monic` if its leading coefficient is 1 -/
def Monic (p : R[X]) :=
  leadingCoeff p = (1 : R)
```

### `Polynomial.monic_prod_of_monic` (commanddeclaration) at `Mathlib/Data/Polynomial/Monic.lean`
```lean
theorem monic_prod_of_monic (s : Finset ι) (f : ι → R[X]) (hs : ∀ i ∈ s, Monic (f i)) :
    Monic (∏ i in s, f i) :=
  monic_multiset_prod_of_monic s.1 f hs
```

### `Polynomial.monic_X_sub_C` (commanddeclaration) at `Mathlib/Data/Polynomial/Monic.lean`
```lean
theorem monic_X_sub_C (x : R) : Monic (X - C x) := by
  simpa only [sub_eq_add_neg, C_neg] using monic_X_add_C (-x)
```
