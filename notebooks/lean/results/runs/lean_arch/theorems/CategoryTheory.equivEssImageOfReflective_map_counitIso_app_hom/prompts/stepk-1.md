## Current goal
```
⊢ inv ((ofRightAdjoint i).unit.app X.obj) = inv ((ofRightAdjoint i).unit.app X.obj)
```

## Full tactic state
```
C : Type u₁
D : Type u₂
E : Type u₃
inst✝³ : Category.{v₁, u₁} C
inst✝² : Category.{v₂, u₂} D
inst✝¹ : Category.{v₃, u₃} E
i : D ⥤ C
inst✝ : Reflective i
X : Functor.EssImageSubcategory i
⊢ inv ((ofRightAdjoint i).unit.app X.obj) = inv ((ofRightAdjoint i).unit.app X.obj)
```
