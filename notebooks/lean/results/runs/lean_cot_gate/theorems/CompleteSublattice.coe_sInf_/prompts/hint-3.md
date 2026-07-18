## Current goal
```
⊢ ↑(sInf S) = ⨅ N ∈ S, ↑N
```

## Full tactic state
```
α : Type u_1
β : Type u_2
inst✝¹ : CompleteLattice α
inst✝ : CompleteLattice β
f : CompleteLatticeHom α β
L : CompleteSublattice α
S : Set ↥L
⊢ ↑(sInf S) = ⨅ N ∈ S, ↑N
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CompleteSublattice.coe_sInf'` in `Mathlib/Order/CompleteSublattice.lean`

## Premises used in the next tactic
- `CompleteSublattice.coe_sInf`
- `Set.image`
- `sInf_image`

## Premise signatures
### `CompleteSublattice.coe_sInf` (commanddeclaration)
```lean
@[simp] theorem coe_sInf (S : Set L) : (↑(sInf S) : α) = sInf {(s : α) | s ∈ S}
```

### `Set.image` (commanddeclaration)
```lean
def image (f : α → β) (s : Set α) : Set β
```

### `sInf_image` (commanddeclaration)
```lean
theorem sInf_image {s : Set β} {f : β → α} : sInf (f '' s) = ⨅ a ∈ s, f a
```

## Premise full source (with proof)
### `CompleteSublattice.coe_sInf` (commanddeclaration) at `Mathlib/Order/CompleteSublattice.lean`
```lean
@[simp] theorem coe_sInf (S : Set L) : (↑(sInf S) : α) = sInf {(s : α) | s ∈ S} := rfl
```

### `Set.image` (commanddeclaration) at `Mathlib/Init/Set.lean`
```lean
/-- The image of `s : Set α` by `f : α → β`, written `f '' s`, is the set of `b : β` such that
`f a = b` for some `a ∈ s`. -/
def image (f : α → β) (s : Set α) : Set β := {f a | a ∈ s}
```

### `sInf_image` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
theorem sInf_image {s : Set β} {f : β → α} : sInf (f '' s) = ⨅ a ∈ s, f a :=
  @sSup_image αᵒᵈ _ _ _ _
```

## Transitive premise context (1-hop, 1/1 premises, ≈77 tokens)
### `sSup_image` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
theorem sSup_image {s : Set β} {f : β → α} : sSup (f '' s) = ⨆ a ∈ s, f a := by
  rw [← iSup_subtype'', sSup_image']
```
