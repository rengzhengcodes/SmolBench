## Current goal
```
⊢ a ∈ ⨅ i, ⨅ j, f i j ↔ ∃ i j, a ∈ f i j
```

## Full tactic state
```
α : Type u_1
β : Type u_2
γ : Type u_3
ι : Sort u_4
κ : ι → Sort u_5
inst✝ : LE α
S : Set (UpperSet α)
s t : UpperSet α
a : α
f : (i : ι) → κ i → UpperSet α
⊢ a ∈ ⨅ i, ⨅ j, f i j ↔ ∃ i j, a ∈ f i j
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`UpperSet.mem_iInf₂_iff` in `Mathlib/Order/UpperLower/Basic.lean`

## Premises used in the next tactic
- `UpperSet.mem_iInf_iff`

## Premise signatures
### `UpperSet.mem_iInf_iff` (commanddeclaration)
```lean
@[simp]
theorem mem_iInf_iff {f : ι → UpperSet α} : (a ∈ ⨅ i, f i) ↔ ∃ i, a ∈ f i
```

## Premise full source (with proof)
### `UpperSet.mem_iInf_iff` (commanddeclaration) at `Mathlib/Order/UpperLower/Basic.lean`
```lean
@[simp]
theorem mem_iInf_iff {f : ι → UpperSet α} : (a ∈ ⨅ i, f i) ↔ ∃ i, a ∈ f i := by
  rw [← SetLike.mem_coe, coe_iInf]
  exact mem_iUnion
```

## Transitive premise context (1-hop, 2/2 premises, ≈156 tokens)
### `UpperSet` (commanddeclaration) at `Mathlib/Order/UpperLower/Basic.lean`
```lean
/-- The type of upper sets of an order. -/
structure UpperSet (α : Type*) [LE α] where
  /-- The carrier of an `UpperSet`. -/
  carrier : Set α
  /-- The carrier of an `UpperSet` is an upper set. -/
  upper' : IsUpperSet carrier
```

### `SetLike.mem_coe` (commanddeclaration) at `Mathlib/Data/SetLike/Basic.lean`
```lean
@[simp]
theorem mem_coe {x : B} : x ∈ (p : Set B) ↔ x ∈ p :=
  Iff.rfl
```
