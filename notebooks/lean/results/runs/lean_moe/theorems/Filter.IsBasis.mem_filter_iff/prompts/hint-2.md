## Current goal
```
⊢ U ∈ IsBasis.filter h ↔ ∃ i, p i ∧ s i ⊆ U
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
ι' : Sort u_5
p : ι → Prop
s : ι → Set α
h : IsBasis p s
U : Set α
⊢ U ∈ IsBasis.filter h ↔ ∃ i, p i ∧ s i ⊆ U
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Filter.IsBasis.mem_filter_iff` in `Mathlib/Order/Filter/Bases.lean`

## Premises used in the next tactic
- `Filter.IsBasis.filter`
- `FilterBasis.mem_filter_iff`
- `Filter.IsBasis.mem_filterBasis_iff`
- `exists_exists_and_eq_and`

## Premise signatures
### `Filter.IsBasis.filter` (commanddeclaration)
```lean
protected def filter (h : IsBasis p s) : Filter α
```

### `FilterBasis.mem_filter_iff` (commanddeclaration)
```lean
theorem mem_filter_iff (B : FilterBasis α) {U : Set α} : U ∈ B.filter ↔ ∃ s ∈ B, s ⊆ U
```

### `Filter.IsBasis.mem_filterBasis_iff` (commanddeclaration)
```lean
theorem mem_filterBasis_iff {U : Set α} : U ∈ h.filterBasis ↔ ∃ i, p i ∧ s i = U
```

### `exists_exists_and_eq_and` (commanddeclaration)
```lean
@[simp] theorem exists_exists_and_eq_and {f : α → β} {p : α → Prop} {q : β → Prop} :
    (∃ b, (∃ a, p a ∧ f a = b) ∧ q b) ↔ ∃ a, p a ∧ q (f a)
```

## Premise full source (with proof)
### `Filter.IsBasis.filter` (commanddeclaration) at `Mathlib/Order/Filter/Bases.lean`
```lean
/-- Constructs a filter from an indexed family of sets satisfying `IsBasis`. -/
protected def filter (h : IsBasis p s) : Filter α :=
  h.filterBasis.filter
```

### `FilterBasis.mem_filter_iff` (commanddeclaration) at `Mathlib/Order/Filter/Bases.lean`
```lean
theorem mem_filter_iff (B : FilterBasis α) {U : Set α} : U ∈ B.filter ↔ ∃ s ∈ B, s ⊆ U :=
  Iff.rfl
```

### `Filter.IsBasis.mem_filterBasis_iff` (commanddeclaration) at `Mathlib/Order/Filter/Bases.lean`
```lean
theorem mem_filterBasis_iff {U : Set α} : U ∈ h.filterBasis ↔ ∃ i, p i ∧ s i = U :=
  Iff.rfl
```

### `exists_exists_and_eq_and` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
@[simp] theorem exists_exists_and_eq_and {f : α → β} {p : α → Prop} {q : β → Prop} :
    (∃ b, (∃ a, p a ∧ f a = b) ∧ q b) ↔ ∃ a, p a ∧ q (f a) :=
  ⟨fun ⟨_, ⟨a, ha, hab⟩, hb⟩ ↦ ⟨a, ha, hab.symm ▸ hb⟩, fun ⟨a, hp, hq⟩ ↦ ⟨f a, ⟨a, hp, rfl⟩, hq⟩⟩
```
