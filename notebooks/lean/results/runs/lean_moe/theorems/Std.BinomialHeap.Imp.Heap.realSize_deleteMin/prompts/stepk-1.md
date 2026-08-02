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
