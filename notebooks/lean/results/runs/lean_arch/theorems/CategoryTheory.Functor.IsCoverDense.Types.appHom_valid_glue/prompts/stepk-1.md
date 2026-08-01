## Current goal
```
⊢ (appHom α X ≫ ℱ'.val.map f) a✝ = (ℱ.map f ≫ α.app (op Y)) a✝
```

## Full tactic state
```
case h
C : Type u_1
inst✝⁵ : Category.{u_6, u_1} C
D : Type u_2
inst✝⁴ : Category.{u_5, u_2} D
E : Type u_3
inst✝³ : Category.{?u.46606, u_3} E
J : GrothendieckTopology C
K : GrothendieckTopology D
L : GrothendieckTopology E
A : Type u_4
inst✝² : Category.{?u.46658, u_4} A
G : C ⥤ D
inst✝¹ : IsCoverDense G K
inst✝ : Full G
ℱ : Dᵒᵖ ⥤ Type v
ℱ' : SheafOfTypes K
α : G.op ⋙ ℱ ⟶ G.op ⋙ ℱ'.val
X : D
Y : C
f : op X ⟶ op (G.obj Y)
a✝ : ℱ.obj (op X)
⊢ (appHom α X ≫ ℱ'.val.map f) a✝ = (ℱ.map f ≫ α.app (op Y)) a✝
```
