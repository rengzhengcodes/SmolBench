## Current goal
```
⊢ IsIso (Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val))) ↔
    IsIso { val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) }
```

## Full tactic state
```
C : Type u
inst✝² : Category.{v, u} C
J : GrothendieckTopology C
A : Type u'
inst✝¹ : Category.{v', u'} A
inst✝ : ConcreteCategory A
F G : Sheaf J (Type w)
f : F ⟶ G
⊢ IsIso (Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val))) ↔
    IsIso { val := Subpresheaf.ι (Subpresheaf.sheafify J (imagePresheaf f.val)) }
```
