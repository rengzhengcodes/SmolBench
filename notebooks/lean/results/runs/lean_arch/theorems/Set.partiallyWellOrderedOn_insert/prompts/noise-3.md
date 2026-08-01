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

## Filler (hint:2 → hint:3 token-match, ≈326 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
