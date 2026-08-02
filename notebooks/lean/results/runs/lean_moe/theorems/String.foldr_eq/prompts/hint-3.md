## Current goal
```
⊢ foldr f a s = List.foldr f a s.data
```

## Full tactic state
```
α : Type u_1
f : Char → α → α
s : String
a : α
⊢ foldr f a s = List.foldr f a s.data
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`String.foldr_eq` in `.lake/packages/std/Std/Data/String/Lemmas.lean`

## Premises used in the next tactic
- `String.foldrAux_of_valid`

## Premise signatures
### `String.foldrAux_of_valid` (commanddeclaration)
```lean
@[nolint unusedHavesSuffices] theorem foldrAux_of_valid (f : Char → α → α) (l m r a) :
    foldrAux f a ⟨l ++ m ++ r⟩ ⟨utf8Len l + utf8Len m⟩ ⟨utf8Len l⟩ = m.foldr f a
```

## Premise full source (with proof)
### `String.foldrAux_of_valid` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
@[nolint unusedHavesSuffices] -- false positive from unfolding String.foldrAux
theorem foldrAux_of_valid (f : Char → α → α) (l m r a) :
    foldrAux f a ⟨l ++ m ++ r⟩ ⟨utf8Len l + utf8Len m⟩ ⟨utf8Len l⟩ = m.foldr f a := by
  rw [← m.reverse_reverse]
  induction m.reverse generalizing r a with (unfold foldrAux; simp)
  | cons c m IH =>
    rw [if_pos (by exact Nat.lt_add_of_pos_right add_csize_pos)]
    simp [← Nat.add_assoc, by simpa using prev_of_valid (l++m.reverse) c r]
    simp [by simpa using get_of_valid (l++m.reverse) (c::r)]
    simpa using IH (c::r) (f c a)
```

## Transitive premise context (1-hop, 10/10 premises, ≈1302 tokens)
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

### `String.foldrAux` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/String/Basic.lean`
```lean
@[specialize] def foldrAux {α : Type u} (f : Char → α → α) (a : α) (s : String) (i begPos : Pos) : α :=
  if h : begPos < i then
    have := String.prev_lt_of_pos s i <| mt (congrArg String.Pos.byteIdx) <|
      Ne.symm <| Nat.ne_of_lt <| Nat.lt_of_le_of_lt (Nat.zero_le _) h
    let i := s.prev i
    let a := f (s.get i) a
    foldrAux f a s i begPos
  else a
termination_by i.1
```

### `Char` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/-- The `Char` Type represents an unicode scalar value.
    See http://www.unicode.org/glossary/#unicode_scalar_value). -/
structure Char where
  /-- The underlying unicode scalar value as a `UInt32`. -/
  val   : UInt32
  /-- The value must be a legal codepoint. -/
  valid : val.isValidChar
```

### `String.utf8Len` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
/-- The UTF-8 byte length of a list of characters. (This is intended for specification purposes.) -/
@[inline] def utf8Len : List Char → Nat := utf8ByteSize.go
```

### `if_pos` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem if_pos {c : Prop} {h : Decidable c} (hc : c) {α : Sort u} {t e : α} : (ite c t e) = t :=
  match h with
  | isTrue  _   => rfl
  | isFalse hnc => absurd hc hnc
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

### `Nat.add_assoc` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Nat/Basic.lean`
```lean
protected theorem add_assoc : ∀ (n m k : Nat), (n + m) + k = n + (m + k)
  | _, _, 0      => rfl
  | n, m, succ k => congrArg succ (Nat.add_assoc n m k)
```

### `String.prev_of_valid` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
theorem prev_of_valid (cs : List Char) (c : Char) (cs' : List Char) :
    prev ⟨cs ++ c :: cs'⟩ ⟨utf8Len cs + csize c⟩ = ⟨utf8Len cs⟩ := by
  simp [prev]; refine (if_neg (Pos.ne_of_gt add_csize_pos)).trans ?_
  rw [utf8PrevAux_of_valid] <;> simp
```

### `String.get_of_valid` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
theorem get_of_valid (cs cs' : List Char) : get ⟨cs ++ cs'⟩ ⟨utf8Len cs⟩ = cs'.headD default :=
  utf8GetAux_of_valid _ _ (Nat.zero_add _)
```
