## Current goal
```
⊢ (unitCompPartialBijective A hB') (f ≫ h) = (unitCompPartialBijective A hB) f ≫ h
```

## Full tactic state
```
C : Type u₁
D : Type u₂
E : Type u₃
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
inst✝¹ : Category.{v₃, u₃} E
i : D ⥤ C
inst✝ : Reflective i
A B B' : C
h : B ⟶ B'
hB : B ∈ Functor.essImage i
hB' : B' ∈ Functor.essImage i
f : A ⟶ B
⊢ (unitCompPartialBijective A hB') (f ≫ h) = (unitCompPartialBijective A hB) f ≫ h
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.unitCompPartialBijective_natural` in `Mathlib/CategoryTheory/Adjunction/Reflective.lean`

## Premises used in the next tactic
- `Equiv.eq_symm_apply`
- `CategoryTheory.unitCompPartialBijective_symm_natural`
- `Equiv.symm_apply_apply`

## Premise signatures
### `Equiv.eq_symm_apply` (commanddeclaration)
```lean
theorem eq_symm_apply {α β} (e : α ≃ β) {x y} : y = e.symm x ↔ e y = x
```

### `CategoryTheory.unitCompPartialBijective_symm_natural` (commanddeclaration)
```lean
theorem unitCompPartialBijective_symm_natural [Reflective i] (A : C) {B B' : C} (h : B ⟶ B')
    (hB : B ∈ i.essImage) (hB' : B' ∈ i.essImage) (f : i.obj ((leftAdjoint i).obj A) ⟶ B) :
    (unitCompPartialBijective A hB').symm (f ≫ h) = (unitCompPartialBijective A hB).symm f ≫ h
```

### `Equiv.symm_apply_apply` (commanddeclaration)
```lean
@[simp] theorem symm_apply_apply (e : α ≃ β) (x : α) : e.symm (e x) = x
```

## Premise full source (with proof)
### `Equiv.eq_symm_apply` (commanddeclaration) at `Mathlib/Logic/Equiv/Defs.lean`
```lean
theorem eq_symm_apply {α β} (e : α ≃ β) {x y} : y = e.symm x ↔ e y = x :=
  (eq_comm.trans e.symm_apply_eq).trans eq_comm
```

### `CategoryTheory.unitCompPartialBijective_symm_natural` (commanddeclaration) at `Mathlib/CategoryTheory/Adjunction/Reflective.lean`
```lean
theorem unitCompPartialBijective_symm_natural [Reflective i] (A : C) {B B' : C} (h : B ⟶ B')
    (hB : B ∈ i.essImage) (hB' : B' ∈ i.essImage) (f : i.obj ((leftAdjoint i).obj A) ⟶ B) :
    (unitCompPartialBijective A hB').symm (f ≫ h) = (unitCompPartialBijective A hB).symm f ≫ h := by
  simp
```

### `Equiv.symm_apply_apply` (commanddeclaration) at `Mathlib/Logic/Equiv/Defs.lean`
```lean
@[simp] theorem symm_apply_apply (e : α ≃ β) (x : α) : e.symm (e x) = x := e.left_inv x
```

## Filler (hint:2 → hint:3 token-match, ≈802 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco
