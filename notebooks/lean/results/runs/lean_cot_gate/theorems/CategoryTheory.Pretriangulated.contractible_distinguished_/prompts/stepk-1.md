## Current goal
```
⊢ (Triangle.mk 0 (𝟙 X) 0).mor₃ ≫ (shiftFunctor C 1).map (Functor.mapZeroObject (shiftFunctor C (-1))).symm.hom =
    (Iso.refl (Triangle.mk 0 (𝟙 X) 0).obj₃).hom ≫ (Triangle.invRotate (contractibleTriangle X)).mor₃
```

## Full tactic state
```
C : Type u
inst✝⁴ : Category.{v, u} C
inst✝³ : HasZeroObject C
inst✝² : HasShift C ℤ
inst✝¹ : Preadditive C
inst✝ : ∀ (n : ℤ), Functor.Additive (shiftFunctor C n)
hC : Pretriangulated C
X : C
⊢ (Triangle.mk 0 (𝟙 X) 0).mor₃ ≫ (shiftFunctor C 1).map (Functor.mapZeroObject (shiftFunctor C (-1))).symm.hom =
    (Iso.refl (Triangle.mk 0 (𝟙 X) 0).obj₃).hom ≫ (Triangle.invRotate (contractibleTriangle X)).mor₃
```
