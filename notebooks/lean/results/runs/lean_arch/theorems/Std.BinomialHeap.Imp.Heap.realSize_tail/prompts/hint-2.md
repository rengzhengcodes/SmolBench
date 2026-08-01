## Current goal
```
⊢ realSize (Option.getD (some tl) nil) = realSize s - 1
```

## Full tactic state
```
α : Type u_1
le : α → α → Bool
s tl : Heap α
eq : tail? le s = some tl
⊢ realSize (Option.getD (some tl) nil) = realSize s - 1
```

## Proof so far (4 tactics)
```lean
simp only [Heap.tail]
match eq : s.tail? le with
| none => cases s with cases eq | nil => rfl
| some tl => simp [Heap.realSize_tail? eq]
cases s with cases eq | nil => rfl
rfl
```

## Theorem
`Std.BinomialHeap.Imp.Heap.realSize_tail` in `.lake/packages/std/Std/Data/BinomialHeap/Basic.lean`

## Premises used in the next tactic
- `Std.BinomialHeap.Imp.Heap.realSize_tail?`

## Premise signatures
### `Std.BinomialHeap.Imp.Heap.realSize_tail?` (commanddeclaration)
```lean
theorem Heap.realSize_tail? {s : Heap α} : s.tail? le = some s' →
    s.realSize = s'.realSize + 1
```

## Premise full source (with proof)
### `Std.BinomialHeap.Imp.Heap.realSize_tail?` (commanddeclaration) at `.lake/packages/std/Std/Data/BinomialHeap/Basic.lean`
```lean
theorem Heap.realSize_tail? {s : Heap α} : s.tail? le = some s' →
    s.realSize = s'.realSize + 1 := by
  simp only [Heap.tail?]; intro eq
  match eq₂ : s.deleteMin le, eq with
  | some (a, tl), rfl => exact realSize_deleteMin eq₂
```
