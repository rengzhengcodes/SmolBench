## Current goal
```
⊢ n * a /. (d * a) = n /. d
```

## Full tactic state
```
n d a : Int
a0 : a ≠ 0
⊢ n * a /. (d * a) = n /. d
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Rat.divInt_mul_right` in `.lake/packages/std/Std/Data/Rat/Lemmas.lean`

## Premises used in the next tactic
- `Rat.divInt_mul_left`
- `Int.mul_comm`

## Premise signatures
### `Rat.divInt_mul_left` (commanddeclaration)
```lean
theorem divInt_mul_left {a : Int} (a0 : a ≠ 0) : (a * n) /. (a * d) = n /. d
```

### `Int.mul_comm` (commanddeclaration)
```lean
protected theorem mul_comm (a b : Int) : a * b = b * a
```

## Premise full source (with proof)
### `Rat.divInt_mul_left` (commanddeclaration) at `.lake/packages/std/Std/Data/Rat/Lemmas.lean`
```lean
theorem divInt_mul_left {a : Int} (a0 : a ≠ 0) : (a * n) /. (a * d) = n /. d := by
  if d0 : d = 0 then simp [d0] else
  simp [divInt_eq_iff (Int.mul_ne_zero a0 d0) d0, Int.mul_assoc, Int.mul_left_comm]
```

### `Int.mul_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem mul_comm (a b : Int) : a * b = b * a := by
  cases a <;> cases b <;> simp [Nat.mul_comm]
```
