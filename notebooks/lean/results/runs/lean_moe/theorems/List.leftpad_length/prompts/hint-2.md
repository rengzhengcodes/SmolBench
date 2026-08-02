## Current goal
```
⊢ length (leftpad n a l) = max n (length l)
```

## Full tactic state
```
α : Type u_1
n : Nat
a : α
l : List α
⊢ length (leftpad n a l) = max n (length l)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`List.leftpad_length` in `.lake/packages/std/Std/Data/List/Lemmas.lean`

## Premises used in the next tactic
- `List.leftpad`
- `List.length_append`
- `List.length_replicate`
- `Nat.sub_add_eq_max`

## Premise signatures
### `List.leftpad` (commanddeclaration)
```lean
def leftpad (n : Nat) (a : α) (l : List α) : List α
```

### `List.length_append` (commanddeclaration)
```lean
@[simp] theorem length_append (as bs : List α) : (as ++ bs).length = as.length + bs.length
```

### `List.length_replicate` (commanddeclaration)
```lean
@[simp] theorem length_replicate (n : Nat) (a : α) : (replicate n a).length = n
```

### `Nat.sub_add_eq_max` (commanddeclaration)
```lean
protected theorem sub_add_eq_max (a b : Nat) : a - b + b = max a b
```

## Premise full source (with proof)
### `List.leftpad` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Basic.lean`
```lean
/--
Pads `l : List α` with repeated occurrences of `a : α` until it is of length `n`.
If `l` is initially larger than `n`, just return `l`.
-/
def leftpad (n : Nat) (a : α) (l : List α) : List α := replicate (n - length l) a ++ l

/-- Optimized version of `leftpad`. -/
```

### `List.length_append` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Basic.lean`
```lean
@[simp] theorem length_append (as bs : List α) : (as ++ bs).length = as.length + bs.length := by
  induction as with
  | nil => simp
  | cons _ as ih => simp [ih, Nat.succ_add]
```

### `List.length_replicate` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Basic.lean`
```lean
@[simp] theorem length_replicate (n : Nat) (a : α) : (replicate n a).length = n := by
  induction n <;> simp_all
```

### `Nat.sub_add_eq_max` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
protected theorem sub_add_eq_max (a b : Nat) : a - b + b = max a b := by
  match Nat.le_total a b with
  | .inl hl => rw [Nat.max_eq_right hl, Nat.sub_eq_zero_iff_le.mpr hl, Nat.zero_add]
  | .inr hr => rw [Nat.max_eq_left hr, Nat.sub_add_cancel hr]
```
