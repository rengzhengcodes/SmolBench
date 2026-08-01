## Current goal
```
⊢ offsetOfPos { data := l ++ r } { byteIdx := utf8Len l } = List.length l
```

## Full tactic state
```
l r : List Char
⊢ offsetOfPos { data := l ++ r } { byteIdx := utf8Len l } = List.length l
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`String.offsetOfPos_of_valid` in `.lake/packages/std/Std/Data/String/Lemmas.lean`

## Premises used in the next tactic
- `String.offsetOfPosAux_of_valid`

## Premise signatures
### `String.offsetOfPosAux_of_valid` (commanddeclaration)
```lean
@[nolint unusedHavesSuffices] theorem offsetOfPosAux_of_valid : ∀ l m r n,
    offsetOfPosAux ⟨l ++ m ++ r⟩ ⟨utf8Len l + utf8Len m⟩ ⟨utf8Len l⟩ n = n + m.length
```

## Premise full source (with proof)
### `String.offsetOfPosAux_of_valid` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
@[nolint unusedHavesSuffices] -- false positive from unfolding String.offsetOfPosAux
theorem offsetOfPosAux_of_valid : ∀ l m r n,
    offsetOfPosAux ⟨l ++ m ++ r⟩ ⟨utf8Len l + utf8Len m⟩ ⟨utf8Len l⟩ n = n + m.length
  | l, [], r, n => by unfold offsetOfPosAux; simp
  | l, c::m, r, n => by
    unfold offsetOfPosAux
    rw [if_neg (by exact Nat.not_le.2 (Nat.lt_add_of_pos_right add_csize_pos))]
    simp only [List.append_assoc, atEnd_of_valid l (c::m++r)]
    simp [next_of_valid l c (m++r)]
    simpa [← Nat.add_assoc, Nat.add_right_comm, Nat.succ_eq_add_one] using
      offsetOfPosAux_of_valid (l++[c]) m r (n + 1)
```
