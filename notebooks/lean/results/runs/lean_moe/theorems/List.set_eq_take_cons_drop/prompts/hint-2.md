## Current goal
```
⊢ set l n a = take n l ++ a :: drop (n + 1) l
```

## Full tactic state
```
α : Type u_1
a : α
n : Nat
l : List α
h : n < length l
⊢ set l n a = take n l ++ a :: drop (n + 1) l
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`List.set_eq_take_cons_drop` in `.lake/packages/std/Std/Data/List/Lemmas.lean`

## Premises used in the next tactic
- `List.set_eq_modifyNth`
- `List.modifyNth_eq_take_cons_drop`

## Premise signatures
### `List.set_eq_modifyNth` (commanddeclaration)
```lean
theorem set_eq_modifyNth (a : α) : ∀ n (l : List α), set l n a = modifyNth (fun _ => a) n l
```

### `List.modifyNth_eq_take_cons_drop` (commanddeclaration)
```lean
theorem modifyNth_eq_take_cons_drop (f : α → α) {n l} (h) :
    modifyNth f n l = take n l ++ f (get l ⟨n, h⟩) :: drop (n + 1) l
```

## Premise full source (with proof)
### `List.set_eq_modifyNth` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem set_eq_modifyNth (a : α) : ∀ n (l : List α), set l n a = modifyNth (fun _ => a) n l
  | 0, l => by cases l <;> rfl
  | n+1, [] => rfl
  | n+1, b :: l => congrArg (cons _) (set_eq_modifyNth _ _ _)
```

### `List.modifyNth_eq_take_cons_drop` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem modifyNth_eq_take_cons_drop (f : α → α) {n l} (h) :
    modifyNth f n l = take n l ++ f (get l ⟨n, h⟩) :: drop (n + 1) l := by
  rw [modifyNth_eq_take_drop, drop_eq_get_cons h]; rfl

/-! ### set -/
```
