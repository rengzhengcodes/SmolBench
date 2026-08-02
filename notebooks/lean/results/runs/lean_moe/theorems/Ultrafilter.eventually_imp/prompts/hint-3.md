## Current goal
```
⊢ (∀ᶠ (x : α) in ↑f, p x → q x) ↔ (∀ᶠ (x : α) in ↑f, p x) → ∀ᶠ (x : α) in ↑f, q x
```

## Full tactic state
```
α : Type u
β : Type v
γ : Type u_1
f g : Ultrafilter α
s t : Set α
p q : α → Prop
⊢ (∀ᶠ (x : α) in ↑f, p x → q x) ↔ (∀ᶠ (x : α) in ↑f, p x) → ∀ᶠ (x : α) in ↑f, q x
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Ultrafilter.eventually_imp` in `Mathlib/Order/Filter/Ultrafilter.lean`

## Premises used in the next tactic
- `imp_iff_not_or`
- `Ultrafilter.eventually_or`
- `Ultrafilter.eventually_not`

## Premise signatures
### `imp_iff_not_or` (commanddeclaration)
```lean
theorem imp_iff_not_or : a → b ↔ ¬a ∨ b
```

### `Ultrafilter.eventually_or` (commanddeclaration)
```lean
theorem eventually_or : (∀ᶠ x in f, p x ∨ q x) ↔ (∀ᶠ x in f, p x) ∨ ∀ᶠ x in f, q x
```

### `Ultrafilter.eventually_not` (commanddeclaration)
```lean
theorem eventually_not : (∀ᶠ x in f, ¬p x) ↔ ¬∀ᶠ x in f, p x
```

## Premise full source (with proof)
### `imp_iff_not_or` (commanddeclaration) at `Mathlib/Logic/Basic.lean`
```lean
theorem imp_iff_not_or : a → b ↔ ¬a ∨ b := Decidable.imp_iff_not_or
```

### `Ultrafilter.eventually_or` (commanddeclaration) at `Mathlib/Order/Filter/Ultrafilter.lean`
```lean
theorem eventually_or : (∀ᶠ x in f, p x ∨ q x) ↔ (∀ᶠ x in f, p x) ∨ ∀ᶠ x in f, q x :=
  union_mem_iff
```

### `Ultrafilter.eventually_not` (commanddeclaration) at `Mathlib/Order/Filter/Ultrafilter.lean`
```lean
theorem eventually_not : (∀ᶠ x in f, ¬p x) ↔ ¬∀ᶠ x in f, p x :=
  compl_mem_iff_not_mem
```

## Transitive premise context (1-hop, 3/3 premises, ≈220 tokens)
### `Decidable.imp_iff_not_or` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/PropLemmas.lean`
```lean
theorem Decidable.imp_iff_not_or [Decidable a] : (a → b) ↔ (¬a ∨ b) :=
  ⟨not_or_of_imp, Or.neg_resolve_left⟩
```

### `Ultrafilter.union_mem_iff` (commanddeclaration) at `Mathlib/Order/Filter/Ultrafilter.lean`
```lean
@[simp]
theorem union_mem_iff : s ∪ t ∈ f ↔ s ∈ f ∨ t ∈ f := by
  simp only [← mem_coe, ← le_principal_iff, ← sup_principal, le_sup_iff]
```

### `Ultrafilter.compl_mem_iff_not_mem` (commanddeclaration) at `Mathlib/Order/Filter/Ultrafilter.lean`
```lean
theorem compl_mem_iff_not_mem : sᶜ ∈ f ↔ s ∉ f := by rw [← compl_not_mem_iff, compl_compl]
```
