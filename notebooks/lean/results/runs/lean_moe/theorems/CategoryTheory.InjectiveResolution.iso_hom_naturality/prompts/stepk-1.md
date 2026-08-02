## Current goal
```
⊢ (injectiveResolution X).ι ≫ (homotopyEquiv (injectiveResolution X) I).hom ≫ φ = (CochainComplex.single₀ C).map f ≫ J.ι
```

## Full tactic state
```
case h.h_comm
C : Type u
inst✝² : Category.{v, u} C
inst✝¹ : Abelian C
inst✝ : HasInjectiveResolutions C
X Y : C
f : X ⟶ Y
I : InjectiveResolution X
J : InjectiveResolution Y
φ : I.cocomplex ⟶ J.cocomplex
comm : I.ι.f 0 ≫ φ.f 0 = f ≫ J.ι.f 0
⊢ (injectiveResolution X).ι ≫ (homotopyEquiv (injectiveResolution X) I).hom ≫ φ = (CochainComplex.single₀ C).map f ≫ J.ι
```
