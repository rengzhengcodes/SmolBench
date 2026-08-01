## Current goal
```
⊢ m + HeapNode.realSize node + realSize next + 1 =
    realSize
        (merge le (HeapNode.toHeap { before := before, val := val, node := node, next := next }.node)
          ({ before := before, val := val, node := node, next := next }.before
            { before := before, val := val, node := node, next := next }.next)) +
      1
```

## Full tactic state
```
α : Type u_1
le : α → α → Bool
r : Nat
a : α
c : HeapNode α
s : Heap α
before : Heap α → Heap α
val : α
node : HeapNode α
next : Heap α
m : Nat
ih₁ : ∀ (s : Heap α), realSize (before s) = m + realSize s
ih₂ : HeapNode.realSize c + realSize s + 1 = m + HeapNode.realSize node + realSize next + 1
⊢ m + HeapNode.realSize node + realSize next + 1 =
    realSize
        (merge le (HeapNode.toHeap { before := before, val := val, node := node, next := next }.node)
          ({ before := before, val := val, node := node, next := next }.before
            { before := before, val := val, node := node, next := next }.next)) +
      1
```

## Proof so far (9 tactics)
```lean
cases s with cases eq | cons r a c s => ?_
have : (s.findMin le (cons r a c) ⟨id, a, c, s⟩).HasSize (c.realSize + s.realSize + 1) :=
  Heap.realSize_findMin (c.realSize + 1) (by simp) (Nat.add_right_comm ..) ⟨0, by simp⟩
revert this
match s.findMin le (cons r a c) ⟨id, a, c, s⟩ with
| { before, val, node, next } =>
  intro ⟨m, ih₁, ih₂⟩; dsimp only at ih₁ ih₂
  rw [realSize, Nat.add_right_comm, ih₂]
  simp only [realSize_merge, HeapNode.realSize_toHeap, ih₁, Nat.add_assoc, Nat.add_left_comm]
simp
simp
intro ⟨m, ih₁, ih₂⟩
dsimp only at ih₁ ih₂
rw [realSize, Nat.add_right_comm, ih₂]
```

## Theorem
`Std.BinomialHeap.Imp.Heap.realSize_deleteMin` in `.lake/packages/std/Std/Data/BinomialHeap/Basic.lean`

## Premises used in the next tactic
- `Std.BinomialHeap.Imp.Heap.realSize_merge`
- `Std.BinomialHeap.Imp.HeapNode.realSize_toHeap`
- `Nat.add_assoc`
- `Nat.add_left_comm`

## Premise signatures
### `Std.BinomialHeap.Imp.Heap.realSize_merge` (commanddeclaration)
```lean
theorem Heap.realSize_merge (le) (s₁ s₂ : Heap α) :
    (s₁.merge le s₂).realSize = s₁.realSize + s₂.realSize
```

### `Std.BinomialHeap.Imp.HeapNode.realSize_toHeap` (commanddeclaration)
```lean
theorem HeapNode.realSize_toHeap (s : HeapNode α) : s.toHeap.realSize = s.realSize
```

### `Nat.add_assoc` (commanddeclaration)
```lean
protected theorem add_assoc : ∀ (n m k : Nat), (n + m) + k = n + (m + k)
```

### `Nat.add_left_comm` (commanddeclaration)
```lean
protected theorem add_left_comm (n m k : Nat) : n + (m + k) = m + (n + k)
```

## Premise full source (with proof)
### `Std.BinomialHeap.Imp.Heap.realSize_merge` (commanddeclaration) at `.lake/packages/std/Std/Data/BinomialHeap/Basic.lean`
```lean
theorem Heap.realSize_merge (le) (s₁ s₂ : Heap α) :
    (s₁.merge le s₂).realSize = s₁.realSize + s₂.realSize := by
  unfold merge; split
  · simp
  · simp
  · next r₁ a₁ n₁ t₁ r₂ a₂ n₂ t₂ =>
    have IH₁ r a n := realSize_merge le t₁ (cons r a n t₂)
    have IH₂ r a n := realSize_merge le (cons r a n t₁) t₂
    have IH₃ := realSize_merge le t₁ t₂
    split; · simp [IH₁, Nat.add_assoc]
    split; · simp [IH₂, Nat.add_assoc, Nat.add_left_comm]
    split; simp only; rename_i a n eq
    have : n.realSize = n₁.realSize + 1 + n₂.realSize := by
      rw [combine] at eq; split at eq <;> cases eq <;>
        simp [Nat.add_assoc, Nat.add_left_comm, Nat.add_comm]
    split <;> split <;> simp [IH₁, IH₂, IH₃, this, Nat.add_assoc, Nat.add_left_comm]
termination_by s₁.length + s₂.length
```

### `Std.BinomialHeap.Imp.HeapNode.realSize_toHeap` (commanddeclaration) at `.lake/packages/std/Std/Data/BinomialHeap/Basic.lean`
```lean
theorem HeapNode.realSize_toHeap (s : HeapNode α) : s.toHeap.realSize = s.realSize := go s where
  go {n res} : ∀ s : HeapNode α, (toHeap.go s n res).realSize = s.realSize + res.realSize
  | .nil => (Nat.zero_add _).symm
  | .node a c s => by simp [toHeap.go, go, Nat.add_assoc, Nat.add_left_comm]
```

### `Nat.add_assoc` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_assoc : ∀ (n m k : Nat), (n + m) + k = n + (m + k)
  | _, _, 0      => rfl
  | n, m, succ k => congrArg succ (Nat.add_assoc n m k)
```

### `Nat.add_left_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_left_comm (n m k : Nat) : n + (m + k) = m + (n + k) := by
  rw [← Nat.add_assoc, Nat.add_comm n m, Nat.add_assoc]
```

## Filler (hint:2 → hint:3 token-match, ≈1512 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occ
