## Current goal
```
⊢ (HomotopyCategory.homologyFunctor D (ComplexShape.up ℕ) n).map (isoRightDerivedToHomotopyCategoryObj I F).hom ≫
      (HomotopyCategory.homologyFunctorFactors D (ComplexShape.up ℕ) n).hom.app
          ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).obj I.cocomplex) ≫
        (HomologicalComplex.homologyFunctor D (ComplexShape.up ℕ) n).map
          ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).map φ) =
    (HomotopyCategory.homologyFunctor D (ComplexShape.up ℕ) n).map (isoRightDerivedToHomotopyCategoryObj I F).hom ≫
      (HomotopyCategory.homologyFunctorFactors D (ComplexShape.up ℕ) n).hom.app
          ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).obj I.cocomplex) ≫
        HomologicalComplex.homologyMap ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).map φ) n
```

## Full tactic state
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u_1
inst✝⁴ : Category.{u_2, u_1} D
inst✝³ : Abelian C
inst✝² : HasInjectiveResolutions C
inst✝¹ : Abelian D
X Y : C
f : X ⟶ Y
I : InjectiveResolution X
J : InjectiveResolution Y
φ : I.cocomplex ⟶ J.cocomplex
comm : I.ι.f 0 ≫ φ.f 0 = f ≫ J.ι.f 0
F : C ⥤ D
inst✝ : Functor.Additive F
n : ℕ
⊢ (HomotopyCategory.homologyFunctor D (ComplexShape.up ℕ) n).map (isoRightDerivedToHomotopyCategoryObj I F).hom ≫
      (HomotopyCategory.homologyFunctorFactors D (ComplexShape.up ℕ) n).hom.app
          ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).obj I.cocomplex) ≫
        (HomologicalComplex.homologyFunctor D (ComplexShape.up ℕ) n).map
          ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).map φ) =
    (HomotopyCategory.homologyFunctor D (ComplexShape.up ℕ) n).map (isoRightDerivedToHomotopyCategoryObj I F).hom ≫
      (HomotopyCategory.homologyFunctorFactors D (ComplexShape.up ℕ) n).hom.app
          ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).obj I.cocomplex) ≫
        HomologicalComplex.homologyMap ((Functor.mapHomologicalComplex F (ComplexShape.up ℕ)).map φ) n
```
