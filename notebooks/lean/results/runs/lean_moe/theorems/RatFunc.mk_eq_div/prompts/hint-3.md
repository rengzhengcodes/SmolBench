## Current goal
```
⊢ RatFunc.mk p q = (algebraMap K[X] (RatFunc K)) p / (algebraMap K[X] (RatFunc K)) q
```

## Full tactic state
```
K : Type u
inst✝¹ : CommRing K
inst✝ : IsDomain K
p q : K[X]
⊢ RatFunc.mk p q = (algebraMap K[X] (RatFunc K)) p / (algebraMap K[X] (RatFunc K)) q
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`RatFunc.mk_eq_div` in `Mathlib/FieldTheory/RatFunc.lean`

## Premises used in the next tactic
- `RatFunc.mk_eq_div'`
- `RatFunc.ofFractionRing_div`
- `RatFunc.ofFractionRing_algebraMap`

## Premise signatures
### `RatFunc.mk_eq_div'` (commanddeclaration)
```lean
theorem mk_eq_div' (p q : K[X]) :
    RatFunc.mk p q = ofFractionRing (algebraMap _ _ p / algebraMap _ _ q)
```

### `RatFunc.ofFractionRing_div` (commanddeclaration)
```lean
theorem ofFractionRing_div (p q : FractionRing K[X]) :
    ofFractionRing (p / q) = ofFractionRing p / ofFractionRing q
```

### `RatFunc.ofFractionRing_algebraMap` (commanddeclaration)
```lean
theorem ofFractionRing_algebraMap (x : K[X]) :
    ofFractionRing (algebraMap _ (FractionRing K[X]) x) = algebraMap _ _ x
```

## Premise full source (with proof)
### `RatFunc.mk_eq_div'` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_eq_div' (p q : K[X]) :
    RatFunc.mk p q = ofFractionRing (algebraMap _ _ p / algebraMap _ _ q) := by rw [RatFunc.mk]
```

### `RatFunc.ofFractionRing_div` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem ofFractionRing_div (p q : FractionRing K[X]) :
    ofFractionRing (p / q) = ofFractionRing p / ofFractionRing q := by
  simp only [Div.div, HDiv.hDiv, RatFunc.div]
```

### `RatFunc.ofFractionRing_algebraMap` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem ofFractionRing_algebraMap (x : K[X]) :
    ofFractionRing (algebraMap _ (FractionRing K[X]) x) = algebraMap _ _ x := by
  rw [← mk_one, mk_one']
```

## Transitive premise context (1-hop, 5/5 premises, ≈576 tokens)
### `RatFunc.mk` (leanelabcommandcommandirreducibledef) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
/-- `RatFunc.mk (p q : K[X])` is `p / q` as a rational function.

If `q = 0`, then `mk` returns 0.

This is an auxiliary definition used to define an `Algebra` structure on `RatFunc`;
the `simp` normal form of `mk p q` is `algebraMap _ _ p / algebraMap _ _ q`.
-/
protected irreducible_def mk (p q : K[X]) : RatFunc K :=
  ofFractionRing (algebraMap _ _ p / algebraMap _ _ q)
```

### `algebraMap` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- Embedding `R →+* A` given by `Algebra` structure. -/
def algebraMap (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] : R →+* A :=
  Algebra.toRingHom
```

### `FractionRing` (commanddeclaration) at `Mathlib/RingTheory/Localization/FractionRing.lean`
```lean
/-- The fraction ring of a commutative ring `R` as a quotient type.

We instantiate this definition as generally as possible, and assume that the
commutative ring `R` is an integral domain only when this is needed for proving.

In this generality, this construction is also known as the *total fraction ring* of `R`.
-/
@[reducible]
def FractionRing :=
  Localization (nonZeroDivisors R)
```

### `RatFunc.div` (leanelabcommandcommandirreducibledef) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
/-- Division of rational functions. -/
protected irreducible_def div : RatFunc K → RatFunc K → RatFunc K
  | ⟨p⟩, ⟨q⟩ => ⟨p / q⟩
```

### `RatFunc.mk_one'` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_one' (p : K[X]) :
    RatFunc.mk p 1 = ofFractionRing (algebraMap K[X] (FractionRing K[X]) p) := by
  -- Porting note: had to hint `M := K[X]⁰` below
  rw [← IsLocalization.mk'_one (M := K[X]⁰) (FractionRing K[X]) p, ← mk_coe_def, Submonoid.coe_one]
```
