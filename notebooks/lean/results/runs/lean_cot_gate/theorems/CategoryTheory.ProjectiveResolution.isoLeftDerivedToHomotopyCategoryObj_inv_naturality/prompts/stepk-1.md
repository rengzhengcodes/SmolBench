## Current goal
```
⊢ (Functor.mapHomotopyCategoryFactors F (ComplexShape.down ℕ)).inv.app P.complex ≫
      (Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map
          ((HomotopyCategory.quotient C (ComplexShape.down ℕ)).map φ) ≫
        (Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map (iso Q).inv =
    (Functor.mapHomotopyCategoryFactors F (ComplexShape.down ℕ)).inv.app P.complex ≫
      (HomotopyCategory.quotient C (ComplexShape.down ℕ) ⋙ Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map φ ≫
        (Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map (iso Q).inv
```

## Full tactic state
```
C : Type u
inst✝⁵ : Category.{v, u} C
D : Type u_1
inst✝⁴ : Category.{u_2, u_1} D
inst✝³ : Abelian C
inst✝² : HasProjectiveResolutions C
inst✝¹ : Abelian D
X Y : C
f : X ⟶ Y
P : ProjectiveResolution X
Q : ProjectiveResolution Y
φ : P.complex ⟶ Q.complex
comm : φ.f 0 ≫ Q.π.f 0 = P.π.f 0 ≫ f
F : C ⥤ D
inst✝ : Functor.Additive F
⊢ (Functor.mapHomotopyCategoryFactors F (ComplexShape.down ℕ)).inv.app P.complex ≫
      (Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map
          ((HomotopyCategory.quotient C (ComplexShape.down ℕ)).map φ) ≫
        (Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map (iso Q).inv =
    (Functor.mapHomotopyCategoryFactors F (ComplexShape.down ℕ)).inv.app P.complex ≫
      (HomotopyCategory.quotient C (ComplexShape.down ℕ) ⋙ Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map φ ≫
        (Functor.mapHomotopyCategory F (ComplexShape.down ℕ)).map (iso Q).inv
```
