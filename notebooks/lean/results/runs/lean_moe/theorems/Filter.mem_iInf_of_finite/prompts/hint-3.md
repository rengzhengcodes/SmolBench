## Current goal
```
⊢ ⋂ i, t i ∈ ⨅ i, f i
```

## Full tactic state
```
case intro.intro
α✝ : Type u
β : Type v
γ : Type w
δ : Type u_1
ι✝ : Sort x
f✝ g : Filter α✝
s t✝ : Set α✝
ι : Type u_2
inst✝ : Finite ι
α : Type u_3
f : ι → Filter α
t : ι → Set α
ht : ∀ (i : ι), t i ∈ f i
⊢ ⋂ i, t i ∈ ⨅ i, f i
```

## Proof so far (2 tactics)
```lean
refine' ⟨exists_iInter_of_mem_iInf, _⟩
rintro ⟨t, ht, rfl⟩
```

## Theorem
`Filter.mem_iInf_of_finite` in `Mathlib/Order/Filter/Basic.lean`

## Premises used in the next tactic
- `Filter.iInter_mem`
- `Filter.mem_iInf_of_mem`

## Premise signatures
### `Filter.iInter_mem` (commanddeclaration)
```lean
@[simp]
theorem iInter_mem {β : Sort v} {s : β → Set α} [Finite β] : (⋂ i, s i) ∈ f ↔ ∀ i, s i ∈ f
```

### `Filter.mem_iInf_of_mem` (commanddeclaration)
```lean
theorem mem_iInf_of_mem {f : ι → Filter α} (i : ι) {s} (hs : s ∈ f i) : s ∈ ⨅ i, f i
```

## Premise full source (with proof)
### `Filter.iInter_mem` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
@[simp]
theorem iInter_mem {β : Sort v} {s : β → Set α} [Finite β] : (⋂ i, s i) ∈ f ↔ ∀ i, s i ∈ f :=
  (sInter_mem (finite_range _)).trans forall_mem_range
```

### `Filter.mem_iInf_of_mem` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
theorem mem_iInf_of_mem {f : ι → Filter α} (i : ι) {s} (hs : s ∈ f i) : s ∈ ⨅ i, f i :=
  iInf_le f i hs
```

## Transitive premise context (1-hop, 5/5 premises, ≈887 tokens)
### `Finite` (commanddeclaration) at `Mathlib/Data/Finite/Defs.lean`
```lean
/-- A type is `Finite` if it is in bijective correspondence to some `Fin n`.

This is similar to `Fintype`, but `Finite` is a proposition rather than data.
A particular benefit to this is that `Finite` instances are definitionally equal to one another
(due to proof irrelevance) rather than being merely propositionally equal,
and, furthermore, `Finite` instances generally avoid the need for `Decidable` instances.
One other notable difference is that `Finite` allows there to be `Finite p` instances
for all `p : Prop`, which is not allowed by `Fintype` due to universe constraints.
An application of this is that `Finite (x ∈ s → β x)` follows from the general instance for pi
types, assuming `[∀ x, Finite (β x)]`.
Implementation note: this is a reason `Finite α` is not defined as `Nonempty (Fintype α)`.

Every `Fintype` instance provides a `Finite` instance via `Finite.of_fintype`.
Conversely, one can noncomputably create a `Fintype` instance from a `Finite` instance
via `Fintype.ofFinite`. In a proof one might write
```lean
  have := Fintype.ofFinite α
```
to obtain such an instance.

Do not write noncomputable `Fintype` instances; instead write `Finite` instances
and use this `Fintype.ofFinite` interface.
The `Fintype` instances should be relied upon to be computable for evaluation purposes.

Theorems should use `Finite` instead of `Fintype`, unless definitions in the theorem statement
require `Fintype`.
Definitions should prefer `Finite` as well, unless it is important that the definitions
are meant to be computable in the reduction or `#eval` sense.
-/
class inductive Finite (α : Sort*) : Prop
  | intro {n : ℕ} : α ≃ Fin n → Finite _
```

### `Filter.sInter_mem` (commanddeclaration) at `Mathlib/Order/Filter/Basic.lean`
```lean
@[simp]
theorem sInter_mem {s : Set (Set α)} (hfin : s.Finite) : ⋂₀ s ∈ f ↔ ∀ U ∈ s, U ∈ f := by
  rw [sInter_eq_biInter, biInter_mem hfin]
```

### `trans` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem trans [IsTrans α r] {a b c : α} : a ≺ b → b ≺ c → a ≺ c :=
  IsTrans.trans _ _ _
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

### `iInf_le` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
theorem iInf_le (f : ι → α) (i : ι) : iInf f ≤ f i :=
  sInf_le ⟨i, rfl⟩
```
