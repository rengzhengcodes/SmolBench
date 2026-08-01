## Current goal
```
⊢ s ∈ ⊤ ↔ s = univ
```

## Full tactic state
```
α : Type u
β : Type v
γ : Type w
δ : Type u_1
ι : Sort x
f g : Filter α
s✝ t s : Set α
⊢ s ∈ ⊤ ↔ s = univ
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Filter.mem_top` in `Mathlib/Order/Filter/Basic.lean`

## Premises used in the next tactic
- `Filter.mem_top_iff_forall`
- `Set.eq_univ_iff_forall`

## Premise signatures
### `Filter.mem_top_iff_forall` (commanddeclaration)
```lean
theorem mem_top_iff_forall {s : Set α} : s ∈ (⊤ : Filter α) ↔ ∀ x, x ∈ s
```

### `Set.eq_univ_iff_forall` (commanddeclaration)
```lean
theorem eq_univ_iff_forall {s : Set α} : s = univ ↔ ∀ x, x ∈ s
```

## Premise full source (with proof)
### `Filter.mem_top_iff_forall` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
theorem mem_top_iff_forall {s : Set α} : s ∈ (⊤ : Filter α) ↔ ∀ x, x ∈ s :=
  Iff.rfl
```

### `Set.eq_univ_iff_forall` (commanddeclaration) at `Mathlib/Data/Set/Basic.lean`
```lean
theorem eq_univ_iff_forall {s : Set α} : s = univ ↔ ∀ x, x ∈ s :=
  univ_subset_iff.symm.trans <| forall_congr' fun _ => imp_iff_right trivial
```

## Transitive premise context (1-hop, 4/4 premises, ≈493 tokens)
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

### `Iff.rfl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
protected theorem Iff.rfl {a : Prop} : a ↔ a :=
  Iff.refl a

macro_rules | `(tactic| rfl) => `(tactic| exact Iff.rfl)
```

### `forall_congr'` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
theorem forall_congr' (h : ∀ a, p a ↔ q a) : (∀ a, p a) ↔ ∀ a, q a :=
  ⟨fun H a => (h a).1 (H a), fun H a => (h a).2 (H a)⟩
```

### `imp_iff_right` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem imp_iff_right {a : Prop} (ha : a) : (a → b) ↔ b := Iff.intro (· ha) (fun a _ => a)

-- This is not marked `@[simp]` because we have `implies_true : (α → True) = True`
```
