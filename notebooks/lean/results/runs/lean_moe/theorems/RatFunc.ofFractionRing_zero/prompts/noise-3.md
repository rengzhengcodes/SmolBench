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

## Filler (hint:2 → hint:3 token-match, ≈163 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur
