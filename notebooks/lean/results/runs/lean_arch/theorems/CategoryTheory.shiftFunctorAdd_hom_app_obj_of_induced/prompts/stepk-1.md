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
