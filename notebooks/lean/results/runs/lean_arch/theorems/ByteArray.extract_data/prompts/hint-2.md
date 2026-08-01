## Current goal
```
⊢ Array.extract a.data start (start + (stop - start)) = Array.extract a.data start stop
```

## Full tactic state
```
a : ByteArray
start stop : Nat
h : stop ≤ start
⊢ Array.extract a.data start (start + (stop - start)) = Array.extract a.data start stop
```

## Proof so far (3 tactics)
```lean
simp [extract]
match Nat.le_total start stop with
| .inl h => simp [h, Nat.add_sub_cancel']
| .inr h => simp [h, Nat.sub_eq_zero_of_le, Array.extract_empty_of_stop_le_start]
simp [h, Nat.add_sub_cancel']
```

## Theorem
`ByteArray.extract_data` in `.lake/packages/std/Std/Data/ByteArray.lean`

## Premises used in the next tactic
- `Nat.sub_eq_zero_of_le`
- `Array.extract_empty_of_stop_le_start`

## Premise signatures
### `Nat.sub_eq_zero_of_le` (commanddeclaration)
```lean
protected theorem sub_eq_zero_of_le {n m : Nat} (h : n ≤ m) : n - m = 0
```

### `Array.extract_empty_of_stop_le_start` (commanddeclaration)
```lean
theorem extract_empty_of_stop_le_start (as : Array α) {start stop : Nat} (h : stop ≤ start) :
    as.extract start stop = #[]
```

## Premise full source (with proof)
### `Nat.sub_eq_zero_of_le` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem sub_eq_zero_of_le {n m : Nat} (h : n ≤ m) : n - m = 0 := by
  match le.dest h with
  | ⟨k, hk⟩ => rw [← hk, Nat.sub_self_add]
```

### `Array.extract_empty_of_stop_le_start` (commanddeclaration) at `.lake/packages/std/Std/Data/Array/Lemmas.lean`
```lean
theorem extract_empty_of_stop_le_start (as : Array α) {start stop : Nat} (h : stop ≤ start) :
    as.extract start stop = #[] := by
  simp [extract]; rw [←Nat.sub_min_sub_right, Nat.sub_eq_zero_of_le h, Nat.zero_min,
    extract_loop_zero]
```
