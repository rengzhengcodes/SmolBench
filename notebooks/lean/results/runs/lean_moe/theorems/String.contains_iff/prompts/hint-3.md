## Current goal
```
⊢ contains s c = true ↔ c ∈ s.data
```

## Full tactic state
```
s : String
c : Char
⊢ contains s c = true ↔ c ∈ s.data
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`String.contains_iff` in `.lake/packages/std/Std/Data/String/Lemmas.lean`

## Premises used in the next tactic
- `String.contains`
- `String.any_iff`

## Premise signatures
### `String.contains` (commanddeclaration)
```lean
def contains (s : String) (c : Char) : Bool
```

### `String.any_iff` (commanddeclaration)
```lean
theorem any_iff (s : String) (p : Char → Bool) : any s p ↔ ∃ c ∈ s.1, p c
```

## Premise full source (with proof)
### `String.contains` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/String/Basic.lean`
```lean
def contains (s : String) (c : Char) : Bool :=
s.any (fun a => a == c)
```

### `String.any_iff` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
theorem any_iff (s : String) (p : Char → Bool) : any s p ↔ ∃ c ∈ s.1, p c := by simp [any_eq]
```

## Transitive premise context (1-hop, 3/3 premises, ≈571 tokens)
### `String` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`String` is the type of (UTF-8 encoded) strings.

The compiler overrides the data representation of this type to a byte sequence,
and both `String.utf8ByteSize` and `String.length` are cached and O(1).
-/
structure String where
  /-- Pack a `List Char` into a `String`. This function is overridden by the
  compiler and is O(n) in the length of the list. -/
  mk ::
  /-- Unpack `String` into a `List Char`. This function is overridden by the
  compiler and is O(n) in the length of the list. -/
  data : List Char
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

### `Bool` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Bool` is the type of boolean values, `true` and `false`. Classically,
this is equivalent to `Prop` (the type of propositions), but the distinction
is important for programming, because values of type `Prop` are erased in the
code generator, while `Bool` corresponds to the type called `bool` or `boolean`
in most programming languages.
-/
inductive Bool : Type where
  /-- The boolean value `false`, not to be confused with the proposition `False`. -/
  | false : Bool
  /-- The boolean value `true`, not to be confused with the proposition `True`. -/
  | true : Bool

export Bool (false true)

/--
`Subtype p`, usually written as `{x : α // p x}`, is a type which
represents all the elements `x : α` for which `p x` is true. It is structurally
a pair-like type, so if you have `x : α` and `h : p x` then
`⟨x, h⟩ : {x // p x}`. An element `s : {x // p x}` will coerce to `α` but
you can also make it explicit using `s.1` or `s.val`.
-/
```
