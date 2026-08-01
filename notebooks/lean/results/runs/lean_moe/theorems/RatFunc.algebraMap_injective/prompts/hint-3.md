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

## Transitive premise context (1-hop, 4/4 premises, ≈338 tokens)
### `Function.Injective` (commanddeclaration) at `Mathlib/Init/Function.lean`
```lean
/-- A function `f : α → β` is called injective if `f x = f y` implies `x = y`. -/
def Injective (f : α → β) : Prop :=
  ∀ ⦃a₁ a₂⦄, f a₁ = f a₂ → a₁ = a₂
```

### `algebraMap` (commanddeclaration) at `Mathlib/Algebra/Algebra/Basic.lean`
```lean
/-- Embedding `R →+* A` given by `Algebra` structure. -/
def algebraMap (R : Type u) (A : Type v) [CommSemiring R] [Semiring A] [Algebra R A] : R →+* A :=
  Algebra.toRingHom
```

### `IsLocalization.injective` (commanddeclaration) at `Mathlib/RingTheory/Localization/Basic.lean`
```lean
protected theorem injective (hM : M ≤ nonZeroDivisors R) : Injective (algebraMap R S) := by
  rw [injective_iff_map_eq_zero (algebraMap R S)]
  intro a ha
  rwa [to_map_eq_zero_iff S hM] at ha
```

### `le_of_eq` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
theorem le_of_eq {a b : α} : a = b → a ≤ b := fun h => h ▸ le_refl a
```
