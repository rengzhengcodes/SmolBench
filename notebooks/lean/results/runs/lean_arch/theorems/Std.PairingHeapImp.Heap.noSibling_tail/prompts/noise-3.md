## Current goal
```
⊢ NoSibling (Option.getD (some tl) nil)
```

## Full tactic state
```
α : Type u_1
le : α → α → Bool
s tl : Heap α
eq : tail? le s = some tl
⊢ NoSibling (Option.getD (some tl) nil)
```

## Proof so far (4 tactics)
```lean
simp only [Heap.tail]
match eq : s.tail? le with
| none => cases s with cases eq | nil => constructor
| some tl => exact Heap.noSibling_tail? eq
cases s with cases eq | nil => constructor
constructor
```

## Theorem
`Std.PairingHeapImp.Heap.noSibling_tail` in `.lake/packages/std/Std/Data/PairingHeap.lean`

## Premises used in the next tactic
- `Std.PairingHeapImp.Heap.noSibling_tail?`

## Premise signatures
### `Std.PairingHeapImp.Heap.noSibling_tail?` (commanddeclaration)
```lean
theorem Heap.noSibling_tail? {s : Heap α} : s.tail? le = some s' →
    s'.NoSibling
```

## Premise full source (with proof)
### `Std.PairingHeapImp.Heap.noSibling_tail?` (commanddeclaration) at `.lake/packages/std/Std/Data/PairingHeap.lean`
```lean
theorem Heap.noSibling_tail? {s : Heap α} : s.tail? le = some s' →
    s'.NoSibling := by
  simp only [Heap.tail?]; intro eq
  match eq₂ : s.deleteMin le, eq with
  | some (a, tl), rfl => exact noSibling_deleteMin eq₂
```

## Filler (hint:2 → hint:3 token-match, ≈111 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
