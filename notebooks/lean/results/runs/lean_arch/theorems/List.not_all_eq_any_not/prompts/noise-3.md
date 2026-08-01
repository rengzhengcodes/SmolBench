## Current goal
```
⊢ (!(p head✝ && all tail✝ p)) = (!p head✝ || any tail✝ fun a => !p a)
```

## Full tactic state
```
case cons
α : Type u_1
p : α → Bool
head✝ : α
tail✝ : List α
ih : (!all tail✝ p) = any tail✝ fun a => !p a
⊢ (!(p head✝ && all tail✝ p)) = (!p head✝ || any tail✝ fun a => !p a)
```

## Proof so far (1 tactic)
```lean
induction l with simp | cons _ _ ih => rw [Bool.not_and, ih]
```

## Theorem
`List.not_all_eq_any_not` in `.lake/packages/std/Std/Data/List/Lemmas.lean`

## Premises used in the next tactic
- `Bool.not_and`

## Premise signatures
### `Bool.not_and` (commanddeclaration)
```lean
theorem not_and : ∀ (x y : Bool), (!(x && y)) = (!x || !y)
```

## Premise full source (with proof)
### `Bool.not_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Data/Bool.lean`
```lean
/-- De Morgan's law for boolean and -/
theorem not_and : ∀ (x y : Bool), (!(x && y)) = (!x || !y) := by decide
```

## Filler (hint:2 → hint:3 token-match, ≈378 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit
