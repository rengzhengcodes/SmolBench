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

## Transitive premise context (1-hop, 1/1 premises, ≈269 tokens)
### `Std.BinomialHeap.Imp.Heap.realSize_deleteMin` (commanddeclaration) at `.lake/packages/std/Std/Data/BinomialHeap/Basic.lean`
```lean
theorem Heap.realSize_deleteMin {s : Heap α} (eq : s.deleteMin le = some (a, s')) :
    s.realSize = s'.realSize + 1 := by
  cases s with cases eq | cons r a c s => ?_
  have : (s.findMin le (cons r a c) ⟨id, a, c, s⟩).HasSize (c.realSize + s.realSize + 1) :=
    Heap.realSize_findMin (c.realSize + 1) (by simp) (Nat.add_right_comm ..) ⟨0, by simp⟩
  revert this
  match s.findMin le (cons r a c) ⟨id, a, c, s⟩ with
  | { before, val, node, next } =>
    intro ⟨m, ih₁, ih₂⟩; dsimp only at ih₁ ih₂
    rw [realSize, Nat.add_right_comm, ih₂]
    simp only [realSize_merge, HeapNode.realSize_toHeap, ih₁, Nat.add_assoc, Nat.add_left_comm]
```
