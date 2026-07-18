## Current goal
```
⊢ { toFractionRing := p - q } = { toFractionRing := p } - { toFractionRing := q }
```

## Full tactic state
```
K : Type u
inst✝ : CommRing K
p q : FractionRing K[X]
⊢ { toFractionRing := p - q } = { toFractionRing := p } - { toFractionRing := q }
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`RatFunc.ofFractionRing_sub` in `Mathlib/FieldTheory/RatFunc.lean`

## Premises used in the next tactic
- `Sub.sub`
- `HSub.hSub`
- `RatFunc.sub`

## Premise signatures
### `Sub.sub`
_(not found in premise corpus)_

### `HSub.hSub`
_(not found in premise corpus)_

### `RatFunc.sub` (leanelabcommandcommandirreducibledef)
```lean
protected irreducible_def sub : RatFunc K → RatFunc K → RatFunc K
  | ⟨p⟩, ⟨q⟩ => ⟨p - q⟩
```

## Premise full source (with proof)
### `Sub.sub`
_(not found in premise corpus)_

### `HSub.hSub`
_(not found in premise corpus)_

### `RatFunc.sub` (leanelabcommandcommandirreducibledef) at `Mathlib/FieldTheory/RatFunc.lean`
```lean
/-- Subtraction of rational functions. -/
protected irreducible_def sub : RatFunc K → RatFunc K → RatFunc K
  | ⟨p⟩, ⟨q⟩ => ⟨p - q⟩
```
