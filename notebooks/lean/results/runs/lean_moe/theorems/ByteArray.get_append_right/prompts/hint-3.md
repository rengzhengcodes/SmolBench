## Current goal
```
⊢ (a.data ++ b.data)[i] = b.data[i - size a]
```

## Full tactic state
```
i : Nat
a b : ByteArray
hle : size a ≤ i
h : i < size (a ++ b)
h' : optParam (i - size a < size b) ⋯
⊢ (a.data ++ b.data)[i] = b.data[i - size a]
```

## Proof so far (1 tactic)
```lean
simp [getElem_eq_data_getElem]
```

## Theorem
`ByteArray.get_append_right` in `.lake/packages/std/Std/Data/ByteArray.lean`

## Premises used in the next tactic
- `Array.get_append_right`

## Premise signatures
### `Array.get_append_right` (commanddeclaration)
```lean
theorem get_append_right {as bs : Array α} {h : i < (as ++ bs).size} (hle : as.size ≤ i)
    (hlt : i - as.size < bs.size := Nat.sub_lt_left_of_lt_add hle (size_append .. ▸ h)) :
    (as ++ bs)[i] = bs[i - as.size]
```

## Premise full source (with proof)
### `Array.get_append_right` (commanddeclaration) at `.lake/packages/std/Std/Data/Array/Lemmas.lean`
```lean
theorem get_append_right {as bs : Array α} {h : i < (as ++ bs).size} (hle : as.size ≤ i)
    (hlt : i - as.size < bs.size := Nat.sub_lt_left_of_lt_add hle (size_append .. ▸ h)) :
    (as ++ bs)[i] = bs[i - as.size] := by
  simp only [getElem_eq_data_get]
  have h' : i < (as.data ++ bs.data).length := by rwa [← data_length, append_data] at h
  conv => rhs; rw [← List.get_append_right (h':=h') (h:=Nat.not_lt_of_ge hle)]
  apply List.get_of_eq; rw [append_data]
```

## Transitive premise context (1-hop, 7/7 premises, ≈920 tokens)
### `Array` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Array α` is the type of [dynamic arrays](https://en.wikipedia.org/wiki/Dynamic_array)
with elements from `α`. This type has special support in the runtime.

An array has a size and a capacity; the size is `Array.size` but the capacity
is not observable from Lean code. Arrays perform best when unshared; as long
as they are used "linearly" all updates will be performed destructively on the
array, so it has comparable performance to mutable arrays in imperative
programming languages.

From the point of view of proofs `Array α` is just a wrapper around `List α`.
-/
structure Array (α : Type u) where
  /--
  Converts a `List α` into an `Array α`.

  At runtime, this constructor is implemented by `List.toArray` and is O(n) in the length of the
  list.
  -/
  mk ::
  /--
  Converts a `Array α` into an `List α`.

  At runtime, this projection is implemented by `Array.toList` and is O(n) in the length of the
  array. -/
  data : List α
```

### `Nat.sub_lt_left_of_lt_add` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem sub_lt_left_of_lt_add {n k m : Nat} (H : n ≤ k) (h : k < n + m) : k - n < m := by
  have := Nat.sub_le_sub_right (succ_le_of_lt h) n
  rwa [Nat.add_sub_cancel_left, Nat.succ_sub H] at this
```

### `Array.getElem_eq_data_get` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Array/Lemmas.lean`
```lean
theorem getElem_eq_data_get (a : Array α) (h : i < a.size) : a[i] = a.data.get ⟨i, h⟩ := by
  by_cases i < a.size <;> (try simp [*]) <;> rfl
```

### `Array.data_length` (commanddeclaration) at `.lake/packages/std/Std/Data/Array/Lemmas.lean`
```lean
@[simp] theorem data_length {l : Array α} : l.data.length = l.size := rfl

/-- # mem -/
```

### `List.get_append_right` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/BasicAux.lean`
```lean
theorem get_append_right (as bs : List α) (h : ¬ i < as.length) {h' h''} : (as ++ bs).get ⟨i, h'⟩ = bs.get ⟨i - as.length, h''⟩ := by
  induction as generalizing i with
  | nil => trivial
  | cons a as ih =>
    cases i with simp [get, Nat.succ_sub_succ] <;> simp_arith [Nat.succ_sub_succ] at h
    | succ i => apply ih; simp_arith [h]
```

### `Nat.not_lt_of_ge` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem not_lt_of_ge : ∀{a b : Nat}, b ≥ a → ¬(b < a) := flip Nat.not_le_of_gt
```

### `List.get_of_eq` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
/--
If one has `get l i hi` in a formula and `h : l = l'`, one can not `rw h` in the formula as
`hi` gives `i < l.length` and not `i < l'.length`. The theorem `get_of_eq` can be used to make
such a rewrite, with `rw (get_of_eq h)`.
-/
theorem get_of_eq {l l' : List α} (h : l = l') (i : Fin l.length) :
    get l i = get l' ⟨i, h ▸ i.2⟩ := by cases h; rfl
```
