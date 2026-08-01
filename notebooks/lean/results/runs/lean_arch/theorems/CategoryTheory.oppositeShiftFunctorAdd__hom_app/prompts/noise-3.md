## Current goal
```
⊢ (shiftFunctorAdd' (OppositeShift C A) a b (a + b) ⋯).hom.app X =
    ((shiftFunctorAdd' C a b (a + b) ⋯).inv.app X.unop).op
```

## Full tactic state
```
C : Type u_1
inst✝² : Category.{u_3, u_1} C
A : Type u_2
inst✝¹ : AddMonoid A
inst✝ : HasShift C A
X : OppositeShift C A
a b : A
⊢ (shiftFunctorAdd' (OppositeShift C A) a b (a + b) ⋯).hom.app X =
    ((shiftFunctorAdd' C a b (a + b) ⋯).inv.app X.unop).op
```

## Proof so far (1 tactic)
```lean
subst h
```

## Theorem
`CategoryTheory.oppositeShiftFunctorAdd'_hom_app` in `Mathlib/CategoryTheory/Shift/Opposite.lean`

## Premises used in the next tactic
- `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd`
- `CategoryTheory.oppositeShiftFunctorAdd_hom_app`

## Premise signatures
### `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd` (lemma)
```lean
lemma shiftFunctorAdd'_eq_shiftFunctorAdd (i j : A) :
    shiftFunctorAdd' C i j (i+j) rfl = shiftFunctorAdd C i j
```

### `CategoryTheory.oppositeShiftFunctorAdd_hom_app` (lemma)
```lean
lemma oppositeShiftFunctorAdd_hom_app :
    (shiftFunctorAdd (OppositeShift C A) a b).hom.app X =
      ((shiftFunctorAdd C a b).inv.app X.unop).op
```

## Premise full source (with proof)
### `CategoryTheory.shiftFunctorAdd'_eq_shiftFunctorAdd` (lemma) at `Mathlib/CategoryTheory/Shift/Basic.lean`
```lean
lemma shiftFunctorAdd'_eq_shiftFunctorAdd (i j : A) :
    shiftFunctorAdd' C i j (i+j) rfl = shiftFunctorAdd C i j := by
  ext1
  apply Category.id_comp
```

### `CategoryTheory.oppositeShiftFunctorAdd_hom_app` (lemma) at `Mathlib/CategoryTheory/Shift/Opposite.lean`
```lean
lemma oppositeShiftFunctorAdd_hom_app :
    (shiftFunctorAdd (OppositeShift C A) a b).hom.app X =
      ((shiftFunctorAdd C a b).inv.app X.unop).op := by
  rw [← cancel_mono ((shiftFunctorAdd (OppositeShift C A) a b).inv.app X),
    Iso.hom_inv_id_app, oppositeShiftFunctorAdd_inv_app, ← op_comp,
    Iso.hom_inv_id_app, op_id]
  rfl
```

## Filler (hint:2 → hint:3 token-match, ≈427 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
