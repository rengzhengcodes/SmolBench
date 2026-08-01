## Current goal
```
⊢ coprod.inl ≫
      (colimit.isoColimitCocone
          { cocone := BinaryCofan.mk (𝟙 X) 0, isColimit := binaryCofanZeroRightIsColimit X }).hom =
    𝟙 X
```

## Full tactic state
```
C : Type u_1
inst✝² : Category.{u_2, u_1} C
inst✝¹ : HasZeroObject C
inst✝ : HasZeroMorphisms C
X : C
⊢ coprod.inl ≫
      (colimit.isoColimitCocone
          { cocone := BinaryCofan.mk (𝟙 X) 0, isColimit := binaryCofanZeroRightIsColimit X }).hom =
    𝟙 X
```
