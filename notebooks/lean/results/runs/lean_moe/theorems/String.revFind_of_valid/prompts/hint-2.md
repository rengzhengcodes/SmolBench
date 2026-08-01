## Current goal
```
⊢ revFind s p =
    Option.map (fun x => { byteIdx := utf8Len x }) (List.tail? (List.dropWhile (fun x => !p x) (List.reverse s.data)))
```

## Full tactic state
```
p : Char → Bool
s : String
⊢ revFind s p =
    Option.map (fun x => { byteIdx := utf8Len x }) (List.tail? (List.dropWhile (fun x => !p x) (List.reverse s.data)))
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`String.revFind_of_valid` in `.lake/packages/std/Std/Data/String/Lemmas.lean`

## Premises used in the next tactic
- `String.revFindAux_of_valid`
- `List.reverse`

## Premise signatures
### `String.revFindAux_of_valid` (commanddeclaration)
```lean
@[nolint unusedHavesSuffices] theorem revFindAux_of_valid (p) : ∀ l r,
    revFindAux ⟨l.reverse ++ r⟩ p ⟨utf8Len l⟩ = (l.dropWhile (!p ·)).tail?.map (⟨utf8Len ·⟩)
```

### `List.reverse` (commanddeclaration)
```lean
def reverse (as : List α) : List α
```

## Premise full source (with proof)
### `String.revFindAux_of_valid` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
@[nolint unusedHavesSuffices] -- false positive from unfolding String.revFindAux
theorem revFindAux_of_valid (p) : ∀ l r,
    revFindAux ⟨l.reverse ++ r⟩ p ⟨utf8Len l⟩ = (l.dropWhile (!p ·)).tail?.map (⟨utf8Len ·⟩)
  | [], r => by unfold revFindAux List.dropWhile; simp
  | c::l, r => by
    unfold revFindAux List.dropWhile
    rw [dif_neg (by exact Pos.ne_of_gt add_csize_pos)]
    have h1 := get_of_valid l.reverse (c::r); have h2 := prev_of_valid l.reverse c r
    simp at h1 h2; simp [h1, h2]
    cases p c <;> simp
    exact revFindAux_of_valid p l (c::r)
```

### `List.reverse` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Basic.lean`
```lean
/--
`O(|as|)`. Reverse of a list:
* `[1, 2, 3, 4].reverse = [4, 3, 2, 1]`

Note that because of the "functional but in place" optimization implemented by Lean's compiler,
this function works without any allocations provided that the input list is unshared:
it simply walks the linked list and reverses all the node pointers.
-/
def reverse (as : List α) : List α :=
  reverseAux as []
```
