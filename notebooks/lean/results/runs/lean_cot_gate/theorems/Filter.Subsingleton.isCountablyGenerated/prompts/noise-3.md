## Current goal
```
⊢ IsCountablyGenerated (pure x)
```

## Full tactic state
```
case inr.intro
α : Type u_1
β : Type u_2
x : α
hl : Filter.Subsingleton (pure x)
⊢ IsCountablyGenerated (pure x)
```

## Proof so far (2 tactics)
```lean
rcases subsingleton_iff_bot_or_pure.1 hl with rfl|⟨x, rfl⟩
exact isCountablyGenerated_bot
```

## Theorem
`Filter.Subsingleton.isCountablyGenerated` in `Mathlib/Order/Filter/Subsingleton.lean`

## Premises used in the next tactic
- `Filter.isCountablyGenerated_pure`

## Premise signatures
### `Filter.isCountablyGenerated_pure` (commanddeclaration)
```lean
@[instance]
theorem isCountablyGenerated_pure (a : α) : IsCountablyGenerated (pure a)
```

## Premise full source (with proof)
### `Filter.isCountablyGenerated_pure` (commanddeclaration) at `Mathlib/Order/Filter/Bases.lean`
```lean
@[instance]
theorem isCountablyGenerated_pure (a : α) : IsCountablyGenerated (pure a) := by
  rw [← principal_singleton]
  exact isCountablyGenerated_principal _
```

## Filler (hint:2 → hint:3 token-match, ≈274 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
