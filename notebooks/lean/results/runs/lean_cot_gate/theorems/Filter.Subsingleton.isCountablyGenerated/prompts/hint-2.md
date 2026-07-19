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
