## Current goal
```
⊢ { toFractionRing := 0 } = 0
```

## Full tactic state
```
K : Type u
inst✝ : CommRing K
⊢ { toFractionRing := 0 } = 0
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`RatFunc.ofFractionRing_zero` in `Mathlib/FieldTheory/RatFunc.lean`

## Premises used in the next tactic
- `Zero.zero`
- `OfNat.ofNat`
- `RatFunc.zero`

## Premise signatures
### `Zero.zero`
_(not found in premise corpus)_

### `OfNat.ofNat`
_(not found in premise corpus)_

### `RatFunc.zero` (leanelabcommandcommandirreducibledef)
```lean
protected irreducible_def zero : RatFunc K
```

## Premise full source (with proof)
### `Zero.zero`
_(not found in premise corpus)_

### `OfNat.ofNat`
_(not found in premise corpus)_

### `RatFunc.zero` (leanelabcommandcommandirreducibledef) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
/-- The zero rational function. -/
protected irreducible_def zero : RatFunc K :=
  ⟨0⟩
```

## Transitive premise context (1-hop, 1/1 premises, ≈142 tokens)
### `RatFunc` (commanddeclaration) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
/-- `RatFunc K` is `K(X)`, the field of rational functions over `K`.

The inclusion of polynomials into `RatFunc` is `algebraMap K[X] (RatFunc K)`,
the maps between `RatFunc K` and another field of fractions of `K[X]`,
especially `FractionRing K[X]`, are given by `IsLocalization.algEquiv`.
-/
structure RatFunc [CommRing K] : Type u where ofFractionRing ::
  toFractionRing : FractionRing K[X]
```
