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

## Transitive premise context (1-hop, 4/4 premises, ≈745 tokens)
### `List` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`List α` is the type of ordered lists with elements of type `α`.
It is implemented as a linked list.

`List α` is isomorphic to `Array α`, but they are useful for different things:
* `List α` is easier for reasoning, and
  `Array α` is modeled as a wrapper around `List α`
* `List α` works well as a persistent data structure, when many copies of the
  tail are shared. When the value is not shared, `Array α` will have better
  performance because it can do destructive updates.
-/
inductive List (α : Type u) where
  /-- `[]` is the empty list. -/
  | nil : List α
  /-- If `a : α` and `l : List α`, then `cons a l`, or `a :: l`, is the
  list whose first element is `a` and with `l` as the rest of the list. -/
  | cons (head : α) (tail : List α) : List α
```

### `congrArg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
Congruence in the function argument: if `a₁ = a₂` then `f a₁ = f a₂` for
any (nondependent) function `f`. This is more powerful than it might look at first, because
you can also use a lambda expression for `f` to prove that
`<something containing a₁> = <something containing a₂>`. This function is used
internally by tactics like `congr` and `simp` to apply equalities inside
subterms.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
theorem congrArg {α : Sort u} {β : Sort v} {a₁ a₂ : α} (f : α → β) (h : Eq a₁ a₂) : Eq (f a₁) (f a₂) :=
  h ▸ rfl

/--
Congruence in both function and argument. If `f₁ = f₂` and `a₁ = a₂` then
`f₁ a₁ = f₂ a₂`. This only works for nondependent functions; the theorem
statement is more complex in the dependent case.

For more information: [Equality](https://lean-lang.org/theorem_proving_in_lean4/quantifiers_and_equality.html#equality)
-/
```

### `List.modifyNth_eq_take_drop` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem modifyNth_eq_take_drop (f : α → α) :
    ∀ n l, modifyNth f n l = take n l ++ modifyHead f (drop n l) :=
  modifyNthTail_eq_take_drop _ rfl
```

### `List.drop_eq_get_cons` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem drop_eq_get_cons {n} {l : List α} (h) : drop n l = get l ⟨n, h⟩ :: drop (n + 1) l :=
  (get_cons_drop _ ⟨n, h⟩).symm
```
