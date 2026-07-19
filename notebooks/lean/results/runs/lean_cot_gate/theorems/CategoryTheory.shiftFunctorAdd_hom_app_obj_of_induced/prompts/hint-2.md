## Current goal
```
⊢ (shiftFunctorAdd D a b).hom.app (F.obj X) =
    (i (a + b)).hom.app X ≫
      F.map ((shiftFunctorAdd C a b).hom.app X) ≫ (i b).inv.app ((shiftFunctor C a).obj X) ≫ (s b).map ((i a).inv.app X)
```

## Full tactic state
```
C : Type u_4
D : Type u_2
inst✝³ : Category.{u_5, u_4} C
inst✝² : Category.{u_1, u_2} D
F : C ⥤ D
A : Type u_3
inst✝¹ : AddMonoid A
inst✝ : HasShift C A
s : A → D ⥤ D
i : (a : A) → F ⋙ s a ≅ shiftFunctor C a ⋙ F
hF : Nonempty (Full ((whiskeringLeft C D D).obj F)) ∧ Faithful ((whiskeringLeft C D D).obj F)
a b : A
X : C
this : Nonempty (Full ((whiskeringLeft C D D).obj F)) ∧ Faithful ((whiskeringLeft C D D).obj F) → HasShift D A :=
  HasShift.induced F A s i
⊢ (shiftFunctorAdd D a b).hom.app (F.obj X) =
    (i (a + b)).hom.app X ≫
      F.map ((shiftFunctorAdd C a b).hom.app X) ≫ (i b).inv.app ((shiftFunctor C a).obj X) ≫ (s b).map ((i a).inv.app X)
```

## Proof so far (1 tactic)
```lean
letI := HasShift.induced F A s i
```

## Theorem
`CategoryTheory.shiftFunctorAdd_hom_app_obj_of_induced` in `Mathlib/CategoryTheory/Shift/Induced.lean`

## Premises used in the next tactic
- `CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq`
- `CategoryTheory.HasShift.Induced.add_hom_app_obj`

## Premise signatures
### `CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq` (lemma)
```lean
lemma ShiftMkCore.shiftFunctorAdd_eq (h : ShiftMkCore C A) (a b : A) :
    letI
```

### `CategoryTheory.HasShift.Induced.add_hom_app_obj` (lemma)
```lean
@[simp]
lemma add_hom_app_obj (a b : A) (X : C) :
    (add F s i hF a b).hom.app (F.obj X) =
      (i (a + b)).hom.app X ≫ F.map ((shiftFunctorAdd C a b).hom.app X) ≫
        (i b).inv.app ((shiftFunctor C a).obj X) ≫ (s b).map ((i a).inv.app X)
```

## Premise full source (with proof)
### `CategoryTheory.ShiftMkCore.shiftFunctorAdd_eq` (lemma) at `Mathlib/CategoryTheory/Shift/Basic.lean`
```lean
lemma ShiftMkCore.shiftFunctorAdd_eq (h : ShiftMkCore C A) (a b : A) :
    letI := hasShiftMk C A h;
    shiftFunctorAdd C a b = h.add a b := by
  letI := hasShiftMk C A h
  change (shiftFunctorAdd C a b).symm.symm = (h.add a b).symm.symm
  congr 1
  ext
  rfl
```

### `CategoryTheory.HasShift.Induced.add_hom_app_obj` (lemma) at `Mathlib/CategoryTheory/Shift/Induced.lean`
```lean
@[simp]
lemma add_hom_app_obj (a b : A) (X : C) :
    (add F s i hF a b).hom.app (F.obj X) =
      (i (a + b)).hom.app X ≫ F.map ((shiftFunctorAdd C a b).hom.app X) ≫
        (i b).inv.app ((shiftFunctor C a).obj X) ≫ (s b).map ((i a).inv.app X) := by
  letI := hF.1.some
  have h : whiskerLeft F (add F s i hF a b).hom = _ :=
    ((whiskeringLeft C D D).obj F).image_preimage _
  exact (NatTrans.congr_app h X).trans (by simp)
```
