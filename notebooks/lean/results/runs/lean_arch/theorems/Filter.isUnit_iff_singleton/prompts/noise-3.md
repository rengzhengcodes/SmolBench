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

## Filler (hint:2 → hint:3 token-match, ≈634 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
