## Current goal
```
⊢ ∀ᶠ (x : α) in l, ∀ y ≤ f x, p y
```

## Full tactic state
```
ι : Type u_1
ι' : Type u_2
α✝ : Type u_3
β✝ : Type u_4
γ : Type u_5
α : Type u_6
β : Type u_7
inst✝ : Preorder β
l : Filter α
p : β → Prop
f : α → β
hf : Tendsto f l atBot
h_evtl : ∀ᶠ (x : β) in atBot, ∀ y ≤ x, p y
⊢ ∀ᶠ (x : α) in l, ∀ y ≤ f x, p y
```

## Proof so far (1 tactic)
```lean
rw [← Filter.eventually_forall_le_atBot] at h_evtl
```

## Theorem
`Filter.Tendsto.eventually_forall_le_atBot` in `Mathlib/Order/Filter/AtTopBot.lean`

## Premises used in the next tactic
- `Filter.Eventually.filter_mono`

## Premise signatures
### `Filter.Eventually.filter_mono` (commanddeclaration)
```lean
theorem Eventually.filter_mono {f₁ f₂ : Filter α} (h : f₁ ≤ f₂) {p : α → Prop}
    (hp : ∀ᶠ x in f₂, p x) : ∀ᶠ x in f₁, p x
```

## Premise full source (with proof)
### `Filter.Eventually.filter_mono` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
theorem Eventually.filter_mono {f₁ f₂ : Filter α} (h : f₁ ≤ f₂) {p : α → Prop}
    (hp : ∀ᶠ x in f₂, p x) : ∀ᶠ x in f₁, p x :=
  h hp
```

## Transitive premise context (1-hop, 1/1 premises, ≈229 tokens)
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
