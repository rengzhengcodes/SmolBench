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

## Transitive premise context (1-hop, 3/3 premises, ≈251 tokens)
### `Filter.IsCountablyGenerated` (commanddeclaration) at `Mathlib/Order/Filter/Bases.lean`
```lean
/-- `IsCountablyGenerated f` means `f = generate s` for some countable `s`. -/
class IsCountablyGenerated (f : Filter α) : Prop where
  /-- There exists a countable set that generates the filter. -/
  out : ∃ s : Set (Set α), s.Countable ∧ f = generate s
```

### `Filter.principal_singleton` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
@[simp]
theorem principal_singleton (a : α) : 𝓟 {a} = pure a :=
  Filter.ext fun s => by simp only [mem_pure, mem_principal, singleton_subset_iff]
```

### `Filter.isCountablyGenerated_principal` (commanddeclaration) at `Mathlib/Order/Filter/Bases.lean`
```lean
@[instance]
theorem isCountablyGenerated_principal (s : Set α) : IsCountablyGenerated (𝓟 s) :=
  isCountablyGenerated_of_seq ⟨fun _ => s, iInf_const.symm⟩
```
