## Current goal
```
⊢ ∀ (j : Discrete PEmpty.{1}),
    ((Cocones.precompose (Functor.uniqueFromEmpty ((equivalenceOfIsEmpty (Discrete PEmpty.{1}) J).functor ⋙ F)).hom).obj
                (asEmptyCocone c.pt)).ι.app
          j ≫
        (Iso.refl
            ((Cocones.precompose
                    (Functor.uniqueFromEmpty ((equivalenceOfIsEmpty (Discrete PEmpty.{1}) J).functor ⋙ F)).hom).obj
                (asEmptyCocone c.pt)).pt).hom =
      (Cocone.whisker (equivalenceOfIsEmpty (Discrete PEmpty.{1}) J).functor c).ι.app j
```

## Full tactic state
```
J : Type v'
inst✝⁵ : Category.{u', v'} J
C : Type u
inst✝⁴ : Category.{v, u} C
K : Type u_1
inst✝³ : Category.{?u.279251, u_1} K
D : Type u_2
inst✝² : Category.{?u.279258, u_2} D
inst✝¹ : HasStrictInitialObjects C
inst✝ : IsEmpty J
F : J ⥤ C
c : Cocone F
hc : IsColimit c
this : IsVanKampenColimit (asEmptyCocone c.pt)
⊢ ∀ (j : Discrete PEmpty.{1}),
    ((Cocones.precompose (Functor.uniqueFromEmpty ((equivalenceOfIsEmpty (Discrete PEmpty.{1}) J).functor ⋙ F)).hom).obj
                (asEmptyCocone c.pt)).ι.app
          j ≫
        (Iso.refl
            ((Cocones.precompose
                    (Functor.uniqueFromEmpty ((equivalenceOfIsEmpty (Discrete PEmpty.{1}) J).functor ⋙ F)).hom).obj
                (asEmptyCocone c.pt)).pt).hom =
      (Cocone.whisker (equivalenceOfIsEmpty (Discrete PEmpty.{1}) J).functor c).ι.app j
```
