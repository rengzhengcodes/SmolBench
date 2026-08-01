## Current goal
```
⊢ Function.Injective (ofFractionRing ∘ ⇑(algebraMap K[X] (FractionRing K[X])))
```

## Full tactic state
```
K : Type u
inst✝¹ : CommRing K
inst✝ : IsDomain K
⊢ Function.Injective (ofFractionRing ∘ ⇑(algebraMap K[X] (FractionRing K[X])))
```

## Proof so far (1 tactic)
```lean
rw [← ofFractionRing_comp_algebraMap]
```

## Theorem
`RatFunc.algebraMap_injective` in `Mathlib/FieldTheory/RatFunc.lean`

## Premises used in the next tactic
- `IsFractionRing.injective`

## Premise signatures
### `IsFractionRing.injective` (commanddeclaration)
```lean
protected theorem injective : Function.Injective (algebraMap R K)
```

## Premise full source (with proof)
### `IsFractionRing.injective` (commanddeclaration) at `Mathlib/RingTheory/Localization/FractionRing.lean`
```lean
protected theorem injective : Function.Injective (algebraMap R K) :=
  IsLocalization.injective _ (le_of_eq rfl)
```
