## Current goal
```
⊢ modifyNth f n l = modifyNthTR f n l
```

## Full tactic state
```
case h.h.h.h
α : Type u_1
f : α → α
n : Nat
l : List α
⊢ modifyNth f n l = modifyNthTR f n l
```

## Proof so far (1 tactic)
```lean
funext α f n l
```

## Theorem
`List.modifyNth_eq_modifyNthTR` in `.lake/packages/std/Std/Data/List/Basic.lean`

## Premises used in the next tactic
- `List.modifyNthTR`
- `List.modifyNthTR_go_eq`

## Premise signatures
### `List.modifyNthTR` (commanddeclaration)
```lean
def modifyNthTR (f : α → α) (n : Nat) (l : List α) : List α
```

### `List.modifyNthTR_go_eq` (commanddeclaration)
```lean
theorem modifyNthTR_go_eq : ∀ l n, modifyNthTR.go f l n acc = acc.data ++ modifyNth f n l
```

## Premise full source (with proof)
### `List.modifyNthTR` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Basic.lean`
```lean
/-- Tail-recursive version of `modifyNth`. -/
def modifyNthTR (f : α → α) (n : Nat) (l : List α) : List α := go l n #[] where
  /-- Auxiliary for `modifyNthTR`: `modifyNthTR.go f l n acc = acc.toList ++ modifyNth f n l`. -/
  go : List α → Nat → Array α → List α
  | [], _, acc => acc.toList
  | a :: l, 0, acc => acc.toListAppend (f a :: l)
  | a :: l, n+1, acc => go l n (acc.push a)
```

### `List.modifyNthTR_go_eq` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Basic.lean`
```lean
theorem modifyNthTR_go_eq : ∀ l n, modifyNthTR.go f l n acc = acc.data ++ modifyNth f n l
  | [], n => by cases n <;> simp [modifyNthTR.go, modifyNth]
  | a :: l, 0 => by simp [modifyNthTR.go, modifyNth]
  | a :: l, n+1 => by simp [modifyNthTR.go, modifyNth, modifyNthTR_go_eq l]
```
