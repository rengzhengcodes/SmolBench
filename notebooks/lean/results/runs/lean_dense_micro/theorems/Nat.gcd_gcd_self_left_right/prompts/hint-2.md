## Current goal
```
⊢ gcd (gcd n m) m = gcd n m
```

## Full tactic state
```
m n : Nat
⊢ gcd (gcd n m) m = gcd n m
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Nat.gcd_gcd_self_left_right` in `.lake/packages/std/Std/Data/Nat/Gcd.lean`

## Premises used in the next tactic
- `Nat.gcd_comm`
- `Nat.gcd_gcd_self_right_right`

## Premise signatures
### `Nat.gcd_comm` (commanddeclaration)
```lean
theorem gcd_comm (m n : Nat) : gcd m n = gcd n m
```

### `Nat.gcd_gcd_self_right_right` (commanddeclaration)
```lean
@[simp] theorem gcd_gcd_self_right_right (m n : Nat) : gcd m (gcd n m) = gcd n m
```

## Premise full source (with proof)
### `Nat.gcd_comm` (commanddeclaration) at `.lake/packages/std/Std/Data/Nat/Gcd.lean`
```lean
theorem gcd_comm (m n : Nat) : gcd m n = gcd n m :=
  Nat.dvd_antisymm
    (dvd_gcd (gcd_dvd_right m n) (gcd_dvd_left m n))
    (dvd_gcd (gcd_dvd_right n m) (gcd_dvd_left n m))
```

### `Nat.gcd_gcd_self_right_right` (commanddeclaration) at `.lake/packages/std/Std/Data/Nat/Gcd.lean`
```lean
@[simp] theorem gcd_gcd_self_right_right (m n : Nat) : gcd m (gcd n m) = gcd n m := by
  rw [gcd_comm n m, gcd_gcd_self_right_left]
```
