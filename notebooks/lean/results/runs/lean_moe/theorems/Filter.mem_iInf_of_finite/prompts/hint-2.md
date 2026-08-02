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
