## Current goal
```
⊢ { toFractionRing := 1 } = 1
```

## Full tactic state
```
K : Type u
inst✝ : CommRing K
⊢ { toFractionRing := 1 } = 1
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`RatFunc.ofFractionRing_one` in `Mathlib/FieldTheory/RatFunc.lean`

## Premises used in the next tactic
- `One.one`
- `OfNat.ofNat`
- `RatFunc.one`

## Premise signatures
### `One.one`
_(not found in premise corpus)_

### `OfNat.ofNat`
_(not found in premise corpus)_

### `RatFunc.one` (leanelabcommandcommandirreducibledef)
```lean
protected irreducible_def one : RatFunc K
```

## Premise full source (with proof)
### `One.one`
_(not found in premise corpus)_

### `OfNat.ofNat`
_(not found in premise corpus)_

### `RatFunc.one` (leanelabcommandcommandirreducibledef) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
/-- The multiplicative unit of rational functions. -/
protected irreducible_def one : RatFunc K :=
  ⟨1⟩
```
