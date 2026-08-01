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

## Transitive premise context (1-hop, 11/11 premises, ≈1710 tokens)
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

### `String.revFindAux` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/String/Basic.lean`
```lean
def revFindAux (s : String) (p : Char → Bool) (pos : Pos) : Option Pos :=
  if h : pos = 0 then none
  else
    have := prev_lt_of_pos s pos h
    let pos := s.prev pos
    if p (s.get pos) then some pos
    else revFindAux s p pos
termination_by pos.1
```

### `String.utf8Len` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
/-- The UTF-8 byte length of a list of characters. (This is intended for specification purposes.) -/
@[inline] def utf8Len : List Char → Nat := utf8ByteSize.go
```

### `List.dropWhile` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/List/Basic.lean`
```lean
/--
`O(|l|)`. `dropWhile p l` removes elements from the list until it finds the first element
for which `p` returns false; this element and everything after it is returned.
```
dropWhile (· < 4) [1, 3, 2, 4, 2, 7, 4] = [4, 2, 7, 4]
```
-/
def dropWhile (p : α → Bool) : List α → List α
  | []   => []
  | a::l => match p a with
    | true  => dropWhile p l
    | false => a::l

/--
`O(|l|)`. `find? p l` returns the first element for which `p` returns true,
or `none` if no such element is found.

* `find? (· < 5) [7, 6, 5, 8, 1, 2, 6] = some 1`
* `find? (· < 1) [7, 6, 5, 8, 1, 2, 6] = none`
-/
```

### `dif_neg` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem dif_neg {c : Prop} {h : Decidable c} (hnc : ¬c) {α : Sort u} {t : c → α} {e : ¬ c → α} : (dite c t e) = e hnc :=
  match h with
  | isTrue hc   => absurd hc hnc
  | isFalse _   => rfl

-- Remark: dite and ite are "defally equal" when we ignore the proofs.
```

### `String.add_csize_pos` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
private theorem add_csize_pos : 0 < i + csize c :=
  Nat.add_pos_right _ (csize_pos c)
```

### `String.get_of_valid` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
theorem get_of_valid (cs cs' : List Char) : get ⟨cs ++ cs'⟩ ⟨utf8Len cs⟩ = cs'.headD default :=
  utf8GetAux_of_valid _ _ (Nat.zero_add _)
```

### `String.prev_of_valid` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
theorem prev_of_valid (cs : List Char) (c : Char) (cs' : List Char) :
    prev ⟨cs ++ c :: cs'⟩ ⟨utf8Len cs + csize c⟩ = ⟨utf8Len cs⟩ := by
  simp [prev]; refine (if_neg (Pos.ne_of_gt add_csize_pos)).trans ?_
  rw [utf8PrevAux_of_valid] <;> simp
```

### `NumberField.place` (commanddeclaration) at `Mathlib/NumberTheory/NumberField/Embeddings.lean`
```lean
/-- An embedding into a normed division ring defines a place of `K` -/
def NumberField.place : AbsoluteValue K ℝ :=
  (IsAbsoluteValue.toAbsoluteValue (norm : A → ℝ)).comp φ.injective
```

### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
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
