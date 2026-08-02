## Current goal
```
⊢ IsCompl ↑a ↑b ↔ IsCompl a b
```

## Full tactic state
```
α : Type u_1
inst✝¹ : DistribLattice α
inst✝ : BoundedOrder α
a b : Complementeds α
⊢ IsCompl ↑a ↑b ↔ IsCompl a b
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Complementeds.isCompl_coe` in `Mathlib/Order/Disjoint.lean`

## Premises used in the next tactic
- `isCompl_iff`
- `Complementeds.disjoint_coe`
- `Complementeds.codisjoint_coe`

## Premise signatures
### `isCompl_iff` (commanddeclaration)
```lean
theorem isCompl_iff [PartialOrder α] [BoundedOrder α] {a b : α} :
    IsCompl a b ↔ Disjoint a b ∧ Codisjoint a b
```

### `Complementeds.disjoint_coe` (commanddeclaration)
```lean
@[simp, norm_cast]
theorem disjoint_coe : Disjoint (a : α) b ↔ Disjoint a b
```

### `Complementeds.codisjoint_coe` (commanddeclaration)
```lean
@[simp, norm_cast]
theorem codisjoint_coe : Codisjoint (a : α) b ↔ Codisjoint a b
```

## Premise full source (with proof)
### `isCompl_iff` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
theorem isCompl_iff [PartialOrder α] [BoundedOrder α] {a b : α} :
    IsCompl a b ↔ Disjoint a b ∧ Codisjoint a b :=
  ⟨fun h ↦ ⟨h.1, h.2⟩, fun h ↦ ⟨h.1, h.2⟩⟩
```

### `Complementeds.disjoint_coe` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
@[simp, norm_cast]
theorem disjoint_coe : Disjoint (a : α) b ↔ Disjoint a b := by
  rw [disjoint_iff, disjoint_iff, ← coe_inf, ← coe_bot, coe_inj]
```

### `Complementeds.codisjoint_coe` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
@[simp, norm_cast]
theorem codisjoint_coe : Codisjoint (a : α) b ↔ Codisjoint a b := by
  rw [codisjoint_iff, codisjoint_iff, ← coe_sup, ← coe_top, coe_inj]
```

## Transitive premise context (1-hop, 7/7 premises, ≈710 tokens)
### `PartialOrder` (commanddeclaration) at `Mathlib/Init/Order/Defs.lean`
```lean
/-- A partial order is a reflexive, transitive, antisymmetric relation `≤`. -/
class PartialOrder (α : Type u) extends Preorder α where
  le_antisymm : ∀ a b : α, a ≤ b → b ≤ a → a = b
```

### `BoundedOrder` (commanddeclaration) at `Mathlib/Order/BoundedOrder.lean`
```lean
/-- A bounded order describes an order `(≤)` with a top and bottom element,
  denoted `⊤` and `⊥` respectively. -/
class BoundedOrder (α : Type u) [LE α] extends OrderTop α, OrderBot α
```

### `IsCompl` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
/-- Two elements `x` and `y` are complements of each other if `x ⊔ y = ⊤` and `x ⊓ y = ⊥`. -/
structure IsCompl [PartialOrder α] [BoundedOrder α] (x y : α) : Prop where
  /-- If `x` and `y` are to be complementary in an order, they should be disjoint. -/
  protected disjoint : Disjoint x y
  /-- If `x` and `y` are to be complementary in an order, they should be codisjoint. -/
  protected codisjoint : Codisjoint x y
```

### `Disjoint` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
/-- Two elements of a lattice are disjoint if their inf is the bottom element.
  (This generalizes disjoint sets, viewed as members of the subset lattice.)

Note that we define this without reference to `⊓`, as this allows us to talk about orders where
the infimum is not unique, or where implementing `Inf` would require additional `Decidable`
arguments. -/
def Disjoint (a b : α) : Prop :=
  ∀ ⦃x⦄, x ≤ a → x ≤ b → x ≤ ⊥
```

### `Codisjoint` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
/-- Two elements of a lattice are codisjoint if their sup is the top element.

Note that we define this without reference to `⊔`, as this allows us to talk about orders where
the supremum is not unique, or where implement `Sup` would require additional `Decidable`
arguments. -/
def Codisjoint (a b : α) : Prop :=
  ∀ ⦃x⦄, a ≤ x → b ≤ x → ⊤ ≤ x
```

### `disjoint_iff` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
theorem disjoint_iff : Disjoint a b ↔ a ⊓ b = ⊥ :=
  disjoint_iff_inf_le.trans le_bot_iff
```

### `codisjoint_iff` (commanddeclaration) at `Mathlib/Order/Disjoint.lean`
```lean
theorem codisjoint_iff : Codisjoint a b ↔ a ⊔ b = ⊤ :=
  @disjoint_iff αᵒᵈ _ _ _ _
```
