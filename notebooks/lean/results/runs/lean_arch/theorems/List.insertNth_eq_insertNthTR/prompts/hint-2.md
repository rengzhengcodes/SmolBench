## Current goal
```
⊢ insertNth f n l = insertNthTR f n l
```

## Full tactic state
```
case h.h.h.h
α : Type u_1
f : Nat
n : α
l : List α
⊢ insertNth f n l = insertNthTR f n l
```

## Proof so far (1 tactic)
```lean
funext α f n l
```

## Theorem
`List.insertNth_eq_insertNthTR` in `.lake/packages/std/Std/Data/List/Basic.lean`

## Premises used in the next tactic
- `List.insertNthTR`
- `List.insertNthTR_go_eq`

## Premise signatures
### `List.insertNthTR` (commanddeclaration)
```lean
@[inline] def insertNthTR (n : Nat) (a : α) (l : List α) : List α
```

### `List.insertNthTR_go_eq` (commanddeclaration)
```lean
theorem insertNthTR_go_eq : ∀ n l, insertNthTR.go a n l acc = acc.data ++ insertNth n a l
```

## Premise full source (with proof)
### `List.insertNthTR` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Basic.lean`
```lean
/-- Tail-recursive version of `insertNth`. -/
@[inline] def insertNthTR (n : Nat) (a : α) (l : List α) : List α := go n l #[] where
  /-- Auxiliary for `insertNthTR`: `insertNthTR.go a n l acc = acc.toList ++ insertNth n a l`. -/
  go : Nat → List α → Array α → List α
  | 0, l, acc => acc.toListAppend (a :: l)
  | _, [], acc => acc.toList
  | n+1, a :: l, acc => go n l (acc.push a)
```

### `List.insertNthTR_go_eq` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Basic.lean`
```lean
theorem insertNthTR_go_eq : ∀ n l, insertNthTR.go a n l acc = acc.data ++ insertNth n a l
  | 0, l | _+1, [] => by simp [insertNthTR.go, insertNth]
  | n+1, a :: l => by simp [insertNthTR.go, insertNth, insertNthTR_go_eq n l]
```
