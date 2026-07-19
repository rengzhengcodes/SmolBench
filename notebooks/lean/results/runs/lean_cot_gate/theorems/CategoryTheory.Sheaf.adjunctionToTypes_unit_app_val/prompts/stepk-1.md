## Current goal
```
⊢ ((sheafEquivSheafOfTypes J).symm.unit.app Y).val ≫
      ((Adjunction.whiskerRight Cᵒᵖ adj).homEquiv Y.val ((presheafToSheaf J D).obj (Y.val ⋙ G)).val)
        (toSheafify J (Y.val ⋙ G)) =
    (Adjunction.whiskerRight Cᵒᵖ adj).unit.app Y.val ≫ whiskerRight (toSheafify J (Y.val ⋙ G)) (forget D)
```

## Full tactic state
```
C : Type u
inst✝⁶ : Category.{v, u} C
J : GrothendieckTopology C
D : Type u_1
inst✝⁵ : Category.{u_3, u_1} D
E : Type u_2
inst✝⁴ : Category.{?u.33983, u_2} E
F : D ⥤ E
G✝ : E ⥤ D
inst✝³ : HasWeakSheafify J D
inst✝² : HasSheafCompose J F
inst✝¹ : ConcreteCategory D
inst✝ : HasSheafCompose J (forget D)
G : Type (max v u) ⥤ D
adj : G ⊣ forget D
Y : SheafOfTypes J
⊢ ((sheafEquivSheafOfTypes J).symm.unit.app Y).val ≫
      ((Adjunction.whiskerRight Cᵒᵖ adj).homEquiv Y.val ((presheafToSheaf J D).obj (Y.val ⋙ G)).val)
        (toSheafify J (Y.val ⋙ G)) =
    (Adjunction.whiskerRight Cᵒᵖ adj).unit.app Y.val ≫ whiskerRight (toSheafify J (Y.val ⋙ G)) (forget D)
```
