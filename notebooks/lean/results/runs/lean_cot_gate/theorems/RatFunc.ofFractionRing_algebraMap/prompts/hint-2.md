## Current goal
```
⊢ { toFractionRing := (algebraMap K[X] (FractionRing K[X])) x } = (algebraMap K[X] (RatFunc K)) x
```

## Full tactic state
```
K : Type u
inst✝¹ : CommRing K
inst✝ : IsDomain K
x : K[X]
⊢ { toFractionRing := (algebraMap K[X] (FractionRing K[X])) x } = (algebraMap K[X] (RatFunc K)) x
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`RatFunc.ofFractionRing_algebraMap` in `Mathlib/FieldTheory/RatFunc.lean`

## Premises used in the next tactic
- `RatFunc.mk_one`
- `RatFunc.mk_one'`

## Premise signatures
### `RatFunc.mk_one` (commanddeclaration)
```lean
theorem mk_one (x : K[X]) : RatFunc.mk x 1 = algebraMap _ _ x
```

### `RatFunc.mk_one'` (commanddeclaration)
```lean
theorem mk_one' (p : K[X]) :
    RatFunc.mk p 1 = ofFractionRing (algebraMap K[X] (FractionRing K[X]) p)
```

## Premise full source (with proof)
### `RatFunc.mk_one` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_one (x : K[X]) : RatFunc.mk x 1 = algebraMap _ _ x :=
  rfl
```

### `RatFunc.mk_one'` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
theorem mk_one' (p : K[X]) :
    RatFunc.mk p 1 = ofFractionRing (algebraMap K[X] (FractionRing K[X]) p) := by
  -- Porting note: had to hint `M := K[X]⁰` below
  rw [← IsLocalization.mk'_one (M := K[X]⁰) (FractionRing K[X]) p, ← mk_coe_def, Submonoid.coe_one]
```
