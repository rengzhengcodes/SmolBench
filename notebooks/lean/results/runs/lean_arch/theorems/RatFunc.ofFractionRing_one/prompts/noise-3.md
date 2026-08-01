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

## Filler (hint:2 → hint:3 token-match, ≈163 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur
