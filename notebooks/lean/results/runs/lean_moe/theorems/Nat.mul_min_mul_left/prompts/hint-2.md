## Current goal
```
⊢ min (b * a) (c * a) = a * min b c
```

## Full tactic state
```
a b c : Nat
⊢ min (b * a) (c * a) = a * min b c
```

## Proof so far (2 tactics)
```lean
repeat rw [Nat.mul_comm a]
exact Nat.mul_min_mul_right ..
```

## Theorem
`Nat.mul_min_mul_left` in `.lake/packages/std/Std/Data/Nat/Lemmas.lean`

## Premises used in the next tactic
- `Nat.mul_comm`

## Premise signatures
### `Nat.mul_comm` (commanddeclaration)
```lean
protected theorem mul_comm : ∀ (n m : Nat), n * m = m * n
```

## Premise full source (with proof)
### `Nat.mul_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem mul_comm : ∀ (n m : Nat), n * m = m * n
  | n, 0      => (Nat.zero_mul n).symm ▸ (Nat.mul_zero n).symm ▸ rfl
  | n, succ m => (mul_succ n m).symm ▸ (succ_mul m n).symm ▸ (Nat.mul_comm n m).symm ▸ rfl
```
