## Current goal
```
⊢ IsUnit f ↔ ∃ a, f = pure a
```

## Full tactic state
```
F : Type u_1
α : Type u_2
β : Type u_3
γ : Type u_4
δ : Type u_5
ε : Type u_6
inst✝³ : Group α
inst✝² : DivisionMonoid β
inst✝¹ : FunLike F α β
inst✝ : MonoidHomClass F α β
m : F
f g f₁ g₁ : Filter α
f₂ g₂ : Filter β
⊢ IsUnit f ↔ ∃ a, f = pure a
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`Filter.isUnit_iff_singleton` in `Mathlib/Order/Filter/Pointwise.lean`

## Premises used in the next tactic
- `Filter.isUnit_iff`
- `Group.isUnit`
- `and_true_iff`

## Premise signatures
### `Filter.isUnit_iff` (commanddeclaration)
```lean
@[to_additive]
theorem isUnit_iff : IsUnit f ↔ ∃ a, f = pure a ∧ IsUnit a
```

### `Group.isUnit` (lemma)
```lean
@[to_additive]
lemma Group.isUnit [Group α] (a : α) : IsUnit a
```

### `and_true_iff` (commanddeclaration)
```lean
theorem and_true_iff : p ∧ True ↔ p
```

## Premise full source (with proof)
### `Filter.isUnit_iff` (commanddeclaration) at `Mathlib/Order/Filter/Pointwise.lean`
```lean
@[to_additive]
theorem isUnit_iff : IsUnit f ↔ ∃ a, f = pure a ∧ IsUnit a := by
  constructor
  · rintro ⟨u, rfl⟩
    obtain ⟨a, b, ha, hb, h⟩ := Filter.mul_eq_one_iff.1 u.mul_inv
    refine' ⟨a, ha, ⟨a, b, h, pure_injective _⟩, rfl⟩
    rw [← pure_mul_pure, ← ha, ← hb]
    exact u.inv_mul
  · rintro ⟨a, rfl, ha⟩
    exact ha.filter
```

### `Group.isUnit` (lemma) at `Mathlib/Algebra/Group/Units.lean`
```lean
@[to_additive]
lemma Group.isUnit [Group α] (a : α) : IsUnit a := ⟨⟨a, a⁻¹, mul_inv_self _, inv_mul_self _⟩, rfl⟩
```

### `and_true_iff` (commanddeclaration) at `Mathlib/Init/Logic.lean`
```lean
theorem and_true_iff : p ∧ True ↔ p := iff_of_eq (and_true _)
```

## Transitive premise context (1-hop, 6/6 premises, ≈608 tokens)
### `IsUnit` (commanddeclaration) at `Mathlib/Algebra/Group/Units.lean`
```lean
/-- An element `a : M` of a `Monoid` is a unit if it has a two-sided inverse.
The actual definition says that `a` is equal to some `u : Mˣ`, where
`Mˣ` is a bundled version of `IsUnit`. -/
@[to_additive
      "An element `a : M` of an `AddMonoid` is an `AddUnit` if it has a two-sided additive inverse.
      The actual definition says that `a` is equal to some `u : AddUnits M`,
      where `AddUnits M` is a bundled version of `IsAddUnit`."]
def IsUnit [Monoid M] (a : M) : Prop :=
  ∃ u : Mˣ, (u : M) = a
```

### `Group` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
/-- A `Group` is a `Monoid` with an operation `⁻¹` satisfying `a⁻¹ * a = 1`.

There is also a division operation `/` such that `a / b = a * b⁻¹`,
with a default so that `a / b = a * b⁻¹` holds by definition.

Use `Group.ofLeftAxioms` or `Group.ofRightAxioms` to define a group structure
on a type with the minumum proof obligations.
-/
class Group (G : Type u) extends DivInvMonoid G where
  protected mul_left_inv : ∀ a : G, a⁻¹ * a = 1
```

### `mul_inv_self` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive]
theorem mul_inv_self (a : G) : a * a⁻¹ = 1 :=
  mul_right_inv a
```

### `inv_mul_self` (commanddeclaration) at `Mathlib/Algebra/Group/Defs.lean`
```lean
@[to_additive]
theorem inv_mul_self (a : G) : a⁻¹ * a = 1 :=
  mul_left_inv a
```

### `iff_of_eq` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/Core.lean`
```lean
theorem iff_of_eq : a = b → (a ↔ b) := Iff.of_eq
```

### `and_true` (commanddeclaration) at `.lake/packages/lean4/src/lean/Init/SimpLemmas.lean`
```lean
@[simp] theorem and_true (p : Prop) : (p ∧ True) = p := propext ⟨(·.1), (⟨·, trivial⟩)⟩
```
