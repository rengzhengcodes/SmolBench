## Current goal
```
⊢ succ a = succ b ↔ a = b
```

## Full tactic state
```
α : Type u_1
β : Type u_2
inst✝¹ : PartialOrder α
inst✝ : SuccOrder α
a b : α
ha : ¬IsMax a
hb : ¬IsMax b
⊢ succ a = succ b ↔ a = b
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Order.succ_eq_succ_iff_of_not_isMax` in `Mathlib/Order/SuccPred/Basic.lean`

## Premises used in the next tactic
- `eq_iff_le_not_lt`
- `eq_iff_le_not_lt`
- `Order.succ_le_succ_iff_of_not_isMax`
- `Order.succ_lt_succ_iff_of_not_isMax`

## Premise signatures
### `eq_iff_le_not_lt` (commanddeclaration)
```lean
theorem eq_iff_le_not_lt [PartialOrder α] {a b : α} : a = b ↔ a ≤ b ∧ ¬a < b
```

### `eq_iff_le_not_lt` (commanddeclaration)
```lean
theorem eq_iff_le_not_lt [PartialOrder α] {a b : α} : a = b ↔ a ≤ b ∧ ¬a < b
```

### `Order.succ_le_succ_iff_of_not_isMax` (commanddeclaration)
```lean
theorem succ_le_succ_iff_of_not_isMax (ha : ¬IsMax a) (hb : ¬IsMax b) :
    succ a ≤ succ b ↔ a ≤ b
```

### `Order.succ_lt_succ_iff_of_not_isMax` (commanddeclaration)
```lean
theorem succ_lt_succ_iff_of_not_isMax (ha : ¬IsMax a) (hb : ¬IsMax b) :
    succ a < succ b ↔ a < b
```

## Premise full source (with proof)
### `eq_iff_le_not_lt` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
theorem eq_iff_le_not_lt [PartialOrder α] {a b : α} : a = b ↔ a ≤ b ∧ ¬a < b :=
  haveI := Classical.dec
  Decidable.eq_iff_le_not_lt
```

### `eq_iff_le_not_lt` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
theorem eq_iff_le_not_lt [PartialOrder α] {a b : α} : a = b ↔ a ≤ b ∧ ¬a < b :=
  haveI := Classical.dec
  Decidable.eq_iff_le_not_lt
```

### `Order.succ_le_succ_iff_of_not_isMax` (commanddeclaration) at `Mathlib/Order/SuccPred/Basic.lean`
```lean
theorem succ_le_succ_iff_of_not_isMax (ha : ¬IsMax a) (hb : ¬IsMax b) :
    succ a ≤ succ b ↔ a ≤ b := by
  rw [succ_le_iff_of_not_isMax ha, lt_succ_iff_of_not_isMax hb]
```

### `Order.succ_lt_succ_iff_of_not_isMax` (commanddeclaration) at `Mathlib/Order/SuccPred/Basic.lean`
```lean
theorem succ_lt_succ_iff_of_not_isMax (ha : ¬IsMax a) (hb : ¬IsMax b) :
    succ a < succ b ↔ a < b := by
  rw [lt_succ_iff_of_not_isMax hb, succ_le_iff_of_not_isMax ha]
```

## Filler (hint:2 → hint:3 token-match, ≈712 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip
