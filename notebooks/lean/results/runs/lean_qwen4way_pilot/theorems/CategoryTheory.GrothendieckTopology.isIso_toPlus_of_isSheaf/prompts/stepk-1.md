## Current goal
```
⊢ (diagram J P X.unop).map e = inv (Cover.toMultiequalizer S.unop P) ≫ Cover.toMultiequalizer T.unop P
```

## Full tactic state
```
C : Type u
inst✝³ : Category.{v, u} C
J : GrothendieckTopology C
D : Type w
inst✝² : Category.{max v u, w} D
inst✝¹ : ∀ (P : Cᵒᵖ ⥤ D) (X : C) (S : Cover J X), HasMultiequalizer (Cover.index S P)
P : Cᵒᵖ ⥤ D
inst✝ : ∀ (X : C), HasColimitsOfShape (Cover J X)ᵒᵖ D
hP : ∀ (X : C) (S : Cover J X), IsIso (Cover.toMultiequalizer S P)
X : Cᵒᵖ
S T : (Cover J X.unop)ᵒᵖ
e : S ⟶ T
this : Cover.toMultiequalizer S.unop P ≫ (diagram J P X.unop).map e = Cover.toMultiequalizer T.unop P
⊢ (diagram J P X.unop).map e = inv (Cover.toMultiequalizer S.unop P) ≫ Cover.toMultiequalizer T.unop P
```
