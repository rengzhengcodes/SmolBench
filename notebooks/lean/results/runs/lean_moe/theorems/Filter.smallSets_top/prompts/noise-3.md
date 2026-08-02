## Current goal
```
⊢ smallSets ⊤ = ⊤
```

## Full tactic state
```
α : Type u_1
β : Type u_2
ι : Sort u_3
l l' la : Filter α
lb : Filter β
⊢ smallSets ⊤ = ⊤
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Filter.smallSets_top` in `Mathlib/Order/Filter/SmallSets.lean`

## Premises used in the next tactic
- `Filter.smallSets`
- `Filter.lift'_top`
- `Set.powerset_univ`
- `Filter.principal_univ`

## Premise signatures
### `Filter.smallSets` (commanddeclaration)
```lean
def smallSets (l : Filter α) : Filter (Set α)
```

### `Filter.lift'_top` (commanddeclaration)
```lean
@[simp]
theorem lift'_top (h : Set α → Set β) : (⊤ : Filter α).lift' h = 𝓟 (h univ)
```

### `Set.powerset_univ` (commanddeclaration)
```lean
@[simp]
theorem powerset_univ : 𝒫(univ : Set α) = univ
```

### `Filter.principal_univ` (commanddeclaration)
```lean
@[simp] theorem principal_univ : 𝓟 (univ : Set α) = ⊤
```

## Premise full source (with proof)
### `Filter.smallSets` (commanddeclaration) at `Mathlib/Order/Filter/SmallSets.lean`
```lean
/-- The filter `l.smallSets` is the largest filter containing all powersets of members of `l`. -/
def smallSets (l : Filter α) : Filter (Set α) :=
  l.lift' powerset
```

### `Filter.lift'_top` (commanddeclaration) at `Mathlib/Order/Filter/Lift.lean`
```lean
@[simp]
theorem lift'_top (h : Set α → Set β) : (⊤ : Filter α).lift' h = 𝓟 (h univ) :=
  lift_top _
```

### `Set.powerset_univ` (commanddeclaration) at `Mathlib/Data/Set/Basic.lean`
```lean
@[simp]
theorem powerset_univ : 𝒫(univ : Set α) = univ :=
  eq_univ_of_forall subset_univ
```

### `Filter.principal_univ` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
@[simp] theorem principal_univ : 𝓟 (univ : Set α) = ⊤ :=
  top_unique <| by simp only [le_principal_iff, mem_top, eq_self_iff_true]
```

## Filler (hint:2 → hint:3 token-match, ≈440 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate
