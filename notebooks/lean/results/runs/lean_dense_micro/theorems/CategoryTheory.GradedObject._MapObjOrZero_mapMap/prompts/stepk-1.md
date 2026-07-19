## Current goal
```
⊢ ιMapObjOrZero X p i j ≫ mapMap φ p j = φ i ≫ ιMapObjOrZero Y p i j
```

## Full tactic state
```
case neg
I : Type u_1
J : Type u_2
K : Type u_3
C : Type u_4
inst✝⁵ : Category.{u_5, u_4} C
X Y Z : GradedObject I C
φ : X ⟶ Y
e : X ≅ Y
ψ : Y ⟶ Z
p : I → J
j✝ : J
inst✝⁴ : HasMap X p
inst✝³ : HasMap Y p
inst✝² : HasMap Z p
q : J → K
r : I → K
hpqr : ∀ (i : I), q (p i) = r i
inst✝¹ : HasZeroMorphisms C
inst✝ : DecidableEq J
i : I
j : J
h : ¬p i = j
⊢ ιMapObjOrZero X p i j ≫ mapMap φ p j = φ i ≫ ιMapObjOrZero Y p i j
```
