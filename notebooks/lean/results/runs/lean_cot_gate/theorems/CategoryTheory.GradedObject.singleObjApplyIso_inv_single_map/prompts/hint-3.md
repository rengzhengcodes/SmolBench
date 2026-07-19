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

## Transitive premise context (1-hop, 1/1 premises, ≈134 tokens)
### `CategoryTheory.GradedObject.singleObjApplyIsoOfEq` (commanddeclaration) at `Mathlib/CategoryTheory/GradedObject/Single.lean`
```lean
/-- The canonical isomorphism `(single j).obj X i ≅ X` when `i = j`. -/
noncomputable def singleObjApplyIsoOfEq (j : J) (X : C) (i : J) (h : i = j) :
    (single j).obj X i ≅ X := eqToIso (if_pos h)

/-- The canonical isomorphism `(single j).obj X j ≅ X`. -/
```
