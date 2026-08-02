## Current goal
```
⊢ -a < b - c
```

## Full tactic state
```
a b c : Int
h✝ : c < a + b
h : -a < -c + b
⊢ -a < b - c
```

## Proof so far (1 tactic)
```lean
have h := Int.lt_neg_add_of_add_lt (Int.sub_left_lt_of_lt_add h)
```

## Theorem
`Int.neg_lt_sub_left_of_lt_add` in `.lake/packages/std/Std/Data/Int/Order.lean`

## Premises used in the next tactic
- `Int.add_comm`

## Premise signatures
### `Int.add_comm` (commanddeclaration)
```lean
protected theorem add_comm : ∀ a b : Int, a + b = b + a
```

## Premise full source (with proof)
### `Int.add_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Int/Lemmas.lean`
```lean
protected theorem add_comm : ∀ a b : Int, a + b = b + a
  | ofNat n, ofNat m => by simp [Nat.add_comm]
  | ofNat _, -[_+1]  => rfl
  | -[_+1],  ofNat _ => rfl
  | -[_+1],  -[_+1]  => by simp [Nat.add_comm]
```
