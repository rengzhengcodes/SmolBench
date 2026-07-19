## Current goal
```
⊢ c.ι.app i ≫
      (IsColimit.coconePointUniqueUpToIso hc isc).hom ≫
        (colimit
            ((Cocone.toCostructuredArrow c ⋙ CostructuredArrow.pre F yoneda c.pt) ⋙
              CostructuredArrow.toOver yoneda c.pt)).hom =
    c.ι.app i ≫ (Over.mk (𝟙 c.pt)).hom
```

## Full tactic state
```
C : Type u₁
inst✝¹ : Category.{v₁, u₁} C
P : Cᵒᵖ ⥤ Type v₁
I : Type v₁
inst✝ : SmallCategory I
F : I ⥤ C
c : Cocone (F ⋙ yoneda)
hc : IsColimit c
isc : IsColimit
  ((Over.forget c.pt).mapCocone
    (colimit.cocone
      ((Cocone.toCostructuredArrow c ⋙ CostructuredArrow.pre F yoneda c.pt) ⋙ CostructuredArrow.toOver yoneda c.pt))) :=
  PreservesColimit.preserves
    (colimit.isColimit
      ((Cocone.toCostructuredArrow c ⋙ CostructuredArrow.pre F yoneda c.pt) ⋙ CostructuredArrow.toOver yoneda c.pt))
i : I
⊢ c.ι.app i ≫
      (IsColimit.coconePointUniqueUpToIso hc isc).hom ≫
        (colimit
            ((Cocone.toCostructuredArrow c ⋙ CostructuredArrow.pre F yoneda c.pt) ⋙
              CostructuredArrow.toOver yoneda c.pt)).hom =
    c.ι.app i ≫ (Over.mk (𝟙 c.pt)).hom
```
