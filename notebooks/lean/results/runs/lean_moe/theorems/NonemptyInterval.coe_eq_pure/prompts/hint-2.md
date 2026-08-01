## Current goal
```
⊢ ↑s = Interval.pure a ↔ s = pure a
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
δ : Type u_4
ι : Sort u_5
κ : ι → Sort u_6
inst✝ : Preorder α
s : NonemptyInterval α
a : α
⊢ ↑s = Interval.pure a ↔ s = pure a
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`NonemptyInterval.coe_eq_pure` in `Mathlib/Order/Interval.lean`

## Premises used in the next tactic
- `Interval.coe_inj`
- `NonemptyInterval.coe_pure_interval`

## Premise signatures
### `Interval.coe_inj` (commanddeclaration)
```lean
@[norm_cast] theorem coe_inj {s t : NonemptyInterval α} : (s : Interval α) = t ↔ s = t
```

### `NonemptyInterval.coe_pure_interval` (commanddeclaration)
```lean
@[simp, norm_cast]
theorem coe_pure_interval (a : α) : (pure a : Interval α) = Interval.pure a
```

## Premise full source (with proof)
### `Interval.coe_inj` (commanddeclaration) at `Mathlib/Order/Interval.lean`
```lean
@[norm_cast] -- @[simp, norm_cast] -- Porting note: not in simpNF
theorem coe_inj {s t : NonemptyInterval α} : (s : Interval α) = t ↔ s = t :=
  WithBot.coe_inj
```

### `NonemptyInterval.coe_pure_interval` (commanddeclaration) at `Mathlib/Order/Interval.lean`
```lean
@[simp, norm_cast]
theorem coe_pure_interval (a : α) : (pure a : Interval α) = Interval.pure a :=
  rfl
```
