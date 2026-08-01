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
