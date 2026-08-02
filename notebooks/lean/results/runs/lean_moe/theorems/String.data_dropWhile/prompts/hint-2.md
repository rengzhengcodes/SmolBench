## Current goal
```
⊢ (dropWhile s p).data = List.dropWhile p s.data
```

## Full tactic state
```
p : Char → Bool
s : String
⊢ (dropWhile s p).data = List.dropWhile p s.data
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`String.data_dropWhile` in `.lake/packages/std/Std/Data/String/Lemmas.lean`

## Premises used in the next tactic
- `String.dropWhile_eq`

## Premise signatures
### `String.dropWhile_eq` (commanddeclaration)
```lean
theorem dropWhile_eq (p : Char → Bool) (s : String) : s.dropWhile p = ⟨s.1.dropWhile p⟩
```

## Premise full source (with proof)
### `String.dropWhile_eq` (commanddeclaration) at `.lake/packages/std/Std/Data/String/Lemmas.lean`
```lean
theorem dropWhile_eq (p : Char → Bool) (s : String) : s.dropWhile p = ⟨s.1.dropWhile p⟩ :=
  (s.validFor_toSubstring.dropWhile p).toString
```
