## Current goal
```
⊢ List.eraseP (fun x => a == x) l₁ <+ List.eraseP (fun x => a == x) l₂
```

## Full tactic state
```
α : Type u_1
inst✝¹ : BEq α
inst✝ : LawfulBEq α
a : α
l₁ l₂ : List α
h : l₁ <+ l₂
⊢ List.eraseP (fun x => a == x) l₁ <+ List.eraseP (fun x => a == x) l₂
```

## Proof so far (1 tactic)
```lean
simp [erase_eq_eraseP]
```

## Theorem
`List.Sublist.erase` in `.lake/packages/std/Std/Data/List/Lemmas.lean`

## Premises used in the next tactic
- `List.Sublist.eraseP`

## Premise signatures
### `List.Sublist.eraseP` (commanddeclaration)
```lean
theorem Sublist.eraseP : l₁ <+ l₂ → l₁.eraseP p <+ l₂.eraseP p
```

## Premise full source (with proof)
### `List.Sublist.eraseP` (commanddeclaration) at `.lake/packages/std/Std/Data/List/Lemmas.lean`
```lean
theorem Sublist.eraseP : l₁ <+ l₂ → l₁.eraseP p <+ l₂.eraseP p
  | .slnil => Sublist.refl _
  | .cons a s => by
    by_cases h : p a <;> simp [h]
    exacts [s.eraseP.trans (eraseP_sublist _), s.eraseP.cons _]
  | .cons₂ a s => by
    by_cases h : p a <;> simp [h]
    exacts [s, s.eraseP.cons₂ _]
```

## Filler (hint:2 → hint:3 token-match, ≈208 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
