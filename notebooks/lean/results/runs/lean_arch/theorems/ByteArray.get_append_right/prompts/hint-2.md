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
