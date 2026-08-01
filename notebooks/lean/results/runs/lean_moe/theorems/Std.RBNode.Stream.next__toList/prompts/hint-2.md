## Current goal
```
⊢ Option.map
      (fun x =>
        match x with
        | (a, b) => (a, toList b))
      (next? s) =
    List.next? (toList s)
```

## Full tactic state
```
α : Type u_1
s : RBNode.Stream α
⊢ Option.map
      (fun x =>
        match x with
        | (a, b) => (a, toList b))
      (next? s) =
    List.next? (toList s)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Std.RBNode.Stream.next?_toList` in `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`

## Premises used in the next tactic
- `Std.RBNode.Stream.next?`
- `Std.RBNode.toStream_toList'`

## Premise signatures
### `Std.RBNode.Stream.next?` (commanddeclaration)
```lean
def next? : RBNode.Stream α → Option (α × RBNode.Stream α)
  | nil => none
  | cons v r tail => some (v, toStream r tail)
```

### `Std.RBNode.toStream_toList'` (commanddeclaration)
```lean
theorem toStream_toList' {t : RBNode α} {s} : (t.toStream s).toList = t.toList ++ s.toList
```

## Premise full source (with proof)
### `Std.RBNode.Stream.next?` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Basic.lean`
```lean
/-- `O(1)` amortized, `O(log n)` worst case: Get the next element from the stream. -/
def next? : RBNode.Stream α → Option (α × RBNode.Stream α)
  | nil => none
  | cons v r tail => some (v, toStream r tail)

/-- Fold a function on the values from left to right (in increasing order). -/
```

### `Std.RBNode.toStream_toList'` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem toStream_toList' {t : RBNode α} {s} : (t.toStream s).toList = t.toList ++ s.toList := by
  induction t generalizing s <;> simp [*, toStream]
```
