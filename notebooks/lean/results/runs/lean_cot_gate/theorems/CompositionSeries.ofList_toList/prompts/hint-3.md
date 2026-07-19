## Current goal
```
⊢ (ofList (toList s) ⋯ ⋯).series { val := i, isLt := hi } = s.series (Fin.cast ⋯ { val := i, isLt := hi })
```

## Full tactic state
```
case refine'_2.mk
X : Type u
inst✝¹ : Lattice X
inst✝ : JordanHolderLattice X
s : CompositionSeries X
i : ℕ
hi : i < (ofList (toList s) ⋯ ⋯).length + 1
⊢ (ofList (toList s) ⋯ ⋯).series { val := i, isLt := hi } = s.series (Fin.cast ⋯ { val := i, isLt := hi })
```

## Proof so far (3 tactics)
```lean
refine' ext_fun _ _
rw [length_ofList, length_toList, Nat.add_one_sub_one]
rintro ⟨i, hi⟩
```

## Theorem
`CompositionSeries.ofList_toList` in `Mathlib/Order/JordanHolder.lean`

## Premises used in the next tactic
- `CompositionSeries.ofList`
- `CompositionSeries.toList`

## Premise signatures
### `CompositionSeries.ofList` (commanddeclaration)
```lean
def ofList (l : List X) (hl : l ≠ []) (hc : List.Chain' IsMaximal l) : CompositionSeries X
    where
  length
```

### `CompositionSeries.toList` (commanddeclaration)
```lean
def toList (s : CompositionSeries X) : List X
```

## Premise full source (with proof)
### `CompositionSeries.ofList` (commanddeclaration) at `Mathlib/Order/JordanHolder.lean`
```lean
/-- Make a `CompositionSeries X` from the ordered list of its elements. -/
def ofList (l : List X) (hl : l ≠ []) (hc : List.Chain' IsMaximal l) : CompositionSeries X
    where
  length := l.length - 1
  series i :=
    l.nthLe i
      (by
        conv_rhs => rw [← tsub_add_cancel_of_le (Nat.succ_le_of_lt (List.length_pos_of_ne_nil hl))]
        exact i.2)
  step' := fun ⟨i, hi⟩ => List.chain'_iff_get.1 hc i hi
```

### `CompositionSeries.toList` (commanddeclaration) at `Mathlib/Order/JordanHolder.lean`
```lean
/-- The ordered `List X` of elements of a `CompositionSeries X`. -/
def toList (s : CompositionSeries X) : List X :=
  List.ofFn s
```

## Transitive premise context (1-hop, 7/7 premises, ≈892 tokens)
### `CompositionSeries` (commanddeclaration) at `Mathlib/Order/JordanHolder.lean`
```lean
/-- A `CompositionSeries X` is a finite nonempty series of elements of a
`JordanHolderLattice` such that each element is maximal inside the next. The length of a
`CompositionSeries X` is one less than the number of elements in the series.
Note that there is no stipulation that a series start from the bottom of the lattice and finish at
the top. For a composition series `s`, `s.top` is the largest element of the series,
and `s.bot` is the least element.
-/
structure CompositionSeries (X : Type u) [Lattice X] [JordanHolderLattice X] : Type u where
  length : ℕ
  series : Fin (length + 1) → X
  step' : ∀ i : Fin length, IsMaximal (series (Fin.castSucc i)) (series (Fin.succ i))
```

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

### `List.Chain'` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Basic.lean`
```lean
/-- `Chain' R l` means that `R` holds between adjacent elements of `l`.
```
Chain' R [a, b, c, d] ↔ R a b ∧ R b c ∧ R c d
``` -/
def Chain' : List α → Prop
  | [] => True
  | a :: l => Chain R a l
```

### `tsub_add_cancel_of_le` (commanddeclaration) at `Mathlib/Algebra/Order/Sub/Canonical.lean`
```lean
theorem tsub_add_cancel_of_le (h : a ≤ b) : b - a + a = b := by
  rw [add_comm]
  exact add_tsub_cancel_of_le h
```

### `Nat.succ_le_of_lt` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
theorem succ_le_of_lt {n m : Nat} (h : n < m) : succ n ≤ m := h
```

### `List.length_pos_of_ne_nil` (stdtacticaliasaliaslr) at `Mathlib/Data/List/Basic.lean`
```lean
alias ⟨ne_nil_of_length_pos, length_pos_of_ne_nil⟩ := length_pos
```

### `List.ofFn` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Basic.lean`
```lean
/--
`ofFn f` with `f : fin n → α` returns the list whose ith element is `f i`
```
ofFn f = [f 0, f 1, ... , f (n - 1)]
```
-/
def ofFn {n} (f : Fin n → α) : List α := (Array.ofFn f).data

/-- `ofFnNthVal f i` returns `some (f i)` if `i < n` and `none` otherwise. -/
```
