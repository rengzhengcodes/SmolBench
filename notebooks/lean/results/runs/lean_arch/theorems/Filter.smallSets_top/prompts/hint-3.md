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

## Transitive premise context (1-hop, 4/4 premises, ≈416 tokens)
### `Filter` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
/-- A filter `F` on a type `α` is a collection of sets of `α` which contains the whole `α`,
is upwards-closed, and is stable under intersection. We do not forbid this collection to be
all sets of `α`. -/
structure Filter (α : Type*) where
  /-- The set of sets that belong to the filter. -/
  sets : Set (Set α)
  /-- The set `Set.univ` belongs to any filter. -/
  univ_sets : Set.univ ∈ sets
  /-- If a set belongs to a filter, then its superset belongs to the filter as well. -/
  sets_of_superset {x y} : x ∈ sets → x ⊆ y → y ∈ sets
  /-- If two sets belong to a filter, then their intersection belongs to the filter as well. -/
  inter_sets {x y} : x ∈ sets → y ∈ sets → x ∩ y ∈ sets
```

### `top_unique` (commanddeclaration) at `Mathlib/Order/BoundedOrder.lean`
```lean
theorem top_unique (h : ⊤ ≤ a) : a = ⊤ :=
  le_top.antisymm h
```

### `Filter.le_principal_iff` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
@[simp]
theorem le_principal_iff {s : Set α} {f : Filter α} : f ≤ 𝓟 s ↔ s ∈ f :=
  ⟨fun h => h Subset.rfl, fun hs _ ht => mem_of_superset hs ht⟩
```

### `eq_self_iff_true` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem eq_self_iff_true (a : α)  : a = a ↔ True  := iff_true_intro rfl
```
