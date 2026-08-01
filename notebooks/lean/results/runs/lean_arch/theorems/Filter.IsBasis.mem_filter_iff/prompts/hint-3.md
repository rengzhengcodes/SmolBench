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

## Transitive premise context (1-hop, 4/4 premises, ≈799 tokens)
### `Lean.Parser.indexed` (commanddeclaration) at `.lake/packages/lean4/src/lean/Lean/Parser/Basic.lean`
```lean
def indexed {α : Type} (map : TokenMap α) (c : ParserContext) (s : ParserState) (behavior : LeadingIdentBehavior) : ParserState × List α :=
  let (s, stx) := peekToken c s
  let find (n : Name) : ParserState × List α :=
    match map.find? n with
    | some as => (s, as)
    | _       => (s, [])
  match stx with
  | .ok (.atom _ sym)      => find (.mkSimple sym)
  | .ok (.ident _ _ val _) =>
    match behavior with
    | .default => find identKind
    | .symbol =>
      match map.find? val with
      | some as => (s, as)
      | none    => find identKind
    | .both =>
      match map.find? val with
      | some as =>
        if val == identKind then
          (s, as)  -- avoid running the same parsers twice
        else
          match map.find? identKind with
          | some as' => (s, as ++ as')
          | _        => (s, as)
      | none    => find identKind
  | .ok (.node _ k _) => find k
  | .ok _             => (s, [])
  | .error s'         => (s', [])
```

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

### `FilterBasis` (commanddeclaration) at `Mathlib/Order/Filter/Bases.lean`
```lean
/-- A filter basis `B` on a type `α` is a nonempty collection of sets of `α`
such that the intersection of two elements of this collection contains some element
of the collection. -/
structure FilterBasis (α : Type*) where
  /-- Sets of a filter basis. -/
  sets : Set (Set α)
  /-- The set of filter basis sets is nonempty. -/
  nonempty : sets.Nonempty
  /-- The set of filter basis sets is directed downwards. -/
  inter_sets {x y} : x ∈ sets → y ∈ sets → ∃ z ∈ sets, z ⊆ x ∩ y
```

### `Iff.rfl` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
protected theorem Iff.rfl {a : Prop} : a ↔ a :=
  Iff.refl a

macro_rules | `(tactic| rfl) => `(tactic| exact Iff.rfl)
```
