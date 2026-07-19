## Current goal
```
⊢ (singleObjApplyIso j X).inv ≫ (single j).map f j = f ≫ (singleObjApplyIso j Y).inv
```

## Full tactic state
```
J : Type u_1
C : Type u_2
inst✝² : Category.{u_3, u_2} C
inst✝¹ : HasInitial C
inst✝ : DecidableEq J
j : J
X Y : C
f : X ⟶ Y
⊢ (singleObjApplyIso j X).inv ≫ (single j).map f j = f ≫ (singleObjApplyIso j Y).inv
```

## Proof so far
_(no tactics applied yet — this is the start of the proof)_

## Theorem
`CategoryTheory.GradedObject.singleObjApplyIso_inv_single_map` in `Mathlib/CategoryTheory/GradedObject/Single.lean`

## Premises used in the next tactic
- `CategoryTheory.GradedObject.singleObjApplyIsoOfEq_inv_single_map`

## Premise signatures
### `CategoryTheory.GradedObject.singleObjApplyIsoOfEq_inv_single_map` (lemma)
```lean
lemma singleObjApplyIsoOfEq_inv_single_map (j : J) {X Y : C} (f : X ⟶ Y) (i : J) (h : i = j) :
    (singleObjApplyIsoOfEq j X i h).inv ≫ (single j).map f i =
      f ≫ (singleObjApplyIsoOfEq j Y i h).inv
```

## Premise full source (with proof)
### `CategoryTheory.GradedObject.singleObjApplyIsoOfEq_inv_single_map` (lemma) at `Mathlib/CategoryTheory/GradedObject/Single.lean`
```lean
lemma singleObjApplyIsoOfEq_inv_single_map (j : J) {X Y : C} (f : X ⟶ Y) (i : J) (h : i = j) :
    (singleObjApplyIsoOfEq j X i h).inv ≫ (single j).map f i =
      f ≫ (singleObjApplyIsoOfEq j Y i h).inv := by
  subst h
  simp [singleObjApplyIsoOfEq, single]
```

## Filler (hint:2 → hint:3 token-match, ≈155 tokens, no informational content)
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse c
