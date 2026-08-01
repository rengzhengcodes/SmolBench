## Current goal
```
⊢ (⨆ i, f i) x = iSup (fun i => ⇑(f i)) x
```

## Full tactic state
```
case h
α : Type u_1
β : Type u_2
inst✝¹ : Preorder α
ι : Sort u_3
inst✝ : CompleteLattice β
f : ι → α →o β
x : α
⊢ (⨆ i, f i) x = iSup (fun i => ⇑(f i)) x
```

## Proof so far (1 tactic)
```lean
funext x
```

## Theorem
`OrderHom.coe_iSup` in `Mathlib/Order/Hom/Order.lean`

## Premises used in the next tactic
- `OrderHom.iSup_apply`

## Premise signatures
### `OrderHom.iSup_apply` (commanddeclaration)
```lean
theorem iSup_apply {ι : Sort*} [CompleteLattice β] (f : ι → α →o β) (x : α) :
    (⨆ i, f i) x = ⨆ i, f i x
```

## Premise full source (with proof)
### `OrderHom.iSup_apply` (commanddeclaration) at `Mathlib/Order/Hom/Order.lean`
```lean
theorem iSup_apply {ι : Sort*} [CompleteLattice β] (f : ι → α →o β) (x : α) :
    (⨆ i, f i) x = ⨆ i, f i x :=
  (sSup_apply _ _).trans iSup_range
```

## Transitive premise context (1-hop, 5/5 premises, ≈539 tokens)
### `iSup_apply` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
@[simp]
theorem iSup_apply {α : Type*} {β : α → Type*} {ι : Sort*} [∀ i, SupSet (β i)] {f : ι → ∀ a, β a}
    {a : α} : (⨆ i, f i) a = ⨆ i, f i a := by
  rw [iSup, sSup_apply, iSup, iSup, ← image_eq_range (fun f : ∀ i, β i => f a) (range f), ←
    range_comp]; rfl
```

### `CompleteLattice` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
/-- A complete lattice is a bounded lattice which has suprema and infima for every subset. -/
class CompleteLattice (α : Type*) extends Lattice α, CompleteSemilatticeSup α,
  CompleteSemilatticeInf α, Top α, Bot α where
  /-- Any element is less than the top one. -/
  protected le_top : ∀ x : α, x ≤ ⊤
  /-- Any element is more than the bottom one. -/
  protected bot_le : ∀ x : α, ⊥ ≤ x
```

### `sSup_apply` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
theorem sSup_apply {α : Type*} {β : α → Type*} [∀ i, SupSet (β i)] {s : Set (∀ a, β a)} {a : α} :
    (sSup s) a = ⨆ f : s, (f : ∀ a, β a) a :=
  rfl
```

### `trans` (commanddeclaration) at `Mathlib/Init/Algebra/Classes.lean`
```lean
theorem trans [IsTrans α r] {a b c : α} : a ≺ b → b ≺ c → a ≺ c :=
  IsTrans.trans _ _ _
```

### `iSup_range` (commanddeclaration) at `Mathlib/Order/CompleteLattice.lean`
```lean
theorem iSup_range {g : β → α} {f : ι → β} : ⨆ b ∈ range f, g b = ⨆ i, g (f i) := by
  rw [← iSup_subtype'', iSup_range']
```
