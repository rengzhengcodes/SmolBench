## Current goal
```
⊢ a ⇔ b = ⊥
```

## Full tactic state
```
ι : Type u_1
α : Type u_2
β : Type u_3
π : ι → Type u_4
inst✝ : HeytingAlgebra α
a✝ a b : α
h : IsCompl a b
⊢ a ⇔ b = ⊥
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`IsCompl.bihimp_eq_bot` in `Mathlib/Order/SymmDiff.lean`

## Premises used in the next tactic
- `compl_bihimp_self`

## Premise signatures
### `compl_bihimp_self` (commanddeclaration)
```lean
@[simp]
theorem compl_bihimp_self : aᶜ ⇔ a = ⊥
```

## Premise full source (with proof)
### `compl_bihimp_self` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
@[simp]
theorem compl_bihimp_self : aᶜ ⇔ a = ⊥ :=
  @hnot_symmDiff_self αᵒᵈ _ _
```

## Transitive premise context (1-hop, 1/1 premises, ≈89 tokens)
### `hnot_symmDiff_self` (commanddeclaration) at `Mathlib/Order/SymmDiff.lean`
```lean
@[simp]
theorem hnot_symmDiff_self : (￢a) ∆ a = ⊤ := by
  rw [eq_top_iff, symmDiff, hnot_sdiff, sup_sdiff_self]
  exact Codisjoint.top_le codisjoint_hnot_left
```
