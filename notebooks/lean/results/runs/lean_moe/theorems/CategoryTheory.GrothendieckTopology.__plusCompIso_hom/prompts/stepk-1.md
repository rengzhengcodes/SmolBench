## Current goal
```
⊢ (colimit.cocone (diagram J P X.unop ⋙ F)).ι.app W ≫
      (HasColimit.isoOfNatIso
          (NatIso.ofComponents
            (fun W =>
              IsLimit.conePointUniqueUpToIso
                  (isLimitOfPreserves F (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P))))
                  (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P) ⋙ F)) ≪≫
                HasLimit.isoOfNatIso (Cover.multicospanComp F P W.unop).symm)
            ⋯)).hom =
    ((IsLimit.conePointUniqueUpToIso
            (isLimitOfPreserves F (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P))))
            (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P) ⋙ F))).hom ≫
        (HasLimit.isoOfNatIso (Cover.multicospanComp F P W.unop).symm).hom) ≫
      colimit.ι (diagram J (P ⋙ F) X.unop) W
```

## Full tactic state
```
C : Type u
inst✝⁸ : Category.{v, u} C
J : GrothendieckTopology C
D : Type w₁
inst✝⁷ : Category.{max v u, w₁} D
E : Type w₂
inst✝⁶ : Category.{max v u, w₂} E
F : D ⥤ E
inst✝⁵ : ∀ (α β : Type (max v u)) (fst snd : β → α), HasLimitsOfShape (WalkingMulticospan fst snd) D
inst✝⁴ : ∀ (α β : Type (max v u)) (fst snd : β → α), HasLimitsOfShape (WalkingMulticospan fst snd) E
inst✝³ : (X : C) → (W : Cover J X) → (P : Cᵒᵖ ⥤ D) → PreservesLimit (MulticospanIndex.multicospan (Cover.index W P)) F
P : Cᵒᵖ ⥤ D
inst✝² : ∀ (X : C), HasColimitsOfShape (Cover J X)ᵒᵖ D
inst✝¹ : ∀ (X : C), HasColimitsOfShape (Cover J X)ᵒᵖ E
inst✝ : (X : C) → PreservesColimitsOfShape (Cover J X)ᵒᵖ F
X : Cᵒᵖ
W : (Cover J X.unop)ᵒᵖ
⊢ (colimit.cocone (diagram J P X.unop ⋙ F)).ι.app W ≫
      (HasColimit.isoOfNatIso
          (NatIso.ofComponents
            (fun W =>
              IsLimit.conePointUniqueUpToIso
                  (isLimitOfPreserves F (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P))))
                  (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P) ⋙ F)) ≪≫
                HasLimit.isoOfNatIso (Cover.multicospanComp F P W.unop).symm)
            ⋯)).hom =
    ((IsLimit.conePointUniqueUpToIso
            (isLimitOfPreserves F (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P))))
            (limit.isLimit (MulticospanIndex.multicospan (Cover.index W.unop P) ⋙ F))).hom ≫
        (HasLimit.isoOfNatIso (Cover.multicospanComp F P W.unop).symm).hom) ≫
      colimit.ι (diagram J (P ⋙ F) X.unop) W
```
