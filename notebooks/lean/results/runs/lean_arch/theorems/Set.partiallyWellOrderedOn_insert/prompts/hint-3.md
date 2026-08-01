## Current goal
```
⊢ PartiallyWellOrderedOn (insert a s) r ↔ PartiallyWellOrderedOn s r
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
π : ι → Type u_5
r : α → α → Prop
r' : β → β → Prop
f : α → β
s t : Set α
a : α
inst✝ : IsRefl α r
⊢ PartiallyWellOrderedOn (insert a s) r ↔ PartiallyWellOrderedOn s r
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Set.partiallyWellOrderedOn_insert` in `Mathlib/Order/WellFoundedSet.lean`

## Premises used in the next tactic
- `Set.singleton_union`
- `Set.partiallyWellOrderedOn_union`
- `Set.partiallyWellOrderedOn_singleton`
- `true_and_iff`

## Premise signatures
### `Set.singleton_union` (commanddeclaration)
```lean
@[simp]
theorem singleton_union : {a} ∪ s = insert a s
```

### `Set.partiallyWellOrderedOn_union` (commanddeclaration)
```lean
@[simp]
theorem partiallyWellOrderedOn_union :
    (s ∪ t).PartiallyWellOrderedOn r ↔ s.PartiallyWellOrderedOn r ∧ t.PartiallyWellOrderedOn r
```

### `Set.partiallyWellOrderedOn_singleton` (commanddeclaration)
```lean
@[simp]
theorem partiallyWellOrderedOn_singleton (a : α) : PartiallyWellOrderedOn {a} r
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

### `Set.partiallyWellOrderedOn_union` (commanddeclaration) at `Mathlib/Order/WellFoundedSet.lean`
```lean
@[simp]
theorem partiallyWellOrderedOn_union :
    (s ∪ t).PartiallyWellOrderedOn r ↔ s.PartiallyWellOrderedOn r ∧ t.PartiallyWellOrderedOn r :=
  ⟨fun h => ⟨h.mono <| subset_union_left _ _, h.mono <| subset_union_right _ _⟩, fun h =>
    h.1.union h.2⟩
```

### `Set.partiallyWellOrderedOn_singleton` (commanddeclaration) at `Mathlib/Order/WellFoundedSet.lean`
```lean
@[simp]
theorem partiallyWellOrderedOn_singleton (a : α) : PartiallyWellOrderedOn {a} r :=
  (finite_singleton a).partiallyWellOrderedOn
```

### `true_and_iff` (commanddeclaration) at `Mathlib/Init/Logic.lean`
```lean
theorem true_and_iff : True ∧ p ↔ p := iff_of_eq (true_and _)
```

## Transitive premise context (1-hop, 4/4 premises, ≈302 tokens)
### `Set.PartiallyWellOrderedOn` (commanddeclaration) at `Mathlib/Order/WellFoundedSet.lean`
```lean
/-- A subset is partially well-ordered by a relation `r` when any infinite sequence contains
  two elements where the first is related to the second by `r`. -/
def PartiallyWellOrderedOn (s : Set α) (r : α → α → Prop) : Prop :=
  ∀ f : ℕ → α, (∀ n, f n ∈ s) → ∃ m n : ℕ, m < n ∧ r (f m) (f n)
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
