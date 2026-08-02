## Current goal
```
⊢ IsPWO (insert a s) ↔ IsPWO s
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
inst✝¹ : Preorder α
inst✝ : Preorder β
s t : Set α
a : α
⊢ IsPWO (insert a s) ↔ IsPWO s
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Set.isPWO_insert` in `Mathlib/Order/WellFoundedSet.lean`

## Premises used in the next tactic
- `Set.singleton_union`
- `Set.isPWO_union`
- `Set.isPWO_singleton`
- `true_and_iff`

## Premise signatures
### `Set.singleton_union` (commanddeclaration)
```lean
@[simp]
theorem singleton_union : {a} ∪ s = insert a s
```

### `Set.isPWO_union` (commanddeclaration)
```lean
@[simp]
theorem isPWO_union : IsPWO (s ∪ t) ↔ IsPWO s ∧ IsPWO t
```

### `Set.isPWO_singleton` (commanddeclaration)
```lean
@[simp] theorem isPWO_singleton (a : α) : IsPWO ({a} : Set α)
```

### `true_and_iff` (commanddeclaration)
```lean
theorem true_and_iff : True ∧ p ↔ p
```

## Premise full source (with proof)
### `Set.singleton_union` (commanddeclaration) at `Mathlib/Data/Set/Basic.lean`
```lean
@[simp]
theorem singleton_union : {a} ∪ s = insert a s :=
  rfl
```

### `Set.isPWO_union` (commanddeclaration) at `Mathlib/Order/WellFoundedSet.lean`
```lean
@[simp]
theorem isPWO_union : IsPWO (s ∪ t) ↔ IsPWO s ∧ IsPWO t :=
  partiallyWellOrderedOn_union
```

### `Set.isPWO_singleton` (commanddeclaration) at `Mathlib/Order/WellFoundedSet.lean`
```lean
@[simp] theorem isPWO_singleton (a : α) : IsPWO ({a} : Set α) := (finite_singleton a).isPWO
```

### `true_and_iff` (commanddeclaration) at `Mathlib/Init/Logic.lean`
```lean
theorem true_and_iff : True ∧ p ↔ p := iff_of_eq (true_and _)
```

## Transitive premise context (1-hop, 5/5 premises, ≈378 tokens)
### `Set.IsPWO` (commanddeclaration) at `Mathlib/Order/WellFoundedSet.lean`
```lean
/-- A subset of a preorder is partially well-ordered when any infinite sequence contains
  a monotone subsequence of length 2 (or equivalently, an infinite monotone subsequence). -/
def IsPWO (s : Set α) : Prop :=
  PartiallyWellOrderedOn s (· ≤ ·)
```

### `Set.partiallyWellOrderedOn_union` (commanddeclaration) at `Mathlib/Order/WellFoundedSet.lean`
```lean
@[simp]
theorem partiallyWellOrderedOn_union :
    (s ∪ t).PartiallyWellOrderedOn r ↔ s.PartiallyWellOrderedOn r ∧ t.PartiallyWellOrderedOn r :=
  ⟨fun h => ⟨h.mono <| subset_union_left _ _, h.mono <| subset_union_right _ _⟩, fun h =>
    h.1.union h.2⟩
```

### `Set.finite_singleton` (commanddeclaration) at `Mathlib/Data/Set/Finite.lean`
```lean
@[simp]
theorem finite_singleton (a : α) : ({a} : Set α).Finite :=
  toFinite _
```

### `iff_of_eq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem iff_of_eq : a = b → (a ↔ b) := Iff.of_eq
```

### `true_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem true_and (p : Prop) : (True ∧ p) = p := propext ⟨(·.2), (⟨trivial, ·⟩)⟩
```
