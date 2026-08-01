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
