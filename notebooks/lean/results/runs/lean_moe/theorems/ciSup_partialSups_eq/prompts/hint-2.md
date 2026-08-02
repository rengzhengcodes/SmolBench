## Current goal
```
⊢ BddAbove (Set.range fun n => (partialSups f) n)
```

## Full tactic state
```
case refine'_2
α : Type u_1
inst✝ : ConditionallyCompleteLattice α
f : ℕ → α
h : BddAbove (Set.range f)
⊢ BddAbove (Set.range fun n => (partialSups f) n)
```

## Proof so far (3 tactics)
```lean
refine' (ciSup_le fun n => _).antisymm (ciSup_mono _ <| le_partialSups f)
rw [partialSups_eq_ciSup_Iic]
exact ciSup_le fun i => le_ciSup h _
```

## Theorem
`ciSup_partialSups_eq` in `Mathlib/Order/PartialSups.lean`

## Premises used in the next tactic
- `bddAbove_range_partialSups`

## Premise signatures
### `bddAbove_range_partialSups` (commanddeclaration)
```lean
@[simp]
theorem bddAbove_range_partialSups {f : ℕ → α} :
    BddAbove (Set.range (partialSups f)) ↔ BddAbove (Set.range f)
```

## Premise full source (with proof)
### `bddAbove_range_partialSups` (commanddeclaration) at `Mathlib/Order/PartialSups.lean`
```lean
@[simp]
theorem bddAbove_range_partialSups {f : ℕ → α} :
    BddAbove (Set.range (partialSups f)) ↔ BddAbove (Set.range f) :=
  .of_eq <| congr_arg Set.Nonempty <| upperBounds_range_partialSups f
```
