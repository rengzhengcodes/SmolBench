## Current goal
```
⊢ F.map (g j) z = (s.ι.app { as := j }) z
```

## Full tactic state
```
case intro.intro.intro.intro.intro.intro.mk.intro
C : Type u₁
inst✝² : Category.{u₂, u₁} C
inst✝¹ : GaloisCategory C
F : C ⥤ FintypeCat
inst✝ : FiberFunctor F
X : C
ι : Type
f : ι → C
g : (i : ι) → f i ⟶ X
hl : IsColimit (Cofan.mk X g)
hc : ∀ (i : ι), IsConnected (f i)
he : Finite ι
this : Fintype ι
s : Cocone (Discrete.functor f ⋙ F) := F.mapCocone (Cofan.mk X g)
s' : IsColimit s := isColimitOfPreserves F hl
j : ι
z : (forget FintypeCat).obj ((Discrete.functor f ⋙ F).obj { as := j })
⊢ F.map (g j) z = (s.ι.app { as := j }) z
```
