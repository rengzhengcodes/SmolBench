## Current goal
```
⊢ a ⩿ b ↔ a ⋖ b ∨ a = b
```

## Full tactic state
```
α : Type u_1
β : Type u_2
inst✝ : PartialOrder α
a b c : α
⊢ a ⩿ b ↔ a ⋖ b ∨ a = b
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`wcovBy_iff_covBy_or_eq` in `Mathlib/Order/Cover.lean`

## Premises used in the next tactic
- `le_antisymm_iff`
- `wcovBy_iff_covBy_or_le_and_le`

## Premise signatures
### `le_antisymm_iff` (commanddeclaration)
```lean
theorem le_antisymm_iff {a b : α} : a = b ↔ a ≤ b ∧ b ≤ a
```

### `wcovBy_iff_covBy_or_le_and_le` (commanddeclaration)
```lean
theorem wcovBy_iff_covBy_or_le_and_le : a ⩿ b ↔ a ⋖ b ∨ a ≤ b ∧ b ≤ a
```

## Premise full source (with proof)
### `le_antisymm_iff` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
theorem le_antisymm_iff {a b : α} : a = b ↔ a ≤ b ∧ b ≤ a :=
  ⟨fun e => ⟨le_of_eq e, le_of_eq e.symm⟩, fun ⟨h1, h2⟩ => le_antisymm h1 h2⟩
```

### `wcovBy_iff_covBy_or_le_and_le` (commanddeclaration) at `Mathlib/Order/Cover.lean`
```lean
theorem wcovBy_iff_covBy_or_le_and_le : a ⩿ b ↔ a ⋖ b ∨ a ≤ b ∧ b ≤ a :=
  ⟨fun h => or_iff_not_imp_right.mpr fun h' => h.covBy_of_not_le fun hba => h' ⟨h.le, hba⟩,
    fun h' => h'.elim (fun h => h.wcovBy) fun h => h.1.wcovBy_of_le h.2⟩
```

## Filler (hint:2 → hint:3 token-match, ≈140 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat
