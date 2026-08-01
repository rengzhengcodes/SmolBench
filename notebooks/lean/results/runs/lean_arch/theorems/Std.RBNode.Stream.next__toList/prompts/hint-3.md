## Current goal
```
⊢ Option.map
      (fun x =>
        match x with
        | (a, b) => (a, toList b))
      (next? s) =
    List.next? (toList s)
```

## Full tactic state
```
α : Type u_1
s : RBNode.Stream α
⊢ Option.map
      (fun x =>
        match x with
        | (a, b) => (a, toList b))
      (next? s) =
    List.next? (toList s)
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Std.RBNode.Stream.next?_toList` in `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`

## Premises used in the next tactic
- `Std.RBNode.Stream.next?`
- `Std.RBNode.toStream_toList'`

## Premise signatures
### `Std.RBNode.Stream.next?` (commanddeclaration)
```lean
def next? : RBNode.Stream α → Option (α × RBNode.Stream α)
  | nil => none
  | cons v r tail => some (v, toStream r tail)
```

### `Std.RBNode.toStream_toList'` (commanddeclaration)
```lean
theorem toStream_toList' {t : RBNode α} {s} : (t.toStream s).toList = t.toList ++ s.toList
```

## Premise full source (with proof)
### `Std.RBNode.Stream.next?` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Basic.lean`
```lean
/-- `O(1)` amortized, `O(log n)` worst case: Get the next element from the stream. -/
def next? : RBNode.Stream α → Option (α × RBNode.Stream α)
  | nil => none
  | cons v r tail => some (v, toStream r tail)

/-- Fold a function on the values from left to right (in increasing order). -/
```

### `Std.RBNode.toStream_toList'` (commanddeclaration) at `.lake/packages/std/Std/Data/RBMap/Lemmas.lean`
```lean
theorem toStream_toList' {t : RBNode α} {s} : (t.toStream s).toList = t.toList ++ s.toList := by
  induction t generalizing s <;> simp [*, toStream]
```

## Transitive premise context (1-hop, 3/3 premises, ≈513 tokens)
### `Lean.Xml.Parser.element` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Data/Xml/Parser.lean`
```lean
  /-- https://www.w3.org/TR/xml/#NT-element -/
  partial def element : Parsec Element := do
    let elem ← Parser.elementPrefix
    EmptyElemTag elem <|> STag elem <*> content <* ETag
```

### `Option` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Prelude.lean`
```lean
/--
`Option α` is the type of values which are either `some a` for some `a : α`,
or `none`. In functional programming languages, this type is used to represent
the possibility of failure, or sometimes nullability.

For example, the function `HashMap.find? : HashMap α β → α → Option β` looks up
a specified key `a : α` inside the map. Because we do not know in advance
whether the key is actually in the map, the return type is `Option β`, where
`none` means the value was not in the map, and `some b` means that the value
was found and `b` is the value retrieved.

To extract a value from an `Option α`, we use pattern matching:
```
def map (f : α → β) (x : Option α) : Option β :=
  match x with
  | some a => some (f a)
  | none => none
```
We can also use `if let` to pattern match on `Option` and get the value
in the branch:
```
def map (f : α → β) (x : Option α) : Option β :=
  if let some a := x then
    some (f a)
  else
    none
```
-/
inductive Option (α : Type u) where
  /-- No value. -/
  | none : Option α
  /-- Some value of type `α`. -/
  | some (val : α) : Option α
```

### `Module.Free.function` (commanddeclaration) at `Mathlib/LinearAlgebra/FreeModule/Basic.lean`
```lean
/-- The product of finitely many free modules is free (non-dependent version to help with typeclass
search). -/
instance function [Finite ι] : Module.Free R (ι → M) :=
  Free.pi _ _
```
