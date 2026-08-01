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

## Transitive premise context (1-hop, 12/12 premises, ≈1411 tokens)
### `Std.Tactic.Lint.unusedHavesSuffices` (commanddeclaration) at `.lake/packages/std/Std/Tactic/Lint/Misc.lean`
```lean
/-- A linter for checking that declarations don't have unused term mode have statements. We do not
tag this as `@[std_linter]` so that it is not in the default linter set as it is slow and an
uncommon problem. -/
@[std_linter] def unusedHavesSuffices : Linter where
  noErrorsFound := "No declarations have unused term mode have statements."
  errorsFound := "THE FOLLOWING DECLARATIONS HAVE INEFFECTUAL TERM MODE HAVE/SUFFICES BLOCKS. \
    In the case of `have` this is a term of the form `have h := foo, bar` where `bar` does not \
    refer to `foo`. Such statements have no effect on the generated proof, and can just be \
    replaced by `bar`, in addition to being ineffectual, they may make unnecessary assumptions \
    in proofs appear as if they are used. \
    For `suffices` this is a term of the form `suffices h : foo, proof_of_goal, proof_of_foo` \
    where `proof_of_goal` does not refer to `foo`. \
    Such statements have no effect on the generated proof, and can just be replaced by \
    `proof_of_goal`, in addition to being ineffectual, they may make unnecessary assumptions \
    in proofs appear as if they are used."
  test declName := do
    if ← isAutoDecl declName then return none
    let info ← getConstInfo declName
    let mut unused ← findUnusedHaves info.type
    if let some value := info.value? then
      unused := unused ++ (← findUnusedHaves value)
    unless unused.isEmpty do
      return some <| .joinSep unused.toList ", "
    return none

/--
A linter for checking if variables appearing on both sides of an iff are explicit. Ideally, such
```

### `String.offsetOfPosAux` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/String/Basic.lean`
```lean
def offsetOfPosAux (s : String) (pos : Pos) (i : Pos) (offset : Nat) : Nat :=
  if i >= pos then offset
  else if h : s.atEnd i then
    offset
  else
    have := Nat.sub_lt_sub_left (Nat.gt_of_not_le (mt decide_eq_true h)) (lt_next s _)
    offsetOfPosAux s pos (s.next i) (offset+1)
termination_by s.endPos.1 - i.1
```

### `String.utf8Len` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
/-- The UTF-8 byte length of a list of characters. (This is intended for specification purposes.) -/
@[inline] def utf8Len : List Char → Nat := utf8ByteSize.go
```

### `if_neg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem if_neg {c : Prop} {h : Decidable c} (hnc : ¬c) {α : Sort u} {t e : α} : (ite c t e) = e :=
  match h with
  | isTrue hc   => absurd hc hnc
  | isFalse _   => rfl

/-- Split an if-then-else into cases. The `split` tactic is generally easier to use than this theorem. -/
```

### `Nat.lt_add_of_pos_right` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Lemmas.lean`
```lean
protected theorem lt_add_of_pos_right (h : 0 < k) : n < n + k :=
  Nat.add_lt_add_left h n
```

### `String.add_csize_pos` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
private theorem add_csize_pos : 0 < i + csize c :=
  Nat.add_pos_right _ (csize_pos c)
```

### `List.append_assoc` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Basic.lean`
```lean
theorem append_assoc (as bs cs : List α) : (as ++ bs) ++ cs = as ++ (bs ++ cs) := by
  induction as with
  | nil => rfl
  | cons a as ih => simp [ih]
```

### `String.atEnd_of_valid` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
theorem atEnd_of_valid (cs : List Char) (cs' : List Char) :
    atEnd ⟨cs ++ cs'⟩ ⟨utf8Len cs⟩ ↔ cs' = [] := by
  rw [atEnd_iff]
  cases cs' <;> simp [Nat.lt_add_of_pos_right add_csize_pos]
```

### `String.next_of_valid` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
theorem next_of_valid (cs : List Char) (c : Char) (cs' : List Char) :
    next ⟨cs ++ c :: cs'⟩ ⟨utf8Len cs⟩ = ⟨utf8Len cs + csize c⟩ := next_of_valid' ..
```

### `Nat.add_assoc` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_assoc : ∀ (n m k : Nat), (n + m) + k = n + (m + k)
  | _, _, 0      => rfl
  | n, m, succ k => congrArg succ (Nat.add_assoc n m k)
```

### `Nat.add_right_comm` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_right_comm (n m k : Nat) : (n + m) + k = (n + k) + m := by
  rw [Nat.add_assoc, Nat.add_comm m k, ← Nat.add_assoc]
```

### `Nat.succ_eq_add_one` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
theorem succ_eq_add_one (n : Nat) : succ n = n + 1 :=
  rfl
```
