## Current goal
```
⊢ IsUpperSet s ↔ ∀ ⦃a : α⦄, a ∈ s → Ioi a ⊆ s
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
κ : ι → Sort u_5
inst✝ : PartialOrder α
s : Set α
⊢ IsUpperSet s ↔ ∀ ⦃a : α⦄, a ∈ s → Ioi a ⊆ s
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`isUpperSet_iff_Ioi_subset` in `Mathlib/Order/UpperLower/Basic.lean`

## Premises used in the next tactic
- `isUpperSet_iff_forall_lt`
- `Set.subset_def`
- `forall_swap`

## Premise signatures
### `isUpperSet_iff_forall_lt` (commanddeclaration)
```lean
theorem isUpperSet_iff_forall_lt : IsUpperSet s ↔ ∀ ⦃a b : α⦄, a < b → a ∈ s → b ∈ s
```

### `Set.subset_def` (commanddeclaration)
```lean
theorem subset_def : (s ⊆ t) = ∀ x, x ∈ s → x ∈ t
```

### `forall_swap` (commanddeclaration)
```lean
theorem forall_swap {p : α → β → Prop} : (∀ x y, p x y) ↔ ∀ y x, p x y
```

## Premise full source (with proof)
### `isUpperSet_iff_forall_lt` (commanddeclaration) at `Mathlib/Order/UpperLower/Basic.lean`
```lean
theorem isUpperSet_iff_forall_lt : IsUpperSet s ↔ ∀ ⦃a b : α⦄, a < b → a ∈ s → b ∈ s :=
  forall_congr' fun a => by simp [le_iff_eq_or_lt, or_imp, forall_and]
```

### `Set.subset_def` (commanddeclaration) at `Mathlib/Data/Set/Basic.lean`
```lean
theorem subset_def : (s ⊆ t) = ∀ x, x ∈ s → x ∈ t :=
  rfl
```

### `forall_swap` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
theorem forall_swap {p : α → β → Prop} : (∀ x y, p x y) ↔ ∀ y x, p x y := ⟨swap, swap⟩
```

## Transitive premise context (1-hop, 5/5 premises, ≈482 tokens)
### `IsUpperSet` (commanddeclaration) at `Mathlib/Order/UpperLower/Basic.lean`
```lean
/-- An upper set in an order `α` is a set such that any element greater than one of its members is
also a member. Also called up-set, upward-closed set. -/
@[aesop norm unfold]
def IsUpperSet (s : Set α) : Prop :=
  ∀ ⦃a b : α⦄, a ≤ b → a ∈ s → b ∈ s
```

### `forall_congr'` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
theorem forall_congr' (h : ∀ a, p a ↔ q a) : (∀ a, p a) ↔ ∀ a, q a :=
  ⟨fun H a => (h a).1 (H a), fun H a => (h a).2 (H a)⟩
```

### `le_iff_eq_or_lt` (commanddeclaration) at `Mathlib/Order/Basic.lean`
```lean
theorem le_iff_eq_or_lt [PartialOrder α] {a b : α} : a ≤ b ↔ a = b ∨ a < b :=
  le_iff_lt_or_eq.trans or_comm
```

### `or_imp` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
theorem or_imp : (a ∨ b → c) ↔ (a → c) ∧ (b → c) :=
  Iff.intro (fun h => ⟨h ∘ .inl, h ∘ .inr⟩) (fun ⟨ha, hb⟩ => Or.rec ha hb)
```

### `forall_and` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
theorem forall_and : (∀ x, p x ∧ q x) ↔ (∀ x, p x) ∧ (∀ x, q x) :=
  ⟨fun h => ⟨fun x => (h x).1, fun x => (h x).2⟩, fun ⟨h₁, h₂⟩ x => ⟨h₁ x, h₂ x⟩⟩
```
